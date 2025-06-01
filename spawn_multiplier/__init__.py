from enum import StrEnum
from typing import Any

import unrealsdk
from mods_base import SliderOption, build_mod, hook
from unrealsdk.hooks import Type
from unrealsdk.unreal import BoundFunction, UObject, WeakPointer, WrappedStruct

last_pop_master: WeakPointer = WeakPointer()
last_pop_master_original_limit: int | None = None


def update_spawn_limit(pop_master: UObject) -> None:
    global last_pop_master, last_pop_master_original_limit

    if (
        existing_pop_master := last_pop_master()
    ) is not None and last_pop_master_original_limit is not None:
        existing_pop_master.MaxActorCost = last_pop_master_original_limit

    last_pop_master = WeakPointer(pop_master)
    last_pop_master_original_limit = pop_master.MaxActorCost

    pop_master.MaxActorCost = int(
        pop_master.MaxActorCost * spawn_limit_multiplier_slider.value
    )


@hook("GearboxFramework.PopulationMaster:SpawnPopulationControlledActor")
def spawn_pop_controlled_actor(
    obj: UObject,
    _args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    if obj == last_pop_master():
        return
    update_spawn_limit(obj)


DEN_BLACKLIST: set[str] = {
    "Grass_Cliffs_Combat.TheWorld:PersistentLevel.PopulationOpportunityDen_16",
    "Boss_Cliffs_CombatLoader.TheWorld:PersistentLevel.PopulationOpportunityDen_4",
    "Sage_RockForest_Dynamic.TheWorld:PersistentLevel.PopulationOpportunityDen_11",
    "Helios_Mission_Main.TheWorld:PersistentLevel.PopulationOpportunityDen_6",
    "Dungeon_Mission.TheWorld:PersistentLevel.PopulationOpportunityDen_4",
    "Dungeon_Mission.TheWorld:PersistentLevel.PopulationOpportunityDen_12",
    "Dungeon_Mission.TheWorld:PersistentLevel.PopulationOpportunityDen_9",
}
ENCOUNTER_BLACKLIST: set[str] = set()


def can_den_be_multiplied(den: UObject | None) -> bool:
    if den is None or den._path_name() in DEN_BLACKLIST or (pop_def := den.PopulationDef) is None:
        return False

    return all(
        (factory := actor.SpawnFactory) is not None
        and factory.Class.Name
        not in (
            "PopulationFactoryBlackMarket",
            "PopulationFactoryInteractiveObject",
            "PopulationFactoryVendingMachine",
        )
        for actor in pop_def.ActorArchetypeList
    )


def multiply_den_if_allowed(den: UObject | None, adjustment: float) -> None:
    if den is None or not can_den_be_multiplied(den):
        return
    den.SpawnData.MaxActiveActors = round(den.SpawnData.MaxActiveActors * adjustment)
    den.MaxActiveActorsIsNormal = round(den.MaxActiveActorsIsNormal * adjustment)
    den.MaxActiveActorsThreatened = round(den.MaxActiveActorsThreatened * adjustment)
    den.MaxTotalActors = round(den.MaxTotalActors * adjustment)


def multiply_pop_encounter_if_allowed(encounter: UObject | None, adjustment: float) -> None:
    if encounter is None or encounter.PathName(encounter) in ENCOUNTER_BLACKLIST:
        return

    for wave in encounter.Waves:
        if (wave_spawn_limits := wave.SpawnLimits) is None:
            continue
        if not all(can_den_be_multiplied(den) for den in wave.MemberOpportunities):
            continue

        for limit in wave_spawn_limits:
            limit.MaxTotalToSpawn.BaseValueScaleConstant = round(
                limit.MaxTotalToSpawn.BaseValueScaleConstant * adjustment,
            )
            limit.MaxActiveAtATime.BaseValueScaleConstant = round(
                limit.MaxActiveAtATime.BaseValueScaleConstant * adjustment,
            )


@hook("GearboxFramework.PopulationEncounter:UpdateOpportunityEnabledStates")
def update_pop_opportunity_enabled_states(
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    if args.nWave != -1:
        return
    multiply_pop_encounter_if_allowed(obj, multiplier_slider.value)


@hook("WillowGame.PopulationOpportunityDen:PostBeginPlay", Type.POST)
def den_post_begin_play(
    obj: UObject,
    _args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    multiply_den_if_allowed(obj, multiplier_slider.value)


def multiply_existing(adjustment: float) -> None:
    for den in unrealsdk.find_all("PopulationOpportunityDen"):
        multiply_den_if_allowed(den, adjustment)
    for encounter in unrealsdk.find_all("PopulationEncounter"):
        multiply_pop_encounter_if_allowed(encounter, adjustment)


@SliderOption(
    identifier="Multiplier",
    value=4,
    min_value=1,
    max_value=25,
    description="The amount to multiply spawns by.",
)
def multiplier_slider(opt: SliderOption, new_value: float) -> None:
    if not opt.mod or not opt.mod.is_enabled:
        return
    multiply_existing(new_value / multiplier_slider.value)


@SliderOption(
    identifier="Spawn Limit Multiplier",
    value=1,
    min_value=1,
    max_value=25,
    description="Multiplier for spawn limit (amount of NPCs that spawn at one time).",
)
def spawn_limit_multiplier_slider(opt: SliderOption, new_value: int) -> None:
    if not opt.mod or not opt.mod.is_enabled:
        return
    update_spawn_limit(
        (
            unrealsdk.find_class("GearboxGlobals")
            .ClassDefaultObject.GetGearboxGlobals()
            .GetPopulationMaster()
        )
    )


def on_enable() -> None:  # noqa: D103
    multiply_existing(multiplier_slider.value / 1)
    update_spawn_limit(
        (
            unrealsdk.find_class("GearboxGlobals")
            .ClassDefaultObject.GetGearboxGlobals()
            .GetPopulationMaster()
        )
    )


def on_disable() -> None:  # noqa: D103
    multiply_existing(1 / multiplier_slider.value)
    if (pop_master := last_pop_master()) is not None and last_pop_master_original_limit is not None:
        pop_master.MaxActorCost = last_pop_master_original_limit


mod = build_mod(
    options=[
        multiplier_slider,
        spawn_limit_multiplier_slider,
    ]
)

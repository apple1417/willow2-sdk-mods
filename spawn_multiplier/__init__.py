from enum import StrEnum
from typing import Any

import unrealsdk
from mods_base import Game, SliderOption, SpinnerOption, build_mod, hook
from unrealsdk.hooks import Type
from unrealsdk.unreal import BoundFunction, UObject, WeakPointer, WrappedStruct


class SpawnLimitType(StrEnum):
    Standard = "Standard"
    Linear = "Linear"
    Unlimited = "Unlimited"
    Custom = "Custom"


last_pop_master: WeakPointer = WeakPointer()
last_pop_master_original_limit: int | None = None


def update_spawn_limit(pop_master: UObject, limit_type: SpawnLimitType | str) -> None:
    """
    Updates the spawn limit, taking into account the new scaling type.

    Args:
        pop_master: The population master holding the spawn limit to update.
        limit_type: What scaling type the limit should use.
    """
    global last_pop_master, last_pop_master_original_limit

    if (
        existing_pop_master := last_pop_master()
    ) is not None and last_pop_master_original_limit is not None:
        existing_pop_master.MaxActorCost = last_pop_master_original_limit

    last_pop_master = WeakPointer(pop_master)
    last_pop_master_original_limit = pop_master.MaxActorCost

    match limit_type:
        case SpawnLimitType.Linear:
            pop_master.MaxActorCost *= multiplier_slider.value
        case SpawnLimitType.Unlimited:
            pop_master.MaxActorCost = 0x7FFFFFFF
        case SpawnLimitType.Custom:
            pop_master.MaxActorCost *= custom_multiplier_slider.value
        case _:
            pass


@SliderOption(
    identifier="Multiplier",
    value=4,
    min_value=1,
    max_value=25,
    description="The amount to multiply spawns by.",
)
def multiplier_slider(opt: SliderOption, new_value: float) -> None:  # noqa: D103
    if not opt.mod or not opt.mod.is_enabled:
        return
    multiply_existing(new_value / multiplier_slider.value)


@SpinnerOption(
    identifier="Spawn Limit",
    value=SpawnLimitType.Linear,
    choices=list(SpawnLimitType),
    description=(
        "How to handle the spawn limit."
        f" {SpawnLimitType.Standard}: Don't change it;"
        f" {SpawnLimitType.Linear}: Increase linearly with the multiplier;"
        f" {SpawnLimitType.Unlimited}: Remove it;"
        f" {SpawnLimitType.Custom}: Apply a custom multiplier."
    ),
)
def spawn_limit_spinner(opt: SpinnerOption, new_value: str) -> None:  # noqa: D103
    if not opt.mod or not opt.mod.is_enabled:
        return
    update_spawn_limit(
        (
            unrealsdk.find_class("GearboxGlobals")
            .ClassDefaultObject.GetGearboxGlobals()
            .GetPopulationMaster()
        ),
        new_value,
    )


@SliderOption(
    identifier="Custom Spawn Limit Multiplier",
    value=4,
    min_value=1,
    max_value=25,
    description="The custom multiplier to apply when using 'Custom' spawn limit type.",
)
def custom_multiplier_slider(opt: SliderOption, new_value: float) -> None:  # noqa: D103
    if not opt.mod or not opt.mod.is_enabled:
        return
    if spawn_limit_spinner.value == SpawnLimitType.Custom:
        multiply_existing(new_value / custom_multiplier_slider.value)


@hook("GearboxFramework.PopulationMaster:SpawnPopulationControlledActor")
def spawn_pop_controlled_actor(  # noqa: D103
    obj: UObject,
    _args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    if obj == last_pop_master():
        return
    update_spawn_limit(obj, spawn_limit_spinner.value)


DEN_BLACKLIST: set[str] = {
    # Thousand Cuts Brick
    "Grass_Cliffs_Combat.TheWorld:PersistentLevel.PopulationOpportunityDen_16",
    # First Bunker autocannon
    "Boss_Cliffs_CombatLoader.TheWorld:PersistentLevel.PopulationOpportunityDen_4",
    # Claptrap worshippers
    "Sage_RockForest_Dynamic.TheWorld:PersistentLevel.PopulationOpportunityDen_11",
    # Story kill Uranus
    "Helios_Mission_Main.TheWorld:PersistentLevel.PopulationOpportunityDen_6",
    # Resurrected skeletons in My Dead Brother - first grave
    "Dungeon_Mission.TheWorld:PersistentLevel.PopulationOpportunityDen_4",
    # Resurrected skeletons in My Dead Brother - second grave
    "Dungeon_Mission.TheWorld:PersistentLevel.PopulationOpportunityDen_12",
    # Resurrected skeletons in My Dead Brother - third grave
    "Dungeon_Mission.TheWorld:PersistentLevel.PopulationOpportunityDen_9",
    # BL1
    # Intro dens just before fyrestone
    "Arid_Firestone.TheWorld:PersistentLevel.PopulationOpportunityDen_4",
    "Arid_Firestone.TheWorld:PersistentLevel.PopulationOpportunityDen_5",
    "Arid_Firestone.TheWorld:PersistentLevel.PopulationOpportunityDen_12",
    "Arid_Firestone.TheWorld:PersistentLevel.PopulationOpportunityDen_15",
    "Arid_Firestone.TheWorld:PersistentLevel.PopulationOpportunityDen_16",
    "Arid_Firestone.TheWorld:PersistentLevel.PopulationOpportunityDen_19",
    "Arid_Firestone.TheWorld:PersistentLevel.PopulationOpportunityDen_26",
    "Arid_Firestone.TheWorld:PersistentLevel.PopulationOpportunityDen_28",
    # Psychos before Hanz/Franz
    "Interlude_2_Digger.TheWorld:PersistentLevel.PopulationOpportunityDen_1",
    # Turrets in Crimson Enclave, spawn with no collision
    "W_Waste_Crimson_P.TheWorld:PersistentLevel.PopulationOpportunityDen_9",
    "W_Waste_Crimson_P.TheWorld:PersistentLevel.PopulationOpportunityDen_12",
    "W_Waste_Crimson_P.TheWorld:PersistentLevel.PopulationOpportunityDen_17",
}
ENCOUNTER_BLACKLIST: set[str] = set()


def can_den_be_multiplied(den: UObject | None) -> bool:
    """
    Checks if a population den is allowed to be multiplied.

    Args:
        den: The den to check.
    Returns:
        True if the den is allowed to be multiplied.
    """
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
    """
    Multiplies spawns of a population den, if allowed.

    Args:
        den: The den to multiply.
        adjustment: How much to multiply spawns by.
    """
    if den is None or not can_den_be_multiplied(den):
        return
    den.SpawnData.MaxActiveActors = round(den.SpawnData.MaxActiveActors * adjustment)
    den.MaxActiveActorsIsNormal = round(den.MaxActiveActorsIsNormal * adjustment)
    den.MaxActiveActorsThreatened = round(den.MaxActiveActorsThreatened * adjustment)
    den.MaxTotalActors = round(den.MaxTotalActors * adjustment)


def multiply_pop_encounter_if_allowed(encounter: UObject | None, adjustment: float) -> None:
    """
    Multiplies spawns of a population encounter, if allowed.

    Args:
        encounter: The encounter to multiply.
        adjustment: How much to multiply spawns by.
    """
    if encounter is None or encounter.PathName(encounter) in ENCOUNTER_BLACKLIST:
        return

    if Game.get_current() == Game.BL1:
        for limit in encounter.SpawnLimits:
            limit.MaxTotalToSpawn.BaseValueScaleConstant = round(
                limit.MaxTotalToSpawn.BaseValueScaleConstant * adjustment,
            )
            limit.MaxActiveAtATime.BaseValueScaleConstant = round(
                limit.MaxActiveAtATime.BaseValueScaleConstant * adjustment,
            )
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
def update_pop_opportunity_enabled_states(  # noqa: D103
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    # Seems to be -1 on map load
    # I've never seen it get called at another time, but seems reasonable to restrict to this
    if args.nWave != -1:
        return
    multiply_pop_encounter_if_allowed(obj, multiplier_slider.value)


@hook("WillowGame.PopulationOpportunityDen:PostBeginPlay", Type.POST)
def den_post_begin_play(  # noqa: D103
    obj: UObject,
    _args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    multiply_den_if_allowed(obj, multiplier_slider.value)


def multiply_existing(adjustment: float) -> None:
    """
    Adjusts the spawn limit on all already existing objects.

    Args:
        adjustment: The adjustment to apply.
    """
    for den in unrealsdk.find_all("PopulationOpportunityDen"):
        multiply_den_if_allowed(den, adjustment)
    for encounter in unrealsdk.find_all("PopulationEncounter"):
        multiply_pop_encounter_if_allowed(encounter, adjustment)


def on_enable() -> None:  # noqa: D103
    multiply_existing(multiplier_slider.value / 1)
    update_spawn_limit(
        (
            unrealsdk.find_class("GearboxGlobals")
            .ClassDefaultObject.GetGearboxGlobals()
            .GetPopulationMaster()
        ),
        spawn_limit_spinner.value,
    )


def on_disable() -> None:  # noqa: D103
    multiply_existing(1 / multiplier_slider.value)
    if (pop_master := last_pop_master()) is not None and last_pop_master_original_limit is not None:
        pop_master.MaxActorCost = last_pop_master_original_limit


mod = build_mod(options=[multiplier_slider, spawn_limit_spinner, custom_multiplier_slider])

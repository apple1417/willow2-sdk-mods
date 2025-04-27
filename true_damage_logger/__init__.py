from typing import Any

from mods_base import SliderOption, build_mod, get_pc, hook
from unrealsdk import logging
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

digits_option = SliderOption(
    identifier="Minimum Digits",
    value=6,
    min_value=0,
    max_value=40,
    description=(
        "The minimum amount of digits a damage number has to have before it is logged to console."
    ),
)


@hook("WillowGame.WillowDamageTypeDefinition:DisplayRecentDamageForPlayer")
def display_damage(  # noqa: D103
    _obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    pc = get_pc()
    if pc != args.PC:
        return

    damage_event_data = args.DamageEventData
    damage = damage_event_data.TotalDamageForDamageType
    if damage < 10**digits_option.value:
        return

    name: str

    actor = damage_event_data.DamagedActor
    if actor.AIClass is not None and actor.AIClass.DefaultDisplayName is not None:
        name = actor.AIClass.DefaultDisplayName
    else:
        name = str(actor)

    if (actor_bal := actor.BalanceDefinitionState.BalanceDefinition) is not None:
        pt_num = pc.GetCurrentPlaythrough() + 1
        for pt in actor_bal.PlayThroughs:
            if pt.PlayThrough > pt_num:
                continue
            if not pt.DisplayName:
                continue
            name = pt.DisplayName

    logging.info(f"Dealt {damage} damage to level {actor.GetExpLevel()} {name}")


mod = build_mod()

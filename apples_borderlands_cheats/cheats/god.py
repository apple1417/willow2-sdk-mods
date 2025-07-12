from enum import StrEnum
from typing import Any

from mods_base import get_pc, hook
from unrealsdk.hooks import Block, prevent_hooking_direct_calls
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

from . import CyclableOption


class GodMode(StrEnum):
    OFF = "Off"
    ONE_HP = "1 HP"
    FULL = "Full"


@CyclableOption("God Mode", GodMode.OFF, list(GodMode))
def god_mode(_: CyclableOption, new_value: str) -> None:  # noqa: D103
    if not god_mode.mod or not god_mode.mod.is_enabled:
        return

    match new_value:
        case GodMode.OFF:
            take_damage.disable()
            set_health.disable()
        case GodMode.ONE_HP:
            take_damage.disable()
            set_health.enable()
        case GodMode.FULL:
            take_damage.enable()
            set_health.disable()
        case _:
            pass


def god_on_disable() -> None:  # noqa: D103
    take_damage.disable()
    set_health.disable()


# This hook is only used by full god mode. Blocking it stops both the damage and the knockback.
@hook("WillowGame.WillowPlayerPawn:TakeDamage")
def take_damage(  # noqa: D103
    obj: UObject,
    _args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> type[Block] | None:
    return Block if obj == get_pc().Pawn else None


# This hook is only used by 1 HP god mode.
@hook("Engine.Pawn:SetHealth")
def set_health(  # noqa: D103
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    func: BoundFunction,
) -> type[Block] | None:
    if obj != get_pc().Pawn:
        return None

    if args.NewHealth < 1:
        with prevent_hooking_direct_calls():
            func(1)
        return Block

    return None

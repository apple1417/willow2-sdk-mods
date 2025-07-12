from enum import StrEnum
from typing import Any

from mods_base import get_pc, hook
from unrealsdk.hooks import Block
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

from . import CyclableOption


class InfiniteAmmo(StrEnum):
    OFF = "Off"
    FREE_RELOADS = "Free Reloads"
    FULL = "Full"


@CyclableOption("Infinite Ammo", "Off", list(InfiniteAmmo))
def infinite_ammo(_: CyclableOption, new_value: str) -> None:  # noqa: D103
    if not infinite_ammo.mod or not infinite_ammo.mod.is_enabled:
        return

    match new_value:
        case InfiniteAmmo.OFF:
            consume_projectile_resource.disable()
            consume_ammo.disable()
        case InfiniteAmmo.FREE_RELOADS | InfiniteAmmo.FULL:
            consume_projectile_resource.enable()
            consume_ammo.enable()
        case _:
            pass


def infinite_ammo_on_disable() -> None:  # noqa: D103
    consume_projectile_resource.disable()
    consume_ammo.disable()


# This hook prevents consuming grenades
@hook("WillowGame.WillowPlayerController:ConsumeProjectileResource")
def consume_projectile_resource(  # noqa: D103
    obj: UObject,
    _args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> type[Block] | None:
    if obj != get_pc():
        return None
    return Block


# And this one does all normal weapons
@hook("WillowGame.WillowWeapon:ConsumeAmmo")
def consume_ammo(  # noqa: D103
    obj: UObject,
    _args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> type[Block] | None:
    try:
        if obj not in ((pawn := get_pc().Pawn).Weapon, pawn.OffHandWeapon):
            return None
    except AttributeError:
        return None

    if infinite_ammo.value == InfiniteAmmo.FULL:
        obj.RefillClip()

    return Block

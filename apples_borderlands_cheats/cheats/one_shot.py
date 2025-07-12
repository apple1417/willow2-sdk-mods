from typing import Any

from mods_base import ENGINE, get_pc, hook
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

from . import CyclableOption, OnOff


@CyclableOption("One Shot Mode", OnOff.OFF, list(OnOff))
def one_shot(_: CyclableOption, new_value: str) -> None:  # noqa: D103
    if not one_shot.mod or not one_shot.mod.is_enabled:
        return

    match new_value:
        case OnOff.OFF:
            take_damage.disable()
        case OnOff.On:
            take_damage.enable()
        case _:
            pass


def one_shot_on_disable() -> None:  # noqa: D103
    take_damage.disable()


@hook("WillowGame.WillowAIPawn:TakeDamage")
@hook("WillowGame.WillowVehicle:TakeDamage")
def take_damage(  # noqa: D103
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    pc = get_pc()

    if (instigator := args.InstigatedBy) != pc:
        return

    if ENGINE.GetCurrentWorldInfo().Game.IsFriendlyFire(obj, instigator.Pawn):
        return

    obj.SetShieldStrength(0)

    # Try set the health to 1 so that your shot kills them, giving xp
    # Only do it if they have more than 1 health though, so that you don't get stuck in a loop if
    # you somehow deal less than 1 damage
    if obj.GetHealth() > 1:
        obj.SetHealth(1)
    else:
        obj.SetHealth(0)

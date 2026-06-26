from typing import TYPE_CHECKING, Any

from mods_base import ENGINE, get_pc, hook

from . import CyclableOption, OnOff

if TYPE_CHECKING:
    from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct


@CyclableOption("One Shot Mode", OnOff.OFF, list(OnOff)).set_on_change()
def one_shot(_: CyclableOption, new_value: str) -> None:  # noqa: D103
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

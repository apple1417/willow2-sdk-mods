from typing import Any

from mods_base import BoolOption, build_mod, hook
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

skip_ffyl = BoolOption(
    identifier="Skip FFYL",
    value=False,
    description="When you take damage, you will instantly respawn, skipping FFYL.",
)
one_hit_enemies = BoolOption(
    identifier="One-Hit Enemies",
    value=False,
    description="Make players also one-hit enemies.",
)


@hook("WillowGame.WillowPlayerPawn:TakeDamage")
def player_take_damage(  # noqa: D103
    obj: UObject,
    _args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    if skip_ffyl.value:
        obj.Controller.CausePlayerDeath(True)
    else:
        obj.SetHealth(0)


@hook("WillowGame.WillowAIPawn:TakeDamage")
@hook("WillowGame.WillowVehicle:TakeDamage")
def enemy_take_damage(  # noqa: D103
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    if not one_hit_enemies.value:
        return
    if args.InstigatedBy.Class.Name != "WillowPlayerController":
        return
    if args.InstigatedBy.WorldInfo.Game.IsFriendlyFire(obj, args.InstigatedBy.Pawn):
        return

    obj.SetShieldStrength(0)
    # Try set the health to 1 so that your shot kills them, giving xp
    # Only do it if they have more than 1 health though, so that you don't get stuck in loop if you
    # somehow deal less than 1 damage
    if obj.GetHealth() > 1:
        obj.SetHealth(1)
    else:
        obj.SetHealth(0)


build_mod()

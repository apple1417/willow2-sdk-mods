from typing import Any

from mods_base import build_mod, get_pc, hook
from unrealsdk.hooks import Type
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct


@hook("WillowGame.WillowPlayerController:PostBeginPlay", Type.POST)
def post_begin_play(  # noqa: D103
    obj: UObject,
    _args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    obj.bShowUndiscoveredMissions = False


def on_enable() -> None:  # noqa: D103
    get_pc().bShowUndiscoveredMissions = False


def on_disable() -> None:  # noqa: D103
    get_pc().bShowUndiscoveredMissions = True


build_mod()

from typing import Any

from mods_base import get_pc, hook
from unrealsdk.hooks import Block
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

from . import CyclableOption, OnOff


@CyclableOption("Instant Cooldown", OnOff.OFF, list(OnOff))
def instant_cooldown(_: CyclableOption, new_value: str) -> None:  # noqa: D103
    if not instant_cooldown.mod or not instant_cooldown.mod.is_enabled:
        return

    match new_value:
        case OnOff.OFF:
            start_cooldown.disable()
        case OnOff.On:
            start_cooldown.enable()

            pc = get_pc()
            pc.ResetSkillCooldown()
            pc.ResetMeleeSkillCooldown()
        case _:
            pass


def instant_cooldown_on_disable() -> None:  # noqa: D103
    start_cooldown.disable()


@hook("WillowGame.WillowPlayerController:StartActiveSkillCooldown")
@hook("WillowGame.WillowPlayerController:StartMeleeSkillCooldown")
def start_cooldown(  # noqa: D103
    obj: UObject,
    _args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> type[Block] | None:
    return Block if obj == get_pc() else None

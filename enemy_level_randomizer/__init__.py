import random
from typing import Any

from mods_base import SliderOption, build_mod, hook
from unrealsdk.hooks import Block, prevent_hooking_direct_calls
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

offset_slider = SliderOption(
    identifier="Level Offset",
    value=0,
    min_value=-50,
    max_value=50,
    description="A constant offset applied to the intended enemy levels, before any randomization.",
)
min_slider = SliderOption(
    identifier="Max Decrease",
    value=5,
    min_value=0,
    max_value=50,
    description=(
        "The maximum amount an enemy's level can be randomly decreased."
        " Note that a level cannot be decreased below 0."
    ),
)
max_slider = SliderOption(
    identifier="Max Increase",
    value=5,
    min_value=0,
    max_value=50,
    description="The maximum amount an enemy's level can be randomly increased.",
)


@hook("WillowGame.WillowPawn:SetGameStage")
def display_damage(  # noqa: D103
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    func: BoundFunction,
) -> type[Block] | None:
    if obj.Class.Name == "WillowPlayerPawn":
        return None

    base = max(0, args.NewGameStage + offset_slider.value)
    min_val = max(0, base - int(min_slider.value))
    max_val = max(0, base + int(max_slider.value))

    new_val = random.randrange(min_val, max_val + 1)  # noqa: S311

    with prevent_hooking_direct_calls():
        func(new_val)
    return Block


build_mod()

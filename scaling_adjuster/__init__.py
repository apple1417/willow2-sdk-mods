import unrealsdk
from mods_base import Game, SliderOption, build_mod


def set_scaling(val: float) -> None:
    """
    Sets the base scaling constant to the given value.

    Args:
        val: The value to set the constant to
    """
    scaling_resolver = unrealsdk.find_object(
        "ConstantAttributeValueResolver",
        "GD_Balance_HealthAndDamage.HealthAndDamage.Att_UniversalBalanceScaler:ConstantAttributeValueResolver_0",
    )
    scaling_resolver.ConstantValue = val / 100


@SliderOption(
    identifier="Scaling Constant",
    value=111 if Game.get_current() == Game.TPS else 113,
    min_value=0,
    max_value=500,
    description=(
        "The base scaling constant to use, multiplied by 100.\n"
        "113 means every level the numbers get 13% higher."
    ),
)
def scaling_option(_: SliderOption, new_val: float) -> None:  # noqa: D103
    if mod.is_enabled:
        set_scaling(new_val)


def on_enable() -> None:  # noqa: D103
    set_scaling(scaling_option.value)


def on_disable() -> None:  # noqa: D103
    set_scaling(scaling_option.default_value)


mod = build_mod()

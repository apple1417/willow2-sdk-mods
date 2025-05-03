from typing import TYPE_CHECKING, Any

import unrealsdk
from mods_base import BoolOption, SliderOption, build_mod, hook
from unrealsdk.hooks import Block
from unrealsdk.unreal import BoundFunction, UObject, WeakPointer, WrappedStruct

if TYPE_CHECKING:
    from enum import auto

    from unrealsdk.unreal._uenum import UnrealEnum  # pyright: ignore[reportMissingModuleSource]

    class EModifierType(UnrealEnum):
        MT_Scale = auto()
        MT_PreAdd = auto()
        MT_PostAdd = auto()
        MT_MAX = auto()

else:
    EModifierType = unrealsdk.find_enum("EModifierType")


jump_damage_slider = SliderOption(
    identifier="Jump Damage",
    value=50,
    min_value=0,
    max_value=100,
    description="The percentage of enemy health jumping damage deals.",
)
jump_damage_champion_slider = SliderOption(
    identifier="Jump Damage (Champion)",
    value=20,
    min_value=0,
    max_value=100,
    description=(
        'The percentage of enemy health jumping damage deals to "Champion" enemies.\n'
        "These are generally Badasses and Bosses."
    ),
)
jump_damage_only = BoolOption(
    identifier="Disable Other Damage",
    value=False,
    description=(
        "Disables other forms of damage, you can only hurt enemies by jumping on them. May have"
        " side effects."
    ),
)

jump_height_attr: WeakPointer = WeakPointer()
jump_height_modifier: WeakPointer = WeakPointer()
move_speed_attr: WeakPointer = WeakPointer()
move_speed_modifier: WeakPointer = WeakPointer()


def enable_disable_modifiers(enable: bool) -> None:  # noqa: D103
    jump_attr = jump_height_attr()
    jump_mod = jump_height_modifier()
    move_attr = move_speed_attr()
    move_mod = move_speed_modifier()

    # Always use a find all to affect all players
    for pawn in unrealsdk.find_all("WillowPlayerPawn"):
        if jump_attr is not None and jump_mod is not None:
            if enable:
                jump_attr.AddAttributeModifier(pawn, jump_mod)
            else:
                jump_attr.RemoveAttributeModifier(pawn, jump_mod)

        if move_attr is not None and move_mod is not None:
            if enable:
                move_attr.AddAttributeModifier(pawn, move_mod)
            else:
                move_attr.RemoveAttributeModifier(pawn, move_mod)


def on_modifier_option_change(  # noqa: D103
    opt: SliderOption,
    new_value: float,
    modifier: UObject | None,
) -> None:
    if modifier is None or opt.mod is None or not opt.mod.is_enabled:
        return
    modifier.Value = new_value / 100
    # Remove and re-add the modifiers to apply at the new value
    enable_disable_modifiers(False)
    enable_disable_modifiers(True)


jump_height_slider = SliderOption(
    identifier="Jump Height Scale",
    value=50,
    min_value=-500,
    max_value=500,
    description=(
        "Percent to adjust jump height by. Positive values increase height, negative values"
        " decrease it."
    ),
    on_change=lambda opt, val: on_modifier_option_change(opt, val, jump_height_modifier()),
)
move_speed_slider = SliderOption(
    identifier="Move Speed Scale",
    value=50,
    min_value=-500,
    max_value=500,
    description=(
        "Percent to adjust move speed by. Positive values increase speed, negative values decrease"
        " it."
    ),
    on_change=lambda opt, val: on_modifier_option_change(opt, val, move_speed_modifier()),
)


def create_objects() -> None:
    """Creates all the global objects we'll be using."""

    def find_or_construct(cls: str, outer: UObject | None, name: str) -> UObject:
        try:
            # Can always add a dot since we know we're not using subpackages
            full_name = name if outer is None else outer._path_name() + "." + name
            return unrealsdk.find_object(cls, full_name)
        except ValueError:
            return unrealsdk.construct_object(cls, outer, name, flags=0x4000)

    global jump_height_attr, jump_height_modifier, move_speed_attr, move_speed_modifier
    package = find_or_construct("Package", None, "Mario")

    # While there is a jump height attribute in BL2, there isn't in TPS(/AoDK??), so we make our own
    jump_attr = find_or_construct(
        "AttributeDefinition",
        package,
        "Attr_JumpHeight",
    )
    jump_attr.ContextResolverChain = [
        # Not setting keep alive flags on this, the attribute will do so, and it means if this code
        # re-runs this object will get gc'd, we don't need a separate check for if to set these
        unrealsdk.construct_object("PawnAttributeContextResolver", jump_attr),
    ]
    jump_attr.ValueResolverChain = [
        jump_value_resolver := unrealsdk.construct_object(
            "ObjectPropertyAttributeValueResolver",
            jump_attr,
        ),
    ]
    jump_value_resolver.CachedProperty = unrealsdk.find_object(
        "FloatAttributeProperty",
        "Engine.Pawn:JumpZ",
    )
    jump_value_resolver.PropertyName = "JumpZ"
    jump_height_attr = WeakPointer(jump_attr)

    jump_modifier = find_or_construct("AttributeModifier", package, "Modifier_JumpHeight")
    jump_modifier.Type = EModifierType.MT_Scale
    jump_modifier.Value = jump_height_slider.value / 100
    jump_height_modifier = WeakPointer(jump_modifier)

    move_attr = unrealsdk.find_object(
        "AttributeDefinition",
        "D_Attributes.GameplayAttributes.FootSpeed",
    )
    move_speed_attr = WeakPointer(move_attr)

    move_modifier = find_or_construct("AttributeModifier", package, "Modifier_MoveSpeed")
    move_modifier.Type = EModifierType.MT_Scale
    move_modifier.Value = move_speed_slider.value / 100
    move_speed_modifier = WeakPointer(move_modifier)


@hook("WillowGame.WillowAIPawn:TakeDamage")
def take_damage(  # noqa: D103
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> type[Block] | None:
    if (instigator := args.InstigatedBy) is None:
        return None
    if instigator.Class.Name != "WillowPlayerController":
        return None
    if obj.WorldInfo.Game.IsFriendlyFire(obj, instigator.Pawn):
        return None
    if args.DamageType.Name != "DmgType_Crushed":
        return Block if jump_damage_only.value else None

    multiplier: float
    if obj.BalanceDefinitionState.BalanceDefinition.Champion:
        multiplier = jump_damage_champion_slider.value / 100
    else:
        multiplier = jump_damage_slider.value / 100

    damage = (obj.GetMaxHealth() + obj.GetMaxShieldStrength()) * multiplier

    shield = obj.GetShieldStrength()
    if damage < shield:
        obj.SetShieldStrength(shield - damage)
        return None

    obj.SetShieldStrength(0)
    damage -= shield

    # If we set the health to 0, you don't get any xp. It's easiest to just set health to 0.5, and
    # let this function continue to have the normal damage tick kill them.
    # In the case that the enemy has less than 0.5 health, we just kill them to avoid a loop.
    health = obj.GetHealth()
    if health < 0.5:  # noqa: PLR2004
        obj.SetHealth(0)
    elif (health - damage) < 0.5:  # noqa: PLR2004
        obj.SetHealth(0.5)
    else:
        obj.SetHealth(health - damage)

    return None


@hook("WillowGame.WillowPawn:PostBeginPlay")
def post_begin_play(  # noqa: D103
    obj: UObject,
    _args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> type[Block] | None:
    if obj.Class.Name != "WillowPlayerPawn":
        return
    enable_disable_modifiers(True)


def on_enable() -> None:  # noqa: D103
    create_objects()
    enable_disable_modifiers(True)


def on_disable() -> None:  # noqa: D103
    enable_disable_modifiers(False)


mod = build_mod(
    options=(
        jump_damage_slider,
        jump_damage_champion_slider,
        jump_damage_only,
        jump_height_slider,
        move_speed_slider,
    ),
)

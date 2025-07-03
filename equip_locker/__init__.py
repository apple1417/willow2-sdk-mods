from collections.abc import Iterator, Sequence
from typing import Any

from mods_base import (
    JSON,
    BaseOption,
    BoolOption,
    GroupedOption,
    NestedOption,
    ValueOption,
    build_mod,
    get_pc,
    hook,
)
from unrealsdk.hooks import Block, Type
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

from equip_locker.restrictions import Restriction
from equip_locker.restrictions.allegiance import allegience_restriction
from equip_locker.restrictions.rarity import rarity_restriction
from equip_locker.restrictions.weap_item_type import weapon_item_type_restriction

type Inventory = UObject

options: list[BaseOption] = []
enable_restriction_pairs: list[tuple[BoolOption, Restriction]] = []

for restriction in (
    allegience_restriction,
    rarity_restriction,
    weapon_item_type_restriction,
):
    enable_opt = BoolOption(
        f"Enable {restriction.name}",
        False,
        true_text="Enabled",
        false_text="Disabled",
        description=restriction.description,
    )
    options.append(enable_opt)
    options.append(
        NestedOption(
            restriction.name,
            restriction.options,
            description=restriction.description,
        ),
    )

    enable_restriction_pairs.append((enable_opt, restriction))


def can_item_be_equipped(item: Inventory) -> bool:
    """
    Checks if an item is allowed to be equipped.

    Args:
        item: The item to check.
    Returns:
        True if the item may be equipped.
    """
    for enable_opt, restriction in enable_restriction_pairs:
        if not enable_opt.value:
            continue
        if not restriction.can_item_be_equipped(item):
            return False
    return True


@hook("Engine.Inventory:GiveTo")
def inventory_give_to(  # noqa: D103
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> type[Block] | None:
    if (pawn := args.Other) != get_pc().Pawn:
        return None

    if can_item_be_equipped(obj):
        return None

    if (inv_manager := pawn.InvManager) is None:
        return None

    inv_manager.ClientConditionalIncrementPickupStats(obj)
    # Force bReady False so that you don't force equip
    inv_manager.AddInventory(obj, False, False, args.bPlayPickupSound)
    return Block


@hook("Engine.WillowInventory:CanBeUsedBy")
def inventory_can_be_used_by(  # noqa: D103
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> tuple[type[Block], bool] | None:
    if args.Other != get_pc().Pawn:
        return None
    if not can_item_be_equipped(obj):
        return Block, False
    return None


@hook("WillowGame.ItemCardGFxObject:SetItemCardEx", Type.POST)
def set_item_card_ex(  # noqa: D103
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    if (item := args.InventoryItem) is None:
        return
    if can_item_be_equipped(item):
        return

    obj.SetLevelRequirement(True, False, False, "Locked by Equip Locker")


@hook("WillowGame.WillowInventoryManager:InventoryShouldBeReadiedWhenEquipped")
def inventory_should_be_readied_when_equipped(  # noqa: D103
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> tuple[type[Block], bool] | None:
    if obj.Owner != get_pc().Pawn:
        return None
    if not can_item_be_equipped(args.WillowInv):
        return Block, False
    return None


def get_equipped_items() -> Iterator[Inventory]:
    """
    Gets all items the local player has equipped.

    Yields:
        All equipped items, in an arbitrary order.
    """
    if (pawn := get_pc().Pawn) is None:
        return

    inv_manager = pawn.InvManager
    for item in (inv_manager.InventoryChain, inv_manager.ItemChain):
        while item is not None:
            yield item
            item = item.Inventory


def unequip_restricted_items() -> None:
    """Unequips any restricted items the player might have equipped."""
    if (pawn := get_pc().Pawn) is None:
        return

    inv_manager = pawn.InvManager
    for item in get_equipped_items():
        if not item.CanBeUsedBy(pawn):
            inv_manager.InventoryUnreadied(item, True)


def on_enable() -> None:  # noqa: D103
    unequip_restricted_items()


mod = build_mod(options=options)

# Only add the option change handlers after constructing the mod, to avoid extra calls as it updates
# every option


def _option_change_handler[J: JSON](opt: ValueOption[J], new_val: J) -> None:
    if not mod.is_enabled:
        return
    opt.value = new_val
    unequip_restricted_items()


def _add_option_change_handlers(options: Sequence[BaseOption]) -> None:
    for opt in options:
        match opt:
            case GroupedOption() | NestedOption():
                _add_option_change_handlers(opt.children)
            case ValueOption():
                opt.on_change = _option_change_handler
            case _:
                pass


_add_option_change_handlers(options)

import typing

import unrealsdk
from unrealsdk.unreal import UObject, WeakPointer

from .replacement_lists import PartSlot

type InventoryBalanceDefinition = UObject
type ManufacturerDefinition = UObject
type WillowInventory = UObject
type WillowPawn = UObject

__all__: tuple[str, ...] = ("create_category_item",)

bank_bal_def: WeakPointer[InventoryBalanceDefinition] = WeakPointer()
cash_manufacturer: WeakPointer[ManufacturerDefinition] = WeakPointer()

slot_bal_defs: dict[PartSlot, InventoryBalanceDefinition] = {}

_slot_names: tuple[PartSlot, ...] = typing.get_args(PartSlot.__value__)
for slot in _slot_names:
    try:
        slot_bal_defs[slot] = unrealsdk.find_object(
            "InventoryBalanceDefinition",
            f"GD_CustomItems.Items.CustomItem_vendor_edit_{slot}",
        )
        continue
    except ValueError:
        pass


def get_bal_def(slot: PartSlot) -> InventoryBalanceDefinition:
    """
    Gets the InventoryBalanceDefinition to use for the given slot, creating it if needed.

    Args:
        slot: The slot to get.
    Returns:
        The slot's inventory balance definition
    """
    if slot in slot_bal_defs:
        return slot_bal_defs[slot]

    global bank_bal_def
    if (base_balance := bank_bal_def()) is None:
        base_balance = unrealsdk.find_object(
            "InventoryBalanceDefinition",
            "GD_CustomItems.Items.CustomItem_SDU_Bank",
        )
        bank_bal_def = WeakPointer(base_balance)

    global cash_manufacturer
    if (manufacturer := cash_manufacturer()) is None:
        manufacturer = unrealsdk.find_object(
            "ManufacturerDefinition",
            "GD_Currency.Manufacturers.Cash_Manufacturer",
        )
        cash_manufacturer = WeakPointer(manufacturer)

    new_balance = unrealsdk.construct_object(
        base_balance.Class,
        base_balance.Outer,
        f"CustomItem_vendor_edit_{slot}",
        0x4000,
        base_balance,
    )
    new_balance.Manufacturers[0].Manufacturer = manufacturer

    new_part_list = unrealsdk.construct_object(
        (base_part_list := new_balance.PartListCollection).Class,
        base_part_list.Outer,
        f"PartCollection_vendor_edit_{slot}",
        0,
        base_part_list,
    )
    new_balance.PartListCollection = new_part_list

    new_part = unrealsdk.construct_object(
        (base_part := (alpha_part_data := new_part_list.AlphaPartData.WeightedParts[0]).Part).Class,
        base_part.Outer,
        f"Part_vendor_edit_{slot}",
        0,
        base_part,
    )
    alpha_part_data.Part = new_part
    new_part_list.MaterialPartData.WeightedParts[0].Part = new_part

    new_part.CustomPresentations.clear()

    new_prefix = unrealsdk.construct_object(
        (base_prefix := new_part.PrefixList[0]).Class,
        base_prefix.Outer,
        f"Prefix_vendor_edit_{slot}",
        0,
        base_prefix,
    )
    new_part.PrefixList = (new_prefix,)
    new_prefix.PartName = slot

    slot_bal_defs[slot] = new_balance
    return new_balance


def create_category_item(slot: PartSlot, owner: WillowPawn) -> WillowInventory:
    """
    Creates a dummy item to use for a category for the given slot.

    Args:
        slot: The slot to create an item for.
        owner: The pawn to set as the item's owner.
    """
    _, spawned = unrealsdk.find_class(
        "ItemPool",
    ).ClassDefaultObject.SpawnBalancedInventoryFromInventoryBalanceDefinition(
        InvBalanceDefinition=get_bal_def(slot),
        Quantity=1,
        GameStage=1,
        AwesomeLevel=0,
        ContextSource=owner,
        SpawnedInventory=(),
    )
    return spawned[0]

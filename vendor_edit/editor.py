from collections.abc import Sequence
from contextlib import suppress
from typing import TYPE_CHECKING, Any

import unrealsdk
from mods_base import BaseOption, BoolOption, get_pc, hook
from unrealsdk.hooks import Type
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

from . import vendor_movie
from .dummy_items import DummyItem
from .replacement_lists import create_replacement_list

if TYPE_CHECKING:
    from enum import auto

    from unrealsdk.unreal._uenum import UnrealEnum  # pyright: ignore[reportMissingModuleSource]

    class EBackButtonScreen(UnrealEnum):
        CS_None = auto()
        CS_MissionLog = auto()
        CS_Map = auto()
        CS_Inventory = auto()
        CS_Skills = auto()
        CS_Challenges = auto()
        CS_MAX = auto()

    class EQuickWeaponSlot(UnrealEnum):
        QuickSelectNone = auto()
        QuickSelectUp = auto()
        QuickSelectDown = auto()
        QuickSelectLeft = auto()
        QuickSelectRight = auto()
        EQuickWeaponSlot_MAX = auto()

else:
    EBackButtonScreen = unrealsdk.find_enum("EBackButtonScreen")
    EQuickWeaponSlot = unrealsdk.find_enum("EQuickWeaponSlot")

type ItemDefinitionData = WrappedStruct
type WillowInventory = UObject

WILLOW_WEAPON = unrealsdk.find_class("WillowWeapon")

__all__: tuple[str, ...] = (
    "open_editor_menu",
    "options",
    "reopen_inventory",
)


reopen_inv_option = BoolOption(
    "Reopen Inventory After Editing",
    False,
    description="If to re-open your inventory after you finish editing an item.",
)


def open_editor_menu(item: WillowInventory) -> None:
    """
    Opens the editor menu for the given item.

    Args:
        item: The item to edit.
    """
    show_categories_menu(item)


def reopen_inventory() -> None:
    """Re-opens the inventory menu, if required."""
    if not reopen_inv_option.value:
        return
    pc = get_pc()
    pc.QuickAccessScreen = EBackButtonScreen.CS_Inventory
    pc.GetPlayerViewportClient().ViewportUI.RunStatusMenu(pc)


def show_categories_menu(item: WillowInventory) -> None:
    # We create a new replacement list every time we show the categories, since if we're coming from
    # having just edited parts, any cached list might be out of date
    replacements = create_replacement_list(item)

    def on_purchase(purchased: WillowInventory) -> None:
        slot = DummyItem.from_balance(purchased.DefinitionData.BalanceDefinition)

        show_part_menu(item, replacements.create_replacements_for_slot(slot), slot)

    vendor_movie.show(
        items=[slot.spawn(item.Owner) for slot in replacements.get_slots()],
        iotd=item,
        on_purchase=on_purchase,
        on_cancel=reopen_inventory,
    )


def show_part_menu(
    item: WillowInventory,
    replacements: Sequence[WillowInventory],
    slot: DummyItem,
) -> None:
    def on_purchase(purchased: WillowInventory) -> None:
        def_data = purchased.DefinitionData
        # Setting unique id to 0 causes the game to re-randomize it
        # We want this so that any other systems (e.g. Sanity Saver) treat this as a new item
        def_data.UniqueId = 0

        new_item = replace_item_def_data(item, def_data)

        if slot is DummyItem.LEVEL:
            # Editing level is a bit of an iterative process, so immediately reopen the level menu
            replacements = create_replacement_list(new_item)
            show_part_menu(
                new_item,
                replacements.create_replacements_for_slot(DummyItem.LEVEL),
                DummyItem.LEVEL,
            )
        else:
            # Otherwise go back to the catgory menu
            show_categories_menu(new_item)

    vendor_movie.show(
        items=replacements,
        iotd=item,
        on_purchase=on_purchase,
        on_cancel=lambda: show_categories_menu(item),
    )


def replace_item_def_data(
    item: WillowInventory,
    def_data: ItemDefinitionData,
) -> WillowInventory:
    """
    Replaces an item from the player's inventory with a new one using the given def data..

    Args:
        item: The base item to replace.
        def_data: The new definition data to use.
    Returns:
        The new item.
    """

    # So the inventory is implemented in an insane way.
    # Basically any time items move, they're completely deleted and recreated from their def data.
    # This means we need to be very careful about what we actually have a reference to, and what
    # order we do everything in.

    # Firstly, gather all the data off of the original item that we need. Some of this will get
    # changed as soon as we remove it.
    is_weapon = False
    quick_slot = EQuickWeaponSlot.QuickSelectNone
    with suppress(AttributeError):
        quick_slot = item.QuickSelectSlot
        is_weapon = True
    quantity = 1
    with suppress(AttributeError):
        quantity = item.Quantity
    mark = item.Mark
    was_ready = item.bReadied

    inv_manager = (owner := item.Owner).InvManager

    # Now remove the original item
    inv_manager.RemoveFromInventory(item)
    # Gearbox making things difficult: the above works for all items, and equipped weapons, but not
    # weapons in the backpack
    if is_weapon:
        inv_manager.RemoveInventoryFromBackpack(item)
        inv_manager.UpdateBackpackInventoryCount()

    # Another awkward part about items constantly getting recreated is it means we can't cleanly get
    # a reference to the new item, since anything we put in will change.
    # Instead we need this digusting hook abuse.
    created_item: UObject | None = None  # type: ignore

    @hook("Engine.WillowInventory:SetMark", Type.POST)
    def inv_set_mark(
        obj: UObject,
        _args: WrappedStruct,
        _ret: Any,
        _func: BoundFunction,
    ) -> None:
        nonlocal created_item
        created_item = obj

    try:
        inv_set_mark.enable()

        # Explictly make sure *not* to ready the item yet, even if we needed it
        # These calls will create a new item, to be caught by the hook
        if is_weapon:
            inv_manager.ClientAddWeaponToBackpack(
                DefinitionData=def_data,
                Mark=mark,
                bReadyAfterAdd=False,
            )
        else:
            inv_manager.ClientAddItemToBackpack(
                DefinitionData=def_data,
                Quantity=quantity,
                Mark=mark,
                bReadyAfterAdd=False,
            )

        # Type checker doesn't realize this may have changed
        if TYPE_CHECKING:
            created_item = object()  # type: ignore
        if created_item is None:
            raise RuntimeError("failed to spawn new item")

        # If the item was ready, but we increased its level, we might no longer be able to ready it
        if was_ready and created_item.CanBeUsedBy(owner):
            # This call also makes a new item. The reference we currenly have will get queued for
            # deletion after this call, we want a reference to the new item this creates in the
            # following code. Luckily, turns out we can use the exact same code.

            # We're free to pass a quick slot even if this is an item
            inv_manager.ReadyBackpackInventory(created_item, quick_slot)
    finally:
        inv_set_mark.disable()

    if TYPE_CHECKING:
        created_item = object()  # type: ignore
    if created_item is None:
        raise RuntimeError("failed to spawn new item")

    # Finally fix up the owner, this is used by the replacement lists
    created_item.Owner = owner
    return created_item


options: tuple[BaseOption, ...] = (reopen_inv_option,)

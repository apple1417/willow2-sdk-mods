from collections.abc import Sequence
from typing import TYPE_CHECKING

import unrealsdk
from mods_base import BaseOption, BoolOption, get_pc
from unrealsdk.unreal import UObject

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

else:
    EBackButtonScreen = unrealsdk.find_enum("EBackButtonScreen")

type WillowInventory = UObject

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

        show_part_menu(item, replacements.create_replacements_for_slot(slot))

    vendor_movie.show(
        items=[slot.spawn(item.Owner) for slot in replacements.get_slots()],
        iotd=item,
        on_purchase=on_purchase,
        on_cancel=reopen_inventory,
    )


def show_part_menu(item: WillowInventory, replacements: Sequence[WillowInventory]) -> None:
    def on_purchase(purchased: WillowInventory) -> None:
        def_data = purchased.DefinitionData
        # Setting unique id to 0 causes the game to re-randomize it
        # We want this so that any other systems (e.g. Sanity Saver) treat this as a new item
        def_data.UniqueId = 0

        item.InitializeFromDefinitionData(
            NewDefinitionData=def_data,
            InAdditionalQueryInterfaceSource=item.Owner,
            bForceSelectNameParts=True,
        )
        show_categories_menu(item)

    vendor_movie.show(
        items=replacements,
        iotd=item,
        on_purchase=on_purchase,
        on_cancel=lambda: show_categories_menu(item),
    )


options: tuple[BaseOption, ...] = (reopen_inv_option,)

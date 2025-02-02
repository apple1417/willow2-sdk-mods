from mods_base import get_pc
from ui_utils import clipboard_paste, show_chat_message
from unrealsdk.unreal import UObject

from . import vendor_movie
from .dummy_items import DummyItem
from .editor import open_editor_menu, reopen_inventory
from .item_codes import spawn_item_from_code

type WillowInventory = UObject

__all__: tuple[str, ...] = ("open_spawner_menu",)


def open_spawner_menu() -> None:
    """Opens the item spawner menu."""
    show_manufacturer_list()


def show_manufacturer_list() -> None:
    owner = get_pc().Pawn

    def on_purchase(purchased: WillowInventory) -> None:
        try:
            slot = DummyItem.from_balance(purchased.DefinitionData.BalanceDefinition)
        except ValueError:
            slot = None

        if slot is DummyItem.PASTE_CODE:
            code = clipboard_paste()
            if code is not None:
                item = spawn_item_from_code(code, owner)
                if item is not None:
                    owner.InvManager.AddInventoryToBackpack(item)
                    open_editor_menu(item)
                    return

            show_chat_message(
                "Couldn't find valid item code in clipboard",
                user="[Vendor Edit]",
                timestamp=None,
            )
            show_manufacturer_list()
            return

    vendor_movie.show(
        items=[DummyItem.PASTE_CODE.spawn(owner)],
        iotd=None,
        on_purchase=on_purchase,
        on_cancel=reopen_inventory,
    )

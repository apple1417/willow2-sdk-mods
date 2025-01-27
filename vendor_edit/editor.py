from collections.abc import Callable

from unrealsdk.unreal import UObject

from . import vendor_movie
from .category_items import create_category_item
from .replacement_lists import create_replacement_list

type WillowInventory = UObject

__all__: tuple[str, ...] = ("open_editor_menu",)


def open_editor_menu(item: WillowInventory, on_finish: Callable[[], None] | None = None) -> None:
    """
    Opens the editor menu for the given item.

    Calling code should previously have checked `can_create_replacements()` to make sure this item
    is valid.

    Args:
        item: The item to edit.
        on_finish: An optional callback to run when editing's finished.
    """
    replacements = create_replacement_list(item)

    def on_purchase(weap: UObject) -> None:
        print(weap.DefinitionData.BarrelPartDefinition)
        open_editor_menu(item)  # type: ignore

    vendor_movie.show(
        items=[create_category_item(slot, item.Owner) for slot in replacements.get_slots()],
        iotd=None,
        on_purchase=on_purchase,
        on_cancel=on_finish,
    )

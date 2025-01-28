from collections.abc import Callable, Sequence

from unrealsdk.unreal import UObject

from . import vendor_movie
from .dummy_items import DummyItem
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
    show_categories_menu(item, on_finish)


def show_categories_menu(
    item: WillowInventory,
    on_finish: Callable[[], None] | None = None,
) -> None:
    # We create a new replacement list every time we show the categories, since if we're coming from
    # having just edited parts, any cached list might be out of date
    replacements = create_replacement_list(item)

    def on_purchase(purchased: WillowInventory) -> None:
        slot = DummyItem.from_balance(purchased.DefinitionData.BalanceDefinition)
        show_part_menu(
            item,
            replacements.create_replacements_for_slot(slot),
            on_finish,
        )

    vendor_movie.show(
        items=[slot.spawn(item.Owner) for slot in replacements.get_slots()],
        iotd=item,
        on_purchase=on_purchase,
        on_cancel=on_finish,
    )


def show_part_menu(
    item: WillowInventory,
    replacements: Sequence[WillowInventory],
    on_finish: Callable[[], None] | None = None,
) -> None:
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
        show_categories_menu(item, on_finish)

    vendor_movie.show(
        items=replacements,
        iotd=item,
        on_purchase=on_purchase,
        on_cancel=lambda: show_categories_menu(item, on_finish),
    )

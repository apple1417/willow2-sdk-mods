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
        if slot is DummyItem.LEVEL:
            show_level_menu(item, on_finish)
            return

        show_part_menu(
            item,
            replacements.create_replacements_for_slot(slot),
            on_finish,
        )

    vendor_movie.show(
        items=(
            *(slot.spawn(item.Owner) for slot in replacements.get_slots()),
            DummyItem.LEVEL.spawn(item.Owner),
        ),
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


def show_level_menu(
    item: WillowInventory,
    on_finish: Callable[[], None] | None = None,
) -> None:
    def on_purchase(purchased: WillowInventory) -> None:
        slot = DummyItem.from_balance(purchased.DefinitionData.BalanceDefinition)

        def_data = item.DefinitionData
        level = def_data.ManufacturerGradeIndex

        match slot:
            case DummyItem.LEVEL_MAX:
                current_level = (owner := item.Owner).GetExpLevel()
                op_levels = owner.Controller.PlayerReplicationInfo.NumOverpowerLevelsUnlocked
                level = current_level + op_levels
            case DummyItem.LEVEL_PLUS_10:
                level += 10
            case DummyItem.LEVEL_PLUS_1:
                level += 1
            case DummyItem.LEVEL_MINUS_1:
                level -= 1
            case DummyItem.LEVEL_MINUS_10:
                level -= 10
            case _:
                raise RuntimeError(f"got unexpected slot: {slot}")

        level = max(level, 0)
        def_data.ManufacturerGradeIndex = level
        def_data.GameStage = level
        def_data.UniqueId = 0

        item.InitializeFromDefinitionData(
            NewDefinitionData=def_data,
            InAdditionalQueryInterfaceSource=item.Owner,
            bForceSelectNameParts=True,
        )
        show_level_menu(item, on_finish)

    vendor_movie.show(
        items=[
            i.spawn(item.Owner)
            for i in (
                DummyItem.LEVEL_MAX,
                DummyItem.LEVEL_PLUS_10,
                DummyItem.LEVEL_PLUS_1,
                DummyItem.LEVEL_MINUS_1,
                DummyItem.LEVEL_MINUS_10,
            )
        ],
        iotd=item,
        on_purchase=on_purchase,
        on_cancel=lambda: show_categories_menu(item, on_finish),
    )

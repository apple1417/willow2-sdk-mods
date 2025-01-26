from typing import TYPE_CHECKING

import unrealsdk
from mods_base import build_mod, get_pc, keybind

from . import bugfix, vendor_movie

if TYPE_CHECKING:
    from enum import auto

    from unrealsdk.unreal._uenum import UnrealEnum  # pyright: ignore[reportMissingModuleSource]

    class EPlayerDroppability(UnrealEnum):
        EPD_Droppable = auto()
        EPD_Sellable = auto()
        EPD_CannotDropOrSell = auto()
        EPD_MAX = auto()
else:
    EPlayerDroppability = unrealsdk.find_enum("EPlayerDroppability")


@keybind("go")
def go() -> None:  # noqa: D103
    _, readied_weapons, unreadied_weapons, all_items = get_pc().GetInventoryLists(
        (),
        (),
        (),
        EPlayerDroppability.EPD_CannotDropOrSell,
    )
    all_items = readied_weapons + unreadied_weapons + all_items

    vendor_movie.show(items=all_items, iotd=all_items[0])


build_mod(hooks=(*bugfix.hooks,))

from mods_base import build_mod, get_pc, keybind
from unrealsdk.unreal import UObject

from . import bugfix, vendor_movie
from .category_items import create_category_item
from .replacement_lists import create_replacement_list


@keybind("go")
def go() -> None:  # noqa: D103
    weap = get_pc().Pawn.Weapon

    replacements = create_replacement_list(weap)

    def on_purchase(weap: UObject) -> None:
        print(weap.DefinitionData.BarrelPartDefinition)
        go.callback()  # type: ignore

    vendor_movie.show(
        items=[create_category_item(slot, weap.Owner) for slot in replacements.get_slots()],
        iotd=None,
        on_purchase=on_purchase,
        on_cancel=lambda: print("cancel"),
    )


build_mod(hooks=(*bugfix.hooks,))

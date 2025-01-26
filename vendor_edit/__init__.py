from copy import copy
from typing import TYPE_CHECKING

import unrealsdk
from mods_base import build_mod, get_pc, keybind
from unrealsdk.unreal import UObject

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


WEAPON_SLOTS: tuple[str, ...] = (
    # "WeaponTypeDefinition",  # WeaponTypeDefinition
    # "BalanceDefinition",  # InventoryBalanceDefinition
    # "ManufacturerDefinition",  # ManufacturerDefinition
    # "ManufacturerGradeIndex",  # int
    "BodyPartDefinition",  # WeaponPartDefinition
    "GripPartDefinition",  # WeaponPartDefinition
    "BarrelPartDefinition",  # WeaponPartDefinition
    "SightPartDefinition",  # WeaponPartDefinition
    "StockPartDefinition",  # WeaponPartDefinition
    "ElementalPartDefinition",  # WeaponPartDefinition
    "Accessory1PartDefinition",  # WeaponPartDefinition
    "Accessory2PartDefinition",  # WeaponPartDefinition
    "MaterialPartDefinition",  # WeaponPartDefinition
    # "PrefixPartDefinition",  # WeaponNamePartDefinition
    # "TitlePartDefinition",  # WeaponNamePartDefinition
    # "GameStage",  # int
    # "UniqueId",  # int
)


@keybind("go")
def go() -> None:  # noqa: D103
    weap = get_pc().Pawn.Weapon

    new_weapons: list[UObject] = []

    def_data = weap.DefinitionData
    part_list = def_data.BalanceDefinition.RuntimePartListCollection

    slot = part_list.BarrelPartData
    original_part = def_data.BarrelPartDefinition
    for part_data in slot.WeightedParts:
        if part_data.part == original_part:
            continue

        new_def = copy(def_data)
        new_def.BarrelPartDefinition = part_data.Part

        new_weapons.append(weap.CreateWeaponFromDef(new_def, weap.Owner, True))

    def on_purchase(weap: UObject) -> None:
        print(weap.DefinitionData.BarrelPartDefinition)
        go.callback()  # type: ignore

    vendor_movie.show(
        items=new_weapons,
        iotd=weap,
        on_purchase=on_purchase,
        on_cancel=lambda: print("cancel"),
    )


build_mod(hooks=(*bugfix.hooks,))

from dataclasses import KW_ONLY, dataclass
from typing import TYPE_CHECKING

import unrealsdk
from mods_base import BoolOption, Game

from . import Inventory, Restriction

if TYPE_CHECKING:
    from enum import auto

    from unrealsdk.unreal._uenum import UnrealEnum  # pyright: ignore[reportMissingModuleSource]

    class EWeaponType(UnrealEnum):
        WT_Pistol = auto()
        WT_Shotgun = auto()
        WT_SMG = auto()
        WT_SniperRifle = auto()
        WT_AssaultRifle = auto()
        WT_RocketLauncher = auto()
        # TPS ONLY:
        # WT_Laser = auto()  # noqa: ERA001

else:
    EWeaponType = unrealsdk.find_enum("EWeaponType")


@dataclass
class BaseWeaponItemTypeOption(BoolOption):
    value: bool = True
    true_text: str | None = "Allowed"
    false_text: str | None = "Not Allowed"

    _: KW_ONLY
    supported_games: Game = Game.Willow2

    def __post_init__(self) -> None:
        super().__post_init__()
        self.is_hidden = Game.get_current() not in self.supported_games
        self.description = f"Should you be able to equip {self.display_name}."


@dataclass
class WeaponOption(BaseWeaponItemTypeOption):
    _: KW_ONLY
    weapon_type: EWeaponType


@dataclass
class ItemOption(BaseWeaponItemTypeOption):
    _: KW_ONLY
    class_name: str


ALL_WEAPON_TYPES: tuple[WeaponOption, ...] = (
    WeaponOption("Pistols", weapon_type=EWeaponType.WT_Pistol),
    WeaponOption("Shotguns", weapon_type=EWeaponType.WT_Shotgun),
    WeaponOption("SMGs", weapon_type=EWeaponType.WT_SMG),
    WeaponOption("Snipers", weapon_type=EWeaponType.WT_SniperRifle),
    WeaponOption("Rifles", weapon_type=EWeaponType.WT_AssaultRifle),
    WeaponOption("Launchers", weapon_type=EWeaponType.WT_RocketLauncher),
    WeaponOption("Lasers", weapon_type=EWeaponType(6), supported_games=Game.TPS),
)
WEAPON_TYPE_MAP = {opt.weapon_type: opt for opt in ALL_WEAPON_TYPES if not opt.is_hidden}

ALL_ITEM_TYPES: tuple[ItemOption, ...] = (
    ItemOption("Shields", class_name="WillowShield"),
    ItemOption("Grenade Mods", class_name="WillowGrenadeMod"),
    ItemOption("Class Mods", class_name="WillowClassMod"),
    ItemOption("Relics", class_name="WillowArtifact", supported_games=Game.BL2 | Game.AoDK),
    ItemOption("Oz Kits", class_name="WillowArtifact", supported_games=Game.TPS),
)
ITEM_CLASS_MAP = {opt.class_name: opt for opt in ALL_ITEM_TYPES if not opt.is_hidden}


def can_item_be_equipped(item: Inventory) -> bool:  # noqa: D103
    if item.Class.Name == "WillowWeapon":
        if (weap_def := item.DefinitionData.WeaponTypeDefinition) is None:
            return True
        if (weap_type := weap_def.WeaponType) not in WEAPON_TYPE_MAP:
            return True
        return WEAPON_TYPE_MAP[weap_type].value

    if (cls_name := item.Class.Name) not in ITEM_CLASS_MAP:
        return True
    return ITEM_CLASS_MAP[cls_name].value


weapon_item_type_restriction = Restriction(
    "Weapon/Item Type",
    "Lock items based on their type.",
    ALL_WEAPON_TYPES + ALL_ITEM_TYPES,
    can_item_be_equipped,
)

from __future__ import annotations

from abc import ABC, abstractmethod
from copy import copy
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Literal

import unrealsdk
from unrealsdk.unreal import UObject, WeakPointer

if TYPE_CHECKING:
    from collections.abc import Collection, Sequence

type WillowInventory = UObject
type WillowWeapon = UObject
type ManufacturerDefinition = UObject
type WeaponPartDefinition = UObject

type PartSlot = Literal[
    "Manufacturer",
    "Material",
    # === Weapons ===
    "Body",
    "Grip",
    "Barrel",
    "Sight",
    "Stock",
    "Element",
    "Accessory",
    "Alt Accessory",
    # === Shields ===
    # "Body",
    "Battery",
    # "Accessory",
    "Capacitor",
    # === Grenades ===
    "Payload",
    "Delivery",
    "Trigger",
    # "Accessory",
    "Damage",
    "Blast Radius",
    "Child Count",
    "Status Damage",
    # === Class Mods ===
    "Specialization",
    "Primary",
    "Secondary",
    "Penalty",
    # === Class Mods ===
    "Upgrade",
    # === Misc Items ===
    "Alpha",
    "Beta",
    "Gamma",
    "Delta",
    "Epsilon",
    "Zeta",
    "Eta",
    "Theta",
]

__all__: tuple[str, ...] = (
    "PartSlot",
    "can_create_replacements",
    "create_replacement_list",
)

WILLOW_WEAPON = unrealsdk.find_class("WillowWeapon")


def can_create_replacements(item: WillowInventory) -> bool:
    """
    Checks if we support creating replacements for the given item.

    Args:
        item: The item to check.
    Returns:
        True if replacements are supported, and `create_replacement_list()` may be called.
    """
    cls = item.Class
    if cls._inherits(WILLOW_WEAPON):
        return True

    _ = "dummy"
    return False


def create_replacement_list(item: WillowInventory) -> AbstractReplacementList:
    """
    Creates an appropriate replacement list for the given item.

    Args:
        item: The item to create replacements for.
    Returns:
        The new replacement list.
    """
    cls = item.Class
    if cls._inherits(WILLOW_WEAPON):
        return WeaponReplacements(item)

    raise ValueError(f"Unable to create replacement list for {item}")


@dataclass
class AbstractReplacementList(ABC):
    @abstractmethod
    def get_slots(self) -> Collection[PartSlot]:
        """
        Gets the part slots this item type supports.

        Returns:
            The list of slots.
        """
        raise NotImplementedError

    @abstractmethod
    def create_replacements_for_slot(self, slot: PartSlot) -> Sequence[WillowInventory]:
        """
        For a given part slot, creates an item for each possible replacement part.

        Args:
            slot: The part slot to create replacements for.
        Returns:
            The list of slots.
        """
        raise NotImplementedError


@dataclass
class WeaponReplacements(AbstractReplacementList):
    @dataclass(frozen=True)
    class SlotNames:
        attr: str
        def_data: str
        part_list: str

    @dataclass(frozen=True)
    class ManufacturerSlotNames:
        attr: str
        def_data: str

    BASIC_SLOTS: ClassVar[dict[PartSlot, SlotNames]] = {
        "Body": SlotNames("bodies", "BodyPartDefinition", "BodyPartData"),
        "Grip": SlotNames("grips", "GripPartDefinition", "GripPartData"),
        "Barrel": SlotNames("barrels", "BarrelPartDefinition", "BarrelPartData"),
        "Sight": SlotNames("sights", "SightPartDefinition", "SightPartData"),
        "Stock": SlotNames("stocks", "StockPartDefinition", "StockPartData"),
        "Element": SlotNames("elements", "ElementalPartDefinition", "ElementalPartData"),
        "Accessory": SlotNames("accessory1s", "Accessory1PartDefinition", "Accessory1PartData"),
        "Alt Accessory": SlotNames("accessory2s", "Accessory2PartDefinition", "Accessory2PartData"),
        "Material": SlotNames("materials", "MaterialPartDefinition", "MaterialPartData"),
    }
    MANUFACTURER_FRIENDLY_NAME: ClassVar[PartSlot] = "Manufacturer"
    MANUFACTURER_SLOT_NAMES: ClassVar[ManufacturerSlotNames] = ManufacturerSlotNames(
        "manufacturers",
        "ManufacturerDefinition",
    )

    weapon: WeakPointer[WillowWeapon]

    manufacturers: list[ManufacturerDefinition]

    bodies: list[WeaponPartDefinition]
    grips: list[WeaponPartDefinition]
    barrels: list[WeaponPartDefinition]
    sights: list[WeaponPartDefinition]
    stocks: list[WeaponPartDefinition]
    elements: list[WeaponPartDefinition]
    accessory1s: list[WeaponPartDefinition]
    accessory2s: list[WeaponPartDefinition]
    materials: list[WeaponPartDefinition]

    def __init__(self, weapon: WillowWeapon) -> None:
        self.weapon = WeakPointer(weapon)

        def_data = weapon.DefinitionData
        balance = def_data.BalanceDefinition
        self.manufacturers = [
            manu for entry in balance.Manufacturers if (manu := entry.Manufacturer) is not None
        ]

        part_list = balance.RuntimePartListCollection
        for slot_names in self.BASIC_SLOTS.values():
            original_part = getattr(def_data, slot_names.def_data)
            setattr(
                self,
                slot_names.attr,
                [
                    part
                    for part_slot in getattr(part_list, slot_names.part_list).WeightedParts
                    if (part := part_slot.part) != original_part
                ],
            )

    def get_slots(self) -> Collection[PartSlot]:
        slots: list[PartSlot] = []

        if self.manufacturers:
            slots.insert(0, self.MANUFACTURER_FRIENDLY_NAME)

        slots.extend(
            friendly_name
            for friendly_name, slots_names in self.BASIC_SLOTS.items()
            if getattr(self, slots_names.attr)
        )

        return slots

    def create_replacements_for_slot(self, slot: PartSlot) -> Sequence[WillowInventory]:
        weapon = self.weapon()
        if weapon is None:
            raise RuntimeError("weapon got gc'd while we were still working with it!")

        slot_names = (
            self.MANUFACTURER_SLOT_NAMES
            if slot == self.MANUFACTURER_FRIENDLY_NAME
            else self.BASIC_SLOTS[slot]
        )
        def_data = weapon.DefinitionData

        new_weapons: list[WillowWeapon] = []
        for part in getattr(self, slot_names.attr):
            new_def = copy(def_data)
            setattr(new_def, slot_names.def_data, part)

            new_weapons.append(
                weapon.CreateWeaponFromDef(
                    NewWeaponDef=new_def,
                    PlayerOwner=weapon.Owner,
                    bForceSelectNameParts=True,
                ),
            )

        return new_weapons

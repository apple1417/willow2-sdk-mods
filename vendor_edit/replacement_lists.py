from __future__ import annotations

from abc import ABC, abstractmethod
from copy import copy
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, overload

import unrealsdk
from unrealsdk.unreal import UObject, WeakPointer, WrappedStruct

from .dummy_items import DummyItem

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

type WillowInventory = UObject
type WillowItem = UObject
type WillowWeapon = UObject
type ManufacturerDefinition = UObject
type ItemPartDefinition = UObject
type WeaponPartDefinition = UObject
type ItemDefinitionData = WrappedStruct
type WeaponDefinitionData = WrappedStruct


__all__: tuple[str, ...] = (
    "can_create_replacements",
    "create_replacement_list",
)

WILLOW_WEAPON = unrealsdk.find_class("WillowWeapon")
WILLOW_SHIELD = unrealsdk.find_class("WillowShield")


def can_create_replacements(item: WillowInventory) -> bool:
    """
    Checks if we support creating replacements for the given item.

    Args:
        item: The item to check.
    Returns:
        True if replacements are supported, and `create_replacement_list()` may be called.
    """
    cls = item.Class
    return any(
        cls._inherits(allowed_class)
        for allowed_class in (
            WILLOW_WEAPON,
            WILLOW_SHIELD,
        )
    )


def create_replacement_list(item: WillowInventory) -> IReplacementList:
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
    if cls._inherits(WILLOW_SHIELD):
        return ShieldReplacements(item)

    raise ValueError(f"Unable to create replacement list for {item}")


@dataclass
class IReplacementList(ABC):
    @abstractmethod
    def get_slots(self) -> Sequence[DummyItem]:
        """
        Gets the dummy items representing the part slots this item type supports.

        Returns:
            The list of slots.
        """

    @abstractmethod
    def create_replacements_for_slot(self, slot: DummyItem) -> Sequence[WillowInventory]:
        """
        For a given part slot, creates an item for each possible replacement part.

        Args:
            slot: The part slot to create replacements for.
        Returns:
            The list of slots.
        """
        raise NotImplementedError


# Using another abstract class for all the private interfaces
class BaseReplacementList(IReplacementList):
    @dataclass(frozen=True)
    class SlotNames:
        attr: str
        def_data: str

    MANUFACTURER: ClassVar[SlotNames] = SlotNames("manufacturers", "ManufacturerDefinition")
    LEVEL: ClassVar[SlotNames] = SlotNames("levels", "ManufacturerGradeIndex")

    inv: WeakPointer[WillowInventory]

    manufacturers: set[ManufacturerDefinition]
    levels: set[int]

    def __init__(self, inv: WillowInventory) -> None:
        self.inv = WeakPointer(inv)

        original_manu = (def_data := inv.DefinitionData).ManufacturerDefinition
        self.manufacturers = {
            manu
            for entry in def_data.BalanceDefinition.Manufacturers
            if (manu := entry.Manufacturer) is not None and manu != original_manu
        }

        player_level = (owner := inv.Owner).GetExpLevel()
        op_levels = (
            controller := owner.Controller
        ).PlayerReplicationInfo.NumOverpowerLevelsUnlocked
        max_level = (
            controller.GetMaximumPossiblePlayerLevelCap()
            + controller.GetMaximumPossibleOverpowerModifier()
        )

        original_level = inv.DefinitionData.ManufacturerGradeIndex
        self.levels = {
            clamped
            for x in (
                player_level + op_levels,
                original_level + 10,
                original_level + 5,
                original_level + 1,
                original_level - 1,
                original_level - 5,
                original_level - 10,
            )
            if (clamped := max(1, min(x, max_level))) != original_level
        }

        self.init_basic_slots(inv)

    def get_slots(self) -> Sequence[DummyItem]:
        slots: list[DummyItem] = []

        if self.manufacturers:
            slots.append(DummyItem.MANUFACTURER)

        if self.levels:
            slots.append(DummyItem.LEVEL)

        slots.extend(
            friendly_name
            for friendly_name, slots_names in self.get_basic_slots().items()
            if getattr(self, slots_names.attr)
        )

        return slots

    def create_replacements_for_slot(self, slot: DummyItem) -> Sequence[WillowInventory]:
        inv = self.inv()
        if inv is None:
            raise RuntimeError("item got gc'd while we were still working with it!")

        slot_names: BaseReplacementList.SlotNames
        match slot:
            case DummyItem.MANUFACTURER:
                slot_names = self.MANUFACTURER
            case DummyItem.LEVEL:
                slot_names = self.LEVEL
            case _:
                slot_names = self.get_basic_slots()[slot]

        def_data = inv.DefinitionData
        new_items: list[WillowInventory] = []
        for part in getattr(self, slot_names.attr):
            new_def = copy(def_data)
            setattr(new_def, slot_names.def_data, part)

            # Keep game stage synced - this is general good practice, and we explictly want it when
            # editing level
            new_def.GameStage = new_def.ManufacturerGradeIndex

            new_items.append(self.create_from_def_data(inv, new_def))

        return new_items

    @classmethod
    @abstractmethod
    def get_basic_slots(cls) -> Mapping[DummyItem, BaseReplacementList.SlotNames]:
        """
        Gets a dict mapping a category dummy item to the basic slots from the item's defintion data.

        Returns:
            The basic slots dict.
        """
        raise NotImplementedError

    @abstractmethod
    def init_basic_slots(self, inv: WillowInventory) -> None:
        """
        Initalizes the fields on this object which depend on the basic slots.

        Args:
            inv: The inventory item to initalize based off of.
        """
        raise NotImplementedError

    @overload
    @staticmethod
    def create_from_def_data(inv: WillowItem, def_data: ItemDefinitionData) -> WillowInventory: ...
    @overload
    @staticmethod
    def create_from_def_data(  # type: ignore
        inv: WillowWeapon,
        def_data: WeaponDefinitionData,
    ) -> WillowInventory: ...

    @staticmethod
    @abstractmethod
    def create_from_def_data(
        inv: WillowItem | WillowWeapon,
        def_data: ItemDefinitionData | WeaponDefinitionData,
    ) -> WillowInventory:
        """
        Creates a new item from it's definition data.

        Args:
            inv: The item to base the new item on.
            def_data: The new definition data.
        Returns:
            The new item.
        """
        raise NotImplementedError


@dataclass
class WeaponReplacements(BaseReplacementList):
    @dataclass(frozen=True)
    class ExtendedSlotNames(BaseReplacementList.SlotNames):
        part_list: str

    BASIC_SLOTS: ClassVar[dict[DummyItem, ExtendedSlotNames]] = {
        DummyItem.WEAP_BODY: ExtendedSlotNames("bodies", "BodyPartDefinition", "BodyPartData"),
        DummyItem.WEAP_GRIP: ExtendedSlotNames("grips", "GripPartDefinition", "GripPartData"),
        DummyItem.WEAP_BARREL: ExtendedSlotNames(
            "barrels",
            "BarrelPartDefinition",
            "BarrelPartData",
        ),
        DummyItem.WEAP_SIGHT: ExtendedSlotNames("sights", "SightPartDefinition", "SightPartData"),
        DummyItem.WEAP_STOCK: ExtendedSlotNames("stocks", "StockPartDefinition", "StockPartData"),
        DummyItem.WEAP_ELEMENT: ExtendedSlotNames(
            "elements",
            "ElementalPartDefinition",
            "ElementalPartData",
        ),
        DummyItem.WEAP_ACCESSORY: ExtendedSlotNames(
            "accessory1s",
            "Accessory1PartDefinition",
            "Accessory1PartData",
        ),
        DummyItem.WEAP_ALT_ACCESSORY: ExtendedSlotNames(
            "accessory2s",
            "Accessory2PartDefinition",
            "Accessory2PartData",
        ),
        DummyItem.MATERIAL: ExtendedSlotNames(
            "materials",
            "MaterialPartDefinition",
            "MaterialPartData",
        ),
    }

    bodies: set[WeaponPartDefinition]
    grips: set[WeaponPartDefinition]
    barrels: set[WeaponPartDefinition]
    sights: set[WeaponPartDefinition]
    stocks: set[WeaponPartDefinition]
    elements: set[WeaponPartDefinition]
    accessory1s: set[WeaponPartDefinition]
    accessory2s: set[WeaponPartDefinition]
    materials: set[WeaponPartDefinition]

    def __init__(self, inv: WillowInventory) -> None:
        super().__init__(inv)

    @classmethod
    def get_basic_slots(cls) -> Mapping[DummyItem, BaseReplacementList.SlotNames]:
        return cls.BASIC_SLOTS

    def init_basic_slots(self, inv: WillowInventory) -> None:
        part_list_collection = (
            def_data := inv.DefinitionData
        ).BalanceDefinition.RuntimePartListCollection
        for slot_names in self.BASIC_SLOTS.values():
            part_list = getattr(part_list_collection, slot_names.part_list)
            if not part_list.bEnabled:
                setattr(self, slot_names.attr, set())
                continue

            original_part = getattr(def_data, slot_names.def_data)
            setattr(
                self,
                slot_names.attr,
                {
                    part
                    for part_slot in part_list.WeightedParts
                    if (part := part_slot.Part) != original_part
                },
            )

    @staticmethod
    def create_from_def_data(inv: WillowWeapon, def_data: WeaponDefinitionData) -> WillowInventory:
        return inv.CreateWeaponFromDef(
            NewWeaponDef=def_data,
            PlayerOwner=inv.Owner,
            bForceSelectNameParts=True,
        )


@dataclass
class ItemReplacements(BaseReplacementList):
    @dataclass(frozen=True)
    class ExtendedSlotNames(BaseReplacementList.SlotNames):
        part_list: str
        item_definition: str

    # Set this to our derived type
    @classmethod
    @abstractmethod
    def get_basic_slots(cls) -> Mapping[DummyItem, ItemReplacements.ExtendedSlotNames]:
        raise NotImplementedError

    ALPHA: ClassVar[ExtendedSlotNames] = ExtendedSlotNames(
        "alpha",
        "AlphaItemPartDefinition",
        "AlphaPartData",
        "AlphaParts",
    )
    BETA: ClassVar[ExtendedSlotNames] = ExtendedSlotNames(
        "beta",
        "BetaItemPartDefinition",
        "BetaPartData",
        "BetaParts",
    )
    GAMMA: ClassVar[ExtendedSlotNames] = ExtendedSlotNames(
        "gamma",
        "GammaItemPartDefinition",
        "GammaPartData",
        "GammaParts",
    )
    DELTA: ClassVar[ExtendedSlotNames] = ExtendedSlotNames(
        "delta",
        "DeltaItemPartDefinition",
        "DeltaPartData",
        "DeltaParts",
    )
    EPSILON: ClassVar[ExtendedSlotNames] = ExtendedSlotNames(
        "epsilon",
        "EpsilonItemPartDefinition",
        "EpsilonPartData",
        "EpsilonParts",
    )
    ZETA: ClassVar[ExtendedSlotNames] = ExtendedSlotNames(
        "zeta",
        "ZetaItemPartDefinition",
        "ZetaPartData",
        "ZetaParts",
    )
    ETA: ClassVar[ExtendedSlotNames] = ExtendedSlotNames(
        "eta",
        "EtaItemPartDefinition",
        "EtaPartData",
        "EtaParts",
    )
    THETA: ClassVar[ExtendedSlotNames] = ExtendedSlotNames(
        "theta",
        "ThetaItemPartDefinition",
        "ThetaPartData",
        "ThetaParts",
    )
    MATERIAL: ClassVar[ExtendedSlotNames] = ExtendedSlotNames(
        "materials",
        "MaterialItemPartDefinition",
        "MaterialPartData",
        "MaterialParts",
    )
    alpha: set[ItemPartDefinition]
    beta: set[ItemPartDefinition]
    gamma: set[ItemPartDefinition]
    delta: set[ItemPartDefinition]
    epsilon: set[ItemPartDefinition]
    zeta: set[ItemPartDefinition]
    eta: set[ItemPartDefinition]
    theta: set[ItemPartDefinition]
    materials: set[ItemPartDefinition]

    def __init__(self, inv: WillowInventory) -> None:
        super().__init__(inv)

    def init_basic_slots(self, inv: WillowInventory) -> None:
        balance = (def_data := inv.DefinitionData).BalanceDefinition
        definition = balance.InventoryDefinition
        part_list_collection = balance.PartListCollection

        for slot_names in self.get_basic_slots().values():
            original_part = getattr(def_data, slot_names.def_data)

            # If the parts list collection defines any parts, treat that as an override
            collection_part_list = getattr(part_list_collection, slot_names.part_list)
            if collection_part_list.bEnabled:
                collection_parts = {
                    part
                    for part_slot in collection_part_list.WeightedParts
                    if (part := part_slot.Part) != original_part
                }
                setattr(self, slot_names.attr, collection_parts)
                continue

            # No collection parts, fall back to those on the definition
            definition_part_list = getattr(definition, slot_names.item_definition)
            if definition_part_list is None:
                setattr(self, slot_names.attr, set())
                continue

            setattr(
                self,
                slot_names.attr,
                {
                    part
                    for part_slot in definition_part_list.WeightedParts
                    if (part := part_slot.Part) != original_part
                },
            )

    @staticmethod
    def create_from_def_data(inv: WillowItem, def_data: ItemDefinitionData) -> WillowInventory:
        return inv.CreateItemFromDef(
            NewItemDef=def_data,
            PlayerOwner=inv.Owner,
            NewQuantity=0,
            bForceSelectNameParts=True,
        )


class ShieldReplacements(ItemReplacements):
    BASIC_SLOTS: ClassVar[dict[DummyItem, ItemReplacements.ExtendedSlotNames]] = {
        DummyItem.SHIELD_ACCESSORY: ItemReplacements.DELTA,
        DummyItem.SHIELD_BATTERY: ItemReplacements.BETA,
        DummyItem.SHIELD_BODY: ItemReplacements.ALPHA,
        DummyItem.SHIELD_CAPACITOR: ItemReplacements.GAMMA,
        DummyItem.MATERIAL: ItemReplacements.MATERIAL,
        DummyItem.EPSILON: ItemReplacements.EPSILON,
        DummyItem.ZETA: ItemReplacements.ZETA,
        DummyItem.ETA: ItemReplacements.ETA,
        DummyItem.THETA: ItemReplacements.THETA,
    }

    @classmethod
    def get_basic_slots(cls) -> Mapping[DummyItem, ItemReplacements.ExtendedSlotNames]:
        return cls.BASIC_SLOTS

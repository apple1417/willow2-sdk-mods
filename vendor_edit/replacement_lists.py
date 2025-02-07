from __future__ import annotations

from abc import ABC, abstractmethod
from copy import copy
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, overload

import unrealsdk
from unrealsdk.unreal import UClass, UObject, WeakPointer, WrappedStruct

from .dummy_items import DummyItem

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from enum import auto

    from unrealsdk.unreal._uenum import UnrealEnum  # pyright: ignore[reportMissingModuleSource]

    class EPartReplacementMode(UnrealEnum):
        EPRM_Additive = auto()
        EPRM_Selective = auto()
        EPRM_Complete = auto()
        EPRM_MAX = auto()

else:
    EPartReplacementMode = unrealsdk.find_enum("EPartReplacementMode")


type ItemDefinition = UObject
type ItemPartDefinition = UObject
type ManufacturerDefinition = UObject
type WeaponPartDefinition = UObject
type ItemPartListCollectionDefinition = UObject
type WillowInventory = UObject
type WillowItem = UObject
type WillowWeapon = UObject

type ItemDefinitionData = WrappedStruct
type WeaponDefinitionData = WrappedStruct


__all__: tuple[str, ...] = ("create_replacement_list",)


def create_replacement_list(item: WillowInventory) -> IReplacementList:
    """
    Creates an appropriate replacement list for the given item.

    Args:
        item: The item to create replacements for.
    Returns:
        The new replacement list.
    """
    cls = item.Class
    for replacement_class in (
        WeaponReplacements,
        ShieldReplacements,
        GrenadeReplacements,
        COMReplacements,
        ArtifactReplacements,
        # Item must be last since the others subclass it
        ItemReplacements,
    ):
        if cls._inherits(replacement_class.UCLASS):
            return replacement_class(item)

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

    UCLASS: ClassVar[UClass]

    inv: WeakPointer[WillowInventory]

    manufacturers: list[ManufacturerDefinition]
    levels: list[int]

    def __init__(self, inv: WillowInventory) -> None:
        self.inv = WeakPointer(inv)

        original_manu = (def_data := inv.DefinitionData).ManufacturerDefinition
        self.manufacturers = sorted(
            {
                manu
                for entry in def_data.BalanceDefinition.Manufacturers
                if (manu := entry.Manufacturer) is not None and manu != original_manu
            },
            key=str,
        )

        player_level = (owner := inv.Owner).GetExpLevel()
        controller = owner.Controller
        try:
            op_levels = controller.PlayerReplicationInfo.NumOverpowerLevelsUnlocked
        except AttributeError:
            op_levels = 0

        try:
            max_level = (
                controller.GetMaximumPossiblePlayerLevelCap()
                + controller.GetMaximumPossibleOverpowerModifier()
            )
        except AttributeError:
            max_level = controller.GetMaxExpLevel()

        original_level = inv.DefinitionData.ManufacturerGradeIndex
        self.levels = sorted(
            {
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
            },
        )

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

            # Keep game stage synced - this is general good practice, and we explicitly want it when
            # editing level
            new_def.GameStage = new_def.ManufacturerGradeIndex

            new_items.append(self.create_from_def_data(inv, new_def))

        return new_items

    @classmethod
    @abstractmethod
    def get_basic_slots(cls) -> Mapping[DummyItem, BaseReplacementList.SlotNames]:
        """
        Gets a dict mapping a category dummy item to the item definition data's basic part slots.

        Returns:
            The basic slots dict.
        """
        raise NotImplementedError

    @abstractmethod
    def init_basic_slots(self, inv: WillowInventory) -> None:
        """
        Initializes the fields on this object which depend on the basic slots.

        Args:
            inv: The inventory item to initialize based off of.
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

    UCLASS: ClassVar[UClass] = unrealsdk.find_class("WillowWeapon")

    bodies: list[WeaponPartDefinition]
    grips: list[WeaponPartDefinition]
    barrels: list[WeaponPartDefinition]
    sights: list[WeaponPartDefinition]
    stocks: list[WeaponPartDefinition]
    elements: list[WeaponPartDefinition]
    accessory1s: list[WeaponPartDefinition]
    accessory2s: list[WeaponPartDefinition]
    materials: list[WeaponPartDefinition]

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
                setattr(self, slot_names.attr, [])
                continue

            original_part = getattr(def_data, slot_names.def_data)
            setattr(
                self,
                slot_names.attr,
                sorted(
                    {
                        part
                        for part_slot in part_list.WeightedParts
                        if (part := part_slot.Part) != original_part
                    },
                    key=str,
                ),
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

    BASIC_SLOTS: ClassVar[dict[DummyItem, ItemReplacements.ExtendedSlotNames]] = {
        DummyItem.ALPHA: ALPHA,
        DummyItem.BETA: BETA,
        DummyItem.GAMMA: GAMMA,
        DummyItem.DELTA: DELTA,
        DummyItem.EPSILON: EPSILON,
        DummyItem.ZETA: ZETA,
        DummyItem.ETA: ETA,
        DummyItem.THETA: THETA,
        DummyItem.MATERIAL: MATERIAL,
    }

    UCLASS: ClassVar[UClass] = unrealsdk.find_class("WillowItem")

    alpha: list[ItemPartDefinition]
    beta: list[ItemPartDefinition]
    gamma: list[ItemPartDefinition]
    delta: list[ItemPartDefinition]
    epsilon: list[ItemPartDefinition]
    zeta: list[ItemPartDefinition]
    eta: list[ItemPartDefinition]
    theta: list[ItemPartDefinition]
    materials: list[ItemPartDefinition]

    def __init__(self, inv: WillowInventory) -> None:
        super().__init__(inv)

    @classmethod
    def get_basic_slots(cls) -> Mapping[DummyItem, ItemReplacements.ExtendedSlotNames]:
        return cls.BASIC_SLOTS

    def init_basic_slots(self, inv: WillowInventory) -> None:
        balance = (def_data := inv.DefinitionData).BalanceDefinition
        definition = balance.InventoryDefinition

        try:
            # If a an item has a runtime parts list, prefer that
            part_list_collection = balance.RuntimePartListCollection
        except AttributeError:
            # Fall back to the basic one
            part_list_collection = balance.PartListCollection

        # Easier for the following to work if all slots already have defaults
        for slot_names in self.get_basic_slots().values():
            setattr(self, slot_names.attr, [])

        if definition is not None:
            self.init_from_definition(def_data, definition)

        if part_list_collection is not None:
            self.init_from_part_list(def_data, part_list_collection)

    def init_from_definition(
        self,
        def_data: ItemDefinitionData,
        definition: ItemDefinition,
    ) -> None:
        """
        Initializes the basic slots with data pulled from the item definition.

        Args:
            def_data: The current items's def data.
            definition: The item definition to init based off of.
        """
        for slot_names in self.get_basic_slots().values():
            original_part = getattr(def_data, slot_names.def_data)
            definition_part_list = getattr(definition, slot_names.item_definition)
            if definition_part_list is None:
                continue

            setattr(
                self,
                slot_names.attr,
                sorted(
                    {
                        part
                        for part_slot in definition_part_list.WeightedParts
                        if (part := part_slot.Part) != original_part
                    },
                    key=str,
                ),
            )

    def init_from_part_list(
        self,
        def_data: ItemDefinitionData,
        part_list_collection: ItemPartListCollectionDefinition,
    ) -> None:
        """
        Initializes the basic slots with data pulled from the part list collection.

        Args:
            def_data: The current items's def data.
            part_list_collection: The part list collection to init based off of.
        """
        replacement_mode = part_list_collection.PartReplacementMode

        for slot_names in self.get_basic_slots().values():
            original_part = getattr(def_data, slot_names.def_data)

            slot_list = getattr(self, slot_names.attr)

            if replacement_mode == EPartReplacementMode.EPRM_Complete:
                slot_list[:] = []

            collection_part_list = getattr(part_list_collection, slot_names.part_list)
            if not collection_part_list.bEnabled:
                continue

            new_parts = sorted(
                {
                    part
                    for part_slot in collection_part_list.WeightedParts
                    if (part := part_slot.Part) != original_part
                },
                key=str,
            )

            match replacement_mode:
                case EPartReplacementMode.EPRM_Additive:
                    slot_list.extend(new_parts)
                case EPartReplacementMode.EPRM_Selective | EPartReplacementMode.EPRM_Complete:
                    slot_list[:] = new_parts
                case _:
                    pass

    @staticmethod
    def create_from_def_data(inv: WillowItem, def_data: ItemDefinitionData) -> WillowInventory:
        return inv.CreateItemFromDef(
            NewItemDef=def_data,
            PlayerOwner=inv.Owner,
            NewQuantity=1,
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

    UCLASS: ClassVar[UClass] = unrealsdk.find_class("WillowShield")


class GrenadeReplacements(ItemReplacements):
    BASIC_SLOTS: ClassVar[dict[DummyItem, ItemReplacements.ExtendedSlotNames]] = {
        DummyItem.GRENADE_ACCESSORY: ItemReplacements.DELTA,
        DummyItem.GRENADE_BLAST_RADIUS: ItemReplacements.ZETA,
        DummyItem.GRENADE_CHILD_COUNT: ItemReplacements.ETA,
        DummyItem.GRENADE_DAMAGE: ItemReplacements.EPSILON,
        DummyItem.GRENADE_DELIVERY: ItemReplacements.BETA,
        DummyItem.GRENADE_PAYLOAD: ItemReplacements.ALPHA,
        DummyItem.GRENADE_STATUS_DAMAGE: ItemReplacements.THETA,
        DummyItem.GRENADE_TRIGGER: ItemReplacements.GAMMA,
        DummyItem.MATERIAL: ItemReplacements.MATERIAL,
    }

    UCLASS: ClassVar[UClass] = unrealsdk.find_class("WillowGrenadeMod")


class COMReplacements(ItemReplacements):
    BASIC_SLOTS: ClassVar[dict[DummyItem, ItemReplacements.ExtendedSlotNames]] = {
        DummyItem.COM_SPECIALIZATION: ItemReplacements.ALPHA,
        DummyItem.COM_PRIMARY: ItemReplacements.BETA,
        DummyItem.COM_SECONDARY: ItemReplacements.GAMMA,
        DummyItem.COM_PENALTY: ItemReplacements.MATERIAL,
        DummyItem.DELTA: ItemReplacements.DELTA,
        DummyItem.EPSILON: ItemReplacements.EPSILON,
        DummyItem.ZETA: ItemReplacements.ZETA,
        DummyItem.ETA: ItemReplacements.ETA,
        DummyItem.THETA: ItemReplacements.THETA,
    }

    UCLASS: ClassVar[UClass] = unrealsdk.find_class("WillowClassMod")


class ArtifactReplacements(ItemReplacements):
    BASIC_SLOTS: ClassVar[dict[DummyItem, ItemReplacements.ExtendedSlotNames]] = {
        DummyItem.RELIC_BODY: ItemReplacements.ETA,
        DummyItem.RELIC_UPGRADE: ItemReplacements.THETA,
        DummyItem.ALPHA: ItemReplacements.ALPHA,
        DummyItem.BETA: ItemReplacements.BETA,
        DummyItem.GAMMA: ItemReplacements.GAMMA,
        DummyItem.DELTA: ItemReplacements.DELTA,
        DummyItem.EPSILON: ItemReplacements.EPSILON,
        DummyItem.ZETA: ItemReplacements.ZETA,
        DummyItem.MATERIAL: ItemReplacements.MATERIAL,
    }

    UCLASS: ClassVar[UClass] = unrealsdk.find_class("WillowArtifact")

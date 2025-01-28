from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass, field
from enum import Enum

import unrealsdk
from unrealsdk.unreal import UObject, WeakPointer

from .packages import INV_BAL_DEF, PART, PART_COLLECTION, PREFIX

type InventoryBalanceDefinition = UObject
type ManufacturerDefinition = UObject
type WillowInventory = UObject
type WillowPawn = UObject

__all__: tuple[str, ...] = ("DummyItem",)

bank_bal_def: WeakPointer[InventoryBalanceDefinition] = WeakPointer()
cash_manufacturer: WeakPointer[ManufacturerDefinition] = WeakPointer()


def _get_bank_bal_def() -> InventoryBalanceDefinition:
    """Gets the Bank SDU's balance definition."""
    global bank_bal_def
    if (inner := bank_bal_def()) is None:
        inner = unrealsdk.find_object(
            "InventoryBalanceDefinition",
            "GD_CustomItems.Items.CustomItem_SDU_Bank",
        )
        bank_bal_def = WeakPointer(inner)
    return inner


def _get_cash_manufacturer() -> InventoryBalanceDefinition:
    """Gets the cash manufacturer."""
    global cash_manufacturer
    if (inner := cash_manufacturer()) is None:
        inner = unrealsdk.find_object(
            "ManufacturerDefinition",
            "GD_Currency.Manufacturers.Cash_Manufacturer",
        )
        cash_manufacturer = WeakPointer(inner)
    return inner


@dataclass(frozen=True)
class DummyItemMixin:
    display_name: str
    obj_name: str

    _bal_def: UObject | None = field(init=False, default=None, compare=False, hash=False)

    def _update_bal_def(self, new_balance: InventoryBalanceDefinition) -> None:
        # Hack to edit frozen dataclass - this field is deliberately not hashed  # noqa: FIX004
        super().__setattr__("_bal_def", new_balance)

    @property
    def bal_def(self) -> InventoryBalanceDefinition:
        if self._bal_def is not None:
            return self._bal_def

        with suppress(ValueError):
            new_balance = unrealsdk.find_object(
                "InventoryBalanceDefinition",
                f"{INV_BAL_DEF.path_name}.{self.obj_name}",
            )
            self._update_bal_def(new_balance)
            return new_balance

        base_balance = _get_bank_bal_def()
        new_balance = unrealsdk.construct_object(
            base_balance.Class,
            INV_BAL_DEF.unreal,
            self.obj_name,
            0x4000,
            base_balance,
        )
        new_balance.Manufacturers[0].Manufacturer = _get_cash_manufacturer()

        new_part_list = unrealsdk.construct_object(
            (base_part_list := new_balance.PartListCollection).Class,
            PART_COLLECTION.unreal,
            self.obj_name,
            0,
            base_part_list,
        )
        new_balance.PartListCollection = new_part_list

        new_part = unrealsdk.construct_object(
            (
                base_part := (alpha_part_data := new_part_list.AlphaPartData.WeightedParts[0]).Part
            ).Class,
            PART.unreal,
            self.obj_name,
            0,
            base_part,
        )
        alpha_part_data.Part = new_part
        new_part_list.MaterialPartData.WeightedParts[0].Part = new_part

        new_part.CustomPresentations.clear()

        new_prefix = unrealsdk.construct_object(
            (base_prefix := new_part.PrefixList[0]).Class,
            PREFIX.unreal,
            self.obj_name,
            0,
            base_prefix,
        )
        new_part.PrefixList = (new_prefix,)
        new_prefix.PartName = self.display_name

        self._update_bal_def(new_balance)
        return new_balance

    def spawn(self, owner: WillowPawn) -> WillowInventory:
        """
        Creates an instance of this dummy item.

        Args:
            owner: The pawn to set as the item's owner.
        """
        _, spawned = unrealsdk.find_class(
            "ItemPool",
        ).ClassDefaultObject.SpawnBalancedInventoryFromInventoryBalanceDefinition(
            InvBalanceDefinition=self.bal_def,
            Quantity=1,
            GameStage=1,
            AwesomeLevel=0,
            ContextSource=owner,
            SpawnedInventory=(),
        )
        return spawned[0]


class DummyItem(DummyItemMixin, Enum):
    MANUFACTURER = "Manufacturer", "manufacturer"
    MATERIAL = "Material", "material"
    ALPHA = "Alpha", "alpha"
    BETA = "Beta", "beta"
    GAMMA = "Gamma", "gamma"
    DELTA = "Delta", "delta"
    EPSILON = "Epsilon", "epsilon"
    ZETA = "Zeta", "zeta"
    ETA = "Eta", "eta"
    THETA = "Theta", "theta"
    # ================
    WEAP_BODY = "Body", "weap_body"
    WEAP_GRIP = "Grip", "weap_grip"
    WEAP_BARREL = "Barrel", "weap_barrel"
    WEAP_SIGHT = "Sight", "weap_sight"
    WEAP_STOCK = "Stock", "weap_stock"
    WEAP_ELEMENT = "Element", "weap_element"
    WEAP_ACCESSORY = "Accessory", "weap_accessory"
    WEAP_ALT_ACCESSORY = "Alt Accessory", "weap_alt_accessory"
    # ================
    SHIELD_BODY = "Body", "shield_body"
    SHIELD_BATTERY = "Battery", "shield_battery"
    SHIELD_ACCESSORY = "Accessory", "shield_accessory"
    SHIELD_CAPACITOR = "Capacitor", "shield_capacitor"
    # ================
    GRENADE_PAYLOAD = "Payload", "grenade_payload"
    GRENADE_DELIVERY = "Delivery", "grenade_delivery"
    GRENADE_TRIGGER = "Trigger", "grenade_trigger"
    GRENADE_ACCESSORY = "Accessory", "grenade_accessory"
    GRENADE_DAMAGE = "Damage", "grenade_damage"
    BLAST_RADIUS = "Blast Radius", "grenade_blast_radius"
    CHILD_COUNT = "Child Count", "grenade_child_count"
    STATUS_DAMAGE = "Status Damage", "grenade_status_damage"
    # ================
    COM_SPECIALIZATION = "Specialization", "com_specialization"
    COM_PRIMARY = "Primary", "com_primary"
    COM_SECONDARY = "Secondary", "com_secondary"
    COM_PENALTY = "Penalty", "com_penalty"
    # ================
    RELIC_UPGRADE = "Upgrade", "relic_upgrade"
    # ================
    LEVEL = "Level", "level"
    LEVEL_MAX = "Max Usable", "level_max"
    LEVEL_PLUS_10 = "+10", "level_+10"
    LEVEL_PLUS_1 = "+1", "level_+1"
    LEVEL_MINUS_1 = "-1", "level_-1"
    LEVEL_MINUS_10 = "-10", "level_-10"

    @classmethod
    def from_balance(cls, bal: InventoryBalanceDefinition) -> DummyItem:
        """
        Given an existing InventoryBalanceDefinition, get the relevant enum value.

        Args:
            bal: The balance to look up.
        Returns:
            The relevant enum value.
        """
        for entry in cls:
            if entry.obj_name.lower() == bal.Name.lower():
                return entry
        raise ValueError(f"Couldn't find dummy item for balance: {bal}")


_all_obj_names = [i.obj_name for i in DummyItem]
if len(_all_obj_names) != len(set(_all_obj_names)):
    raise ValueError("have dummy items with duplicate object names!")
del _all_obj_names

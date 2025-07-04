from collections.abc import Callable, Iterator
from dataclasses import dataclass

from unrealsdk.unreal import UObject

from .ak_events import AKE_BUY, AKE_SELL, find_and_play_akevent
from .enums import EInteractionIcons, EShopType, PlayerMark

type AmmoResourcePool = UObject
type WillowInventory = UObject
type WillowPlayerController = UObject
type WillowVendingMachine = UObject


@dataclass
class AmmoInfo:
    resource_pool_name: str
    bullets_per_item: int


@dataclass
class ShopInfo:
    icon_name: str
    icon_text: str
    icon: EInteractionIcons
    cost_function: Callable[[WillowPlayerController, WillowVendingMachine], int]
    purchase_function: Callable[[WillowPlayerController, WillowVendingMachine], None]
    requires_manual_payment: bool = True


GRENADE_RESOURCE_NAME: str = "Ammo_Grenade_Protean"

# Going to assume you haven't modded ammo amounts.
# The UCP does edit it to let you refill in one purchage, BUT it also doesn't change the price, so
# I think it's better sticking with the defaults than reading the actual amounts.
AMMO_COUNTS: dict[str, AmmoInfo] = {
    "AmmoShop_Assault_Rifle_Bullets": AmmoInfo("Ammo_Combat_Rifle", 54),
    "AmmoShop_Grenade_Protean": AmmoInfo(GRENADE_RESOURCE_NAME, 3),
    "AmmoShop_Laser_Cells": AmmoInfo("Ammo_Combat_Laser", 68),
    "AmmoShop_Patrol_SMG_Clip": AmmoInfo("Ammo_Patrol_SMG", 72),
    "AmmoShop_Repeater_Pistol_Clip": AmmoInfo("Ammo_Repeater_Pistol", 54),
    "AmmoShop_Rocket_Launcher": AmmoInfo("Ammo_Rocket_Launcher", 12),
    "AmmoShop_Shotgun_Shells": AmmoInfo("Ammo_Combat_Shotgun", 24),
    "AmmoShop_Sniper_Rifle_Cartridges": AmmoInfo("Ammo_Sniper_Rifle", 18),
}

# Again assuming you haven't modded how much a vial heals
VIAL_HEAL_PERCENT: float = 0.25


def get_trash_value(pc: WillowPlayerController, vendor: WillowVendingMachine) -> int:
    """
    Gets the value of selling all trash in the player's inventory.

    Args:
        pc: The player controller trying to sell trash.
        vendor: The vendor they're trying to sell trash at.
    Returns:
        The value of the player's trash, or 0 if unable to sell any.
    """
    _ = vendor

    inv_manager = pc.GetPawnInventoryManager()
    if inv_manager is None:  # Offhost
        return 0

    total_value = 0
    for item in inv_manager.Backpack:
        if item is None:
            continue
        if item.GetMark() != PlayerMark.PM_Trash:
            continue
        total_value += item.GetMonetaryValue()
    return total_value


def sell_trash(pc: WillowPlayerController, vendor: WillowVendingMachine) -> None:
    """
    Sells all trash in the player's inventory, and gives payment.

    Args:
        pc: The player controller whose trash to sell.
        vendor: The vendor they're selling at.
    """
    _ = vendor

    pc.GetPawnInventoryManager().SellAllTrash()
    find_and_play_akevent(pc, AKE_SELL)


def iter_ammo_data(
    pc: WillowPlayerController,
    vendor: WillowVendingMachine,
) -> Iterator[tuple[WillowInventory, AmmoInfo, AmmoResourcePool]]:
    """
    Looks though all items in a vendor, and returns various data on the ammo that's available.

    Does not return ammo not in the vendor - won't have nades/rockets in early game ones.

    Args:
        pc: The player controller trying to refill ammo.
        vendor: The vendor they're trying to refill ammo at.
    Returns:
        A tuple of the ammo item, the AmmoInfo object for that type, and the player's ammo pool.
    """
    ammo_pools = {
        pool.Definition.Resource.Name: pool
        for pool in pc.ResourcePoolManager.ResourcePools
        if (
            pool is not None
            and (
                pool.Class.Name == "AmmoResourcePool"
                or pool.Definition.Resource.Name == GRENADE_RESOURCE_NAME
            )
        )
    }

    for item in vendor.ShopInventory:
        def_name: str
        try:
            def_name = item.DefinitionData.ItemDefinition.Name
        except AttributeError:  # If anything in the chain was None
            continue

        if def_name not in AMMO_COUNTS:
            continue
        info = AMMO_COUNTS[def_name]
        pool = ammo_pools[info.resource_pool_name]

        yield item, info, pool


def get_ammo_cost(pc: WillowPlayerController, vendor: WillowVendingMachine) -> int:
    """
    Gets the cost of refilling ammo at a vendor.

    Args:
        pc: The player controller trying to refill ammo.
        vendor: The vendor they're trying to refill ammo at.
    Returns:
        The cost of refilling ammo, or 0 if unable to refill.
    """
    total_cost = 0
    for item, info, pool in iter_ammo_data(pc, vendor):
        ammo_needed = int(pool.GetMaxValue()) - pool.GetCurrentValue()
        cost_per_bullet = vendor.GetSellingPriceForInventory(item, pc, 1) / info.bullets_per_item
        if ammo_needed != 0:
            total_cost += max(1, int(ammo_needed * cost_per_bullet))

    return total_cost


def refill_ammo(pc: WillowPlayerController, vendor: WillowVendingMachine) -> None:
    """
    Refills all ammo types which are available at the given vendor. Does not take payment.

    Args:
        pc: The player controller to refill ammo of.
        vendor: The vendor they're refilling ammo at.
    """
    for _, _, pool in iter_ammo_data(pc, vendor):
        pool.SetCurrentValue(pool.GetMaxValue())
    find_and_play_akevent(pc, AKE_BUY)


def get_heal_cost(pc: WillowPlayerController, vendor: WillowVendingMachine) -> int:
    """
    Gets the cost of healing at a vendor.

    Args:
        pc: The player controller trying to heal.
        vendor: The vendor they're trying to heal at.
    Returns:
        The cost of healing, or 0 if unable to heal.
    """
    if (pawn := pc.Pawn).GetHealth() >= pawn.GetMaxHealth():
        return 0

    vial_cost: int
    for item in vendor.ShopInventory:
        if item is None:
            continue
        if item.DefinitionData.ItemDefinition.Name == "BuffDrink_HealingInstant":
            vial_cost = vendor.GetSellingPriceForInventory(item, pc, 1)
            break
    else:
        return 0

    full_heal_cost = vial_cost / VIAL_HEAL_PERCENT
    missing_health = 1 - (pawn.GetHealth() / pawn.GetMaxHealth())
    return max(1, int(full_heal_cost * missing_health))


def do_heal(pc: WillowPlayerController, vendor: WillowVendingMachine) -> None:
    """
    Performs a heal. Does not take payment.

    Args:
        pc: The player controller to heal.
        vendor: The vendor they're healing at.
    """
    _ = vendor

    (pawn := pc.Pawn).SetHealth(pawn.GetMaxHealth())
    find_and_play_akevent(pc, AKE_BUY)


SHOP_INFO_MAP: dict[EShopType, ShopInfo] = {  # type: ignore
    EShopType.SType_Weapons: ShopInfo(
        "Icon_SellTrash",
        "SELL TRASH",
        EInteractionIcons.INTERACTION_ICON_Open,
        lambda pc, vendor: -get_trash_value(pc, vendor),
        sell_trash,
        requires_manual_payment=False,
    ),
    EShopType.SType_Items: ShopInfo(
        "Icon_RefillAmmo",
        "REFILL AMMO",
        EInteractionIcons.INTERACTION_ICON_Gunner,
        get_ammo_cost,
        refill_ammo,
    ),
    EShopType.SType_Health: ShopInfo(
        "Icon_RefillHealth",
        "REFILL HEALTH",
        EInteractionIcons.INTERACTION_ICON_Heal,
        get_heal_cost,
        do_heal,
    ),
}

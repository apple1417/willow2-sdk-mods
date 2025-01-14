from __future__ import annotations

import unrealsdk

if unrealsdk.GetVersion() < (0, 7, 10):
    # Needed to read fixed arrays
    raise ImportError("Alt Use Vendors requires at least SDK version 0.7.10")

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Dict, Iterator, Set, Tuple

if TYPE_CHECKING:
    from typing_extensions import TypeAlias

from Mods.ModMenu import VERSION_MAJOR, VERSION_MINOR

if (VERSION_MAJOR, VERSION_MINOR) < (2, 4):
    # Needed for Hook
    raise ImportError("Alt Use Vendors requires at least Mod Menu version 2.4")

from Mods.ModMenu import EnabledSaveType, Game, Hook, Mods, ModTypes, RegisterMod, SDKMod

try:
    from Mods.Enums import (EChangeStatus, ECurrencyType, EInteractionIcons, ENetRole, EShopType,
                            ESkillEventType, ETransactionStatus, EUsabilityType, PlayerMark)
except ImportError:
    import webbrowser
    webbrowser.open("https://bl-sdk.github.io/requirements/?mod=Alt%20Use%20Vendors&all")
    raise ImportError("Alt Use Vendors requires at least Enums version 1.0")


Actor: TypeAlias = unrealsdk.UObject
AkEvent: TypeAlias = unrealsdk.UObject
AmmoResourcePool: TypeAlias = unrealsdk.UObject
InteractionIconDefinition: TypeAlias = unrealsdk.UObject
WillowInventory: TypeAlias = unrealsdk.UObject
WillowPlayerController: TypeAlias = unrealsdk.UObject
WillowVendingMachine: TypeAlias = unrealsdk.UObject


@dataclass
class AmmoInfo:
    resource_pool_name: str
    bullets_per_item: int


@dataclass
class ShopInfo:
    icon_name: str
    icon_text: str
    icon: EInteractionIcons  # type: ignore
    cost_function: Callable[[WillowPlayerController, WillowVendingMachine], int]
    purchase_function: Callable[[WillowPlayerController, WillowVendingMachine], None]
    requires_manual_payment: bool = True


GRENADE_RESOURCE_NAME: str = "Ammo_Grenade_Protean"

"""
Going to assume you haven't modded ammo amounts.
The UCP does edit it to let you refill in one purchage, BUT it also doesn't change the price, so I
 think it's better sticking with the defaults than reading the actual amounts.
"""
AMMO_COUNTS: Dict[str, AmmoInfo] = {
    "AmmoShop_Assault_Rifle_Bullets": AmmoInfo("Ammo_Combat_Rifle", 54),
    "AmmoShop_Grenade_Protean": AmmoInfo(GRENADE_RESOURCE_NAME, 3),
    "AmmoShop_Laser_Cells": AmmoInfo("Ammo_Combat_Laser", 68),
    "AmmoShop_Patrol_SMG_Clip": AmmoInfo("Ammo_Patrol_SMG", 72),
    "AmmoShop_Repeater_Pistol_Clip": AmmoInfo("Ammo_Repeater_Pistol", 54),
    "AmmoShop_Rocket_Launcher": AmmoInfo("Ammo_Rocket_Launcher", 12),
    "AmmoShop_Shotgun_Shells": AmmoInfo("Ammo_Combat_Shotgun", 24),
    "AmmoShop_Sniper_Rifle_Cartridges": AmmoInfo("Ammo_Sniper_Rifle", 18)
}

# Again assuming you haven't modded how much a vial heals
VIAL_HEAL_PERCENT: float = 0.25


# Sound AkEvents for playing
AKE_BUY: str = "Ake_UI.UI_Vending.Ak_Play_UI_Vending_Buy"
AKE_SELL: str = "Ake_UI.UI_Vending.Ak_Play_UI_Vending_Sell"
AKE_INTERACT_BY_VENDOR_NAME: Dict[str, str] = {
    Game.BL2: {
        "InteractiveObj_VendingMachine_GrenadesAndAmmo": "Ake_VOCT_Contextual.Ak_Play_VOCT_Marcus_Vending_Munition_Purchase",
        "InteractiveObj_VendingMachine_HealthItems": "Ake_VOCT_Contextual.Ak_Play_VOCT_Zed_Store_Welcome",
        "VendingMachine_Weapons_Definition": "Ake_VOCT_Contextual.Ak_Play_VOCT_Marcus_Vending_Munition_Bye",
        "IO_Aster_VendingMachine_GrenadesAndAmmo": "Ake_Aster_VO.VOCT.Ak_Play_VOCT_Aster_Marcus_Store_Purchase",
        "IO_Aster_VendingMachine_HealthItems": "Ake_Aster_VO.VOCT.Ak_Play_VOCT_Aster_Zed_Store_Purchase",
        "VendingMachine_Aster_Weapons_Definition": "Ake_Aster_VO.VOCT.Ak_Play_VOCT_Aster_Marcus_Store_Bye",
        "VendingMachine_TorgueToken": "Ake_Iris_VO.Ak_Play_Iris_TorgueVendingMachine_Purchase",
    },
    Game.TPS: {
        "InteractiveObj_VendingMachine_GrenadesAndAmmo": "Ake_VOCT_Contextual.Ak_Play_VOCT_Marcus_Vending_Munition_Purchase",
        "InteractiveObj_VendingMachine_HealthItems": "Ake_Cork_VOCT_Contextuals.Cork_VOCT_NurseNina.Ak_Play_VOCT_Cork_NurseNina_Store_Purchase",
        "VendingMachine_Weapons_Definition": "Ake_VOCT_Contextual.Ak_Play_VOCT_Marcus_Vending_Munition_Bye",
        "InteractiveObj_VendingMachine_GrenadesAndAmmo_Marigold": "Ake_VOCT_Contextual.Ak_Play_VOCT_Marcus_Vending_Munition_Purchase",
        "InteractiveObj_VendingMachine_HealthItems_Marigold": "Ake_Cork_VOCT_Contextuals.Cork_VOCT_NurseNina.Ak_Play_VOCT_Cork_NurseNina_Store_Purchase",
        "VendingMachine_Weapons_Definition_Marigold": "Ake_VOCT_Contextual.Ak_Play_VOCT_Marcus_Vending_Munition_Bye",
        "InteractiveObj_VendingMachine_GrenadesAndAmmo_Marigold_BL1": "Ake_VOCT_Contextual.Ak_Play_VOCT_Marcus_Vending_Munition_Purchase",
        "InteractiveObj_VendingMachine_HealthItems_Marigold_BL1": "Ake_Marigold_VOCT_Contextuals.Dlc_Marigold_VOCT_Zed.Ak_Play_Dlc_Marigold_VOCT_Zed_Vending_Welcome",
        "VendingMachine_Weapons_Definition_Marigold_BL1": "Ake_VOCT_Contextual.Ak_Play_VOCT_Marcus_Vending_Munition_Bye",
    },
    Game.AoDK: {
        "IO_Aster_VendingMachine_GrenadesAndAmmo": "Ake_Aster_VO.VOCT.Ak_Play_VOCT_Aster_Marcus_Store_Purchase",
        "IO_Aster_VendingMachine_HealthItems": "Ake_Aster_VO.VOCT.Ak_Play_VOCT_Aster_Zed_Store_Purchase",
        "VendingMachine_Aster_Weapons_Definition": "Ake_Aster_VO.VOCT.Ak_Play_VOCT_Aster_Marcus_Store_Bye",
    }
}[Game.GetCurrent()]


# AkEvents are not loaded by default, and we don't want to do an "expensive" find object call, or a
# truely expensive load package, so we'll just cache them (and keep alive) as we use them
akevent_cache: Dict[str, AkEvent] = {}

def find_and_play_akevent(actor: Actor, event_name: str) -> None:
    """
    Attempts to find and play an AkEvent.

    Silently drops it on failure.

    Args:
        actor: The actor to play at.
        event_name: The object name of the event to play.
    """

    event = akevent_cache.get(event_name)
    if event is None:
        event = unrealsdk.FindObject("AkEvent", event_name)
        if event is None:
            return
        unrealsdk.KeepAlive(event)
        akevent_cache[event_name] = event

    actor.PlayAkEvent(event)


def trigger_money_is_power(PC: WillowPlayerController) -> None:
    """
    If the Game is TPS, triggers the removal of the Doppelganger's Money is Power stacks.

    Args:
        PC: The player controller that has spent money.
    """
    if Game.GetCurrent() is not Game.TPS:
        return
    PC.GetSkillManager().NotifySkillEvent(ESkillEventType.SEVT_OnPaidCashForUse, PC, PC, None, None)


def get_trash_value(PC: WillowPlayerController, vendor: WillowVendingMachine) -> int:
    """
    Gets the value of selling all trash in the player's inventory.

    Args:
        PC: The player controller trying to sell trash.
        vendor: The vendor they're trying to sell trash at.
    Returns:
        The value of the player's trash, or 0 if unable to sell any.
    """
    inv_manager = PC.GetPawnInventoryManager()
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


def sell_trash(PC: WillowPlayerController, vendor: WillowVendingMachine) -> None:
    """
    Sells all trash in the player's inventory, and gives payment.

    Args:
        PC: The player controller whose trash to sell.
        vendor: The vendor they're selling at.
    """
    PC.GetPawnInventoryManager().SellAllTrash()
    find_and_play_akevent(PC, AKE_SELL)


def iter_ammo_data(
    PC: WillowPlayerController,
    vendor: WillowVendingMachine
) -> Iterator[Tuple[WillowInventory, AmmoInfo, AmmoResourcePool]]:
    """
    Looks though all items in a vendor, and returns various data on the ammo that's available.

    Does not return ammo not in the vendor - won't have nades/rockets in early game ones.

    Args:
        PC: The player controller trying to refill ammo.
        vendor: The vendor they're trying to refill ammo at.
    Returns:
        A tuple of the ammo item, the AmmoInfo object for that type, and the player's ammo pool.
    """
    ammo_pools = {
        pool.Definition.Resource.Name: pool
        for pool in PC.ResourcePoolManager.ResourcePools
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


def get_ammo_cost(PC: WillowPlayerController, vendor: WillowVendingMachine) -> int:
    """
    Gets the cost of refilling ammo at a vendor.

    Args:
        PC: The player controller trying to refill ammo.
        vendor: The vendor they're trying to refill ammo at.
    Returns:
        The cost of refilling ammo, or 0 if unable to refill.
    """
    if PC is None:  # Offhost
        return 0

    total_cost = 0
    for item, info, pool in iter_ammo_data(PC, vendor):
        ammo_needed = int(pool.GetMaxValue()) - pool.GetCurrentValue()
        cost_per_bullet = vendor.GetSellingPriceForInventory(item, PC, 1) / info.bullets_per_item
        if ammo_needed != 0:
            total_cost += max(1, int(ammo_needed * cost_per_bullet))

    return total_cost


def refill_ammo(PC: WillowPlayerController, vendor: WillowVendingMachine) -> None:
    """
    Refills all ammo types which are available at the given vendor. Does not take payment.

    Args:
        PC: The player controller to refill ammo of.
        vendor: The vendor they're refilling ammo at.
    """
    for _, _, pool in iter_ammo_data(PC, vendor):
        pool.SetCurrentValue(pool.GetMaxValue())
    find_and_play_akevent(PC, AKE_BUY)


def get_heal_cost(PC: WillowPlayerController, vendor: WillowVendingMachine) -> int:
    """
    Gets the cost of healing at a vendor.

    Args:
        PC: The player controller trying to heal.
        vendor: The vendor they're trying to heal at.
    Returns:
        The cost of healing, or 0 if unable to heal.
    """
    if PC is None:  # Offhost
        return 0

    if PC.Pawn.GetHealth() >= PC.Pawn.GetMaxHealth():
        return 0

    vial_cost: int
    for item in vendor.ShopInventory:
        if item is None:
            continue
        if item.DefinitionData.ItemDefinition.Name == "BuffDrink_HealingInstant":
            vial_cost = vendor.GetSellingPriceForInventory(item, PC, 1)
            break
    else:
        return 0

    full_heal_cost = vial_cost / VIAL_HEAL_PERCENT
    missing_health = 1 - (PC.Pawn.GetHealth() / PC.Pawn.GetMaxHealth())
    return max(1, int(full_heal_cost * missing_health))


def do_heal(PC: WillowPlayerController, vendor: WillowVendingMachine) -> None:
    """
    Performs a heal. Does not take payment.

    Args:
        PC: The player controller to heal.
        vendor: The vendor they're healing at.
    """
    PC.Pawn.SetHealth(PC.Pawn.GetMaxHealth())
    find_and_play_akevent(PC, AKE_BUY)


SHOP_INFO_MAP: Dict[EShopType, ShopInfo] = {  # type: ignore
    EShopType.SType_Weapons: ShopInfo(
        "Icon_SellTrash",
        "SELL TRASH",
        EInteractionIcons.INTERACTION_ICON_Open,
        lambda pc, vendor: -get_trash_value(pc, vendor),
        sell_trash,
        requires_manual_payment=False
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


class AltUseVendors(SDKMod):
    Name: str = "Alt Use Vendors"
    Author: str = "apple1417"
    Description: str = (
        "Adds alt use binds to vendors, like in BL3/Wonderlands."
    )
    Version: str = "2.2"

    Types: ModTypes = ModTypes.Utility
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    icon_map: Dict[EShopType, InteractionIconDefinition]  # type: ignore
    player_vendor_map: Dict[WillowPlayerController, Set[WillowVendingMachine]]

    def Enable(self) -> None:
        super().Enable()
        self.icon_map = {}
        self.player_vendor_map = {}

        self.create_icons()

    def create_icons(self) -> None:
        """
        Creates the icon objects we're using.

        If an object of the same name already exists, uses that instead.
        """
        if len(self.icon_map) == len(SHOP_INFO_MAP):
            return
        self.icon_map = {}

        PC = unrealsdk.GetEngine().GamePlayers[0].Actor
        base_icon = unrealsdk.FindObject("InteractionIconDefinition", "GD_InteractionIcons.Default.Icon_DefaultUse")

        for shop_type, info in SHOP_INFO_MAP.items():
            icon = unrealsdk.FindObject("InteractionIconDefinition", f"GD_InteractionIcons.Default.{info.icon_name}")
            if icon is None:
                icon = unrealsdk.ConstructObject(
                    Class=base_icon.Class,
                    Outer=base_icon.Outer,
                    Name=info.icon_name,
                    Template=base_icon,
                )
                unrealsdk.KeepAlive(icon)

                icon.Icon = info.icon
                # Setting values directly on the object causes a crash on quitting the game
                # Everything still works fine, not super necessary to fix, but people get paranoid
                # https://github.com/bl-sdk/PythonSDK/issues/45
                PC.ServerRCon(f"set {PC.PathName(icon)} Action UseSecondary")
                PC.ServerRCon(f"set {PC.PathName(icon)} Text {info.icon_text}")

            self.icon_map[shop_type] = icon

    def update_vendor_costs(self, PC: WillowPlayerController, shop_type: EShopType) -> None:  # type: ignore
        """
        Updates the alt use cost of all vendors of the given type which are associated with the
         given player.
        """
        if PC not in self.player_vendor_map:
            return

        info = SHOP_INFO_MAP[shop_type]

        for vendor in self.player_vendor_map[PC]:
            if vendor.ShopType != shop_type:
                continue

            vendor.Behavior_ChangeUsabilityCost(
                EChangeStatus.CHANGE_Enable,
                ECurrencyType.CURRENCY_Credits,
                info.cost_function(PC, vendor),
                EUsabilityType.UT_Secondary
            )

    @Hook("WillowGame.WillowInteractiveObject.InitializeFromDefinition")
    def InitializeFromDefinition(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        """
        Called when any interactive object is created. Use it to enable alt use and add the icons.
        """
        if caller.Class.Name != "WillowVendingMachine":
            return True

        if caller.ShopType in SHOP_INFO_MAP:
            params.Definition.HUDIconDefSecondary = self.icon_map[caller.ShopType]
            caller.SetUsability(True, EUsabilityType.UT_Secondary)

        return True

    @Hook("WillowGame.WillowPlayerController.PerformedSecondaryUseAction")
    def PerformedSecondaryUseAction(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        """
        Called whenever someone secondary uses an interactive object. We need to overwrite this far
         up because this is what checks if you can afford to use it, and the secondary use cost
         isn't necessarily accurate.
        """
        if caller.Role < ENetRole.ROLE_Authority:
            return True
        if caller.CurrentUsableObject is None:
            return True
        if caller.CurrentInteractionIcon[1].IconDef is None:
            return True

        vendor = caller.CurrentUsableObject.ObjectPointer
        if vendor.Class.Name != "WillowVendingMachine":
            return True
        if vendor.ShopType not in SHOP_INFO_MAP:
            return True

        caller.UsableObjectUpdateTime = 0.0

        info = SHOP_INFO_MAP[vendor.ShopType]

        cost = info.cost_function(caller, vendor)
        wallet = caller.PlayerReplicationInfo.GetCurrencyOnHand(ECurrencyType.CURRENCY_Credits)
        if cost == 0 or wallet < cost:
            caller.NotifyUnableToAffordUsableObject(EUsabilityType.UT_Secondary)
            return False

        if info.requires_manual_payment:
            caller.PlayerReplicationInfo.AddCurrencyOnHand(ECurrencyType.CURRENCY_Credits, -cost)
            caller.SetPendingTransactionStatus(ETransactionStatus.TS_TransactionComplete)
            trigger_money_is_power(caller)

        info.purchase_function(caller, vendor)

        vendor_name = vendor.InteractiveObjectDefinition.Name
        interact_event = AKE_INTERACT_BY_VENDOR_NAME.get(vendor_name)
        if interact_event is None:
            unrealsdk.Log(f"[Alt Use Vendors] Couldn't find interact voice line for {vendor_name}")
        else:
            find_and_play_akevent(vendor, interact_event)

        self.update_vendor_costs(caller, vendor.ShopType)

        return False

    @Hook("WillowGame.WillowInteractiveObject.Touch")
    def Touch(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        """
        Called when a player moves near an interactive object. Use it to keep track of which players
         are near vendors.
        """
        if caller.Class.Name != "WillowVendingMachine":
            return True
        if params.Other.Class.Name != "WillowPlayerPawn":
            return True

        PC = params.Other.Controller
        if PC not in self.player_vendor_map:
            self.player_vendor_map[PC] = set()
        self.player_vendor_map[PC].add(caller)

        self.update_vendor_costs(PC, caller.ShopType)

        return True

    @Hook("WillowGame.WillowInteractiveObject.UnTouch")
    def UnTouch(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        """
        Called when a player moves away from an interactive object. Use it to keep track of which
         players are near vendors.
        """
        if caller.Class.Name != "WillowVendingMachine":
            return True
        if params.Other.Class.Name != "WillowPlayerPawn":
            return True

        PC = params.Other.Controller
        if PC not in self.player_vendor_map:
            return True

        self.player_vendor_map[PC].discard(caller)
        if len(self.player_vendor_map[PC]) == 0:
            del self.player_vendor_map[PC]

        return True

    @Hook("WillowGame.WillowPlayerController.WillowShowLoadingMovie")
    def WillowShowLoadingMovie(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        """
        Called when starting to load into a new map. Use it clear the player vendor map.
        """
        self.player_vendor_map = {}
        return True

    @Hook("WillowGame.WillowWeapon.InstantFire")
    def InstantFire(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        """
        Called to fire a gun. Happens *after* ammo is removed. Used to update ammo costs.
        """
        if caller.Owner.Class.Name != "WillowPlayerPawn":
            return True
        PC = caller.Owner.Controller

        self.update_vendor_costs(PC, EShopType.SType_Items)
        return True

    @Hook("WillowGame.WillowPlayerController.ConsumeProjectileResource")
    def ConsumeProjectileResource(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        """
        Called to remove the grenade ammo from your inventory. Happens before it's removed. Used to
         update ammo costs.

        Roughly recreating the logic so that we don't break infinite ammo hooks on this same
         function. Not perfect if stuff gets modded too much, but doesn't need to be since this cost
         doesn't really matter.
        """
        if params.ProjectileDefinition.Resource is None:
            return True
        if params.ProjectileDefinition.Resource.Name != GRENADE_RESOURCE_NAME:
            return True

        grenade_pool: AmmoResourcePool
        for pool in caller.ResourcePoolManager.ResourcePools:
            if pool is None:
                continue
            if pool.Definition.Resource.Name == GRENADE_RESOURCE_NAME:
                grenade_pool = pool
                break
        else:
            return True

        grenade_pool.AddCurrentValueImpulse(-1)
        self.update_vendor_costs(caller, EShopType.SType_Items)
        grenade_pool.AddCurrentValueImpulse(1)

        return True

    @Hook("WillowGame.WillowPlayerPawn.TakeDamage")
    def TakeDamage(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        """
        Called whenever a player takes damage. Happens before health is removed. Used to update
         health costs.
        """
        def HasActiveDuel(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            """
            Called as part of TakeDamage, unconditionally, and after health is removed. Used to
             actually update the health costs.
            """
            self.update_vendor_costs(caller.Controller, EShopType.SType_Health)

            unrealsdk.RemoveHook("WillowGame.WillowPlayerPawn.HasActiveDuel", self.Name)
            return True

        unrealsdk.RunHook("WillowGame.WillowPlayerPawn.HasActiveDuel", self.Name, HasActiveDuel)
        return True


instance = AltUseVendors()
if __name__ == "__main__":
    unrealsdk.Log(f"[{instance.Name}] Manually loaded")
    for mod in Mods:
        if mod.Name == instance.Name:
            if mod.IsEnabled:
                mod.Disable()
            Mods.remove(mod)
            unrealsdk.Log(f"[{instance.Name}] Removed last instance")

            # Fixes inspect.getfile()
            instance.__class__.__module__ = mod.__class__.__module__
            break
RegisterMod(instance)

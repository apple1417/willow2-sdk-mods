from typing import Any

import unrealsdk
from mods_base import Game, ObjectFlags, build_mod, hook
from unrealsdk import logging
from unrealsdk.hooks import Block, Type
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

from alt_use_vendors.ak_events import AKE_INTERACT_BY_VENDOR_NAME, find_and_play_akevent

from .enums import (
    EChangeStatus,
    ECurrencyType,
    ENetRole,
    EShopType,
    ESkillEventType,
    ETransactionStatus,
    EUsabilityType,
)
from .shop_info import GRENADE_RESOURCE_NAME, SHOP_INFO_MAP

type Actor = UObject
type AkEvent = UObject
type AmmoResourcePool = UObject
type InteractionIconDefinition = UObject
type WillowInventory = UObject
type WillowPlayerController = UObject
type WillowVendingMachine = UObject


# ==================================================================================================

icon_map: dict[EShopType, InteractionIconDefinition] = {}


def create_icons() -> None:
    """
    Creates the icon objects we're using.

    If an object of the same name already exists, uses that instead.
    """
    if icon_map:
        return

    base_icon = unrealsdk.find_object(
        "InteractionIconDefinition",
        "GD_InteractionIcons.Default.Icon_DefaultUse",
    )

    for shop_type, info in SHOP_INFO_MAP.items():
        try:
            icon = unrealsdk.find_object(
                "InteractionIconDefinition",
                f"GD_InteractionIcons.Default.{info.icon_name}",
            )
        except ValueError:
            icon = unrealsdk.construct_object(
                cls=base_icon.Class,
                outer=base_icon.Outer,
                name=info.icon_name,
                flags=ObjectFlags.KEEP_ALIVE,
                template_obj=base_icon,
            )

            icon.Icon = info.icon
            icon.Action = "UseSecondary"
            icon.Text = info.icon_text

        icon_map[shop_type] = icon


# Called when any interactive object is created. Use it to enable alt use and add the icons.
@hook("WillowGame.WillowInteractiveObject:InitializeFromDefinition")
def initialize_from_definition(  # noqa: D103
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    if obj.Class.Name != "WillowVendingMachine":
        return

    if obj.ShopType in SHOP_INFO_MAP:
        args.Definition.HUDIconDefSecondary = icon_map[obj.ShopType]
        obj.SetUsability(True, EUsabilityType.UT_Secondary)


def trigger_money_is_power(pc: WillowPlayerController) -> None:
    """
    If the Game is TPS, triggers the removal of the Doppelganger's Money is Power stacks.

    Args:
        pc: The player controller that has spent money.
    """
    if Game.get_current() is not Game.TPS:
        return
    pc.GetSkillManager().NotifySkillEvent(ESkillEventType.SEVT_OnPaidCashForUse, pc, pc, None, None)


# This is called whenever someone uses an interactive object.
# At this point, the secondary use cost is not necessarily accurate - the player who used it might
# not be the last one who updated the cost. Hooking in at this point lets us easily overwrite it.
@hook("WillowGame.WillowPlayerController:PerformedSecondaryUseAction")
def performed_secondary_use_action(  # noqa: D103
    obj: UObject,
    _args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> tuple[type[Block], bool] | None:
    if obj.Role < ENetRole.ROLE_Authority:
        return None
    if obj.CurrentUsableObject is None:
        return None
    if obj.CurrentInteractionIcon[1].IconDef is None:
        return None

    vendor = obj.CurrentUsableObject
    if vendor.Class.Name != "WillowVendingMachine":
        return None
    if vendor.ShopType not in SHOP_INFO_MAP:
        return None

    obj.UsableObjectUpdateTime = 0.0

    info = SHOP_INFO_MAP[vendor.ShopType]

    cost = info.cost_function(obj, vendor)
    wallet = obj.PlayerReplicationInfo.GetCurrencyOnHand(ECurrencyType.CURRENCY_Credits)
    if cost == 0 or wallet < cost:
        obj.NotifyUnableToAffordUsableObject(EUsabilityType.UT_Secondary)
        return Block, False

    if info.requires_manual_payment:
        obj.PlayerReplicationInfo.AddCurrencyOnHand(ECurrencyType.CURRENCY_Credits, -cost)
        obj.SetPendingTransactionStatus(ETransactionStatus.TS_TransactionComplete)
        trigger_money_is_power(obj)

    info.purchase_function(obj, vendor)

    vendor_name = vendor.InteractiveObjectDefinition.Name
    interact_event = AKE_INTERACT_BY_VENDOR_NAME.get(vendor_name)
    if interact_event is None:
        logging.warning(f"[Alt Use Vendors] Couldn't find interact voice line for {vendor_name}")
    else:
        find_and_play_akevent(vendor, interact_event)

    update_vendor_costs(obj, vendor.ShopType)
    return Block, True


# ==================================================================================================

# This map keeps track of which vendors each player is near to
# Historically, we've run into some issues with hitches when updating costs
# The current approach is to only do an update when it changes (i.e. on shooting or taking damage),
# and only to the vendors they can actually see - which is where this comes in
player_vendor_map: dict[WillowPlayerController, set[WillowVendingMachine]] = {}


# Called when a player moves near any interactive object - use it to add to the map
@hook("WillowGame.WillowInteractiveObject:Touch")
def interactive_obj_touch(  # noqa: D103
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    if obj.Class.Name != "WillowVendingMachine":
        return
    if (pawn := args.Other).Class.Name != "WillowPlayerPawn":
        return

    pc = pawn.Controller
    if pc not in player_vendor_map:
        player_vendor_map[pc] = set()
    player_vendor_map[pc].add(obj)

    update_vendor_costs(pc, obj.ShopType)


# Called when a player moves away from an interactive object - use it to remove from the map
@hook("WillowGame.WillowInteractiveObject:UnTouch")
def interactive_obj_untouch(  # noqa: D103
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    if obj.Class.Name != "WillowVendingMachine":
        return
    if (other := args.Other).Class.Name != "WillowPlayerPawn":
        return

    pc = other.Controller
    if pc not in player_vendor_map:
        return

    player_vendor_map[pc].discard(obj)

    if not player_vendor_map[pc]:
        del player_vendor_map[pc]


# Called on starting to load into a new level - use it to clear the map
@hook("WillowGame.WillowPlayerController:WillowShowLoadingMovie")
def show_loading_movie(*_: Any) -> None:  # noqa: D103
    player_vendor_map.clear()


def update_vendor_costs(pc: WillowPlayerController, shop_type: EShopType) -> None:  # type: ignore
    """
    Updates the alt use cost for vendors given associated with the given player and type.

    Args:
        pc: The player controller to look for associated vendors of.
        shop_type: The type of ship to filter to.
    """
    if (nearby_vendors := player_vendor_map.get(pc)) is None:
        return

    info = SHOP_INFO_MAP[shop_type]

    for vendor in nearby_vendors:
        if vendor.ShopType != shop_type:
            continue

        vendor.Behavior_ChangeUsabilityCost(
            EChangeStatus.CHANGE_Enable,
            ECurrencyType.CURRENCY_Credits,
            info.cost_function(pc, vendor),
            EUsabilityType.UT_Secondary,
        )


# ==================================================================================================


# Called to fire a gun, *after* ammo is removed - use to update ammo costs
@hook("WillowGame.WillowWeapon:InstantFire")
def weapon_instant_fire(  # noqa: D103
    obj: UObject,
    _args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    if (pawn := obj.Owner).Class.Name != "WillowPlayerPawn":
        return
    update_vendor_costs(pawn.Controller, EShopType.SType_Items)


# Called to remove the grenade ammo after throwing one - use to update ammo costs
@hook("WillowGame.WillowPlayerController:ConsumeProjectileResource", Type.POST)
def consume_projectile_resource(  # noqa: D103
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    if (proj_resource := args.ProjectileDefinition.Resource) is None:
        return
    if proj_resource.Name != GRENADE_RESOURCE_NAME:
        return

    update_vendor_costs(obj, EShopType.SType_Items)


# Called whenever a player takes damage - use it to update health costs
@hook("WillowGame.WillowPlayerPawn:TakeDamage", Type.POST)
def player_pawn_take_damage(  # noqa: D103
    obj: UObject,
    _args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    update_vendor_costs(obj.Controller, EShopType.SType_Health)


# Negative costs don't display for the weapon/trash vendor, so no need to have a change hook for it

# ==================================================================================================


def on_enable() -> None:  # noqa: D103
    create_icons()


mod = build_mod()

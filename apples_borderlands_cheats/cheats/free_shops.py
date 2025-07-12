from typing import TYPE_CHECKING, Any

import unrealsdk
from mods_base import hook
from unrealsdk.hooks import Block, Type
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

from . import CyclableOption, OnOff

if TYPE_CHECKING:
    from enum import auto

    from unrealsdk.unreal._uenum import UnrealEnum  # pyright: ignore[reportMissingModuleSource]

    class EShopItemStatus(UnrealEnum):
        SIS_ItemCanBePurchased = auto()
        SIS_NotEnoughRoomForItem = auto()
        SIS_PlayerCannotAffordItem = auto()
        SIS_PlayerCannotUseItem = auto()
        SIS_InvalidItem = auto()
else:
    EShopItemStatus = unrealsdk.find_enum("EShopItemStatus")


@CyclableOption("Free Shops", OnOff.OFF, list(OnOff))
def free_shops(_: CyclableOption, new_value: str) -> None:  # noqa: D103
    if not free_shops.mod or not free_shops.mod.is_enabled:
        return

    match new_value:
        case OnOff.OFF:
            on_buy_pre.disable()
            on_buy_post.disable()
        case OnOff.On:
            on_buy_pre.enable()
            on_buy_post.enable()
        case _:
            pass


def free_shops_on_disable() -> None:  # noqa: D103
    on_buy_pre.disable()
    on_buy_post.disable()


@hook("WillowGame.WillowPlayerReplicationInfo:GetCurrencyOnHand")
def force_max_currency(*_: Any) -> tuple[type[Block], int]:  # noqa: D103
    return Block, 0x7FFFFFFF


@hook("WillowGame.WillowPlayerReplicationInfo:AddCurrencyOnHand")
def block_spend_currency(  # noqa: D103
    _obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> type[Block] | None:
    return Block if args.AddValue < 0 else None


# All these functions are various ways to spend money at a shop
# For the duration of their calls, pretend we have the max currency, and prevent spending any
@hook("WillowGame.WillowPlayerController:PlayerBuyBackInventory")
@hook("WillowGame.WillowPlayerController:ServerPlayerBoughtItem")
@hook("WillowGame.WillowPlayerController:ServerPlayerResetShop")
@hook("WillowGame.WillowPlayerController:ServerPurchaseBlackMarketUpgrade")
@hook("WillowGame.WillowPlayerController:ServerPurchaseSkillTreeReset")
# This one's just used to tell if you can afford the item in the shop - which we also want to force
@hook("WillowGame.WillowVendingMachineBase:GetItemStatus")
def on_buy_pre(*_: Any) -> None:  # noqa: D103
    force_max_currency.enable()
    block_spend_currency.enable()


@hook("WillowGame.WillowPlayerController:PlayerBuyBackInventory", Type.POST_UNCONDITIONAL)
@hook("WillowGame.WillowPlayerController:ServerPlayerBoughtItem", Type.POST_UNCONDITIONAL)
@hook("WillowGame.WillowPlayerController:ServerPlayerResetShop", Type.POST_UNCONDITIONAL)
@hook("WillowGame.WillowPlayerController:ServerPurchaseBlackMarketUpgrade", Type.POST_UNCONDITIONAL)
@hook("WillowGame.WillowPlayerController:ServerPurchaseSkillTreeReset", Type.POST_UNCONDITIONAL)
@hook("WillowGame.WillowVendingMachineBase:GetItemStatus", Type.POST_UNCONDITIONAL)
def on_buy_post(*_: Any) -> None:  # noqa: D103
    force_max_currency.disable()
    block_spend_currency.disable()

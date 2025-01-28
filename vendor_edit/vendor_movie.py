from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING, Any

import unrealsdk
from mods_base import get_pc, hook
from unrealsdk.hooks import Block, Type
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

from .packages import ROOT

if TYPE_CHECKING:
    from enum import auto

    from unrealsdk.unreal._uenum import UnrealEnum  # pyright: ignore[reportMissingModuleSource]

    class EShopItemStatus(UnrealEnum):
        SIS_ItemCanBePurchased = auto()
        SIS_NotEnoughRoomForItem = auto()
        SIS_PlayerCannotAffordItem = auto()
        SIS_PlayerCannotUseItem = auto()
        SIS_InvalidItem = auto()
        SIS_MAX = auto()

    class EShopType(UnrealEnum):
        SType_Weapons = auto()
        SType_Items = auto()
        SType_Health = auto()
        SType_BlackMarket = auto()
        SType_MAX = auto()

    class EInventorySortType(UnrealEnum):
        IST_EquippedThenMajorTypeThenRarityThenSubtype = auto()
        IST_MajorTypeThenSubtypeThenRarity = auto()
        IST_MajorTypeThenRarityThenSubtype = auto()
        IST_Manufacturer = auto()
        IST_ClassRequirementThenRarity = auto()
        IST_Value = auto()
        IST_MAX = auto()

else:
    EShopItemStatus = unrealsdk.find_enum("EShopItemStatus")
    EShopType = unrealsdk.find_enum("EShopType")
    EInventorySortType = unrealsdk.find_enum("EInventorySortType")

type WillowInventory = UObject
type VendingMachineExGFxDefinition = UObject

__all__: tuple[str, ...] = ("show",)

VENDOR_GFX_DEF_NAME = "vendor_gfx_def"
vendor_gfx_def: VendingMachineExGFxDefinition | None
try:
    vendor_gfx_def = unrealsdk.find_object(
        "VendingMachineExGFxDefinition",
        f"{ROOT.path_name}.{VENDOR_GFX_DEF_NAME}",
    )
except ValueError:
    vendor_gfx_def = None

# This is all designed around the assumption only one vendor movie's open at a time, keep track so
# we can throw
any_movie_active = False

# This means we keep a few params in global scope. Since it's a singleton, didn't really feel right
# using a class like in ui_utils

# We can't quite set the vendor contents at the moment we create the movie, need to wait a little
# past the end of the function call. These vars hold the contents while waiting on the hook - we
# invalidate them right after
pending_items: Sequence[WillowInventory] | None = None
pending_iotd: WillowInventory | None = None

# The callbacks we keep around for the full lifespan of the movie
on_purchase_callback: Callable[[WillowInventory], None] | None = None
on_cancel_callback: Callable[[], None] | None = None


def show(
    *,
    items: Sequence[WillowInventory],
    iotd: WillowInventory | None = None,
    on_purchase: Callable[[WillowInventory], None] | None = None,
    on_cancel: Callable[[], None] | None = None,
) -> None:
    """
    Shows the vendor movie.

    Args:
        items: The list of items to show.
        iotd: The item of the day, or None.
        on_purchase: A callback run when one of the items is purchased.
        on_cancel: A callback run when the menu is quit out of without purchasing anything.
    """
    global any_movie_active, pending_items, pending_iotd, on_purchase_callback, on_cancel_callback
    if any_movie_active:
        raise RuntimeError("cannot show two vendor movies at once")
    any_movie_active = True

    pending_items = items
    pending_iotd = iotd
    on_purchase_callback = on_purchase
    on_cancel_callback = on_cancel

    _on_start.enable()
    _init_iotd.enable()
    _refresh_left_panel.enable()
    _force_never_sell.enable()
    _block_refresh_timer.enable()
    _block_transient_refresh.enable()
    _refresh.enable()
    _on_purchase.enable()
    _on_close.enable()

    movie = get_pc().GFxUIManager.PlayMovie(get_gfx_def())

    movie.BlackMarketTitle = "EDIT"
    movie.StoragePanelLabel = "EDIT"
    movie.ItemOfTheDayLabel_BlackMarket = "No Change"
    movie.VisitLabel_BlackMarket = ""


def get_gfx_def() -> VendingMachineExGFxDefinition:
    """
    Gets the vendor gfx movie definition to use, constructing it if required.

    Returns:
        The vendor gfx movie definition.
    """
    global vendor_gfx_def
    if vendor_gfx_def is None:
        # TODO: other games
        unrealsdk.load_package("Sanctuary_P")
        unrealsdk.load_package("Sanctuary_Dynamic")

        black_market = unrealsdk.find_object(
            "VendingMachineExGFxDefinition",
            "UI_VendingMachine.VendingMachineDef_BlackMarket",
        )
        vendor_gfx_def = unrealsdk.construct_object(
            black_market.Class,
            ROOT.unreal,
            VENDOR_GFX_DEF_NAME,
            0x4000,
            black_market,
        )
        vendor_gfx_def.bCustomStoragePanelTint = True
        vendor_gfx_def.bShouldAllowCompare = True
        vendor_gfx_def.bShouldShowAmmoPanel = False

        tint = vendor_gfx_def.CustomStoragePanelTint
        tint.R = 255
        tint.G = 255
        tint.B = 0
        tint.A = 100

    return vendor_gfx_def


@hook("WillowGame.VendingMachineExGFxMovie:Start", Type.POST)
def _on_start(
    obj: UObject,
    _args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    _on_start.disable()
    # Force the shop type back to black market after regular initialization
    obj.ShopType = EShopType.SType_BlackMarket


@hook("WillowGame.VendingMachineExGFxMovie:extInitItemOfTheDayPanel")
def _init_iotd(
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> type[Block]:
    _init_iotd.disable()

    iotd_panel = obj.GetVariableObject(
        args.ItemOfTheDayPanelPath,
        unrealsdk.find_class("ItemOfTheDayPanelGFxObject"),
    )
    obj.ItemOfTheDayPanel = iotd_panel
    iotd_panel.Init(obj)

    global pending_iotd

    iotd = obj.ItemOfTheDayData
    iotd.Item = pending_iotd
    iotd.Price = 0
    iotd.ItemStatus = EShopItemStatus.SIS_ItemCanBePurchased

    iotd_panel.SetItemOfTheDayItem(pending_iotd)

    obj.ConfigureForType_IOTD()

    pending_iotd = None
    return Block


SORT_CONFIG = unrealsdk.make_struct(
    "SortFilterConfiguration",
    # For some reason the two `MajorTypeThenRarity` types have an unstable sort order, we can redraw
    # the exact same list and they end up in different positions. Manufacturer seems like it'll be
    # the most stable.
    SortType=EInventorySortType.IST_Manufacturer,
    SortTitleLookupKey="all",
)


@hook("WillowGame.TwoPanelInterfaceGFxObject:RefreshLeftPanel")
def _refresh_left_panel(
    obj: UObject,
    _args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> type[Block]:
    # This is called any time you return to the vendor after comparing, so need to keep it
    # active the whole time

    vendor_movie = obj.TwoPanelInterface
    storage_panel = obj.StoragePanel

    current_index = storage_panel.CurrentSelectedIndex

    global pending_items
    if pending_items is not None:
        # Adding the items to the storage panel list is what actually gets them to show up, but they
        # get cleared from time to time
        storage_panel.SetList(pending_items, SORT_CONFIG, 0)

        # So also keep a backup reference to each item in the vendor movie, to keep them all alive
        vendor_movie.ShopItems = [
            unrealsdk.make_struct(
                "ShopItemData",
                Item=item,
                Price=0,
                ItemStatus=EShopItemStatus.SIS_ItemCanBePurchased,
            )
            for item in pending_items
        ]

        pending_items = None
    else:
        # Restore from our backup list
        storage_panel.SetList([x.Item for x in vendor_movie.ShopItems], SORT_CONFIG, 0)

    # This has to be a setattr to avoid name mangling
    storage_panel.__OnListSort__Delegate = obj.OnListSort
    storage_panel.CurrentSelectedIndex = current_index
    storage_panel.FixupSelectedIndex()
    obj.bLeftPanelRefreshed = True

    return Block


# We'll be filling the vendor with items technically owned by the player. Force these to be shown as
# buyables, instead of sellables
@hook("WillowGame.VendingMachineExGFxMovie:IsCurrentSelectionSell")
def _force_never_sell(*_: Any) -> tuple[type[Block], bool]:
    return Block, False


# The menu normally sets up a timer to constantly refresh its contents, in case the vending
# machine cycled. We try block all this best we can, so the items we set on init are the ones
# which stay there


@hook("WillowGame.VendingMachineExGFxMovie:SetVendingMachineRefreshTimer")
def _block_refresh_timer(*_: Any) -> type[Block]:
    _block_refresh_timer.disable()
    return Block


# Block any stray calls
@hook("WillowGame.VendingMachineExGFxMovie:RefreshTransientData")
def _block_transient_refresh(*_: Any) -> type[Block]:
    return Block


# This one is called for regular refreshes, e.g. when finishing comparing, so we do need to do some
# things, but don't overwrite the item lists like the default one does
@hook("WillowGame.VendingMachineExGFxMovie:Refresh")
def _refresh(
    obj: UObject,
    _args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> type[Block]:
    two_panel = obj.TwoPanelInterface
    two_panel.Refresh()

    if two_panel.bOnLeftPanel and obj.bOnItemOfTheDay:
        obj.SwitchToItemOfTheDay()

    obj.SetCreditsDisplay()
    obj.EvaluateCurrentSelection()

    return Block


# Purchasing something normally goes though `ConditionalStartTransfer`, which is a big complex
# function that'd be annoying to hook. Luckily for us, on a successful purchase it schedules a timer
# to call this function 0.1s later - which is actually perfect since it gives a bit of time for the
# animation/sound effect before we close the menu.
@hook("WillowGame.VendingMachineExGFxMovie:CheckShopOpStatus")
def _on_purchase(
    obj: UObject,
    _args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    # Since we don't have a real vendor hooked up, purchasing doesn't actually do anything, it's
    # still the currently selected item
    selection = obj.CurrentSelectionItem
    if selection is None:
        return

    global on_cancel_callback, on_purchase_callback
    on_purchase = on_purchase_callback
    on_cancel = on_cancel_callback

    on_purchase_callback = None
    on_cancel_callback = None

    obj.Close()

    # If you purchased the original item, treat it as a cancel
    if selection == obj.ItemOfTheDayData.Item:
        if on_cancel is not None:
            on_cancel()
    elif on_purchase is not None:
        on_purchase(selection)


@hook("WillowGame.VendingMachineExGFxMovie:OnClose", Type.POST)
def _on_close(*_: Any) -> None:
    # Make sure all the hooks are off when we finally close the movie
    _on_start.disable()
    _init_iotd.disable()
    _refresh_left_panel.disable()
    _force_never_sell.disable()
    _block_refresh_timer.disable()
    _block_transient_refresh.disable()
    _refresh.disable()
    _on_purchase.disable()
    _on_close.disable()

    global any_movie_active, on_purchase_callback, on_cancel_callback
    any_movie_active = False

    if on_cancel_callback is not None:
        on_cancel_callback()
    on_purchase_callback = None
    on_cancel_callback = None

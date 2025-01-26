from typing import TYPE_CHECKING, Any

import unrealsdk
from mods_base import build_mod, get_pc, hook, keybind
from unrealsdk.hooks import Block, Type
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

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

    class EPlayerDroppability(UnrealEnum):
        EPD_Droppable = auto()
        EPD_Sellable = auto()
        EPD_CannotDropOrSell = auto()
        EPD_MAX = auto()

else:
    EShopItemStatus = unrealsdk.find_enum("EShopItemStatus")
    EShopType = unrealsdk.find_enum("EShopType")
    EPlayerDroppability = unrealsdk.find_enum("EPlayerDroppability")

try:
    vendor_gfx_def = unrealsdk.find_object(
        "VendingMachineExGFxDefinition",
        "UI_VendingMachine.vendor_edit_def",
    )
except ValueError:
    vendor_gfx_def = None


@keybind("go")
def go() -> None:  # noqa: D103
    global vendor_gfx_def
    if vendor_gfx_def is None:
        unrealsdk.load_package("Sanctuary_Dynamic")
        black_market = unrealsdk.find_object(
            "VendingMachineExGFxDefinition",
            "UI_VendingMachine.VendingMachineDef_BlackMarket",
        )
        vendor_gfx_def = unrealsdk.construct_object(
            black_market.Class,
            black_market.Outer,
            "vendor_edit_def",
            0x4000,
            black_market,
        )
        vendor_gfx_def.bShouldAllowCompare = True
        vendor_gfx_def.bShouldShowAmmoPanel = False

    on_start.enable()
    init_iotd.enable()
    refresh_left.enable()
    init_items.enable()
    block_refresh_timer.enable()
    block_transient_refresh.enable()
    handle_menu_refresh.enable()
    on_close.enable()
    get_pc().GFxUIManager.PlayMovie(vendor_gfx_def)


def get_items_to_sell() -> list[UObject]:  # noqa: D103
    _, readied_weapons, unreadied_weapons, all_items = get_pc().GetInventoryLists(
        (),
        (),
        (),
        EPlayerDroppability.EPD_CannotDropOrSell,
    )
    return readied_weapons + unreadied_weapons + all_items


@hook("WillowGame.VendingMachineExGFxMovie:Start", Type.POST)
def on_start(  # noqa: D103
    obj: UObject,
    _args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    on_start.disable()
    obj.ShopType = EShopType.SType_BlackMarket


@hook("WillowGame.VendingMachineExGFxMovie:extInitItemOfTheDayPanel")
def init_iotd(  # noqa: D103
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> type[Block]:
    init_iotd.disable()

    obj.ItemOfTheDayLabel_BlackMarket = "Original Item"

    iotd_panel = obj.GetVariableObject(
        args.ItemOfTheDayPanelPath,
        unrealsdk.find_class("ItemOfTheDayPanelGFxObject"),
    )
    obj.ItemOfTheDayPanel = iotd_panel
    iotd_panel.Init(obj)

    weapon = obj.WPCOwner.GetPawnInventoryManager().InventoryChain

    iotd = obj.ItemOfTheDayData
    iotd.Item = weapon
    iotd.Price = 0
    iotd.ItemStatus = EShopItemStatus.SIS_InvalidItem

    iotd_panel.SetItemOfTheDayItem(weapon)

    obj.ConfigureForType_IOTD()
    obj.UpdateTimeRemaining()

    if (custom_iotd_movid := obj.VMGFxDef.CustomIOTDMovie) is not None:
        iotd_panel.SetBackgroundClip(custom_iotd_movid)

    return Block


@hook("WillowGame.TwoPanelInterfaceGFxObject:RefreshLeftPanel")
def refresh_left(  # noqa: D103
    obj: UObject,
    _args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> type[Block]:
    storage_panel = obj.StoragePanel
    _, config = obj.TwoPanelInterface.GetSortConfigDataForPanel(
        storage_panel,
        unrealsdk.make_struct("SortFilterConfiguration"),
    )

    current_index = storage_panel.CurrentSelectedIndex

    storage_panel.SetList(get_items_to_sell(), config, 0)

    storage_panel.__OnListSort__Delegate = obj.OnListSort
    storage_panel.CurrentSelectedIndex = current_index
    storage_panel.FixupSelectedIndex()
    obj.bLeftPanelRefreshed = True

    return Block


@hook("WillowGame.VendingMachineExGFxMovie:GetStoragePanelItems")
def init_items(  # noqa: D103
    obj: UObject,
    _args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> type[Block]:
    init_items.disable()

    obj.ShopItems = [
        unrealsdk.make_struct(
            "ShopItemData",
            Item=item,
            Price=2222,
            ItemStatus=EShopItemStatus.SIS_InvalidItem,
        )
        for item in get_items_to_sell()
    ]

    return Block


@hook("WillowGame.VendingMachineExGFxMovie:SetVendingMachineRefreshTimer")
def block_refresh_timer(*_: Any) -> type[Block]:  # noqa: D103
    block_refresh_timer.disable()
    return Block


@hook("WillowGame.VendingMachineExGFxMovie:RefreshTransientData")
def block_transient_refresh(*_: Any) -> type[Block]:  # noqa: D103
    return Block


@hook("WillowGame.VendingMachineExGFxMovie:Refresh")
def handle_menu_refresh(  # noqa: D103
    obj: UObject,
    _args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> type[Block]:
    two_panel = obj.TwoPanelInterface
    two_panel.Refresh()

    # TODO: on item of the day becomes false  # noqa: FIX002, TD002, TD003
    if two_panel.bOnLeftPanel and obj.bOnItemOfTheDay:
        obj.SwitchToItemOfTheDay()

    obj.SetCreditsDisplay()
    obj.EvaluateCurrentSelection()

    return Block


@hook("WillowGame.VendingMachineExGFxMovie:OnClose", Type.POST)
def on_close(*_: Any) -> None:  # noqa: D103
    block_transient_refresh.disable()
    refresh_left.disable()
    handle_menu_refresh.disable()
    on_close.disable()


build_mod(hooks=[])

from typing import TYPE_CHECKING, Any

import unrealsdk
from mods_base import BoolOption, EInputEvent, KeybindOption, get_pc, hook
from unrealsdk.hooks import Block, Type, prevent_hooking_direct_calls
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

from .editor import open_editor_menu
from .replacement_lists import can_create_replacements

if TYPE_CHECKING:
    from enum import auto

    from unrealsdk.unreal._uenum import UnrealEnum  # pyright: ignore[reportMissingModuleSource]

    class EBackButtonScreen(UnrealEnum):
        CS_None = auto()
        CS_MissionLog = auto()
        CS_Map = auto()
        CS_Inventory = auto()
        CS_Skills = auto()
        CS_Challenges = auto()
        CS_MAX = auto()

else:
    EBackButtonScreen = unrealsdk.find_enum("EBackButtonScreen")

type WillowInventory = UObject

__all__: tuple[str, ...] = (
    "hooks",
    "options",
)

reopen_inv_option = BoolOption(
    "Reopen Inventory After Editing",
    True,
    description="If to re-open your inventory after you finish editing an item.",
)
bind_option = KeybindOption(
    "Edit Item Keybind",
    "Backslash",
    description="While in your inventory, press this key on an item to start editing.",
)


@hook("WillowGame.StatusMenuExGFxMovie:SetInventoryTooltipsText")
def start_update_tooltips(
    _obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    if bind_option.value is not None:
        if args.WInv is not None and can_create_replacements(args.WInv):
            adjust_tooltips_usable.enable()
        else:
            adjust_tooltips_disabled.enable()


@hook("WillowGame.StatusMenuExGFxMovie:SetInventoryTooltipsText", Type.POST_UNCONDITIONAL)
def stop_update_tooltips(*_: Any) -> None:
    adjust_tooltips_usable.disable()
    adjust_tooltips_disabled.disable()


def adjust_tooltips_common(
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    func: BoundFunction,
    disabled: bool,
) -> tuple[type[Block], str]:
    edit_text = obj.ColorizeTooltipText(f"[{bind_option.value}] Edit", disabled)
    with prevent_hooking_direct_calls():
        return Block, func(f"{args.Markup}  {edit_text}")


@hook("GFxUI.GFxMoviePlayer:ResolveDataStoreMarkup")
def adjust_tooltips_usable(
    obj: UObject,
    args: WrappedStruct,
    ret: Any,
    func: BoundFunction,
) -> tuple[type[Block], str]:
    return adjust_tooltips_common(obj, args, ret, func, False)


@hook("GFxUI.GFxMoviePlayer:ResolveDataStoreMarkup")
def adjust_tooltips_disabled(
    obj: UObject,
    args: WrappedStruct,
    ret: Any,
    func: BoundFunction,
) -> tuple[type[Block], str]:
    return adjust_tooltips_common(obj, args, ret, func, True)


item_to_edit: WillowInventory | None = None


@hook("WillowGame.StatusMenuExGFxMovie:HandleInputKey")
def handle_edit_press(
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> tuple[type[Block], bool] | None:
    if obj.CurrentScreen != EBackButtonScreen.CS_Inventory:
        return None

    if not (args.ukey == bind_option.value and args.uevent == EInputEvent.IE_Released):
        return None

    item = obj.InventoryPanel.GetSelectedThing()
    if item is None:
        return None

    if not can_create_replacements(item):
        return None

    # If we immediately opening the edit menu, closing it compeltely loses focus and you lose all
    # control. Instead just cache this item for a split second until after the `OnClose` call.
    global item_to_edit
    item_to_edit = item
    on_close_to_edit.enable()

    obj.Hide()
    return Block, True


@hook("WillowGame.StatusMenuExGFxMovie:OnClose", Type.POST)
def on_close_to_edit(*_: Any) -> None:
    on_close_to_edit.disable()

    global item_to_edit
    if item_to_edit is not None:

        def on_finish() -> None:
            pc = get_pc()
            pc.QuickAccessScreen = EBackButtonScreen.CS_Inventory
            pc.GetPlayerViewportClient().ViewportUI.RunStatusMenu(pc)

        open_editor_menu(item_to_edit, on_finish if reopen_inv_option.value else None)
        item_to_edit = None


hooks = [start_update_tooltips, stop_update_tooltips, handle_edit_press]
options = [reopen_inv_option, bind_option]

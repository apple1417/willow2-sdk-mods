from typing import Any

import unrealsdk
from mods_base import (
    BaseOption,
    EInputEvent,
    Game,
    HookType,
    KeybindOption,
    hook,
)
from ui_utils import clipboard_copy, clipboard_paste, show_chat_message
from unrealsdk import logging
from unrealsdk.hooks import Block, Type, Unset, prevent_hooking_direct_calls
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

from .editor import EBackButtonScreen, open_editor_menu
from .item_codes import UnpackResult, pack_item_code, unpack_item_code

type StatusMenuExGFxMovie = UObject
type WillowInventory = UObject

__all__: tuple[str, ...] = (
    "hooks",
    "options",
)

edit_bind = KeybindOption(
    "Edit Item",
    "F9",
    description="While in your inventory, press this key on an item to start editing.",
)
copy_bind = KeybindOption(
    "Copy Code",
    "F10",
    description="While in your inventory, press this key to copy an item's code.",
)
paste_bind = KeybindOption(
    "Paste Code",
    "F11",
    description="While in your inventory, press this key to paste an item code.",
)

# The actual SetInventoryTooltipsText implementation is very complex. Rather than replicating, just
# trigger another hook right at the end when we have the final string.
# This hook doesn't have access to the selected item in the arg, which we need to work out which
# tooltips to enable, so we create the tooltips first in the outer hook, and inject them in the
# inner one
_pending_extra_tooltips: list[str] = []


@hook("WillowGame.StatusMenuExGFxMovie:SetInventoryTooltipsText")
def start_update_tooltips(
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    inv: WillowInventory | None = args.WInv

    _pending_extra_tooltips.clear()

    if edit_bind.value is not None:
        _pending_extra_tooltips.append(
            obj.ColorizeTooltipText(
                f"[{edit_bind.value}] {edit_bind.display_name}",
                bDisabled=inv is None,
            ),
        )

    if copy_bind.value is not None:
        _pending_extra_tooltips.append(
            obj.ColorizeTooltipText(
                f"[{copy_bind.value}] {copy_bind.display_name}",
                bDisabled=inv is None,
            ),
        )

    if paste_bind.value is not None:
        _pending_extra_tooltips.append(
            obj.ColorizeTooltipText(
                f"[{paste_bind.value}] {paste_bind.display_name}",
                bDisabled=False,
            ),
        )

    if _pending_extra_tooltips:
        adjust_tooltips.enable()


@hook("WillowGame.StatusMenuExGFxMovie:SetInventoryTooltipsText", Type.POST_UNCONDITIONAL)
def stop_update_tooltips(*_: Any) -> None:
    adjust_tooltips.disable()


@hook("GFxUI.GFxMoviePlayer:ResolveDataStoreMarkup")
def adjust_tooltips(
    _obj: UObject,
    args: WrappedStruct,
    ret: Any,
    func: BoundFunction,
) -> tuple[type[Block], str]:
    original_markup: str
    if ret is Unset:
        with prevent_hooking_direct_calls():
            original_markup = func(args)
    else:
        original_markup = ret

    with prevent_hooking_direct_calls():
        extra_tooltips: str = func("    ".join(_pending_extra_tooltips))

    if ret is Unset:
        # If we have a single extra tooltip, put it on the same line
        if len(_pending_extra_tooltips) == 1:
            return Block, original_markup + "  " + extra_tooltips
        # If we have multiple, put them all on the second
        return Block, original_markup + "\n" + extra_tooltips

    # If another function added it's own tooltips to a new line, just add ours on the end
    if "\n" in original_markup:
        return Block, original_markup + "    " + extra_tooltips

    # If it added it on the same line, add all of ours, even if it's just one, to the second line
    return Block, original_markup + "\n" + extra_tooltips


@hook("WillowGame.StatusMenuExGFxMovie:HandleInputKey")
def handle_menu_input(
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> tuple[type[Block], bool] | None:
    if obj.CurrentScreen != EBackButtonScreen.CS_Inventory:
        return None

    key: str = args.ukey
    event: EInputEvent = args.uevent

    match key, event:
        case edit_bind.value, EInputEvent.IE_Released:
            return handle_edit_press(obj)
        case copy_bind.value, EInputEvent.IE_Released:
            return handle_copy_press(obj)
        case paste_bind.value, EInputEvent.IE_Released:
            return handle_paste_press(obj)
        case _:
            return None


# If we immediately opening the edit menu, closing it completely loses focus and you lose all
# control. Instead we just cache this item for a split second, until after the `OnClose` call.
_item_to_edit: WillowInventory | None = None


def handle_edit_press(obj: StatusMenuExGFxMovie) -> tuple[type[Block], bool] | None:
    """
    Handles an "Edit Item" press.

    Args:
        obj: The current inventory movie object.
    Returns:
        The hook's return value.
    """
    item = obj.InventoryPanel.GetSelectedThing()
    if item is None:
        return None

    global _item_to_edit
    _item_to_edit = item
    on_close_to_edit.enable()

    obj.Hide()
    return Block, True


@hook("WillowGame.StatusMenuExGFxMovie:OnClose", Type.POST)
def on_close_to_edit(*_: Any) -> None:
    on_close_to_edit.disable()

    global _item_to_edit
    if _item_to_edit is not None:
        open_editor_menu(_item_to_edit)
        _item_to_edit = None


def handle_copy_press(obj: StatusMenuExGFxMovie) -> tuple[type[Block], bool] | None:
    """
    Handles a "Copy Code" press.

    Args:
        obj: The current inventory movie object.
    Returns:
        The hook's return value.
    """
    item = obj.InventoryPanel.GetSelectedThing()
    if item is None:
        return None

    name = item.GetShortHumanReadableName()
    code = pack_item_code(item.DefinitionData)
    clipboard_copy(code)

    logging.info(f"Serial code for {name}: {code}")
    show_chat_message(f"Copied code for {name}", user="[Vendor Edit]", timestamp=None)

    return Block, True


def chat_error_for_item_paste(result: UnpackResult) -> None:
    """
    Writes the error message (if any) for the given unpack result to chat.

    Args:
        result: The result of trying to unpack an item code.
    """
    match result:
        case UnpackResult.FULL_WEAPON | UnpackResult.FULL_ITEM:
            return

        case UnpackResult.NO_MATCH:
            msg = "Couldn't find an item code in your clipboard"
        case UnpackResult.WRONG_GAME:
            msg = f"Item code was not for {Game.get_current().name}"
        case UnpackResult.MALFORMED_CODE | UnpackResult.GAME_REJECTED_CODE:
            msg = "Item code was corrupt"
        case UnpackResult.PARTIAL_WEAPON | UnpackResult.PARTIAL_ITEM:
            msg = (
                "Some modded parts were not found, and were ignored. Are you running the right"
                " mods?"
            )

    show_chat_message(msg, user="[Vendor Edit]", timestamp=None)


CREATE_WEAPON_FROM_DEF = unrealsdk.find_class("WillowWeapon").ClassDefaultObject.CreateWeaponFromDef
CREATE_ITEM_FROM_DEF = unrealsdk.find_class("WillowItem").ClassDefaultObject.CreateItemFromDef


def handle_paste_press(obj: StatusMenuExGFxMovie) -> tuple[type[Block], bool] | None:
    """
    Handles a "Paste Code" press.

    Args:
        obj: The current inventory movie object.
    Returns:
        The hook's return value.
    """
    code = clipboard_paste()
    if code is None:
        chat_error_for_item_paste(UnpackResult.NO_MATCH)
        return Block, True

    result, def_data = unpack_item_code(code)
    chat_error_for_item_paste(result)

    owner = obj.WPCOwner.Pawn

    match result:
        case UnpackResult.FULL_WEAPON | UnpackResult.PARTIAL_WEAPON:
            item = CREATE_WEAPON_FROM_DEF(
                NewWeaponDef=def_data,
                PlayerOwner=owner,
                bForceSelectNameParts=True,
            )
        case UnpackResult.FULL_ITEM | UnpackResult.PARTIAL_ITEM:
            item = CREATE_ITEM_FROM_DEF(
                NewItemDef=def_data,
                PlayerOwner=owner,
                NewQuantity=1,
                bForceSelectNameParts=True,
            )

        case _:
            return Block, True

    owner.InvManager.AddInventoryToBackpack(item)
    item.Owner = owner

    global _item_to_edit
    _item_to_edit = item
    on_close_to_edit.enable()

    obj.Hide()
    return Block, True


hooks: tuple[HookType, ...] = (start_update_tooltips, stop_update_tooltips, handle_menu_input)
options: tuple[BaseOption, ...] = (edit_bind, copy_bind, paste_bind)

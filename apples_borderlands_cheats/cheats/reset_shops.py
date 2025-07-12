import unrealsdk
from mods_base import keybind
from ui_utils import show_hud_message


@keybind("Reset Shops")
def reset_shops() -> None:  # noqa: D103
    count = 0
    for obj in unrealsdk.find_all("WillowVendingMachine"):
        if obj.Name == "Default__WillowVendingMachine":
            continue
        count += 1
        obj.ResetInventory()

    show_hud_message("Reset Shops", f"Reset {count} shops")

from mods_base import get_pc, keybind
from ui_utils import show_hud_message


@keybind("Add OP Level")
def add_op_level() -> None:  # noqa: D103
    pri = (pc := get_pc()).PlayerReplicationInfo
    if pri.NumOverpowerLevelsUnlocked == pc.GetMaximumPossibleOverpowerModifier():
        show_hud_message("Add OP Level", "You are already at the maximum OP level")
    else:
        pri.NumOverpowerLevelsUnlocked += 1
        show_hud_message(
            "Add OP Level",
            f"You have now unlocked OP {pri.NumOverpowerLevelsUnlocked}",
        )

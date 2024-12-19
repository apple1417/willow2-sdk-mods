import sys
from pathlib import Path

from mods_base import deregister_mod, register_mod

from .anti_circular_import import TextModState, all_text_mods
from .text_mod import TextMod

BINARIES_DIR = Path(sys.executable).parent.parent


def load_all_text_mods(auto_enable: bool) -> None:
    """
    (Re-)Loads all text mods from binaries.

    Args:
        auto_enable: If to enable any mods marked as such in the settings file.
    """
    # Iterate through a copy so we can delete while iterating
    for mod in list(all_text_mods.values()):
        mod.check_deleted()

        match mod.state:
            # Delete what mods we can
            case (
                TextModState.Disabled
                | TextModState.LockedHotfixes
                | TextModState.LockedBadService
                | TextModState.DeletedInactive
            ):
                all_text_mods.pop(mod.file)
                deregister_mod(mod)

            # Need to keep any active mods around in the list
            case TextModState.Enabled | TextModState.DisableOnRestart | TextModState.DeletedActive:
                pass

    for entry in BINARIES_DIR.iterdir():
        if not entry.is_file():
            continue

        # Don't reload active mods
        if entry in all_text_mods:
            continue

        # load metadata

        mod = TextMod(
            name=entry.name,
            file=entry,
            spark_service_idx=None,
            recommended_game=None,
            internal_description=None,
        )

        _ = auto_enable

        all_text_mods[entry] = mod
        register_mod(mod)

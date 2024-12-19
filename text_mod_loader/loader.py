import sys
from pathlib import Path

from mods_base import deregister_mod, register_mod

from .anti_circular_import import TextModState, all_text_mods
from .settings import ModInfo, get_cached_mod_info, update_cached_mod_info
from .text_mod import TextMod

BINARIES_DIR = Path(sys.executable).parent.parent


def load_mod_info(path: Path) -> ModInfo:
    """
    Loads metadata for a specific mod.

    Args:
        path: The path to load from.
    Returns:
        The loaded mod info.
    """
    return {
        "modify_time": path.stat().st_mtime,
        "ignore_me": False,
        "spark_service_idx": None,
        "recommended_game": None,
        "title": path.name,
        "author": "Text Mod Loader",
        "version": "",
        "description": "",
    }


def load_all_text_mods() -> None:
    """(Re-)Loads all text mods from binaries."""
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

        if (mod_info := get_cached_mod_info(entry)) is None:
            mod_info = load_mod_info(entry)
            update_cached_mod_info(entry, mod_info)

        if mod_info["ignore_me"]:
            continue

        mod = TextMod(
            name=mod_info["title"],
            author=mod_info["author"],
            version=mod_info["version"],
            file=entry,
            spark_service_idx=mod_info["spark_service_idx"],
            recommended_game=mod_info["recommended_game"],
            internal_description=mod_info["description"],
        )

        all_text_mods[entry] = mod
        register_mod(mod)

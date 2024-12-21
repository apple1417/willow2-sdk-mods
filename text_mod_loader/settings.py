from __future__ import annotations

from contextlib import contextmanager, suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypedDict

from mods_base import BaseOption, Game, HiddenOption

if TYPE_CHECKING:
    from collections.abc import Iterator

    from .text_mod import TextMod

CURRENT_MOD_INFO_VERSION: int = 2


class ModInfo(TypedDict):
    modify_time: float
    ignore_me: bool

    spark_service_idx: int | None
    recommended_game: Game | None

    title: str
    author: str
    version: str
    description: str


auto_enable = HiddenOption[list[str]]("auto_enable", [])
mod_info = HiddenOption[dict[str, dict[str, Any]]]("mod_info", {})

# Default to 0 so if it's unset we always consider us to have updated
version = HiddenOption[int]("version", 0)

all_settings: tuple[BaseOption, ...] = (
    auto_enable,
    mod_info,
    version,
)

suppress_auto_enable_update_counter: int = 0


def sanitize_settings() -> None:
    """
    Sanitizes the mod file paths we're storing in settings.

    Normalizes mod file paths them, and removes any for mod files which no longer exist on disk.
    Clears cached mod info on TML updates.
    """

    # If we've updated (in either direction), clear all cached mod info so we re-gather it with the
    # current version's logic
    if version.value != CURRENT_MOD_INFO_VERSION:
        mod_info.value.clear()
    version.value = CURRENT_MOD_INFO_VERSION

    auto_enable.value = [
        str(path.resolve())
        for x in auto_enable.value
        if (path := Path(x)).exists() and path.is_file()
    ]
    mod_info.value = {
        str(path.resolve()): v
        for k, v in mod_info.value.items()
        if (path := Path(k)).exists() and path.is_file()
    }

    # Since all settings are associated with the same mod, only need to call one
    mod_info.save()


def change_mod_auto_enable(mod: TextMod, enable: bool) -> None:
    """
    Changes if a mod should be auto-enabled.

    Args:
        mod: The mod to edit.
        enable: True if the mod should auto-enable.
    """
    if suppress_auto_enable_update_counter > 0:
        return

    path = str(mod.file.resolve())

    # If we're adding, remove it first anyway to make sure it gets pushed to the end
    with suppress(ValueError):
        auto_enable.value.remove(path)

    if enable:
        auto_enable.value.append(path)

    auto_enable.save()


@contextmanager
def suppress_auto_enable_updates() -> Iterator[None]:
    """Context manager which suppresses any changes to the auto enabled mod list while active."""
    global suppress_auto_enable_update_counter
    suppress_auto_enable_update_counter += 1
    yield
    suppress_auto_enable_update_counter -= 1


def iter_auto_enabled_paths() -> Iterator[Path]:
    """
    Gets the mod file paths which should auto-enable.

    Yields:
        The mod file paths
    """
    yield from (Path(x) for x in auto_enable.value)


def get_cached_mod_info(path: Path) -> ModInfo | None:
    """
    If we have the mod info for the given path cached, gets it.

    Args:
        path: The path to check for mod info on.
    Returns:
        The mod info, or None if not cached.
    """
    if (raw_dict := mod_info.value.get(str(path.resolve()))) is None:
        return None

    # This is the only one we need to convert types on
    raw_dict["recommended_game"] = Game.__members__.get(raw_dict["recommended_game"])

    # Set some sane defaults.
    # Not going to bother with more in depth sanity checking since it's really your fault if you're
    # messing the settings manually
    cached_info: ModInfo = {
        "modify_time": 0,
        "ignore_me": False,
        "spark_service_idx": None,
        "recommended_game": None,
        "title": path.name,
        "author": "Text Mod Loader",
        "version": "",
        "description": "",
    } | raw_dict  # type: ignore

    # If the file has been modified since we cached it, we can't trust our info
    if path.stat().st_mtime > cached_info["modify_time"]:
        return None

    return cached_info


def update_cached_mod_info(path: Path, info: ModInfo) -> None:
    """
    Cache the mod info for the given path.

    Args:
        path: The path to cache under.
        info: The info to cache.
    """
    mod_info.value[str(path.resolve())] = {
        "modify_time": info["modify_time"],
        "ignore_me": info["ignore_me"],
        "spark_service_idx": info["spark_service_idx"],
        "recommended_game": None if (game := info["recommended_game"]) is None else game.name,
        "title": info["title"],
        "author": info["author"],
        "version": info["version"],
        "description": info["description"],
    }

    mod_info.save()

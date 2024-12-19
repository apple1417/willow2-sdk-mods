from __future__ import annotations

from contextlib import contextmanager, suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypedDict

from mods_base import BaseOption, HiddenOption

if TYPE_CHECKING:
    from collections.abc import Iterator

    from .text_mod import TextMod


# Mark this as non total just to make sure we check everything, in case someone does manual edits
class ModInfo(TypedDict, total=False):
    modify_time: float
    spark_service_idx: int | None
    recommended_game: str | None

    ignore_me: bool

    title: str
    author: str
    version: str
    description: str


auto_enable = HiddenOption[list[str]]("auto_enable", [])
mod_info = HiddenOption[dict[str, dict[str, Any]]]("mod_info", {})

all_settings: tuple[BaseOption, ...] = (
    auto_enable,
    mod_info,
)

suppress_auto_enable_update_counter: int = 0


def sanitize_mod_paths() -> None:
    """
    Sanitizes the mod file paths we're storing in settings.

    Normalizes them, and removes any for mod files which no longer exist on disk.
    """

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

    # Since both settings are associated with the same mod, only need to call one
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

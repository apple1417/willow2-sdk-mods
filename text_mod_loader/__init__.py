# ruff: noqa: D103

if True:
    assert __import__("mods_base").__version_info__ >= (1, 5), "Please update the SDK"

from typing import Any

from legacy_compat import add_compat_module
from mods_base import ButtonOption, Library, build_mod, hook

from . import legacy_compat as tml_legacy_compat
from .loader import all_text_mods, load_all_text_mods
from .settings import (
    all_settings,
    iter_auto_enabled_paths,
    sanitize_settings,
    suppress_auto_enable_updates,
)

__version__: str
__version_info__: tuple[int, ...]


# This hook fires on the main menu - importantly after all the main packages have been loaded and
# after receiving hotfixes. This is the earliest we can safely auto enable text mods.
@hook("WillowGame.FrontendGFxMovie:Start")
def auto_enable_hook(*_: Any) -> None:
    with suppress_auto_enable_updates():
        for path in iter_auto_enabled_paths():
            if (text_mod := all_text_mods.get(path)) is not None:
                text_mod.enable()

    # Don't re-run if the user quits back to title
    auto_enable_hook.disable()


@ButtonOption("Reload Text Mods")
def reload(_: ButtonOption) -> None:
    mod.load_settings()
    sanitize_settings()

    load_all_text_mods()


mod = build_mod(
    cls=Library,
    options=[reload, *all_settings],
)
sanitize_settings()
load_all_text_mods()

add_compat_module("Mods.TextModLoader", tml_legacy_compat)

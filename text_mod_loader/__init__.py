# ruff: noqa: D103

if True:
    assert __import__("mods_base").__version_info__ >= (1, 5), "Please update the SDK"

from mods_base import ButtonOption, Library, build_mod

from .loader import load_all_text_mods

__version__: str
__version_info__: tuple[int, ...]

reload_option = ButtonOption("Reload Text Mods", on_press=lambda _: load_all_text_mods(False))

mod = build_mod(cls=Library)
load_all_text_mods(True)

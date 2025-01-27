from mods_base import build_mod

from . import bugfix, hooks
from .editor import open_editor_menu

__version__: str
__version_info__: tuple[int, ...]
__all__: tuple[str, ...] = (
    "mod",
    "open_editor_menu",
)


mod = build_mod(
    options=(*hooks.options,),
    hooks=(
        *hooks.hooks,
        *bugfix.hooks,
    ),
)

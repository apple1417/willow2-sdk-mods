from mods_base import build_mod

from . import bugfix, editor, hooks, item_codes
from .editor import open_editor_menu

__version__: str
__version_info__: tuple[int, ...]

__all__: tuple[str, ...] = (
    "item_codes",
    "open_editor_menu",
)


mod = build_mod(
    options=(
        *editor.options,
        *hooks.options,
    ),
    hooks=(
        *hooks.hooks,
        *bugfix.hooks,
    ),
)

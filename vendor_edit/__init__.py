from mods_base import build_mod

from . import bugfix, editor, hooks
from .editor import open_editor_menu
from .item_codes import get_item_code

__version__: str
__version_info__: tuple[int, ...]
__all__: tuple[str, ...] = (
    "get_item_code",
    "mod",
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

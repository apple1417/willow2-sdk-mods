from collections.abc import Callable
from pathlib import Path
from typing import Any

from legacy_compat import legacy_compat
from mods_base import hook, register_mod
from unrealsdk.hooks import Block
from unrealsdk.unreal import BoundFunction, UFunction, UObject, WrappedStruct

from .anti_circular_import import all_text_mods
from .loader import load_mod_info
from .settings import get_cached_mod_info, update_cached_mod_info
from .text_mod import TextMod as NewTextMod

# The old TML Python interface was a very leaky abstraction. Our internals don't really match up
# with it anymore.
# Luckily, it seems there's only actually one mod which used it, Arcania. We can just create a fake
# interface to catch it specifically.

__all__: tuple[str, ...] = (
    "TextMod",
    "add_custom_mod_path",
)


class TextMod:
    Name: str
    Author: str
    Description: str
    Version: str

    onLevelTransition: Callable[[UObject, UFunction, WrappedStruct], bool]  # noqa: N815


def add_custom_mod_path(filename: str, cls: type[TextMod] = TextMod) -> None:  # noqa: D103
    if not ((path := Path(filename)).name == "Arcania.blcm" and cls.__name__ == "Arcania"):
        raise RuntimeError(f"Text Mod Loader legacy compat not implemented for {path.name}")

    if (mod_info := get_cached_mod_info(path)) is None:
        mod_info = load_mod_info(path)

        mod_info["title"] = cls.Name
        mod_info["author"] = cls.Author
        mod_info["description"] = cls.Description
        mod_info["version"] = cls.Version

        update_cached_mod_info(path, mod_info)

    @hook("Engine.GameInfo:PostCommitMapChange")
    def on_level_transition(
        obj: UObject,
        args: WrappedStruct,
        _3: Any,
        func: BoundFunction,
    ) -> type[Block] | None:
        with legacy_compat():
            ret = cls.onLevelTransition(obj, func.func, args)
        return Block if ret else None

    mod = NewTextMod(
        name=mod_info["title"],
        author=mod_info["author"],
        version=mod_info["version"],
        file=path,
        spark_service_idx=mod_info["spark_service_idx"],
        recommended_game=mod_info["recommended_game"],
        internal_description=mod_info["description"],
        prevent_reloading=True,
        hooks=(on_level_transition,),
    )

    all_text_mods[path] = mod
    register_mod(mod)

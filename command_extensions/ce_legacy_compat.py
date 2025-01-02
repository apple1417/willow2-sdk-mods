# ruff: noqa: D103, N802
import argparse
import shlex
from collections.abc import Callable
from typing import Any

from mods_base import AbstractCommand, command

from . import autoregister
from . import ce_legacy_compat_builtins as builtins

__all__: tuple[str, ...] = (
    "RegisterConsoleCommand",
    "UnregisterConsoleCommand",
    "builtins",
    "try_handle_command",
)

legacy_cmds: dict[str, AbstractCommand] = {}


def RegisterConsoleCommand(
    name: str,
    callback: Callable[[argparse.Namespace], None],
    *,
    splitter: Callable[[str], list[str]] = shlex.split,
    **kwargs: Any,
) -> AbstractCommand:
    cmd = command(name, splitter, **kwargs)(callback)
    autoregister(cmd)
    legacy_cmds[cmd.cmd] = cmd

    cmd.enable()
    return cmd


def UnregisterConsoleCommand(name: str, *, allow_missing: bool = False) -> None:
    name = name.lower()

    if name not in legacy_cmds:
        if allow_missing:
            return
        raise KeyError(f"No command with name '{name}' has been registered.")
    legacy_cmds.pop(name).disable()


def try_handle_command(cmd: str, args: str) -> bool:
    # In old sdk, if a mod called PC.ConsoleCommand() it wouldn't trigger any hooks. This function
    # existed to let you also forward those to CE processing.
    # In new sdk, it does trigger hooks, so no need for us to do anything
    _ = args
    return cmd in legacy_cmds

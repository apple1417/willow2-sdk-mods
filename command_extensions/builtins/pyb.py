import argparse
import re
import shlex
import traceback
from contextlib import AbstractContextManager, nullcontext
from typing import Any

from mods_base import command
from unrealsdk import logging

try:
    import legacy_compat

    if not legacy_compat.ENABLED:
        legacy_compat = None
except ImportError:
    legacy_compat = None

RE_OPTIONAL_ARG = re.compile(r"^\s*--?\w+")  # type: ignore


if legacy_compat is not None:
    with legacy_compat.legacy_compat():
        import Mods as legacy_Mods  # type: ignore
        import unrealsdk as legacy_unrealsdk  # type: ignore

    legacy_py_globals: dict[str, Any] = {"unrealsdk": legacy_unrealsdk, "Mods": legacy_Mods}

legacy_cached_lines: list[str] = []
new_cached_lines: list[str] = []


def run_pyb(
    args: argparse.Namespace,
    cached_lines: list[str],
    context: AbstractContextManager[None],
    py_globals: dict[str, Any],
) -> None:
    """
    Executes a pyb-style command.

    Args:
        args: The raw command args.
        cached_lines: The list to cache lines in between commands.
        context: The context manager to acquire while executing the command.
        py_globals: The globals to use.
    """
    if args.print:
        for line in cached_lines:
            logging.info(line)
    if args.exec:
        joined = "\n".join(cached_lines)
        try:
            with context:
                exec(joined, py_globals)  # noqa: S102
        except Exception:  # noqa: BLE001
            logging.error("Error occurred during 'pyb' command:")
            logging.error(joined)
            if len(cached_lines) > 1:
                logging.error("=" * 80)

            traceback.print_exc()
    if args.discard or args.exec:
        cached_lines.clear()

    if args.exec or args.discard or args.print:
        return

    cached_lines.append(args.args[0])


def pyb_splitter(args: str) -> list[str]:
    """
    Custom splitter for pyb commands, to handle our optional arg logic.

    Args:
        args: The arg line to parse
    Returns:
        The split args.
    """
    if RE_OPTIONAL_ARG.match(args):
        return shlex.split(args)
    return [args[1:]]


DESCRIPTION = (
    "Runs a block of python statements, which may span multiple lines. Only one space after the"
    " command is consumed for arg parsing - `{cmd}[3*space]abc` extracts the line `[2*space]abc`."
)
EPILOG = (
    "If an optional arg is specified, python code is ignored. Optional args must be at the"
    " start of the command to be recognised."
)


@command(
    cmd="pyb",
    splitter=pyb_splitter,
    description=(
        "DEPRECATED. This command executes all Python under legacy mod compatibility. It will"
        " automatically be disabled when legacy mod compatibility is.\n\n"
        + DESCRIPTION.format(cmd="pyb")
    ),
    epilog=EPILOG,
)
def legacy_pyb(args: argparse.Namespace) -> None:  # noqa: D103
    if legacy_compat is None:
        logging.error(
            "The 'pyb' command has been disabled due to legacy mod compatibility being disabled.",
        )
        return

    run_pyb(args, legacy_cached_lines, legacy_compat.legacy_compat(), legacy_py_globals)


@command(
    cmd="py|",
    splitter=pyb_splitter,
    description=DESCRIPTION.format(cmd="py|"),
    epilog=EPILOG,
)
def new_pyb(args: argparse.Namespace) -> None:  # noqa: D103
    run_pyb(args, new_cached_lines, nullcontext(), {})


for cmd in (legacy_pyb, new_pyb):
    cmd.add_argument("args", help="Python code. Whitespace is preserved.", nargs=argparse.REMAINDER)
    cmd.add_argument(
        "-x",
        "--exec",
        action="store_true",
        help="Executes stored lines.",
    )
    cmd.add_argument(
        "-d",
        "--discard",
        action="store_true",
        help="Discards stored lines.",
    )
    cmd.add_argument(
        "-p",
        "--print",
        action="store_true",
        help="Prints stored lines.",
    )

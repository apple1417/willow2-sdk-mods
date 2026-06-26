from typing import TYPE_CHECKING

from mods_base import command

from . import obj_name_splitter, parse_object

if TYPE_CHECKING:
    import argparse


@command(
    splitter=obj_name_splitter,
    description=(
        "Prevents an object from being garbaged collected, it will always be loaded until you"
        " restart the game."
    ),
)
def keep_alive(args: argparse.Namespace) -> None:  # noqa: D103
    obj = parse_object(args.object)
    if obj is None:
        return

    if args.undo:
        obj.ObjectFlags &= ~0x4000
    else:
        obj.ObjectFlags |= 0x4000


keep_alive.add_argument("object", help="The object to keep alive.")
keep_alive.add_argument(
    "-u",
    "--undo",
    action="store_true",
    help="Undo a previous keep alive call.",
)

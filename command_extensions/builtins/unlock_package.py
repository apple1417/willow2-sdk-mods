from typing import TYPE_CHECKING

from mods_base import command

from . import obj_name_splitter, parse_object

if TYPE_CHECKING:
    import argparse


@command(
    splitter=obj_name_splitter,
    description="Unlocks an object allowing it to be referenced cross-package.",
)
def unlock_package(args: argparse.Namespace) -> None:  # noqa: D103
    obj = parse_object(args.object)
    if obj is None:
        return

    if args.undo:
        obj.ObjectFlags &= ~4
    else:
        obj.ObjectFlags |= 4


unlock_package.add_argument("object", help="The object to unlock.")
unlock_package.add_argument(
    "-u",
    "--undo",
    action="store_true",
    help="Undo a previous unlock package call.",
)

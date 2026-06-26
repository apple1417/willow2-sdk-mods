import fnmatch
import itertools
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import unrealsdk
from mods_base import command
from unrealsdk import logging

if TYPE_CHECKING:
    import argparse

game_dir = Path(sys.executable).parent.parent.parent
all_upks = sorted(
    upk.stem
    for upk in itertools.chain(
        (game_dir / "WillowGame" / "CookedPCConsole").glob("*.upk"),
        ((game_dir / "DLC").glob("*/*/Content/*.upk")),
    )
)


@command(
    description=(
        "Loads a package and all objects contained within it. This freezes the game as it loads; it"
        " should be used sparingly. Supports using glob-style wildcards to load up to 10 packages"
        " at once, though being explicit should still be preferred."
    ),
)
def load_package(args: argparse.Namespace) -> None:  # noqa: D103
    upks = fnmatch.filter(all_upks, args.package)

    if args.list:
        if upks == all_upks:
            logging.info("All known packages:")
        else:
            logging.info(f"Packages matching '{args.package}':")
        logging.info("=" * 80)
        for package in upks:
            logging.info(package)
        return

    if len(upks) <= 0:
        logging.info(f"Could not find package '{args.package}'!")
    elif len(upks) > 10:  # noqa: PLR2004
        logging.info(f"'{args.package}' matches more than 10 packages!")
    else:
        for package in upks:
            unrealsdk.load_package(package)


load_package.add_argument(
    "package",
    help=(
        "The package(s) to load. This uses the full upk names; not the shortened version hotfixes"
        " use."
    ),
    nargs="?",
    default="*",
)
load_package.add_argument(
    "--list",
    action="store_true",
    help="List all packages matching the given pattern, instead of trying to load any.",
)

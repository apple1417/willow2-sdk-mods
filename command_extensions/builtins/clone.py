import argparse
from contextlib import suppress

import unrealsdk
from mods_base import command
from unrealsdk import logging
from unrealsdk.unreal import UObject

from . import RE_OBJ_NAME, obj_name_splitter, parse_object

suppress_exists_warning: bool = False


def clone_object(src: UObject, outer: UObject | None, name: str) -> UObject | None:
    """
    Clones an object and sets it up for proper use while modding.

    Args:
        src: The object to use as the template.
        outer: The outer object the clone should be created under.
        name: The name of the cloned object.
    Returns:
        The cloned object, or None if it failed to clone.
    """
    try:
        cloned = unrealsdk.construct_object(src.Class, outer, name, 0x400004000, src)
    except Exception:  # noqa: BLE001
        return None

    cloned.ObjectArchetype = src.ObjectArchetype
    return cloned


def parse_clone_target(name: str, src_class: str) -> tuple[UObject | None, str] | tuple[None, None]:
    """
    Parses a full object name intended to be a clone target into it's outer object and name.

    If it's unable to parse or find the object, logs an error to console and returns None.

    Args:
        name: The full object name to parse.
        src_class: The class of the source object. The target must use this class (or object).
    Returns:
        A tuple of the target's outer object and it's name, or a tuple of two `None`s on error.
    """
    dst_match = RE_OBJ_NAME.match(name)
    if dst_match is None:
        logging.error(f"Unable to parse object name {name}")
        return None, None

    dst_class = dst_match.group("class") or "Object"
    if dst_class not in ("Object", src_class):
        logging.error(f"Cannot clone object of class {src_class} as class {dst_class}")
        return None, None

    with suppress(ValueError):
        dst_obj = unrealsdk.find_object(dst_class, dst_match.group("fullname"))
        if not suppress_exists_warning:
            logging.error(f"Object '{dst_obj.PathName(dst_obj)}' already exists")
        return None, None

    dst_outer = dst_match.group("outer")
    dst_outer_object = None
    if dst_outer:
        try:
            dst_outer_object = unrealsdk.find_object("Object", dst_outer)
        except ValueError:
            logging.error(f"Unable to find outer object {dst_outer}")
            return None, None

    return dst_outer_object, dst_match.group("name")


@command(splitter=obj_name_splitter, description="Creates a clone of an existing object.")
def clone(args: argparse.Namespace) -> None:  # noqa: D103
    src = parse_object(args.base)
    if src is None:
        return
    outer, name = parse_clone_target(args.clone, src.Class.Name)
    if name is None:
        return

    clone_object(src, outer, name)


clone.add_argument("base", help="The object to create a copy of.")
clone.add_argument("clone", help="The name of the clone to create.")
clone.add_argument(
    "-x",
    "--suppress-exists",
    action="store_true",
    help="Deprecated, does nothing. See 'clone_dbg_suppress_exists' instead.",
)


@command(
    description=(
        "Suppresses the 'object already exists' errors which may occur while cloning. Only intended"
        " for debug usage."
    ),
)
def clone_dbg_suppress_exists(args: argparse.Namespace) -> None:  # noqa: D103
    global suppress_exists_warning
    if args.value == "Enable":
        suppress_exists_warning = True
        logging.info("clone 'object already exists' warnings suppressed")
    elif args.value == "Disable":
        suppress_exists_warning = False
        logging.info("clone 'object already exists' warnings re-enabled")
    else:
        logging.error(f"unrecognised value '{args.value}'")


clone_dbg_suppress_exists.add_argument("value", choices=("Enable", "Disable"))

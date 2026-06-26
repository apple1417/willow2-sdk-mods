import re
import shlex
from typing import TYPE_CHECKING

import unrealsdk
from unrealsdk import logging

if TYPE_CHECKING:
    from unrealsdk.unreal import UObject

__all__: tuple[str, ...] = (
    "RE_OBJ_NAME",
    "obj_name_splitter",
    "parse_object",
)

"""
Regex matching an object name.

Group Name | Contents
:----------|:---------
`class`    | The object's class name, if specified.
`fullname` | The object's full path.
`outer`    | The full path to the outer object, if there is one.
`name`     | The object's name.
"""
RE_OBJ_NAME = re.compile(
    r"^((?P<class>[\w?+!,'\"\\\-]+?)')?(?P<fullname>((?P<outer>[\w.:?+!,'\"\\\-]+)[.:])?(?P<name>[\w?+!,'\"\\\-]+))(?(class)'|)$",
    flags=re.I,
)


def obj_name_splitter(args: str) -> list[str]:
    """
    Custom argument splitter that returns object names as single tokens.

    Note that this makes the splitting less versatile - quoting is completely gone for example.

    Args:
        args: A string of arguments
    Returns:
        A list of individual arguments split out from the input string.
    """
    lex = shlex.shlex(args)
    lex.wordchars += ".:?+!,'\"\\-"
    lex.quotes = ""
    lex.whitespace_split = True
    return list(lex)


def parse_object(name: str) -> UObject | None:
    """
    Given an object name, returns the object.

    If it's unable to parse or find the object, logs an error to console and returns None.

    Args:
        name: The object name to look for
    Returns:
        The parsed object, or None on error.
    """
    match = RE_OBJ_NAME.match(name)
    if match is None:
        logging.error(f"Unable to parse object name {name}")
        return None

    class_ = match.group("class") or "Object"
    fullname = match.group("fullname")
    try:
        return unrealsdk.find_object(class_, fullname)
    except ValueError:
        logging.error(f"Unable to find object {name}")
        return None

import fnmatch
from typing import TYPE_CHECKING, Any

from mods_base import command, hook
from unrealsdk.hooks import Block

if TYPE_CHECKING:
    import argparse

    from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

suppressed_patterns: dict[str, int] = {}
suppress_global_count: int = 0


@command(
    description=(
        "Prevents the next chat message that matches a given glob pattern from being printed."
        " Multiple calls to this stack, and suppress multiple messages.\n"
        "\n"
        "This is intended to be used to suppress an error message, so that it only gets printed"
        " when someone tries to exec your file without running Command Extensions."
    ),
)
def suppress_next_chat(args: argparse.Namespace) -> None:  # noqa: D103
    global suppress_global_count
    if args.pattern == "*":
        suppress_global_count += 1
        return

    if args.pattern not in suppressed_patterns:
        suppressed_patterns[args.pattern] = 0
    suppressed_patterns[args.pattern] += 1


suppress_next_chat.add_argument(
    "pattern",
    nargs="?",
    default="*",
    help="The glob pattern matching the message to suppress.",
)


@hook("Engine.PlayerController:ServerSay")
def server_say_hook(  # noqa: D103
    _1: UObject,
    args: WrappedStruct,
    _3: Any,
    _4: BoundFunction,
) -> type[Block] | None:
    global suppress_global_count

    for pattern, count in suppressed_patterns.items():
        if fnmatch.fnmatch(args.msg, pattern):
            if count == 1:
                del suppressed_patterns[pattern]
            else:
                suppressed_patterns[pattern] -= 1
            return Block

    if suppress_global_count > 0:
        suppress_global_count -= 1
        return Block

    return None

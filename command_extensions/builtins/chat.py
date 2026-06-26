from typing import TYPE_CHECKING

import unrealsdk
from mods_base import command, get_pc

if TYPE_CHECKING:
    import argparse


@command(
    description=(
        "Similarly to the `say` command, writes a message in chat, but lets you customize the"
        " message source. Note this does not use the same parsing as the `say` command, make sure"
        " you quote your message if it includes spaces."
    ),
)
def chat(args: argparse.Namespace) -> None:  # noqa: D103
    source = args.source

    chat_movie = (pc := get_pc()).GetTextChatMovie()
    if source is None:
        timestamp = chat_movie.GetTimestampString(
            unrealsdk.find_class("WillowSaveGameManager").ClassDefaultObject.TimeFormat,
        )
        player = pc.PlayerReplicationInfo.PlayerName
        source = player + " " + timestamp

    chat_movie.AddChatMessageInternal(source, args.msg)


chat.add_argument(
    "source",
    help=(
        "What the message source should be. Defaults to the same as a normal chat message,"
        " username/timestamp."
    ),
    nargs="?",
)
chat.add_argument("msg", help="The message to write.")

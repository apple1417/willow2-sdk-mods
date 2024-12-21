import string
import sys
import traceback
from collections.abc import Iterable, Sequence
from pathlib import Path

from mods_base import Game, deregister_mod, register_mod
from unrealsdk import logging

from . import file_parser
from .anti_circular_import import TextModState, all_text_mods
from .settings import ModInfo, get_cached_mod_info, update_cached_mod_info
from .text_mod import TextMod

BINARIES_DIR = Path(sys.executable).parent.parent


def join_lines_markdown_like(lines: Iterable[str]) -> str:
    """
    Joins a list of lines similarly to how markdown does it.

    Adjacent lines get space seperated, you need an entirely empty line to add a newline.

    Args:
        lines: The lines to join.
    Returns:
        The lines joined into a single string.
    """

    def _markdown_iterator() -> Iterable[str]:
        no_space = True
        for line in lines:
            stripped = line.strip()
            if stripped:
                if not no_space:
                    yield " "
                yield stripped
                no_space = False
            else:
                if not no_space:
                    yield "\n"
                no_space = True

    return "".join(_markdown_iterator())


def join_sentence(entries: Sequence[str], final_connector: str = "and") -> str:
    """
    Joins a list of strings as in a sentence listing them.

    e.g. ["Alice", "Bob", "Carl"] -> "Alice, Bob, and Carl"

    Args:
        entries: The list to join.
        final_connector: The word to use to connect the final two entries.
    Returns:
        The list joined into a single string.
    """

    def _sentence_iterator() -> Iterable[str]:
        for entry in entries[:-1]:
            yield entry
            yield ", "
        if len(entries) > 2:  # noqa: PLR2004
            yield final_connector
            yield " "
        yield entries[-1]

    return "".join(_sentence_iterator())


def find_edge_characters(lines: Sequence[str]) -> str:
    """
    Given a list of strings, try detect characters used to create ASCII art edges around them.

    Will always return whitespace, so that you can pass the return value directly to `str.strip()`.

    Args:
        lines: The list of lines to search though.
    Returns:
        A string containing all detected characters.
    """
    strip_chars = string.whitespace

    # Do one quick pass removing existing whitespace
    stripped_lines = list(filter(None, (line.strip() for line in lines)))
    if not stripped_lines:
        return strip_chars

    edges = (
        stripped_lines[0],
        stripped_lines[-1],
        "".join(line[0] for line in stripped_lines),
        "".join(line[-1] for line in stripped_lines),
    )

    for edge in edges:
        threshold = 0.8 * len(edge)
        symbols = list(filter(lambda c: not c.isalnum(), edge))
        if len(symbols) > threshold:
            strip_chars += "".join(set(symbols))

    return strip_chars


def load_mod_info(path: Path) -> ModInfo:
    """
    Loads metadata for a specific mod.

    Args:
        path: The path to load from.
    Returns:
        The loaded mod info.
    """
    try:
        parse_result = file_parser.parse(path)
    except Exception:  # noqa: BLE001
        logging.warning(f"[TML]: Failed to extract mod metadata for file '{path.name}'")
        logging.dev_warning(traceback.format_exc())
        # Just return a sane default
        return {
            "modify_time": path.stat().st_mtime,
            "ignore_me": False,
            "spark_service_idx": None,
            "recommended_game": None,
            "title": path.name,
            "author": "Text Mod Loader",
            "version": "",
            "description": "",
        }

    blimp_authors: list[str] = []
    if (main_author := parse_result.blimp_tags.get("@main-author")) is not None:
        blimp_authors.append(main_author[0])
    if (author_list := parse_result.blimp_tags.get("@author")) is not None:
        blimp_authors.extend(x.strip() for x in author_list)

    description: str
    if (description_list := parse_result.blimp_tags.get("@description")) is not None:
        description = join_lines_markdown_like(description_list)
    else:
        # If there's no explict description tags, extract it from the untagged lines instead
        strip_chars = find_edge_characters(parse_result.untagged_lines)
        description = join_lines_markdown_like(
            line.strip(strip_chars) for line in parse_result.untagged_lines
        )

    return {
        "modify_time": path.stat().st_mtime,
        "ignore_me": "@tml-ignore-me" in parse_result.blimp_tags,
        "spark_service_idx": parse_result.spark_service_idx,
        "recommended_game": (
            None if parse_result.game is None else Game.__members__.get(parse_result.game)
        ),
        "title": parse_result.blimp_tags.get("@title", (path.name,))[0],
        "author": join_sentence(blimp_authors) if blimp_authors else "Text Mod Loader",
        "version": parse_result.blimp_tags.get("@version", ("",))[0],
        "description": description,
    }


def load_all_text_mods() -> None:
    """(Re-)Loads all text mods from binaries."""
    # Iterate through a copy so we can delete while iterating
    for mod in list(all_text_mods.values()):
        mod.check_deleted()

        match mod.state:
            # Delete what mods we can
            case (
                TextModState.Disabled
                | TextModState.LockedHotfixes
                | TextModState.LockedBadService
                | TextModState.DeletedInactive
            ):
                all_text_mods.pop(mod.file)
                deregister_mod(mod)

            # Need to keep any active mods around in the list
            case TextModState.Enabled | TextModState.DisableOnRestart | TextModState.DeletedActive:
                pass

    for entry in BINARIES_DIR.iterdir():
        if not entry.is_file():
            continue

        # Don't reload active mods
        if entry in all_text_mods:
            continue

        if (mod_info := get_cached_mod_info(entry)) is None:
            mod_info = load_mod_info(entry)
            update_cached_mod_info(entry, mod_info)

        if mod_info["ignore_me"]:
            continue

        mod = TextMod(
            name=mod_info["title"],
            author=mod_info["author"],
            version=mod_info["version"],
            file=entry,
            spark_service_idx=mod_info["spark_service_idx"],
            recommended_game=mod_info["recommended_game"],
            internal_description=mod_info["description"],
        )

        all_text_mods[entry] = mod
        register_mod(mod)

from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from .text_mod import TextMod

# Circular imports are annoying

# This would be more suitable in `loader.py`
all_text_mods: dict[Path, TextMod] = {}


# This would be more suitable in `text_mod.py`
class TextModState(Enum):
    """
    Represent the various states a text mod can be in.

    Transitions
    ===========
    DisableOnRestart--------+
      ^ | [Toggle Enabled]  | [Mod file deleted]
      | v                   |
    Enabled-----------------+---> DeletedActive
       ^ [Mod Enabled]
       |
    Disabled-----------------------------+
    |  |                                 | [Mod file deleted]
    |  | [Init, if wrong spark service]  |
    |  +->LockedBadService---------------+---> DeletedInactive
    |                                    |
    | [Other mod with hotfixes enabled]  |
    +->LockedHotfixes--------------------+
    """

    Disabled = auto()
    DisableOnRestart = auto()
    Enabled = auto()
    LockedHotfixes = auto()
    LockedBadService = auto()
    DeletedActive = auto()
    DeletedInactive = auto()

from __future__ import annotations

import os
import sys
from dataclasses import KW_ONLY, dataclass
from pathlib import Path
from typing import Literal

from mods_base import Game, Mod, get_pc
from ui_utils import TrainingBox

from .anti_circular_import import TextModState
from .hotfixes import any_hotfix_used, is_hotfix_service
from .settings import change_mod_auto_enable

BINARIES_DIR = Path(sys.executable).parent.parent


@dataclass
class TextMod(Mod):
    auto_enable: Literal[False] = False  # pyright: ignore[reportIncompatibleVariableOverride]

    _: KW_ONLY

    file: Path
    state: TextModState = TextModState.Disabled
    prevent_reloading: bool = False

    spark_service_idx: int | None
    recommended_game: Game | None
    # The raw description as extracted from the mod file - since we add extra things to the real one
    internal_description: str | None

    @property
    def description(self) -> str:  # noqa: D102
        description_parts: list[str] = []
        if (
            self.recommended_game is not None
            and (current_game := Game.get_current()) != self.recommended_game
        ):
            description_parts.append(
                f'<font color="#FFFF00">Warning:</font> This mod is intended for'
                f" {self.recommended_game.name}, and may not function as expected in"
                f" {current_game.name}.",
            )

        if self.state in {TextModState.DeletedActive, TextModState.DeletedInactive}:
            description_parts.append(
                '<font color="#FFFF00">Warning:</font> This mod no longer exists on disk.',
            )

        match self.state:
            case TextModState.DisableOnRestart | TextModState.DeletedActive:
                description_parts.append(
                    "This mod was previously enabled, but will not be re-enabled. Restart the game"
                    " to remove it fully.",
                )
            case TextModState.LockedHotfixes:
                description_parts.append(
                    'This mod is <font color="#FFFF00">Locked</font> because you\'ve already run'
                    " another mod which uses hotfixes.",
                )
            case TextModState.LockedBadService:
                description_parts.append(
                    'This mod is <font color="#FFFF00">Locked</font> because it uses a non-existent'
                    " hotfix service - try open and re-save it using OpenBLCMM.",
                )

            case TextModState.Disabled | TextModState.Enabled | TextModState.DeletedInactive:
                pass

        if self.internal_description:
            description_parts.append("\n" + self.internal_description)

        return "\n".join(description_parts)

    @description.setter
    def description(self, _: str) -> None:  # pyright: ignore[reportIncompatibleVariableOverride]
        pass

    @property
    def enabling_locked(self) -> bool:  # noqa: D102
        match self.state:
            case TextModState.Disabled | TextModState.DisableOnRestart | TextModState.Enabled:
                return False
            case (
                TextModState.LockedHotfixes
                | TextModState.LockedBadService
                | TextModState.DeletedActive
                | TextModState.DeletedInactive
            ):
                return True

    @enabling_locked.setter
    def enabling_locked(self, _: bool) -> None:  # pyright: ignore[reportIncompatibleVariableOverride]
        pass

    def __post_init__(self) -> None:
        super().__post_init__()

        if self.spark_service_idx is not None:
            if any_hotfix_used:
                self.state = TextModState.LockedHotfixes
            elif not is_hotfix_service(self.spark_service_idx):
                self.state = TextModState.LockedBadService

    def enable(self) -> None:  # noqa: D102
        super().enable()

        self.check_deleted()

        match self.state:
            case TextModState.Enabled:
                return
            case TextModState.LockedHotfixes | TextModState.LockedBadService:
                TrainingBox(
                    title=f"Unable to execute '{self.name}'",
                    message="The mod was supposed to be locked, how did you manage this?",
                ).show()
                self.disable()
                return
            case TextModState.DeletedActive | TextModState.DeletedInactive:
                TrainingBox(
                    title=f"Unable to execute '{self.name}'",
                    message=f"The associated mod file has been deleted:\n{self.file}",
                ).show()
                self.disable()
                return

            case TextModState.Disabled:
                # Path.relative_to requires one path be a subpath of the other, it won't prefix
                # `../`s if we're executing something in a parent dir of binaries
                get_pc().ConsoleCommand(f'exec "{os.path.relpath(self.file, BINARIES_DIR)}"')

                self.state = TextModState.Enabled
                change_mod_auto_enable(self, True)
            case TextModState.DisableOnRestart:
                self.state = TextModState.Enabled
                change_mod_auto_enable(self, True)

    def disable(self, dont_update_setting: bool = False) -> None:  # noqa: D102
        super().disable(dont_update_setting)

        self.check_deleted()

        match self.state:
            case (
                TextModState.Disabled
                | TextModState.DisableOnRestart
                | TextModState.LockedHotfixes
                | TextModState.LockedBadService
                | TextModState.DeletedActive
                | TextModState.DeletedInactive
            ):
                return

            case TextModState.Enabled:
                self.state = TextModState.DisableOnRestart
                change_mod_auto_enable(self, False)

    def get_status(self) -> str:  # noqa: D102
        if Game.get_current() not in self.supported_games:
            return "<font color='#ffff00'>Incompatible</font>"

        match self.state:
            case TextModState.Disabled:
                return "<font color='#ff0000'>Disabled</font>"
            case TextModState.DisableOnRestart:
                return "<font color='#ff6060'>Disabling on Restart</font>"
            case TextModState.Enabled:
                return "<font color='#00ff00'>Enabled</font>"
            case TextModState.LockedHotfixes | TextModState.LockedBadService:
                return "<font color='#ffff00'>Locked</font>"
            case TextModState.DeletedActive | TextModState.DeletedInactive:
                return "<font color='#ffff00'>Deleted</font>"

    def check_deleted(self) -> None:
        """Checks if this mod file has been deleted, and if so changes state as required."""
        if self.file.exists():
            return

        match self.state:
            case (
                TextModState.Disabled
                | TextModState.LockedHotfixes
                | TextModState.LockedBadService
            ):
                self.state = TextModState.DeletedInactive
            case TextModState.DisableOnRestart | TextModState.Enabled:
                self.state = TextModState.DeletedActive
            case TextModState.DeletedActive | TextModState.DeletedInactive:
                pass

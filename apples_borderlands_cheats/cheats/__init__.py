from dataclasses import KW_ONLY, dataclass, field
from enum import StrEnum

from mods_base import KeybindType, SpinnerOption, keybind
from ui_utils import show_hud_message


class OnOff(StrEnum):
    OFF = "Off"
    On = "On"


@dataclass
class CyclableOption(SpinnerOption):
    _: KW_ONLY
    keybind: KeybindType = field(init=False)

    def __post_init__(self) -> None:
        super().__post_init__()

        cycle_prefix = "Cycle " if len(self.choices) > 2 else "Toggle "  # noqa: PLR2004

        @keybind(
            cycle_prefix + self.identifier,
            display_name=cycle_prefix + self.display_name,
            description=self.description,
            description_title=cycle_prefix + self.description_title,
            is_hidden=self.is_hidden,
        )
        def on_cycle() -> None:
            idx = self.choices.index(self.value)
            idx = (idx + 1) % len(self.choices)
            new_value = self.choices[idx]

            # Show a message before updating the value, just in case of exceptions
            show_hud_message(self.display_name, f"{self.display_name}: {new_value}")

            self.value = new_value

            if self.mod:
                self.mod.save_settings()

        self.keybind = on_cycle

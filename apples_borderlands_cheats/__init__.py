from dataclasses import dataclass, field

from mods_base import KeybindType, Mod, build_mod, keybind
from ui_utils import OptionBox, OptionBoxButton

from .cheats import CyclableOption
from .cheats.add_op_level import add_op_level
from .cheats.free_shops import free_shops, free_shops_on_disable
from .cheats.ghost import ghost, ghost_speed_down, ghost_speed_up
from .cheats.god import god_mode, god_on_disable
from .cheats.infinite_ammo import infinite_ammo, infinite_ammo_on_disable
from .cheats.instant_cooldown import instant_cooldown, instant_cooldown_on_disable
from .cheats.kill_all import kill_all
from .cheats.level_up import level_up
from .cheats.one_shot import one_shot, one_shot_on_disable
from .cheats.passive_mode import passive_enemies, passive_enemies_on_disable
from .cheats.reset_shops import reset_shops
from .cheats.revive import revive_self
from .cheats.suicide import suicide
from .cheats.tp_travels import tp_fast_travel, tp_level_transition

mod: Mod | None = None


@dataclass
class _CycleableButton(OptionBoxButton):
    option: CyclableOption = field(kw_only=True, repr=False)

    @property
    def tip(self) -> str:  # pyright: ignore[reportIncompatibleVariableOverride]
        return f"Currently: {self.option.value}"

    @tip.setter
    def tip(self, val: str) -> None:  # pyright: ignore[reportIncompatibleVariableOverride]
        pass

    def trigger(self) -> None:
        self.option.keybind.callback()  # type: ignore


@dataclass
class _KeybindButton(OptionBoxButton):
    keybind: KeybindType = field(kw_only=True, repr=False)

    def trigger(self) -> None:
        self.keybind.callback()  # type: ignore


last_button: OptionBoxButton | None = None
buttons: list[OptionBoxButton] = []


def _on_cheats_menu_select(_: OptionBox, button: OptionBoxButton) -> None:
    global last_button
    last_button = button

    assert isinstance(button, _CycleableButton | _KeybindButton)
    button.trigger()


@keybind("Cheats Menu")
def cheats_menu() -> None:  # noqa: D103
    assert mod is not None

    if not buttons:
        # Keybinds aren't hashable, need a list :/
        seen_binds: list[KeybindType] = [cheats_menu]

        for opt in mod.options:
            if not isinstance(opt, CyclableOption):
                continue
            buttons.append(_CycleableButton(opt.keybind.display_name, option=opt))
            seen_binds.append(opt.keybind)

        for bind in mod.keybinds:
            if bind in seen_binds:
                continue
            buttons.append(_KeybindButton(bind.display_name, keybind=bind))

    OptionBox(
        title=mod.name,
        message="Select a cheat to activate.",
        buttons=buttons,
        on_select=_on_cheats_menu_select,
    ).show(last_button)


def on_enable() -> None:  # noqa: D103
    # Re-assign all cycleable options to re-enable their hooks if required
    if mod:
        for opt in mod.options:
            if isinstance(opt, CyclableOption):
                opt.value = opt.value


def on_disable() -> None:  # noqa: D103
    free_shops_on_disable()
    god_on_disable()
    infinite_ammo_on_disable()
    instant_cooldown_on_disable()
    one_shot_on_disable()
    passive_enemies_on_disable()


mod = build_mod(
    options=[
        free_shops,
        god_mode,
        infinite_ammo,
        instant_cooldown,
        one_shot,
        passive_enemies,
    ],
    keybinds=[
        cheats_menu,
        # ==========================
        free_shops.keybind,
        god_mode.keybind,
        infinite_ammo.keybind,
        instant_cooldown.keybind,
        one_shot.keybind,
        # ==========================
        add_op_level,
        ghost,
        ghost_speed_up,
        ghost_speed_down,
        kill_all,
        level_up,
        reset_shops,
        revive_self,
        suicide,
        tp_fast_travel.keybind,
        tp_level_transition.keybind,
    ],
)
on_enable()

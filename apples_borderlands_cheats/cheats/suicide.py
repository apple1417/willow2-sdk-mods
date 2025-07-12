from mods_base import get_pc, keybind


@keybind("Suicide")
def suicide() -> None:  # noqa: D103
    get_pc().CausePlayerDeath(True)

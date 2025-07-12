from mods_base import get_pc, keybind


@keybind("Revive Self")
def revive_self() -> None:  # noqa: D103
    pawn = get_pc().Pawn

    # Only activate if in FFYL
    if pawn.bIsInjured and not pawn.bIsDead:
        pawn.GoFromInjuredToHealthy()
        pawn.ClientOnRevived()

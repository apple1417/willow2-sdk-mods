import unrealsdk
from mods_base import ENGINE, get_pc, keybind


@keybind("Kill All")
def kill_all() -> None:  # noqa: D103
    player_pawn = get_pc().Pawn
    is_friendly_fire = ENGINE.GetCurrentWorldInfo().Game.IsFriendlyFire

    player_pools = [
        pool
        for pawn in unrealsdk.find_all("WillowPlayerPawn")
        if (pool := pawn.HealthPool.Data) is not None
    ]

    for pool in unrealsdk.find_all("HealthResourcePool"):
        if pool in player_pools:
            continue
        if (provider := pool.AssociatedProvider) is None or (pawn := provider.Pawn) is None:
            continue
        if is_friendly_fire(pawn, player_pawn):
            continue
        pool.CurrentValue = 0

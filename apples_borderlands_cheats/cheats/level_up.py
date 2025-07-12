from mods_base import get_pc, keybind


@keybind("Level Up")
def level_up() -> None:  # noqa: D103
    pc = get_pc()

    if pc.IsResourcePoolValid(exp_pool := pc.ExpPool):
        exp_pool.Data.SetCurrentValue(0)

    pc.OnExpLevelChange(True, False)
    pc.ExpEarn(pc.GetExpPointsRequiredForLevel(pc.PlayerReplicationInfo.ExpLevel + 1), 0)
    exp_pool.Data.ApplyExpPointsToExpLevel(True)

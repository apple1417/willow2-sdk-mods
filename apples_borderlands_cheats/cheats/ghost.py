from mods_base import get_pc, keybind
from unrealsdk.unreal import WeakPointer

MIN_SPEED: int = 100
DEFAULT_SPEED: int = 2500
MAX_SPEED: int = 100000

SPEED_INCREMENT: float = 1.2

original_pawn = WeakPointer()


@keybind("Toggle Ghost Mode")
def ghost() -> None:  # noqa: D103
    pc = get_pc()

    pawn = original_pawn()
    if pawn is None:
        original_pawn.replace(pc.Pawn)

        pc.ServerSpectate()
        pc.bCollideWorld = False
        pc.SpectatorCameraSpeed = DEFAULT_SPEED
    else:
        pawn.Location = pc.Location
        pc.Possess(pawn, True)

        original_pawn.replace(None)


@keybind("Ghost Speed Up", "MouseScrollUp")
def ghost_speed_up() -> None:  # noqa: D103
    if original_pawn() is None:
        return
    speed = (pc := get_pc()).SpectatorCameraSpeed
    pc.SpectatorCameraSpeed = min(speed * SPEED_INCREMENT, MAX_SPEED)


@keybind("Ghost Speed Down", "MouseScrollDown")
def ghost_speed_down() -> None:  # noqa: D103
    if original_pawn() is None:
        return
    speed = (pc := get_pc()).SpectatorCameraSpeed
    pc.SpectatorCameraSpeed = max(speed / SPEED_INCREMENT, MIN_SPEED)

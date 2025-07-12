from enum import StrEnum
from typing import TYPE_CHECKING

import unrealsdk

from . import CyclableOption

if TYPE_CHECKING:
    from enum import auto

    from unrealsdk.unreal._uenum import UnrealEnum  # pyright: ignore[reportMissingModuleSource]

    class EOpinion(UnrealEnum):
        OPINION_Enemy = auto()
        OPINION_Neutral = auto()
        OPINION_Friendly = auto()

else:
    EOpinion = unrealsdk.find_enum("EOpinion")


class PassiveMode(StrEnum):
    OFF = "Off"
    NEUTRAL = "Neutral"
    FRIENDLY = "Friendly"


@CyclableOption("Passive Enemies", PassiveMode.OFF, list(PassiveMode))
def passive_enemies(_: CyclableOption, new_value: str) -> None:  # noqa: D103
    if not passive_enemies.mod or not passive_enemies.mod.is_enabled:
        return

    match new_value:
        case PassiveMode.OFF:
            change_allegiance(EOpinion.OPINION_Enemy)
        case PassiveMode.NEUTRAL:
            change_allegiance(EOpinion.OPINION_Neutral)
        case PassiveMode.FRIENDLY:
            change_allegiance(EOpinion.OPINION_Friendly)
        case _:
            pass


def passive_enemies_on_disable() -> None:  # noqa: D103
    change_allegiance(EOpinion.OPINION_Enemy)


def change_allegiance(opinion: EOpinion) -> None:  # noqa: D103
    for obj_name in (
        "GD_AI_Allegiance.Allegiance_Player",
        "GD_AI_Allegiance.Allegiance_Player_NoLevel",
    ):
        obj = unrealsdk.find_object("PawnAllegiance", obj_name)
        obj.bForceAllOtherOpinions = opinion != EOpinion.OPINION_Enemy
        obj.ForcedOtherOpinion = opinion

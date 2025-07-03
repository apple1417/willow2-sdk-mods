from dataclasses import KW_ONLY, dataclass
from typing import TYPE_CHECKING

import unrealsdk
from mods_base import BoolOption, Game
from unrealsdk.unreal import WeakPointer

if TYPE_CHECKING:
    from enum import auto

    from unrealsdk.unreal._uenum import UnrealEnum  # pyright: ignore[reportMissingModuleSource]

    class EItemRarity(UnrealEnum):
        RARITY_Unknown = auto()
        RARITY_Common = auto()
        RARITY_Uncommon = auto()
        RARITY_Rare = auto()
        RARITY_VeryRare = auto()
        RARITY_Legendary = auto()
        RARITY_Seraph = auto()
        RARITY_Rainbow = auto()

else:
    EItemRarity = unrealsdk.find_enum("EItemRarity")

from . import Inventory, Restriction


@dataclass
class RarityOption(BoolOption):
    value: bool = True
    true_text: str | None = "Allowed"
    false_text: str | None = "Not Allowed"

    _: KW_ONLY
    rarity: EItemRarity
    supported_games: Game = Game.Willow2

    def __post_init__(self) -> None:
        super().__post_init__()
        self.is_hidden = Game.get_current() not in self.supported_games
        self.description = f"Should you be able to equip {self.display_name} items."


ALL_RARITIES: tuple[RarityOption, ...] = (
    RarityOption("Common", rarity=EItemRarity.RARITY_Common),
    RarityOption("Uncommon", rarity=EItemRarity.RARITY_Uncommon),
    RarityOption("Rare", rarity=EItemRarity.RARITY_Rare),
    RarityOption("Very Rare", rarity=EItemRarity.RARITY_VeryRare),
    RarityOption("Legendary", rarity=EItemRarity.RARITY_Legendary),
    RarityOption("Seraph", rarity=EItemRarity.RARITY_Seraph, supported_games=Game.BL2 | Game.AoDK),
    RarityOption("Glitch", rarity=EItemRarity.RARITY_Seraph, supported_games=Game.TPS),
    RarityOption(
        "Rainbow",
        rarity=EItemRarity.RARITY_Rainbow,
        supported_games=Game.BL2 | Game.AoDK,
    ),
)
RARITY_LEVEL_MAP = {opt.rarity: opt for opt in ALL_RARITIES if not opt.is_hidden}

weak_globals: WeakPointer = WeakPointer()


def can_item_be_equipped(item: Inventory) -> bool:  # noqa: D103
    if (globals_obj := weak_globals()) is None:
        globals_obj = unrealsdk.find_object("GlobalsDefinition", "GD_Globals.General.Globals")
        weak_globals.replace(globals_obj)

    rarity = globals_obj.GetRarityForLevel(item.RarityLevel)
    if rarity not in RARITY_LEVEL_MAP:
        return True

    return RARITY_LEVEL_MAP[rarity].value


rarity_restriction = Restriction(
    "Rarity",
    "Lock items based on their rarity. Mods that edit rarities may be compatible if they"
    " logically categorised all their new rarities.",
    ALL_RARITIES,
    can_item_be_equipped,
)

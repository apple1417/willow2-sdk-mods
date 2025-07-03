from dataclasses import KW_ONLY, dataclass

from mods_base import BoolOption, Game
from unrealsdk.unreal import UObject

from . import Restriction

type Inventory = UObject


@dataclass
class ManufacturerOption(BoolOption):
    value: bool = True
    true_text: str | None = "Allowed"
    false_text: str | None = "Not Allowed"

    _: KW_ONLY
    flash_label: str
    artifact: str | None = None
    supported_games: Game = Game.Willow2

    def __post_init__(self) -> None:
        super().__post_init__()
        self.is_hidden = Game.get_current() not in self.supported_games
        self.description = f"Should you be able to equip {self.display_name} items."


ALL_MANUFACTURERS: tuple[ManufacturerOption, ...] = (
    ManufacturerOption(
        "Bandit",
        flash_label="s_and_s",
        artifact="Artifact_AllegianceA",
        supported_games=Game.BL2,
    ),
    ManufacturerOption("Dahl", flash_label="dahl", artifact="Artifact_AllegianceB"),
    ManufacturerOption("Hyperion", flash_label="hyperion", artifact="Artifact_AllegianceC"),
    ManufacturerOption("Jakobs", flash_label="jakobs", artifact="Artifact_AllegianceD"),
    ManufacturerOption("Maliwan", flash_label="maliwan", artifact="Artifact_AllegianceE"),
    ManufacturerOption("Scav", flash_label="s_and_s", supported_games=Game.TPS),
    ManufacturerOption("Tediore", flash_label="tediore", artifact="Artifact_AllegianceF"),
    ManufacturerOption("Torgue", flash_label="torgue", artifact="Artifact_AllegianceG"),
    ManufacturerOption("Vladof", flash_label="vladof", artifact="Artifact_AllegianceH"),
    ManufacturerOption("Anshin", flash_label="anshin"),
    ManufacturerOption("Pangolin", flash_label="pangolin"),
    ManufacturerOption("Eridan", flash_label="eridan", supported_games=Game.BL2 | Game.AoDK),
)

FLASH_LABEL_MAP = {opt.flash_label: opt for opt in ALL_MANUFACTURERS if not opt.is_hidden}
ARTIFACT_MAP = {
    opt.artifact: opt for opt in ALL_MANUFACTURERS if not opt.is_hidden and opt.artifact is not None
}

allegiance_relics = BoolOption(
    "Allegiance Relics",
    False,
    true_text="Allowed",
    false_text="Not Allowed",
    description=(
        "Should you be able to equip allegiance relics. You will only be able to equip ones that"
        " boost manufacturers you're already allowed to equip."
    ),
    is_hidden=Game.get_current() == Game.TPS,
)

usable_items = BoolOption(
    "Ignore Usable Items",
    True,
    description=(
        "Should you be able to use useable items regardless of their manufacturer. This includes"
        " things such as health vials, oxygen, SDUs, shield boosters, and more."
    ),
)

weapons_only = BoolOption(
    "Weapons Only",
    False,
    description="Only prevent equipping weapons. This overwrites the previous two options.",
)


def can_item_be_equipped(item: Inventory) -> bool:  # noqa: D103
    manu = item.GetManufacturer()
    if manu is None:
        return True

    flash = manu.FlashLabelName
    if flash not in FLASH_LABEL_MAP:
        return True

    if weapons_only.value and item.Class.Name != "WillowWeapon":
        return True

    if usable_items.value and item.Class.Name == "WillowUsableItem":
        return True

    if allegiance_relics.value and item.Class.Name == "WillowArtifact":
        item_def = item.DefinitionData.ItemDefinition
        if item_def is not None and item_def.Name in ARTIFACT_MAP:
            return ARTIFACT_MAP[item_def.Name].value

    return FLASH_LABEL_MAP[flash].value


allegiance_restriction = Restriction(
    "Allegiance",
    "Lock items based on their manufacturer.",
    (*ALL_MANUFACTURERS, allegiance_relics, usable_items, weapons_only),
    can_item_be_equipped,
)

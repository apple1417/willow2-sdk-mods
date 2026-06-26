from dataclasses import dataclass
from typing import TYPE_CHECKING

from unrealsdk.unreal import UObject

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from mods_base import BaseOption

type Inventory = UObject


@dataclass
class Restriction:
    name: str
    description: str
    options: Sequence[BaseOption]
    can_item_be_equipped: Callable[[Inventory], bool]

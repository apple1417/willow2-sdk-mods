from collections.abc import Callable, Sequence
from dataclasses import dataclass

from mods_base import BaseOption
from unrealsdk.unreal import UObject

type Inventory = UObject


@dataclass
class Restriction:
    name: str
    description: str
    options: Sequence[BaseOption]
    can_item_be_equipped: Callable[[Inventory], bool]

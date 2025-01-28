from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import unrealsdk

if TYPE_CHECKING:
    from unrealsdk.unreal import UObject


@dataclass
class Package:
    name: str
    outer: Package | None = None

    _unreal: UObject | None = field(init=False, repr=False, default=None)

    @property
    def unreal(self) -> UObject:  # noqa: D102
        if self._unreal is None:
            try:
                self._unreal = unrealsdk.find_object("Package", self.path_name)
            except ValueError:
                self._unreal = unrealsdk.construct_object(
                    "Package",
                    None if self.outer is None else self.outer.unreal,
                    self.name,
                    0x4000,
                )
        return self._unreal

    @property
    def path_name(self) -> str:  # noqa: D102
        if self.outer is None:
            return self.name
        return f"{self.outer.path_name}.{self.name}"


ROOT = Package("vendor_edit")

INV_BAL_DEF = Package("inv_bal_def", ROOT)
PART = Package("part", ROOT)
PART_COLLECTION = Package("part_collection", ROOT)
PREFIX = Package("prefix", ROOT)

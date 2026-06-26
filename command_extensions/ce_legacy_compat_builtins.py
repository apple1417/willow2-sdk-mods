# ruff: noqa: D103
from typing import TYPE_CHECKING

import unrealsdk

from .builtins import obj_name_splitter, parse_object

if TYPE_CHECKING:
    from unrealsdk.unreal import UObject

__all__: tuple[str, ...] = (
    "is_obj_instance",
    "obj_name_splitter",
    "parse_object",
)


def is_obj_instance(obj: UObject, cls: str) -> bool:
    return obj.Class._inherits(unrealsdk.find_class(cls))

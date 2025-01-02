# ruff: noqa: D103
import unrealsdk
from unrealsdk.unreal import UObject

from .builtins import obj_name_splitter, parse_object

__all__: tuple[str, ...] = (
    "is_obj_instance",
    "obj_name_splitter",
    "parse_object",
)


def is_obj_instance(obj: UObject, cls: str) -> bool:
    return obj.Class._inherits(unrealsdk.find_class(cls))

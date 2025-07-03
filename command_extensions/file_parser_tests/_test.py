import importlib.util
import json
import platform
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, ClassVar

import pytest

if TYPE_CHECKING:
    from command_extensions import file_parser


def import_from_path(module_name: str, file_path: Path) -> ModuleType:
    """
    Imports a module from a set file path.

    Args:
        module_name: The name to import the module under.
        file_path: The path to import from.
    Returns:
        The imported module.
    """
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError
    module = importlib.util.module_from_spec(spec)

    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


if platform.system() == "Windows":
    file_parser_path = Path(__file__).parent.parent / "file_parser.pyd"
else:
    file_parser_path = next(Path(__file__).parent.parent.glob("file_parser.*.so"))


file_parser = import_from_path("file_parser", file_parser_path)


@dataclass
class TestData:
    __test__: ClassVar[bool] = False

    path: Path
    commands: list[str]
    output: list[tuple[str, str, int]]

    def __init__(self, input_path: Path, data_path: Path) -> None:
        """
        Creates a test data object from it's input files.

        Args:
            input_path: The input file path.
            data_path: The corresponding test data path.
        """
        self.path = input_path

        with data_path.open() as data_file:
            data = json.load(data_file)
            self.commands = data["commands"]
            self.output = [tuple(x) for x in data["output"]]


def gather_test_data() -> list[TestData]:
    """
    Creates the test data objects for all standard test files.

    Returns:
        A list of test data objects.
    """
    all_test_data = [
        TestData(
            Path(__file__).parent.parent / "sanic.blcm",
            Path(__file__).parent / "sanic.blcm.json",
        ),
    ]

    for input_path in Path(__file__).parent.glob("**/*.test_in"):
        data_path = input_path.with_suffix(".json")
        if not data_path.exists():
            warnings.warn(
                f"Skipping '{input_path}' because it does not have a corresponding data file.",
                stacklevel=1,
            )
            continue

        all_test_data.append(TestData(input_path, data_path))

    return all_test_data


def test_non_existent_file() -> None:
    dummy_path = Path("dummy")
    assert not dummy_path.exists()

    file_parser.update_commands([])
    with pytest.raises(FileNotFoundError):
        file_parser.parse(dummy_path)


def test_corrupt_blcm() -> None:
    file_parser.update_commands(["CE_EnableOn", "chat"])
    with pytest.raises(file_parser.BLCMParserError):
        file_parser.parse(Path(__file__).parent / "corrupt.blcm")


def test_no_commands() -> None:
    file_parser.update_commands([])
    assert file_parser.parse(Path(__file__)) == []


@pytest.mark.parametrize("data", gather_test_data(), ids=lambda d: d.path.name)
def test_parsing(data: TestData) -> None:
    file_parser.update_commands(data.commands)
    assert file_parser.parse(data.path) == data.output

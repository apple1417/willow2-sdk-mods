from os import PathLike

class BLCMParserError(RuntimeError): ...

class ParseResult:
    blimp_tags: dict[str, list[str]]
    untagged_lines: list[str]
    game: str | None
    spark_service_idx: int | None

def parse(file_path: PathLike[str]) -> ParseResult:
    """
    Parses the tml-specific info out of mod file.

    Args:
        file_path: The file to parse.
    Returns:
        The parsing result.
    """

def parse_string(string: str) -> ParseResult:
    """
    Parses the tml-specific info out of a string.

    Args:
        string: The string to parse.
    Returns:
        The parsing result.
    """

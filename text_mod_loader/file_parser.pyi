from os import PathLike

class BLCMParserError(RuntimeError): ...

def parse(file_path: PathLike[str]) -> tuple[int | None, str | None, list[str]]:
    """
    Parses the tml-specific info out of mod file.

    Args:
        file_path: The file to parse.
    Returns:
        A tuple of the extracted spark service index (or None), the recommended game (or
        None), and a list of the description comments.
    """

def parse_string(string: str) -> tuple[int | None, str | None, list[str]]:
    """
    Parses the tml-specific info out of a string.

    Args:
        string: The string to parse.
    Returns:
        A tuple of the extracted spark service index (or None), the recommended game (or
        None), and a list of the description comments.
    """

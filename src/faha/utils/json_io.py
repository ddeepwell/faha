"""Read and write with JSON."""
import json
from pathlib import Path


def read(file: Path) -> dict:
    """Read json file.

    Args:
        file (Path): JSON file

    Returns:
        dict: JSON file contents
    """
    with open(file, "r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


def write(file: Path, contents: dict) -> None:
    """Write content to a file.

    Args:
        file (Path): File to write to
        contents (str): Content to write
    """
    with open(file, "w", encoding="utf-8") as file_handle:
        json.dump(contents, file_handle)

"""Read and write string content."""
from pathlib import Path


def read_file(file: Path) -> str:
    """Read content from a file.

    Args:
        file: File to read from
    """
    with open(file, "r", encoding="utf-8") as file_handle:
        return file_handle.read()


def write_file(file: Path, content: str) -> None:
    """Write content to a file.

    Args:
        file: File to write to
        content: Content to write
    """
    with open(file, "w", encoding="utf-8") as file_handle:
        file_handle.write(content)

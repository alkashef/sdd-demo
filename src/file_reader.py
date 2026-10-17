"""Reads plain-text files: documents from a folder, prompt files and evaluation files.

The only module that reads plain-text files (design section 2.1). It does not parse what it reads
(`evaluation` and `prompt_data` do) and it writes nothing (DEC-009).
Implements EXT-001, JOB-001 and DEC-017 (reading only).
"""

from pathlib import Path

from src.records import Document


def read_documents(folder: Path) -> list[Document]:
    """Read every visible file in a folder into a `Document`.

    Args:
        folder: The folder of CVs or job descriptions.

    Returns:
        One `Document` per file, with the file name as its ID, sorted by file name.

    Raises:
        FileNotFoundError: If `folder` is not an existing folder.
    """
    if not folder.is_dir():
        raise FileNotFoundError(f"Document folder not found: {folder}")
    files = sorted(
        (path for path in folder.iterdir() if path.is_file() and not path.name.startswith(".")),
        key=lambda path: path.name,
    )
    return [Document(path.name, path.read_text(encoding="utf-8")) for path in files]


def read_text(path: Path) -> str:
    """Read one prompt file or evaluation file as text.

    Args:
        path: The file to read.

    Returns:
        The file content.

    Raises:
        FileNotFoundError: If `path` is not an existing file.
    """
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    return path.read_text(encoding="utf-8")

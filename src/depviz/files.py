"""Writing of text files with readable errors."""

from depviz.errors import DepvizError


def write_text(path: str, text: str) -> None:
    """Write a UTF-8 text file."""
    try:
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    except OSError as error:
        raise DepvizError(f"cannot write {path}: {error}") from error

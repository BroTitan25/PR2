"""Shared helpers for tests."""

import io
import os
from contextlib import redirect_stderr, redirect_stdout
from typing import List, Tuple

from depviz.cli import main


def run_cli(argv: List[str]) -> Tuple[int, str, str]:
    """Run the CLI and return exit code, stdout and stderr."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


def write_file(directory: str, name: str, text: str) -> str:
    """Create a UTF-8 text file and return its path."""
    path = os.path.join(directory, name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path

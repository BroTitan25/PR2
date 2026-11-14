"""Entry point of the command-line tool."""

import sys
from dataclasses import asdict
from typing import List, Optional

from depviz.config import Config, load_config
from depviz.errors import DepvizError

EXIT_OK = 0
EXIT_ERROR = 1


def print_params(config: Config) -> None:
    """Print all user-configurable parameters as key-value pairs."""
    for key, value in asdict(config).items():
        print(f"{key}: {value}")


def main(argv: Optional[List[str]] = None) -> int:
    """Run the tool and return the process exit code."""
    try:
        print_params(load_config(argv))
    except DepvizError as error:
        print(f"error: {error}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_OK

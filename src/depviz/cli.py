"""Entry point of the command-line tool."""

import sys
from typing import List, Optional

from depviz.config import Config, load_config
from depviz.errors import DepvizError
from depviz.names import canonical_name
from depviz.pypi import direct_dependencies

EXIT_OK = 0
EXIT_ERROR = 1
NO_DEPENDENCIES = "(none)"


def print_direct_dependencies(config: Config) -> None:
    """Print all direct dependencies of the requested package."""
    if config.test_mode:
        raise DepvizError("test repository mode is added in stage 3")
    package = canonical_name(config.package)
    names = direct_dependencies(config.repo, package)
    print(f"Direct dependencies of {package}:")
    for name in names:
        print(name)
    if not names:
        print(NO_DEPENDENCIES)


def main(argv: Optional[List[str]] = None) -> int:
    """Run the tool and return the process exit code."""
    try:
        print_direct_dependencies(load_config(argv))
    except DepvizError as error:
        print(f"error: {error}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_OK

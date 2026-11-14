"""Reading of test repositories: graphs with Latin uppercase names.

File format: one package per line, ``NAME: DEP1 DEP2``. Empty lines and
lines starting with ``#`` are ignored. A dependency that has no line of
its own is a package without dependencies.
"""

from typing import List, Tuple

from depviz.errors import DepvizError
from depviz.graph import Graph
from depviz.names import TEST_NAME_RE

COMMENT_PREFIX = "#"
SEPARATOR = ":"


def check_name(name: str, number: int) -> None:
    """Validate a package name found on a given line."""
    if not TEST_NAME_RE.match(name):
        raise DepvizError(
            f"line {number}: invalid package name {name!r}, "
            "use uppercase Latin letters"
        )


def parse_line(line: str, number: int) -> Tuple[str, List[str]]:
    """Split a line into a package name and its unique dependencies."""
    name, separator, rest = line.partition(SEPARATOR)
    if not separator:
        raise DepvizError(f"line {number}: expected 'NAME: DEPS'")
    name = name.strip()
    check_name(name, number)
    dependencies: List[str] = []
    for dependency in rest.split():
        check_name(dependency, number)
        if dependency not in dependencies:
            dependencies.append(dependency)
    return name, dependencies


def parse_test_repo(text: str) -> Graph:
    """Parse the text of a test repository into a graph."""
    graph: Graph = {}
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith(COMMENT_PREFIX):
            continue
        name, dependencies = parse_line(line, number)
        if name in graph:
            raise DepvizError(f"line {number}: package {name} repeated")
        graph[name] = dependencies
    for dependencies in list(graph.values()):
        for dependency in dependencies:
            graph.setdefault(dependency, [])
    return graph


def load_test_repo(path: str) -> Graph:
    """Read and parse a test repository file."""
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError) as error:
        raise DepvizError(f"cannot read {path}: {error}") from error
    return parse_test_repo(text)

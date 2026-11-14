"""Text representation of a dependency graph in the D2 language."""

import re
from typing import List

from depviz.graph import Graph

SIMPLE_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
HEADER = "direction: down"


def d2_id(name: str) -> str:
    """Return a package name as a D2 key, quoting it when needed."""
    if SIMPLE_ID_RE.match(name):
        return name
    escaped = name.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def to_d2(graph: Graph) -> str:
    """Convert the graph to D2: node declarations and ``->`` edges."""
    lines: List[str] = [HEADER]
    lines.extend(d2_id(node) for node in graph)
    for node, dependencies in graph.items():
        for dependency in dependencies:
            lines.append(f"{d2_id(node)} -> {d2_id(dependency)}")
    return "\n".join(lines) + "\n"

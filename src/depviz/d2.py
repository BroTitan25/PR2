"""Text representation of a dependency graph in the D2 language."""

import re
from typing import Dict, List, Optional

from depviz.graph import Graph

SIMPLE_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
HEADER = "direction: down"


def d2_id(name: str) -> str:
    """Return a package name as a D2 key, quoting it when needed."""
    if SIMPLE_ID_RE.match(name):
        return name
    escaped = name.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def d2_label(name: str, labels: Dict[str, str]) -> str:
    """Declare a node, with a text label when one is given."""
    if name not in labels:
        return d2_id(name)
    text = labels[name].replace("\\", "\\\\").replace('"', '\\"')
    return f'{d2_id(name)}: "{text}"'


def to_d2(graph: Graph, labels: Optional[Dict[str, str]] = None) -> str:
    """Convert the graph to D2: node declarations and ``->`` edges.

    ``labels`` maps a node to the text shown instead of its name.
    """
    lines: List[str] = [HEADER]
    lines.extend(d2_label(node, labels or {}) for node in graph)
    for node, dependencies in graph.items():
        for dependency in dependencies:
            lines.append(f"{d2_id(node)} -> {d2_id(dependency)}")
    return "\n".join(lines) + "\n"

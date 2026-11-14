"""Text reports about dependency graphs."""

from typing import List

from depviz.graph import Graph

NO_DEPENDENCIES = "(none)"
ARROW = " -> "


def format_graph(graph: Graph) -> List[str]:
    """Return one ``NAME -> DEPS`` line for every node of the graph."""
    lines = []
    for node, dependencies in graph.items():
        targets = ", ".join(dependencies) if dependencies else NO_DEPENDENCIES
        lines.append(f"{node}{ARROW}{targets}")
    return lines


def format_cycles(cycles: List[List[str]]) -> List[str]:
    """Return one line for every dependency cycle."""
    return [ARROW.join(cycle) for cycle in cycles]

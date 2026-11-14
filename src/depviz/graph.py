"""Dependency graph construction and analysis."""

from typing import Callable, Dict, List, Tuple

Graph = Dict[str, List[str]]
Neighbors = Callable[[str], List[str]]

START_DEPTH = 0
WHITE = "white"
GRAY = "gray"
BLACK = "black"


def build_graph(root: str, get_neighbors: Neighbors, max_depth: int) -> Graph:
    """Build the transitive graph from ``root`` with an iterative DFS.

    Nodes deeper than ``max_depth`` are kept as leaves. A node that was
    reached again by a shorter path is expanded again, so the depth limit
    never hides nodes that are reachable within the limit. Every node is
    expanded at most once per distinct depth, which also makes cyclic
    dependencies safe.
    """
    graph: Graph = {}
    best_depth: Dict[str, int] = {}
    stack: List[Tuple[str, int]] = [(root, START_DEPTH)]
    while stack:
        node, depth = stack.pop()
        known = best_depth.get(node)
        if known is not None and known <= depth:
            continue
        best_depth[node] = depth
        if depth >= max_depth:
            graph.setdefault(node, [])
            continue
        children = get_neighbors(node)
        graph[node] = list(children)
        for child in reversed(children):
            stack.append((child, depth + 1))
    return graph


def find_cycles(graph: Graph, root: str) -> List[List[str]]:
    """Find dependency cycles reachable from ``root`` without recursion.

    Each cycle is returned as a path that starts and ends in the same node.
    """
    cycles: List[List[str]] = []
    state = {root: GRAY}
    path = [root]
    stack = [(root, iter(graph.get(root, [])))]
    while stack:
        node, children = stack[-1]
        child = next(children, None)
        if child is None:
            state[node] = BLACK
            stack.pop()
            path.pop()
            continue
        status = state.get(child, WHITE)
        if status == GRAY:
            cycles.append(path[path.index(child):] + [child])
        elif status == WHITE:
            state[child] = GRAY
            path.append(child)
            stack.append((child, iter(graph.get(child, []))))
    return cycles


def invert_graph(graph: Graph) -> Graph:
    """Reverse every edge: map a package to packages that depend on it."""
    inverted: Graph = {node: [] for node in graph}
    for node, dependencies in graph.items():
        for dependency in dependencies:
            inverted.setdefault(dependency, []).append(node)
    return inverted


def merge_graphs(target: Graph, source: Graph) -> None:
    """Add all nodes of ``source`` to ``target`` keeping known edges."""
    for node, dependencies in source.items():
        if dependencies or node not in target:
            target[node] = dependencies

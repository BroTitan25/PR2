"""ASCII tree output of a dependency graph."""

from typing import List, Tuple

from depviz.graph import Graph

BRANCH = "|-- "
LAST_BRANCH = "`-- "
BAR = "|   "
BLANK = "    "
CYCLE_MARK = " (cycle)"
REPEAT_MARK = " (*)"

Entry = Tuple[str, str, bool, Tuple[str, ...]]


def child_entries(
    graph: Graph, node: str, prefix: str, ancestors: Tuple[str, ...]
) -> List[Entry]:
    """Create stack entries of the children of a node, last child first."""
    children = graph.get(node, [])
    last_index = len(children) - 1
    entries = [
        (child, prefix, index == last_index, ancestors)
        for index, child in enumerate(children)
    ]
    return entries[::-1]


def render_tree(graph: Graph, root: str) -> List[str]:
    """Draw the graph as an ASCII tree without recursion.

    ``(cycle)`` marks a package that is its own ancestor and ``(*)``
    marks a package whose dependencies are already shown above.
    """
    lines = [root]
    shown = {root}
    stack = child_entries(graph, root, "", (root,))
    while stack:
        node, prefix, is_last, ancestors = stack.pop()
        branch = LAST_BRANCH if is_last else BRANCH
        mark = ""
        expand = False
        if node in ancestors:
            mark = CYCLE_MARK
        elif node in shown and graph.get(node):
            mark = REPEAT_MARK
        else:
            shown.add(node)
            expand = True
        lines.append(prefix + branch + node + mark)
        if expand:
            indent = prefix + (BLANK if is_last else BAR)
            stack.extend(
                child_entries(graph, node, indent, ancestors + (node,))
            )
    return lines

"""Saving a dependency graph as an SVG image.

The image is made by the ``d2`` program when it is installed. Otherwise
a simple built-in layered layout is used.
"""

import html
import os
import shutil
import subprocess
import tempfile
from collections import deque
from typing import Dict, List, NamedTuple, Tuple

from depviz.errors import DepvizError
from depviz.files import write_text
from depviz.graph import Graph

D2_COMMAND = "d2"
RENDERER_D2 = "d2"
RENDERER_BUILTIN = "built-in"
NODE_HEIGHT = 36
MIN_WIDTH = 60
CHAR_WIDTH = 9
TEXT_PADDING = 24
H_GAP = 30
V_GAP = 70
MARGIN = 24
LOOP_BEND = 40
LOOP_SKEW = 8
FONT_SIZE = 14
ROOT_FILL = "#cfe8ff"
NODE_FILL = "#f4f4f4"


class Box(NamedTuple):
    """Position of a node on the canvas."""

    x: float
    y: float
    width: float
    layer: int


def compute_layers(graph: Graph, root: str) -> List[List[str]]:
    """Group nodes by the length of the shortest path from the root."""
    level = {root: 0}
    queue = deque([root])
    while queue:
        node = queue.popleft()
        for dependency in graph.get(node, []):
            if dependency not in level:
                level[dependency] = level[node] + 1
                queue.append(dependency)
    layers: List[List[str]] = [[] for _ in range(max(level.values()) + 1)]
    for node, depth in level.items():
        layers[depth].append(node)
    return layers


def node_width(name: str) -> int:
    """Width of the box that holds a package name."""
    return max(MIN_WIDTH, CHAR_WIDTH * len(name) + TEXT_PADDING)


def row_width(row: List[str]) -> int:
    """Total width of a row of boxes including gaps."""
    return sum(node_width(name) for name in row) + H_GAP * (len(row) - 1)


def place_nodes(layers: List[List[str]]) -> Tuple[Dict[str, Box], int, int]:
    """Compute boxes of all nodes and the size of the canvas."""
    widths = [row_width(row) for row in layers]
    canvas_width = max(widths) + 2 * MARGIN
    boxes: Dict[str, Box] = {}
    for index, row in enumerate(layers):
        x = (canvas_width - widths[index]) / 2
        y = MARGIN + index * (NODE_HEIGHT + V_GAP)
        for name in row:
            width = node_width(name)
            boxes[name] = Box(x, y, width, index)
            x += width + H_GAP
    rows = len(layers)
    height = 2 * MARGIN + rows * NODE_HEIGHT + (rows - 1) * V_GAP
    return boxes, canvas_width, height


def edge_path(source: Box, target: Box) -> str:
    """Path of an arrow between two boxes; back edges bend to the right."""
    if target.layer > source.layer:
        x1 = source.x + source.width / 2
        y1 = source.y + NODE_HEIGHT
        x2 = target.x + target.width / 2
        return f"M {x1:.1f} {y1:.1f} L {x2:.1f} {target.y:.1f}"
    x1 = source.x + source.width
    y1 = source.y + NODE_HEIGHT / 2 - LOOP_SKEW
    x2 = target.x + target.width
    y2 = target.y + NODE_HEIGHT / 2 + LOOP_SKEW
    return (
        f"M {x1:.1f} {y1:.1f} C {x1 + LOOP_BEND:.1f} {y1:.1f} "
        f"{x2 + LOOP_BEND:.1f} {y2:.1f} {x2:.1f} {y2:.1f}"
    )


def node_svg(name: str, box: Box, is_root: bool) -> str:
    """SVG elements of one node: a rectangle and its label."""
    fill = ROOT_FILL if is_root else NODE_FILL
    center_x = box.x + box.width / 2
    center_y = box.y + NODE_HEIGHT / 2
    return (
        f'<rect x="{box.x:.1f}" y="{box.y:.1f}" width="{box.width}" '
        f'height="{NODE_HEIGHT}" rx="6" fill="{fill}" stroke="#333"/>\n'
        f'<text x="{center_x:.1f}" y="{center_y:.1f}" '
        f'text-anchor="middle" dominant-baseline="middle" '
        f'font-family="monospace" font-size="{FONT_SIZE}">'
        f"{html.escape(name)}</text>"
    )


def render_svg(graph: Graph, root: str) -> str:
    """Draw the graph with the built-in layered layout."""
    boxes, width, height = place_nodes(compute_layers(graph, root))
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="10" '
        'refX="9" refY="5" orient="auto">'
        '<path d="M0,0 L10,5 L0,10 z" fill="#555"/></marker></defs>',
    ]
    for node, dependencies in graph.items():
        for dependency in dependencies:
            path = edge_path(boxes[node], boxes[dependency])
            parts.append(
                f'<path d="{path}" fill="none" stroke="#555" '
                'marker-end="url(#arrow)"/>'
            )
    parts.extend(node_svg(n, box, n == root) for n, box in boxes.items())
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def render_with_d2(d2_text: str, svg_path: str) -> bool:
    """Make the image with the d2 program; return False if it is missing."""
    command = shutil.which(D2_COMMAND)
    if command is None:
        return False
    with tempfile.TemporaryDirectory() as folder:
        source = os.path.join(folder, "graph.d2")
        write_text(source, d2_text)
        result = subprocess.run(
            [command, source, svg_path],
            capture_output=True, text=True, check=False,
        )
    if result.returncode:
        raise DepvizError(f"d2 failed: {result.stderr.strip()}")
    return True


def write_svg(graph: Graph, root: str, d2_text: str, path: str) -> str:
    """Save the SVG image and return the name of the renderer used."""
    if render_with_d2(d2_text, path):
        return RENDERER_D2
    write_text(path, render_svg(graph, root))
    return RENDERER_BUILTIN

"""Entry point of the command-line tool."""

import os
import sys
from typing import Dict, List, Optional, Tuple

from depviz.config import Config, load_config
from depviz.d2 import to_d2
from depviz.errors import DepvizError
from depviz.files import write_text
from depviz.graph import Graph, build_graph, find_cycles
from depviz.pypi import package_version
from depviz.report import format_cycles, format_graph
from depviz.sources import forward_neighbors, reverse_neighbors, root_name
from depviz.svg import write_svg
from depviz.tree import render_tree

EXIT_OK = 0
EXIT_ERROR = 1
D2_SUFFIX = ".d2"


def collect_graph(config: Config) -> Tuple[Graph, Dict[str, str]]:
    """Build the graph and collect version specifiers of its packages."""
    requirements: Dict[str, str] = {}
    if config.reverse:
        neighbors = reverse_neighbors(config, requirements)
    else:
        neighbors = forward_neighbors(config, requirements)
    graph = build_graph(root_name(config), neighbors, config.max_depth)
    return graph, requirements


def build_labels(
    config: Config, requirements: Dict[str, str]
) -> Dict[str, str]:
    """Image labels: required versions, and the analyzed version of the root.

    Every package gets its version requirement (for example ``>=2.5``);
    the analyzed package gets the version that was actually analyzed.
    """
    if config.test_mode:
        return {}
    labels = {
        name: f"{name} {spec}" for name, spec in requirements.items() if spec
    }
    root = root_name(config)
    try:
        labels[root] = f"{root} {package_version(config.repo, root)}"
    except DepvizError:
        pass
    return labels


def print_report(config: Config, graph: Graph) -> None:
    """Print the graph and the dependency cycles found in it."""
    root = root_name(config)
    title = "Reverse dependencies" if config.reverse else "Dependencies"
    print(f"{title} of {root} (max depth {config.max_depth}):")
    for line in format_graph(graph):
        print(line)
    cycles = find_cycles(graph, root)
    if cycles:
        print("Cyclic dependencies:")
        for line in format_cycles(cycles):
            print(f"  {line}")
    if config.ascii_tree:
        print("Dependency tree:")
        print("\n".join(render_tree(graph, root)))


def export_graph(
    config: Config, graph: Graph, labels: Dict[str, str]
) -> None:
    """Save the graph as D2 text and as an SVG image."""
    root = root_name(config)
    d2_text = to_d2(graph, labels)
    d2_path = os.path.splitext(config.output)[0] + D2_SUFFIX
    write_text(d2_path, d2_text)
    renderer = write_svg(
        graph, root, d2_text, config.output, labels
    )
    print(f"D2 source saved to {d2_path}")
    print(f"SVG image saved to {config.output} (renderer: {renderer})")


def run(config: Config) -> None:
    """Analyze the package, print the report and save the image."""
    graph, requirements = collect_graph(config)
    print_report(config, graph)
    export_graph(config, graph, build_labels(config, requirements))


def main(argv: Optional[List[str]] = None) -> int:
    """Run the tool and return the process exit code."""
    try:
        run(load_config(argv))
    except DepvizError as error:
        print(f"error: {error}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_OK

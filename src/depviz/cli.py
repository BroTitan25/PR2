"""Entry point of the command-line tool."""

import sys
from typing import List, Optional

from depviz.config import Config, load_config
from depviz.errors import DepvizError
from depviz.graph import Graph, build_graph, find_cycles
from depviz.report import format_cycles, format_graph
from depviz.sources import forward_neighbors, reverse_neighbors, root_name

EXIT_OK = 0
EXIT_ERROR = 1


def collect_graph(config: Config) -> Graph:
    """Build the dependency graph of the requested package."""
    if config.reverse:
        neighbors = reverse_neighbors(config)
    else:
        neighbors = forward_neighbors(config)
    return build_graph(root_name(config), neighbors, config.max_depth)


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


def run(config: Config) -> None:
    """Analyze the package and print the report."""
    print_report(config, collect_graph(config))


def main(argv: Optional[List[str]] = None) -> int:
    """Run the tool and return the process exit code."""
    try:
        run(load_config(argv))
    except DepvizError as error:
        print(f"error: {error}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_OK

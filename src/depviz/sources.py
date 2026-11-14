"""Providers of package neighbors for the graph traversal."""

from typing import Dict, List

from depviz.config import MAX_DEPTH_LIMIT, Config
from depviz.errors import DepvizError
from depviz.graph import (
    Graph, Neighbors, build_graph, invert_graph, merge_graphs,
)
from depviz.names import canonical_name
from depviz.pypi import direct_dependencies
from depviz.testrepo import load_test_repo


def root_name(config: Config) -> str:
    """Return the name of the analyzed package as used in the graph."""
    if config.test_mode:
        return config.package
    return canonical_name(config.package)


def pypi_neighbors(repo: str) -> Neighbors:
    """Return a function that reads dependencies of a package from a URL.

    Answers are cached, so every package is requested only once.
    """
    cache: Dict[str, List[str]] = {}

    def neighbors(package: str) -> List[str]:
        """Direct dependencies of ``package``."""
        if package not in cache:
            cache[package] = direct_dependencies(repo, package)
        return cache[package]

    return neighbors


def file_neighbors(path: str, package: str) -> Neighbors:
    """Return a function that reads dependencies from a test repository."""
    graph = load_test_repo(path)
    if package not in graph:
        raise DepvizError(f"package {package} is not in test repository")

    def neighbors(name: str) -> List[str]:
        """Direct dependencies of ``name``."""
        return graph.get(name, [])

    return neighbors


def forward_neighbors(config: Config) -> Neighbors:
    """Return the neighbor function for the configured repository."""
    if config.test_mode:
        return file_neighbors(config.repo, config.package)
    return pypi_neighbors(config.repo)


def scan_candidates(config: Config) -> Graph:
    """Build the forward graph of every candidate package of a repository.

    A pip repository has no index of dependents, so reverse dependencies
    are searched among the packages given by the user.
    """
    if not config.candidates:
        raise DepvizError(
            "reverse mode with a repository URL needs --candidates"
        )
    neighbors = pypi_neighbors(config.repo)
    scanned: Graph = {}
    for candidate in config.candidates:
        start = canonical_name(candidate)
        merge_graphs(scanned, build_graph(start, neighbors, MAX_DEPTH_LIMIT))
    return scanned


def reverse_neighbors(config: Config) -> Neighbors:
    """Return a function that lists packages depending on a package."""
    if config.test_mode:
        forward = load_test_repo(config.repo)
        if config.package not in forward:
            raise DepvizError(
                f"package {config.package} is not in test repository"
            )
    else:
        forward = scan_candidates(config)
    inverted = invert_graph(forward)

    def neighbors(name: str) -> List[str]:
        """Packages that depend directly on ``name``."""
        return inverted.get(name, [])

    return neighbors

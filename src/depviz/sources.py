"""Providers of package neighbors for the graph traversal."""

from typing import Dict, List

from depviz.config import Config
from depviz.errors import DepvizError
from depviz.graph import Neighbors
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

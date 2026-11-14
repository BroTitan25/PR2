"""Command-line configuration of the tool."""

import argparse
import os
from dataclasses import dataclass
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from depviz.errors import DepvizError
from depviz.names import PIP_NAME_RE, TEST_NAME_RE

DEFAULT_REPO = "https://pypi.org/pypi"
DEFAULT_OUTPUT = "graph.svg"
DEFAULT_DEPTH = 3
MIN_DEPTH = 0
MAX_DEPTH_LIMIT = 100
URL_SCHEMES = ("http", "https")
SVG_SUFFIX = ".svg"


@dataclass(frozen=True)
class Config:
    """Settings given by the user on the command line."""

    package: str
    repo: str
    test_mode: bool
    output: str
    ascii_tree: bool
    max_depth: int
    reverse: bool = False
    candidates: Tuple[str, ...] = ()


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="depviz",
        description="Dependency graph visualizer for pip packages.",
    )
    parser.add_argument(
        "-p", "--package", required=True, help="name of the package"
    )
    parser.add_argument(
        "-r", "--repo", default=DEFAULT_REPO,
        help="repository URL or path to a test repository file",
    )
    parser.add_argument(
        "-t", "--test-mode", action="store_true",
        help="treat --repo as a test repository file",
    )
    parser.add_argument(
        "-o", "--output", default=DEFAULT_OUTPUT,
        help="name of the generated SVG file",
    )
    parser.add_argument(
        "-a", "--ascii-tree", action="store_true",
        help="print dependencies as an ASCII tree",
    )
    parser.add_argument(
        "-d", "--max-depth", type=int, default=DEFAULT_DEPTH,
        help="maximum depth of the dependency analysis",
    )
    parser.add_argument(
        "-R", "--reverse", action="store_true",
        help="print reverse dependencies (packages that depend on it)",
    )
    parser.add_argument(
        "-c", "--candidates", default="",
        help="comma-separated pip packages to scan for reverse dependencies",
    )
    return parser


def split_candidates(text: str) -> Tuple[str, ...]:
    """Split the comma-separated list of candidate packages."""
    parts = (part.strip() for part in text.split(","))
    return tuple(part for part in parts if part)


def validate_package(name: str, test_mode: bool) -> None:
    """Check the package name against the rules of the chosen mode."""
    pattern = TEST_NAME_RE if test_mode else PIP_NAME_RE
    if not pattern.match(name):
        expected = "uppercase Latin letters" if test_mode else "a pip name"
        raise DepvizError(f"invalid package name {name!r}: need {expected}")


def validate_repo(repo: str, test_mode: bool) -> None:
    """Check that the repository is a readable file or a valid URL."""
    if test_mode:
        if not os.path.isfile(repo):
            raise DepvizError(f"test repository file not found: {repo}")
        return
    parsed = urlparse(repo)
    if parsed.scheme not in URL_SCHEMES or not parsed.netloc:
        raise DepvizError(f"invalid repository URL: {repo!r}")


def validate_candidates(candidates: Tuple[str, ...], test_mode: bool) -> None:
    """Check names of the packages scanned for reverse dependencies."""
    for name in candidates:
        validate_package(name, test_mode)


def validate_output(path: str) -> None:
    """Check the name of the image file and its directory."""
    if not path.lower().endswith(SVG_SUFFIX):
        raise DepvizError(f"output file must have {SVG_SUFFIX} extension")
    directory = os.path.dirname(path) or "."
    if not os.path.isdir(directory):
        raise DepvizError(f"output directory does not exist: {directory}")


def validate_depth(depth: int) -> None:
    """Check that the depth is inside the allowed range."""
    if depth < MIN_DEPTH or depth > MAX_DEPTH_LIMIT:
        raise DepvizError(
            f"max depth must be in range {MIN_DEPTH}..{MAX_DEPTH_LIMIT}"
        )


def validate(config: Config) -> None:
    """Validate every user-configurable parameter."""
    validate_package(config.package, config.test_mode)
    validate_repo(config.repo, config.test_mode)
    validate_output(config.output)
    validate_depth(config.max_depth)
    validate_candidates(config.candidates, config.test_mode)


def load_config(argv: Optional[List[str]] = None) -> Config:
    """Parse and validate command-line arguments."""
    args = build_parser().parse_args(argv)
    config = Config(
        package=args.package,
        repo=args.repo,
        test_mode=args.test_mode,
        output=args.output,
        ascii_tree=args.ascii_tree,
        max_depth=args.max_depth,
        reverse=args.reverse,
        candidates=split_candidates(args.candidates),
    )
    validate(config)
    return config

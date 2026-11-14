"""Package name helpers."""

import re

PIP_NAME_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?$")
TEST_NAME_RE = re.compile(r"^[A-Z]+$")
SEPARATOR_RE = re.compile(r"[-_.]+")


def canonical_name(name: str) -> str:
    """Return the PEP 503 normalized form of a pip package name."""
    return SEPARATOR_RE.sub("-", name).lower()

"""Collecting direct dependencies of pip packages from a PyPI-like API."""

import json
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from depviz.errors import DepvizError
from depviz.names import canonical_name

TIMEOUT_SECONDS = 15
HTTP_NOT_FOUND = 404
REQUIREMENT_NAME_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")
EXTRA_MARKER_RE = re.compile(r"\bextra\s*==")


def metadata_url(repo: str, package: str) -> str:
    """Build the URL of the JSON description of a package."""
    return f"{repo.rstrip('/')}/{package}/json"


def http_error(url: str, error: urllib.error.HTTPError) -> DepvizError:
    """Convert an HTTP failure into a readable error."""
    if error.code == HTTP_NOT_FOUND:
        return DepvizError(f"package not found: {url}")
    return DepvizError(f"HTTP error {error.code} for {url}")


def fetch_json(url: str) -> Any:
    """Download and decode a JSON document."""
    request = urllib.request.Request(
        url, headers={"Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as reply:
            return json.load(reply)
    except urllib.error.HTTPError as error:
        raise http_error(url, error) from error
    except urllib.error.URLError as error:
        raise DepvizError(f"cannot reach {url}: {error.reason}") from error
    except (OSError, ValueError) as error:
        raise DepvizError(f"cannot read data from {url}: {error}") from error


def parse_requirement(line: str) -> Optional[str]:
    """Return the canonical package name of a Requires-Dist entry.

    Optional dependencies (``extra == ...`` markers) are skipped.
    """
    requirement, _, marker = line.partition(";")
    if EXTRA_MARKER_RE.search(marker):
        return None
    match = REQUIREMENT_NAME_RE.match(requirement)
    if match is None:
        return None
    return canonical_name(match.group(1))


def fetch_info(repo: str, package: str) -> Dict[str, Any]:
    """Download the ``info`` section of the description of a package."""
    data = fetch_json(metadata_url(repo, package))
    info = data.get("info") if isinstance(data, dict) else None
    if not isinstance(info, dict):
        raise DepvizError(f"unexpected response for package {package!r}")
    return info


def package_version(repo: str, package: str) -> str:
    """Return the latest version of a package, the one that is analyzed."""
    version = fetch_info(repo, package).get("version")
    if not isinstance(version, str) or not version:
        raise DepvizError(f"version of package {package!r} is unknown")
    return version


def direct_dependencies(repo: str, package: str) -> List[str]:
    """Return names of direct dependencies of the latest package version."""
    info = fetch_info(repo, package)
    own_name = canonical_name(package)
    names: List[str] = []
    for line in info.get("requires_dist") or []:
        name = parse_requirement(line)
        if name and name != own_name and name not in names:
            names.append(name)
    return names

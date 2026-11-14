"""Tests for collecting pip dependencies (stage 2)."""

import io
import json
import unittest
import urllib.error
from unittest import mock

from depviz import pypi
from depviz.errors import DepvizError

REPO = "https://example.test/pypi"
URLOPEN = "depviz.pypi.urllib.request.urlopen"
REQUESTS_INFO = {
    "info": {
        "requires_dist": [
            "charset_normalizer (<4,>=2)",
            "idna<4,>=2.5",
            "urllib3<3,>=1.21.1",
            "PySocks!=1.5.7,>=1.5.6; extra == 'socks'",
            "certifi>=2017.4.17",
            "idna<4; python_version < '3.8'",
            "requests[security]>=2",
        ]
    }
}


def reply_with(data):
    """Create a fake HTTP reply holding a JSON document."""
    return io.BytesIO(json.dumps(data).encode("utf-8"))


class ParseRequirementTest(unittest.TestCase):
    """Extraction of package names from Requires-Dist lines."""

    def test_plain_name(self):
        self.assertEqual(pypi.parse_requirement("idna"), "idna")

    def test_version_and_extras(self):
        self.assertEqual(
            pypi.parse_requirement("Charset_Normalizer[x] (>=2,<4)"),
            "charset-normalizer",
        )

    def test_extra_marker_is_skipped(self):
        line = "PySocks>=1.5.6; extra == 'socks'"
        self.assertIsNone(pypi.parse_requirement(line))

    def test_other_marker_is_kept(self):
        line = "colorama; platform_system == 'Windows'"
        self.assertEqual(pypi.parse_requirement(line), "colorama")

    def test_garbage_line(self):
        self.assertIsNone(pypi.parse_requirement("!!!"))


class DirectDependenciesTest(unittest.TestCase):
    """Reading direct dependencies through a mocked repository."""

    def test_collects_unique_names(self):
        with mock.patch(URLOPEN, return_value=reply_with(REQUESTS_INFO)):
            names = pypi.direct_dependencies(REPO, "requests")
        self.assertEqual(
            names,
            ["charset-normalizer", "idna", "urllib3", "certifi"],
        )

    def test_package_without_dependencies(self):
        data = {"info": {"requires_dist": None}}
        with mock.patch(URLOPEN, return_value=reply_with(data)):
            self.assertEqual(pypi.direct_dependencies(REPO, "six"), [])

    def test_unexpected_format(self):
        with mock.patch(URLOPEN, return_value=reply_with([1, 2])):
            with self.assertRaises(DepvizError):
                pypi.direct_dependencies(REPO, "six")

    def test_not_found(self):
        failure = urllib.error.HTTPError(REPO, 404, "Not Found", {}, None)
        with mock.patch(URLOPEN, side_effect=failure):
            with self.assertRaisesRegex(DepvizError, "not found"):
                pypi.direct_dependencies(REPO, "nope")

    def test_server_error(self):
        failure = urllib.error.HTTPError(REPO, 500, "Oops", {}, None)
        with mock.patch(URLOPEN, side_effect=failure):
            with self.assertRaisesRegex(DepvizError, "500"):
                pypi.direct_dependencies(REPO, "six")

    def test_network_error(self):
        failure = urllib.error.URLError("connection refused")
        with mock.patch(URLOPEN, side_effect=failure):
            with self.assertRaisesRegex(DepvizError, "cannot reach"):
                pypi.direct_dependencies(REPO, "six")

    def test_invalid_json(self):
        with mock.patch(URLOPEN, return_value=io.BytesIO(b"<html>")):
            with self.assertRaises(DepvizError):
                pypi.direct_dependencies(REPO, "six")

    def test_url_building(self):
        self.assertEqual(
            pypi.metadata_url(REPO + "/", "requests"),
            "https://example.test/pypi/requests/json",
        )


if __name__ == "__main__":
    unittest.main()

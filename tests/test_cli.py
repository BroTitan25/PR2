"""Tests for the command-line behaviour (stage 3)."""

import os
import tempfile
import unittest
from unittest import mock

from depviz.errors import DepvizError
from depviz.pypi import Requirement
from helpers import run_cli, write_file

DEPS = "depviz.sources.direct_requirements"
VERSION = "depviz.cli.package_version"
CYCLE = "A: B\nB: C\nC: A D\nD:\n"
CHAIN = "A: B\nB: C\nC: D\nD:\n"


def reqs(names):
    """Make requirements without version specifiers from names."""
    return [Requirement(name, "") for name in names]


def run_on_repo(text, *options):
    """Run the CLI in test mode on a temporary repository file."""
    with tempfile.TemporaryDirectory() as folder:
        repo = write_file(folder, "repo.txt", text)
        return run_cli(["-t", "-r", repo, *options])


class TestRepositoryModeTest(unittest.TestCase):
    """Graph analysis on test repositories."""

    def test_prints_graph(self):
        code, out, _ = run_on_repo(CHAIN, "-p", "A", "-d", "10")
        self.assertEqual(code, 0)
        self.assertIn("A -> B\nB -> C\nC -> D\nD -> (none)\n", out)

    def test_depth_limit(self):
        _, out, _ = run_on_repo(CHAIN, "-p", "A", "-d", "1")
        self.assertIn("A -> B\nB -> (none)\n", out)
        self.assertNotIn("C ->", out)

    def test_reports_cycles(self):
        code, out, _ = run_on_repo(CYCLE, "-p", "A", "-d", "10")
        self.assertEqual(code, 0)
        self.assertIn("Cyclic dependencies:\n  A -> B -> C -> A\n", out)

    def test_unknown_package(self):
        code, _, err = run_on_repo(CHAIN, "-p", "Z")
        self.assertEqual(code, 1)
        self.assertIn("not in test repository", err)

    def test_broken_repository_file(self):
        code, _, err = run_on_repo("A B\n", "-p", "A")
        self.assertEqual(code, 1)
        self.assertIn("line 1", err)


class PypiModeTest(unittest.TestCase):
    """Graph analysis on a pip repository (mocked)."""

    def test_transitive_dependencies(self):
        table = {"requests": ["idna", "urllib3"], "idna": [], "urllib3": []}
        with mock.patch(DEPS, side_effect=lambda repo, name: reqs(table[name])):
            with mock.patch(VERSION, return_value="2.34.2"):
                code, out, _ = run_cli(["-p", "Requests", "-d", "3"])
        self.assertEqual(code, 0)
        self.assertIn("requests -> idna, urllib3\n", out)
        self.assertIn("Dependencies of requests (max depth", out)

    def test_each_package_is_requested_once(self):
        table = {"a": ["b", "c"], "b": ["c"], "c": []}
        with mock.patch(DEPS, side_effect=lambda r, n: reqs(table[n])) as fake:
            with mock.patch(VERSION, return_value="1.0"):
                run_cli(["-p", "a", "-d", "5"])
        self.assertEqual(fake.call_count, len(table))

    def test_image_shows_version_requirements(self):
        table = {
            "flask": [Requirement("click", ">=8.1.3")],
            "click": [Requirement("colorama", "")],
            "colorama": [],
        }
        with tempfile.TemporaryDirectory() as folder:
            image = os.path.join(folder, "flask.svg")
            with mock.patch(DEPS, side_effect=lambda r, n: table[n]):
                with mock.patch(VERSION, return_value="3.1.3"):
                    run_cli(["-p", "flask", "-d", "5", "-o", image])
            with open(os.path.join(folder, "flask.d2"), encoding="utf-8") as f:
                d2_text = f.read()
            with open(image, encoding="utf-8") as handle:
                svg_text = handle.read()
        self.assertIn('flask: "flask 3.1.3"', d2_text)
        self.assertIn('click: "click >=8.1.3"', d2_text)
        self.assertIn(">click &gt;=8.1.3</text>", svg_text)
        self.assertIn(">flask 3.1.3</text>", svg_text)
        self.assertIn(">colorama</text>", svg_text)

    def test_repository_error(self):
        with mock.patch(DEPS, side_effect=DepvizError("boom")):
            code, _, err = run_cli(["-p", "six"])
        self.assertEqual(code, 1)
        self.assertIn("error: boom", err)

    def test_unknown_version_is_not_fatal(self):
        broken = DepvizError("no version")
        with mock.patch(DEPS, return_value=[]):
            with mock.patch(VERSION, side_effect=broken):
                code, out, _ = run_cli(["-p", "six"])
        self.assertEqual(code, 0)
        self.assertIn("Dependencies of six (max depth", out)


if __name__ == "__main__":
    unittest.main()

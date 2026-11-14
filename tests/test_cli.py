"""Tests for the command-line behaviour (stage 3)."""

import tempfile
import unittest
from unittest import mock

from depviz.errors import DepvizError
from helpers import run_cli, write_file

DEPS = "depviz.sources.direct_dependencies"
CYCLE = "A: B\nB: C\nC: A D\nD:\n"
CHAIN = "A: B\nB: C\nC: D\nD:\n"


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
        with mock.patch(DEPS, side_effect=lambda repo, name: table[name]):
            code, out, _ = run_cli(["-p", "Requests", "-d", "3"])
        self.assertEqual(code, 0)
        self.assertIn("requests -> idna, urllib3\n", out)

    def test_each_package_is_requested_once(self):
        table = {"a": ["b", "c"], "b": ["c"], "c": []}
        with mock.patch(DEPS, side_effect=lambda r, n: table[n]) as fake:
            run_cli(["-p", "a", "-d", "5"])
        self.assertEqual(fake.call_count, len(table))

    def test_repository_error(self):
        with mock.patch(DEPS, side_effect=DepvizError("boom")):
            code, _, err = run_cli(["-p", "six"])
        self.assertEqual(code, 1)
        self.assertIn("error: boom", err)


if __name__ == "__main__":
    unittest.main()

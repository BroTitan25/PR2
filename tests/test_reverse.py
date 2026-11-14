"""Tests for reverse dependencies (stage 4)."""

import tempfile
import unittest
from unittest import mock

from depviz.graph import build_graph, invert_graph, merge_graphs
from helpers import run_cli, write_file

DEPS = "depviz.sources.direct_dependencies"
REPO = "A: B C\nB: D\nC: D\nD:\nE: D\n"


def run_reverse(*options):
    """Run the CLI in reverse test mode on the sample repository."""
    with tempfile.TemporaryDirectory() as folder:
        repo = write_file(folder, "repo.txt", REPO)
        return run_cli(["-t", "-R", "-r", repo, *options])


class GraphHelpersTest(unittest.TestCase):
    """Inversion and merging of graphs."""

    def test_invert_graph(self):
        inverted = invert_graph({"A": ["B", "C"], "B": ["C"], "C": []})
        self.assertEqual(inverted, {"A": [], "B": ["A"], "C": ["A", "B"]})

    def test_invert_twice_gives_same_edges(self):
        graph = {"A": ["B"], "B": ["C"], "C": []}
        self.assertEqual(invert_graph(invert_graph(graph)), graph)

    def test_merge_keeps_known_edges(self):
        target = {"A": ["B"], "B": []}
        merge_graphs(target, {"A": [], "C": []})
        self.assertEqual(target, {"A": ["B"], "B": [], "C": []})

    def test_same_traversal_works_on_inverted_graph(self):
        inverted = invert_graph({"A": ["B"], "B": ["C"], "C": []})
        graph = build_graph("C", lambda n: inverted.get(n, []), 10)
        self.assertEqual(list(graph), ["C", "B", "A"])


class ReverseCliTest(unittest.TestCase):
    """Reverse dependencies on test and pip repositories."""

    def test_direct_and_transitive_dependents(self):
        code, out, _ = run_reverse("-p", "D", "-d", "10")
        self.assertEqual(code, 0)
        self.assertIn("Reverse dependencies of D", out)
        self.assertIn("D -> B, C, E\n", out)
        self.assertIn("B -> A\n", out)

    def test_depth_limit(self):
        _, out, _ = run_reverse("-p", "D", "-d", "1")
        self.assertIn("D -> B, C, E\n", out)
        self.assertIn("B -> (none)\n", out)

    def test_package_without_dependents(self):
        _, out, _ = run_reverse("-p", "A")
        self.assertIn("A -> (none)\n", out)

    def test_unknown_package(self):
        code, _, err = run_reverse("-p", "Z")
        self.assertEqual(code, 1)
        self.assertIn("not in test repository", err)

    def test_pip_mode_needs_candidates(self):
        code, _, err = run_cli(["-p", "idna", "-R"])
        self.assertEqual(code, 1)
        self.assertIn("--candidates", err)

    def test_pip_mode_with_candidates(self):
        table = {"requests": ["idna"], "flask": ["click"], "idna": []}
        table["click"] = []
        with mock.patch(DEPS, side_effect=lambda r, n: table[n]):
            code, out, _ = run_cli(
                ["-p", "idna", "-R", "-c", "requests, flask", "-d", "2"]
            )
        self.assertEqual(code, 0)
        self.assertIn("idna -> requests\n", out)
        self.assertNotIn("flask", out)

    def test_invalid_candidate_name(self):
        code, _, err = run_cli(["-p", "idna", "-R", "-c", "bad name"])
        self.assertEqual(code, 1)
        self.assertIn("invalid package name", err)


if __name__ == "__main__":
    unittest.main()

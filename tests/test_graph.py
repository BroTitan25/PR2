"""Tests for the graph traversal and cycle detection (stage 3)."""

import unittest

from depviz.graph import build_graph, find_cycles
from depviz.testrepo import parse_test_repo

DIAMOND = "A: B C\nB: D\nC: D\nD:\n"
CYCLE = "A: B\nB: C\nC: A D\nD:\n"
SELF_LOOP = "A: A B\nB:\n"
CHAIN = "A: B\nB: C\nC: D\nD: E\nE:\n"
LATE_SHORTCUT = "A: B X\nB: C\nC: D\nD: E\nX: D\nE:\n"


def traverse(text, root, depth):
    """Parse a test repository and build the graph from ``root``."""
    repo = parse_test_repo(text)
    return build_graph(root, lambda name: repo.get(name, []), depth)


class BuildGraphTest(unittest.TestCase):
    """Transitive graph construction with the depth limit."""

    def test_diamond_has_all_nodes_once(self):
        graph = traverse(DIAMOND, "A", 10)
        self.assertEqual(
            graph, {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        )

    def test_dfs_order(self):
        graph = traverse(DIAMOND, "A", 10)
        self.assertEqual(list(graph), ["A", "B", "D", "C"])

    def test_depth_zero_keeps_only_root(self):
        self.assertEqual(traverse(CHAIN, "A", 0), {"A": []})

    def test_depth_limit_cuts_chain(self):
        graph = traverse(CHAIN, "A", 2)
        self.assertEqual(graph, {"A": ["B"], "B": ["C"], "C": []})

    def test_depth_larger_than_graph(self):
        graph = traverse(CHAIN, "A", 100)
        self.assertEqual(list(graph), ["A", "B", "C", "D", "E"])

    def test_shorter_path_expands_node_again(self):
        graph = traverse(LATE_SHORTCUT, "A", 3)
        self.assertEqual(graph["D"], ["E"])
        self.assertIn("E", graph)

    def test_cycle_terminates(self):
        graph = traverse(CYCLE, "A", 100)
        self.assertEqual(list(graph), ["A", "B", "C", "D"])

    def test_self_loop_terminates(self):
        graph = traverse(SELF_LOOP, "A", 100)
        self.assertEqual(graph, {"A": ["A", "B"], "B": []})

    def test_deep_chain_does_not_use_recursion(self):
        count = 5000
        edges = {str(i): [str(i + 1)] for i in range(count)}
        graph = build_graph("0", lambda n: edges.get(n, []), count + 1)
        self.assertEqual(len(graph), count + 1)


class FindCyclesTest(unittest.TestCase):
    """Detection of cyclic dependencies."""

    def test_no_cycles(self):
        graph = traverse(DIAMOND, "A", 10)
        self.assertEqual(find_cycles(graph, "A"), [])

    def test_simple_cycle(self):
        graph = traverse(CYCLE, "A", 10)
        self.assertEqual(find_cycles(graph, "A"), [["A", "B", "C", "A"]])

    def test_self_loop(self):
        graph = traverse(SELF_LOOP, "A", 10)
        self.assertEqual(find_cycles(graph, "A"), [["A", "A"]])

    def test_two_cycles(self):
        graph = traverse("A: B C\nB: A\nC: A\n", "A", 10)
        self.assertEqual(
            find_cycles(graph, "A"), [["A", "B", "A"], ["A", "C", "A"]]
        )


if __name__ == "__main__":
    unittest.main()

"""Tests for ASCII tree, D2 text and SVG output (stage 5)."""

import os
import tempfile
import unittest
import xml.etree.ElementTree as xml_tree
from unittest import mock

from depviz import svg
from depviz.d2 import d2_id, to_d2
from depviz.errors import DepvizError
from depviz.tree import render_tree
from helpers import run_cli, write_file

DIAMOND = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
CYCLE = {"A": ["B"], "B": ["A"]}


class RenderTreeTest(unittest.TestCase):
    """ASCII tree rendering."""

    def test_diamond_tree(self):
        expected = [
            "A",
            "|-- B",
            "|   `-- D",
            "`-- C",
            "    `-- D",
        ]
        self.assertEqual(render_tree(DIAMOND, "A"), expected)

    def test_repeated_subtree_is_marked(self):
        graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": ["E"]}
        graph["E"] = []
        lines = render_tree(graph, "A")
        self.assertIn("    `-- D (*)", lines)

    def test_cycle_is_marked(self):
        self.assertEqual(
            render_tree(CYCLE, "A"), ["A", "`-- B", "    `-- A (cycle)"]
        )

    def test_single_node(self):
        self.assertEqual(render_tree({"A": []}, "A"), ["A"])

    def test_output_is_ascii(self):
        text = "\n".join(render_tree(DIAMOND, "A"))
        self.assertTrue(text.isascii())


class D2Test(unittest.TestCase):
    """D2 text generation."""

    def test_edges(self):
        text = to_d2(DIAMOND)
        for edge in ("A -> B", "A -> C", "B -> D", "C -> D"):
            self.assertIn(edge + "\n", text)

    def test_isolated_node_is_declared(self):
        self.assertIn("\nA\n", to_d2({"A": []}))

    def test_special_names_are_quoted(self):
        self.assertEqual(d2_id("zope.interface"), '"zope.interface"')
        self.assertEqual(d2_id("charset-normalizer"), "charset-normalizer")
        self.assertEqual(d2_id('a"b'), '"a\\"b"')


class SvgTest(unittest.TestCase):
    """Built-in SVG renderer and the d2 wrapper."""

    def test_svg_is_valid_xml(self):
        document = svg.render_svg(DIAMOND, "A")
        root = xml_tree.fromstring(document)
        self.assertTrue(root.tag.endswith("svg"))
        self.assertEqual(document.count("<rect"), len(DIAMOND))

    def test_cycle_and_self_loop(self):
        graph = {"A": ["A", "B"], "B": ["A"]}
        document = svg.render_svg(graph, "A")
        xml_tree.fromstring(document)
        self.assertEqual(document.count("marker-end"), 3)

    def test_names_are_escaped(self):
        document = svg.render_svg({"A<B": []}, "A<B")
        self.assertIn("A&lt;B", document)
        xml_tree.fromstring(document)

    def test_layers(self):
        layers = svg.compute_layers(DIAMOND, "A")
        self.assertEqual(layers, [["A"], ["B", "C"], ["D"]])

    def test_without_d2_uses_builtin_renderer(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "g.svg")
            with mock.patch("depviz.svg.shutil.which", return_value=None):
                used = svg.write_svg(DIAMOND, "A", "A -> B", path)
            self.assertEqual(used, svg.RENDERER_BUILTIN)
            self.assertTrue(os.path.getsize(path))

    def test_d2_program_is_used_when_installed(self):
        done = mock.Mock(returncode=0, stderr="")
        with mock.patch("depviz.svg.shutil.which", return_value="/bin/d2"):
            with mock.patch("depviz.svg.subprocess.run", return_value=done):
                self.assertTrue(svg.render_with_d2("A -> B", "g.svg"))

    def test_d2_failure_is_reported(self):
        failed = mock.Mock(returncode=1, stderr="syntax error")
        with mock.patch("depviz.svg.shutil.which", return_value="/bin/d2"):
            with mock.patch("depviz.svg.subprocess.run", return_value=failed):
                with self.assertRaisesRegex(DepvizError, "syntax error"):
                    svg.render_with_d2("A -> B", "g.svg")


class VisualizationCliTest(unittest.TestCase):
    """Files and output produced by the whole tool."""

    def run_on_diamond(self, *options):
        """Run the tool on a diamond repository in a temporary folder."""
        with tempfile.TemporaryDirectory() as folder:
            repo = write_file(folder, "repo.txt", "A: B C\nB: D\nC: D\nD:\n")
            image = os.path.join(folder, "out.svg")
            args = ["-t", "-r", repo, "-p", "A", "-o", image, *options]
            with mock.patch("depviz.svg.shutil.which", return_value=None):
                result = run_cli(args)
            files = sorted(os.listdir(folder))
        return result, files

    def test_creates_d2_and_svg(self):
        (code, out, _), files = self.run_on_diamond()
        self.assertEqual(code, 0)
        self.assertEqual(files, ["out.d2", "out.svg", "repo.txt"])
        self.assertIn("SVG image saved", out)

    def test_ascii_tree_only_when_requested(self):
        (_, out, _), _ = self.run_on_diamond()
        self.assertNotIn("Dependency tree:", out)
        (_, out, _), _ = self.run_on_diamond("-a")
        self.assertIn("Dependency tree:\nA\n|-- B", out)

    def test_reverse_graph_is_drawn(self):
        (code, out, _), files = self.run_on_diamond("-R", "-p", "D")
        self.assertEqual(code, 0)
        self.assertIn("Reverse dependencies of D", out)
        self.assertIn("out.svg", files)


if __name__ == "__main__":
    unittest.main()

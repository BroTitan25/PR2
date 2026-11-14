"""Tests for reading test repositories (stage 3)."""

import tempfile
import unittest

from depviz.errors import DepvizError
from depviz.testrepo import load_test_repo, parse_test_repo
from helpers import write_file


class ParseTestRepoTest(unittest.TestCase):
    """Parsing of the test repository format."""

    def test_basic_graph(self):
        graph = parse_test_repo("A: B C\nB: C\nC:\n")
        self.assertEqual(graph, {"A": ["B", "C"], "B": ["C"], "C": []})

    def test_comments_and_blank_lines(self):
        graph = parse_test_repo("# demo\n\nA: B\n")
        self.assertEqual(graph, {"A": ["B"], "B": []})

    def test_duplicate_dependencies_are_merged(self):
        self.assertEqual(parse_test_repo("A: B B\n")["A"], ["B"])

    def test_multi_letter_names(self):
        graph = parse_test_repo("AB: CD\n")
        self.assertEqual(graph, {"AB": ["CD"], "CD": []})

    def test_missing_colon(self):
        with self.assertRaisesRegex(DepvizError, "line 1"):
            parse_test_repo("A B\n")

    def test_lowercase_name(self):
        with self.assertRaisesRegex(DepvizError, "invalid package name"):
            parse_test_repo("A: b\n")

    def test_repeated_package(self):
        with self.assertRaisesRegex(DepvizError, "repeated"):
            parse_test_repo("A: B\nA: C\n")

    def test_empty_file(self):
        self.assertEqual(parse_test_repo(""), {})


class LoadTestRepoTest(unittest.TestCase):
    """Reading of test repository files."""

    def test_load_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = write_file(folder, "repo.txt", "A: B\n")
            self.assertEqual(load_test_repo(path), {"A": ["B"], "B": []})

    def test_missing_file(self):
        with self.assertRaises(DepvizError):
            load_test_repo("no-such-file.txt")

    def test_binary_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = folder + "/repo.bin"
            with open(path, "wb") as handle:
                handle.write(b"\xff\xfe\x00\xd8")
            with self.assertRaises(DepvizError):
                load_test_repo(path)


if __name__ == "__main__":
    unittest.main()

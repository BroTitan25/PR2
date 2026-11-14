"""Tests for command-line configuration (stage 1)."""

import tempfile
import unittest

from depviz.config import (
    DEFAULT_DEPTH, DEFAULT_OUTPUT, DEFAULT_REPO, load_config,
)
from depviz.errors import DepvizError
from helpers import run_cli, write_file


class LoadConfigTest(unittest.TestCase):
    """Parsing and validation of command-line options."""

    def test_defaults(self):
        config = load_config(["-p", "requests"])
        self.assertEqual(config.package, "requests")
        self.assertEqual(config.repo, DEFAULT_REPO)
        self.assertEqual(config.output, DEFAULT_OUTPUT)
        self.assertEqual(config.max_depth, DEFAULT_DEPTH)
        self.assertFalse(config.test_mode)
        self.assertFalse(config.ascii_tree)

    def test_all_options(self):
        with tempfile.TemporaryDirectory() as folder:
            repo = write_file(folder, "repo.txt", "A: B\nB:\n")
            config = load_config([
                "-p", "A", "-r", repo, "-t", "-o", "out.svg",
                "-a", "-d", "5",
            ])
        self.assertTrue(config.test_mode)
        self.assertTrue(config.ascii_tree)
        self.assertEqual(config.max_depth, 5)
        self.assertEqual(config.output, "out.svg")

    def test_package_is_required(self):
        with self.assertRaises(SystemExit):
            load_config([])

    def test_invalid_package_name(self):
        with self.assertRaises(DepvizError):
            load_config(["-p", "bad name!"])

    def test_test_mode_requires_uppercase_name(self):
        with tempfile.TemporaryDirectory() as folder:
            repo = write_file(folder, "repo.txt", "A:\n")
            with self.assertRaises(DepvizError):
                load_config(["-p", "a", "-r", repo, "-t"])

    def test_missing_test_repository_file(self):
        with self.assertRaises(DepvizError):
            load_config(["-p", "A", "-r", "no-such-file.txt", "-t"])

    def test_invalid_url(self):
        for url in ("ftp://example.com", "pypi.org/pypi", "https://"):
            with self.assertRaises(DepvizError):
                load_config(["-p", "requests", "-r", url])

    def test_depth_out_of_range(self):
        for depth in ("-1", "101"):
            with self.assertRaises(DepvizError):
                load_config(["-p", "requests", "-d", depth])

    def test_depth_is_not_a_number(self):
        with self.assertRaises(SystemExit):
            load_config(["-p", "requests", "-d", "many"])

    def test_output_must_be_svg(self):
        with self.assertRaises(DepvizError):
            load_config(["-p", "requests", "-o", "graph.png"])

    def test_output_directory_must_exist(self):
        with self.assertRaises(DepvizError):
            load_config(["-p", "requests", "-o", "no/such/dir/g.svg"])


class CliPrototypeTest(unittest.TestCase):
    """Stage 1 behaviour: print parameters as key-value pairs."""

    def test_prints_parameters(self):
        code, out, _ = run_cli(["-p", "requests", "-d", "2"])
        self.assertEqual(code, 0)
        self.assertIn("package: requests", out)
        self.assertIn("max_depth: 2", out)
        self.assertIn("test_mode: False", out)

    def test_error_is_reported(self):
        code, out, err = run_cli(["-p", "requests", "-d", "-5"])
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("error:", err)


if __name__ == "__main__":
    unittest.main()

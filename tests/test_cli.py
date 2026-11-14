"""Tests for the command-line behaviour (stage 2)."""

import tempfile
import unittest
from unittest import mock

from depviz.errors import DepvizError
from helpers import run_cli, write_file

DEPS = "depviz.cli.direct_dependencies"


class CliTest(unittest.TestCase):
    """Printing of direct dependencies."""

    def test_prints_direct_dependencies(self):
        with mock.patch(DEPS, return_value=["idna", "urllib3"]):
            code, out, _ = run_cli(["-p", "Requests"])
        self.assertEqual(code, 0)
        self.assertIn("Direct dependencies of requests:", out)
        self.assertIn("idna\nurllib3\n", out)

    def test_no_dependencies(self):
        with mock.patch(DEPS, return_value=[]):
            code, out, _ = run_cli(["-p", "six"])
        self.assertEqual(code, 0)
        self.assertIn("(none)", out)

    def test_repository_error_is_reported(self):
        with mock.patch(DEPS, side_effect=DepvizError("boom")):
            code, _, err = run_cli(["-p", "six"])
        self.assertEqual(code, 1)
        self.assertIn("error: boom", err)

    def test_test_mode_is_not_available_yet(self):
        with tempfile.TemporaryDirectory() as folder:
            repo = write_file(folder, "repo.txt", "A:\n")
            code, _, err = run_cli(["-p", "A", "-r", repo, "-t"])
        self.assertEqual(code, 1)
        self.assertIn("stage 3", err)


if __name__ == "__main__":
    unittest.main()

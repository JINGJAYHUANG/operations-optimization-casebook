from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout

from opcase.cli import main
from tests.helpers import EXPECTED, FIXED_TIME, NEGATIVE, SUITE, case_paths, temporary_directory


class CliTests(unittest.TestCase):
    def call(self, argv):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main([str(item) for item in argv])
        return code, stdout.getvalue(), stderr.getvalue()

    def test_validate_case(self):
        code, output, _ = self.call(["validate", case_paths()[0]])
        self.assertEqual(code, 0)
        self.assertIn("VALID", output)

    def test_validate_suite(self):
        code, output, _ = self.call(["validate", "--kind", "suite", SUITE])
        self.assertEqual(code, 0)
        self.assertIn("VALID", output)

    def test_invalid_case_returns_two(self):
        code, output, _ = self.call(["validate", NEGATIVE / "infeasible-transport.json"])
        self.assertEqual(code, 2)
        self.assertIn("ERROR", output)

    def test_solve_case(self):
        with temporary_directory() as temp:
            code, output, _ = self.call(["solve", "--case", case_paths()[0], "--output", temp / "run", "--fixed-time", FIXED_TIME])
            self.assertEqual(code, 0)
            self.assertIn("PASS", output)

    def test_run_suite(self):
        with temporary_directory() as temp:
            code, output, _ = self.call(["run-suite", "--manifest", SUITE, "--output", temp / "run", "--fixed-time", FIXED_TIME])
            self.assertEqual(code, 0)
            self.assertIn("cases=10/10", output)

    def test_verify_text(self):
        code, output, _ = self.call(["verify", "--run-dir", EXPECTED])
        self.assertEqual(code, 0)
        self.assertTrue(output.startswith("PASS"))

    def test_verify_json(self):
        code, output, _ = self.call(["verify", "--run-dir", EXPECTED, "--format", "json"])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(output)["passed"])

    def test_verify_deep(self):
        code, output, _ = self.call(["verify", "--run-dir", EXPECTED, "--deep"])
        self.assertEqual(code, 0)
        self.assertIn("deep: True", output)

    def test_inspect_suite(self):
        code, output, _ = self.call(["inspect", "--run-dir", EXPECTED])
        self.assertEqual(code, 0)
        self.assertIn("Suite", output)
        self.assertIn("product_mix", output)

    def test_inspect_json(self):
        code, output, _ = self.call(["inspect", "--run-dir", EXPECTED, "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output)["case_count"], 10)

    def test_list_types(self):
        code, output, _ = self.call(["list-types"])
        self.assertEqual(code, 0)
        self.assertIn("vehicle_routing", output)
        self.assertEqual(len(output.splitlines()), 10)

    def test_list_types_json(self):
        code, output, _ = self.call(["list-types", "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(len(json.loads(output)), 10)

    def test_compare_identical(self):
        code, output, _ = self.call(["compare", "--baseline", EXPECTED, "--candidate", EXPECTED])
        self.assertEqual(code, 0)
        self.assertIn("NO_REGRESSION", output)

    def test_init_preview(self):
        with temporary_directory() as temp:
            target = temp / "starter"
            code, output, _ = self.call(["init", "--target", target])
            self.assertEqual(code, 0)
            self.assertIn("Preview", output)
            self.assertFalse(target.exists())

    def test_init_apply(self):
        with temporary_directory() as temp:
            target = temp / "starter"
            code, output, _ = self.call(["init", "--target", target, "--apply"])
            self.assertEqual(code, 0)
            self.assertTrue((target / "case.json").exists())
            self.assertIn("Created", output)

    def test_init_refuses_overwrite(self):
        with temporary_directory() as temp:
            target = temp / "starter"
            self.call(["init", "--target", target, "--apply"])
            code, _, error = self.call(["init", "--target", target, "--apply"])
            self.assertEqual(code, 2)
            self.assertIn("refusing", error)

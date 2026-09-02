from __future__ import annotations

import json
import unittest

from opcase.compare import compare_runs
from opcase.pipeline import run_case, run_suite
from tests.helpers import FIXED_TIME, SUITE, case_paths, temporary_directory


class CompareTests(unittest.TestCase):
    def test_identical_suite_no_regression(self):
        with temporary_directory() as temp:
            first, second = temp / "first", temp / "second"
            run_suite(SUITE, first, fixed_time=FIXED_TIME)
            run_suite(SUITE, second, fixed_time=FIXED_TIME)
            self.assertEqual(compare_runs(first, second)["status"], "no_regression")

    def test_removed_case_is_regression(self):
        with temporary_directory() as temp:
            first, second = temp / "first", temp / "second"
            run_suite(SUITE, first, fixed_time=FIXED_TIME)
            run_suite(SUITE, second, fixed_time=FIXED_TIME)
            summary = json.loads((second / "summary.json").read_text())
            summary["cases"] = summary["cases"][:-1]
            (second / "summary.json").write_text(json.dumps(summary))
            result = compare_runs(first, second)
            self.assertTrue(any("removed" in item for item in result["regressions"]))

    def test_status_decline_is_regression(self):
        with temporary_directory() as temp:
            path = case_paths()[0]
            first, second = temp / "first", temp / "second"
            run_case(path, first, fixed_time=FIXED_TIME)
            run_case(path, second, fixed_time=FIXED_TIME)
            summary = json.loads((second / "summary.json").read_text())
            summary["decision_status"] = "hold"
            (second / "summary.json").write_text(json.dumps(summary))
            result = compare_runs(first, second)
            self.assertIn("decision status declined", result["regressions"])

    def test_stability_decline_is_regression(self):
        with temporary_directory() as temp:
            path = case_paths()[0]
            first, second = temp / "first", temp / "second"
            run_case(path, first, fixed_time=FIXED_TIME)
            run_case(path, second, fixed_time=FIXED_TIME)
            summary = json.loads((second / "summary.json").read_text())
            summary["decision_stability_ratio"] = 0
            (second / "summary.json").write_text(json.dumps(summary))
            result = compare_runs(first, second)
            self.assertTrue(any("stability" in item for item in result["regressions"]))

    def test_result_contains_snapshots(self):
        with temporary_directory() as temp:
            first, second = temp / "first", temp / "second"
            run_case(case_paths()[0], first, fixed_time=FIXED_TIME)
            run_case(case_paths()[0], second, fixed_time=FIXED_TIME)
            result = compare_runs(first, second)
            self.assertIn("baseline", result)
            self.assertIn("candidate", result)

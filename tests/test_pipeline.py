from __future__ import annotations

import json
import unittest
from pathlib import Path

from opcase.canonical import sha256_file
from opcase.pipeline import run_case, run_suite
from opcase.verify import verify_case_run, verify_run, verify_suite_run
from tests.helpers import EXPECTED, FIXED_TIME, SUITE, case_paths, temporary_directory


CASE_PATHS = case_paths()


def file_map(root: Path):
    return {path.relative_to(root).as_posix(): sha256_file(path) for path in sorted(root.rglob("*")) if path.is_file()}


class PipelineTests(unittest.TestCase):
    def test_reference_suite_passes(self):
        with temporary_directory() as temp:
            summary = run_suite(SUITE, temp / "run", fixed_time=FIXED_TIME)
            self.assertTrue(summary["passed"])
            self.assertEqual(summary["case_count"], 10)
            self.assertEqual(summary["recommended_count"], 5)
            self.assertEqual(summary["conditional_count"], 5)
            self.assertEqual(summary["hold_count"], 0)

    def test_reference_suite_verifies(self):
        result = verify_suite_run(EXPECTED, deep=True)
        self.assertTrue(result["passed"], result)

    def test_reference_suite_generic_verify(self):
        self.assertTrue(verify_run(EXPECTED, deep=False)["passed"])

    def test_reference_suite_is_byte_deterministic(self):
        with temporary_directory() as temp:
            first = temp / "first"
            second = temp / "second"
            run_suite(SUITE, first, fixed_time=FIXED_TIME)
            run_suite(SUITE, second, fixed_time=FIXED_TIME)
            self.assertEqual(file_map(first), file_map(second))

    def test_committed_reference_matches_rebuild(self):
        with temporary_directory() as temp:
            rebuilt = temp / "rebuilt"
            run_suite(SUITE, rebuilt, fixed_time=FIXED_TIME)
            self.assertEqual(file_map(rebuilt), file_map(EXPECTED))

    def test_suite_portfolio_csv(self):
        rows = (EXPECTED / "decision-portfolio.csv").read_text().splitlines()
        self.assertEqual(len(rows), 11)
        self.assertIn("decision_status", rows[0])

    def test_suite_html_self_contained(self):
        text = (EXPECTED / "report.html").read_text()
        self.assertIn("<style>", text)
        self.assertNotIn("<script", text.lower())
        self.assertNotIn("http://", text)
        self.assertNotIn("https://", text)

    def test_nonempty_output_refused(self):
        with temporary_directory() as temp:
            output = temp / "run"
            output.mkdir()
            (output / "x").write_text("x")
            with self.assertRaises(FileExistsError):
                run_case(CASE_PATHS[0], output, fixed_time=FIXED_TIME)

    def test_replace_output(self):
        with temporary_directory() as temp:
            output = temp / "run"
            output.mkdir()
            (output / "x").write_text("x")
            summary = run_case(CASE_PATHS[0], output, fixed_time=FIXED_TIME, replace=True)
            self.assertTrue(summary["passed"])
            self.assertFalse((output / "x").exists())

    def test_tampered_summary_detected(self):
        with temporary_directory() as temp:
            output = temp / "run"
            run_case(CASE_PATHS[0], output, fixed_time=FIXED_TIME)
            summary = json.loads((output / "summary.json").read_text())
            summary["objective"] = -999
            (output / "summary.json").write_text(json.dumps(summary))
            result = verify_case_run(output)
            self.assertFalse(result["passed"])
            self.assertTrue(any("summary.json" in item for item in result["errors"]))

    def test_tampered_event_detected(self):
        with temporary_directory() as temp:
            output = temp / "run"
            run_case(CASE_PATHS[0], output, fixed_time=FIXED_TIME)
            lines = (output / "events.jsonl").read_text().splitlines()
            event = json.loads(lines[1])
            event["payload"]["objective"] = -1
            lines[1] = json.dumps(event)
            (output / "events.jsonl").write_text("\n".join(lines) + "\n")
            self.assertFalse(verify_case_run(output)["passed"])

    def test_missing_output_detected(self):
        with temporary_directory() as temp:
            output = temp / "run"
            run_case(CASE_PATHS[0], output, fixed_time=FIXED_TIME)
            (output / "report.md").unlink()
            result = verify_case_run(output)
            self.assertFalse(result["passed"])
            self.assertIn("missing output: report.md", result["errors"])


# Every case must produce the complete evidence contract.
def _make_case_run_test(index: int):
    def test(self):
        with temporary_directory() as temp:
            output = temp / "run"
            summary = run_case(CASE_PATHS[index], output, fixed_time=FIXED_TIME)
            self.assertTrue(summary["passed"])
            for name in ("solution.json", "audit.json", "sensitivity.json", "decision.json", "summary.json", "report.md", "report.html", "events.jsonl", "run-manifest.json", "inputs/case.json"):
                self.assertTrue((output / name).exists(), name)
    return test


def _make_case_verify_test(index: int):
    def test(self):
        case_id = json.loads(CASE_PATHS[index].read_text())["case_id"]
        result = verify_case_run(EXPECTED / "cases" / case_id, deep=True)
        self.assertTrue(result["passed"], result)
    return test


def _make_case_report_boundary_test(index: int):
    def test(self):
        case_id = json.loads(CASE_PATHS[index].read_text())["case_id"]
        text = (EXPECTED / "cases" / case_id / "report.md").read_text()
        self.assertIn("Interpretation boundary", text)
        self.assertIn("synthetic", text.lower())
    return test


for _index, _path in enumerate(CASE_PATHS):
    suffix = _path.stem.replace("-", "_")
    setattr(PipelineTests, f"test_case_run_{_index:02d}_{suffix}", _make_case_run_test(_index))
    setattr(PipelineTests, f"test_case_verify_{_index:02d}_{suffix}", _make_case_verify_test(_index))
    setattr(PipelineTests, f"test_case_report_boundary_{_index:02d}_{suffix}", _make_case_report_boundary_test(_index))

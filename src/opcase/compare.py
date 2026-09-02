from __future__ import annotations

from pathlib import Path
from typing import Any

from .canonical import load_json


def _load_summary(path: Path) -> dict[str, Any]:
    return load_json(path / "summary.json")


def compare_runs(baseline: Path, candidate: Path) -> dict[str, Any]:
    before = _load_summary(baseline)
    after = _load_summary(candidate)
    regressions: list[str] = []
    improvements: list[str] = []
    if "cases" in before and "cases" in after:
        before_cases = {item["case_id"]: item for item in before["cases"]}
        after_cases = {item["case_id"]: item for item in after["cases"]}
        for case_id in sorted(set(before_cases) | set(after_cases)):
            old = before_cases.get(case_id)
            new = after_cases.get(case_id)
            if old is None:
                improvements.append(f"new case added: {case_id}")
                continue
            if new is None:
                regressions.append(f"case removed: {case_id}")
                continue
            if old["passed"] and not new["passed"]:
                regressions.append(f"case regressed from pass to fail: {case_id}")
            if not old["passed"] and new["passed"]:
                improvements.append(f"case improved from fail to pass: {case_id}")
            ranks = {"recommended": 2, "conditional": 1, "hold": 0}
            if ranks[new["decision_status"]] < ranks[old["decision_status"]]:
                regressions.append(f"decision status declined: {case_id} {old['decision_status']} -> {new['decision_status']}")
            elif ranks[new["decision_status"]] > ranks[old["decision_status"]]:
                improvements.append(f"decision status improved: {case_id} {old['decision_status']} -> {new['decision_status']}")
            if new["decision_stability_ratio"] + 1e-12 < old["decision_stability_ratio"]:
                regressions.append(f"stress stability declined: {case_id}")
        if after.get("hold_count", 0) > before.get("hold_count", 0):
            regressions.append(f"hold count increased from {before.get('hold_count', 0)} to {after.get('hold_count', 0)}")
        if after.get("passed_cases", 0) < before.get("passed_cases", 0):
            regressions.append(f"passed case count decreased from {before.get('passed_cases', 0)} to {after.get('passed_cases', 0)}")
    else:
        if before.get("passed") and not after.get("passed"):
            regressions.append("case changed from pass to fail")
        ranks = {"recommended": 2, "conditional": 1, "hold": 0}
        if ranks.get(after.get("decision_status"), -1) < ranks.get(before.get("decision_status"), -1):
            regressions.append("decision status declined")
        if after.get("decision_stability_ratio", 0) < before.get("decision_stability_ratio", 0):
            regressions.append("stress stability declined")
    return {
        "schema_version": "1.0",
        "status": "regressed" if regressions else "no_regression",
        "regressions": regressions,
        "improvements": improvements,
        "baseline": before,
        "candidate": after,
    }

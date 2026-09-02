from __future__ import annotations

import csv
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from .algorithms import solve_case
from .audit import audit_solution
from .canonical import load_json, sha256_file, sha256_json, write_json
from .decision import build_decision
from .events import DeterministicClock, EventLog, verify_event_log
from .report import render_case_html, render_case_markdown, render_suite_html, render_suite_markdown
from .sensitivity import run_sensitivity
from .timeutil import format_time, parse_time
from .validation import validate_case, validate_suite


def _prepare(path: Path, replace: bool) -> None:
    if path.exists() and any(path.iterdir()):
        if not replace:
            raise FileExistsError(f"output directory is not empty: {path}")
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def run_case(case_path: Path, output_dir: Path, fixed_time: str | None = None, replace: bool = False) -> dict[str, Any]:
    case_path = case_path.resolve()
    case = load_json(case_path)
    errors = validate_case(case)
    if errors:
        raise ValueError("invalid case:\n- " + "\n- ".join(errors))
    _prepare(output_dir, replace)
    evaluated_at = parse_time(fixed_time) if fixed_time else datetime.now(timezone.utc)
    run_id = sha256_json({"case": case, "evaluated_at": format_time(evaluated_at), "version": __version__})[:24]
    write_json(output_dir / "inputs" / "case.json", case)
    events = EventLog(output_dir / "events.jsonl", run_id, DeterministicClock(evaluated_at))
    events.append("run_started", {"case_id": case["case_id"], "case_type": case["case_type"], "input_hash": sha256_json(case)})
    solution = solve_case(case)
    events.append("solution_computed", {"solver": solution["solver"], "objective": solution["objective"], "decision_hash": sha256_json(solution["decision"])})
    audit = audit_solution(case, solution)
    events.append("solution_audited", {"passed": audit["passed"], "gates": audit["gates"]})
    sensitivity = run_sensitivity(case, solution)
    events.append("sensitivity_completed", {"count": sensitivity["stress_test_count"], "stability": sensitivity["decision_stability_ratio"], "all_feasible": sensitivity["all_stress_tests_feasible"]})
    decision = build_decision(case, solution, audit, sensitivity)
    events.append("implementation_gate_evaluated", {"status": decision["status"], "hard_failures": decision["hard_failures"], "conditions": decision["conditions"]})
    write_json(output_dir / "solution.json", solution)
    write_json(output_dir / "audit.json", audit)
    write_json(output_dir / "sensitivity.json", sensitivity)
    write_json(output_dir / "decision.json", decision)
    summary = {
        "schema_version": "1.0",
        "run_id": run_id,
        "case_id": case["case_id"],
        "case_type": case["case_type"],
        "evaluated_at": format_time(evaluated_at),
        "objective": solution["objective"],
        "decision_status": decision["status"],
        "audit_passed": audit["passed"],
        "decision_stability_ratio": sensitivity["decision_stability_ratio"],
        "improvement": audit["baseline"]["improvement"] if audit["baseline"] is not None else None,
        "passed": audit["passed"] and decision["status"] != "hold",
    }
    write_json(output_dir / "summary.json", summary)
    (output_dir / "report.md").write_text(render_case_markdown(case, solution, audit, sensitivity, decision), encoding="utf-8", newline="\n")
    (output_dir / "report.html").write_text(render_case_html(case, solution, audit, sensitivity, decision), encoding="utf-8", newline="\n")
    events.append("run_completed", {"passed": summary["passed"], "summary_hash": sha256_file(output_dir / "summary.json")})
    ok, event_errors, event_details = verify_event_log(output_dir / "events.jsonl", run_id)
    if not ok:
        raise RuntimeError("new event log failed verification: " + "; ".join(event_errors))
    output_files = ["solution.json", "audit.json", "sensitivity.json", "decision.json", "summary.json", "report.md", "report.html", "events.jsonl"]
    manifest = {
        "schema_version": "1.0",
        "harness_version": __version__,
        "run_id": run_id,
        "case_id": case["case_id"],
        "evaluated_at": format_time(evaluated_at),
        "input_hashes": {"inputs/case.json": sha256_file(output_dir / "inputs" / "case.json")},
        "output_hashes": {name: sha256_file(output_dir / name) for name in output_files},
        "event_count": event_details["event_count"],
        "final_event_hash": event_details["final_event_hash"],
    }
    write_json(output_dir / "run-manifest.json", manifest)
    return summary


def run_suite(suite_path: Path, output_dir: Path, fixed_time: str | None = None, replace: bool = False) -> dict[str, Any]:
    suite_path = suite_path.resolve()
    suite = load_json(suite_path)
    errors = validate_suite(suite)
    if errors:
        raise ValueError("invalid suite:\n- " + "\n- ".join(errors))
    _prepare(output_dir, replace)
    evaluated_at = fixed_time or format_time(datetime.now(timezone.utc))
    write_json(output_dir / "inputs" / "suite.json", suite)
    rows: list[dict[str, Any]] = []
    for relative in suite["cases"]:
        case_path = (suite_path.parent / relative).resolve()
        case = load_json(case_path)
        case_dir = output_dir / "cases" / case["case_id"]
        row = run_case(case_path, case_dir, fixed_time=evaluated_at, replace=False)
        rows.append(row)
    counts = {status: sum(1 for row in rows if row["decision_status"] == status) for status in ("recommended", "conditional", "hold")}
    summary = {
        "schema_version": "1.0",
        "suite_id": suite["suite_id"],
        "evaluated_at": evaluated_at,
        "case_count": len(rows),
        "passed_cases": sum(1 for row in rows if row["passed"]),
        "recommended_count": counts["recommended"],
        "conditional_count": counts["conditional"],
        "hold_count": counts["hold"],
        "passed": all(row["passed"] for row in rows),
        "cases": rows,
    }
    write_json(output_dir / "summary.json", summary)
    (output_dir / "report.md").write_text(render_suite_markdown(summary, rows), encoding="utf-8", newline="\n")
    (output_dir / "report.html").write_text(render_suite_html(summary, rows), encoding="utf-8", newline="\n")
    with (output_dir / "decision-portfolio.csv").open("w", encoding="utf-8", newline="") as handle:
        fieldnames = ["case_id", "case_type", "objective", "decision_status", "audit_passed", "decision_stability_ratio", "improvement", "passed"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})
    output_hashes: dict[str, str] = {}
    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and path.name != "suite-manifest.json":
            output_hashes[path.relative_to(output_dir).as_posix()] = sha256_file(path)
    manifest = {
        "schema_version": "1.0",
        "harness_version": __version__,
        "suite_id": suite["suite_id"],
        "evaluated_at": evaluated_at,
        "output_hashes": output_hashes,
        "case_run_ids": {row["case_id"]: row["run_id"] for row in rows},
    }
    write_json(output_dir / "suite-manifest.json", manifest)
    return summary

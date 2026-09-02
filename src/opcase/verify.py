from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from .canonical import load_json, sha256_file
from .events import verify_event_log
from .pipeline import run_case


def verify_case_run(run_dir: Path, deep: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    manifest_path = run_dir / "run-manifest.json"
    if not manifest_path.exists():
        return {"passed": False, "errors": ["run-manifest.json is missing"], "details": {}}
    try:
        manifest = load_json(manifest_path)
    except Exception as exc:  # noqa: BLE001
        return {"passed": False, "errors": [f"invalid run manifest: {exc}"], "details": {}}
    for relative, expected in manifest.get("input_hashes", {}).items():
        path = run_dir / relative
        if not path.exists():
            errors.append(f"missing input: {relative}")
        elif sha256_file(path) != expected:
            errors.append(f"input hash mismatch: {relative}")
    for relative, expected in manifest.get("output_hashes", {}).items():
        path = run_dir / relative
        if not path.exists():
            errors.append(f"missing output: {relative}")
        elif sha256_file(path) != expected:
            errors.append(f"output hash mismatch: {relative}")
    event_ok, event_errors, event_details = verify_event_log(run_dir / "events.jsonl", manifest.get("run_id"))
    errors.extend(event_errors)
    if event_details.get("event_count") != manifest.get("event_count"):
        errors.append("event count mismatch")
    if event_details.get("final_event_hash") != manifest.get("final_event_hash"):
        errors.append("final event hash mismatch")
    if deep and not errors:
        with tempfile.TemporaryDirectory(prefix="opcase-deep-") as temporary:
            rebuilt = Path(temporary) / "rebuilt"
            run_case(
                run_dir / "inputs" / "case.json",
                rebuilt,
                fixed_time=manifest["evaluated_at"],
            )
            for relative, expected in manifest.get("output_hashes", {}).items():
                if sha256_file(rebuilt / relative) != expected:
                    errors.append(f"deep rebuild mismatch: {relative}")
            if sha256_file(rebuilt / "run-manifest.json") != sha256_file(run_dir / "run-manifest.json"):
                errors.append("deep rebuild manifest mismatch")
    return {
        "passed": not errors and event_ok,
        "errors": errors,
        "details": {
            "run_id": manifest.get("run_id"),
            "case_id": manifest.get("case_id"),
            "event_count": event_details.get("event_count", 0),
            "final_event_hash": event_details.get("final_event_hash"),
            "deep": deep,
        },
    }


def verify_suite_run(run_dir: Path, deep: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    manifest_path = run_dir / "suite-manifest.json"
    if not manifest_path.exists():
        return {"passed": False, "errors": ["suite-manifest.json is missing"], "details": {}}
    manifest = load_json(manifest_path)
    for relative, expected in manifest.get("output_hashes", {}).items():
        path = run_dir / relative
        if not path.exists():
            errors.append(f"missing output: {relative}")
        elif sha256_file(path) != expected:
            errors.append(f"output hash mismatch: {relative}")
    case_results: dict[str, Any] = {}
    for case_id in manifest.get("case_run_ids", {}):
        result = verify_case_run(run_dir / "cases" / case_id, deep=deep)
        case_results[case_id] = result
        if not result["passed"]:
            errors.append(f"case verification failed: {case_id}")
    return {
        "passed": not errors,
        "errors": errors,
        "details": {
            "suite_id": manifest.get("suite_id"),
            "case_count": len(case_results),
            "case_results": case_results,
            "deep": deep,
        },
    }


def verify_run(run_dir: Path, deep: bool = False) -> dict[str, Any]:
    if (run_dir / "suite-manifest.json").exists():
        return verify_suite_run(run_dir, deep=deep)
    return verify_case_run(run_dir, deep=deep)

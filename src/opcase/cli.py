from __future__ import annotations

import argparse
import json
import shutil
import sys
from importlib import resources
from pathlib import Path
from typing import Any

from . import __version__
from .algorithms import InfeasibleError
from .canonical import canonical_dumps, load_json, write_json
from .compare import compare_runs
from .pipeline import run_case, run_suite
from .validation import CASE_TYPES, validate_case, validate_suite
from .verify import verify_run


def path_value(value: str) -> Path:
    return Path(value)


def command_validate(args: argparse.Namespace) -> int:
    try:
        data = load_json(args.path)
        errors = validate_suite(data) if args.kind == "suite" else validate_case(data)
    except Exception as exc:  # noqa: BLE001
        print(f"validation error: {exc}", file=sys.stderr)
        return 2
    if errors:
        for error in errors:
            print(f"ERROR {error}")
        return 2
    print(f"VALID kind={args.kind} path={args.path}")
    return 0


def command_solve(args: argparse.Namespace) -> int:
    try:
        summary = run_case(args.case, args.output, fixed_time=args.fixed_time, replace=args.replace)
    except InfeasibleError as exc:
        print(f"INFEASIBLE {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"run error: {exc}", file=sys.stderr)
        return 2
    print(f"{'PASS' if summary['passed'] else 'FAIL'} case={summary['case_id']} status={summary['decision_status']} objective={summary['objective']} run_id={summary['run_id']}")
    return 0 if summary["passed"] else 1


def command_suite(args: argparse.Namespace) -> int:
    try:
        summary = run_suite(args.manifest, args.output, fixed_time=args.fixed_time, replace=args.replace)
    except Exception as exc:  # noqa: BLE001
        print(f"suite error: {exc}", file=sys.stderr)
        return 2
    print(f"{'PASS' if summary['passed'] else 'FAIL'} suite={summary['suite_id']} cases={summary['passed_cases']}/{summary['case_count']} recommended={summary['recommended_count']} conditional={summary['conditional_count']} hold={summary['hold_count']}")
    return 0 if summary["passed"] else 1


def command_verify(args: argparse.Namespace) -> int:
    result = verify_run(args.run_dir, deep=args.deep)
    if args.format == "json":
        print(canonical_dumps(result))
    else:
        print("PASS" if result["passed"] else "FAIL")
        for error in result["errors"]:
            print(f"- {error}")
        for key, value in sorted(result["details"].items()):
            if key != "case_results":
                print(f"{key}: {value}")
    return 0 if result["passed"] else 2


def command_inspect(args: argparse.Namespace) -> int:
    try:
        summary = load_json(args.run_dir / "summary.json")
    except Exception as exc:  # noqa: BLE001
        print(f"inspect error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(canonical_dumps(summary))
    elif "cases" in summary:
        print(f"Suite {summary['suite_id']} — {'PASS' if summary['passed'] else 'FAIL'}")
        for item in summary["cases"]:
            print(f"{item['case_id']:<28} {item['case_type']:<22} {item['decision_status']:<12} objective={item['objective']}")
    else:
        print(f"Case {summary['case_id']} — {summary['decision_status'].upper()} objective={summary['objective']} audit_passed={summary['audit_passed']}")
    return 0


def command_compare(args: argparse.Namespace) -> int:
    try:
        result = compare_runs(args.baseline, args.candidate)
    except Exception as exc:  # noqa: BLE001
        print(f"compare error: {exc}", file=sys.stderr)
        return 2
    if args.output:
        write_json(args.output, result)
    if args.format == "json":
        print(canonical_dumps(result))
    else:
        print(result["status"].upper())
        for item in result["regressions"]:
            print(f"REGRESSION {item}")
        for item in result["improvements"]:
            print(f"IMPROVEMENT {item}")
    return 1 if args.fail_on_regression and result["regressions"] else 0


def command_list_types(args: argparse.Namespace) -> int:
    if args.json:
        print(json.dumps(sorted(CASE_TYPES)))
    else:
        for item in sorted(CASE_TYPES):
            print(item)
    return 0


def _starter_files() -> dict[str, str]:
    root = resources.files("opcase.data")
    return {
        "case.json": root.joinpath("starter-case.json").read_text(encoding="utf-8"),
        "README.md": root.joinpath("starter-readme.md").read_text(encoding="utf-8"),
    }


def command_init(args: argparse.Namespace) -> int:
    files = _starter_files()
    conflicts = [args.target / name for name in files if (args.target / name).exists()]
    if not args.apply:
        print(f"Preview: would create {len(files)} files under {args.target}")
        for name in files:
            marker = " [exists]" if (args.target / name).exists() else ""
            print(f"- {args.target / name}{marker}")
        return 1 if conflicts else 0
    if conflicts and not args.replace:
        for path in conflicts:
            print(f"refusing to overwrite: {path}", file=sys.stderr)
        return 2
    args.target.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        destination = args.target / name
        if destination.exists() and args.replace:
            shutil.copy2(destination, destination.with_suffix(destination.suffix + ".bak"))
        destination.write_text(content, encoding="utf-8", newline="\n")
    print(f"Created {len(files)} files under {args.target}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="opcase", description="Auditable operations optimization casebook.")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate", help="validate a case or suite manifest")
    p.add_argument("--kind", choices=("case", "suite"), default="case")
    p.add_argument("path", type=path_value)
    p.set_defaults(func=command_validate)

    p = sub.add_parser("solve", help="solve and audit one case")
    p.add_argument("--case", required=True, type=path_value)
    p.add_argument("--output", required=True, type=path_value)
    p.add_argument("--fixed-time")
    p.add_argument("--replace", action="store_true")
    p.set_defaults(func=command_solve)

    p = sub.add_parser("run-suite", help="run the complete casebook suite")
    p.add_argument("--manifest", required=True, type=path_value)
    p.add_argument("--output", required=True, type=path_value)
    p.add_argument("--fixed-time")
    p.add_argument("--replace", action="store_true")
    p.set_defaults(func=command_suite)

    p = sub.add_parser("verify", help="verify hashes, event chains, and optionally rebuild")
    p.add_argument("--run-dir", required=True, type=path_value)
    p.add_argument("--deep", action="store_true")
    p.add_argument("--format", choices=("text", "json"), default="text")
    p.set_defaults(func=command_verify)

    p = sub.add_parser("inspect", help="inspect a completed case or suite")
    p.add_argument("--run-dir", required=True, type=path_value)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=command_inspect)

    p = sub.add_parser("compare", help="compare baseline and candidate runs")
    p.add_argument("--baseline", required=True, type=path_value)
    p.add_argument("--candidate", required=True, type=path_value)
    p.add_argument("--output", type=path_value)
    p.add_argument("--format", choices=("text", "json"), default="text")
    p.add_argument("--fail-on-regression", action="store_true")
    p.set_defaults(func=command_compare)

    p = sub.add_parser("list-types", help="list supported reference model types")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=command_list_types)

    p = sub.add_parser("init", help="preview or create a starter case")
    p.add_argument("--target", type=path_value, default=Path("opcase-starter"))
    p.add_argument("--apply", action="store_true")
    p.add_argument("--replace", action="store_true")
    p.set_defaults(func=command_init)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))

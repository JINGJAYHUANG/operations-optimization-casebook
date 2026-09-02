from __future__ import annotations

import tempfile
from pathlib import Path

from opcase.algorithms import InfeasibleError, solve_case
from opcase.canonical import load_json, sha256_file
from opcase.pipeline import run_suite
from opcase.verify import verify_suite_run
from opcase.validation import validate_case

ROOT = Path(__file__).resolve().parents[1]
SUITE_ROOT = ROOT / "examples" / "synthetic-suite"
SUITE = SUITE_ROOT / "casebook.json"
EXPECTED = SUITE_ROOT / "expected"
NEGATIVE = ROOT / "examples" / "negative-controls"
FIXED = "2026-09-02T00:00:00Z"


def file_map(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }

if not verify_suite_run(EXPECTED, deep=True)["passed"]:
    raise SystemExit("committed reference suite failed deep verification")

with tempfile.TemporaryDirectory(prefix="opcase-reference-") as temporary:
    rebuilt = Path(temporary) / "rebuilt"
    summary = run_suite(SUITE, rebuilt, fixed_time=FIXED)
    if not summary["passed"] or summary["case_count"] != 10:
        raise SystemExit("reference suite did not pass")
    if file_map(rebuilt) != file_map(EXPECTED):
        raise SystemExit("committed reference outputs drifted")

invalid_transport = load_json(NEGATIVE / "infeasible-transport.json")
if not validate_case(invalid_transport):
    raise SystemExit("unbalanced transportation negative control was not rejected")

cyclic = load_json(NEGATIVE / "cyclic-project.json")
try:
    solve_case(cyclic)
except InfeasibleError:
    pass
else:
    raise SystemExit("cyclic project negative control did not fail")

service_hold = load_json(NEGATIVE / "service-hold.json")
from opcase.audit import audit_solution
from opcase.decision import build_decision
from opcase.sensitivity import run_sensitivity
solution = solve_case(service_hold)
decision = build_decision(service_hold, solution, audit_solution(service_hold, solution), run_sensitivity(service_hold, solution))
if decision["status"] != "hold":
    raise SystemExit("service-gate negative control did not produce hold")

print("examples passed: 10 positive cases, 30 stresses, 3 negative controls")

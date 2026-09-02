from __future__ import annotations

from typing import Any

from .algorithms import InfeasibleError, apply_patch, solve_case
from .audit import audit_solution
from .canonical import sha256_json
from .validation import validate_case


def run_sensitivity(case: dict[str, Any], base_solution: dict[str, Any]) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    base_hash = sha256_json(base_solution["decision"])
    sense = case["objective_sense"]
    for stress in case.get("stress_tests", []):
        try:
            stressed_case = apply_patch(case, stress["patch"])
            validation_errors = validate_case(stressed_case)
            if validation_errors:
                raise ValueError("; ".join(validation_errors))
            stressed_solution = solve_case(stressed_case)
            audit = audit_solution(stressed_case, stressed_solution)
            objective_change = float(stressed_solution["objective"]) - float(base_solution["objective"])
            degradation = -objective_change if sense == "max" else objective_change
            results.append(
                {
                    "name": stress["name"],
                    "status": "solved",
                    "objective": stressed_solution["objective"],
                    "objective_change": objective_change,
                    "degradation": degradation,
                    "decision_changed": sha256_json(stressed_solution["decision"]) != base_hash,
                    "decision": stressed_solution["decision"],
                    "audit_passed": audit["core_passed"],
                }
            )
        except (ValueError, KeyError, InfeasibleError) as exc:
            results.append({"name": stress["name"], "status": "infeasible_or_invalid", "error": str(exc), "decision_changed": True, "audit_passed": False})
    solved = [item for item in results if item["status"] == "solved"]
    stable_count = sum(1 for item in solved if not item["decision_changed"])
    worst_degradation = max((float(item["degradation"]) for item in solved), default=0.0)
    return {
        "stress_test_count": len(results),
        "solved_count": len(solved),
        "decision_stability_ratio": 1.0 if not results else stable_count / len(results),
        "worst_objective_degradation": worst_degradation,
        "all_stress_tests_feasible": len(solved) == len(results),
        "results": results,
    }

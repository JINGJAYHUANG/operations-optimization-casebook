from __future__ import annotations

from typing import Any


def build_decision(case: dict[str, Any], solution: dict[str, Any], audit: dict[str, Any], sensitivity: dict[str, Any]) -> dict[str, Any]:
    policy = case.get("policy", {})
    hard_failures: list[str] = [name for name, passed in audit["gates"].items() if not passed]
    conditions: list[str] = []
    if not sensitivity["all_stress_tests_feasible"]:
        hard_failures.append("stress_test_infeasible_or_invalid")
    minimum_stability = float(policy.get("min_decision_stability_ratio", 0.0))
    if sensitivity["decision_stability_ratio"] + 1e-12 < minimum_stability:
        conditions.append("decision_changes_under_material_stress")
    maximum_degradation = policy.get("max_objective_degradation")
    if maximum_degradation is not None and sensitivity["worst_objective_degradation"] > float(maximum_degradation) + 1e-9:
        conditions.append("objective_degradation_exceeds_policy")
    if case["case_type"] == "newsvendor":
        min_fill = policy.get("min_fill_rate")
        if min_fill is not None and float(solution.get("fill_rate", 0.0)) + 1e-12 < float(min_fill):
            hard_failures.append("minimum_fill_rate_not_met")
        max_stockout = policy.get("max_stockout_probability")
        if max_stockout is not None and float(solution.get("stockout_probability", 1.0)) > float(max_stockout) + 1e-12:
            conditions.append("stockout_probability_above_preference")
    if case["case_type"] == "robust_choice":
        max_regret = policy.get("max_regret")
        if max_regret is not None and float(solution.get("max_regret", 0.0)) > float(max_regret) + 1e-9:
            hard_failures.append("max_regret_exceeded")
    owner = policy.get("implementation_owner")
    if not isinstance(owner, str) or not owner:
        hard_failures.append("implementation_owner_missing")
    if policy.get("require_human_approval", True):
        conditions.append("human_approval_required")
    if hard_failures:
        status = "hold"
    elif conditions:
        status = "conditional"
    else:
        status = "recommended"
    return {
        "status": status,
        "case_id": case["case_id"],
        "objective": solution["objective"],
        "decision": solution["decision"],
        "hard_failures": sorted(set(hard_failures)),
        "conditions": sorted(set(conditions)),
        "implementation_owner": owner,
        "approval_required": bool(policy.get("require_human_approval", True)),
        "rollback_trigger": policy.get("rollback_trigger", "Re-solve when a binding input, cost, capacity, demand, or policy assumption changes."),
        "monitoring_kpis": policy.get("monitoring_kpis", []),
        "known_limitations": case.get("known_limitations", []),
    }

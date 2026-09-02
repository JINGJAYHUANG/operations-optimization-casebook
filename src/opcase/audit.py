from __future__ import annotations

import math
from typing import Any, Callable

from .algorithms import TOL, _distance, _project_duration
from .canonical import sha256_json


def _objective_close(a: float, b: float) -> bool:
    return abs(a - b) <= max(TOL, 1e-8 * max(1.0, abs(a), abs(b)))


def _eval_product_mix(case: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    products = {item["id"]: item for item in case["data"]["products"]}
    quantities = decision
    errors: list[str] = []
    for pid in quantities:
        if pid not in products:
            errors.append(f"unknown product: {pid}")
    if any(not isinstance(value, (int, float)) or isinstance(value, bool) or value < -TOL for value in quantities.values()):
        errors.append("product quantities must be non-negative numbers")
    usage: dict[str, float] = {}
    slacks: dict[str, float] = {}
    for resource, capacity in case["data"]["capacities"].items():
        used = sum(float(quantities.get(pid, 0.0)) * float(item["resource_use"][resource]) for pid, item in products.items())
        usage[resource] = used
        slacks[resource] = float(capacity) - used
        if used > float(capacity) + TOL:
            errors.append(f"resource exceeded: {resource}")
    objective = sum(float(quantities.get(pid, 0.0)) * float(item["value"]) for pid, item in products.items())
    return {"feasible": not errors, "errors": errors, "objective": objective, "resource_usage": usage, "slacks": slacks}


def _eval_transportation(case: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    shipments = decision.get("shipments", {})
    supply = case["data"]["supply"]
    demand = case["data"]["demand"]
    costs = case["data"]["costs"]
    errors: list[str] = []
    origin_totals = {origin: 0.0 for origin in supply}
    destination_totals = {destination: 0.0 for destination in demand}
    objective = 0.0
    for origin, row in shipments.items():
        if origin not in supply or not isinstance(row, dict):
            errors.append(f"unknown origin or invalid row: {origin}")
            continue
        for destination, quantity in row.items():
            if destination not in demand:
                errors.append(f"unknown destination: {destination}")
                continue
            if not isinstance(quantity, (int, float)) or isinstance(quantity, bool) or quantity < -TOL:
                errors.append(f"invalid shipment quantity: {origin}->{destination}")
                continue
            cost = costs.get(origin, {}).get(destination)
            if cost is None and quantity > TOL:
                errors.append(f"forbidden lane used: {origin}->{destination}")
                continue
            origin_totals[origin] += float(quantity)
            destination_totals[destination] += float(quantity)
            objective += float(quantity) * float(cost or 0.0)
    for origin, available in supply.items():
        if abs(origin_totals[origin] - float(available)) > TOL:
            errors.append(f"supply mismatch: {origin}")
    for destination, required in demand.items():
        if abs(destination_totals[destination] - float(required)) > TOL:
            errors.append(f"demand mismatch: {destination}")
    return {"feasible": not errors, "errors": errors, "objective": objective, "origin_totals": origin_totals, "destination_totals": destination_totals}


def _eval_assignment(case: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    assignments = decision.get("assignments", {})
    agents = case["data"]["agents"]
    tasks = case["data"]["tasks"]
    costs = case["data"]["costs"]
    errors: list[str] = []
    if set(assignments) != set(agents):
        errors.append("every agent must be assigned exactly once")
    assigned_tasks = list(assignments.values())
    if set(assigned_tasks) != set(tasks) or len(assigned_tasks) != len(set(assigned_tasks)):
        errors.append("every task must be assigned exactly once")
    objective = 0.0
    for agent, task in assignments.items():
        cost = costs.get(agent, {}).get(task)
        if cost is None:
            errors.append(f"forbidden assignment used: {agent}->{task}")
        else:
            objective += float(cost)
    return {"feasible": not errors, "errors": errors, "objective": objective}


def _eval_facility_location(case: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    open_facilities = set(decision.get("open_facilities", []))
    assignments = decision.get("assignments", {})
    facilities = {item["id"]: item for item in case["data"]["facilities"]}
    customers = {item["id"]: item for item in case["data"]["customers"]}
    errors: list[str] = []
    if not open_facilities or not open_facilities.issubset(facilities):
        errors.append("open facilities are invalid")
    if set(assignments) != set(customers):
        errors.append("every customer must be assigned")
    loads = {fid: 0.0 for fid in open_facilities}
    shipping = 0.0
    for customer, facility in assignments.items():
        if customer not in customers or facility not in open_facilities:
            errors.append(f"invalid assignment: {customer}->{facility}")
            continue
        demand = float(customers[customer]["demand"])
        loads[facility] += demand
        cost = case["data"]["shipping_cost"].get(facility, {}).get(customer)
        if cost is None:
            errors.append(f"missing shipping cost: {facility}->{customer}")
        else:
            shipping += demand * float(cost)
    for facility, load in loads.items():
        if load > float(facilities[facility]["capacity"]) + TOL:
            errors.append(f"facility capacity exceeded: {facility}")
    fixed = sum(float(facilities[facility]["fixed_cost"]) for facility in open_facilities)
    return {"feasible": not errors, "errors": errors, "objective": fixed + shipping, "loads": loads, "fixed_cost": fixed, "shipping_cost": shipping}


def _eval_workforce_schedule(case: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    workers = decision.get("workers_by_shift", {})
    shifts = {item["id"]: item for item in case["data"]["shifts"]}
    periods = case["data"]["periods"]
    errors: list[str] = []
    coverage = {period: 0 for period in periods}
    objective = 0.0
    for sid, count in workers.items():
        if sid not in shifts or not isinstance(count, int) or isinstance(count, bool) or count < 0 or count > int(shifts.get(sid, {}).get("max_workers", -1)):
            errors.append(f"invalid shift count: {sid}")
            continue
        objective += count * float(shifts[sid]["cost"])
        for period in shifts[sid]["covers"]:
            coverage[period] += count
    for sid in shifts:
        if sid not in workers:
            errors.append(f"missing shift decision: {sid}")
    for period in periods:
        if coverage[period] < case["data"]["demand"][period]:
            errors.append(f"coverage shortfall: {period}")
    return {"feasible": not errors, "errors": errors, "objective": objective, "coverage": coverage}


def _eval_newsvendor(case: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    quantity = decision.get("order_quantity")
    errors: list[str] = []
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 0:
        return {"feasible": False, "errors": ["order_quantity must be a non-negative integer"], "objective": 0.0}
    data = case["data"]
    expected_profit = 0.0
    expected_sales = 0.0
    expected_demand = 0.0
    stockout_probability = 0.0
    for row in data["demand_distribution"]:
        demand = int(row["demand"])
        probability = float(row["probability"])
        sales = min(quantity, demand)
        leftover = max(quantity - demand, 0)
        shortage = max(demand - quantity, 0)
        expected_profit += probability * (sales * float(data["unit_price"]) + leftover * float(data["salvage_value"]) - quantity * float(data["unit_cost"]) - shortage * float(data["shortage_penalty"]))
        expected_sales += probability * sales
        expected_demand += probability * demand
        if demand > quantity:
            stockout_probability += probability
    fill_rate = 1.0 if expected_demand <= TOL else expected_sales / expected_demand
    return {"feasible": not errors, "errors": errors, "objective": expected_profit, "fill_rate": fill_rate, "stockout_probability": stockout_probability}


def _eval_project_crashing(case: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    durations = decision.get("duration_by_activity", {})
    activities = case["data"]["activities"]
    errors: list[str] = []
    direct_cost = 0.0
    for activity in activities:
        aid = activity["id"]
        if aid not in durations:
            errors.append(f"missing activity duration: {aid}")
            continue
        match = next((option for option in activity["options"] if abs(float(option["duration"]) - float(durations[aid])) <= TOL), None)
        if match is None:
            errors.append(f"invalid activity option: {aid}")
        else:
            direct_cost += float(match["cost"])
    if errors:
        return {"feasible": False, "errors": errors, "objective": 0.0}
    project_duration, starts, critical_path = _project_duration(activities, {key: float(value) for key, value in durations.items()})
    tardiness = max(0.0, project_duration - float(case["data"]["deadline"]))
    objective = direct_cost + tardiness * float(case["data"]["tardiness_penalty"])
    return {"feasible": True, "errors": [], "objective": objective, "direct_cost": direct_cost, "project_duration": project_duration, "tardiness": tardiness, "start_times": starts, "critical_path": critical_path}


def _eval_vehicle_routing(case: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    routes = decision.get("routes", [])
    data = case["data"]
    customers = {item["id"]: item for item in data["customers"]}
    errors: list[str] = []
    if not isinstance(routes, list) or len(routes) != int(data["vehicles"]):
        return {"feasible": False, "errors": ["route count must equal vehicle count"], "objective": 0.0}
    seen: list[str] = []
    total_distance = 0.0
    loads: list[float] = []
    for route in routes:
        if not isinstance(route, list):
            errors.append("each route must be an array")
            continue
        load = 0.0
        points = []
        for cid in route:
            if cid not in customers:
                errors.append(f"unknown customer: {cid}")
                continue
            seen.append(cid)
            points.append(customers[cid])
            load += float(customers[cid]["demand"])
        if load > float(data["vehicle_capacity"]) + TOL:
            errors.append("vehicle capacity exceeded")
        loads.append(load)
        if points:
            total_distance += _distance(data["depot"], points[0]) + sum(_distance(points[i], points[i + 1]) for i in range(len(points) - 1)) + _distance(points[-1], data["depot"])
    if sorted(seen) != sorted(customers) or len(seen) != len(set(seen)):
        errors.append("every customer must be served exactly once")
    used = sum(1 for route in routes if route)
    objective = total_distance * float(data.get("distance_cost", 1.0)) + used * float(data.get("vehicle_fixed_cost", 0.0))
    return {"feasible": not errors, "errors": errors, "objective": objective, "total_distance": total_distance, "loads": loads, "vehicles_used": used}


def _eval_robust_choice(case: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    selected = decision.get("selected")
    data = case["data"]
    candidate = next((item for item in data["decisions"] if item["id"] == selected), None)
    if candidate is None:
        return {"feasible": False, "errors": ["selected decision is unknown"], "objective": 0.0}
    scenarios = data["scenarios"]
    probabilities = {item["id"]: float(item["probability"]) for item in scenarios}
    scenario_ids = list(probabilities)
    best_by_scenario = {sid: min(float(item["scenario_costs"][sid]) for item in data["decisions"]) for sid in scenario_ids}
    costs = {sid: float(candidate["scenario_costs"][sid]) for sid in scenario_ids}
    expected = sum(probabilities[sid] * costs[sid] for sid in scenario_ids)
    worst = max(costs.values())
    max_regret = max(costs[sid] - best_by_scenario[sid] for sid in scenario_ids)
    criterion = data["criterion"]
    if criterion == "expected_cost":
        objective = expected
    elif criterion == "worst_case":
        objective = worst
    elif criterion == "minimax_regret":
        objective = max_regret
    else:
        weights = data.get("weights", {})
        objective = float(weights.get("expected", 0.0)) * expected + float(weights.get("worst", 0.0)) * worst + float(weights.get("regret", 0.0)) * max_regret
    return {"feasible": True, "errors": [], "objective": objective, "expected_cost": expected, "worst_case_cost": worst, "max_regret": max_regret}


def _eval_capital_budgeting(case: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    selected_list = decision.get("selected_projects", [])
    projects = {item["id"]: item for item in case["data"]["projects"]}
    selected = set(selected_list)
    errors: list[str] = []
    if len(selected) != len(selected_list) or not selected.issubset(projects):
        errors.append("selected project list is invalid")
    for pid in selected:
        if not set(projects[pid].get("requires", [])).issubset(selected):
            errors.append(f"dependency missing for {pid}")
    for group in case["data"].get("exclusive_groups", []):
        if sum(1 for pid in group if pid in selected) > 1:
            errors.append("mutual-exclusion group violated")
    cost = sum(float(projects[pid]["cost"]) for pid in selected if pid in projects)
    risk = sum(float(projects[pid]["risk"]) for pid in selected if pid in projects)
    value = sum(float(projects[pid]["value"]) for pid in selected if pid in projects)
    if cost > float(case["data"]["budget"]) + TOL:
        errors.append("budget exceeded")
    if risk > float(case["data"]["risk_budget"]) + TOL:
        errors.append("risk budget exceeded")
    return {"feasible": not errors, "errors": errors, "objective": value, "total_cost": cost, "total_risk": risk}


EVALUATORS: dict[str, Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]] = {
    "product_mix": _eval_product_mix,
    "transportation": _eval_transportation,
    "assignment": _eval_assignment,
    "facility_location": _eval_facility_location,
    "workforce_schedule": _eval_workforce_schedule,
    "newsvendor": _eval_newsvendor,
    "project_crashing": _eval_project_crashing,
    "vehicle_routing": _eval_vehicle_routing,
    "robust_choice": _eval_robust_choice,
    "capital_budgeting": _eval_capital_budgeting,
}


def evaluate_decision(case: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    return EVALUATORS[case["case_type"]](case, decision)


def audit_solution(case: dict[str, Any], solution: dict[str, Any]) -> dict[str, Any]:
    evaluation = evaluate_decision(case, solution["decision"])
    objective_matches = _objective_close(float(solution["objective"]), float(evaluation["objective"]))
    gates = {
        "solution_status_optimal": solution.get("status") == "optimal",
        "decision_feasible": bool(evaluation["feasible"]),
        "objective_recomputed": objective_matches,
        "optimality_certificate_exact": float(solution.get("optimality_gap", math.inf)) <= TOL,
    }
    core_gate_names = ("solution_status_optimal", "decision_feasible", "objective_recomputed", "optimality_certificate_exact")
    core_passed = all(gates[name] for name in core_gate_names)
    baseline = None
    if "baseline_decision" in case:
        baseline_eval = evaluate_decision(case, case["baseline_decision"])
        sense = case["objective_sense"]
        improvement = float(solution["objective"]) - float(baseline_eval["objective"]) if sense == "max" else float(baseline_eval["objective"]) - float(solution["objective"])
        baseline = {**baseline_eval, "improvement": improvement}
        gates["baseline_feasible"] = bool(baseline_eval["feasible"])
        gates["baseline_not_better"] = improvement >= -TOL
        minimum = float(case.get("policy", {}).get("min_improvement", 0.0))
        gates["minimum_improvement_met"] = improvement + TOL >= minimum
    return {
        "core_passed": core_passed,
        "passed": all(gates.values()),
        "gates": gates,
        "evaluation": evaluation,
        "baseline": baseline,
        "decision_hash": sha256_json(solution["decision"]),
        "objective_delta": float(solution["objective"]) - float(evaluation["objective"]),
    }

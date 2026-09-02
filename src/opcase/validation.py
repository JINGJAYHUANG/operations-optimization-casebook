from __future__ import annotations

import re
from typing import Any

CASE_TYPES = {
    "product_mix",
    "transportation",
    "assignment",
    "facility_location",
    "workforce_schedule",
    "newsvendor",
    "project_crashing",
    "vehicle_routing",
    "robust_choice",
    "capital_budgeting",
}
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,127}$")


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _nonnegative(value: Any) -> bool:
    return _number(value) and value >= 0


def validate_case(case: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(case, dict):
        return ["case must be an object"]
    if case.get("schema_version") != "1.0":
        errors.append("schema_version must be '1.0'")
    case_id = case.get("case_id")
    if not isinstance(case_id, str) or not ID_RE.fullmatch(case_id):
        errors.append("case_id is invalid")
    case_type = case.get("case_type")
    if case_type not in CASE_TYPES:
        errors.append(f"case_type must be one of: {', '.join(sorted(CASE_TYPES))}")
    for field in ("title", "decision_context"):
        if not isinstance(case.get(field), str) or not case.get(field):
            errors.append(f"{field} must be a non-empty string")
    if case.get("objective_sense") not in {"min", "max"}:
        errors.append("objective_sense must be min or max")
    data = case.get("data")
    if not isinstance(data, dict):
        errors.append("data must be an object")
        return errors
    policy = case.get("policy", {})
    if not isinstance(policy, dict):
        errors.append("policy must be an object")
    stress_tests = case.get("stress_tests", [])
    if not isinstance(stress_tests, list):
        errors.append("stress_tests must be an array")
    else:
        names: set[str] = set()
        for index, stress in enumerate(stress_tests):
            if not isinstance(stress, dict):
                errors.append(f"stress_tests[{index}] must be an object")
                continue
            name = stress.get("name")
            if not isinstance(name, str) or not name:
                errors.append(f"stress_tests[{index}].name must be non-empty")
            elif name in names:
                errors.append(f"duplicate stress test name: {name}")
            else:
                names.add(name)
            if not isinstance(stress.get("patch"), dict):
                errors.append(f"stress_tests[{index}].patch must be an object")
    if errors:
        return errors
    validator = globals().get(f"_validate_{case_type}")
    if validator:
        errors.extend(validator(data))
    return errors


def validate_suite(suite: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(suite, dict):
        return ["suite must be an object"]
    if suite.get("schema_version") != "1.0":
        errors.append("suite.schema_version must be '1.0'")
    suite_id = suite.get("suite_id")
    if not isinstance(suite_id, str) or not ID_RE.fullmatch(suite_id):
        errors.append("suite_id is invalid")
    cases = suite.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("suite.cases must be a non-empty array")
    else:
        seen: set[str] = set()
        for index, item in enumerate(cases):
            if not isinstance(item, str) or not item.endswith(".json"):
                errors.append(f"suite.cases[{index}] must be a JSON path")
            elif item in seen:
                errors.append(f"duplicate case path: {item}")
            else:
                seen.add(item)
    return errors


def _validate_product_mix(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    products = data.get("products")
    capacities = data.get("capacities")
    if not isinstance(products, list) or not products:
        errors.append("product_mix.products must be non-empty")
    if not isinstance(capacities, dict) or not capacities:
        errors.append("product_mix.capacities must be non-empty")
    if errors:
        return errors
    resources = set(capacities)
    ids: set[str] = set()
    for item in products:
        if not isinstance(item, dict):
            errors.append("each product must be an object")
            continue
        pid = item.get("id")
        if not isinstance(pid, str) or not pid or pid in ids:
            errors.append("product ids must be unique non-empty strings")
        else:
            ids.add(pid)
        if not _number(item.get("value")):
            errors.append(f"product {pid!r} value must be numeric")
        use = item.get("resource_use")
        if not isinstance(use, dict) or set(use) != resources or any(not _nonnegative(v) for v in use.values()):
            errors.append(f"product {pid!r} resource_use must match capacities with non-negative values")
    if any(not _nonnegative(v) for v in capacities.values()):
        errors.append("capacities must be non-negative")
    return errors


def _validate_transportation(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    supply = data.get("supply")
    demand = data.get("demand")
    costs = data.get("costs")
    if not isinstance(supply, dict) or not supply or any(not _nonnegative(v) for v in supply.values()):
        errors.append("transportation.supply must be a non-empty non-negative mapping")
    if not isinstance(demand, dict) or not demand or any(not _nonnegative(v) for v in demand.values()):
        errors.append("transportation.demand must be a non-empty non-negative mapping")
    if isinstance(supply, dict) and isinstance(demand, dict) and abs(sum(supply.values()) - sum(demand.values())) > 1e-9:
        errors.append("transportation total supply must equal total demand")
    if not isinstance(costs, dict):
        errors.append("transportation.costs must be an object")
    else:
        for origin in supply or {}:
            row = costs.get(origin)
            if not isinstance(row, dict):
                errors.append(f"missing cost row for {origin}")
                continue
            for destination in demand or {}:
                value = row.get(destination)
                if value is not None and not _number(value):
                    errors.append(f"cost {origin}->{destination} must be numeric or null")
    return errors


def _validate_assignment(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    agents = data.get("agents")
    tasks = data.get("tasks")
    costs = data.get("costs")
    if not isinstance(agents, list) or not agents or len(set(agents)) != len(agents):
        errors.append("assignment.agents must be unique and non-empty")
    if not isinstance(tasks, list) or not tasks or len(set(tasks)) != len(tasks):
        errors.append("assignment.tasks must be unique and non-empty")
    if isinstance(agents, list) and isinstance(tasks, list) and len(agents) != len(tasks):
        errors.append("reference assignment solver requires equal agent and task counts")
    if not isinstance(costs, dict):
        errors.append("assignment.costs must be an object")
    else:
        for agent in agents or []:
            row = costs.get(agent)
            if not isinstance(row, dict):
                errors.append(f"missing cost row for {agent}")
                continue
            for task in tasks or []:
                value = row.get(task)
                if value is not None and not _number(value):
                    errors.append(f"assignment cost {agent}->{task} must be numeric or null")
    return errors


def _validate_facility_location(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    facilities = data.get("facilities")
    customers = data.get("customers")
    shipping = data.get("shipping_cost")
    if not isinstance(facilities, list) or not facilities:
        errors.append("facility_location.facilities must be non-empty")
    if not isinstance(customers, list) or not customers:
        errors.append("facility_location.customers must be non-empty")
    if not isinstance(shipping, dict):
        errors.append("facility_location.shipping_cost must be an object")
    for facility in facilities or []:
        if not isinstance(facility, dict) or not isinstance(facility.get("id"), str):
            errors.append("each facility needs an id")
        elif not _nonnegative(facility.get("fixed_cost")) or not _nonnegative(facility.get("capacity")):
            errors.append(f"facility {facility.get('id')} costs and capacity must be non-negative")
    for customer in customers or []:
        if not isinstance(customer, dict) or not isinstance(customer.get("id"), str) or not _nonnegative(customer.get("demand")):
            errors.append("each customer needs id and non-negative demand")
    return errors


def _validate_workforce_schedule(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    periods = data.get("periods")
    demand = data.get("demand")
    shifts = data.get("shifts")
    if not isinstance(periods, list) or not periods or len(set(periods)) != len(periods):
        errors.append("workforce periods must be unique and non-empty")
    if not isinstance(demand, dict) or any(not _nonnegative(v) for v in demand.values()) or set(demand or {}) != set(periods or []):
        errors.append("workforce demand must match periods")
    if not isinstance(shifts, list) or not shifts:
        errors.append("workforce shifts must be non-empty")
    for shift in shifts or []:
        if not isinstance(shift, dict) or not isinstance(shift.get("id"), str):
            errors.append("each shift needs an id")
            continue
        if not _nonnegative(shift.get("cost")) or not isinstance(shift.get("max_workers"), int) or shift["max_workers"] < 0:
            errors.append(f"shift {shift.get('id')} has invalid cost or max_workers")
        covers = shift.get("covers")
        if not isinstance(covers, list) or not set(covers).issubset(set(periods or [])):
            errors.append(f"shift {shift.get('id')} covers unknown periods")
    return errors


def _validate_newsvendor(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    distribution = data.get("demand_distribution")
    if not isinstance(distribution, list) or not distribution:
        errors.append("newsvendor demand_distribution must be non-empty")
    else:
        probability = 0.0
        for row in distribution:
            if not isinstance(row, dict) or not isinstance(row.get("demand"), int) or row["demand"] < 0 or not _nonnegative(row.get("probability")):
                errors.append("newsvendor distribution rows need non-negative integer demand and probability")
            else:
                probability += row["probability"]
        if abs(probability - 1.0) > 1e-9:
            errors.append("newsvendor probabilities must sum to 1")
    for field in ("unit_cost", "unit_price", "salvage_value", "shortage_penalty"):
        if not _number(data.get(field)):
            errors.append(f"newsvendor {field} must be numeric")
    return errors


def _validate_project_crashing(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    activities = data.get("activities")
    if not isinstance(activities, list) or not activities:
        return ["project_crashing.activities must be non-empty"]
    ids = {item.get("id") for item in activities if isinstance(item, dict)}
    if None in ids or len(ids) != len(activities):
        errors.append("activity ids must be unique strings")
    for item in activities:
        if not isinstance(item, dict):
            errors.append("activities must be objects")
            continue
        if not isinstance(item.get("predecessors"), list) or not set(item["predecessors"]).issubset(ids):
            errors.append(f"activity {item.get('id')} has unknown predecessors")
        options = item.get("options")
        if not isinstance(options, list) or not options:
            errors.append(f"activity {item.get('id')} needs options")
        else:
            for option in options:
                if not isinstance(option, dict) or not _nonnegative(option.get("duration")) or not _nonnegative(option.get("cost")):
                    errors.append(f"activity {item.get('id')} has invalid option")
    if not _nonnegative(data.get("deadline")) or not _nonnegative(data.get("tardiness_penalty")):
        errors.append("project deadline and tardiness_penalty must be non-negative")
    return errors


def _validate_vehicle_routing(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    depot = data.get("depot")
    customers = data.get("customers")
    if not isinstance(depot, dict) or not all(_number(depot.get(k)) for k in ("x", "y")):
        errors.append("vehicle_routing depot requires numeric x and y")
    if not isinstance(customers, list) or not customers:
        errors.append("vehicle_routing customers must be non-empty")
    for customer in customers or []:
        if not isinstance(customer, dict) or not isinstance(customer.get("id"), str) or not all(_number(customer.get(k)) for k in ("x", "y", "demand")):
            errors.append("each customer needs id, x, y, and demand")
    if not isinstance(data.get("vehicles"), int) or data["vehicles"] < 1 or not _nonnegative(data.get("vehicle_capacity")):
        errors.append("vehicle_routing requires positive vehicles and non-negative capacity")
    return errors


def _validate_robust_choice(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    scenarios = data.get("scenarios")
    decisions = data.get("decisions")
    if not isinstance(scenarios, list) or not scenarios:
        errors.append("robust_choice.scenarios must be non-empty")
    else:
        probability = sum(item.get("probability", 0) for item in scenarios if isinstance(item, dict))
        if abs(probability - 1.0) > 1e-9:
            errors.append("robust_choice scenario probabilities must sum to 1")
    if not isinstance(decisions, list) or not decisions:
        errors.append("robust_choice.decisions must be non-empty")
    scenario_ids = {item.get("id") for item in scenarios or [] if isinstance(item, dict)}
    for decision in decisions or []:
        if not isinstance(decision, dict) or not isinstance(decision.get("id"), str):
            errors.append("each robust decision needs an id")
            continue
        costs = decision.get("scenario_costs")
        if not isinstance(costs, dict) or set(costs) != scenario_ids or any(not _number(v) for v in costs.values()):
            errors.append(f"decision {decision.get('id')} must cover every scenario")
    if data.get("criterion") not in {"expected_cost", "worst_case", "minimax_regret", "weighted"}:
        errors.append("robust_choice criterion is invalid")
    return errors


def _validate_capital_budgeting(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    projects = data.get("projects")
    if not isinstance(projects, list) or not projects:
        return ["capital_budgeting.projects must be non-empty"]
    ids = {item.get("id") for item in projects if isinstance(item, dict)}
    if None in ids or len(ids) != len(projects):
        errors.append("project ids must be unique strings")
    for project in projects:
        if not isinstance(project, dict):
            errors.append("projects must be objects")
            continue
        for field in ("cost", "value", "risk"):
            if not _nonnegative(project.get(field)):
                errors.append(f"project {project.get('id')} {field} must be non-negative")
        deps = project.get("requires", [])
        if not isinstance(deps, list) or not set(deps).issubset(ids):
            errors.append(f"project {project.get('id')} has invalid dependencies")
    for field in ("budget", "risk_budget"):
        if not _nonnegative(data.get(field)):
            errors.append(f"capital_budgeting {field} must be non-negative")
    groups = data.get("exclusive_groups", [])
    if not isinstance(groups, list) or any(not isinstance(group, list) or not set(group).issubset(ids) for group in groups):
        errors.append("exclusive_groups must contain known project ids")
    return errors

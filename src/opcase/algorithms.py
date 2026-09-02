from __future__ import annotations

import copy
import itertools
import math
from collections import defaultdict, deque
from typing import Any, Callable

TOL = 1e-8


class InfeasibleError(ValueError):
    pass


def _gaussian_solve(matrix: list[list[float]], vector: list[float]) -> list[float] | None:
    n = len(vector)
    augmented = [list(map(float, matrix[i])) + [float(vector[i])] for i in range(n)]
    for column in range(n):
        pivot = max(range(column, n), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) <= TOL:
            return None
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]
        augmented[column] = [value / divisor for value in augmented[column]]
        for row in range(n):
            if row == column:
                continue
            factor = augmented[row][column]
            if abs(factor) <= TOL:
                continue
            augmented[row] = [augmented[row][j] - factor * augmented[column][j] for j in range(n + 1)]
    return [augmented[i][-1] for i in range(n)]


def solve_product_mix(case: dict[str, Any]) -> dict[str, Any]:
    data = case["data"]
    products = data["products"]
    capacities = data["capacities"]
    ids = [p["id"] for p in products]
    n = len(products)
    constraints: list[tuple[str, list[float], float]] = []
    for resource, capacity in capacities.items():
        constraints.append((f"resource:{resource}", [float(p["resource_use"][resource]) for p in products], float(capacity)))
    for index, pid in enumerate(ids):
        row = [0.0] * n
        row[index] = 1.0
        constraints.append((f"nonnegative:{pid}", row, 0.0))
    candidates: list[dict[str, Any]] = []
    for active in itertools.combinations(range(len(constraints)), n):
        matrix: list[list[float]] = []
        rhs: list[float] = []
        for index in active:
            name, coefficients, bound = constraints[index]
            matrix.append(coefficients)
            rhs.append(bound)
        solution = _gaussian_solve(matrix, rhs)
        if solution is None:
            continue
        if any(value < -TOL for value in solution):
            continue
        feasible = True
        slacks: dict[str, float] = {}
        for name, coefficients, bound in constraints[: len(capacities)]:
            used = sum(coefficients[i] * solution[i] for i in range(n))
            slack = bound - used
            slacks[name] = slack
            if slack < -TOL:
                feasible = False
                break
        if not feasible:
            continue
        objective = sum(float(products[i]["value"]) * solution[i] for i in range(n))
        candidates.append(
            {
                "decision": {ids[i]: max(0.0, solution[i]) for i in range(n)},
                "objective": objective,
                "active_constraints": [constraints[index][0] for index in active],
                "slacks": slacks,
            }
        )
    zero = {pid: 0.0 for pid in ids}
    candidates.append(
        {
            "decision": zero,
            "objective": 0.0,
            "active_constraints": [f"nonnegative:{pid}" for pid in ids],
            "slacks": {f"resource:{r}": float(v) for r, v in capacities.items()},
        }
    )
    if not candidates:
        raise InfeasibleError("product mix has no feasible vertex")
    reverse = case["objective_sense"] == "max"
    candidates.sort(key=lambda item: item["objective"], reverse=reverse)
    best = candidates[0]
    second = next((item for item in candidates[1:] if abs(item["objective"] - best["objective"]) > TOL), None)
    return {
        "status": "optimal",
        "solver": "exact-vertex-enumeration",
        "objective": best["objective"],
        "decision": best["decision"],
        "slacks": best["slacks"],
        "active_constraints": best["active_constraints"],
        "candidate_vertices": len(candidates),
        "optimality_gap": 0.0,
        "second_best_objective": second["objective"] if second else best["objective"],
    }


class _Edge:
    __slots__ = ("to", "rev", "capacity", "cost", "initial")

    def __init__(self, to: int, rev: int, capacity: float, cost: float) -> None:
        self.to = to
        self.rev = rev
        self.capacity = capacity
        self.cost = cost
        self.initial = capacity


def _add_edge(graph: list[list[_Edge]], source: int, target: int, capacity: float, cost: float) -> None:
    forward = _Edge(target, len(graph[target]), capacity, cost)
    backward = _Edge(source, len(graph[source]), 0.0, -cost)
    graph[source].append(forward)
    graph[target].append(backward)


def solve_transportation(case: dict[str, Any]) -> dict[str, Any]:
    data = case["data"]
    origins = list(data["supply"])
    destinations = list(data["demand"])
    source = 0
    origin_offset = 1
    destination_offset = origin_offset + len(origins)
    sink = destination_offset + len(destinations)
    graph: list[list[_Edge]] = [[] for _ in range(sink + 1)]
    for i, origin in enumerate(origins):
        _add_edge(graph, source, origin_offset + i, float(data["supply"][origin]), 0.0)
    lane_edges: dict[tuple[str, str], _Edge] = {}
    total = sum(float(v) for v in data["demand"].values())
    for i, origin in enumerate(origins):
        for j, destination in enumerate(destinations):
            cost = data["costs"][origin].get(destination)
            if cost is None:
                continue
            before = len(graph[origin_offset + i])
            _add_edge(graph, origin_offset + i, destination_offset + j, total, float(cost))
            lane_edges[(origin, destination)] = graph[origin_offset + i][before]
    for j, destination in enumerate(destinations):
        _add_edge(graph, destination_offset + j, sink, float(data["demand"][destination]), 0.0)

    flow = 0.0
    objective = 0.0
    node_count = sink + 1
    while flow < total - TOL:
        distance = [math.inf] * node_count
        parent: list[tuple[int, int] | None] = [None] * node_count
        distance[source] = 0.0
        for _ in range(node_count - 1):
            changed = False
            for u in range(node_count):
                if math.isinf(distance[u]):
                    continue
                for edge_index, edge in enumerate(graph[u]):
                    if edge.capacity > TOL and distance[edge.to] > distance[u] + edge.cost + TOL:
                        distance[edge.to] = distance[u] + edge.cost
                        parent[edge.to] = (u, edge_index)
                        changed = True
            if not changed:
                break
        if parent[sink] is None:
            raise InfeasibleError("transportation network cannot satisfy all demand")
        augment = total - flow
        node = sink
        while node != source:
            u, edge_index = parent[node]  # type: ignore[misc]
            augment = min(augment, graph[u][edge_index].capacity)
            node = u
        node = sink
        while node != source:
            u, edge_index = parent[node]  # type: ignore[misc]
            edge = graph[u][edge_index]
            edge.capacity -= augment
            graph[node][edge.rev].capacity += augment
            objective += augment * edge.cost
            node = u
        flow += augment
    shipments: dict[str, dict[str, float]] = {origin: {} for origin in origins}
    for (origin, destination), edge in lane_edges.items():
        used = edge.initial - edge.capacity
        if used > TOL:
            shipments[origin][destination] = used
    return {
        "status": "optimal",
        "solver": "successive-shortest-path-min-cost-flow",
        "objective": objective,
        "decision": {"shipments": shipments},
        "flow": flow,
        "optimality_gap": 0.0,
        "used_lanes": sum(len(row) for row in shipments.values()),
    }


def solve_assignment(case: dict[str, Any]) -> dict[str, Any]:
    data = case["data"]
    agents = list(data["agents"])
    tasks = list(data["tasks"])
    candidates: list[tuple[float, tuple[str, ...]]] = []
    for permutation in itertools.permutations(tasks):
        total = 0.0
        feasible = True
        for agent, task in zip(agents, permutation):
            cost = data["costs"][agent].get(task)
            if cost is None:
                feasible = False
                break
            total += float(cost)
        if feasible:
            candidates.append((total, permutation))
    if not candidates:
        raise InfeasibleError("assignment has no complete matching")
    reverse = case["objective_sense"] == "max"
    candidates.sort(key=lambda item: item[0], reverse=reverse)
    best = candidates[0]
    second = next((item for item in candidates[1:] if abs(item[0] - best[0]) > TOL), best)
    return {
        "status": "optimal",
        "solver": "exact-permutation-enumeration",
        "objective": best[0],
        "decision": {"assignments": {agent: task for agent, task in zip(agents, best[1])}},
        "candidate_matchings": len(candidates),
        "second_best_objective": second[0],
        "optimality_gap": 0.0,
    }


def solve_facility_location(case: dict[str, Any]) -> dict[str, Any]:
    data = case["data"]
    facilities = list(data["facilities"])
    customers = sorted(data["customers"], key=lambda item: (-float(item["demand"]), item["id"]))
    facility_map = {item["id"]: item for item in facilities}
    all_ids = [item["id"] for item in facilities]
    best: dict[str, Any] | None = None
    evaluated = 0
    for mask in range(1, 1 << len(all_ids)):
        open_ids = [all_ids[i] for i in range(len(all_ids)) if mask & (1 << i)]
        total_capacity = sum(float(facility_map[fid]["capacity"]) for fid in open_ids)
        total_demand = sum(float(c["demand"]) for c in customers)
        if total_capacity + TOL < total_demand:
            continue
        remaining = {fid: float(facility_map[fid]["capacity"]) for fid in open_ids}
        fixed_cost = sum(float(facility_map[fid]["fixed_cost"]) for fid in open_ids)

        def search(index: int, assignment: dict[str, str], shipping_cost: float) -> None:
            nonlocal best, evaluated
            if best is not None and fixed_cost + shipping_cost >= best["objective"] - TOL:
                return
            if index == len(customers):
                evaluated += 1
                candidate = {
                    "objective": fixed_cost + shipping_cost,
                    "decision": {"open_facilities": sorted(open_ids), "assignments": dict(sorted(assignment.items()))},
                    "fixed_cost": fixed_cost,
                    "shipping_cost": shipping_cost,
                    "capacity_slack": {fid: remaining[fid] for fid in sorted(open_ids)},
                }
                if best is None or candidate["objective"] < best["objective"] - TOL:
                    best = candidate
                return
            customer = customers[index]
            cid = customer["id"]
            demand = float(customer["demand"])
            options = sorted(open_ids, key=lambda fid: (float(data["shipping_cost"][fid][cid]), fid))
            for fid in options:
                if remaining[fid] + TOL < demand:
                    continue
                remaining[fid] -= demand
                assignment[cid] = fid
                search(index + 1, assignment, shipping_cost + demand * float(data["shipping_cost"][fid][cid]))
                del assignment[cid]
                remaining[fid] += demand

        search(0, {}, 0.0)
    if best is None:
        raise InfeasibleError("facility location cannot cover all demand")
    return {
        "status": "optimal",
        "solver": "exact-facility-and-assignment-enumeration",
        **best,
        "evaluated_complete_assignments": evaluated,
        "optimality_gap": 0.0,
    }


def solve_workforce_schedule(case: dict[str, Any]) -> dict[str, Any]:
    data = case["data"]
    periods = list(data["periods"])
    shifts = list(data["shifts"])
    ranges = [range(int(shift["max_workers"]) + 1) for shift in shifts]
    best: dict[str, Any] | None = None
    feasible_count = 0
    for counts in itertools.product(*ranges):
        coverage = {period: 0 for period in periods}
        cost = 0.0
        for shift, count in zip(shifts, counts):
            cost += float(shift["cost"]) * count
            for period in shift["covers"]:
                coverage[period] += count
        if any(coverage[p] < data["demand"][p] for p in periods):
            continue
        feasible_count += 1
        overstaff = sum(coverage[p] - data["demand"][p] for p in periods)
        decision = {shift["id"]: count for shift, count in zip(shifts, counts)}
        candidate = {"objective": cost, "decision": {"workers_by_shift": decision}, "coverage": coverage, "overstaff": overstaff}
        if best is None or (cost, overstaff, tuple(counts)) < (best["objective"], best["overstaff"], tuple(best["decision"]["workers_by_shift"][s["id"]] for s in shifts)):
            best = candidate
    if best is None:
        raise InfeasibleError("workforce schedule cannot meet all demand")
    return {
        "status": "optimal",
        "solver": "exact-integer-enumeration",
        **best,
        "feasible_schedules": feasible_count,
        "optimality_gap": 0.0,
    }


def solve_newsvendor(case: dict[str, Any]) -> dict[str, Any]:
    data = case["data"]
    distribution = data["demand_distribution"]
    max_demand = max(int(row["demand"]) for row in distribution)
    candidates: list[dict[str, Any]] = []
    for quantity in range(max_demand + 1):
        expected_profit = 0.0
        expected_sales = 0.0
        expected_shortage = 0.0
        stockout_probability = 0.0
        for row in distribution:
            demand = int(row["demand"])
            probability = float(row["probability"])
            sales = min(quantity, demand)
            leftover = max(quantity - demand, 0)
            shortage = max(demand - quantity, 0)
            profit = (
                sales * float(data["unit_price"])
                + leftover * float(data["salvage_value"])
                - quantity * float(data["unit_cost"])
                - shortage * float(data["shortage_penalty"])
            )
            expected_profit += probability * profit
            expected_sales += probability * sales
            expected_shortage += probability * shortage
            if demand > quantity:
                stockout_probability += probability
        expected_demand = sum(float(row["probability"]) * int(row["demand"]) for row in distribution)
        fill_rate = 1.0 if expected_demand <= TOL else expected_sales / expected_demand
        candidates.append(
            {
                "quantity": quantity,
                "objective": expected_profit,
                "expected_sales": expected_sales,
                "expected_shortage": expected_shortage,
                "stockout_probability": stockout_probability,
                "fill_rate": fill_rate,
            }
        )
    candidates.sort(key=lambda item: (item["objective"], -item["quantity"]), reverse=True)
    best = candidates[0]
    second = next((item for item in candidates[1:] if abs(item["objective"] - best["objective"]) > TOL), best)
    return {
        "status": "optimal",
        "solver": "exact-discrete-expectation-enumeration",
        "objective": best["objective"],
        "decision": {"order_quantity": best["quantity"]},
        "expected_sales": best["expected_sales"],
        "expected_shortage": best["expected_shortage"],
        "stockout_probability": best["stockout_probability"],
        "fill_rate": best["fill_rate"],
        "second_best_objective": second["objective"],
        "optimality_gap": 0.0,
    }


def _topological_order(activities: list[dict[str, Any]]) -> list[str]:
    ids = [item["id"] for item in activities]
    indegree = {aid: 0 for aid in ids}
    successors: dict[str, list[str]] = {aid: [] for aid in ids}
    for item in activities:
        for predecessor in item["predecessors"]:
            successors[predecessor].append(item["id"])
            indegree[item["id"]] += 1
    queue = deque(sorted(aid for aid, degree in indegree.items() if degree == 0))
    order: list[str] = []
    while queue:
        aid = queue.popleft()
        order.append(aid)
        for successor in sorted(successors[aid]):
            indegree[successor] -= 1
            if indegree[successor] == 0:
                queue.append(successor)
    if len(order) != len(ids):
        raise InfeasibleError("project network contains a cycle")
    return order


def _project_duration(activities: list[dict[str, Any]], durations: dict[str, float]) -> tuple[float, dict[str, float], list[str]]:
    order = _topological_order(activities)
    finish: dict[str, float] = {}
    start: dict[str, float] = {}
    critical_predecessor: dict[str, str | None] = {}
    by_id = {item["id"]: item for item in activities}
    for aid in order:
        predecessors = by_id[aid]["predecessors"]
        if predecessors:
            pred = max(predecessors, key=lambda value: (finish[value], value))
            start[aid] = finish[pred]
            critical_predecessor[aid] = pred
        else:
            start[aid] = 0.0
            critical_predecessor[aid] = None
        finish[aid] = start[aid] + durations[aid]
    end = max(order, key=lambda value: (finish[value], value))
    path: list[str] = []
    cursor: str | None = end
    while cursor is not None:
        path.append(cursor)
        cursor = critical_predecessor[cursor]
    path.reverse()
    return finish[end], start, path


def solve_project_crashing(case: dict[str, Any]) -> dict[str, Any]:
    data = case["data"]
    activities = list(data["activities"])
    option_lists = [item["options"] for item in activities]
    best: dict[str, Any] | None = None
    evaluated = 0
    for options in itertools.product(*option_lists):
        durations = {activity["id"]: float(option["duration"]) for activity, option in zip(activities, options)}
        direct_cost = sum(float(option["cost"]) for option in options)
        duration, starts, critical_path = _project_duration(activities, durations)
        tardiness = max(0.0, duration - float(data["deadline"]))
        objective = direct_cost + tardiness * float(data["tardiness_penalty"])
        evaluated += 1
        candidate = {
            "objective": objective,
            "decision": {"duration_by_activity": durations},
            "direct_cost": direct_cost,
            "project_duration": duration,
            "tardiness": tardiness,
            "start_times": starts,
            "critical_path": critical_path,
        }
        signature = tuple(durations[item["id"]] for item in activities)
        if best is None or (objective, duration, signature) < (best["objective"], best["project_duration"], tuple(best["decision"]["duration_by_activity"][item["id"]] for item in activities)):
            best = candidate
    if best is None:
        raise InfeasibleError("project crashing has no option combination")
    return {"status": "optimal", "solver": "exact-crash-option-enumeration", **best, "evaluated_plans": evaluated, "optimality_gap": 0.0}


def _distance(a: dict[str, Any], b: dict[str, Any]) -> float:
    return math.hypot(float(a["x"]) - float(b["x"]), float(a["y"]) - float(b["y"]))


def _best_route(depot: dict[str, Any], customers: list[dict[str, Any]]) -> tuple[float, list[str]]:
    if not customers:
        return 0.0, []
    best_cost = math.inf
    best_order: tuple[dict[str, Any], ...] | None = None
    for order in itertools.permutations(customers):
        cost = _distance(depot, order[0]) + sum(_distance(order[i], order[i + 1]) for i in range(len(order) - 1)) + _distance(order[-1], depot)
        ids = tuple(item["id"] for item in order)
        if (cost, ids) < (best_cost, tuple(item["id"] for item in best_order) if best_order else tuple("~" for _ in ids)):
            best_cost = cost
            best_order = order
    return best_cost, [item["id"] for item in best_order or ()]


def solve_vehicle_routing(case: dict[str, Any]) -> dict[str, Any]:
    data = case["data"]
    customers = list(data["customers"])
    vehicle_count = int(data["vehicles"])
    capacity = float(data["vehicle_capacity"])
    if vehicle_count > 3 or len(customers) > 9:
        raise ValueError("reference vehicle-routing solver is limited to 3 vehicles and 9 customers")
    best: dict[str, Any] | None = None
    assignments_evaluated = 0
    for allocation in itertools.product(range(vehicle_count), repeat=len(customers)):
        routes: list[list[dict[str, Any]]] = [[] for _ in range(vehicle_count)]
        for customer, vehicle in zip(customers, allocation):
            routes[vehicle].append(customer)
        loads = [sum(float(item["demand"]) for item in route) for route in routes]
        if any(load > capacity + TOL for load in loads):
            continue
        assignments_evaluated += 1
        route_results = [_best_route(data["depot"], route) for route in routes]
        distance = sum(result[0] for result in route_results)
        used = sum(1 for route in routes if route)
        objective = distance * float(data.get("distance_cost", 1.0)) + used * float(data.get("vehicle_fixed_cost", 0.0))
        ordered_routes = [result[1] for result in route_results]
        signature = tuple(tuple(route) for route in ordered_routes)
        candidate = {"objective": objective, "decision": {"routes": ordered_routes}, "total_distance": distance, "loads": loads, "vehicles_used": used}
        if best is None or (objective, used, signature) < (best["objective"], best["vehicles_used"], tuple(tuple(route) for route in best["decision"]["routes"])):
            best = candidate
    if best is None:
        raise InfeasibleError("vehicle routing cannot serve all customers within capacity")
    return {"status": "optimal", "solver": "exact-allocation-and-route-enumeration", **best, "feasible_allocations": assignments_evaluated, "optimality_gap": 0.0}


def solve_robust_choice(case: dict[str, Any]) -> dict[str, Any]:
    data = case["data"]
    scenarios = data["scenarios"]
    decisions = data["decisions"]
    scenario_ids = [item["id"] for item in scenarios]
    probabilities = {item["id"]: float(item["probability"]) for item in scenarios}
    best_by_scenario = {sid: min(float(decision["scenario_costs"][sid]) for decision in decisions) for sid in scenario_ids}
    candidates: list[dict[str, Any]] = []
    for decision in decisions:
        costs = {sid: float(decision["scenario_costs"][sid]) for sid in scenario_ids}
        expected = sum(probabilities[sid] * costs[sid] for sid in scenario_ids)
        worst = max(costs.values())
        regrets = {sid: costs[sid] - best_by_scenario[sid] for sid in scenario_ids}
        max_regret = max(regrets.values())
        criterion = data["criterion"]
        if criterion == "expected_cost":
            score = expected
        elif criterion == "worst_case":
            score = worst
        elif criterion == "minimax_regret":
            score = max_regret
        else:
            weights = data.get("weights", {"expected": 1.0, "worst": 0.0, "regret": 0.0})
            score = float(weights.get("expected", 0.0)) * expected + float(weights.get("worst", 0.0)) * worst + float(weights.get("regret", 0.0)) * max_regret
        candidates.append({"id": decision["id"], "score": score, "expected_cost": expected, "worst_case_cost": worst, "max_regret": max_regret, "scenario_costs": costs, "regrets": regrets})
    candidates.sort(key=lambda item: (item["score"], item["expected_cost"], item["id"]))
    best = candidates[0]
    return {
        "status": "optimal",
        "solver": "exact-robust-choice-enumeration",
        "objective": best["score"],
        "decision": {"selected": best["id"]},
        "expected_cost": best["expected_cost"],
        "worst_case_cost": best["worst_case_cost"],
        "max_regret": best["max_regret"],
        "scenario_costs": best["scenario_costs"],
        "regrets": best["regrets"],
        "candidate_metrics": candidates,
        "optimality_gap": 0.0,
    }


def solve_capital_budgeting(case: dict[str, Any]) -> dict[str, Any]:
    data = case["data"]
    projects = list(data["projects"])
    ids = [item["id"] for item in projects]
    by_id = {item["id"]: item for item in projects}
    best: dict[str, Any] | None = None
    feasible_count = 0
    for mask in range(1 << len(projects)):
        selected = {ids[index] for index in range(len(ids)) if mask & (1 << index)}
        if any(not set(by_id[pid].get("requires", [])).issubset(selected) for pid in selected):
            continue
        if any(sum(1 for pid in group if pid in selected) > 1 for group in data.get("exclusive_groups", [])):
            continue
        cost = sum(float(by_id[pid]["cost"]) for pid in selected)
        risk = sum(float(by_id[pid]["risk"]) for pid in selected)
        if cost > float(data["budget"]) + TOL or risk > float(data["risk_budget"]) + TOL:
            continue
        feasible_count += 1
        value = sum(float(by_id[pid]["value"]) for pid in selected)
        strategic = sum(float(by_id[pid].get("strategic_score", 0.0)) for pid in selected)
        candidate = {"objective": value, "decision": {"selected_projects": sorted(selected)}, "total_cost": cost, "total_risk": risk, "strategic_score": strategic, "budget_slack": float(data["budget"]) - cost, "risk_slack": float(data["risk_budget"]) - risk}
        signature = tuple(sorted(selected))
        if best is None or (value, strategic, -cost, signature) > (best["objective"], best["strategic_score"], -best["total_cost"], tuple(best["decision"]["selected_projects"])):
            best = candidate
    if best is None:
        raise InfeasibleError("capital budgeting has no feasible portfolio")
    return {"status": "optimal", "solver": "exact-binary-portfolio-enumeration", **best, "feasible_portfolios": feasible_count, "optimality_gap": 0.0}


SOLVERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "product_mix": solve_product_mix,
    "transportation": solve_transportation,
    "assignment": solve_assignment,
    "facility_location": solve_facility_location,
    "workforce_schedule": solve_workforce_schedule,
    "newsvendor": solve_newsvendor,
    "project_crashing": solve_project_crashing,
    "vehicle_routing": solve_vehicle_routing,
    "robust_choice": solve_robust_choice,
    "capital_budgeting": solve_capital_budgeting,
}


def solve_case(case: dict[str, Any]) -> dict[str, Any]:
    try:
        solver = SOLVERS[case["case_type"]]
    except KeyError as exc:
        raise ValueError(f"unsupported case type: {case.get('case_type')}") from exc
    return solver(case)


def apply_patch(case: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    updated = copy.deepcopy(case)
    for dotted_path, value in patch.items():
        parts = dotted_path.split(".")
        target: Any = updated
        for part in parts[:-1]:
            if isinstance(target, list):
                target = target[int(part)]
            else:
                if part not in target:
                    raise KeyError(f"patch path not found: {dotted_path}")
                target = target[part]
        final = parts[-1]
        if isinstance(target, list):
            target[int(final)] = value
        else:
            if final not in target:
                raise KeyError(f"patch path not found: {dotted_path}")
            target[final] = value
    return updated

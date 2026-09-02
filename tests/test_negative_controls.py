from __future__ import annotations

import copy
import unittest

from opcase.algorithms import InfeasibleError, solve_case
from opcase.audit import audit_solution
from opcase.decision import build_decision
from opcase.pipeline import run_case
from opcase.sensitivity import run_sensitivity
from opcase.validation import validate_case
from tests.helpers import FIXED_TIME, NEGATIVE, load, temporary_directory


class NegativeControlTests(unittest.TestCase):
    def test_unbalanced_transport_rejected(self):
        case = load(NEGATIVE / "infeasible-transport.json")
        self.assertTrue(any("supply" in item for item in validate_case(case)))

    def test_cyclic_project_solver_rejects(self):
        case = load(NEGATIVE / "cyclic-project.json")
        self.assertEqual(validate_case(case), [])
        with self.assertRaises(InfeasibleError):
            solve_case(case)

    def test_service_gate_produces_hold(self):
        case = load(NEGATIVE / "service-hold.json")
        solution = solve_case(case)
        audit = audit_solution(case, solution)
        sensitivity = run_sensitivity(case, solution)
        decision = build_decision(case, solution, audit, sensitivity)
        self.assertEqual(decision["status"], "hold")
        self.assertIn("minimum_fill_rate_not_met", decision["hard_failures"])

    def test_missing_owner_produces_hold(self):
        case = load(NEGATIVE / "service-hold.json")
        case["policy"].pop("implementation_owner")
        solution = solve_case(case)
        decision = build_decision(case, solution, audit_solution(case, solution), run_sensitivity(case, solution))
        self.assertEqual(decision["status"], "hold")
        self.assertIn("implementation_owner_missing", decision["hard_failures"])

    def test_objective_tamper_fails_audit(self):
        case = load(NEGATIVE / "service-hold.json")
        solution = solve_case(case)
        solution["objective"] += 100
        audit = audit_solution(case, solution)
        self.assertFalse(audit["passed"])
        self.assertFalse(audit["gates"]["objective_recomputed"])

    def test_infeasible_baseline_fails_gate(self):
        case = load(NEGATIVE / "service-hold.json")
        case["baseline_decision"] = {"order_quantity": -1}
        solution = solve_case(case)
        audit = audit_solution(case, solution)
        self.assertFalse(audit["gates"]["baseline_feasible"])

    def test_solve_invalid_case_returns_validation_error(self):
        with temporary_directory() as temp:
            with self.assertRaises(ValueError):
                run_case(NEGATIVE / "infeasible-transport.json", temp / "run", fixed_time=FIXED_TIME)

    def test_stress_invalid_path_is_fail_closed(self):
        case = load(NEGATIVE / "service-hold.json")
        case["stress_tests"] = [{"name": "bad", "patch": {"data.missing": 1}}]
        solution = solve_case(case)
        sensitivity = run_sensitivity(case, solution)
        self.assertFalse(sensitivity["all_stress_tests_feasible"])
        self.assertEqual(sensitivity["results"][0]["status"], "infeasible_or_invalid")

    def test_exact_solver_gap_cannot_be_faked(self):
        case = load(NEGATIVE / "service-hold.json")
        solution = solve_case(case)
        solution["optimality_gap"] = 1
        audit = audit_solution(case, solution)
        self.assertFalse(audit["gates"]["optimality_certificate_exact"])

    def test_nonoptimal_status_fails(self):
        case = load(NEGATIVE / "service-hold.json")
        solution = solve_case(case)
        solution["status"] = "heuristic"
        self.assertFalse(audit_solution(case, solution)["gates"]["solution_status_optimal"])

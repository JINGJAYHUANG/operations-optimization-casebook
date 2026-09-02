from __future__ import annotations

import copy
import unittest

from opcase.algorithms import InfeasibleError, apply_patch, solve_case
from opcase.audit import audit_solution, evaluate_decision
from tests.helpers import cases


ALL_CASES = cases()


class AlgorithmTests(unittest.TestCase):
    def test_patch_does_not_mutate_original(self):
        case = copy.deepcopy(ALL_CASES[0])
        original = copy.deepcopy(case)
        patched = apply_patch(case, {"data.capacities.machine": 99})
        self.assertEqual(case, original)
        self.assertEqual(patched["data"]["capacities"]["machine"], 99)

    def test_unknown_patch_path_rejected(self):
        with self.assertRaises(KeyError):
            apply_patch(ALL_CASES[0], {"data.unknown": 1})

    def test_unknown_case_type_rejected(self):
        case = copy.deepcopy(ALL_CASES[0])
        case["case_type"] = "unknown"
        with self.assertRaises(ValueError):
            solve_case(case)


# Per-case algorithm contracts.
def _make_solver_test(index: int):
    def test(self):
        solution = solve_case(copy.deepcopy(ALL_CASES[index]))
        self.assertEqual(solution["status"], "optimal")
        self.assertEqual(solution["optimality_gap"], 0.0)
        self.assertIsInstance(solution["decision"], dict)
    return test


def _make_audit_test(index: int):
    def test(self):
        case = copy.deepcopy(ALL_CASES[index])
        solution = solve_case(case)
        audit = audit_solution(case, solution)
        self.assertTrue(audit["passed"], audit)
        self.assertTrue(audit["evaluation"]["feasible"])
    return test


def _make_objective_recompute_test(index: int):
    def test(self):
        case = copy.deepcopy(ALL_CASES[index])
        solution = solve_case(case)
        evaluated = evaluate_decision(case, solution["decision"])
        self.assertAlmostEqual(float(solution["objective"]), float(evaluated["objective"]), places=7)
    return test


def _make_baseline_test(index: int):
    def test(self):
        case = copy.deepcopy(ALL_CASES[index])
        evaluated = evaluate_decision(case, case["baseline_decision"])
        self.assertTrue(evaluated["feasible"], evaluated)
    return test


def _make_baseline_dominance_test(index: int):
    def test(self):
        case = copy.deepcopy(ALL_CASES[index])
        solution = solve_case(case)
        baseline = evaluate_decision(case, case["baseline_decision"])
        if case["objective_sense"] == "min":
            self.assertLessEqual(solution["objective"], baseline["objective"] + 1e-8)
        else:
            self.assertGreaterEqual(solution["objective"] + 1e-8, baseline["objective"])
    return test


def _make_decision_hash_stability_test(index: int):
    def test(self):
        first = solve_case(copy.deepcopy(ALL_CASES[index]))
        second = solve_case(copy.deepcopy(ALL_CASES[index]))
        self.assertEqual(first, second)
    return test


for _index, _case in enumerate(ALL_CASES):
    suffix = f"{_index:02d}_{_case['case_type']}"
    setattr(AlgorithmTests, f"test_solver_{suffix}", _make_solver_test(_index))
    setattr(AlgorithmTests, f"test_audit_{suffix}", _make_audit_test(_index))
    setattr(AlgorithmTests, f"test_recompute_{suffix}", _make_objective_recompute_test(_index))
    setattr(AlgorithmTests, f"test_baseline_{suffix}", _make_baseline_test(_index))
    setattr(AlgorithmTests, f"test_dominance_{suffix}", _make_baseline_dominance_test(_index))
    setattr(AlgorithmTests, f"test_deterministic_{suffix}", _make_decision_hash_stability_test(_index))

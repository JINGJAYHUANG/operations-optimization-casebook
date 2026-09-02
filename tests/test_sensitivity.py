from __future__ import annotations

import copy
import unittest

from opcase.algorithms import apply_patch, solve_case
from opcase.audit import audit_solution
from opcase.decision import build_decision
from opcase.sensitivity import run_sensitivity
from opcase.validation import validate_case
from tests.helpers import cases


ALL_CASES = cases()
STRESSES = [(case_index, stress_index) for case_index, case in enumerate(ALL_CASES) for stress_index, _ in enumerate(case["stress_tests"])]


class SensitivityTests(unittest.TestCase):
    def test_reference_cases_have_three_stresses(self):
        self.assertTrue(all(len(case["stress_tests"]) == 3 for case in ALL_CASES))

    def test_sensitivity_summary_shape(self):
        case = copy.deepcopy(ALL_CASES[0])
        solution = solve_case(case)
        result = run_sensitivity(case, solution)
        self.assertEqual(result["stress_test_count"], 3)
        self.assertIn("decision_stability_ratio", result)

    def test_decision_status_vocabulary(self):
        for case in ALL_CASES:
            case = copy.deepcopy(case)
            solution = solve_case(case)
            audit = audit_solution(case, solution)
            sensitivity = run_sensitivity(case, solution)
            decision = build_decision(case, solution, audit, sensitivity)
            self.assertIn(decision["status"], {"recommended", "conditional", "hold"})

    def test_owner_always_present(self):
        for case in ALL_CASES:
            self.assertTrue(case["policy"]["implementation_owner"])


# Each stress patch must preserve input validity and produce an audited solution.
def _make_stress_valid_test(case_index: int, stress_index: int):
    def test(self):
        base = copy.deepcopy(ALL_CASES[case_index])
        stress = base["stress_tests"][stress_index]
        stressed = apply_patch(base, stress["patch"])
        self.assertEqual(validate_case(stressed), [])
    return test


def _make_stress_solve_test(case_index: int, stress_index: int):
    def test(self):
        base = copy.deepcopy(ALL_CASES[case_index])
        stressed = apply_patch(base, base["stress_tests"][stress_index]["patch"])
        solution = solve_case(stressed)
        self.assertEqual(solution["status"], "optimal")
    return test


def _make_stress_audit_test(case_index: int, stress_index: int):
    def test(self):
        base = copy.deepcopy(ALL_CASES[case_index])
        stressed = apply_patch(base, base["stress_tests"][stress_index]["patch"])
        solution = solve_case(stressed)
        self.assertTrue(audit_solution(stressed, solution)["core_passed"])
    return test


def _make_stress_repeat_test(case_index: int, stress_index: int):
    def test(self):
        base = copy.deepcopy(ALL_CASES[case_index])
        stressed = apply_patch(base, base["stress_tests"][stress_index]["patch"])
        self.assertEqual(solve_case(copy.deepcopy(stressed)), solve_case(copy.deepcopy(stressed)))
    return test


for _case_index, _stress_index in STRESSES:
    name = ALL_CASES[_case_index]["stress_tests"][_stress_index]["name"].replace("-", "_")
    suffix = f"{_case_index:02d}_{_stress_index:02d}_{name}"
    setattr(SensitivityTests, f"test_stress_valid_{suffix}", _make_stress_valid_test(_case_index, _stress_index))
    setattr(SensitivityTests, f"test_stress_solves_{suffix}", _make_stress_solve_test(_case_index, _stress_index))
    setattr(SensitivityTests, f"test_stress_audits_{suffix}", _make_stress_audit_test(_case_index, _stress_index))
    setattr(SensitivityTests, f"test_stress_repeats_{suffix}", _make_stress_repeat_test(_case_index, _stress_index))

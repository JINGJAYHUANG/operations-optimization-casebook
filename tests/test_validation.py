from __future__ import annotations

import copy
import unittest

from opcase.validation import CASE_TYPES, validate_case, validate_suite
from tests.helpers import SUITE, cases, load


ALL_CASES = cases()


class ValidationTests(unittest.TestCase):
    def test_suite_valid(self):
        self.assertEqual(validate_suite(load(SUITE)), [])

    def test_suite_requires_version(self):
        value = load(SUITE)
        value["schema_version"] = "2.0"
        self.assertTrue(validate_suite(value))

    def test_suite_requires_cases(self):
        value = load(SUITE)
        value["cases"] = []
        self.assertTrue(validate_suite(value))

    def test_suite_rejects_duplicate_paths(self):
        value = load(SUITE)
        value["cases"].append(value["cases"][0])
        self.assertTrue(any("duplicate" in item for item in validate_suite(value)))

    def test_all_types_present(self):
        self.assertEqual({item["case_type"] for item in ALL_CASES}, CASE_TYPES)

    def test_non_object_rejected(self):
        self.assertTrue(validate_case([]))

    def test_invalid_type_rejected(self):
        value = copy.deepcopy(ALL_CASES[0])
        value["case_type"] = "magic"
        self.assertTrue(validate_case(value))

    def test_invalid_objective_sense_rejected(self):
        value = copy.deepcopy(ALL_CASES[0])
        value["objective_sense"] = "maybe"
        self.assertTrue(validate_case(value))

    def test_missing_title_rejected(self):
        value = copy.deepcopy(ALL_CASES[0])
        value["title"] = ""
        self.assertTrue(validate_case(value))

    def test_stress_patch_requires_mapping(self):
        value = copy.deepcopy(ALL_CASES[0])
        value["stress_tests"][0]["patch"] = []
        self.assertTrue(validate_case(value))

    def test_duplicate_stress_names_rejected(self):
        value = copy.deepcopy(ALL_CASES[0])
        value["stress_tests"].append(copy.deepcopy(value["stress_tests"][0]))
        self.assertTrue(validate_case(value))


# Each published case is independently required to validate.
def _make_valid_case_test(index: int):
    def test(self):
        self.assertEqual(validate_case(copy.deepcopy(ALL_CASES[index])), [])
    return test


# Required top-level fields cannot be removed from any case.
def _make_required_field_test(index: int, field: str):
    def test(self):
        value = copy.deepcopy(ALL_CASES[index])
        value.pop(field, None)
        self.assertTrue(validate_case(value))
    return test


for _index, _case in enumerate(ALL_CASES):
    setattr(ValidationTests, f"test_valid_case_{_index:02d}_{_case['case_type']}", _make_valid_case_test(_index))
    for _field in ("schema_version", "case_id", "case_type", "title", "decision_context", "objective_sense", "data"):
        setattr(ValidationTests, f"test_case_{_index:02d}_requires_{_field}", _make_required_field_test(_index, _field))

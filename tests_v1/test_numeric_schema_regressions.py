"""Positive representation controls and strict discrete-output contracts."""
import copy
import unittest

from nrb_v1.grading import EXACT_INTEGER_PATHS, compare_value, grade
from nrb_v1.registry import module


class NumericSchemaRegressions(unittest.TestCase):
    def test_physical_fields_accept_equal_integer_and_float_representations(self):
        examples = {
            "C03": {"temperature_K": [2, 7]},
            "C05": {"observations": [{"time_s": 0, "state": [1, 0]}],
                    "accepted_steps": 2, "rejected_steps": 0},
            "C10": {"final": {"n": 3, "step": 0, "D": 0, "A": [1, 0, 2]},
                    "checkpoint": {"n": 3, "step": 0, "k": 0}},
        }
        def float_physical(value, path, exact):
            if isinstance(value, dict):
                return {k: float_physical(v, path + "." + k, exact) for k, v in value.items()}
            if isinstance(value, list):
                return [float_physical(v, path + "[]", exact) for v in value]
            return float(value) if type(value) is int and path not in exact else value
        for task_id, expected in examples.items():
            with self.subTest(task=task_id):
                actual = float_physical(expected, "result", EXACT_INTEGER_PATHS[task_id])
                self.assertTrue(compare_value(actual, expected,
                    exact_integer_paths=EXACT_INTEGER_PATHS[task_id])[0])

    def test_discrete_fields_still_require_exact_integer_types_and_values(self):
        fixtures = [
            ("C01", {"n_usable": 1, "samples": [{"n": 1}]}, ("n_usable",)),
            ("C01", {"samples": [{"n": 1}]}, ("samples", 0, "n")),
            ("C02", {"strata": [{"n_groups": 1}]}, ("strata", 0, "n_groups")),
            ("C05", {"accepted_steps": 1}, ("accepted_steps",)),
            ("C10", {"checkpoint": {"step": 1}}, ("checkpoint", "step")),
            ("C10", {"bootstrap": {"rng_state": 1}}, ("bootstrap", "rng_state")),
        ]
        for task_id, expected, keys in fixtures:
            for wrong in (1.0, True, 2, 10**400):
                with self.subTest(task=task_id, field=keys, wrong=type(wrong).__name__):
                    actual = copy.deepcopy(expected)
                    target = actual
                    for key in keys[:-1]: target = target[key]
                    target[keys[-1]] = wrong
                    self.assertFalse(compare_value(actual, expected,
                        exact_integer_paths=EXACT_INTEGER_PATHS[task_id])[0])

    def test_real_fields_reject_bool_nonfinite_and_out_of_tolerance(self):
        for wrong in (True, float("nan"), float("inf"), 10**400, 2.01):
            with self.subTest(wrong=type(wrong).__name__):
                self.assertFalse(compare_value({"temperature_K": [wrong]}, {"temperature_K": [2]},
                    exact_integer_paths=EXACT_INTEGER_PATHS["C03"])[0])

    def test_float_state_c03_and_c05_keep_all_current_automatic_points(self):
        wrappers = {
            "C03": "\n_original=solve\ndef solve(problem):\n value=_original(problem)\n value['temperature_K']=[float(v) for v in value['temperature_K']]\n return value\n",
            "C05": "\n_original=solve\ndef solve(problem):\n value=_original(problem)\n for row in value['observations']: row['state']=[float(v) for v in row['state']]\n return value\n",
        }
        for task_id, wrapper in wrappers.items():
            with self.subTest(task=task_id):
                submission = module(task_id).reference_submission()
                submission["artifacts"]["solution.py"] += wrapper
                report = grade(task_id, submission, backend="trusted", timeout=20)
                self.assertEqual(report["auto_points"], 70, report["checks"])
                self.assertEqual(report["completion_status"], "pending_review")


if __name__ == "__main__": unittest.main()

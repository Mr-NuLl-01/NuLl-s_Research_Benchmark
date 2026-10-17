"""Legal public display rounding must not fail field-specific numeric checks."""
from __future__ import annotations

import copy
import math
import unittest

from nrb.tasks import t01, t02, t03


def rounded(value, digits=9):
    if isinstance(value, dict):
        return {key: rounded(item, digits) for key, item in value.items()}
    if isinstance(value, list):
        return [rounded(item, digits) for item in value]
    if type(value) is float:
        return float(format(value, f".{digits}g"))
    return value


class PrecisionContractTests(unittest.TestCase):
    def test_nine_significant_figures_pass_all_answer_fields(self):
        for module in (t01, t02, t03):
            for seed in (0, 1, 17, 37, 101, 255, 2026):
                with self.subTest(module=module.__name__, seed=seed):
                    case = module.build(seed)
                    submission = module.reference(case)
                    submission["answer"] = rounded(submission["answer"])
                    checks = module.grade(case, submission)
                    self.assertEqual(sum(row["points"] for row in checks), 70)
                    self.assertTrue(all(row["passed"] for row in checks),
                                    [row for row in checks if not row["passed"]])
                    self.assertIn("至少保留 9 位有效数字", case["prompt"])

    def test_analytic_tau_example_discriminates_old_six_digit_contract(self):
        expected = 21/1.7
        self.assertFalse(t02._near(float(format(expected, ".6g")), expected))
        self.assertTrue(t02._near(float(format(expected, ".9g")), expected))
        case = t02.build(0)
        case["expected"]["answer"]["baseline"]["tau_s"] = expected
        submission = t02.reference(case)
        submission["answer"]["baseline"]["tau_s"] = float(format(expected, ".9g"))
        checks = {row["id"]: row for row in t02.grade(case, submission)}
        self.assertTrue(checks["baseline_tau_s"]["passed"])
        submission["answer"]["baseline"]["tau_s"] = float(format(expected, ".6g"))
        self.assertFalse(next(row["passed"] for row in t02.grade(case, submission)
                              if row["id"] == "baseline_tau_s"))

    def test_nine_digit_rounding_across_orders_sign_and_zero(self):
        values = (0.0, 1e-14, -1e-14, 1.234567891e-4, -1.234567891e-4,
                  0.9999999996, -0.9999999996, 123456789.4, -123456789.4)
        for module in (t01, t02, t03):
            for expected in values:
                with self.subTest(module=module.__name__, expected=expected):
                    self.assertTrue(module._near(float(format(expected, ".9g")), expected))
            # Keep the existing relative/absolute tolerance behavior: changing
            # the output contract is not a blanket acceptance-range expansion.
            self.assertFalse(module._near(0.0, 1e-4))
            for value in (True, None, "1", math.inf, math.nan, 10**400):
                self.assertFalse(module._near(value, 1.0))


if __name__ == "__main__":
    unittest.main()

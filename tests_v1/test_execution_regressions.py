"""Execution-phase regressions using real trusted candidate subprocesses."""
from __future__ import annotations

import unittest

from nrb_v1.execution import execute
from nrb_v1.grading import grade
from nrb_v1.registry import module


class PythonExecutionPhases(unittest.TestCase):
    def setUp(self):
        self.task = module("C01")
        self.cases = self.task.cases(17)

    def submission(self, source):
        submission = self.task.reference_submission(17)
        submission["artifacts"]["solution.py"] = source
        return submission

    def assert_initialization_failure(self, submission, exception_type, detail):
        result = execute(self.task, submission, self.cases, backend="trusted", timeout=5)
        self.assertEqual(result["status"], "executed")
        self.assertEqual(len(result["records"]), len(self.cases))
        for record in result["records"]:
            self.assertFalse(record["ok"])
            self.assertEqual(record["error"], "WorkerInitializationError")
            self.assertTrue(record["detail"].startswith(exception_type + ": "))
            self.assertIn(detail, record["detail"])
        report = grade("C01", submission, 17, backend="trusted", timeout=5)
        self.assertEqual(report["auto_points"], 0)
        self.assertEqual(report["auto_scored_max"], 70)
        self.assertEqual(report["completion_status"], "failed")
        self.assertTrue(all(check["passed"] is False for check in report["checks"]))

    def test_top_level_value_error_earns_no_invalid_input_credit(self):
        submission = self.submission("raise ValueError('top-level failure')\n")
        self.assert_initialization_failure(submission, "ValueError", "top-level failure")

    def test_imported_module_value_error_is_an_initialization_failure(self):
        submission = self.submission("import helper\ndef solve(problem): return {}\n")
        submission["artifacts"]["helper.py"] = "raise ValueError('helper import failure')\n"
        self.assert_initialization_failure(submission, "ValueError", "helper import failure")

    def test_missing_solve_earns_no_invalid_input_credit(self):
        submission = self.submission("answer = 42\n")
        self.assert_initialization_failure(submission, "TypeError", "callable solve")

    def test_noncallable_solve_is_an_initialization_failure(self):
        submission = self.submission("solve = 42\n")
        self.assert_initialization_failure(submission, "TypeError", "callable solve")

    def test_solve_value_error_keeps_intended_invalid_input_credit(self):
        submission = self.submission("def solve(problem): raise ValueError('case failure')\n")
        result = execute(self.task, submission, self.cases, backend="trusted", timeout=5)
        self.assertTrue(all(record == {"ok": False, "error": "ValueError", "detail": "case failure"}
                            for record in result["records"]))
        report = grade("C01", submission, 17, backend="trusted", timeout=5)
        self.assertEqual(report["auto_points"], 10)
        self.assertEqual({check["id"] for check in report["checks"] if check["passed"]},
                         {case["id"] for case in self.cases if case.get("error") == "ValueError"})

    def test_reference_keeps_full_automatic_score(self):
        report = grade("C01", self.task.reference_submission(17), 17,
                       backend="trusted", timeout=5)
        self.assertEqual(report["auto_points"], 70)
        self.assertEqual(report["completion_status"], "pending_review")

    def test_input_mutation_still_overrides_returns_and_solve_exceptions(self):
        for last_line in ("return {}", "raise ValueError('case failure')"):
            with self.subTest(last_line=last_line):
                submission = self.submission("def solve(problem):\n"
                                             "    problem['modified'] = True\n"
                                             "    " + last_line + "\n")
                result = execute(self.task, submission, self.cases, backend="trusted", timeout=5)
                self.assertTrue(all(not record["ok"] and record["error"] == "InputMutation"
                                    for record in result["records"]))
                report = grade("C01", submission, 17, backend="trusted", timeout=5)
                self.assertEqual(report["auto_points"], 0)

    def test_non_json_output_still_cannot_earn_exception_credit(self):
        submission = self.submission("def solve(problem): return float('nan')\n")
        result = execute(self.task, submission, self.cases, backend="trusted", timeout=5)
        self.assertTrue(all(not record["ok"] and record["error"] == "NonJSONOutput"
                            for record in result["records"]))
        report = grade("C01", submission, 17, backend="trusted", timeout=5)
        self.assertEqual(report["auto_points"], 0)


if __name__ == "__main__":
    unittest.main()

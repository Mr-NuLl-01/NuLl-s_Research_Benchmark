"""NRB03 actual-search execution and bound-review integration contracts.

All sources and reviews here are synthetic repository-owned test fixtures.
Trusted execution tests the fixture code; it never stands in for successful
Docker/container isolation or a real scientific/human review. No passing
isolated receipt is invented or relabeled from a trusted run.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nrb import cli
from nrb.core import (attach_review, canonical_json, fingerprint, get_case,
                      grade_submission, reference_submission, review_ledger,
                      validate_final_report)
from nrb.provenance import identity_from


FIXTURE = "SYNTHETIC CONTRACT FIXTURE; not a scientific or isolation review"
WRONG_SOLVER = "def solve(problem):\n    return {}\n"


def ledger_fixture(case, submission, report, *, reproduced="unassessed"):
    ledger = review_ledger(case, submission, report=report)
    ledger.update(reviewer_id="search-execution-contract-fixture", reviewer_type="human")
    for entry in ledger["criteria"]:
        entry.update(score=10, evidence=FIXTURE + ": supplied fixture artifacts",
                     rationale=FIXTURE + ": artificial score only exercises report aggregation")
    for entry in ledger["essential_review"]:
        outcome = reproduced if entry["id"] == "search_reproduced" else "unassessed"
        entry.update(outcome=outcome,
                     evidence="" if outcome == "unassessed" else FIXTURE + ": bound solve.py execution receipt",
                     rationale="" if outcome == "unassessed" else FIXTURE + ": explicit fixture decision")
    return ledger


def include_receipt(directory, ledger, receipt):
    data = (canonical_json(receipt)+"\n").encode("utf-8")
    path = Path(directory) / "solve_execution.json"
    path.write_bytes(data)
    ledger["evidence_artifacts"]["solve_reproduction"] = {
        "file": path.name, "sha256": hashlib.sha256(data).hexdigest()}


class SearchExecutionReviewContracts(unittest.TestCase):
    def setUp(self):
        self.case = get_case("NRB03", 17)
        self.reference = reference_submission(self.case)
        self.wrong = copy.deepcopy(self.reference)
        self.wrong["artifacts"]["solve.py"] = WRONG_SOLVER

    def test_correct_artifact_is_actually_run_and_its_receipt_is_bound(self):
        report = grade_submission(self.case, self.reference, execution="trusted")
        self.assertEqual(report["auto_points"], 70)
        self.assertEqual(report["completion_status"], "pending_review")
        self.assertEqual(len(report["mandatory_execution"]), 1)
        receipt = report["mandatory_execution"][0]
        self.assertEqual(receipt["id"], "solve_reproduction")
        self.assertEqual(receipt["status"], "pass", receipt)
        self.assertIs(receipt["passed"], True)
        self.assertEqual(receipt["execution"], "trusted")
        self.assertEqual(receipt["execution_status"], "ok")
        self.assertEqual(receipt["task_id"], self.case["id"])
        self.assertEqual(receipt["case_hash"], self.case["case_hash"])
        self.assertEqual(receipt["submission_hash"], fingerprint(self.reference))
        self.assertEqual(receipt["source_hash"], hashlib.sha256(self.reference["artifacts"]["solve.py"].encode()).hexdigest())
        self.assertEqual(receipt["evaluator_identity"], identity_from(report))
        self.assertTrue(all(item["passed"] is True for item in receipt["checks"]))
        self.assertTrue(validate_final_report(report))

    def test_attaching_a_wrong_solver_file_cannot_complete_an_otherwise_correct_answer(self):
        report = grade_submission(self.case, self.wrong, execution="trusted")
        self.assertEqual(report["auto_points"], 70)
        self.assertEqual(report["coverage"], 1)
        self.assertTrue(report["delivery_complete"])
        self.assertEqual(report["missing_artifacts"], [])
        receipt = report["mandatory_execution"][0]
        self.assertEqual(receipt["execution_status"], "ok")
        self.assertEqual(receipt["status"], "fail")
        self.assertIs(receipt["passed"], False)
        self.assertEqual(report["completion_status"], "failed")
        self.assertIs(report["quality_qualified"], False)
        self.assertIn("execution:solve_reproduction", report["critical_failures"])
        self.assertIn("essential:search_reproduced", report["pending_items"])
        self.assertIn("essential:optimality_explanation", report["pending_items"])
        self.assertTrue(validate_final_report(report))

    def test_backend_none_is_infrastructure_unscored_with_pending_execution(self):
        report = grade_submission(self.case, self.reference, execution="none")
        self.assertEqual(report["auto_points"], 70)
        self.assertEqual(report["coverage"], 1)
        self.assertEqual(report["auto_percent"], 100)
        receipt = report["mandatory_execution"][0]
        self.assertEqual(receipt["execution_status"], "unavailable")
        self.assertEqual(receipt["status"], "unassessed")
        self.assertIsNone(receipt["passed"])
        self.assertIsNone(receipt["result_hash"])
        self.assertEqual(report["completion_status"], "infrastructure_unscored")
        self.assertIsNone(report["quality_qualified"])
        self.assertIn("execution:solve_reproduction", report["pending_items"])
        self.assertIn("essential:search_reproduced", report["pending_items"])
        self.assertEqual(report["critical_failures"], [])
        self.assertTrue(validate_final_report(report))

    def test_failure_and_unassessed_essentials_survive_attaching_quality_scores(self):
        report = grade_submission(self.case, self.wrong, execution="trusted")
        ledger = ledger_fixture(self.case, self.wrong, report)
        with tempfile.TemporaryDirectory() as directory:
            include_receipt(directory, ledger, report["mandatory_execution"][0])
            attached = attach_review(self.case, report, ledger, submission=self.wrong, evidence_dir=directory)
        self.assertEqual(attached["auto_points"], 70)
        self.assertEqual(attached["review_points"], 30)
        self.assertEqual(attached["total"], 100)
        self.assertEqual(attached["completion_status"], "failed")
        self.assertIs(attached["quality_qualified"], False)
        self.assertIn("execution:solve_reproduction", attached["critical_failures"])
        self.assertIn("essential:search_reproduced", attached["pending_items"])
        self.assertIn("essential:optimality_explanation", attached["pending_items"])
        self.assertEqual({item["outcome"] for item in attached["essential_review"]}, {"unassessed"})
        self.assertFalse(attached["review_pending"])
        self.assertTrue(validate_final_report(attached))

    def test_a_failed_receipt_cannot_be_promoted_to_an_essential_pass(self):
        report = grade_submission(self.case, self.wrong, execution="trusted")
        ledger = ledger_fixture(self.case, self.wrong, report, reproduced="pass")
        with tempfile.TemporaryDirectory() as directory:
            include_receipt(directory, ledger, report["mandatory_execution"][0])
            with self.assertRaises(ValueError):
                attach_review(self.case, report, ledger, submission=self.wrong, evidence_dir=directory)

    def test_trusted_success_does_not_fabricate_a_successful_isolated_review(self):
        report = grade_submission(self.case, self.reference, execution="trusted")
        receipt = report["mandatory_execution"][0]
        self.assertIs(receipt["passed"], True)
        self.assertEqual(receipt["execution"], "trusted")
        ledger = ledger_fixture(self.case, self.reference, report, reproduced="pass")
        with tempfile.TemporaryDirectory() as directory:
            include_receipt(directory, ledger, receipt)
            with self.assertRaises(ValueError):
                attach_review(self.case, report, ledger, submission=self.reference, evidence_dir=directory)

    def test_report_receipt_tampering_is_rejected_by_its_automatic_seal(self):
        report = grade_submission(self.case, self.wrong, execution="trusted")
        ledger = ledger_fixture(self.case, self.wrong, report)
        for key, value in (("source_hash", "0"*64), ("result_hash", "0"*64),
                           ("execution", "none"), ("passed", None)):
            with self.subTest(field=key):
                changed = copy.deepcopy(report)
                changed["mandatory_execution"][0][key] = value
                with self.assertRaises(ValueError):
                    attach_review(self.case, changed, ledger, submission=self.wrong)

    def test_external_receipt_identity_cannot_be_rebound_by_updating_file_hash(self):
        report = grade_submission(self.case, self.wrong, execution="trusted")
        for key, value in (("task_id", "NRB02"), ("case_hash", "0"*64),
                           ("submission_hash", "0"*64), ("source_hash", "0"*64),
                           ("input_hash", "0"*64), ("evaluator_identity", {})):
            with self.subTest(field=key), tempfile.TemporaryDirectory() as directory:
                receipt = copy.deepcopy(report["mandatory_execution"][0])
                receipt[key] = value
                ledger = ledger_fixture(self.case, self.wrong, report)
                include_receipt(directory, ledger, receipt)
                with self.assertRaises(ValueError):
                    attach_review(self.case, report, ledger, submission=self.wrong, evidence_dir=directory)

    def test_external_execution_result_must_match_the_report_receipt(self):
        report = grade_submission(self.case, self.wrong, execution="trusted")
        # These are mutations of a real FAILED trusted fixture receipt, never
        # an invented successful Docker receipt. Even equal pass/fail outcomes
        # do not make a different result or execution record the same evidence.
        for key, value in (("id", "different_execution"), ("result_hash", "0"*64),
                           ("execution", "none"), ("execution_status", "unavailable"),
                           ("checks", [])):
            with self.subTest(field=key), tempfile.TemporaryDirectory() as directory:
                receipt = copy.deepcopy(report["mandatory_execution"][0])
                receipt[key] = value
                ledger = ledger_fixture(self.case, self.wrong, report)
                include_receipt(directory, ledger, receipt)
                with self.assertRaises(ValueError):
                    attach_review(self.case, report, ledger, submission=self.wrong, evidence_dir=directory)

    def test_actual_unavailable_and_failed_runs_cannot_be_interchanged_in_review(self):
        failed = grade_submission(self.case, self.wrong, execution="trusted")
        unavailable = grade_submission(self.case, self.wrong, execution="none")
        self.assertIs(failed["mandatory_execution"][0]["passed"], False)
        self.assertIsNone(unavailable["mandatory_execution"][0]["passed"])
        for report, evidence in ((failed, unavailable), (unavailable, failed)):
            with self.subTest(report_status=report["mandatory_execution"][0]["status"]), tempfile.TemporaryDirectory() as directory:
                ledger = ledger_fixture(self.case, self.wrong, report)
                include_receipt(directory, ledger, evidence["mandatory_execution"][0])
                with self.assertRaises(ValueError):
                    attach_review(self.case, report, ledger, submission=self.wrong, evidence_dir=directory)

    def test_selftest_checks_actual_mandatory_execution_not_only_automatic_seventy(self):
        # Restrict the CLI suite to one actual NRB03 case; both fixture sources
        # really execute. The negative arm changes only the required code file.
        for submission, expected_exit, expected_pass in ((self.reference, 0, True), (self.wrong, 1, False)):
            with self.subTest(correct_code=expected_pass), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "selftest.json"
                with patch("nrb.cli.build_suite", return_value=[self.case]), \
                     patch("nrb.cli.reference_submission", return_value=copy.deepcopy(submission)):
                    exit_code = cli.main(["selftest", "--seeds", "17", "--out", str(output)])
                result = json.loads(output.read_text(encoding="utf-8"))
                self.assertEqual(exit_code, expected_exit)
                self.assertIs(result["passed"], expected_pass)
                self.assertEqual(result["cases_checked"], 1)
                row = result["checks"][0]
                self.assertEqual(row["oracle_auto_points"], 70)
                self.assertEqual(row["oracle_coverage"], 1)
                self.assertIs(row["passed"], expected_pass)
                self.assertIs(row["mandatory_execution"][0]["passed"], expected_pass)
                self.assertEqual(row["mandatory_execution"][0]["execution"], "trusted")


if __name__ == "__main__":
    unittest.main()

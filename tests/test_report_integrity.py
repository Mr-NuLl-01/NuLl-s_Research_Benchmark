"""Report mutation controls, using explicit synthetic reviewer fixtures.

No fixture is a scientific review, a model trial, or an execution attestation.
The tests do not fabricate execution passes. They check that accidental edits to
saved report data cannot alter scores or completion under an unchanged seal.
"""
from __future__ import annotations

import copy
import unittest

from nrb.analysis import paired_comparison
from nrb.completion import refresh_completion
from nrb.core import (attach_review, get_case, grade_submission, reference_submission,
                      review_ledger, seal_report, summarize, validate_final_report)


LABEL = "Synthetic report-integrity fixture, not a scientific judgment"


def reviewed(case, submission, automatic, *, scores=(10, 10, 10), fail_proofs=False):
    ledger = review_ledger(case, submission, report=automatic)
    ledger["reviewer_id"] = "report-integrity-fixture"
    for row, score in zip(ledger["criteria"], scores):
        row.update(score=score, evidence=LABEL, rationale=LABEL)
    for row in ledger["essential_review"]:
        outcome = "fail" if fail_proofs and row["id"] in {"existence_uniqueness", "residual_bound_proof"} else "pass"
        row.update(outcome=outcome, evidence=LABEL, rationale=LABEL)
    return attach_review(case, automatic, ledger, submission=submission)


def run_for(report):
    result = summarize([report], expected_ids=(report["task_id"],))
    result.update(track="agent-diagnostic", model_label="synthetic-fixture",
                  harness_label="unit-test", metadata={})
    return result


class ReportIntegrityContracts(unittest.TestCase):
    def setUp(self):
        self.case = get_case("NRB08", 17)
        self.submission = reference_submission(self.case)
        self.automatic = grade_submission(self.case, self.submission)
        self.reviewed = reviewed(self.case, self.submission, self.automatic)

    def assert_rejected_everywhere(self, original, mutant, score_kind="automatic"):
        with self.assertRaises(ValueError):
            validate_final_report(mutant)
        with self.assertRaises(ValueError):
            summarize([mutant], expected_ids=(mutant["task_id"],))
        left = run_for(original)
        right = copy.deepcopy(left)
        right["reports"] = [mutant]
        with self.assertRaises(ValueError):
            paired_comparison([left], [right], score_kind=score_kind, draws=100)

    def test_automatic_score_mutation_cannot_enter_summary_or_comparison(self):
        mutant = copy.deepcopy(self.automatic)
        mutant.update(auto_points=999, auto_percent=999)
        self.assert_rejected_everywhere(self.automatic, mutant)

    def test_reviewed_total_and_quality_record_mutations_are_rejected(self):
        for label, change in (
            ("plausible wrong total", lambda row: row.update(total=81)),
            ("inflated total", lambda row: row.update(total=999)),
            ("review points", lambda row: row.update(review_points=29)),
            ("altered quality ledger", lambda row: row["review"]["criteria"][0].update(score=9)),
            ("altered review identity", lambda row: row["review"].update(reviewer_id="different-fixture")),
        ):
            with self.subTest(mutation=label):
                mutant = copy.deepcopy(self.reviewed)
                change(mutant)
                self.assert_rejected_everywhere(self.reviewed, mutant, score_kind="reviewed")

    def test_pending_proofs_cannot_be_relabelled_complete(self):
        mutant = copy.deepcopy(self.automatic)
        mutant.update(completion_status="complete", quality_qualified=True, pending_items=[])
        self.assert_rejected_everywhere(self.automatic, mutant)

    def test_bound_essential_proof_failure_preserves_raw_eighty(self):
        report = reviewed(self.case, self.submission, self.automatic,
                          scores=(0, 0, 10), fail_proofs=True)
        self.assertTrue(validate_final_report(report))
        self.assertEqual(report["total"], 80)
        self.assertEqual(report["completion_status"], "failed")
        self.assertIs(report["quality_qualified"], False)
        mutant = copy.deepcopy(report)
        for row in mutant["essential_review"]:
            row["outcome"] = "pass"
        mutant = refresh_completion(mutant)
        self.assert_rejected_everywhere(report, mutant, score_kind="reviewed")

    def test_search_receipt_identity_or_result_edits_break_automatic_seal(self):
        case = get_case("NRB03", 17)
        report = grade_submission(case, reference_submission(case), execution="none")
        self.assertEqual(report["completion_status"], "infrastructure_unscored")
        for key, value in (("source_hash", "0"*64), ("input_hash", "0"*64),
                           ("result_hash", "0"*64), ("passed", False),
                           ("execution_status", "ok"), ("status", "fail")):
            with self.subTest(receipt_field=key):
                mutant = copy.deepcopy(report)
                mutant["mandatory_execution"][0][key] = value
                mutant = refresh_completion(mutant)
                self.assert_rejected_everywhere(report, mutant)

    def test_unsealed_extra_execution_cannot_fabricate_failure_or_pending_work(self):
        for task_id, receipt_id in (("NRB08", "never_executed"), ("NRB09", "render")):
            case = get_case(task_id, 17)
            original = grade_submission(case, reference_submission(case))
            for outcome in (False, None):
                with self.subTest(task=task_id, receipt=receipt_id, passed=outcome):
                    mutant = copy.deepcopy(original)
                    mutant["mandatory_execution"] = [{"id": receipt_id, "passed": outcome}]
                    mutant = refresh_completion(mutant)
                    # Updating derived fields must not legitimise an unbound
                    # underlying mandatory-execution observation.
                    self.assert_rejected_everywhere(original, mutant)

    def test_protocol_eligibility_flags_are_bound_to_automatic_report(self):
        protocol = seal_report(dict(self.automatic, status="protocol_violation",
                                    protocol_violation=True, comparison_eligible=False))
        self.assertTrue(validate_final_report(protocol))
        self.assertFalse(summarize([protocol], expected_ids=("NRB08",))["comparison_eligible"])
        mutant = copy.deepcopy(protocol)
        mutant.update(protocol_violation=False, comparison_eligible=True)
        with self.assertRaises(ValueError):
            validate_final_report(mutant)
        with self.assertRaises(ValueError):
            summarize([mutant], expected_ids=("NRB08",))


if __name__ == "__main__":
    unittest.main()

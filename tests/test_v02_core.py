"""Completion and evaluator-identity contracts using synthetic review fixtures.

Every review below is a labeled unit-test fixture, not a scientific judgment,
model trial, human-review observation, or evidence of reviewer performance.
Blank ledgers are filled explicitly so no missing essential outcome defaults
to pass. These tests do not forge execution or rendering pass receipts.
"""

from __future__ import annotations

import copy
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import nrb
from nrb.analysis import paired_comparison
from nrb.core import (attach_review, get_case, grade_submission,
                      reference_submission, review_ledger, summarize)
from nrb.provenance import IDENTITY_FIELDS, evaluator_digest, source_manifest


FIXTURE_LABEL = "SYNTHETIC CONTRACT FIXTURE; not a scientific review"


def fixture_review(case, submission, report, *, scores=(10, 10, 10), outcomes=None,
                   reviewer_type="human"):
    """Fill a genuine blank ledger with explicit, synthetic fixture decisions."""
    ledger = review_ledger(case, submission, report=report)
    ledger["reviewer_id"] = "contract-fixture-" + reviewer_type
    ledger["reviewer_type"] = reviewer_type
    for entry, score in zip(ledger["criteria"], scores):
        entry.update(score=score, evidence=FIXTURE_LABEL + ": submitted artifacts",
                     rationale=FIXTURE_LABEL + ": explicit score supplied only to test aggregation")
    outcomes = outcomes or {}
    for entry in ledger["essential_review"]:
        outcome = outcomes.get(entry["id"], "pass")
        entry.update(outcome=outcome,
                     evidence="" if outcome == "unassessed" else FIXTURE_LABEL + ": submitted artifacts",
                     rationale="" if outcome == "unassessed" else FIXTURE_LABEL + ": explicit " + outcome + " finding")
    return ledger


def reviewed_fixture(task_id, *, seed=17, scores=(10, 10, 10), outcomes=None,
                     reviewer_type="human", execution="none"):
    case = get_case(task_id, seed)
    submission = reference_submission(case)
    report = grade_submission(case, submission, execution=execution)
    ledger = fixture_review(case, submission, report, scores=scores, outcomes=outcomes,
                            reviewer_type=reviewer_type)
    return case, submission, ledger, attach_review(case, report, ledger, submission=submission)


def diagnostic_run(report):
    run = summarize([report], expected_ids=(report["task_id"],))
    run.update(track="agent-diagnostic", model_label="synthetic-contract-model",
               harness_label="unit-test", metadata={})
    return run


class CompletionContracts(unittest.TestCase):
    def test_blank_ledger_contains_no_default_scores_or_essential_passes(self):
        case = get_case("NRB08", 17)
        submission = reference_submission(case)
        report = grade_submission(case, submission)
        ledger = review_ledger(case, submission, report=report)
        self.assertEqual(len(ledger["criteria"]), 3)
        self.assertTrue(all(entry["score"] is None for entry in ledger["criteria"]))
        self.assertEqual({entry["outcome"] for entry in ledger["essential_review"]}, {"unassessed"})
        self.assertTrue(all(not entry["evidence"] and not entry["rationale"] for entry in ledger["essential_review"]))
        self.assertEqual(ledger["automatic_report_hash"], report["automatic_report_hash"])
        with self.assertRaises(ValueError):
            attach_review(case, report, ledger, submission=submission)

    def test_numeric_seventy_plus_zero_zero_ten_keeps_eighty_but_fails_proofs(self):
        case, submission, ledger, report = reviewed_fixture(
            "NRB08", scores=(0, 0, 10), outcomes={
                "existence_uniqueness": "fail", "residual_bound_proof": "fail",
                "counterexample_explanation": "pass"})
        self.assertEqual(report["auto_points"], 70)
        self.assertEqual(report["review_points"], 10)
        self.assertEqual(report["total"], 80)
        self.assertEqual(report["completion_status"], "failed")
        self.assertIs(report["quality_qualified"], False)
        self.assertEqual(set(report["review_critical_failures"]), {"existence_uniqueness", "residual_bound_proof"})
        self.assertEqual(report["automatic_critical_failures"], [])

    def test_meaningless_english_can_keep_numeric_eighty_but_not_completion(self):
        case = get_case("NRB10", 17)
        submission = reference_submission(case)
        nonsense = "Blue algebra sleeps potato potato.\n"
        submission["artifacts"]["revised_excerpt.md"] = nonsense
        submission["answer"]["artifact_sha256"]["revised_excerpt.md"] = hashlib.sha256(nonsense.encode()).hexdigest()
        automatic = grade_submission(case, submission)
        self.assertEqual(automatic["auto_points"], 70)
        ledger = fixture_review(case, submission, automatic, scores=(5, 0, 5),
                                outcomes={"english_fidelity": "fail"})
        for entry in ledger["essential_review"]:
            if entry["id"] == "english_fidelity":
                entry.update(evidence=FIXTURE_LABEL + ": revised_excerpt.md line 1 is 'Blue algebra sleeps potato potato.'",
                             rationale=FIXTURE_LABEL + ": this supplied text contains no meaningful scientific revision")
        report = attach_review(case, automatic, ledger, submission=submission)
        self.assertEqual(report["total"], 80)
        self.assertEqual(report["completion_status"], "failed")
        self.assertIs(report["quality_qualified"], False)
        self.assertIn("english_fidelity", report["review_critical_failures"])

    def test_low_style_score_has_no_arbitrary_five_point_completion_floor(self):
        case, submission, ledger, report = reviewed_fixture("NRB04", scores=(10, 10, 4), execution="trusted")
        self.assertEqual([entry["score"] for entry in ledger["criteria"]], [10, 10, 4])
        self.assertEqual(ledger["criteria"][-1]["id"], "maintainability")
        self.assertEqual(report["total"], 94)
        self.assertEqual(report["completion_status"], "complete")
        self.assertIs(report["quality_qualified"], True)
        self.assertEqual(report["critical_failures"], [])

    def test_unreviewed_work_is_pending_not_failed_or_assumed_complete(self):
        case = get_case("NRB08", 17)
        report = grade_submission(case, reference_submission(case))
        self.assertEqual(report["auto_points"], 70)
        self.assertEqual(report["completion_status"], "pending_review")
        self.assertIsNone(report["quality_qualified"])
        self.assertIsNone(report["review_points"])
        self.assertIsNone(report["total"])
        self.assertEqual(report["review_critical_failures"], [])
        self.assertIn("essential:existence_uniqueness", report["pending_items"])

    def test_infrastructure_unscored_remains_distinct_from_model_failure(self):
        case = get_case("NRB04", 17)
        report = grade_submission(case, reference_submission(case), execution="none")
        self.assertEqual(report["auto_points"], 20)
        self.assertAlmostEqual(report["coverage"], 20/70)
        self.assertEqual(report["completion_status"], "infrastructure_unscored")
        self.assertIsNone(report["auto_percent"])
        self.assertIsNone(report["quality_qualified"])
        self.assertEqual(report["critical_failures"], [])
        self.assertTrue(any(item.startswith("automatic:") for item in report["pending_items"]))

    def test_confirmed_failure_does_not_erase_pending_responsibilities(self):
        case, submission, ledger, report = reviewed_fixture("NRB08", scores=(0, 0, 10), outcomes={
            "existence_uniqueness": "fail", "residual_bound_proof": "unassessed"})
        self.assertEqual(report["completion_status"], "failed")
        self.assertIs(report["quality_qualified"], False)
        self.assertIn("existence_uniqueness", report["review_critical_failures"])
        self.assertIn("essential:residual_bound_proof", report["pending_items"])
        self.assertEqual({entry["id"]: entry["outcome"] for entry in report["essential_review"]}, {
            "existence_uniqueness": "fail", "residual_bound_proof": "unassessed",
            "counterexample_explanation": "pass"})

    def test_summary_counts_and_bounds_keep_missing_tasks_in_the_denominator(self):
        complete = reviewed_fixture("NRB01")[3]
        failed = reviewed_fixture("NRB08", scores=(0, 0, 10), outcomes={"existence_uniqueness": "fail"})[3]
        pending_case = get_case("NRB02", 17)
        pending = grade_submission(pending_case, reference_submission(pending_case))
        infra_case = get_case("NRB04", 17)
        infra = grade_submission(infra_case, reference_submission(infra_case), execution="none")
        result = summarize([complete, failed, pending, infra], expected_ids=("NRB01", "NRB02", "NRB04", "NRB05", "NRB08"))
        self.assertEqual(result["completion_counts"], {
            "complete": 1, "failed": 1, "pending_review": 1,
            "infrastructure_unscored": 1, "legacy_unverified": 0, "missing": 1})
        self.assertEqual(result["expected_tasks"], 5)
        self.assertEqual(result["missing_tasks"], ["NRB05"])
        self.assertEqual(result["pending_task_count"], 3)
        self.assertIsNone(result["completion_rate"])
        self.assertEqual(result["completion_rate_bounds"], [1/5, 4/5])
        self.assertEqual(result["critical_failure_rate_bounds"], [1/5, 4/5])
        self.assertIsNone(result["critical_free_rate"])
        self.assertIsNone(result["auto_macro_percent"])
        self.assertIsNone(result["reviewed_macro_total"])
        self.assertEqual(len(result["task_table"]), 4)
        self.assertEqual({entry["task_id"] for entry in result["task_table"]}, {"NRB01", "NRB02", "NRB04", "NRB08"})

    def test_mixed_human_llm_review_is_explicitly_provisional(self):
        human = reviewed_fixture("NRB08", reviewer_type="human")[3]
        llm = reviewed_fixture("NRB10", reviewer_type="llm")[3]
        result = summarize([human, llm], expected_ids=("NRB08", "NRB10"))
        self.assertEqual(result["review_status"], "mixed_human_llm_provisional")
        self.assertEqual(human["score_label"], "human_reviewed")
        self.assertEqual(llm["score_label"], "llm_reviewed_provisional")


class EvaluatorIdentityContracts(unittest.TestCase):
    def setUp(self):
        self.case = get_case("NRB08", 17)
        self.submission = reference_submission(self.case)
        self.report = grade_submission(self.case, self.submission)
        self.review = fixture_review(self.case, self.submission, self.report)

    def test_real_grader_change_changes_digest_with_identical_candidate_prompt(self):
        original_root = Path(nrb.__file__).resolve().parent
        with tempfile.TemporaryDirectory() as root:
            workspace = Path(root)
            package = workspace / "nrb"
            shutil.copytree(original_root, package, ignore=shutil.ignore_patterns("__pycache__"))
            code = "from nrb.core import candidate_prompt,get_case; import hashlib; print(hashlib.sha256(candidate_prompt(get_case('NRB06',17)).encode()).hexdigest())"
            def public_prompt_hash():
                result = subprocess.run([sys.executable, "-c", code], cwd=workspace,
                                        env={key: os.environ[key] for key in ("PATH", "SYSTEMROOT", "WINDIR") if key in os.environ},
                                        capture_output=True, text=True, check=True, timeout=10)
                return result.stdout.strip()
            before_prompt = public_prompt_hash()
            before_digest = evaluator_digest(package)
            grader = package / "tasks" / "t06.py"
            source = grader.read_text(encoding="utf-8")
            self.assertIn("rtol=2e-6, atol=1e-18", source)
            grader.write_text(source.replace("rtol=2e-6, atol=1e-18", "rtol=2.5e-6, atol=1e-18", 1), encoding="utf-8")
            self.assertNotEqual(evaluator_digest(package), before_digest)
            self.assertEqual(public_prompt_hash(), before_prompt)

    def test_documentation_and_standalone_regressions_are_intentionally_excluded(self):
        original_root = Path(nrb.__file__).resolve().parent
        with tempfile.TemporaryDirectory() as root:
            workspace = Path(root)
            package = workspace / "nrb"
            shutil.copytree(original_root, package, ignore=shutil.ignore_patterns("__pycache__"))
            digest = evaluator_digest(package)
            (workspace / "docs").mkdir()
            (workspace / "docs" / "note.md").write_text("Synthetic documentation fixture.\n", encoding="utf-8")
            (workspace / "tests").mkdir()
            (workspace / "tests" / "test_fixture.py").write_text("# Synthetic standalone regression fixture.\n", encoding="utf-8")
            self.assertEqual(evaluator_digest(package), digest)
            names = source_manifest(package)
            self.assertIn("nrb/tasks/t04.py", names)
            self.assertIn("nrb/tasks/t05.py", names)
            self.assertIn("nrb/evaluation_policy.json", names)
            self.assertFalse(any(name.startswith(("docs/", "tests/")) for name in names))

    def test_automatic_report_tampering_is_rejected_before_review_attachment(self):
        mutations = {
            "inflated automatic points": lambda report: report.update(auto_points=999),
            "removed checks": lambda report: report.update(checks=[]),
            "different answer key": lambda report: report.update(answer_key_hash="0"*64),
            "different report seal": lambda report: report.update(automatic_report_hash="0"*64),
        }
        for label, mutate in mutations.items():
            with self.subTest(tampering=label):
                report = copy.deepcopy(self.report)
                mutate(report)
                with self.assertRaises(ValueError):
                    attach_review(self.case, report, self.review, submission=self.submission)

    def test_report_and_ledger_identity_mismatches_are_rejected(self):
        wrong_values = {"task_id": "NRB10", "seed": 18, "case_hash": "0"*64,
                        "submission_hash": "0"*64, "rubric_hash": "0"*64,
                        "review_policy_version": "wrong-policy", "evaluator_digest": "0"*64,
                        "evaluation_schema_version": "wrong-schema", "benchmark_version": "0.0.0",
                        "evaluator_commit": "f"*40, "automatic_report_hash": "0"*64}
        for location in ("report", "ledger"):
            for key, value in wrong_values.items():
                with self.subTest(location=location, field=key):
                    report, ledger = copy.deepcopy(self.report), copy.deepcopy(self.review)
                    target = report if location == "report" else ledger
                    target[key] = value
                    with self.assertRaises(ValueError):
                        attach_review(self.case, report, ledger, submission=self.submission)

    def test_essential_outcomes_cannot_be_omitted_or_pass_without_evidence(self):
        variants = []
        missing = copy.deepcopy(self.review)
        missing["essential_review"].pop()
        variants.append(missing)
        duplicated = copy.deepcopy(self.review)
        duplicated["essential_review"][1] = copy.deepcopy(duplicated["essential_review"][0])
        variants.append(duplicated)
        unsupported = copy.deepcopy(self.review)
        unsupported["essential_review"][0]["outcome"] = "approved"
        variants.append(unsupported)
        no_evidence = copy.deepcopy(self.review)
        no_evidence["essential_review"][0]["evidence"] = ""
        variants.append(no_evidence)
        for ledger in variants:
            with self.subTest(essential=ledger["essential_review"]), self.assertRaises(ValueError):
                attach_review(self.case, self.report, ledger, submission=self.submission)

    def test_original_submission_and_exact_case_are_required(self):
        with self.assertRaises(ValueError):
            attach_review(self.case, self.report, self.review)
        changed = copy.deepcopy(self.submission)
        changed["artifacts"]["reasoning.md"] += "\nChanged synthetic fixture after grading.\n"
        with self.assertRaises(ValueError):
            attach_review(self.case, self.report, self.review, submission=changed)
        with self.assertRaises(ValueError):
            attach_review(get_case("NRB08", 18), self.report, self.review, submission=self.submission)
        changed_case = copy.deepcopy(self.case)
        changed_case["expected"]["answer"]["weighted_operator_norm"] = -1
        with self.assertRaises(ValueError):
            attach_review(changed_case, self.report, self.review, submission=self.submission)

    def test_legacy_reports_are_readable_unverified_but_cannot_enter_comparison(self):
        legacy = copy.deepcopy(self.report)
        for key in (*IDENTITY_FIELDS, "automatic_report_hash"):
            legacy.pop(key, None)
        result = summarize([legacy], expected_ids=("NRB08",))
        self.assertEqual(result["scoring_identity_status"], "legacy_unverified")
        self.assertIs(result["comparison_eligible"], False)
        self.assertEqual(result["completion_counts"]["legacy_unverified"], 1)
        self.assertNotIn("evaluator_digest", result)
        self.assertIsNone(result["completion_rate"])
        with self.assertRaises(ValueError):
            paired_comparison([diagnostic_run(legacy)], [diagnostic_run(legacy)], mode="diagnostic", draws=100)

    def test_identical_metadata_omissions_do_not_qualify_a_controlled_comparison(self):
        run = diagnostic_run(self.report)
        diagnostic = paired_comparison([run], [run], mode="diagnostic", draws=100)
        self.assertEqual(diagnostic["macro_delta_b_minus_a"], 0)
        self.assertEqual(diagnostic["score_kind"], "automatic_only_percent")
        self.assertEqual({entry["arm"] for entry in diagnostic["missing_metadata"]}, {"a", "b"})
        for entry in diagnostic["missing_metadata"]:
            self.assertLessEqual({"model_version", "tool_policy", "budget", "isolation"}, set(entry["fields"]))
        controlled = dict(run, track="agent-controlled")
        with self.assertRaises(ValueError):
            paired_comparison([controlled], [controlled], mode="controlled", draws=100)


if __name__ == "__main__":
    unittest.main()

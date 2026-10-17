"""Actual raster/receipt integration with explicitly synthetic review decisions.

The PNGs below come from an installed renderer, not mocked image success. Scores,
scientific outcomes and inspection acknowledgments are labeled contract fixtures;
they are not a scientific review, observation of candidate quality, or a human
inspection. Repository-authored NRB03 controls use only ``trusted`` or ``none``;
no Docker success is invented or relabeled as isolated execution.
"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nrb.core import (attach_review, fingerprint, get_case, grade_submission,
                      reference_submission, review_ledger, validate_final_report)
from nrb.provenance import evaluator_identity
from nrb.rendering import (RendererUnavailable, UnsafeSVG, render_svg,
                           renderer_identity)
from scripts.check_rendering import negative_controls

FIXTURE = "SYNTHETIC EVIDENCE CONTRACT FIXTURE; not a scientific review"


def filled_ledger(case, submission, report, *, outcomes=None):
    ledger = review_ledger(case, submission, report)
    ledger.update(reviewer_id="evidence-contract-fixture", reviewer_type="llm")
    for criterion in ledger["criteria"]:
        criterion.update(score=10, evidence=FIXTURE + ": submitted artifact",
                         rationale=FIXTURE + ": high scores test that numeric totals cannot replace essential gates")
    outcomes = outcomes or {}
    for essential in ledger["essential_review"]:
        outcome = outcomes.get(essential["id"], "pass")
        essential.update(outcome=outcome,
                         evidence="" if outcome == "unassessed" else FIXTURE + ": exact submission",
                         rationale="" if outcome == "unassessed" else FIXTURE + ": explicit " + outcome + " test decision")
    return ledger


def add_receipt(folder, ledger, receipt, name="render", filename="render-receipt.json"):
    path = Path(folder) / filename
    data = (json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode("utf-8")
    path.write_bytes(data)
    ledger["evidence_artifacts"][name] = {"file": filename, "sha256": hashlib.sha256(data).hexdigest()}


class ActualFigureReviewEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            renderer_identity()
        except RendererUnavailable as exc:
            raise unittest.SkipTest("Actual renderer integration unavailable: " + str(exc))

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="nrb-review-evidence-")
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.case = get_case("NRB09", 0)
        self.submission = reference_submission(self.case)
        self.report = grade_submission(self.case, self.submission)
        self.ledger = filled_ledger(self.case, self.submission, self.report)

    def rendered(self, submission=None, outcomes=None):
        submission = self.submission if submission is None else submission
        report = grade_submission(self.case, submission)
        ledger = filled_ledger(self.case, submission, report, outcomes=outcomes)
        receipt = render_svg(submission["artifacts"]["figure.svg"], self.folder / "figure.png",
                             case_hash=self.case["case_hash"], submission_hash=fingerprint(submission),
                             evaluator_identity=evaluator_identity())
        add_receipt(self.folder, ledger, receipt)
        ledger.update(render_png="figure.png", inspected_whole_figure=True, inspected_at_180mm=True)
        return report, ledger, receipt

    def attach(self, report, ledger, submission=None):
        return attach_review(self.case, report, ledger,
                             submission=self.submission if submission is None else submission,
                             evidence_dir=self.folder)

    def test_actual_png_receipt_can_satisfy_evidence_gate_for_explicit_fixture_review(self):
        report, ledger, receipt = self.rendered()
        out = self.attach(report, ledger)
        self.assertEqual(out["auto_points"], 70)
        self.assertEqual(out["total"], 100)
        self.assertEqual(out["completion_status"], "complete")
        self.assertTrue(out["quality_qualified"])
        self.assertEqual(out["score_label"], "llm_reviewed_provisional")
        self.assertEqual(out["mandatory_execution"], [{"id": "render", "passed": True,
            "detail": "Actual rendered bytes verified; readability remains a separate review judgement"}])
        self.assertTrue(validate_final_report(out))
        self.assertEqual(receipt["output_png_sha256"], hashlib.sha256((self.folder / "figure.png").read_bytes()).hexdigest())

    def test_white_cover_auto_seventy_and_high_scores_do_not_override_review_failure(self):
        covered = negative_controls(self.submission)["whitecover"]
        report, ledger, receipt = self.rendered(covered, outcomes={"render_legibility": "fail"})
        self.assertEqual(report["auto_points"], 70)
        self.assertFalse(report["critical_failures"])
        out = self.attach(report, ledger, covered)
        self.assertEqual(out["total"], 100)
        self.assertEqual(out["completion_status"], "failed")
        self.assertFalse(out["quality_qualified"])
        self.assertIn("render_legibility", out["review_critical_failures"])
        self.assertIn("essential:render_legibility", out["critical_failures"])
        # Successful rasterization is retained separately from the failed
        # readable-figure responsibility; a receipt alone never decides quality.
        self.assertTrue(out["mandatory_execution"][0]["passed"])
        self.assertTrue(validate_final_report(out))

    def test_missing_receipt_or_png_cannot_pass(self):
        with self.assertRaisesRegex(ValueError, "Required evaluator-side evidence is missing"):
            self.attach(self.report, self.ledger)
        report, ledger, _ = self.rendered()
        (self.folder / "figure.png").unlink()
        with self.assertRaisesRegex(ValueError, "Invalid actual-render evidence"):
            self.attach(report, ledger)

    def test_changed_svg_cannot_reuse_receipt_even_with_fresh_automatic_report(self):
        _, ledger, receipt = self.rendered()
        changed = copy.deepcopy(self.submission)
        changed["artifacts"]["figure.svg"] += "\n"
        report = grade_submission(self.case, changed)
        fresh_ledger = filled_ledger(self.case, changed, report)
        fresh_ledger.update(evidence_artifacts=copy.deepcopy(ledger["evidence_artifacts"]), render_png="figure.png",
                            inspected_whole_figure=True, inspected_at_180mm=True)
        self.assertEqual(report["auto_points"], 70)
        with self.assertRaisesRegex(ValueError, "Invalid actual-render evidence"):
            self.attach(report, fresh_ledger, changed)

    def test_changed_png_cannot_pass(self):
        report, ledger, _ = self.rendered()
        path = self.folder / "figure.png"
        path.write_bytes(path.read_bytes() + b"altered PNG bytes")
        with self.assertRaisesRegex(ValueError, "actual PNG hash mismatch"):
            self.attach(report, ledger)

    def test_whole_figure_and_180mm_acknowledgments_are_both_required(self):
        report, ledger, _ = self.rendered()
        for field in ("inspected_whole_figure", "inspected_at_180mm"):
            for wrong in (False, None, 1, "true"):
                changed = copy.deepcopy(ledger)
                changed[field] = wrong
                with self.subTest(field=field, value=wrong), self.assertRaisesRegex(ValueError, "explicit whole-figure and 180mm inspection"):
                    self.attach(report, changed)

    def test_rendering_pass_with_unassessed_visual_decision_stays_pending(self):
        report, ledger, _ = self.rendered(outcomes={"render_legibility": "unassessed"})
        ledger.update(inspected_whole_figure=False, inspected_at_180mm=False)
        out = self.attach(report, ledger)
        self.assertEqual(out["total"], 100)
        self.assertEqual(out["completion_status"], "pending_review")
        self.assertIsNone(out["quality_qualified"])
        self.assertIn("essential:render_legibility", out["pending_items"])
        self.assertTrue(out["mandatory_execution"][0]["passed"])


class UnavailableOrUnsafeFigureEvidence(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="nrb-unavailable-evidence-")
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.case = get_case("NRB09", 0)
        self.submission = reference_submission(self.case)

    def unavailable_receipt(self):
        # Exercise the real failure path with an explicit missing-runtime
        # condition. This is not an image or rendering-success mock.
        with patch("nrb.rendering.renderer_identity", side_effect=RendererUnavailable("contract fixture: renderer absent")):
            with self.assertRaises(RendererUnavailable):
                render_svg(self.submission["artifacts"]["figure.svg"], self.folder / "absent.png",
                           case_hash=self.case["case_hash"], submission_hash=fingerprint(self.submission),
                           evaluator_identity=evaluator_identity())
        self.assertFalse((self.folder / "absent.png").exists())
        return {"rendered": False, "status": "unavailable", "case_hash": self.case["case_hash"],
                "submission_hash": fingerprint(self.submission), "evaluator_identity": evaluator_identity(),
                "detail": FIXTURE + ": actual renderer invocation was unavailable"}

    def test_unavailable_render_evidence_preserves_infrastructure_status_and_cannot_pass(self):
        receipt = self.unavailable_receipt()
        report = grade_submission(self.case, self.submission)
        ledger = filled_ledger(self.case, self.submission, report, outcomes={"render_legibility": "unassessed"})
        add_receipt(self.folder, ledger, receipt)
        out = attach_review(self.case, report, ledger, submission=self.submission, evidence_dir=self.folder)
        self.assertEqual(out["total"], 100)
        self.assertEqual(out["completion_status"], "infrastructure_unscored")
        self.assertIsNone(out["quality_qualified"])
        self.assertEqual(out["mandatory_execution"][0]["passed"], None)
        self.assertIn("execution:render", out["pending_items"])
        self.assertTrue(validate_final_report(out))
        for entry in ledger["essential_review"]:
            if entry["id"] == "render_legibility":
                entry.update(outcome="pass", evidence=FIXTURE, rationale=FIXTURE)
        with self.assertRaisesRegex(ValueError, "Unrendered SVG cannot pass"):
            attach_review(self.case, report, ledger, submission=self.submission, evidence_dir=self.folder)

    def test_unsafe_render_failure_cannot_be_replaced_by_high_scores_or_pass_claim(self):
        unsafe = copy.deepcopy(self.submission)
        unsafe["artifacts"]["figure.svg"] = unsafe["artifacts"]["figure.svg"].replace("</svg>", "<script>1</script></svg>")
        with self.assertRaises(UnsafeSVG):
            render_svg(unsafe["artifacts"]["figure.svg"], self.folder / "unsafe.png", case_hash=self.case["case_hash"],
                       submission_hash=fingerprint(unsafe), evaluator_identity=evaluator_identity())
        receipt = {"rendered": False, "status": "unsafe_svg", "case_hash": self.case["case_hash"],
                   "submission_hash": fingerprint(unsafe), "evaluator_identity": evaluator_identity(),
                   "detail": FIXTURE + ": forbidden script was actually rejected before rendering"}
        report = grade_submission(self.case, unsafe)
        ledger = filled_ledger(self.case, unsafe, report, outcomes={"render_legibility": "fail"})
        add_receipt(self.folder, ledger, receipt)
        out = attach_review(self.case, report, ledger, submission=unsafe, evidence_dir=self.folder)
        self.assertEqual(out["completion_status"], "failed")
        self.assertFalse(out["quality_qualified"])
        self.assertIn("execution:render", out["critical_failures"])
        self.assertFalse((self.folder / "unsafe.png").exists())
        for entry in ledger["essential_review"]:
            if entry["id"] == "render_legibility":
                entry.update(outcome="pass", evidence=FIXTURE, rationale=FIXTURE)
        with self.assertRaisesRegex(ValueError, "Unrendered SVG cannot pass"):
            attach_review(self.case, report, ledger, submission=unsafe, evidence_dir=self.folder)


class MandatorySearchEvidence(unittest.TestCase):
    def test_unavailable_mandatory_search_is_retained_under_high_review_scores(self):
        case = get_case("NRB03", 0)
        submission = reference_submission(case)
        report = grade_submission(case, submission, execution="none")
        receipt = copy.deepcopy(report["mandatory_execution"][0])
        self.assertEqual(receipt["execution"], "none")
        self.assertEqual(receipt["status"], "unassessed")
        self.assertIsNone(receipt["passed"])
        ledger = filled_ledger(case, submission, report, outcomes={"search_reproduced": "unassessed"})
        out = attach_review(case, report, ledger, submission=submission)
        self.assertEqual(out["total"], 100)
        self.assertEqual(out["completion_status"], "infrastructure_unscored")
        self.assertIsNone(out["quality_qualified"])
        self.assertEqual(out["mandatory_execution"], [receipt])
        self.assertIn("execution:solve_reproduction", out["pending_items"])

    def test_actually_failed_repository_search_control_retains_failure(self):
        case = get_case("NRB03", 0)
        submission = reference_submission(case)
        # Repository-authored negative control, not untrusted candidate code.
        submission["artifacts"]["solve.py"] = "def solve(problem):\n    return {}\n"
        report = grade_submission(case, submission, execution="trusted")
        receipt = copy.deepcopy(report["mandatory_execution"][0])
        self.assertEqual(report["auto_points"], 70)
        self.assertEqual(receipt["execution"], "trusted")
        self.assertEqual(receipt["status"], "fail")
        self.assertFalse(receipt["passed"])
        ledger = filled_ledger(case, submission, report, outcomes={"search_reproduced": "fail"})
        out = attach_review(case, report, ledger, submission=submission)
        self.assertEqual(out["total"], 100)
        self.assertEqual(out["completion_status"], "failed")
        self.assertFalse(out["quality_qualified"])
        self.assertEqual(out["mandatory_execution"], [receipt])
        self.assertIn("execution:solve_reproduction", out["critical_failures"])

    def test_real_trusted_success_is_retained_but_cannot_claim_isolated_execution(self):
        case = get_case("NRB03", 0)
        submission = reference_submission(case)
        report = grade_submission(case, submission, execution="trusted")
        receipt = copy.deepcopy(report["mandatory_execution"][0])
        self.assertEqual(receipt["execution"], "trusted")
        self.assertEqual(receipt["execution_status"], "ok")
        self.assertTrue(receipt["passed"])
        ledger = filled_ledger(case, submission, report, outcomes={"search_reproduced": "unassessed"})
        out = attach_review(case, report, ledger, submission=submission)
        self.assertEqual(out["mandatory_execution"], [receipt])
        self.assertEqual(out["completion_status"], "pending_review")
        with tempfile.TemporaryDirectory(prefix="nrb-trusted-receipt-") as folder:
            add_receipt(folder, ledger, receipt, name="solve_reproduction", filename="solve-receipt.json")
            for entry in ledger["essential_review"]:
                if entry["id"] == "search_reproduced":
                    entry.update(outcome="pass", evidence=FIXTURE, rationale=FIXTURE)
            with self.assertRaisesRegex(ValueError, "successful isolated execution"):
                attach_review(case, report, ledger, submission=submission, evidence_dir=folder)


if __name__ == "__main__":
    unittest.main()

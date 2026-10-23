"""Regression tests for the V2 automatic-score contract, not model benchmarks."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nrb_v1.provenance import fingerprint
from nrb_v2 import __version__
from nrb_v2.cli import batch, read
from nrb_v2.grading import grade, validate_report, public_manifest
from nrb_v2.packets import candidate, catalog
from nrb_v2.registry import ALL_IDS, PYTHON_IDS, OBJECTIVE_IDS, MANUAL_IDS, source_filename, module, cases, spec


def submission(source="def solve(problem): return {}\n"):
    return {"task_id": "P01", "artifacts": {"solution.py": source}, "answer": {}}


class CatalogTests(unittest.TestCase):
    def test_exact_release_scope(self):
        self.assertEqual(len(ALL_IDS), 20)
        self.assertEqual(sum(spec(t)["status"] == "ready" for t in ALL_IDS), 20)
        self.assertEqual(len(OBJECTIVE_IDS), 13)
        self.assertEqual(len(MANUAL_IDS), 7)
        for task in catalog()["tasks"]:
            if task["id"] in OBJECTIVE_IDS:
                self.assertEqual(task["required_artifacts"], [source_filename(task["id"])])
                self.assertFalse(task["manual_review_required"])
            else:
                self.assertTrue(task["manual_review_required"])
                with self.assertRaises(ValueError):
                    module(task["id"])

    def test_candidate_packets_preserve_bug_programs_and_remove_manual_gate(self):
        for task_id in PYTHON_IDS:
            packet = candidate(task_id)
            self.assertEqual(packet["packet_hash"], fingerprint(packet["content"].encode()))
            self.assertIn(__version__, packet["content"])
            self.assertNotIn("自动70/人工30", packet["content"])
            self.assertNotIn("其余 30 分由人工", packet["content"])
            self.assertIn("只需提交一个完整的 `solution.py`", packet["content"])
        self.assertIn("def solve(problem)", candidate("P03")["content"])
        self.assertIn("def _fit", candidate("P08")["content"])
        self.assertIn("最大密度残差必须≤4e-7", candidate("P07")["content"])
        self.assertIn("1e-26", candidate("P06")["content"])

    def test_checks_keep_fixed_relative_weights(self):
        for task in OBJECTIVE_IDS:
            fixture = cases(task, 17)
            self.assertEqual(sum(c["weight"] for c in fixture), 70)
            for tier, total in [("basic", 20), ("scientific", 30), ("stress", 20)]:
                self.assertEqual(sum(c["weight"] for c in fixture if c["tier"] == tier), total)

    def test_all_python_packets_allow_the_same_pinned_libraries(self):
        for task_id in PYTHON_IDS:
            body = candidate(task_id)["content"]
            self.assertIn("NumPy 2.3.5、SciPy 1.17.0", body)
            for prohibition in ("仅Python标准库", "只用Python标准库", "无第三方", "不使用第三方", "外部数据及第三方", "提交标准库solution.py"):
                self.assertNotIn(prohibition, body)

    def test_p06_endpoints_are_interior_and_numeric_rank_is_public(self):
        fixtures = cases("P06", 17)
        for case in fixtures:
            if case["id"].endswith("endpoint_interior_minimum"):
                lo, hi = case["input"]["bounds"]
                expected_D = lo + (hi - lo) * 1e-4 if case["id"].startswith("lower") else hi - (hi - lo) * 1e-4
                self.assertAlmostEqual(case["expected"]["diffusion"], expected_D, delta=3e-8)
                self.assertGreater(case["expected"]["diffusion"], lo)
                self.assertLess(case["expected"]["diffusion"], hi)
        bad = next(c for c in fixtures if c["id"] == "reject_unresolved_nuisance")
        self.assertEqual(bad["error"], "ValueError")
        with self.assertRaises(ValueError):
            module("P06")._solve(bad["input"])


class GradingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ref = module("P01").reference_submission(17)
        cls.report = grade("P01", dict(ref, task_id="P01"), backend="trusted")

    def test_reference_is_fully_automatic_but_not_model_result(self):
        report = validate_report(self.report)
        self.assertEqual(report["score"], 100)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["completion_status"], "complete")
        self.assertFalse(report["manual_review_required"])
        self.assertTrue(report["control_only"])
        self.assertFalse(report["comparison_eligible"])

    def test_no_execution_is_null_not_zero(self):
        report = grade("P01", submission(), backend="none")
        validate_report(report)
        self.assertIsNone(report["score"])
        self.assertEqual(report["status"], "unscored")
        self.assertTrue(all(c["passed"] is None for c in report["checks"]))

    def test_missing_source_is_unscored(self):
        report = grade("P01", {"task_id": "P01", "artifacts": {}, "answer": {}}, backend="none")
        self.assertIsNone(report["score"])
        validate_report(report)

    def test_load_failure_cannot_earn_invalid_input_points(self):
        report = grade("P01", submission("raise ValueError('import failure')"), backend="trusted")
        self.assertEqual(report["score"], 0)
        self.assertTrue(all(c["passed"] is False for c in report["checks"]))
        validate_report(report)

    def test_candidate_timeout_is_reported_not_silently_lost(self):
        report = grade("P01", submission("def solve(problem):\n while True: pass\n"), backend="trusted", timeout=0.1)
        self.assertEqual(report["score"], 0)
        self.assertEqual(report["execution"]["status"], "failed")
        self.assertIn("Timeout", report["checks"][0]["detail"])

    def test_sidecars_are_not_executed(self):
        candidate_submission = submission("def solve(problem): return {}")
        candidate_submission["artifacts"]["sitecustomize.py"] = "raise RuntimeError('must not execute')"
        with patch("nrb_v2.grading.execute") as execute:
            execute.return_value = {"backend": "none", "language": "python", "status": "unavailable", "records": []}
            grade("P01", candidate_submission, backend="none")
            self.assertEqual(set(execute.call_args.args[1]["artifacts"]), {"solution.py"})

    def test_tampering_rejected_even_after_resealing(self):
        changes = [
            lambda r: r.update(score=99),
            lambda r: r.update(task_id="P02"),
            lambda r: r["checks"][0].update(weight=999),
            lambda r: r["checks"][0].update(passed=1),
            lambda r: r["checks"].pop(),
            lambda r: r["checks"].append(copy.deepcopy(r["checks"][0])),
            lambda r: r.update(packet_hash="0" * 64),
            lambda r: r.update(test_manifest_hash="0" * 64),
            lambda r: r.update(evaluator_fingerprint="0" * 64),
            lambda r: r.update(comparison_eligible=True),
            lambda r: r.update(critical_passed=False),
            lambda r: r["execution"].update(status="failed"),
        ]
        for change in changes:
            report = copy.deepcopy(self.report)
            change(report)
            report["report_hash"] = fingerprint({k: v for k, v in report.items() if k != "report_hash"})
            with self.assertRaises(ValueError):
                validate_report(report)

    def test_partial_credit_is_recomputed(self):
        report = grade("P01", submission("def solve(problem): raise ValueError('always')"), backend="trusted")
        self.assertGreater(report["score"], 0)
        self.assertLess(report["score"], 100)
        self.assertEqual(report["score"], round(100 * sum(c["weight"] for c in report["checks"] if c["passed"]) / 70, 6))
        self.assertEqual(report["status"], "failed")

    def test_docker_unavailable_points_to_the_v2_environment(self):
        with patch("nrb_v2.grading.execute") as execute:
            execute.return_value = {"backend": "docker", "language": "python", "status": "unavailable", "records": [],
                                    "error": "Docker image/daemon unavailable; build environments/v1/Dockerfile"}
            report = grade("P01", submission(), backend="docker")
        self.assertIn("environments/v2/Dockerfile", report["execution"]["error"])
        self.assertIn("Build-Environment", report["execution"]["error"])
        self.assertNotIn("environments/v1", report["execution"]["error"])

    def test_batch_keeps_missing_and_unavailable_separate(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work); target = root / "submissions" / "P01"; target.mkdir(parents=True)
            (target / "solution.py").write_text("def solve(problem): return {}")
            summary = batch(root / "submissions", root / "results", backend="none")
            self.assertEqual(summary["coverage"], {"submitted": 1, "scored": 0, "passed": 0, "total": 13})
            self.assertIsNone(summary["mean_score"])
            self.assertIsNone(summary["subset_mean"])
            self.assertEqual(summary["entries"][0]["status"], "unscored")
            self.assertEqual(summary["entries"][1]["status"], "not_submitted")
            with self.assertRaises(FileExistsError):
                batch(root / "submissions", root / "results", backend="none")

    def test_json_duplicate_keys_and_nonfinite_are_rejected(self):
        with tempfile.TemporaryDirectory() as work:
            path = Path(work) / "bad.json"
            for value in ['{"score":1,"score":2}', '{"score":NaN}']:
                path.write_text(value)
                with self.assertRaises(ValueError):
                    read(path)

    def test_bad_source_does_not_abort_other_batch_tasks(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work); inputs = root / "submissions"
            for tid in ("P01", "P02"):
                (inputs / tid).mkdir(parents=True)
            (inputs / "P01" / "solution.py").write_bytes(b"\xffinvalid utf8")
            (inputs / "P02" / "solution.py").write_text("def solve(problem): return {}")
            result = batch(inputs, root / "results", backend="none")
            self.assertEqual(result["entries"][0]["status"], "submission_invalid")
            self.assertIsNone(result["entries"][0]["score"])
            self.assertIn("UnicodeDecodeError", result["entries"][0]["error"])
            self.assertEqual(result["entries"][1]["status"], "unscored")
            self.assertTrue((root / "results" / "P02.json").is_file())

    def test_web_manifest_matches_actual_report(self):
        manifest = public_manifest((17,))
        case = manifest["tasks"]["P01"]["seeds"]["17"]
        self.assertEqual(case["packet_hash"], self.report["packet_hash"])
        self.assertEqual(case["test_manifest_hash"], self.report["test_manifest_hash"])
        self.assertEqual(manifest["evaluatorFingerprint"], self.report["evaluator_fingerprint"])
        self.assertEqual(case["checks"], [{k: c[k] for k in ("id", "tier", "weight", "critical")} for c in self.report["checks"]])


if __name__ == "__main__":
    unittest.main()

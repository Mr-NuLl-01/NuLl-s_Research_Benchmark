"""Runner eligibility survives CLI re-aggregation; known cohorts cannot mix."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

from nrb_v1.adapters import run_command
from nrb_v1.cli import main
from nrb_v1.grading import grade, summarize
from nrb_v1.provenance import seal
from nrb_v1.registry import module


class SummaryRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reports = [grade(t, module(t).reference_submission(), backend="trusted", timeout=10)
                       for t in ("C01", "C02")]

    def test_cli_resummarization_preserves_actual_runner_disqualification(self):
        # A controlled no-model fixture changes its task file and returns a
        # known reference. The score remains evidence, but is not comparable.
        submission = module("C01").reference_submission()
        source = ("import json,pathlib,sys\np=pathlib.Path(sys.argv[1])\n"
                  "p.write_text(p.read_text()+'\\nmodified fixture')\n"
                  "print(" + repr(json.dumps(submission)) + ")\n")
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "run"
            result = run_command([sys.executable, "-c", source, "{task}"], dest,
                                 selection="C01", model_label="fixture", harness_label="test",
                                 execution="trusted", timeout=10)
            self.assertFalse(result["reports"][0]["comparison_eligible"])
            self.assertEqual(result["reports"][0]["auto_points"], 70)
            out = Path(tmp) / "summary.json"
            self.assertEqual(main(["summarize", "--reports", str(dest / "run.json"),
                                   "--tasks", "C01", "--out", str(out)]), 0)
            summary = json.loads(out.read_text())
            self.assertIsNone(summary["profiles"]["coding"]["automatic_mean_of_70"])
            self.assertEqual(summary["comparison_ineligible_instances"], 1)
            self.assertIn("input_integrity_not_confirmed",
                          summary["task_table"][0]["comparison_ineligibility_reasons"])

    def test_multitask_harness_error_retains_an_incomplete_run_summary(self):
        submission = module("C01").reference_submission()
        source = ("import pathlib,sys\n"
                  "if pathlib.Path(sys.argv[1]).parent.parent.name=='C02': sys.exit(1)\n"
                  "print(" + repr(json.dumps(submission)) + ")\n")
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "run"
            result = run_command([sys.executable, "-c", source, "{task}"], dest,
                                 selection="C01,C02", model_label="fixture", harness_label="test",
                                 execution="trusted", timeout=10)
            self.assertTrue((dest / "run.json").is_file())
            self.assertEqual([r["generation"]["status"] for r in result["reports"]],
                             ["completed", "harness_error"])
            self.assertEqual([r["generation"]["execution_backend"] for r in result["reports"]],
                             ["trusted", "trusted"])
            summary = summarize(result["reports"], "C01,C02")
            self.assertIsNone(summary["profiles"]["coding"]["automatic_mean_of_70"])
            self.assertEqual(summary["comparison_ineligible_instances"], 1)
            self.assertIn("generation_harness_error",
                          summary["task_table"][1]["comparison_ineligibility_reasons"])

    def test_eligibility_cannot_override_modified_input(self):
        report = copy.deepcopy(self.reports[0])
        report.update(comparison_eligible=True, input_integrity={"unchanged": False})
        report["report_hash"] = seal(report)
        summary = summarize([report], "C01")
        self.assertIsNone(summary["profiles"]["coding"]["automatic_mean_of_70"])
        self.assertFalse(summary["task_table"][0]["comparison_eligible"])

    def test_equivalent_integer_and_float_timeout_configuration_can_mix(self):
        reports = copy.deepcopy(self.reports)
        for report, timeout in zip(reports, (120, 120.0)):
            report["generation"]["timeout_seconds"] = timeout
            report["execution"]["timeout_seconds"] = timeout
            report["report_hash"] = seal(report)
        summary = summarize(reports, "C01,C02")
        self.assertEqual(summary["profiles"]["coding"]["automatic_mean_of_70"], 70)
        self.assertIs(type(reports[0]["execution"]["timeout_seconds"]), int)
        self.assertIs(type(reports[1]["execution"]["timeout_seconds"]), float)

    def test_each_recorded_configuration_conflict_is_rejected(self):
        for section, key, left, right in (
            ("generation", "model_label", "model-a", "model-b"),
            ("generation", "harness_label", "tools", "response-only"),
            ("generation", "timeout_seconds", 900, 1800),
            ("generation", "metadata", {"skills": "a"}, {"skills": "b"}),
            ("generation", "execution_backend", "trusted", "docker"),
            ("execution", "backend", "trusted", "docker"),
            ("execution", "image_id", "sha256:a", "sha256:b"),
            ("execution", "timeout_seconds", 10, 20),
        ):
            with self.subTest(field=section + "." + key):
                reports = copy.deepcopy(self.reports)
                for report, value in zip(reports, (left, right)):
                    report[section][key] = value
                    report["report_hash"] = seal(report)
                with self.assertRaisesRegex(ValueError, "Mixed comparison cohort"):
                    summarize(reports, "C01,C02")

    def test_missing_identity_is_reported_without_fabricating_it(self):
        reports = copy.deepcopy(self.reports)
        reports[0]["generation"].update(model_label="fixture", harness_label="test")
        reports[0]["report_hash"] = seal(reports[0])
        summary = summarize(reports, "C01,C02")
        self.assertEqual(summary["profiles"]["coding"]["automatic_mean_of_70"], 70)
        self.assertFalse(summary["cohort_check"]["generation_identity_complete"])
        self.assertIn("generation.model_label", summary["cohort_check"]["partially_recorded_fields"])
        self.assertIsNone(summary["task_table"][0]["comparison_eligible"])

    def test_consistent_declared_eligible_reports_keep_the_mean(self):
        reports = copy.deepcopy(self.reports)
        for report in reports:
            report.update(comparison_eligible=True, input_integrity={"unchanged": True})
            report["generation"].update(model_label="fixture", harness_label="test", timeout_seconds=900)
            report["report_hash"] = seal(report)
        summary = summarize(reports, "C01,C02")
        self.assertEqual(summary["profiles"]["coding"]["automatic_mean_of_70"], 70)
        self.assertEqual(summary["comparison_ineligible_instances"], 0)
        self.assertTrue(summary["cohort_check"]["generation_identity_complete"])
        self.assertTrue(all(row["comparison_eligible"] for row in summary["task_table"]))


if __name__ == "__main__": unittest.main()

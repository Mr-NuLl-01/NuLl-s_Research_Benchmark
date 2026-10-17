"""Offline adapter contracts, fresh-run handling, and export leakage checks.

Mocking an optional framework's callback does not validate that framework's
runtime. No model APIs are called by these tests.
"""
from __future__ import annotations

import importlib.util
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from nrb.adapters import (IncompleteGrade, ProvenanceError, candidate_sha256,
                          export_harbor, export_promptfoo, harbor_verify,
                          inspect_samples, promptfoo_assertion, promptfoo_command_provider,
                          promptfoo_mock_provider, score_output, summarize_inspect_log,
                          summarize_promptfoo_results)
from nrb.harness import run_command, unwrap_output


def fixture_case():
    return {"id": "NRB01", "title": "Synthetic adapter fixture", "domain": "test",
            "seed": 7, "benchmark_version": "fixture", "case_hash": "fixture-hash",
            "prompt": "Return a submission. This is synthetic test data.",
            "files": {"data/input.csv": "x,y\n1,2\n"},
            "required_artifacts": [],
            "expected": {"secret": "REFERENCE_ONLY_SENTINEL"},
            "rubric": [{"id": f"q{i}", "description": "fixture quality", "max": 10} for i in range(3)]}


def fixture_submission():
    return {"task_id": "NRB01", "answer": {"value": 2}, "artifacts": {}}


def fixture_report(points=35, complete=True):
    return {"task_id": "NRB01", "auto_points": points, "auto_max": 70,
            "auto_percent": points / 70 * 100 if complete else None,
            "coverage": 1 if complete else .5, "critical_failures": [],
            "checks": [], "review_pending": True, "total": None}


class CallbackContracts(unittest.TestCase):
    def setUp(self):
        self.case = fixture_case()
        self.context = {"vars": {"task_id": "NRB01", "seed": 7, "execution": "none",
                                 "candidate_sha256": candidate_sha256(self.case)}}

    def test_single_core_scorer_is_used_without_rescaling_to_full_score(self):
        expected = fixture_report()
        with patch("nrb.core.get_case", return_value=self.case), patch("nrb.core.grade_submission", return_value=expected) as grader:
            result = promptfoo_assertion("model output", self.context)
        self.assertEqual(result["score"], .5)
        self.assertFalse(result["pass"])
        self.assertIn('"total": null', result["reason"])
        grader.assert_called_once_with(self.case, "model output", execution="none")

    def test_provenance_drift_fails_before_scoring(self):
        with patch("nrb.core.get_case", return_value=self.case), patch("nrb.core.grade_submission") as grader:
            with self.assertRaises(ProvenanceError):
                score_output("NRB01", 7, "output", candidate_hash="stale")
        grader.assert_not_called()

    def test_incomplete_grading_is_an_error_not_zero_model_accuracy(self):
        with patch("nrb.core.get_case", return_value=self.case), patch("nrb.core.grade_submission", return_value=fixture_report(complete=False)):
            with self.assertRaises(IncompleteGrade):
                promptfoo_assertion("output", self.context)

    def test_offline_mock_explicitly_identifies_itself(self):
        with patch("nrb.core.get_case", return_value=self.case), patch("nrb.core.reference_submission", return_value=fixture_submission()):
            output = promptfoo_mock_provider("prompt", {"config": {"mode": "oracle"}}, self.context)
        self.assertEqual(json.loads(output["output"]), fixture_submission())
        self.assertTrue(output["metadata"]["not_model_performance"])
        self.assertNotIn("tokenUsage", output)
        self.assertNotIn("cost", output)

    def test_inspect_records_do_not_contain_expected_answers(self):
        with patch("nrb.core.build_suite", return_value=[self.case]):
            records = inspect_samples(7)
        self.assertEqual(records[0]["target"], "")
        self.assertNotIn("REFERENCE_ONLY_SENTINEL", json.dumps(records))
        self.assertEqual(records[0]["metadata"]["candidate_sha256"], candidate_sha256(self.case))

    def test_promptfoo_cli_provider_runs_real_offline_subprocess(self):
        with tempfile.TemporaryDirectory() as temp:
            code = f"import sys; sys.stdin.read(); print({json.dumps(fixture_submission())!r})"
            config = {"config": {"command": [sys.executable, "-c", code], "workdir_root": temp}}
            with patch("nrb.core.get_case", return_value=self.case):
                response = promptfoo_command_provider("prompt", config, self.context)
            self.assertEqual(json.loads(response["output"]), fixture_submission())
            self.assertEqual(response["metadata"]["nrb_run"]["status"], "completed")
            self.assertIsNone(response["metadata"]["nrb_run"]["usage"])

    def test_promptfoo_cli_missing_executable_is_not_a_model_output(self):
        with tempfile.TemporaryDirectory() as temp:
            config = {"config": {"command": ["nrb-definitely-missing-command"], "workdir_root": temp}}
            with patch("nrb.core.get_case", return_value=self.case):
                with self.assertRaises(RuntimeError):
                    promptfoo_command_provider("prompt", config, self.context)

    def test_inspect_summary_does_not_hide_missing_tasks(self):
        report = fixture_report()
        report["seed"] = 7
        sample = SimpleNamespace(id="NRB01", epoch=1,
                                 scores={"nrb_automatic": SimpleNamespace(metadata={"nrb_report": report})})
        log = SimpleNamespace(samples=[sample], status="success", invalidated=False)
        summary = summarize_inspect_log(log)
        self.assertFalse(summary["complete_auto"])
        self.assertIsNone(summary["auto_macro_percent"])
        self.assertEqual(len(summary["missing_tasks"]), 9)

    def test_inspect_summary_excludes_log_with_provider_error(self):
        log = SimpleNamespace(samples=[], status="error", invalidated=False)
        summary = summarize_inspect_log(log)
        self.assertFalse(summary["complete_auto"])
        self.assertEqual(summary["inspect_status"], "error")

    def test_inspect_summary_preserves_recorded_identity_and_generation_settings(self):
        spec = SimpleNamespace(model="example/model-v1", packages={"inspect_ai": "0.3.281"},
                               task="null_research", task_args={"seed": 7, "execution": "docker"},
                               model_args={"api_key": "private-fixture", "temperature": .25},
                               model_generate_config={"max_tokens": 8000}, eval_id="fixture-run")
        log = SimpleNamespace(samples=[], status="success", invalidated=False, eval=spec,
                              plan=SimpleNamespace(config={"temperature": .25},
                                                   steps=[{"solver": "generate", "params": {}}]))
        result = summarize_inspect_log(log)
        self.assertEqual(result["model_label"], "example/model-v1")
        self.assertEqual(result["harness_label"], "inspect_ai")
        self.assertEqual(result["metadata"]["harness_version"], "0.3.281")
        self.assertEqual(result["metadata"]["model_generate_config"]["max_tokens"], 8000)
        self.assertEqual(result["metadata"]["model_args"]["api_key"], "[REDACTED]")
        self.assertNotIn("seed", result["metadata"]["task_args"])
        self.assertEqual(result["source_log"]["task_args"]["seed"], 7)
        self.assertTrue(result["metadata_incomplete"])
        self.assertIsNone(result["metadata"]["model_version"])

    def test_promptfoo_runtime_redaction_requires_complete_matching_logged_input(self):
        from nrb.core import get_case, candidate_prompt
        case = get_case("NRB01", 0)
        variables = {"task_id": case["id"], "seed": 0, "execution": "none",
                     "candidate_sha256": candidate_sha256(case), "prompt": candidate_prompt(case)}
        grade = promptfoo_assertion('{"task_id":"NRB01","answer":{},"artifacts":{}}', {"vars": variables})
        # Observed in actual promptfoo 0.124.1 GitHub Actions results.json: a
        # SHA-looking vars value becomes [REDACTED], while vars.prompt and the
        # canonical report survive. Do not turn off framework redaction.
        variables["candidate_sha256"] = "[REDACTED]"
        row = {"vars": variables, "provider": {"id": "example:model-v1", "label": "arm-a"},
               "promptIdx": 0, "score": 0, "success": False, "failureReason": 1,
               "gradingResult": {"componentResults": [grade]}}
        data = {"results": {"stats": {"successes": 0, "failures": 1, "errors": 0}, "results": [row]},
                "metadata": {"promptfooVersion": "0.124.1"},
                "config": {"providers": [{"id": "example:model-v1", "label": "arm-a",
                                            "config": {"temperature": .25, "apiKey": "private-fixture"}}],
                           "prompts": ["{{prompt}}"]},
                "runtimeOptions": {"repeat": 1, "maxConcurrency": 1, "cache": False}}
        result = summarize_promptfoo_results(data)
        self.assertEqual(result["provenance"]["hash_recovered_from_full_logged_prompt"], ["NRB01"])
        self.assertEqual(result["model_label"], "example:model-v1")
        self.assertEqual(result["harness_label"], "promptfoo")
        self.assertEqual(result["metadata"]["harness_version"], "0.124.1")
        self.assertEqual(result["metadata"]["provider"]["config"]["temperature"], .25)
        self.assertEqual(result["metadata"]["provider"]["config"]["apiKey"], "[REDACTED]")
        self.assertTrue(result["metadata_incomplete"])
        for mutation in ({"prompt": "changed input"}, {"prompt": None},
                         {"candidate_sha256": "incorrect-unredacted-hash"}):
            changed = copy.deepcopy(data)
            changed["results"]["results"][0]["vars"].update(mutation)
            with self.subTest(mutation=mutation), self.assertRaises(ProvenanceError):
                summarize_promptfoo_results(changed)
        changed = copy.deepcopy(data)
        changed["results"]["results"][0]["gradingResult"]["componentResults"][0]["metadata"]["nrb_report"]["case_hash"] = "different-case"
        with self.assertRaises(ProvenanceError):
            summarize_promptfoo_results(changed)

    def test_promptfoo_summary_uses_canonical_reports_and_full_denominator(self):
        from nrb.core import build_suite
        rows = []
        for case in build_suite(0):
            variables = {"task_id": case["id"], "seed": 0, "execution": "none",
                         "candidate_sha256": candidate_sha256(case)}
            output = json.dumps({"task_id": case["id"], "answer": {}, "artifacts": {}})
            grade = promptfoo_assertion(output, {"vars": variables})
            rows.append({"vars": variables, "provider": {"id": "fixture", "label": "empty"},
                         "promptIdx": 0, "score": grade["score"], "success": False,
                         "failureReason": 1, "gradingResult": {"componentResults": [grade]}})
        data = {"results": {"stats": {"successes": 0, "failures": 10, "errors": 0}, "results": rows}}
        result = summarize_promptfoo_results(data)
        self.assertTrue(result["complete_auto"])
        self.assertEqual(result["auto_macro_percent"], 0)
        # Simulate framework assertion metadata stripping: the canonical reason
        # still carries an identical report, with no second scientific scorer.
        for row in rows:
            row["gradingResult"]["componentResults"][0].pop("metadata")
        self.assertEqual(summarize_promptfoo_results(data)["auto_macro_percent"], 0)
        rows.pop()
        result = summarize_promptfoo_results(data)
        self.assertFalse(result["complete_auto"])
        self.assertIsNone(result["auto_macro_percent"])

    def test_promptfoo_summary_does_not_average_repetitions_or_runtime_errors(self):
        row = {"vars": {"task_id": "NRB01", "seed": 0}, "provider": {"id": "fixture"},
               "promptIdx": 0, "failureReason": 2, "response": None}
        data = {"results": {"stats": {"errors": 1}, "results": [row]}}
        self.assertFalse(summarize_promptfoo_results(data)["complete_auto"])
        data["results"]["results"].append(row)
        with self.assertRaises(ValueError):
            summarize_promptfoo_results(data)


class ExportContracts(unittest.TestCase):
    def test_promptfoo_yaml_is_valid_json_subset_and_roundtrip_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "export"
            report = export_promptfoo([fixture_case()], dest, execution="none")
            config = json.loads((dest / "promptfooconfig.yaml").read_text())
            self.assertEqual(report["task_count"], 1)
            self.assertEqual(config["tests"][0]["vars"]["seed"], 7)
            self.assertEqual(config["defaultTest"]["assert"][0]["type"], "python")
            self.assertNotIn("REFERENCE_ONLY_SENTINEL", (dest / "promptfooconfig.yaml").read_text())
            with self.assertRaises(FileExistsError):
                export_promptfoo([fixture_case()], dest)

    def test_harbor_candidate_build_has_no_evaluator_or_reference(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp) / "harbor"
            reference = fixture_submission()
            reference["answer"]["sentinel"] = "REFERENCE_ONLY_SENTINEL"
            with patch("nrb.core.reference_submission", return_value=reference):
                export_harbor([fixture_case()], dest)
            task = dest / "nrb01"
            environment = task / "environment"
            for path in environment.rglob("*"):
                if path.is_file():
                    self.assertNotIn("REFERENCE_ONLY_SENTINEL", path.read_text())
            self.assertFalse((environment / "nrb").exists())
            self.assertFalse((environment / "tests").exists())
            self.assertTrue((task / "tests" / "grader" / "nrb" / "core.py").is_file())
            self.assertIn("REFERENCE_ONLY_SENTINEL", (task / "solution" / "reference.json").read_text())
            dockerfile = (environment / "Dockerfile").read_text()
            self.assertIn("COPY packet/ /app/", dockerfile)
            self.assertNotIn("COPY . ", dockerfile)
            verifier = (task / "tests" / "Dockerfile").read_text()
            self.assertIn("COPY grader/ /grader/", verifier)
            self.assertIn("chmod -R go-rwx /grader /tests", verifier)
            config = (task / "task.toml").read_text()
            self.assertIn('environment_mode = "separate"', config)
            self.assertIn('network_mode = "no-network"', config)
            self.assertIn('schema_version = "1.4"', config)
            try:
                import tomllib
            except ImportError:
                pass
            else:
                parsed = tomllib.loads(config)
                self.assertEqual(parsed["verifier"]["environment"]["network_mode"], "no-network")
                self.assertEqual(parsed["artifacts"], ["/app/"])

    def test_harbor_verifier_refuses_host_checkout(self):
        with self.assertRaises(IncompleteGrade):
            harbor_verify()

    def test_harbor_smoke_checker_requires_report_and_framework_agreement(self):
        path = Path(__file__).resolve().parents[1] / "adapters" / "harbor" / "smoke.py"
        spec = importlib.util.spec_from_file_location("nrb_harbor_smoke_contract", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            job = Path(temp) / "job"
            trial = job / "nrb01_fixture"
            verifier = trial / "verifier"
            verifier.mkdir(parents=True)
            result = {"exception_info": None, "verifier_environment_mode": "separate",
                      "verifier_result": {"rewards": {"reward": 1.0}}}
            (trial / "result.json").write_text(json.dumps(result))
            report = fixture_report(points=70)
            report.update(seed=0, adapter="harbor", input_integrity={"unchanged": True},
                          comparison_eligible=True,
                          verifier_log_permissions={"owner_uid": 0, "mode": "0o755"})
            (verifier / "report.json").write_text(json.dumps(report))
            (verifier / "reward.txt").write_text("1\n")
            self.assertTrue(module.check_job(job, ["NRB01"])["passed"])
            report["coverage"] = 0.5
            (verifier / "report.json").write_text(json.dumps(report))
            self.assertFalse(module.check_job(job, ["NRB01"])["passed"])
            (verifier / "report.json").unlink()
            self.assertFalse(module.check_job(job, ["NRB01"])["passed"])


class CLIEnvelopeContracts(unittest.TestCase):
    def test_cli_envelopes_require_explicit_format(self):
        payload = json.dumps(fixture_submission())
        wrapped = json.dumps({"result": payload, "usage": {"input_tokens": 10}, "total_cost_usd": .1})
        result, usage, cost = unwrap_output(wrapped, "claude-json")
        self.assertEqual(result, payload)
        self.assertEqual(usage["reported"]["input_tokens"], 10)
        self.assertEqual(cost, .1)
        self.assertEqual(unwrap_output(wrapped, "plain"), (wrapped, None, None))

    def test_codex_jsonl_extracts_last_agent_message_and_reported_usage(self):
        payload = json.dumps(fixture_submission())
        events = [{"type": "item.completed", "item": {"type": "agent_message", "text": "progress"}},
                  {"type": "item.completed", "item": {"type": "agent_message", "text": payload}},
                  {"type": "turn.completed", "usage": {"input_tokens": 20, "output_tokens": 30}}]
        result, usage, cost = unwrap_output("\n".join(map(json.dumps, events)), "codex-jsonl")
        self.assertEqual(result, payload)
        self.assertEqual(usage["reported"]["output_tokens"], 30)
        self.assertIsNone(cost)

    def test_gemini_reported_stats_and_errors(self):
        payload = json.dumps({"response": "{}", "stats": {"model": {"tokens": 20}}})
        output, usage, cost = unwrap_output(payload, "gemini-json")
        self.assertEqual(output, "{}")
        self.assertEqual(usage["source"], "gemini-cli.stats")
        self.assertIsNone(cost)
        with self.assertRaises(ValueError):
            unwrap_output('{"error":{"message":"auth failure"}}', "gemini-json")


class NativeRunnerContracts(unittest.TestCase):
    def run_case(self, code, **kwargs):
        temp = tempfile.TemporaryDirectory(prefix="nrb-adapter-test-")
        self.addCleanup(temp.cleanup)
        path = Path(temp.name) / "candidate"
        return run_command(fixture_case(), [sys.executable, "-c", code], path, **kwargs), path

    def test_stdout_submission_and_manifest(self):
        submission = json.dumps(fixture_submission())
        code = f"import sys; sys.stdin.read(); print({submission!r})"
        result, path = self.run_case(code)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["submission"], fixture_submission())
        self.assertEqual(result["submission_source"], "stdout")
        self.assertTrue(result["input_integrity"]["unchanged"])
        self.assertIsNone(result["usage"])
        self.assertIsNone(result["cost_usd"])
        self.assertTrue(Path(result["logs_dir"]).is_dir())
        self.assertNotEqual(Path(result["logs_dir"]), path)
        with self.assertRaises(FileExistsError):
            run_command(fixture_case(), [sys.executable, "-c", code], path)

    def test_written_submission_takes_precedence_over_progress_stdout(self):
        text = json.dumps(fixture_submission())
        code = f"from pathlib import Path; Path('submission.json').write_text({text!r}); print('finished')"
        result, _ = self.run_case(code)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["submission_source"], "file")

    def test_explicit_cli_error_cannot_be_overridden_by_valid_submission_file(self):
        envelopes = [("claude-json", {"is_error": True, "result": "provider failed"}),
                     ("codex-jsonl", {"type": "turn.failed", "error": {"message": "provider failed"}}),
                     ("gemini-json", {"error": {"message": "provider failed"}})]
        for format_name, envelope in envelopes:
            with self.subTest(format=format_name):
                text = json.dumps(fixture_submission())
                code = (f"from pathlib import Path; Path('submission.json').write_text({text!r}); "
                        f"print({json.dumps(envelope)!r})")
                result, _ = self.run_case(code, stdout_format=format_name)
                self.assertEqual(result["exit_code"], 0)
                self.assertEqual(result["status"], "command_error")
                self.assertEqual(result["infra_error"], "cli_reported_error")
                self.assertIsNone(result["submission"])
                self.assertIsNotNone(result["envelope_error"])

    def test_malformed_codex_item_is_recorded_instead_of_crashing_suite(self):
        result, _ = self.run_case('print(\'{"type":"item.completed","item":null}\')',
                                  stdout_format="codex-jsonl")
        self.assertEqual(result["status"], "invalid_submission")
        self.assertIn("item object", result["envelope_error"])
        self.assertIsNone(result["submission"])

    def test_missing_executable_is_infrastructure_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            result = run_command(fixture_case(), ["nrb-definitely-missing-command"], Path(temp) / "candidate")
        self.assertEqual(result["status"], "infrastructure_error")
        self.assertEqual(result["infra_error"], "executable_not_found")
        self.assertIsNone(result["submission"])

    def test_malformed_json_and_nonzero_exit_are_distinct(self):
        malformed, _ = self.run_case("print('not json')")
        failed, _ = self.run_case("import sys; sys.exit(3)")
        self.assertEqual(malformed["status"], "invalid_submission")
        self.assertEqual(failed["status"], "command_error")
        self.assertEqual(failed["exit_code"], 3)

    def test_input_changes_and_missing_files_are_detected(self):
        text = json.dumps(fixture_submission())
        code = ("from pathlib import Path; Path('data/input.csv').write_text('changed'); "
                f"Path('packet_manifest.json').unlink(); print({text!r})")
        result, _ = self.run_case(code)
        self.assertEqual(result["protocol_violation"], "candidate_input_modified")
        self.assertIn("data/input.csv", result["input_integrity"]["changed_files"])
        self.assertIn("packet_manifest.json", result["input_integrity"]["missing_files"])

    @unittest.skipUnless(os.name == "posix", "POSIX symlink behavior")
    def test_submission_symlink_is_not_followed(self):
        result, _ = self.run_case("from pathlib import Path; Path('submission.json').symlink_to('/etc/passwd')")
        self.assertEqual(result["status"], "invalid_submission")
        self.assertIn("symlink", result["output_error"])

    @unittest.skipUnless(os.name == "posix", "POSIX process group behavior")
    def test_timeout_kills_descendant_process(self):
        code = ("import subprocess,sys,time; "
                "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
                "print(p.pid,flush=True); time.sleep(60)")
        result, _ = self.run_case(code, timeout=.3)
        self.assertEqual(result["status"], "timeout")
        self.assertLess(result["elapsed_seconds"], 5)
        pid = int((Path(result["logs_dir"]) / "stdout.txt").read_text().strip())
        proc_stat = Path(f"/proc/{pid}/stat")
        if proc_stat.exists():
            # The process may briefly remain an unreaped zombie owned by init.
            for _ in range(10):
                if not proc_stat.exists() or proc_stat.read_text().split()[2] == "Z":
                    break
                time.sleep(.02)
            self.assertTrue(not proc_stat.exists() or proc_stat.read_text().split()[2] == "Z")

    def test_known_env_credentials_are_redacted_in_transcripts(self):
        token = "adapter_fixture_private_value_938491"
        with patch.dict(os.environ, {"NRB_TEST_API_KEY": token}):
            result, _ = self.run_case("import os; print(os.environ['NRB_TEST_API_KEY'])")
        output = (Path(result["logs_dir"]) / "stdout.txt").read_text()
        self.assertNotIn(token, output)
        self.assertIn("[REDACTED]", output)

    def test_credential_flags_and_unsafe_reuse_are_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                run_command(fixture_case(), ["agent", "--api-key", "secret"], Path(temp) / "candidate")


if __name__ == "__main__":
    unittest.main()

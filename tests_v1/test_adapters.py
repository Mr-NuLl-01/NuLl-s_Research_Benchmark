"""V1 adapter contracts plus real optional framework smoke checks.

No model APIs are called. Missing optional dependencies are explicit skips, not
runtime-validation passes. Harbor schema checks do not execute Docker.
"""
from __future__ import annotations
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from nrb_v1.adapters import (IncompleteGrade, ProvenanceError, export, export_harbor,
    inspect_samples, promptfoo_assertion, score_output, summarize_inspect_log,
    summarize_promptfoo_results)
from nrb_v1.packets import candidate
from nrb_v1.provenance import fingerprint, identity, seal, validate_report
from nrb_v1.registry import module

REPO=Path(__file__).resolve().parents[1]


def load_script(name, filename):
    specification=importlib.util.spec_from_file_location(name,REPO/"adapters/v1"/filename)
    loaded=importlib.util.module_from_spec(specification)
    specification.loader.exec_module(loaded)
    return loaded


def variables(task_id="C01",seed=17,execution="trusted"):
    packet=candidate(task_id,seed)
    return {"task_id":task_id,"seed":seed,"prompt":packet["content"],"packet_hash":packet["packet_hash"],
            "evaluator_identity":identity(),"execution":execution}


def promptfoo_row(task_id="C01",seed=17):
    v=variables(task_id,seed)
    assertion=promptfoo_assertion(json.dumps({"task_id":task_id,"answer":{},"artifacts":{}}),{"vars":v})
    return {"vars":v,"provider":{"id":"file://empty.py","label":"empty-validation"},"promptIdx":0,
            "score":assertion["score"],"success":assertion["pass"],"failureReason":1,
            "response":{"metadata":{"nrb_mock":True}},
            "gradingResult":{"componentResults":[assertion]}}


def promptfoo_data(rows):
    return {"results":{"stats":{"successes":0,"failures":len(rows),"errors":0},"results":rows},
            "metadata":{"promptfooVersion":"0.124.1"},
            "config":{"providers":[{"id":"file://empty.py","config":{"max_tokens":1024,"api_key":"synthetic-credential"}}]}}


class AdapterCoreContracts(unittest.TestCase):
    def test_candidate_samples_are_blank_target_and_packet_bound(self):
        records=inspect_samples("coding",17)
        self.assertEqual(len(records),10)
        for record in records:
            self.assertEqual(record["target"],"")
            self.assertEqual(set(record),{"id","input","target","metadata"})
            self.assertEqual(record["metadata"]["packet_hash"],fingerprint(record["input"].encode()))
            self.assertEqual(record["metadata"]["evaluator_identity"],identity())
            self.assertNotIn('"expected"',record["input"])
        with self.assertRaises(ValueError):inspect_samples("research",17)

    def test_real_grade_partial_score_and_incomplete_manual_total(self):
        v=variables()
        reference=module("C01").reference_submission()
        positive=score_output("C01",17,json.dumps(reference),"trusted",v["packet_hash"],v["evaluator_identity"])
        self.assertEqual(positive["auto_points"],70)
        self.assertEqual(positive["completion_status"],"pending_review")
        self.assertIsNone(positive["total"])
        self.assertIsNone(positive["review_points"])
        negative=module("C01").mutants()["duplicate_first"]
        result=promptfoo_assertion(json.dumps(negative),{"vars":v})
        self.assertAlmostEqual(result["score"],55/70)
        self.assertFalse(result["pass"])
        report=result["metadata"]["nrb_v1_report"]
        validate_report(report)
        self.assertEqual(report["auto_points"],55)
        self.assertEqual(report["completion_status"],"failed")
        self.assertIsNone(report["total"])
        self.assertIn(json.dumps(report,ensure_ascii=False),result["reason"])

    def test_invalid_envelope_scores_zero_but_unavailable_execution_is_unscored(self):
        report=score_output("C01",17,"not a JSON submission",execution="none")
        self.assertEqual(report["auto_points"],0)
        self.assertEqual(report["auto_scored_max"],70)
        self.assertIsNotNone(report["invalid_submission"])
        self.assertEqual(report["completion_status"],"failed")
        v=variables(execution="none")
        with self.assertRaises(IncompleteGrade):
            promptfoo_assertion(json.dumps(module("C01").reference_submission()),{"vars":v})

    def test_provenance_drift_rejected_before_actual_grading(self):
        v=variables()
        for kwargs in ({"packet_hash":"changed"},{"evaluator_identity":dict(v["evaluator_identity"],evaluator_digest="0"*64)}):
            with self.subTest(kwargs=kwargs),patch("nrb_v1.adapters.grade") as grader:
                with self.assertRaises(ProvenanceError):score_output("C01",17,"{}",**kwargs)
                grader.assert_not_called()

    def test_promptfoo_summary_preserves_denominator_and_generation_budget(self):
        rows=[promptfoo_row(task_id) for task_id in [f"C{i:02d}" for i in range(1,11)]]
        result=summarize_promptfoo_results(promptfoo_data(rows))
        self.assertEqual(len(result["reports"]),10)
        summary=result["summary"]
        self.assertEqual(summary["missing_tasks"],[])
        self.assertEqual(summary["profiles"]["coding"]["automatic_mean_of_70"],0)
        self.assertIsNone(summary["profiles"]["coding"]["mean_total"])
        self.assertTrue(summary["not_model_performance"])
        configuration=summary["provider_config"][0]["config"]
        self.assertEqual(configuration["max_tokens"],1024)
        self.assertEqual(configuration["api_key"],"[REDACTED]")
        partial=summarize_promptfoo_results(promptfoo_data(rows[:-1]))["summary"]
        self.assertEqual(partial["missing_tasks"],["C10"])
        self.assertIsNone(partial["profiles"]["coding"]["automatic_mean_of_70"])

    def test_promptfoo_redaction_recovery_is_bound_to_full_logged_prompt(self):
        row=promptfoo_row()
        row["vars"]["packet_hash"]="[REDACTED]"
        row["vars"]["evaluator_identity"]["evaluator_digest"]="[REDACTED]"
        self.assertEqual(len(summarize_promptfoo_results(promptfoo_data([row]))["reports"]),1)
        for label,mutate in (
            ("prompt",lambda r:r["vars"].update(prompt="changed")),
            ("packet",lambda r:r["vars"].update(packet_hash="incorrect-unredacted")),
            ("scalar",lambda r:r.update(score=1)),
            ("huge_scalar",lambda r:r.update(score=10**400)),
            ("boolean_scalar",lambda r:r.update(score=True)),
            ("report",lambda r:r["gradingResult"]["componentResults"][0]["metadata"]["nrb_v1_report"].update(auto_points=70)),
        ):
            with self.subTest(tamper=label):
                changed=copy.deepcopy(row);mutate(changed)
                with self.assertRaises(ValueError):summarize_promptfoo_results(promptfoo_data([changed]))
        data=promptfoo_data([row,row])
        with self.assertRaises(ValueError):summarize_promptfoo_results(data)

    def test_inspect_summary_preserves_partial_report_and_redacts_only_credentials(self):
        report=score_output("C01",17,{"task_id":"C01","artifacts":{},"answer":{}},"none")
        sample=SimpleNamespace(id="C01",epoch=1,metadata=variables(),
                               scores={"v1":SimpleNamespace(value=0,metadata={"nrb_v1_report":report})})
        log=SimpleNamespace(samples=[sample],invalidated=False,status="success",
                            eval={"model":"mockllm/model","model_generate_config":{"max_tokens":2048},
                                  "model_args":{"api_key":"synthetic-secret"}})
        converted=summarize_inspect_log(log)
        self.assertEqual(converted["reports"],[report])
        summary=converted["summary"]
        self.assertEqual(len(summary["missing_tasks"]),9)
        self.assertIsNone(summary["profiles"]["coding"]["automatic_mean_of_70"])
        self.assertEqual(summary["metadata"]["model_generate_config"]["max_tokens"],2048)
        self.assertEqual(summary["metadata"]["model_args"]["api_key"],"[REDACTED]")
        self.assertTrue(summary["not_model_performance"])
        for invalid_scalar in (1,10**400,True):
            sample.scores["v1"].value=invalid_scalar
            with self.assertRaises(ProvenanceError):summarize_inspect_log(log)
        sample.scores["v1"].value=0
        log.invalidated=True
        with self.assertRaises(ProvenanceError):summarize_inspect_log(log)

    def test_exports_have_no_default_oracle_and_use_exact_candidate_bytes(self):
        harbor=load_script("v1_harbor_export_contract","harbor_smoke.py")
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            export("jsonl",root/"jsonl",selection="C01,C04",seed=17)
            records=[json.loads(line) for line in (root/"jsonl/tasks.jsonl").read_text().splitlines()]
            self.assertEqual([r["id"] for r in records],["C01","C04"])
            self.assertTrue(all(r["target"]=="" for r in records))
            export("promptfoo",root/"promptfoo",selection="C01",seed=17)
            config=json.loads((root/"promptfoo/promptfooconfig.yaml").read_text())
            self.assertEqual(config["providers"][0]["label"],"offline-empty-smoke")
            self.assertEqual(config["tests"][0]["vars"]["prompt"],candidate("C01")["content"])
            manifest=export_harbor(root/"harbor",selection="C01,C04",seed=17)
            self.assertFalse(manifest["include_oracle"])
            for task_id in ("C01","C04"):
                directory=root/"harbor"/task_id.lower()
                self.assertFalse((directory/"solution").exists())
                self.assertEqual(set(harbor._snapshot(directory/"environment")),{"Dockerfile",".dockerignore","packet/task.md"})
                self.assertEqual((directory/"environment/packet/task.md").read_text(),candidate(task_id)["content"])
                self.assertTrue((directory/"tests/grader/nrb_v1/grading.py").is_file())
                self.assertIn("chmod -R go-rwx",(directory/"tests/Dockerfile").read_text())
            before=harbor._snapshot(root/"harbor/c01/environment")
            injected=harbor.inject_oracles_for_validation(root/"harbor",selection="C01,C04",seed=17)
            self.assertTrue(injected["candidate_environment_unchanged"])
            self.assertEqual(before,harbor._snapshot(root/"harbor/c01/environment"))
            oracle=json.loads((root/"harbor/c01/solution/reference.json").read_text())
            self.assertEqual(oracle,module("C01").reference_submission())
            with self.assertRaises(FileExistsError):export_harbor(root/"harbor",selection="C01")

    def test_fresh_exports_reject_dangling_destination_symlinks(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            destination=root/"alias"
            target=root/"not-created"
            destination.symlink_to(target,target_is_directory=True)
            with self.assertRaises(FileExistsError):export("jsonl",destination,selection="C01")
            self.assertFalse(target.exists())

    def test_harbor_trial_checker_requires_canonical_evidence_not_reward_only(self):
        harbor=load_script("v1_harbor_trial_contract","harbor_smoke.py")
        report=score_output("C01",17,module("C01").reference_submission(),"trusted")
        report.update(adapter="harbor",input_integrity={"unchanged":True},comparison_eligible=True,
                      verifier_log_permissions={"owner_uid":0,"mode":"0o755"})
        report["report_hash"]=seal(report)
        # A synthetic trial-directory fixture, never represented as Docker execution.
        with tempfile.TemporaryDirectory() as temp:
            job=Path(temp);trial=job/"trial";(trial/"verifier").mkdir(parents=True)
            (trial/"result.json").write_text(json.dumps({"exception_info":None,"verifier_environment_mode":"separate", "verifier_result":{"rewards":{"reward":1.0}}}))
            report_path=trial/"verifier/report.json";report_path.write_text(json.dumps(report))
            reward_path=trial/"verifier/reward.txt";reward_path.write_text("1\n")
            self.assertTrue(harbor.check_job(job,["C01"])["passed"])
            reward_path.write_text("0\n")
            self.assertFalse(harbor.check_job(job,["C01"])["passed"])
            reward_path.write_text("1\n");changed=copy.deepcopy(report);changed["auto_points"]=69
            report_path.write_text(json.dumps(changed))
            self.assertFalse(harbor.check_job(job,["C01"])["passed"])


class MalformedEnvelopeRegression(unittest.TestCase):
    def test_nonfinite_or_invalid_unicode_envelopes_are_candidate_failures(self):
        from nrb_v1.adapters import score_output
        for bad in ('NaN','Infinity','-Infinity','"\\ud800"'):
            with self.subTest(value=bad):
                output='{"task_id":"C01","artifacts":{},"answer":{"bad":'+bad+'}}'
                report=score_output('C01',17,output,'none')
                self.assertEqual(report['auto_points'],0)
                self.assertIsNotNone(report['invalid_submission'])


@unittest.skipUnless(importlib.util.find_spec("inspect_ai"),"inspect-ai absent: real runtime not validated")
class RealInspectRuntime(unittest.TestCase):
    def test_task_construction_and_actual_mock_eval(self):
        adapter=load_script("v1_inspect_actual_runtime","inspect_eval.py")
        task=adapter.null_research_v1(seed=17,selection="coding",execution="none")
        self.assertEqual(len(task.dataset),10)
        self.assertTrue(all(sample.target=="" for sample in task.dataset))
        with tempfile.TemporaryDirectory() as temp:
            report=adapter.run_smoke(Path(temp)/"run")
            self.assertTrue(report["passed"])
            self.assertEqual(report["api_provider_calls"],0)
            self.assertEqual([e["score"] for e in report["entries"]],[1,0,None])


@unittest.skipUnless(importlib.util.find_spec("harbor"),"Harbor absent: real schema runtime not validated")
class RealHarborSchemaRuntime(unittest.TestCase):
    def test_all_ten_exports_parse_actual_task_config(self):
        harbor=load_script("v1_harbor_actual_schema","harbor_smoke.py")
        with tempfile.TemporaryDirectory() as temp:
            report=harbor.run_smoke(Path(temp)/"run",selection="coding",schema_only=True)
            self.assertTrue(report["passed"])
            self.assertFalse(report["runtime_executed"])
            self.assertEqual(len(report["entries"]),10)


@unittest.skipUnless(shutil.which(os.environ.get("NRB_PROMPTFOO_EXECUTABLE","promptfoo")),"promptfoo absent: real CLI runtime not validated")
class RealPromptfooRuntime(unittest.TestCase):
    def test_actual_empty_cli_ten_expected_failures(self):
        adapter=load_script("v1_promptfoo_actual_runtime","promptfoo_smoke.py")
        with tempfile.TemporaryDirectory() as temp:
            report=adapter.run_smoke(Path(temp)/"run",executable=os.environ.get("NRB_PROMPTFOO_EXECUTABLE","promptfoo"))
            self.assertTrue(report["passed"])
            self.assertEqual(report["stats"]["failures"],10)
            self.assertEqual(report["stats"]["errors"],0)
            self.assertEqual(report["api_provider_calls"],0)


if __name__=="__main__":unittest.main()

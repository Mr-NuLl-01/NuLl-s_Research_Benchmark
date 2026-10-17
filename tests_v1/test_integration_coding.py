"""V1 integration checks use real trusted subprocesses, never mocked candidate values.

Review ledgers below are synthetic test fixtures for gate mechanics. They are not
human or model ratings of benchmark quality or actual model submissions.
"""
from __future__ import annotations
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from nrb_v1 import execution
from nrb_v1.artifacts import materialize, safe_name, validate_submission
from nrb_v1.grading import attach_review, grade, review_packet
from nrb_v1.packets import candidate
from nrb_v1.registry import module, spec


class RealSubprocessCodingIntegration(unittest.TestCase):
    def test_references_and_mutant_score_gradient(self):
        expected = {
            "C01": {"duplicate_first":55, "unweighted_summary":18},
            "C02": {"technical_pseudoreplication":45, "pooled_strata":40},
            "C03": {"arithmetic_interface":40, "lost_left_boundary_one_cell":60},
            "C04": {"amplitude_as_power":25, "ignore_p_polarization":39, "opaque_cutoff":29},
            "C05": {"accept_rejected_state":33, "left_continuous_source":55, "discard_small_remainder":48},
        }
        for task_id, scores in expected.items():
            variants=module(task_id).mutants(17)
            for name, submission in variants.items():
                with self.subTest(task=task_id,variant=name):
                    report=grade(task_id,submission,17,backend="trusted",timeout=10)
                    self.assertEqual(report["execution"]["status"],"executed")
                    self.assertEqual(report["auto_scored_max"],70)
                    self.assertEqual(report["auto_points"],70 if name=="reference" else scores[name])
                    self.assertEqual(report["completion_status"],"pending_review" if name=="reference" else "failed")
                    self.assertIsNone(report["total"])
                    self.assertTrue(all(report["tier_scores"][tier]["scored_max"]==maximum for tier,maximum in (("basic",20),("scientific",30),("stress",20))))

    def test_worker_receives_only_inputs_and_declared_artifacts(self):
        task=module("C01")
        original_run=execution._run
        captures=[]
        def inspected_run(argv,cwd,payload,timeout,*args,**kwargs):
            data=json.loads(payload)
            captures.append((data,{p.relative_to(cwd).as_posix() for p in Path(cwd).rglob("*") if p.is_file()}))
            return original_run(argv,cwd,payload,timeout,*args,**kwargs)
        submission=task.reference_submission()
        with patch.object(execution,"_run",side_effect=inspected_run):
            report=grade("C01",submission,backend="trusted",timeout=10)
        self.assertEqual(report["auto_points"],70)
        self.assertEqual(len(captures),1)
        payload,files=captures[0]
        self.assertEqual(set(payload),{"language","runs","case_timeout"})
        self.assertEqual(payload["runs"],[c["input"] for c in task.cases()])
        self.assertEqual(files,set(submission["artifacts"])|{"_driver_nrb.py"})
        self.assertNotIn("expected",json.dumps(payload))
        for task_id in ("C01","C02","C03","C04","C05"):
            with patch.object(module(task_id),"cases",side_effect=AssertionError("Candidate packet must not call hidden cases/oracle")):
                packet=candidate(task_id)
                self.assertNotIn('"expected"',packet["content"])

    def test_scientific_seed_variation_and_visible_examples(self):
        for task_id in ("C01", "C02", "C03", "C04", "C05"):
            task=module(task_id)
            scientific=lambda seed:[c["input"] for c in task.cases(seed) if c["tier"]=="scientific"]
            with self.subTest(task=task_id):
                self.assertNotEqual(scientific(17),scientific(2026))
                self.assertEqual(scientific(17),scientific(17))
                for seed in (17,2026):
                    section=task.prompt(seed).split("## 可见示例输入",1)[1]
                    visible=json.loads(section.split("```json\n",1)[1].split("\n```",1)[0])
                    self.assertIn(visible,[c["input"] for c in task.cases(seed)])
        # Stable multilayer composition must be constructed from field relations.
        optical=module("C04").prompt(17)
        self.assertIn("界面两侧这两个总场连续",optical)
        self.assertNotIn("t_new=",optical)
        self.assertNotIn("r_new=",optical)

    def test_malformed_execution_does_not_get_exception_credits(self):
        task=module("C01")
        for label,source in {
            "syntax":"def solve(:\n    pass\n",
            "no_function":"answer=42\n",
            "nan":"def solve(problem): return float('nan')\n",
            "infinite":"def solve(problem): return float('inf')\n",
            "no_json":"def solve(problem): return {1,2}\n",
        }.items():
            with self.subTest(candidate=label):
                submission=task.reference_submission()
                submission["artifacts"]["solution.py"]=source
                report=grade("C01",submission,backend="trusted",timeout=5)
                self.assertEqual(report["auto_points"],0)
                self.assertEqual(report["completion_status"],"failed")
                self.assertFalse(report["quality_qualified"])
        # A genuine candidate ValueError is distinct from malformed return values.
        submission=task.reference_submission()
        submission["artifacts"]["solution.py"]="def solve(problem): raise ValueError('deliberately refuses every input')\n"
        self.assertEqual(grade("C01",submission,backend="trusted",timeout=5)["auto_points"],10)

    def test_malformed_worker_frame_cannot_crash_host(self):
        submission=module("C01").reference_submission()
        submission["artifacts"]["solution.py"] += "\n_original=solve\ndef solve(problem):\n import __main__\n __main__.records[:]=[None for _ in __main__.records]\n return _original(problem)\n"
        report=grade("C01",submission,backend="trusted",timeout=5)
        self.assertEqual(report["auto_points"],0)
        self.assertEqual(report["execution"]["status"],"failed")
        self.assertEqual(report["completion_status"],"failed")

    def test_timeout_and_unavailable_backend_are_distinct(self):
        submission=module("C01").reference_submission()
        submission["artifacts"]["solution.py"]="def solve(problem):\n    while True: pass\n"
        timed=grade("C01",submission,backend="trusted",timeout=0.2)
        self.assertEqual(timed["auto_points"],0)
        self.assertEqual(timed["execution"]["status"],"failed")
        self.assertEqual(timed["completion_status"],"failed")
        unavailable=grade("C01",module("C01").reference_submission(),backend="none")
        self.assertEqual(unavailable["auto_scored_max"],0)
        self.assertIsNone(unavailable["auto_percent"])
        self.assertIsNone(unavailable["quality_qualified"])
        self.assertEqual(unavailable["completion_status"],"infrastructure_unscored")

    def test_input_mutation_and_integer_types_are_enforced(self):
        original=module("C01").reference_submission()
        wrappers={
            "mutate_success":"\n_original=solve\ndef solve(problem):\n value=_original(problem)\n problem['modified']=True\n return value\n",
            "mutate_then_error":"\n_original=solve\ndef solve(problem):\n problem['modified']=True\n return _original(problem)\n",
            "huge_counts":"\n_original=solve\ndef solve(problem):\n value=_original(problem)\n value['n_usable']=10**400\n return value\n",
            "float_counts":"\n_original=solve\ndef solve(problem):\n value=_original(problem)\n value['n_usable']=float(value['n_usable'])\n value['n_skipped']=float(value['n_skipped'])\n for row in value['samples']: row['n']=float(row['n'])\n return value\n",
        }
        for label,wrapper in wrappers.items():
            with self.subTest(wrapper=label):
                submission=copy.deepcopy(original)
                submission["artifacts"]["solution.py"]+=wrapper
                report=grade("C01",submission,backend="trusted",timeout=5)
                self.assertLess(report["auto_points"],70)
                self.assertEqual(report["completion_status"],"failed")
                if label=="mutate_then_error": self.assertEqual(report["auto_points"],0)

    def test_artifact_path_aliases_and_collisions_are_rejected(self):
        for name in (".","./solution.py","folder//file.txt","/absolute","a/../b","a\\b","_driver_nrb.py"):
            with self.subTest(name=name):
                with self.assertRaises(ValueError): safe_name(name)
        for artifacts in ({"a":"text","a/b":"text"},{"a/b":"text","a":"text"}):
            with self.subTest(artifacts=artifacts):
                with self.assertRaises(ValueError): validate_submission({"task_id":"C01","artifacts":artifacts},"C01")
        submission={"task_id":"C01","artifacts":{"folder/data.txt":"payload"}}
        with tempfile.TemporaryDirectory() as temp:
            manifest=materialize(submission,Path(temp)/"artifacts")
            self.assertEqual((Path(temp)/"artifacts/folder/data.txt").read_text(),"payload")
            self.assertEqual(manifest["folder/data.txt"]["bytes"],7)


class ManualReviewBindingIntegration(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.directory=Path(self.temp.name)/"review"
        self.submission=module("C01").reference_submission()
        review_packet("C01",self.submission,self.directory,backend="trusted",timeout=5)
        self.path=self.directory/"review.json"
        self.ledger=json.loads(self.path.read_text())
        # Synthetic ratings only exercise the state machine.
        self.ledger["reviewer"]={"type":"human","id":"synthetic-regression-reviewer","model":None,"prompt_hash":None}
        for c in self.ledger["criteria"]:
            c.update(score=4,evidence="Regression fixture artifact reference",rationale="Synthetic state-machine fixture, not a real quality judgment")
        for e in self.ledger["essential_review"]:
            e.update(outcome="pass",evidence="Regression fixture artifact reference",rationale="Synthetic state-machine fixture")

    def tearDown(self):
        self.temp.cleanup()

    def attach(self,ledger=None,submission=None):
        self.path.write_text(json.dumps(self.ledger if ledger is None else ledger))
        return attach_review(self.submission if submission is None else submission,self.path)

    def test_complete_pending_failed_and_provisional_authority(self):
        report=self.attach()
        self.assertEqual(report["total"],100)
        self.assertEqual(report["completion_status"],"complete")
        self.assertEqual(report["completion_authority"],"human_assessed")
        self.assertTrue(report["quality_qualified"])
        ledger=copy.deepcopy(self.ledger)
        ledger["essential_review"][0]["outcome"]="unassessed"
        report=self.attach(ledger)
        self.assertEqual(report["completion_status"],"pending_review")
        self.assertIsNone(report["quality_qualified"])
        ledger["essential_review"][0]["outcome"]="fail"
        report=self.attach(ledger)
        self.assertEqual(report["total"],100)
        self.assertEqual(report["completion_status"],"failed")
        self.assertFalse(report["quality_qualified"])
        ledger=copy.deepcopy(self.ledger)
        ledger["reviewer"]={"type":"llm","id":"synthetic-llm-review","model":"fixture-only","prompt_hash":"fixture-prompt-fingerprint"}
        report=self.attach(ledger)
        self.assertEqual(report["review_status"],"llm_reviewed_provisional")
        self.assertEqual(report["completion_authority"],"llm_provisional")
        self.assertTrue(report["quality_qualified"])

    def test_tampered_automatic_report_and_artifact_are_rejected(self):
        automatic=self.directory/"automatic.json"
        original=automatic.read_text()
        value=json.loads(original);value["auto_points"]=69
        automatic.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError,"fingerprint"):
            self.attach()
        automatic.write_text(original)
        report_path=self.directory/"artifacts/report.md"
        report_path.write_text(report_path.read_text()+"\nChanged after grading")
        with self.assertRaisesRegex(ValueError,"artifact bytes changed"):
            self.attach()

    def test_review_binding_score_and_evidence_tampering_rejected(self):
        for label,mutate in (
            ("packet",lambda l:l.update(packet_hash="changed")),
            ("weight",lambda l:l["criteria"][0].update(weight=999)),
            ("score_type",lambda l:l["criteria"][0].update(score=4.0)),
            ("empty_evidence",lambda l:l["criteria"][0].update(evidence="")),
            ("essential_wording",lambda l:l["essential_review"][0].update(requirement="weakened")),
            ("missing_essential",lambda l:l["essential_review"].pop()),
            ("missing_manifest",lambda l:l["artifact_manifest"].pop("report.md")),
        ):
            with self.subTest(tamper=label):
                ledger=copy.deepcopy(self.ledger);mutate(ledger)
                with self.assertRaises(ValueError): self.attach(ledger)
        changed=copy.deepcopy(self.submission)
        changed["artifacts"]["solution.py"]+="\n# changed"
        with self.assertRaisesRegex(ValueError,"different submission"):
            self.attach(submission=changed)

    def test_numeric_score_cannot_override_critical_or_missing_artifact(self):
        for label,submission in (
            ("critical",module("C01").mutants()["duplicate_first"]),
            ("missing_report",module("C01").reference_submission()),
        ):
            with self.subTest(case=label):
                if label=="missing_report": submission["artifacts"].pop("report.md")
                directory=Path(self.temp.name)/label
                review_packet("C01",submission,directory,backend="trusted",timeout=5)
                path=directory/"review.json";ledger=json.loads(path.read_text())
                ledger["reviewer"]=self.ledger["reviewer"]
                for c in ledger["criteria"]:c.update(score=4,evidence="fixture",rationale="fixture")
                for e in ledger["essential_review"]:e.update(outcome="pass",evidence="fixture",rationale="fixture")
                path.write_text(json.dumps(ledger))
                report=attach_review(submission,path)
                self.assertGreaterEqual(report["total"],80)
                self.assertEqual(report["completion_status"],"failed")
                self.assertFalse(report["quality_qualified"])


class ModalObservationGateIntegration(unittest.TestCase):
    def test_visual_interactive_video_audio_observations_bind_actual_bytes(self):
        # Deliberately synthetic byte/ledger fixtures test the gate schema only.
        # They are not claimed as valid scientific figures or playable media,
        # and these scores are not real human/model quality assessments.
        for task_id,action in (("R01","viewed"),("X01","interacted"),("X02","watched"),("X03","listened")):
            with self.subTest(task=task_id), tempfile.TemporaryDirectory() as temp:
                task=spec(task_id)
                submission={"task_id":task_id,"answer":{},"artifacts":{
                    name:"Synthetic schema fixture bytes for "+name for name in task["required_artifacts"]}}
                directory=Path(temp)/"review"
                review_packet(task_id,submission,directory,backend="none")
                path=directory/"review.json"
                ledger=json.loads(path.read_text())
                ledger["reviewer"]={"type":"human","id":"synthetic-modal-gate-fixture"}
                for criterion in ledger["criteria"]:
                    criterion.update(score=4,evidence="Synthetic gate fixture",rationale="Not a scientific or media quality assessment")
                for essential in ledger["essential_review"]:
                    essential.update(outcome="pass",evidence="Synthetic gate fixture",rationale="Tests assertion binding only")
                self.assertEqual({o["artifact"] for o in ledger["observations"]},set(task["modal_observation_artifacts"]))
                self.assertTrue(all(o["action"]==action and o["performed"] is False for o in ledger["observations"]))
                def attach(value):
                    path.write_text(json.dumps(value))
                    return attach_review(submission,path)
                with self.assertRaisesRegex(ValueError,"actual viewing/listening/interaction"):
                    attach(ledger)
                viewed=copy.deepcopy(ledger)
                for observation in viewed["observations"]:
                    observation.update(performed=True,evidence="Synthetic assertion fixture for this exact byte hash, not an actual media review")
                result=attach(viewed)
                self.assertEqual(result["observations"],viewed["observations"])
                self.assertEqual(result["completion_status"],"complete")
                self.assertEqual(result["completion_authority"],"human_assessed")
                for label,mutate in (
                    ("bytes",lambda l:l["observations"][0].update(sha256="different-bytes")),
                    ("action",lambda l:l["observations"][0].update(action="wrong-action")),
                    ("missing",lambda l:l["observations"].pop()),
                    ("evidence",lambda l:l["observations"][0].update(evidence="")),
                    ("boolean",lambda l:l["observations"][0].update(performed="true")),
                ):
                    with self.subTest(tamper=label):
                        malformed=copy.deepcopy(viewed);mutate(malformed)
                        with self.assertRaises(ValueError):attach(malformed)
                for outcome,status in (("unassessed","pending_review"),("fail","failed")):
                    without_view=copy.deepcopy(ledger)
                    for essential in without_view["essential_review"]:essential["outcome"]=outcome
                    result=attach(without_view)
                    self.assertEqual(result["completion_status"],status)
                    self.assertIsNot(result["quality_qualified"],True)


if __name__=="__main__":
    unittest.main()

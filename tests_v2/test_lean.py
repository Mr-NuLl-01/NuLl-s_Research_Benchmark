"""Checks for the L01 proof boundary, failure semantics and native controls."""
import json
import os
from pathlib import Path
import shutil
import unittest
from unittest import mock

from nrb_v2 import lean


class LeanContractTests(unittest.TestCase):
    def test_readable_audit_sources_match_runtime(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual((root / "environments/v2/lean/NRBPrelude.lean").read_text(), lean.PRELUDE)
        self.assertEqual((root / "environments/v2/lean/Verifier.lean").read_text(), lean.DRIVER)

    def test_frozen_goals_and_weights(self):
        c = lean.cases(17)
        self.assertEqual([x["id"] for x in c], list(lean.GOALS))
        self.assertEqual({t: sum(x["weight"] for x in c if x["tier"] == t)
                          for t in ("basic", "scientific", "stress")},
                         {"basic": 20, "scientific": 30, "stress": 20})
        self.assertEqual(lean.cases(0), lean.cases(2026))

    def test_no_execution_is_unscored(self):
        r = lean.execute(lean.reference_submission(), backend="none")
        self.assertEqual(r["status"], "unavailable")
        self.assertEqual(r["records"], [])

    def test_missing_docker_is_not_candidate_failure(self):
        with mock.patch.object(lean.shutil, "which", return_value=None):
            r = lean.execute(lean.reference_submission(), backend="docker")
        self.assertEqual(r["status"], "unavailable")

    def test_strict_candidate_json(self):
        for raw in ('{"step_balance":"by rfl","step_balance":"by sorry"}',
                    '{"unknown":"by rfl"}', '{"step_balance":true}', '["by sorry"]',
                    '{"step_balance":NaN}'):
            with self.subTest(raw=raw), self.assertRaises((ValueError, TypeError)):
                lean._strict_proofs(raw)
        self.assertEqual(lean._strict_proofs('{}'), {})

    def test_malformed_source_is_failed(self):
        r = lean.execute({"artifacts": {lean.SOURCE_NAME: "not json"}}, backend="trusted")
        self.assertEqual(r["status"], "failed")
        self.assertEqual(len(r["records"]), 6)
        self.assertFalse(any(x["ok"] for x in r["records"]))

    def test_audit_contract_rejects_weakening_or_extra_axiom(self):
        c = lean.cases()[0]
        good = {"goal": c["id"], "kernel_checked": True, "target_verified": True,
                "axioms": ["propext", "Quot.sound"], "statement": "fixed audited target"}
        self.assertTrue(lean.validate_output(c, good)[0])
        for change in ({"goal": "True"}, {"kernel_checked": 1}, {"target_verified": False},
                       {"axioms": ["sorryAx"]}, {"axioms": ["axiom_secret"]},
                       {"axioms": ["Lean.trustCompiler"]}, {"axioms": ["propext", "propext"]}):
            with self.subTest(change=change):
                self.assertFalse(lean.validate_output(c, dict(good, **change))[0])

    def test_candidate_packet_has_definitions_but_no_answer(self):
        files = lean.candidate_files()
        self.assertEqual(set(files), {"L01.md", "NRBPrelude.lean", "lean-toolchain", "proofs.template.json"})
        self.assertEqual(json.loads(files["proofs.template.json"]), {key: "" for key in lean.GOALS})
        for proof in lean.REFERENCE_PROOFS.values():
            self.assertNotIn(proof, files["L01.md"])
            self.assertNotIn(proof, files["NRBPrelude.lean"])


def native_available():
    return bool(os.environ.get("NRB_LEAN") or shutil.which("lean"))


@unittest.skipUnless(native_available(), "Pinned native Lean unavailable; set NRB_LEAN for real kernel controls")
class NativeLeanTests(unittest.TestCase):
    def test_reference_and_real_negative_controls(self):
        for label, submission in lean.mutants().items():
            with self.subTest(label=label):
                r = lean.execute(submission, backend="trusted")
                self.assertEqual(r["status"], "executed", r.get("error"))
                passed = [c["id"] for c, record in zip(lean.cases(), r["records"])
                          if record.get("ok") is True and lean.validate_output(c, record["value"])[0]]
                self.assertEqual(len(passed) == 6, label == "reference", r["records"])
                if label in ("invalid_trace_induction", "missing_obligation"):
                    self.assertEqual(len(passed), 5, r["records"])
                elif label != "reference":
                    self.assertEqual(len(passed), 0, r["records"])
                if label == "include_file":
                    self.assertTrue(all("external input" in x.get("detail", "") for x in r["records"]))
                if label in ("sorry", "indirect_sorry"):
                    self.assertTrue(all("sorryAx" in x.get("detail", "") for x in r["records"]))

    def test_comments_do_not_trigger_regex_rejection(self):
        proofs = {k: v + "\n-- sorry axiom native_decide are just commentary\n"
                  for k, v in lean.REFERENCE_PROOFS.items()}
        r = lean.execute({"artifacts": {lean.SOURCE_NAME: json.dumps(proofs)}}, backend="trusted")
        self.assertEqual(r["status"], "executed", r.get("error"))
        self.assertTrue(all(x["ok"] for x in r["records"]), r["records"])

    def test_meta_terms_rejected_before_io_side_effect(self):
        marker = Path('/tmp/nrb-lean-forbidden-side-effect.txt')
        if marker.exists():
            marker.unlink()
        term = 'by_elab do\n  IO.FS.writeFile "/tmp/nrb-lean-forbidden-side-effect.txt" "bad"\n  return Lean.mkConst ``True.intro'
        r = lean.execute({"artifacts": {lean.SOURCE_NAME: json.dumps({key: term for key in lean.GOALS})}}, backend="trusted")
        self.assertEqual(r["status"], "executed", r.get("error"))
        self.assertFalse(any(x["ok"] for x in r["records"]))
        self.assertFalse(marker.exists(), "Candidate metaprogram crossed proof-term boundary")


if __name__ == "__main__":
    unittest.main()

"""Actual release archives: input isolation, integrity and extracted offline use."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from scripts import package_v2_release as package
from nrb_v2 import __version__
from nrb_v2.packets import candidate, input_manifest
from nrb_v2.registry import ALL_IDS, MANUAL_IDS, OBJECTIVE_IDS, source_filename
from nrb_v2.subjective import candidate_inputs


class ArchivePrimitiveTests(unittest.TestCase):
    def test_deterministic_zip_and_explicit_metadata(self):
        with tempfile.TemporaryDirectory(prefix="nrb-package-unit-") as directory:
            root = Path(directory)
            first = package.archive(root / "one.zip", "same-root", {"b.txt": b"second", "a.txt": b"first"},
                                    kind="candidate", task_id="R06", mode="A", seed=17)
            second = package.archive(root / "two.zip", "same-root", {"a.txt": b"first", "b.txt": b"second"},
                                     kind="candidate", task_id="R06", mode="A", seed=17)
            self.assertEqual(first["sha256"], second["sha256"])
            with zipfile.ZipFile(root / "one.zip") as archive:
                self.assertTrue(all(info.date_time == package.ZIP_DATE for info in archive.infolist()))
                manifest = json.loads(archive.read("same-root/MANIFEST.json"))
                self.assertEqual((manifest["kind"], manifest["task_id"], manifest["mode"]),
                                 ("candidate", "R06", "A"))
            with self.assertRaises(FileExistsError):
                package.archive(root / "one.zip", "same-root", {"a.txt": b"changed"})

    def test_unsafe_or_ambiguous_paths_fail_before_writing(self):
        with tempfile.TemporaryDirectory(prefix="nrb-package-paths-") as directory:
            target = Path(directory) / "invalid.zip"
            for files in ({"../x": b"bad"}, {"/abs": b"bad"}, {"a/./b": b"bad"},
                          {"a": b"file", "a/b": b"collision"}, {"MANIFEST.json": b"forged"}):
                with self.subTest(files=files), self.assertRaises(ValueError):
                    package.archive(target, "root", files)
                self.assertFalse(target.exists())


class ReleasePackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = tempfile.TemporaryDirectory(prefix="nrb-v2-packages-")
        cls.root = Path(cls.workspace.name)
        cls.report = package.build_release(cls.root / "delivery")
        cls.artifacts = cls.report["artifacts"]
        evaluator = next(item for item in cls.artifacts if item["kind"] == "evaluator")
        with zipfile.ZipFile(evaluator["path"]) as archive:
            archive.extractall(cls.root / "extracted")
        cls.evaluator = cls.root / "extracted" / evaluator["zip_root"]

    @classmethod
    def tearDownClass(cls):
        cls.workspace.cleanup()

    def test_all_twenty_tasks_and_twenty_one_single_packages(self):
        singles = [item for item in self.artifacts if item["kind"] == "candidate"]
        self.assertEqual(self.report["task_count"], 20)
        self.assertEqual(len(singles), 21)
        self.assertEqual({item["task_id"] for item in singles}, set(ALL_IDS))
        self.assertEqual({(item["task_id"], item["mode"]) for item in singles}, set(package.task_variants()))
        self.assertEqual(len(self.artifacts), 23)
        with self.assertRaises(FileExistsError):
            package.build_release(self.root / "delivery")

    def test_every_manifest_hashes_actual_zip_bytes(self):
        for item in self.artifacts:
            with self.subTest(archive=item["name"]):
                self.assertEqual(package.digest(Path(item["path"]).read_bytes()), item["sha256"])
                with zipfile.ZipFile(item["path"]) as archive:
                    prefix = item["zip_root"] + "/"
                    manifest = json.loads(archive.read(prefix + "MANIFEST.json"))
                    self.assertEqual(len(archive.infolist()), len(manifest["files"]) + 1)
                    for entry in manifest["files"]:
                        data = archive.read(prefix + entry["path"])
                        self.assertEqual((len(data), package.digest(data)), (entry["bytes"], entry["sha256"]))

    def test_candidate_contents_match_the_frozen_allowlist_exactly(self):
        for item in self.artifacts:
            if item["kind"] != "candidate":
                continue
            tid, mode = item["task_id"], item["mode"]
            with self.subTest(task=tid, mode=mode), zipfile.ZipFile(item["path"]) as archive:
                prefix = item["zip_root"] + "/"
                names = {name.removeprefix(prefix) for name in archive.namelist()}
                bound = input_manifest(tid, 17, mode)
                allowed = {entry["path"] for entry in bound["files"]}
                self.assertEqual(names, allowed | {"PACKET.json", "README.txt", "MANIFEST.json"})
                self.assertEqual(archive.read(prefix + tid + ".md").decode(), candidate(tid)["content"])
                packet = json.loads(archive.read(prefix + "PACKET.json"))
                self.assertEqual(packet["input_manifest_hash"], bound["sha256"])
                self.assertEqual(packet["mode"], mode)
                self.assertFalse(any(part in {"nrb_v1", "nrb_v2", "evaluator", "demo_project"}
                                     for name in names for part in Path(name).parts))
                self.assertNotIn("TASK.md", names)
                if tid == "R06":
                    self.assertEqual("assets/R06/reference.mp4" in names, mode == "B")
                if tid == "L01":
                    self.assertTrue({"L01.md", "NRBPrelude.lean", "lean-toolchain", "proofs.template.json"} <= names)
                    self.assertNotIn("Verifier.lean", names)
                    self.assertTrue(all(not value for value in json.loads(archive.read(prefix + "proofs.template.json")).values()))

    def test_master_keeps_modes_in_separate_directories(self):
        item = next(item for item in self.artifacts if item["kind"] == "candidate_collection")
        with zipfile.ZipFile(item["path"]) as archive:
            prefix = item["zip_root"] + "/"
            catalog = json.loads(archive.read(prefix + "CATALOG.json"))
            self.assertEqual((catalog["task_count"], catalog["condition_count"]), (20, 21))
            names = {name.removeprefix(prefix) for name in archive.namelist()}
            self.assertNotIn("tasks/R06/A/assets/R06/reference.mp4", names)
            self.assertIn("tasks/R06/B/assets/R06/reference.mp4", names)
            self.assertIn("不能把整个主包交给候选", archive.read(prefix + "README.txt").decode())

    def test_evaluator_has_inputs_templates_and_no_fake_submissions(self):
        root = self.evaluator
        for tid in OBJECTIVE_IDS:
            self.assertTrue((root / f"submissions/{tid}/PLACE-SUBMISSION-HERE.txt").is_file())
            self.assertFalse((root / f"submissions/{tid}/{source_filename(tid)}").exists())
        templates = sorted((root / "reviews").rglob("review.template.json"))
        self.assertEqual(len(templates), 8)
        self.assertEqual({json.loads(path.read_text())["task_id"] for path in templates}, set(MANUAL_IDS))
        for tid, mode in package.task_variants():
            if tid in MANUAL_IDS:
                for item in candidate_inputs(tid, mode):
                    self.assertEqual((root / item["source"]).read_bytes(), package.source_bytes(item["source"]))
        for filename in ("environments/v2/Dockerfile", "environments/v2/LeanDockerfile",
                         "environments/v2/lean/Verifier.lean", "environments/v2/install_lean.sh",
                         f"release/{__version__}/run-grader.py", "run-grader.py", "LICENSE"):
            self.assertTrue((root / filename).is_file(), filename)
        self.assertFalse(any("demo_project" in path.parts for path in root.rglob("*")))

    def _offline(self, *args):
        env = {key: value for key, value in os.environ.items() if key not in ("PYTHONPATH", "PYTHONHOME")}
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        result = subprocess.run([sys.executable, "-S", *args], cwd=self.evaluator, env=env,
                                capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def test_extracted_cli_and_h02_run_without_site_packages(self):
        listing = json.loads(self._offline("-m", "nrb_v2", "list"))
        self.assertEqual({task["id"] for task in listing}, set(ALL_IDS))
        self._offline("-c", "from pathlib import Path; from nrb_v2.h02 import reference_submission; "
                      "Path('H02-reference-control.json').write_text(reference_submission()['artifacts']['answer.json'])")
        self._offline("-m", "nrb_v2", "grade", "--task", "H02", "--source", "H02-reference-control.json",
                      "--out", "results/H02-package-control.json")
        report = json.loads((self.evaluator / "results/H02-package-control.json").read_text())
        self.assertEqual((report["status"], report["score"], report["execution"]["backend"]), ("passed", 100, "answer"))
        self._offline("-m", "nrb_v2", "validate-report", "results/H02-package-control.json")
        self._offline("-m", "nrb_v2", "batch", "--input", "submissions", "--out-dir", "results/empty-control",
                      "--execution", "none")
        batch = json.loads((self.evaluator / "results/empty-control/summary.json").read_text())
        self.assertTrue(all(entry["status"] == "not_submitted" for entry in batch["entries"]))
        self.assertIsNone(batch["mean_score"])

    def test_extracted_subjective_templates_and_protocol_work_offline(self):
        result = self._offline("-c", """
import json
from pathlib import Path
from nrb_v2.subjective import blank_review, score_review
count = 0
for path in sorted(Path('reviews').rglob('review.template.json')):
    saved = json.loads(path.read_text())
    fresh = blank_review(saved['task_id'], saved['mode'])
    assert saved == fresh, path
    assert score_review(fresh)['score'] is None
    fresh['reviewer']['id'] = 'packaging-protocol-control'
    fresh['submission_id'] = 'synthetic-control-not-model-performance'
    for row in fresh['ratings']:
        row.update(level=4, evidence='PACKAGING CONTROL: checks protocol computation only.')
    for row in fresh['requirements']:
        row.update(status='pass', evidence='PACKAGING CONTROL: synthetic evidence.')
    for row in fresh['observations']:
        row.update(status='observed', evidence='PACKAGING CONTROL: synthetic observation.')
    assert score_review(fresh)['score'] == 100
    count += 1
print(count)
""")
        self.assertEqual(result.strip(), "8")
        self._offline("-m", "nrb_v2", "review", "reviews/R06/B/review.template.json",
                      "--out", "results/R06-B-blank-control.json")
        result = json.loads((self.evaluator / "results/R06-B-blank-control.json").read_text())
        self.assertIsNone(result["score"])
        self.assertEqual(result["status"], "review_incomplete")


if __name__ == "__main__":
    unittest.main()

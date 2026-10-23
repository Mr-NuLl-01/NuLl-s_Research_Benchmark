#!/usr/bin/env python3
"""Read and audit this exact GitHub Actions artifact; never executes candidates."""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from nrb_v1.artifacts import decode
from nrb_v1.provenance import fingerprint
from nrb_v2.grading import identity, validate_report
from nrb_v2.registry import OBJECTIVE_IDS, CODING_IDS, module, source_filename
from nrb_v2.lean import GOALS, ALLOWED_AXIOMS, LEAN_VERSION
from scripts.v2.check_docker import PROBE, PROBE_CHECKS

EXPECTED_COMMIT = "735174612fe0fb298a83c872a0350f6eabf2d0a5"
EXPECTED_FINGERPRINT = "7f2487673f1a214d60311193a369d48ab9215f9d7006554bf5c823e6ce5c7aa3"
EXPECTED_ARTIFACT_SHA256 = "77b68639e6e3c23a0583c85bb1d1b00f663047494dc736ab068c06af436e52d6"

def read(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))

def require(condition, message):
    if not condition:
        raise ValueError(message)

def sealed(value):
    return value["report_hash"] == fingerprint({k: v for k, v in value.items() if k != "report_hash"})

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE / 'summary.json')
    args = parser.parse_args()
    run, job, artifact = read("run.json"), read("job.json"), read("artifact.json")
    controls, isolation, images = read("v2-docker-controls.json"), read("v2-isolation.json"), read("v2-images.json")
    current = identity()
    require(current["evaluator_fingerprint"] == EXPECTED_FINGERPRINT, "Local audit evaluator differs")
    require(run["id"] == 39970163399 and run["head_sha"] == EXPECTED_COMMIT, "Wrong workflow commit/run")
    require(run["path"] == ".github/workflows/v2.yml" and run["status"] == "completed" and run["conclusion"] == "success", "V2 run not successful")
    require(job["id"] == 120470415803 and job["run_id"] == run["id"] and job["conclusion"] == "success", "Wrong/failed Docker job")
    require(all(s["status"] == "completed" and s["conclusion"] == "success" for s in job["steps"]), "Incomplete/failed Docker step")
    require(artifact["id"] == 12508199381 and artifact["name"] == "v2-docker-evidence" and not artifact["expired"], "Wrong artifact")
    require(artifact["workflow_run"]["id"] == run["id"] and artifact["workflow_run"]["head_sha"] == EXPECTED_COMMIT, "Artifact belongs to another commit")
    archive_bytes = (HERE / "v2-docker-evidence.zip").read_bytes()
    require(len(archive_bytes) == artifact["size_in_bytes"] == 48542, "Archive size differs")
    require(hashlib.sha256(archive_bytes).hexdigest() == EXPECTED_ARTIFACT_SHA256 == artifact["digest"].removeprefix("sha256:"), "GitHub artifact digest differs")
    inventory = read("extracted-files.json")
    with zipfile.ZipFile(HERE / "v2-docker-evidence.zip") as archive:
        require(len(archive.namelist()) == len(inventory) == 9, "Wrong artifact file inventory")
        require(set(archive.namelist()) == {x["path"] for x in inventory}, "ZIP/inventory paths differ")
        for item in inventory:
            payload = (HERE / item["path"]).read_bytes()
            require(payload == archive.read(item["path"]), "Extracted bytes differ: " + item["path"])
            require(len(payload) == item["bytes"] and hashlib.sha256(payload).hexdigest() == item["sha256"], "Extracted digest differs")
    expected_identity = {"grader_version": "2.0.0", "evaluator_fingerprint": EXPECTED_FINGERPRINT,
                         "source_commit": EXPECTED_COMMIT, "source_dirty": False}
    for value, name in ((controls, "controls"), (isolation, "isolation")):
        require(sealed(value), name + " evidence content hash differs")
        require(value["evaluator_identity"] == expected_identity, name + " evaluator identity differs")
        require(value["not_model_performance"] is True and value["api_provider_calls"] == 0, "Author-control scope changed")
        require(value["passed"] is True, name + " evidence failed")
    require(controls["execution_requested"] == "docker" and controls["seeds"] == [17] and controls["mutant_selection"] == "all", "Wrong controls condition")
    require(len(controls["checks"]) == 72 and all(x["passed"] is True for x in controls["checks"]), "Control gate incomplete/failed")
    require(len(images) == 2 and {x["Id"] for x in images} == {x["Id"] for x in controls["images"].values()}, "Image inspect/snapshot differs")
    inspected = {x["Id"]: x for x in images}
    for kind, image in controls["images"].items():
        require(re.fullmatch(r"sha256:[0-9a-f]{64}", image["Id"]) is not None, "No immutable image ID")
        require(image["Architecture"] == "amd64" and image["Os"] == "linux", "Wrong runtime architecture")
        require(all(inspected[image["Id"]].get(k) == v for k, v in image.items()), "Image details differ: " + kind)
    expected_controls = {}
    for tid in OBJECTIVE_IDS:
        task = module(tid)
        expected_controls[(tid, "reference", 17)] = task.reference_submission(17)
        for label, submission in task.mutants(17).items():
            if label != "reference":
                expected_controls[(tid, label, 17)] = submission
    entries = controls["entries"]
    keys = [(x["task_id"], x["label"], x["seed"]) for x in entries]
    require(len(keys) == len(set(keys)) == len(expected_controls) == 70 and set(keys) == set(expected_controls), "Missing/extra/duplicate control")
    reference_rows, wrong_counts, backend_counts = [], Counter(), Counter()
    compiler_versions, lean_rows = {}, {}
    for entry in entries:
        tid, label, seed = entry["task_id"], entry["label"], entry["seed"]
        report = entry["report"]
        validate_report(report)
        require(entry["passed"] is True and entry["not_model_performance"] is True, "Unexpected control outcome")
        require(report["task_id"] == tid and report["seed"] == seed, "Wrong report task/seed")
        require(all(report[k] == v for k, v in expected_identity.items()), "Report identity differs")
        require(report["manual_review_required"] is False and report["score"] is not None, "Manual/unscored automatic control")
        require(report["execution"]["status"] == "executed", "Control did not execute")
        source = expected_controls[(tid, label, seed)]["artifacts"][source_filename(tid)]
        slim = {"task_id": tid, "artifacts": {source_filename(tid): source}, "answer": {}}
        require(report["source_hash"] == fingerprint(decode(source)) and report["submission_hash"] == fingerprint(slim), "Control source differs: " + tid + "/" + label)
        backend = report["execution"]["backend"]
        require(backend == ("answer" if tid == "H02" else "docker"), "Wrong execution kind")
        backend_counts[backend] += 1
        if tid in CODING_IDS:
            image_id = controls["images"]["lean" if tid == "L01" else "python_fortran"]["Id"]
            require(report["execution"].get("image_id") == image_id, "Code control not bound to actual image")
        else:
            require(report["execution"].get("image_id") is None, "H02 must not claim a container")
        if label == "reference":
            require(report["score"] == 100 and report["status"] == "passed" and all(x["passed"] is True for x in report["checks"]), "Reference failed: " + tid)
            reference_rows.append({"task_id": tid, "score": report["score"], "backend": backend,
                                   "image_id": report["execution"].get("image_id")})
        else:
            require(0 <= report["score"] < 100 and report["failed_checks"] > 0, "Wrong control was not detected")
            wrong_counts[tid] += 1
        if report["execution"].get("compiler"):
            compiler_versions[tid] = report["execution"]["compiler"]
        if tid == "L01":
            lean_rows[label] = report
    require(len(reference_rows) == 13 and sum(wrong_counts.values()) == 57, "Wrong reference/control counts")
    require(backend_counts == {"docker": 62, "answer": 8}, "Wrong runtime/answer partition")
    for report in lean_rows.values():
        require(report["execution"]["toolchain"] == LEAN_VERSION, "Wrong Lean toolchain")
        require(report["execution"]["compiler"] == "Lean (version 4.19.0, x86_64-unknown-linux-gnu, commit 6caaee842e94, Release)", "Wrong actual Lean compiler")
    proof_audit = lean_rows["reference"]["execution"]["proof_audit"]
    require([x["goal"] for x in proof_audit] == list(GOALS), "Missing/changed fixed Lean goals")
    for obligation in proof_audit:
        require(obligation["kernel_checked"] is True and obligation["target_verified"] is True, "Unchecked Lean goal")
        require(set(obligation["axioms"]) <= ALLOWED_AXIOMS and obligation["statement"], "Wrong Lean axiom/target audit")
    for label in ("sorry", "indirect_sorry"):
        require(lean_rows[label]["score"] == 0 and all("sorryAx" in x.get("detail", "") for x in lean_rows[label]["execution"]["proof_audit"]), "Transitive sorry control not rejected")
    require(lean_rows["include_file"]["score"] == 0 and all("external input" in x.get("detail", "") for x in lean_rows["include_file"]["execution"]["proof_audit"]), "External-input proof control not rejected")
    require(lean_rows["invalid_trace_induction"]["failed_checks"] == 1 and lean_rows["missing_obligation"]["failed_checks"] == 1, "Partial Lean scoring changed")
    require(isolation["runtime_status"] == "executed" and all(v is True for v in isolation["checks"].values()), "Isolation gate failed")
    require(isolation["probe_source_sha256"] == fingerprint(PROBE.encode()), "Different isolation probe")
    require(isolation["actual_image"] == controls["images"]["python_fortran"], "Isolation used a different image")
    probe = isolation["probe_output"]
    require(set(probe["checks"]) == PROBE_CHECKS and len(PROBE_CHECKS) == 13 and all(v is True for v in probe["checks"].values()), "Isolation observation missing/failed")
    require(probe["uid"] == probe["gid"] == 65534 and not probe["present_forbidden_paths"] and not probe["denied_forbidden_paths"], "Isolation filesystem/user observation differs")
    require(probe["candidate_files"] == ["_driver_nrb.py", "solution.py"] and not probe["candidate_symlinks"], "Unexpected candidate mount")
    require(probe["network_interfaces"] == ["lo"] and probe["connect_errno"] in (101, 113), "External networking not blocked")
    require(probe["process_security"] == {"CapEff": "0000000000000000", "NoNewPrivs": "1"}, "Privileges changed")
    require("ro" in probe["mounts"]["/"]["options"] and "ro" in probe["mounts"]["/task"]["options"] and probe["mounts"]["/tmp"]["filesystem"] == "tmpfs", "Mount observation differs")
    require(len(isolation["controls"]) == 2, "Missing isolation reference/wrong control")
    for entry in isolation["controls"]:
        report = entry["report"]
        validate_report(report)
        require(entry["passed"] is True and all(v is True for v in entry["checks"].values()), "Isolation companion control failed")
        require(report["execution"]["image_id"] == isolation["actual_image"]["Id"], "Isolation companion image differs")
        require(all(report[k] == v for k, v in expected_identity.items()), "Isolation companion evaluator differs")
    require(identity()["evaluator_fingerprint"] == EXPECTED_FINGERPRINT, "Evaluator changed during audit")
    summary = {
        "schema": "nrb-v2-ci-docker-independent-audit-v1", "passed": True,
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run["id"], "run_url": run["html_url"], "job_id": job["id"],
        "commit": EXPECTED_COMMIT, "evaluator_fingerprint": EXPECTED_FINGERPRINT,
        "artifact_id": artifact["id"], "artifact_bytes": len(archive_bytes),
        "artifact_sha256": EXPECTED_ARTIFACT_SHA256,
        "control_gate_checks_passed": 72, "reference_count": 13, "wrong_control_count": 57,
        "control_record_count": 70, "unscored_count": 0,
        "backend_record_counts": dict(backend_counts),
        "references": reference_rows, "wrong_controls_by_task": dict(wrong_counts),
        "isolation_observation_count": 13, "isolation_observations": probe["checks"],
        "isolation_companion_control_count": 2,
        "images": controls["images"], "compiler_versions": compiler_versions,
        "lean_fixed_obligations": proof_audit,
        "lean_partial_scores": {name: lean_rows[name]["score"] for name in ("invalid_trace_induction", "missing_obligation")},
        "controls_wall_seconds": controls["wall_seconds"],
        "isolation_wall_seconds": isolation["wall_seconds"],
        "docker_server_version": isolation["docker_server_version"],
        "candidate_python": probe["python"],
        "not_model_performance": True, "api_provider_calls": 0,
        "scope": "12 code-task references plus 50 code mutants executed through Docker; H02 reference plus 7 answer mutants use data verification. The 13-observation isolation probe uses the Python/Fortran production executor/image. Lean is separately kernel-checked in its pinned image. These authored controls do not measure model performance or establish general host/kernel exploit resistance.",
    }
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(summary, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({k: summary[k] for k in ("passed", "control_record_count", "reference_count", "wrong_control_count", "unscored_count", "backend_record_counts", "isolation_observation_count", "controls_wall_seconds")}, indent=2))

if __name__ == "__main__":
    main()

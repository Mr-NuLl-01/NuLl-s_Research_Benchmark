#!/usr/bin/env python3
"""Complete V2 release gates; reference controls are never model performance.

`contracts` checks the frozen catalog, generated/static prompt boundaries,
candidate-only exports, allowlisted inputs and the site's actual score contract.
`controls` executes all 13 automatic tasks, validates each resulting report and
records the actual immutable Docker image selected for every code control.
H02 verifies data only; it is explicitly not reported as a container execution.
Missing runtimes fail this release gate and retain unscored/null evidence.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import platform
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from nrb_v1.provenance import fingerprint
from nrb_v2 import __version__
from nrb_v2.grading import grade, identity, public_manifest, validate_report
from nrb_v2.packets import candidate, catalog, export_tasks, input_manifest
from nrb_v2.registry import ALL_IDS, CODING_IDS, FORTRAN_IDS, MANUAL_IDS, OBJECTIVE_IDS, PYTHON_IDS, module, spec
from nrb_v2.subjective import blank_review, candidate_inputs, rubric_hash, rubric_spec


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def new_evidence(kind):
    return {"schema": "nrb-v2-release-check-v1", "kind": kind,
            "benchmark_version": __version__, "created_at": datetime.now(timezone.utc).isoformat(),
            "not_model_performance": True, "api_provider_calls": 0,
            "evaluator_identity": identity(), "checks": [],
            "environment": {"python": platform.python_version(), "platform": platform.platform(),
                            "machine": platform.machine()}}


def check(evidence, label, action):
    try:
        detail = action()
        result = {"name": label, "passed": True}
        if detail is not None:
            result["detail"] = detail
    except (OSError, ValueError, KeyError, TypeError, AssertionError, subprocess.SubprocessError) as exc:
        result = {"name": label, "passed": False,
                  "error": type(exc).__name__ + ": " + str(exc)[:2000]}
    evidence["checks"].append(result)
    print(("PASS " if result["passed"] else "FAIL ") + label, flush=True)
    return result["passed"]


def contracts():
    evidence = new_evidence("complete_twenty_task_contracts")
    generated = catalog(17)

    def release_scope():
        require(len(ALL_IDS) == 20 and len(set(ALL_IDS)) == 20, "Exactly 20 unique tasks required")
        require(len(PYTHON_IDS) == 8 and len(FORTRAN_IDS) == 3 and len(CODING_IDS) == 12,
                "Expected eight Python, three Fortran and one Lean task")
        require(len(OBJECTIVE_IDS) == 13 and len(MANUAL_IDS) == 7, "Expected 13 automatic and seven rubric tasks")
        require(set(OBJECTIVE_IDS).isdisjoint(MANUAL_IDS) and set(OBJECTIVE_IDS) | set(MANUAL_IDS) == set(ALL_IDS),
                "Task tracks must partition the release")
        require(generated["status"] == "complete" and generated["ready_count"] == 20 and generated["planned_count"] == 0,
                "Release contains planned/unavailable tasks")
        for task in generated["tasks"]:
            require(task["status"] == "ready" and task["required_artifacts"], "Missing ready task contract")
            require(task["manual_review_required"] is (task["id"] in MANUAL_IDS), "Manual gate on automatic task")
        return dict(Counter(task["category"] for task in generated["tasks"]))
    check(evidence, "complete 20-task scope and 13/7 score partition", release_scope)

    def frozen_sources():
        manifest = read_json(ROOT / "tasks/v2.0/manifest.json")
        require(manifest["benchmark_version"] == __version__, "Frozen packet version differs")
        rows = manifest["tasks"]
        require(len(rows) == 20 and {r["task_id"] for r in rows} == set(ALL_IDS), "Frozen manifest must contain all 20 exactly once")
        entries = {row["task_id"]: row for row in rows}
        source_hashes = {}
        for tid in ALL_IDS:
            row = entries[tid]
            require(row["file"] == tid + ".md" and row["seed"] == 17, tid + " frozen filename/seed mismatch")
            packet = candidate(tid, 17)
            require(row["sha256"] == packet["packet_hash"], tid + " candidate digest is stale")
            source = (ROOT / "tasks/v2.0" / (tid + ".md")).read_bytes()
            source_hashes[tid] = sha256(source)
            require(row.get("source_sha256") == source_hashes[tid], tid + " source digest is missing or stale")
            if tid == "R06":
                expected_inputs = {mode: input_manifest(tid, 17, mode)["sha256"] for mode in ("A", "B")}
                require(row.get("input_manifest_hashes") == expected_inputs, "R06 frozen mode input digests differ")
            else:
                require(row.get("input_manifest_hash") == input_manifest(tid, 17)["sha256"], tid + " frozen input digest differs")
            if tid in PYTHON_IDS:
                require(source == packet["content"].encode("utf-8"), tid + " frozen Python packet differs from generator")
            elif tid in (*FORTRAN_IDS, "L01"):
                require(source == module(tid).prompt(17).encode("utf-8"), tid + " frozen source differs from generator")
            else:
                require(not source.startswith(b"NRB "), tid + " static source contains a recursively exported header")
        require(read_json(ROOT / "tasks/v2.0/catalog.json") == generated, "Frozen catalog differs from current contracts")
        return source_hashes
    check(evidence, "frozen generated prompts and hashed static sources", frozen_sources)

    def candidate_exports():
        with tempfile.TemporaryDirectory(prefix="nrb-v2-release-packets-") as directory:
            exported = export_tasks(directory, "all", 17)
            target = Path(directory)
            require({p.name for p in target.iterdir()} == {*(t + ".md" for t in ALL_IDS), "manifest.json", "catalog.json"},
                    "Prompt export contains unexpected evaluator/reference files")
            require(len(exported["tasks"]) == 20, "Prompt export lost tasks")
            for row in exported["tasks"]:
                packet = candidate(row["task_id"], 17)
                payload = (target / row["file"]).read_bytes()
                require(payload == packet["content"].encode("utf-8") and sha256(payload) == row["sha256"],
                        row["task_id"] + " exported bytes differ")
            require(read_json(target / "catalog.json") == generated, "Exported catalog differs")
        lean = module("L01")
        files = lean.candidate_files(17)
        require(set(files) == {"L01.md", "NRBPrelude.lean", "lean-toolchain", "proofs.template.json"}, "Lean candidate allowlist changed")
        require(files["NRBPrelude.lean"] == lean.PRELUDE and files["lean-toolchain"] == "leanprover/lean4:v4.19.0\n",
                "Lean candidate definitions/toolchain differ from evaluator")
        require(json.loads(files["proofs.template.json"]) == {key: "" for key in lean.GOALS}, "Lean candidate template contains proofs")
        return {"prompt_count": 20, "lean_candidate_files": sorted(files)}
    check(evidence, "candidate-only exports reproduce all public prompts", candidate_exports)

    def allowed_assets():
        records = []
        for tid in MANUAL_IDS:
            for mode in (("A", "B") if tid == "R06" else (None,)):
                definition = rubric_spec(tid, mode)
                require(sum(d["weight"] for d in definition["rubric"]) == 100, "Invalid manual score scale")
                mappings = candidate_inputs(tid, mode)
                for item in mappings:
                    source = ROOT / item["source"]
                    require(source.is_file() and not source.is_symlink(), "Missing/unsafe input: " + item["source"])
                    require(source.resolve().is_relative_to(ROOT), "Input outside repository")
                    payload = source.read_bytes()
                    require(bool(payload), "Empty input: " + item["source"])
                    records.append({"task": tid, "mode": mode, "path": item["path"], "bytes": len(payload), "sha256": sha256(payload)})
                if tid == "R06":
                    reference_count = sum(Path(item["path"]).name == "reference.mp4" for item in mappings)
                    require(reference_count == (1 if mode == "B" else 0), "R06 A/B reference boundary violated")
        for tid in ALL_IDS:
            for mode in (("A", "B") if tid == "R06" else (None,)):
                # Independently reconstruct hashes from the bytes actually
                # delivered, including the wrapped prompt rather than TASK.md.
                payloads = {tid + ".md": candidate(tid, 17)["content"].encode("utf-8")}
                if tid in MANUAL_IDS:
                    for item in candidate_inputs(tid, mode):
                        if item["source"] != "tasks/v2.0/" + tid + ".md":
                            payloads[item["path"]] = (ROOT / item["source"]).read_bytes()
                elif tid == "L01":
                    payloads.update({name: value.encode("utf-8") for name, value in module(tid).candidate_files(17).items()
                                     if name != "L01.md"})
                actual = [{"path": name, "bytes": len(data), "sha256": sha256(data)} for name, data in sorted(payloads.items())]
                current = input_manifest(tid, 17, mode)
                require(current["files"] == actual and current["sha256"] == fingerprint(actual), tid + " full candidate input identity differs")
                if tid in MANUAL_IDS:
                    review = blank_review(tid, mode)
                    require(review["packet_hash"] == candidate(tid, 17)["packet_hash"] and
                            review["input_manifest_hash"] == current["sha256"], tid + " manual review is not bound to actual input bytes")
        return records
    check(evidence, "rubric input allowlists resolve and R06 modes stay separate", allowed_assets)

    def web_contract():
        text = (ROOT / "web/dist/release-data.js").read_text(encoding="utf-8")
        prefix = "globalThis.NRB_RELEASE = "
        require(text.startswith(prefix) and text.rstrip().endswith(";"), "Unexpected release-data syntax")
        release = json.loads(text[len(prefix):].rstrip().removesuffix(";"))
        require(release["version"] == __version__ and release["status"] == "complete", "Site version/scope is stale")
        rows = release["tasks"]
        require(len(rows) == 20 and {x["id"] for x in rows} == set(ALL_IDS), "Site does not contain all 20 tasks")
        for row in rows:
            tid = row["id"]
            require(row["status"] == "ready" and row["packet"] == "packets-v2/" + tid + ".md", "Site task is not ready")
            packet = candidate(tid, 17)
            require(row["packetHash"] == packet["packet_hash"], tid + " site packet digest differs")
            require((ROOT / "web/dist" / row["packet"]).read_bytes() == packet["content"].encode("utf-8"), tid + " site prompt bytes differ")
            for field in ("scoring", "required_artifacts", "manual_review_required", "time_budget_s"):
                require(row.get(field) == spec(tid).get(field), tid + " site metadata differs: " + field)
        require(release["grading"] == public_manifest((0, 17, 2026)), "Site evaluator identity/check weights are stale")
        expected_rubrics = {}
        for tid in MANUAL_IDS:
            for mode in (("A", "B") if tid == "R06" else (None,)):
                expected_rubrics[tid + ("-" + mode if mode else "")] = {"spec": rubric_spec(tid, mode), "hash": rubric_hash(tid, mode),
                                                                    "input_manifest_hash": input_manifest(tid, 17, mode)["sha256"]}
        require(release["rubrics"] == expected_rubrics, "Site rubric evidence protocol differs")
        return {"public_prompts": len(rows), "automatic_tasks": 13, "rubric_protocols": len(expected_rubrics)}
    check(evidence, "actual site prompts, rubrics and automatic manifests match evaluator", web_contract)
    return evidence


def inspect_image(image):
    docker = shutil.which("docker")
    require(docker is not None, "Docker executable unavailable")
    completed = subprocess.run([docker, "image", "inspect", image], capture_output=True, text=True, timeout=30)
    require(completed.returncode == 0, "Cannot inspect runtime " + image + ": " + completed.stderr[-1000:])
    rows = json.loads(completed.stdout)
    require(len(rows) == 1 and rows[0]["Id"].startswith("sha256:"), "No immutable image ID")
    return {key: rows[0].get(key) for key in ("Id", "RepoTags", "RepoDigests", "Created", "Architecture", "Os")}


def controls(args):
    evidence = new_evidence("actual_reference_and_wrong_controls")
    evidence.update(execution_requested=args.execution, seeds=args.seeds, mutant_selection=args.mutants, entries=[], images={})
    evidence["scope"] = "Twelve source-code tasks execute in the requested runtime. H02 verifies submitted numeric data. All are reviewed author controls, never model performance."
    if args.execution == "docker":
        def snapshot():
            evidence["images"] = {"python_fortran": inspect_image(args.image), "lean": inspect_image(args.lean_image)}
            return evidence["images"]
        if not check(evidence, "actual immutable runtime images are available", snapshot):
            return evidence
    evaluator = evidence["evaluator_identity"]["evaluator_fingerprint"]
    for tid in OBJECTIVE_IDS:
        task = module(tid)
        selected = [(seed, "reference", task.reference_submission(seed)) for seed in args.seeds]
        if args.mutants != "none":
            mutants = [(label, submission) for label, submission in task.mutants(17).items() if label != "reference"]
            require(bool(mutants), tid + " has no negative control")
            if args.mutants == "representative":
                mutants = mutants[:1]
            selected.extend((17, label, submission) for label, submission in mutants)
        for seed, label, submission in selected:
            image_id = None
            if args.execution == "docker" and tid in CODING_IDS:
                image_id = evidence["images"]["lean" if tid == "L01" else "python_fortran"]["Id"]
            row = {"task_id": tid, "seed": seed, "label": label, "not_model_performance": True}
            def run_control():
                report = grade(tid, dict(submission, task_id=tid), seed=seed, backend=args.execution,
                               timeout=args.timeout, image=image_id)
                row["report"] = report
                validate_report(report)
                require(report["score"] is not None, "Runtime unavailable: " + str(report["execution"].get("error")))
                expected_backend = "answer" if tid == "H02" and args.execution == "docker" else args.execution
                require(report["execution"]["backend"] == expected_backend, "Unexpected execution backend")
                require(report["evaluator_fingerprint"] == evaluator, "Evaluator sources changed during controls")
                require(report["manual_review_required"] is False, "Automatic task has manual gate")
                if image_id is not None:
                    require(report["execution"].get("image_id") == image_id, "Report is not tied to inspected immutable image")
                require((report["score"] == 100) if label == "reference" else report["score"] < 100,
                        "Wrong reference/mutant outcome: " + str(report["score"]))
                if label == "reference":
                    require(report["execution"]["status"] == "executed" and report["status"] == "passed", "Reference did not actually complete")
                return {"score": report["score"], "execution_status": report["execution"]["status"], "image_id": image_id}
            row["passed"] = check(evidence, f"{tid} seed={seed} {label}", run_control)
            evidence["entries"].append(row)
    def coverage():
        for seed in args.seeds:
            observed = [r["task_id"] for r in evidence["entries"] if r["seed"] == seed and r["label"] == "reference"]
            require(len(observed) == 13 and set(observed) == set(OBJECTIVE_IDS), "Reference coverage is incomplete")
        if args.mutants != "none":
            require({r["task_id"] for r in evidence["entries"] if r["label"] != "reference"} == set(OBJECTIVE_IDS), "Wrong-control coverage is incomplete")
        require(identity()["evaluator_fingerprint"] == evaluator, "Evaluator changed during controls")
        return {"reference_runs": sum(r["label"] == "reference" for r in evidence["entries"]),
                "wrong_controls": sum(r["label"] != "reference" for r in evidence["entries"]),
                "unscored": sum(r.get("report", {}).get("score") is None for r in evidence["entries"])}
    check(evidence, "complete automatic-task coverage and stable evaluator", coverage)
    return evidence


def seeds(value):
    try:
        result = list(map(int, value.split(",")))
        if not result or len(result) != len(set(result)) or any(not 0 <= x < 2**32 for x in result):
            raise ValueError
        return result
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Use distinct uint32 seeds separated by commas") from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("contracts", "controls"):
        child = sub.add_parser(command)
        child.add_argument("--out", type=Path, required=True)
        if command == "controls":
            child.add_argument("--execution", choices=("trusted", "docker"), default="docker")
            child.add_argument("--seeds", type=seeds, default=[17])
            child.add_argument("--mutants", choices=("none", "representative", "all"), default="all")
            child.add_argument("--image", default="nrb-v2:local")
            child.add_argument("--lean-image", default="nrb-v2-lean:local")
            child.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args(argv)
    if args.out.exists() or args.out.is_symlink():
        parser.error("Choose a new evidence filename; existing evidence is never overwritten")
    if args.command == "controls" and (not math.isfinite(args.timeout) or not 0 < args.timeout <= 3600):
        parser.error("timeout must lie in (0,3600]")
    started = time.monotonic()
    evidence = contracts() if args.command == "contracts" else controls(args)
    evidence["passed"] = bool(evidence["checks"]) and all(c["passed"] for c in evidence["checks"])
    evidence["wall_seconds"] = time.monotonic() - started
    evidence["report_hash"] = fingerprint(evidence)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(evidence, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"passed": evidence["passed"], "checks": len(evidence["checks"]), "evidence": str(args.out)}))
    return 0 if evidence["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

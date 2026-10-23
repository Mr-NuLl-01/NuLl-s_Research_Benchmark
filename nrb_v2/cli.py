"""Small standard-library CLI for file-based, fully automatic Python evaluation."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys

from . import __version__
from .grading import grade, identity, load_source, load_submission, public_manifest, validate_report
from .registry import PYTHON_IDS, ids, module, spec


def write(path, data):
    payload = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8") as stream:
            stream.write(payload)
    else:
        print(payload)


def read(path):
    def invalid(value):
        raise ValueError("Nonfinite JSON constant: " + value)
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key: " + key)
            result[key] = value
        return result
    target = Path(path)
    if target.stat().st_size > 5 * 1024 * 1024:
        raise ValueError("JSON input exceeds 5 MiB")
    return json.loads(target.read_text(encoding="utf-8"), parse_constant=invalid, object_pairs_hook=unique)


def batch(input_directory, output_directory, seed=17, backend="docker", timeout=120, image=None):
    source = Path(input_directory)
    dest = Path(output_directory)
    if not source.is_dir() or source.is_symlink():
        raise ValueError("Batch input must be an existing real directory")
    if type(seed) is not int or not 0 <= seed < 2**32:
        raise ValueError("Seed must be an integer in [0,2**32)")
    if backend not in ("docker", "none"):
        raise ValueError("Batch execution supports docker or none")
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 3600:
        raise ValueError("Timeout must be finite and in (0,3600]")
    planned_files = [dest / "summary.json", *(dest / (tid + ".json") for tid in PYTHON_IDS)]
    if any(path.exists() for path in planned_files):
        raise FileExistsError("Output reports already exist; select a new results directory")
    dest.mkdir(parents=True, exist_ok=True)
    entries = []
    for task_id in PYTHON_IDS:
        path = source / task_id / "solution.py"
        if not path.exists() and not path.is_symlink():
            entries.append({"task_id": task_id, "status": "not_submitted", "score": None,
                            "report_file": None, "comparison_eligible": False})
            continue
        try:
            if (source / task_id).is_symlink():
                raise ValueError("Submission task directory cannot be a symlink")
            submission = load_source(task_id, path)
        except (ValueError, OSError, UnicodeError) as exc:
            message = type(exc).__name__ + ": " + str(exc)[:1000]
            entries.append({"task_id": task_id, "status": "submission_invalid", "score": None,
                            "report_file": None, "comparison_eligible": False, "error": message})
            print(f"{task_id}: submission_invalid / {message}", file=sys.stderr)
            continue
        report = grade(task_id, submission, seed, backend, timeout, image)
        write(dest / (task_id + ".json"), report)
        entries.append({"task_id": task_id, "status": report["status"], "score": report["score"],
                        "report_file": task_id + ".json", "comparison_eligible": report["comparison_eligible"]})
        print(f"{task_id}: {report['status']} / score={report['score']}", file=sys.stderr)
    scored = [item["score"] for item in entries if item["score"] is not None]
    complete = len(scored) == len(PYTHON_IDS)
    summary = {"schema": "nrb-batch-v2", "benchmark_version": __version__, **identity(), "seed": seed,
               "created_at": datetime.now(timezone.utc).isoformat(), "entries": entries,
               "coverage": {"submitted": sum(i["status"] != "not_submitted" for i in entries),
                            "scored": len(scored), "passed": sum(i["status"] == "passed" for i in entries), "total": 8},
               "mean_score": round(math.fsum(scored) / 8, 6) if complete else None,
               "subset_mean": round(math.fsum(scored) / len(scored), 6) if scored else None,
               "complete": complete, "status": "complete" if complete else "partial" if scored else "unscored",
               "note": "Missing submissions and unavailable environments are null, not zero. Full-suite mean exists only at 8/8 scored coverage."}
    write(dest / "summary.json", summary)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(prog="nrb-v2", description="NRB V2 phase one: eight Python tasks, 100% automatic scores")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("list"); p.add_argument("--tasks", default="all")
    commands.add_parser("identity")
    p = commands.add_parser("manifest"); p.add_argument("--seeds", default="0,17,2026"); p.add_argument("--out")
    p = commands.add_parser("grade"); p.add_argument("--task", choices=PYTHON_IDS, required=True)
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument("--source"); source.add_argument("--submission-dir"); source.add_argument("--submission")
    p.add_argument("--seed", type=int, default=17); p.add_argument("--image", default="nrb-v2-python:local")
    p.add_argument("--execution", choices=("docker", "none"), default="docker")
    p.add_argument("--timeout", type=float, default=120); p.add_argument("--out", required=True)
    p = commands.add_parser("batch"); p.add_argument("--input", required=True); p.add_argument("--out-dir", required=True)
    p.add_argument("--seed", type=int, default=17); p.add_argument("--image", default="nrb-v2-python:local")
    p.add_argument("--execution", choices=("docker", "none"), default="docker"); p.add_argument("--timeout", type=float, default=120)
    p = commands.add_parser("validate-report"); p.add_argument("report"); p.add_argument("--out")
    p = commands.add_parser("export"); p.add_argument("--tasks", default="python"); p.add_argument("--dest", required=True)
    p.add_argument("--seed", type=int, default=17)
    p = commands.add_parser("selftest"); p.add_argument("--tasks", default="python"); p.add_argument("--seeds", default="17")
    p.add_argument("--include-mutants", action="store_true"); p.add_argument("--execution", choices=("trusted", "docker"), default="trusted")
    p.add_argument("--image", default="nrb-v2-python:local"); p.add_argument("--timeout", type=float, default=120); p.add_argument("--out")
    args = parser.parse_args(argv)
    try:
        if args.command == "list":
            write(None, [spec(t) for t in ids(args.tasks)])
        elif args.command == "identity":
            write(None, identity())
        elif args.command == "manifest":
            write(args.out, public_manifest(tuple(map(int, args.seeds.split(",")))))
        elif args.command == "grade":
            if args.source:
                submission = load_source(args.task, args.source)
            elif args.submission_dir:
                submission = load_submission(args.task, args.submission_dir)
            else:
                submission = read(args.submission)
            # Never execute candidate code if writing its report would overwrite
            # a prior attempt. Attempts are separately preserved.
            if Path(args.out).exists():
                raise FileExistsError("Report already exists; choose a new output filename")
            report = grade(args.task, submission, args.seed, args.execution, args.timeout, args.image)
            write(args.out, report)
            print(f"{args.task}: {report['status']}; score={report['score']} / 100; report={args.out}", file=sys.stderr)
        elif args.command == "batch":
            result = batch(args.input, args.out_dir, args.seed, args.execution, args.timeout, args.image)
            print(json.dumps({"out_dir": args.out_dir, "coverage": result["coverage"], "mean_score": result["mean_score"]}, ensure_ascii=False))
        elif args.command == "validate-report":
            report = validate_report(read(args.report))
            write(args.out, {"valid": True, "task_id": report["task_id"], "status": report["status"], "score": report["score"],
                             "note": "Integrity and score consistency checked; not a signature or program re-execution."})
        elif args.command == "export":
            from .packets import export_tasks
            result = export_tasks(args.dest, args.tasks, args.seed)
            print(json.dumps({"destination": args.dest, "tasks": len(result["tasks"])}, ensure_ascii=False))
        elif args.command == "selftest":
            entries = []
            for seed in map(int, args.seeds.split(",")):
                for task_id in ids(args.tasks):
                    mod = module(task_id)
                    variants = mod.mutants(seed) if args.include_mutants else {"reference": mod.reference_submission(seed)}
                    for label, submission in variants.items():
                        report = grade(task_id, dict(submission, task_id=task_id), seed, args.execution, args.timeout, args.image)
                        expected = report["score"] is not None and ((report["score"] == 100) == (label == "reference"))
                        entries.append({"task_id": task_id, "seed": seed, "label": label, "score": report["score"],
                                        "execution_status": report["execution"]["status"], "passed": expected,
                                        "unscored": report["score"] is None, "critical_failures": report["critical_failures"],
                                        "error": report["execution"].get("error")})
            result = {"kind": "reference_and_mutant_validation", "not_model_performance": True, "api_provider_calls": 0,
                      "benchmark_version": __version__, **identity(), "entries": entries,
                      "passed": bool(entries) and all(e["passed"] for e in entries),
                      "unscored_count": sum(e["unscored"] for e in entries)}
            write(args.out, result)
            return 0 if result["passed"] else 1
        return 0
    except (ValueError, KeyError, TypeError, OSError, UnicodeError) as exc:
        print(f"nrb-v2: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

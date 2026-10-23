"""Execute Python submissions and derive every score from fixed check weights."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from pathlib import Path
import platform
import re
import subprocess

from nrb_v1.artifacts import decode, validate_submission
from nrb_v1.execution import execute
from nrb_v1.grading import compare_value, EXACT_INTEGER_PATHS
from nrb_v1.provenance import fingerprint
from . import __version__, GRADER_VERSION, REPORT_SCHEMA
from .packets import candidate
from .registry import PYTHON_IDS, LEGACY, cases, module


def identity():
    root = Path(__file__).resolve().parent.parent
    files = {}
    for directory in ("nrb_v1", "nrb_v2"):
        for path in sorted((root / directory).rglob("*.py")):
            files[path.relative_to(root).as_posix()] = fingerprint(path.read_bytes())
    info = {"grader_version": GRADER_VERSION,
            "evaluator_fingerprint": fingerprint({"algorithm": "sha256-path-content-v1", "files": files}),
            "source_commit": None, "source_dirty": None}
    try:
        commit = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=3)
        state = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--", "nrb_v1", "nrb_v2"],
                               capture_output=True, text=True, timeout=3)
        if commit.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", commit.stdout.strip()):
            info.update(source_commit=commit.stdout.strip(), source_dirty=bool(state.stdout.strip()) if state.returncode == 0 else None)
    except (OSError, subprocess.SubprocessError):
        pass
    return info


def _manifest(test_cases):
    return [{"id": c["id"], "tier": c["tier"], "weight": c["weight"],
             "critical": bool(c.get("critical", False))} for c in test_cases]


def test_manifest_hash(task_id, seed, test_cases):
    # Bind the test contract and numerical generator version, not incidental
    # last-bit platform variation in recomputed transcendental reference values.
    contract = [{**m, "rtol": c.get("rtol", 1e-8), "atol": c.get("atol", 1e-10),
                 "expected_error": c.get("error")} for m, c in zip(_manifest(test_cases), test_cases)]
    return fingerprint({"benchmark_version": __version__, "task_id": task_id, "seed": seed, "checks": contract})


def public_manifest(seeds=(0, 17, 2026)):
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("Manifest seeds must be nonempty and unique")
    tasks = {}
    for task_id in PYTHON_IDS:
        seed_entries = {}
        for seed in seeds:
            test_cases = cases(task_id, seed)
            seed_entries[str(seed)] = {"packet_hash": candidate(task_id, seed)["packet_hash"],
                                       "test_manifest_hash": test_manifest_hash(task_id, seed, test_cases),
                                       "checks": _manifest(test_cases)}
        tasks[task_id] = {"packet_hash": candidate(task_id, 17)["packet_hash"], "seeds": seed_entries}
    return {"schema": REPORT_SCHEMA, "version": __version__, "grader_version": GRADER_VERSION,
            "evaluatorFingerprint": identity()["evaluator_fingerprint"],
            "seed_policy": "The manifest binds seed, check contract and evaluator source. Execution records separately hash actual numerical inputs.",
            "tasks": tasks}


def _score(checks):
    if any(c["passed"] is None for c in checks):
        return None
    return round(100 * math.fsum(c["weight"] for c in checks if c["passed"] is True) /
                 math.fsum(c["weight"] for c in checks), 6)


def _derived(checks):
    score = _score(checks)
    status = "unscored" if score is None else "passed" if all(c["passed"] is True for c in checks) else "failed"
    critical = [c for c in checks if c["critical"]]
    critical_passed = (None if any(c["passed"] is None for c in critical)
                       else all(c["passed"] is True for c in critical))
    tiers = {}
    for tier in ("basic", "scientific", "stress"):
        group = [c for c in checks if c["tier"] == tier]
        tiers[tier] = {"earned_weight": sum(c["weight"] for c in group if c["passed"] is True),
                       "scored_weight": sum(c["weight"] for c in group if c["passed"] is not None),
                       "max_weight": sum(c["weight"] for c in group)}
    return {"score": score, "total": score, "status": status, "critical_passed": critical_passed,
            "critical_failures": [c["id"] for c in critical if c["passed"] is False],
            "completion_status": "infrastructure_unscored" if score is None else "complete" if status == "passed" else "failed",
            "tier_scores": tiers, "passed_checks": sum(c["passed"] is True for c in checks),
            "failed_checks": sum(c["passed"] is False for c in checks),
            "unscored_checks": sum(c["passed"] is None for c in checks)}


def load_source(task_id, source):
    path = Path(source)
    if path.is_symlink() or not path.is_file():
        raise ValueError("Source must be an existing regular file, not a symlink")
    if path.stat().st_size > 2 * 1024 * 1024:
        raise ValueError("Source file exceeds 2 MiB")
    return {"task_id": task_id, "artifacts": {"solution.py": path.read_text(encoding="utf-8")}, "answer": {}}


def load_submission(task_id, directory):
    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("Submission directory must be an existing real directory")
    return load_source(task_id, directory / "solution.py")


def grade(task_id, submission, seed=17, backend="docker", timeout=120, image=None):
    if task_id not in PYTHON_IDS:
        raise ValueError("Only P01–P08 are released for execution in this phase")
    if backend not in ("docker", "trusted", "none"):
        raise ValueError("Unsupported execution backend")
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 3600:
        raise ValueError("Timeout must be finite and in (0,3600]")
    validate_submission(submission, task_id)
    source = submission["artifacts"].get("solution.py")
    if source is not None and len(decode(source)) > 2 * 1024 * 1024:
        raise ValueError("Source file exceeds 2 MiB")
    slim = {"task_id": task_id, "artifacts": {} if source is None else {"solution.py": source}, "answer": {}}
    test_cases = cases(task_id, seed)
    manifest = _manifest(test_cases)
    checks = []
    if source is None:
        execution = {"backend": backend, "language": "python", "status": "unavailable", "error": "Missing solution.py"}
        records = []
    else:
        try:
            result = execute(module(task_id), slim, test_cases, backend, timeout,
                             image or ("nrb-v2-python:local" if backend == "docker" else None))
            records = result["records"]
            execution = {k: v for k, v in result.items() if k != "records"}
            if execution.get("status") == "unavailable" and backend == "docker":
                execution["error"] = execution.get("error", "Docker execution unavailable").replace(
                    "environments/v1/Dockerfile", "environments/v2/Dockerfile")
                execution["error"] += "; start Docker, then run Build-Environment or build nrb-v2-python:local from environments/v2/Dockerfile"
        except (OSError, subprocess.SubprocessError) as exc:
            execution = {"backend": backend, "language": "python", "status": "unavailable",
                         "error": type(exc).__name__ + ": " + str(exc)[:1000]}
            records = []
    for i, case in enumerate(test_cases):
        if execution["status"] == "unavailable":
            passed, detail = None, execution.get("error", "Execution unavailable")
        else:
            record = records[i]
            if "error" in case:
                passed = record.get("ok") is False and record.get("error") == case["error"]
                detail = "" if passed else "Required exception behavior did not match"
            elif record.get("ok") is not True:
                passed, detail = False, str(record.get("error")) + ": " + str(record.get("detail", ""))[:1000]
            elif hasattr(module(task_id), "validate_output"):
                passed, detail = module(task_id).validate_output(case, record["value"])
            else:
                passed, detail = compare_value(record["value"], case["expected"], case.get("rtol", 1e-8),
                                                case.get("atol", 1e-10),
                                                exact_integer_paths=EXACT_INTEGER_PATHS[LEGACY[task_id]])
            passed = bool(passed)
        checks.append({**manifest[i], "passed": passed, "detail": detail})
    info = identity()
    derived = _derived(checks)
    report = {"schema": REPORT_SCHEMA, "benchmark_version": __version__, **info,
              "task_id": task_id, "seed": seed, "created_at": datetime.now(timezone.utc).isoformat(),
              "packet_hash": candidate(task_id, seed)["packet_hash"],
              "test_manifest_hash": test_manifest_hash(task_id, seed, test_cases),
              "scoring": "automatic", "manual_review_required": False, "max_score": 100,
              "weight_total": sum(c["weight"] for c in checks), "checks": checks, **derived,
              "execution": execution,
              "environment": {"evaluator_python": platform.python_version(), "platform": platform.system(), "machine": platform.machine()},
              "submission_hash": fingerprint(slim), "source_hash": fingerprint(decode(source)) if source is not None else fingerprint(b""),
              "report_origin": "local_verifier", "control_only": backend == "trusted",
              "comparison_eligible": derived["score"] is not None and backend == "docker",
              "trust_note": "Local execution report. Browser import does not rerun code. Hashes detect changes but are not an authenticity signature."}
    report["report_hash"] = fingerprint(report)
    return report


def validate_report(report, current=True):
    if not isinstance(report, dict) or report.get("schema") != REPORT_SCHEMA:
        raise ValueError("Expected " + REPORT_SCHEMA)
    if report.get("benchmark_version") != __version__ or report.get("grader_version") != GRADER_VERSION:
        raise ValueError("Incompatible benchmark or grader version")
    task_id, seed = report.get("task_id"), report.get("seed")
    if task_id not in PYTHON_IDS or type(seed) is not int:
        raise ValueError("Invalid task or seed")
    test_cases = cases(task_id, seed)
    expected = _manifest(test_cases)
    checks = report.get("checks")
    if not isinstance(checks, list) or len(checks) != len(expected):
        raise ValueError("Missing or extra checks")
    for actual, contract in zip(checks, expected):
        if not isinstance(actual, dict) or any(actual.get(k) != v or type(actual.get(k)) is not type(v) for k, v in contract.items()):
            raise ValueError("Check ID/order/weight/tier/critical flag differs from the release manifest")
        if type(actual.get("passed")) is not bool and actual.get("passed") is not None:
            raise ValueError("Check outcomes must be true, false or null")
        if not isinstance(actual.get("detail"), str):
            raise ValueError("Every check requires a detail string")
    if any(c["passed"] is None for c in checks) and not all(c["passed"] is None for c in checks):
        raise ValueError("Partially unscored reports are not produced by this evaluator")
    for key, expected_value in _derived(checks).items():
        if report.get(key) != expected_value or (key in ("score", "total") and isinstance(report.get(key), bool)):
            raise ValueError("Derived field disagrees with fixed check weights: " + key)
        if isinstance(expected_value, bool) and type(report.get(key)) is not bool:
            raise ValueError("Derived boolean field has wrong type: " + key)
    if report.get("packet_hash") != candidate(task_id, seed)["packet_hash"]:
        raise ValueError("Candidate packet hash mismatch")
    if report.get("test_manifest_hash") != test_manifest_hash(task_id, seed, test_cases):
        raise ValueError("Test contract hash mismatch")
    if report.get("weight_total") != 70 or report.get("max_score") != 100 or report.get("manual_review_required") is not False:
        raise ValueError("Objective scoring contract changed")
    if report.get("scoring") != "automatic" or report.get("report_origin") != "local_verifier":
        raise ValueError("Unsupported report origin")
    execution = report.get("execution")
    if not isinstance(execution, dict) or execution.get("backend") not in ("docker", "trusted", "none"):
        raise ValueError("Invalid execution backend")
    backend, status = execution["backend"], execution.get("status")
    if status not in ("executed", "failed", "unavailable"):
        raise ValueError("Invalid execution status")
    if (report["score"] is None) is not (status == "unavailable"):
        raise ValueError("Execution status disagrees with score availability")
    if status == "failed" and (report["score"] != 0 or any(c["passed"] is not False for c in checks)):
        raise ValueError("A failed worker must fail every check and score zero")
    if backend == "none" and status != "unavailable":
        raise ValueError("Disabled execution cannot be scored")
    if report.get("control_only") is not (backend == "trusted"):
        raise ValueError("Control flag disagrees with execution backend")
    if report.get("comparison_eligible") is not (report["score"] is not None and backend == "docker"):
        raise ValueError("Comparison eligibility disagrees with execution conditions")
    for key in ("submission_hash", "source_hash", "evaluator_fingerprint", "report_hash"):
        if not isinstance(report.get(key), str) or not re.fullmatch(r"[0-9a-f]{64}", report[key]):
            raise ValueError("Invalid " + key)
    if fingerprint({k: v for k, v in report.items() if k != "report_hash"}) != report["report_hash"]:
        raise ValueError("Report content hash mismatch; this is an integrity check, not authentication")
    if current and report["evaluator_fingerprint"] != identity()["evaluator_fingerprint"]:
        raise ValueError("Evaluator sources changed; use the selected release to regrade")
    return report

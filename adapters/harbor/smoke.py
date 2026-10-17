"""Run real Harbor/Docker oracle trials and verify the complete NRB reports.

This is evaluator/runtime validation only, never a model-performance result.
The default three tasks cover both code executors and editable SVG grading.
CLI flags and result paths were checked against Harbor tag v0.24.0 source.
"""
from __future__ import annotations

import argparse
from importlib.metadata import version
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys


REPO = Path(__file__).resolve().parents[2]


def check_job(job_dir, expected_ids, *, seed=0):
    """Check actual single-step TrialPaths, not just Harbor's aggregate mean."""
    job_dir = Path(job_dir)
    expected_ids = set(expected_ids)
    trial_paths = sorted(job_dir.glob("*/result.json"))
    entries, reports, seen = [], [], set()
    for path in trial_paths:
        trial = json.loads(path.read_text(encoding="utf-8"))
        entry = {"trial": path.parent.name, "passed": False,
                 "exception_info": trial.get("exception_info")}
        entries.append(entry)
        report_path = path.parent / "verifier" / "report.json"
        reward_path = path.parent / "verifier" / "reward.txt"
        if not report_path.is_file() or not reward_path.is_file():
            entry["error"] = "Missing canonical verifier report or scalar reward"
            continue
        report = json.loads(report_path.read_text(encoding="utf-8"))
        reward = float(reward_path.read_text(encoding="utf-8").strip())
        from nrb.core import validate_final_report
        try:
            validate_final_report(report)
        except ValueError as exc:
            entry["error"] = "Invalid canonical verifier report: " + str(exc)
            continue
        task_id = report["task_id"]
        duplicate = task_id in seen
        seen.add(task_id)
        from nrb.provenance import evaluator_identity, identity_from
        report_ok = (identity_from(report) == evaluator_identity() and report.get("adapter") == "harbor" and report.get("seed") == seed
                     and report["auto_points"] == 70 and report["auto_percent"] == 100
                     and report["coverage"] == 1 and not report["critical_failures"]
                     and report["review_pending"] is True and report["total"] is None
                     and report["input_integrity"]["unchanged"] is True
                     and report["comparison_eligible"] is True
                     and report["verifier_log_permissions"] == {"owner_uid": 0, "mode": "0o755"})
        trial_ok = (trial.get("exception_info") is None
                    and trial.get("verifier_environment_mode") == "separate"
                    and (trial.get("verifier_result") or {}).get("rewards") == {"reward": 1.0})
        reward_ok = math.isfinite(reward) and math.isclose(reward, 1.0, abs_tol=1e-12)
        entry.update(task_id=task_id, reward=reward, auto_points=report["auto_points"],
                     coverage=report["coverage"], duplicate=duplicate,
                     passed=report_ok and trial_ok and reward_ok and not duplicate
                     and task_id in expected_ids)
        reports.append(report)
    result = {"kind": "harbor_oracle_runtime_smoke", "not_model_performance": True,
              "job_dir": str(job_dir), "expected_tasks": sorted(expected_ids),
              "missing_tasks": sorted(expected_ids - seen), "trial_count": len(trial_paths),
              "entries": entries, "reports": reports,
              "passed": len(trial_paths) == len(expected_ids) and seen == expected_ids
                        and all(entry["passed"] for entry in entries)}
    return result


def _run(argv, *, cwd, stdout_path, stderr_path, timeout):
    with stdout_path.open("w", encoding="utf-8") as stdout:
        with stderr_path.open("w", encoding="utf-8") as stderr:
            return subprocess.run(argv, cwd=cwd, stdout=stdout, stderr=stderr,
                                  text=True, timeout=timeout).returncode


def run_smoke(dest, *, tasks="NRB04,NRB05,NRB09", seed=0,
              python_image="python:3.12-slim", timeout=1800,
              expected_version="0.24.0"):
    from nrb.core import TASK_IDS
    from harbor.models.task.config import TaskConfig

    harbor_version = version("harbor")
    if harbor_version != expected_version:
        raise RuntimeError(f"Expected Harbor {expected_version}; found {harbor_version}")
    harbor, docker = shutil.which("harbor"), shutil.which("docker")
    if not harbor or not docker:
        raise RuntimeError("Both Harbor and Docker must be installed; this is a real container smoke test")
    task_ids = list(TASK_IDS) if tasks == "all" else tasks.split(",")
    if not task_ids or len(set(task_ids)) != len(task_ids) or not set(task_ids) <= set(TASK_IDS):
        raise ValueError("Choose distinct NRB task IDs or all")
    dest = Path(dest).resolve()
    if dest.exists() or dest.is_symlink():
        raise FileExistsError("Harbor smoke output directory must be new")
    dest.mkdir(parents=True)
    export_dir, jobs_dir = dest / "export", dest / "jobs"
    export_argv = [sys.executable, "-m", "nrb", "export", "--format", "harbor",
                   "--seed", str(seed), "--tasks", ",".join(task_ids), "--python-image", python_image,
                   "--include-oracle", "--dest", str(export_dir)]
    exported = _run(export_argv, cwd=REPO, stdout_path=dest / "export-stdout.txt",
                    stderr_path=dest / "export-stderr.txt", timeout=60)
    if exported:
        raise RuntimeError(f"NRB export failed; see {dest}")
    # Validate against the installed release's actual Pydantic configuration.
    for path in sorted(export_dir.glob("nrb*/task.toml")):
        config = TaskConfig.model_validate_toml(path.read_text(encoding="utf-8"))
        data = config.model_dump(mode="json")
        if (data["schema_version"] != "1.4" or data["verifier"]["environment_mode"] != "separate"
                or data["verifier"]["environment"]["network_mode"] != "no-network"):
            raise RuntimeError("Harbor schema silently changed the required verifier contract")
    _run([docker, "version"], cwd=dest, stdout_path=dest / "docker-version.txt",
         stderr_path=dest / "docker-version-stderr.txt", timeout=30)
    argv = [harbor, "run", "-p", str(export_dir), "-a", "oracle", "--env", "docker",
            "--jobs-dir", str(jobs_dir), "--job-name", "oracle",
            "--n-concurrent", "1", "--n-attempts", "1", "--max-retries", "0"]
    timed_out = False
    try:
        exit_code = _run(argv, cwd=dest, stdout_path=dest / "harbor-stdout.txt",
                         stderr_path=dest / "harbor-stderr.txt", timeout=timeout)
    except subprocess.TimeoutExpired:
        exit_code, timed_out = None, True
    result = check_job(jobs_dir / "oracle", task_ids, seed=seed)
    result.update(harbor_version=harbor_version, schema_version="1.4", command_argv=argv,
                  python_image=python_image, seed=seed, cli_exit_code=exit_code,
                  timed_out=timed_out, api_provider_calls=0)
    result["passed"] = result["passed"] and exit_code == 0 and not timed_out
    (dest / "smoke_report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not result["passed"]:
        raise RuntimeError(f"Harbor smoke failed; inspect {dest / 'smoke_report.json'} and trial logs")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", required=True)
    parser.add_argument("--tasks", default="NRB04,NRB05,NRB09")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--python-image", default="python:3.12-slim")
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--expected-version", default="0.24.0")
    args = parser.parse_args()
    report = run_smoke(args.dest, tasks=args.tasks, seed=args.seed,
                       python_image=args.python_image, timeout=args.timeout,
                       expected_version=args.expected_version)
    print(json.dumps({key: value for key, value in report.items() if key != "reports"},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

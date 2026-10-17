"""Run the installed promptfoo CLI against ten deliberately empty submissions.

No model provider or submitted Python code is executed. The expected CLI status
is 100 (assertion failures); infrastructure failures and changed score semantics
fail this smoke test. This is framework validation, never model performance.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


REPO = Path(__file__).resolve().parents[2]


def run_smoke(dest, *, executable="promptfoo", timeout=180):
    dest = Path(dest).resolve()
    if dest.exists() or dest.is_symlink():
        raise FileExistsError("Smoke output directory must be new")
    command = shutil.which(executable)
    if not command:
        raise RuntimeError("promptfoo executable missing; install the documented pinned version")
    dest.mkdir(parents=True)
    export_dir, output = dest / "export", dest / "results.json"
    subprocess.run([sys.executable, "-m", "nrb", "export", "--format", "promptfoo",
                    "--seed", "0", "--execution", "none", "--dest", str(export_dir)],
                   cwd=REPO, check=True, capture_output=True, text=True, timeout=30)
    env = os.environ.copy()
    # Documented controls turn off hosted features; they are not a firewall.
    env.update(PROMPTFOO_DISABLE_TELEMETRY="1", PROMPTFOO_DISABLE_UPDATE="1",
               PROMPTFOO_DISABLE_SHARING="1", PROMPTFOO_DISABLE_REMOTE_GENERATION="true",
               PROMPTFOO_SELF_HOSTED="1", PROMPTFOO_FAILED_TEST_EXIT_CODE="100",
               PROMPTFOO_PASS_RATE_THRESHOLD="100", PROMPTFOO_CONFIG_DIR=str(dest / "config"),
               PROMPTFOO_PYTHON=sys.executable)
    version = subprocess.run([command, "--version"], capture_output=True, text=True,
                             check=True, env=env, timeout=30).stdout.strip()
    argv = [command, "eval", "-c", str(export_dir / "promptfooconfig.yaml"),
            "--no-cache", "--no-share", "--no-progress-bar", "--no-table",
            "--max-concurrency", "1", "--output", str(output)]
    result = subprocess.run(argv, cwd=export_dir, env=env, capture_output=True,
                            text=True, timeout=timeout)
    (dest / "stdout.txt").write_text(result.stdout, encoding="utf-8")
    (dest / "stderr.txt").write_text(result.stderr, encoding="utf-8")
    if not output.is_file():
        raise RuntimeError(f"promptfoo emitted no results JSON; exit={result.returncode}; see {dest}")
    data = json.loads(output.read_text(encoding="utf-8"))
    from nrb.adapters import summarize_promptfoo_results
    canonical = summarize_promptfoo_results(data)
    (dest / "nrb_report.json").write_text(json.dumps(canonical, indent=2) + "\n", encoding="utf-8")
    summary = data["results"]
    stats, rows = summary["stats"], summary["results"]
    expected = (result.returncode == 100 and stats["successes"] == 0
                and stats["failures"] == 10 and stats["errors"] == 0 and len(rows) == 10
                and all(row["score"] == 0 and row["success"] is False for row in rows)
                and canonical["complete_auto"] and canonical["auto_macro_percent"] == 0)
    report = {"framework": "promptfoo", "version_output": version,
              "kind": "empty_submission_runtime_smoke", "not_model_performance": True,
              "cli_exit_code": result.returncode, "stats": stats,
              "task_count": len(rows), "passed": expected,
              "score_kind": "automatic_only", "api_provider_calls": 0}
    (dest / "smoke_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not expected:
        raise RuntimeError(f"Unexpected promptfoo runtime result; see {dest / 'smoke_report.json'}")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", help="New output directory; omitted uses a temporary directory")
    parser.add_argument("--executable", default="promptfoo")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    if args.dest:
        report = run_smoke(args.dest, executable=args.executable, timeout=args.timeout)
    else:
        with tempfile.TemporaryDirectory(prefix="nrb-promptfoo-smoke-") as temp:
            report = run_smoke(Path(temp) / "run", executable=args.executable, timeout=args.timeout)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

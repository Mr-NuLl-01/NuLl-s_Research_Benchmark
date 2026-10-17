"""Run real promptfoo against deliberately empty V1 coding submissions.

Expected exit 100 means ten intended assertion failures, not infrastructure
failure. This is framework validation with zero model calls. Disabled hosted
features are convenience settings, not a network firewall.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

REPO=Path(__file__).resolve().parents[2]

EMPTY_PROVIDER='''import json

def call_api(prompt, options, context):
    return {"output":json.dumps({"task_id":context["vars"]["task_id"],"answer":{},"artifacts":{}}),
            "metadata":{"nrb_mock":True,"not_model_performance":True,"mode":"empty"}}
'''


def run_smoke(dest, *, executable="promptfoo", timeout=180, selection="coding", seed=17,
              expected_version="0.124.1"):
    from nrb_v1.adapters import export, summarize_promptfoo_results
    from nrb_v1.registry import CODING_IDS, ids
    selected=ids(selection)
    if not set(selected)<=set(CODING_IDS):
        raise ValueError("Empty promptfoo automatic smoke covers coding tasks only")
    command=shutil.which(executable)
    if not command:
        raise RuntimeError("promptfoo executable missing; install the documented pinned version")
    dest=Path(dest)
    if dest.exists() or dest.is_symlink():
        raise FileExistsError("Smoke output directory must be new")
    dest=dest.resolve()
    dest.mkdir(parents=True)
    export_dir,output=dest/"export",dest/"results.json"
    export("promptfoo",export_dir,selection=selection,seed=seed)
    config_path=export_dir/"promptfooconfig.yaml"
    config=json.loads(config_path.read_text())
    # Smoke-only provider injection contains no oracle and never contacts a model.
    (export_dir/"empty_validation_provider.py").write_text(EMPTY_PROVIDER)
    config["providers"]=[{"id":"file://empty_validation_provider.py","label":"offline-v1-empty-validation"}]
    config_path.write_text(json.dumps(config,ensure_ascii=False,indent=2)+"\n")
    env=os.environ.copy()
    env.update(PROMPTFOO_DISABLE_TELEMETRY="1",PROMPTFOO_DISABLE_UPDATE="1",
               PROMPTFOO_DISABLE_SHARING="1",PROMPTFOO_DISABLE_REMOTE_GENERATION="true",
               PROMPTFOO_SELF_HOSTED="1",PROMPTFOO_FAILED_TEST_EXIT_CODE="100",
               PROMPTFOO_PASS_RATE_THRESHOLD="100",PROMPTFOO_CONFIG_DIR=str(dest/"config"),
               PROMPTFOO_PYTHON=sys.executable,
               PYTHONPATH=str(REPO)+(os.pathsep+env["PYTHONPATH"] if env.get("PYTHONPATH") else ""))
    version_result=subprocess.run([command,"--version"],capture_output=True,text=True,check=True,env=env,timeout=30)
    version_output=version_result.stdout.strip()
    if not re.search(r"(?<![0-9.])"+re.escape(expected_version)+r"(?![0-9.])",version_output):
        raise RuntimeError(f"Expected promptfoo {expected_version}; found {version_output}")
    argv=[command,"eval","-c",str(config_path),"--no-cache","--no-share","--no-progress-bar", "--no-table",
          "--max-concurrency","1","--output",str(output)]
    process=subprocess.run(argv,cwd=export_dir,env=env,capture_output=True,text=True,timeout=timeout)
    (dest/"stdout.txt").write_text(process.stdout)
    (dest/"stderr.txt").write_text(process.stderr)
    if not output.is_file():
        raise RuntimeError(f"promptfoo emitted no results JSON; exit={process.returncode}; see {dest}")
    data=json.loads(output.read_text())
    canonical=summarize_promptfoo_results(data,selection=selection)
    (dest/"nrb_report.json").write_text(json.dumps(canonical,ensure_ascii=False,indent=2,allow_nan=False)+"\n")
    envelope=data["results"]
    stats,rows=envelope["stats"],envelope["results"]
    summary=canonical["summary"]
    table=summary.get("task_table",[])
    canonical_zero=(not summary.get("missing_tasks") and len(table)==len(selected)
                    and all(row.get("instances")==1 and row.get("automatic_mean")==0 for row in table))
    passed=(process.returncode==100 and stats.get("successes")==0 and stats.get("failures")==len(selected)
            and stats.get("errors")==0 and len(rows)==len(selected)
            and all(row.get("score")==0 and row.get("success") is False for row in rows)
            and canonical_zero)
    report={"framework":"promptfoo","version_output":version_output,"kind":"empty_submission_runtime_smoke",
            "not_model_performance":True,"api_provider_calls":0,"task_count":len(rows),"seed":seed,
            "cli_exit_code":process.returncode,"stats":stats,"passed":bool(passed),
            "score_kind":"automatic_only","canonical_missing_tasks":summary.get("missing_tasks")}
    (dest/"smoke_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+"\n")
    if not passed:
        raise RuntimeError(f"Unexpected promptfoo runtime result; see {dest/'smoke_report.json'}")
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest")
    parser.add_argument("--executable",default="promptfoo")
    parser.add_argument("--timeout",type=int,default=180)
    parser.add_argument("--tasks",default="coding")
    parser.add_argument("--seed",type=int,default=17)
    parser.add_argument("--expected-version",default="0.124.1")
    args=parser.parse_args()
    if args.dest:
        result=run_smoke(args.dest,executable=args.executable,timeout=args.timeout,selection=args.tasks,seed=args.seed,expected_version=args.expected_version)
    else:
        with tempfile.TemporaryDirectory(prefix="nrb-v1-promptfoo-smoke-") as temp:
            result=run_smoke(Path(temp)/"run",executable=args.executable,timeout=args.timeout,selection=args.tasks,seed=args.seed,expected_version=args.expected_version)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()

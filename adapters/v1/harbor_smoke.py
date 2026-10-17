"""Harbor 0.24/schema 1.4 validation and explicit Docker oracle smoke.

Default V1 exports never contain an oracle. This validation helper injects one
only after exporting and confirming the candidate image inputs are unchanged.
Schema validation is not evidence that Docker isolation or trials executed.
"""
from __future__ import annotations
import argparse
from importlib.metadata import version
import json
import math
from pathlib import Path
import shutil
import subprocess

REPO=Path(__file__).resolve().parents[2]


def _snapshot(directory):
    from nrb_v1.provenance import fingerprint
    return {p.relative_to(directory).as_posix():fingerprint(p.read_bytes()) for p in sorted(Path(directory).rglob("*")) if p.is_file()}


def validate_export(export_dir, *, selection="coding", seed=17, expected_version="0.24.0"):
    """Use the installed Harbor Pydantic model and exact candidate packet bytes."""
    from harbor.models.task.config import TaskConfig
    from nrb_v1.packets import candidate
    from nrb_v1.registry import CODING_IDS, ids
    installed=version("harbor")
    if installed!=expected_version:
        raise RuntimeError(f"Expected Harbor {expected_version}; found {installed}")
    selected=ids(selection)
    if not set(selected)<=set(CODING_IDS):raise ValueError("Harbor automatic validation is coding-only")
    export_dir=Path(export_dir)
    entries=[]
    for task_id in selected:
        directory=export_dir/task_id.lower()
        data=TaskConfig.model_validate_toml((directory/"task.toml").read_text()).model_dump(mode="json")
        environment=directory/"environment"
        expected_files={"Dockerfile",".dockerignore","packet/task.md"}
        actual_files=set(_snapshot(environment))
        exact_packet=(environment/"packet/task.md").read_text()==candidate(task_id,seed)["content"]
        passed=(data["schema_version"]=="1.4" and data["verifier"]["environment_mode"]=="separate"
                and data["verifier"]["environment"]["network_mode"]=="no-network"
                and data["agent"]["network_mode"]=="no-network" and data["artifacts"]==["/app/"]
                and actual_files==expected_files and exact_packet and not (directory/"solution").exists()
                and (directory/"tests/grader/nrb_v1/grading.py").is_file())
        entries.append({"task_id":task_id,"schema_version":data["schema_version"],"candidate_files":sorted(actual_files),
                        "separate_verifier":data["verifier"]["environment_mode"],"passed":bool(passed)})
    return {"framework":"harbor","version":installed,"kind":"schema_and_export_validation",
            "not_model_performance":True,"runtime_executed":False,"api_provider_calls":0,
            "entries":entries,"passed":all(e["passed"] for e in entries)}


def inject_oracles_for_validation(export_dir, *, selection="coding", seed=17):
    """Evaluator-only opt-in; never called by normal export or candidate tasks."""
    from nrb_v1.registry import ids, module
    export_dir=Path(export_dir)
    selected=ids(selection)
    before={task_id:_snapshot(export_dir/task_id.lower()/"environment") for task_id in selected}
    for task_id in selected:
        solution=export_dir/task_id.lower()/"solution"
        solution.mkdir(exist_ok=False)
        reference=module(task_id).reference_submission(seed)
        (solution/"reference.json").write_text(json.dumps(reference,ensure_ascii=False,indent=2)+"\n")
        (solution/"solve.sh").write_text("#!/bin/sh\nset -eu\ncp /solution/reference.json /app/submission.json\n")
        (solution/"solve.sh").chmod(0o755)
    after={task_id:_snapshot(export_dir/task_id.lower()/"environment") for task_id in selected}
    if before!=after:raise RuntimeError("Oracle validation injection changed candidate image contents")
    record={"kind":"explicit_evaluator_oracle_validation_only","not_model_performance":True,
            "candidate_environment_unchanged":True,"tasks":selected,"seed":seed}
    (export_dir/"oracle_validation.json").write_text(json.dumps(record,indent=2)+"\n")
    return record


def check_job(job_dir, expected_ids, *, seed=17):
    """Validate actual per-trial canonical reports, not only Harbor's mean."""
    from nrb_v1.provenance import identity, validate_report
    job_dir=Path(job_dir)
    expected_ids=set(expected_ids)
    paths=sorted(job_dir.glob("*/result.json"))
    entries=[];reports=[];seen=set()
    for path in paths:
        trial=json.loads(path.read_text())
        entry={"trial":path.parent.name,"passed":False,"exception_info":trial.get("exception_info")}
        entries.append(entry)
        report_path=path.parent/"verifier/report.json"
        reward_path=path.parent/"verifier/reward.txt"
        if not report_path.is_file() or not reward_path.is_file():
            entry["error"]="Missing canonical report or scalar reward";continue
        try:
            report=validate_report(json.loads(report_path.read_text()))
            reward=float(reward_path.read_text().strip())
        except (ValueError,TypeError,KeyError) as exc:
            entry["error"]="Invalid report/reward: "+str(exc);continue
        task_id=report["task_id"]
        duplicate=task_id in seen;seen.add(task_id)
        report_ok=(report["evaluator_identity"]==identity() and report.get("adapter")=="harbor" and report["seed"]==seed
                   and report["auto_points"]==70 and report["auto_percent"]==100 and report["auto_scored_max"]==70
                   and report["total"] is None and report["completion_status"]=="pending_review"
                   and not report["critical_failures"] and not report["missing_artifacts"]
                   and report["input_integrity"]["unchanged"] is True and report["comparison_eligible"] is True
                   and report["verifier_log_permissions"]=={"owner_uid":0,"mode":"0o755"})
        trial_ok=(trial.get("exception_info") is None and trial.get("verifier_environment_mode")=="separate"
                  and (trial.get("verifier_result") or {}).get("rewards")=={"reward":1.0})
        entry.update(task_id=task_id,reward=reward,auto_points=report["auto_points"],duplicate=duplicate,
                     passed=bool(report_ok and trial_ok and math.isfinite(reward) and math.isclose(reward,1,abs_tol=1e-12)
                                 and not duplicate and task_id in expected_ids))
        reports.append(report)
    return {"kind":"harbor_oracle_runtime_smoke","not_model_performance":True,"job_dir":str(job_dir),
            "expected_tasks":sorted(expected_ids),"missing_tasks":sorted(expected_ids-seen),"trial_count":len(paths),
            "entries":entries,"reports":reports,
            "passed":len(paths)==len(expected_ids) and seen==expected_ids and all(e["passed"] for e in entries)}


def _run(argv, *, cwd, stdout_path, stderr_path, timeout):
    with stdout_path.open("w") as out, stderr_path.open("w") as err:
        return subprocess.run(argv,cwd=cwd,stdout=out,stderr=err,text=True,timeout=timeout).returncode


def run_smoke(dest, *, selection="C01,C04,C09", seed=17, image="nrb-v1:local", timeout=1800,
              expected_version="0.24.0", schema_only=False):
    from nrb_v1.adapters import export_harbor
    from nrb_v1.registry import ids
    dest=Path(dest)
    if dest.exists() or dest.is_symlink():raise FileExistsError("Harbor smoke output directory must be new")
    dest=dest.resolve()
    if not schema_only and (not shutil.which("harbor") or not shutil.which("docker")):
        raise RuntimeError("Harbor and Docker are required for runtime smoke; --schema-only is a separately labeled check")
    dest.mkdir(parents=True)
    export_dir=dest/"export"
    export_harbor(export_dir,selection=selection,seed=seed,image=image)
    schema=validate_export(export_dir,selection=selection,seed=seed,expected_version=expected_version)
    (dest/"schema_report.json").write_text(json.dumps(schema,ensure_ascii=False,indent=2)+"\n")
    if not schema["passed"]:raise RuntimeError("Harbor export/schema validation failed")
    if schema_only:
        (dest/"smoke_report.json").write_text(json.dumps(schema,ensure_ascii=False,indent=2)+"\n")
        return schema
    inject_oracles_for_validation(export_dir,selection=selection,seed=seed)
    docker,harbor=shutil.which("docker"),shutil.which("harbor")
    docker_exit=_run([docker,"version"],cwd=dest,stdout_path=dest/"docker-version.txt",stderr_path=dest/"docker-version-stderr.txt",timeout=30)
    if docker_exit:raise RuntimeError("Docker daemon is unavailable; no runtime evidence produced")
    argv=[harbor,"run","-p",str(export_dir),"-a","oracle","--env","docker","--jobs-dir",str(dest/"jobs"),
          "--job-name","oracle","--n-concurrent","1","--n-attempts","1","--max-retries","0"]
    timed_out=False
    try:
        exit_code=_run(argv,cwd=dest,stdout_path=dest/"harbor-stdout.txt",stderr_path=dest/"harbor-stderr.txt",timeout=timeout)
    except subprocess.TimeoutExpired:
        exit_code=None;timed_out=True
    result=check_job(dest/"jobs/oracle",ids(selection),seed=seed)
    result.update(framework="harbor",version=version("harbor"),schema_version="1.4",runtime_executed=True,
                  command_argv=argv,image=image,seed=seed,cli_exit_code=exit_code,timed_out=timed_out,api_provider_calls=0)
    result["passed"]=result["passed"] and exit_code==0 and not timed_out
    (dest/"smoke_report.json").write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+"\n")
    if not result["passed"]:raise RuntimeError(f"Harbor runtime smoke failed; inspect {dest/'smoke_report.json'}")
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest",required=True)
    parser.add_argument("--tasks",default="C01,C04,C09")
    parser.add_argument("--seed",type=int,default=17)
    parser.add_argument("--image",default="nrb-v1:local")
    parser.add_argument("--timeout",type=int,default=1800)
    parser.add_argument("--expected-version",default="0.24.0")
    parser.add_argument("--schema-only",action="store_true")
    args=parser.parse_args()
    result=run_smoke(args.dest,selection=args.tasks,seed=args.seed,image=args.image,timeout=args.timeout,
                     expected_version=args.expected_version,schema_only=args.schema_only)
    print(json.dumps({k:v for k,v in result.items() if k!="reports"},ensure_ascii=False,indent=2))


if __name__=="__main__":main()

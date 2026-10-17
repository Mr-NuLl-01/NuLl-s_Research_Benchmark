"""Evaluator-side adapters. Candidate packets never include this module.

Framework scalar scores are automatic points / 70 only. The complete signed-by-
content report and later manual ledger remain the source of research judgments.
"""
from __future__ import annotations
import json
import math
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile
import time
from .artifacts import parse_response
from .grading import grade, summarize
from .packets import candidate, public_metadata
from .provenance import fingerprint, identity, seal, validate_report
from .registry import CODING_IDS, ids, spec


class ProvenanceError(ValueError): pass
class IncompleteGrade(RuntimeError): pass


def _write(path, value):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")


def _fresh(dest):
    dest=Path(dest)
    if dest.exists() or dest.is_symlink():
        raise FileExistsError("Export destination must be new")
    dest=dest.resolve()
    dest.mkdir(parents=True,exist_ok=False)
    return dest


def _coding(selection):
    selected=ids(selection)
    if not set(selected)<=set(CODING_IDS):
        raise ValueError("This automatic adapter is coding-only; research/multimodal files use the manual review workflow")
    return selected


def _redact(value):
    if isinstance(value,dict):
        return {str(k):"[REDACTED]" if re.search(r"api.?key|password|secret|credential|authorization|(?:access|refresh|auth|api|bearer)[_-]?token|^token$",str(k),re.I) else _redact(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):return [_redact(v) for v in value]
    if hasattr(value,"model_dump"):return _redact(value.model_dump(mode="json"))
    if value is None or isinstance(value,(str,int,float,bool)):return value
    return None


def score_output(task_id, seed, output, execution="docker", packet_hash=None, evaluator_identity=None, image=None):
    if evaluator_identity is not None and evaluator_identity!=identity():raise ProvenanceError("Exported evaluator commit/content changed")
    if packet_hash is not None and packet_hash!=candidate(task_id,seed)["packet_hash"]:raise ProvenanceError("Candidate packet changed after export")
    invalid=None
    try:
        submission=parse_response(output,task_id) if isinstance(output,str) else output
        from .artifacts import validate_submission
        submission=validate_submission(submission,task_id)
    except (ValueError,TypeError,KeyError):
        invalid="Response is not a valid task submission envelope"
        submission={"task_id":task_id,"artifacts":{},"answer":{}}
    report=grade(task_id,submission,seed,execution,image=image)
    report.update(invalid_submission=invalid,raw_response_hash=fingerprint(output))
    report["report_hash"]=seal(report)
    return report


def inspect_samples(selection="coding",seed=17):
    evaluator=identity()
    return [{"id":tid,"input":candidate(tid,seed)["content"],"target":"",
             "metadata":{"task_id":tid,"seed":seed,"packet_hash":candidate(tid,seed)["packet_hash"],
                         "evaluator_identity":evaluator}} for tid in _coding(selection)]


_PREFIX="NRB V1 automatic-only; manual review pending. "


def _automatic_scalar_matches(value, percent):
    if isinstance(value,bool) or not isinstance(value,(int,float)):
        return False
    try:
        return math.isfinite(value) and abs(value-percent/100)<=1e-10
    except (OverflowError,TypeError,ValueError):
        return False


def promptfoo_assertion(output, context):
    v=context["vars"]
    report=score_output(v["task_id"],int(v["seed"]),output,v.get("execution","docker"),
                        v["packet_hash"],v["evaluator_identity"],v.get("image"))
    if report["auto_percent"] is None:raise IncompleteGrade("Grading infrastructure incomplete: "+json.dumps(report))
    return {"pass":report["auto_points"]==70 and not report["critical_failures"],"score":report["auto_percent"]/100,
            "reason":_PREFIX+json.dumps(report,ensure_ascii=False),"metadata":{"nrb_v1_report":report}}


def promptfoo_mock_provider(prompt,options,context):
    return {"output":json.dumps({"task_id":context["vars"]["task_id"],"artifacts":{},"answer":{}}),
            "metadata":{"nrb_mock":True,"not_model_performance":True,"api_provider_calls":0}}


def summarize_inspect_log(log,selection="coding",epoch=1):
    if isinstance(log,(str,Path)):
        from inspect_ai.log import read_eval_log
        log=read_eval_log(log)
    if getattr(log,"invalidated",False):raise ProvenanceError("Invalidated Inspect log")
    reports=[];errors=[]
    for sample in log.samples or []:
        if sample.epoch!=epoch:continue
        found=[(s,(s.metadata or {}).get("nrb_v1_report")) for s in (sample.scores or {}).values()]
        found=[(s,r) for s,r in found if r is not None]
        if len(found)!=1:errors.append(str(sample.id));continue
        recorded_score,recorded_report=found[0]
        report=validate_report(recorded_report,current=False)
        if report["auto_percent"] is not None:
            value=getattr(recorded_score,"value",None)
            if not _automatic_scalar_matches(value,report["auto_percent"]):
                raise ProvenanceError("Inspect scalar changed the automatic score")
        meta=sample.metadata or {}
        if str(sample.id)!=report["task_id"] or meta.get("packet_hash")!=report["packet_hash"] or meta.get("evaluator_identity")!=report["evaluator_identity"]:
            raise ProvenanceError("Inspect sample identity disagrees with its report")
        reports.append(report)
    result=summarize(reports,selection)
    ev=_redact(log.eval)
    result.update(adapter="inspect_ai",score_kind="automatic_only",epoch=epoch,framework_status=log.status,
                  missing_or_unscored_samples=errors,metadata=ev,
                  not_model_performance=str(ev.get("model","")).startswith("mockllm/"))
    if errors or log.status!="success":
        for p in result["profiles"].values():p.update(mean_total=None,automatic_mean_of_70=None)
        result["mean_total"]=None
    return {"reports":reports,"summary":result}


def summarize_promptfoo_results(data,selection="coding"):
    if isinstance(data,(str,Path)):data=json.loads(Path(data).read_text())
    envelope=data["results"];rows=envelope["results"]
    arms={(r.get("provider",{}).get("id"),r.get("provider",{}).get("label"),r.get("promptIdx")) for r in rows}
    if len(arms)>1:raise ProvenanceError("Summarize one provider/prompt arm at a time")
    def find(g):
        if not isinstance(g,dict):return []
        report=(g.get("metadata") or {}).get("nrb_v1_report")
        reason=g.get("reason","")
        recovered=json.loads(reason[len(_PREFIX):]) if isinstance(reason,str) and reason.startswith(_PREFIX) else None
        if report is not None or recovered is not None:
            if report is not None and recovered is not None and report!=recovered:raise ProvenanceError("Conflicting recorded canonical reports")
            return [report if report is not None else recovered]
        return [r for c in g.get("componentResults",[]) for r in find(c)]
    reports=[];errors=[]
    for row in rows:
        v=row.get("vars") or row.get("testCase",{}).get("vars",{})
        found=find(row.get("gradingResult"))
        if row.get("failureReason")==2 or len(found)!=1:errors.append(v.get("task_id"));continue
        report=validate_report(found[0],current=False)
        if v.get("task_id")!=report["task_id"] or int(v.get("seed"))!=report["seed"]:
            raise ProvenanceError("promptfoo task identity mismatch")
        # promptfoo may redact 64-hex variables. Recompute from the exact logged
        # prompt and recover identity only from the sealed canonical report.
        if not isinstance(v.get("prompt"),str) or fingerprint(v["prompt"].encode())!=report["packet_hash"]:
            raise ProvenanceError("Full logged prompt cannot validate the packet fingerprint")
        if v.get("packet_hash") not in (report["packet_hash"],"[REDACTED]"):raise ProvenanceError("Packet hash mismatch")
        eid=v.get("evaluator_identity")
        if not isinstance(eid,dict) or set(eid)!=set(report["evaluator_identity"]):raise ProvenanceError("Missing evaluator export identity")
        for k,value in eid.items():
            if value!=report["evaluator_identity"][k] and not(value=="[REDACTED]" and k in ("evaluator_commit","evaluator_digest")):
                raise ProvenanceError("Export evaluator differs from report")
        if report["auto_percent"] is not None and not _automatic_scalar_matches(row.get("score"),report["auto_percent"]):
            raise ProvenanceError("Framework scalar changed the automatic score")
        reports.append(report)
    result=summarize(reports,selection)
    result.update(adapter="promptfoo",score_kind="automatic_only",framework_stats=envelope["stats"],conversion_errors=errors,
                  framework_metadata=_redact(data.get("metadata",{})),provider_config=_redact(data.get("config",{}).get("providers")),
                  not_model_performance=bool(rows) and all(((r.get("response") or {}).get("metadata") or {}).get("nrb_mock") for r in rows))
    if errors or envelope["stats"].get("errors"):
        for p in result["profiles"].values():p.update(mean_total=None,automatic_mean_of_70=None)
        result["mean_total"]=None
    return {"reports":reports,"summary":result}


def _manifest(dest,format,selected,seed,**extra):
    data={"format":format,"seed":seed,"evaluator_identity":identity(),"tasks":[public_metadata(t,seed) for t in selected],**extra}
    data["files"]={p.relative_to(dest).as_posix():fingerprint(p.read_bytes()) for p in sorted(dest.rglob("*")) if p.is_file()}
    _write(dest/"manifest.json",data)
    return data


def export(format,dest,selection="coding",seed=17,image="nrb-v1:local",agent_hosts=""):
    if format=="harbor":return export_harbor(dest,selection,seed,image,agent_hosts)
    selected=_coding(selection)
    dest=_fresh(dest)
    samples=inspect_samples(selection,seed)
    if format=="jsonl":
        _write(dest/"tasks.jsonl","".join(json.dumps(s,ensure_ascii=False)+"\n" for s in samples))
    elif format=="promptfoo":
        _write(dest/"assertion.py","from nrb_v1.adapters import promptfoo_assertion as get_assert\n")
        _write(dest/"mock_provider.py","from nrb_v1.adapters import promptfoo_mock_provider as call_api\n")
        config={"description":"NRB V1 automatic70 only; empty mock is plumbing, not model performance","prompts":["{{prompt}}"],
                "providers":[{"id":"file://mock_provider.py","label":"offline-empty-smoke"}],
                "defaultTest":{"assert":[{"type":"python","value":"file://assertion.py","metric":"NRB-V1-auto"}]},
                "tests":[{"description":r["id"],"vars":dict(r["metadata"],prompt=r["input"],execution="docker",image=image)} for r in samples]}
        _write(dest/"promptfooconfig.yaml",config)
        _write(dest/"README.md","# Evaluator-side promptfoo configuration\n\nRun `promptfoo eval -c promptfooconfig.yaml --no-cache`. Default empty mock makes no API calls. Replace providers for actual models; retain every prompt and assertion. Scalar is automatic points / 70. Keep manual quality and core completion separate. Never give this export directory to a shell agent.\n")
    else:raise ValueError("Unknown export format")
    return _manifest(dest,format,selected,seed)


_AGENT_DOCKERFILE='''FROM {image}
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends bash ca-certificates curl git && rm -rf /var/lib/apt/lists/*
COPY packet/ /app/
RUN touch /app/submission.json
'''
_VERIFIER_DOCKERFILE='''FROM {image}
WORKDIR /app
COPY grader/ /grader/
COPY test.sh /tests/test.sh
RUN mkdir -p /app /logs/verifier && chmod -R go-rwx /grader /tests /logs/verifier && chmod 700 /grader /tests /tests/test.sh
ENV NRB_V1_IN_VERIFIER=1
'''


def export_harbor(dest,selection="coding",seed=17,image="nrb-v1:local",agent_hosts=""):
    selected=_coding(selection)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/:@-]*",image):raise ValueError("Invalid image reference")
    hosts=[h.strip() for h in agent_hosts.split(",") if h.strip()] if isinstance(agent_hosts,str) else list(agent_hosts)
    if len(set(hosts))!=len(hosts) or any(not re.fullmatch(r"(?=.{1,253}\Z)(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?",h) for h in hosts):
        raise ValueError("Use distinct exact DNS API hostnames")
    dest=_fresh(dest)
    pkg=Path(__file__).resolve().parent;evaluator=identity()
    for tid in selected:
        packet=candidate(tid,seed); task=spec(tid); directory=dest/tid.lower()
        _write(directory/"environment/packet/task.md",packet["content"])
        _write(directory/"environment/Dockerfile",_AGENT_DOCKERFILE.format(image=image))
        _write(directory/"environment/.dockerignore","*\n!Dockerfile\n!packet/\n!packet/**\n")
        _write(directory/"instruction.md",packet["content"]+"\n\n## Harbor delivery\nThe complete original task is /app/task.md. Keep it unchanged. Replace /app/submission.json with the complete JSON submission. Do not edit any verifier or result files.\n")
        grader=directory/"tests/grader"
        for file in sorted(pkg.rglob("*")):
            if file.is_file() and (file.suffix==".py" or file.name in ("policy.json","video_rubrics.json")) and "__pycache__" not in file.parts:
                target=grader/"nrb_v1"/file.relative_to(pkg)
                target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(file,target)
        # Coding imports do not need the research article archive; no archive
        # is copied to candidate or verifier images for coding-only runs.
        _write(grader/"nrb_v1/_origin.json",evaluator)
        _write(grader/"case_identity.json",{"task_id":tid,"seed":seed,"packet_hash":packet["packet_hash"],"evaluator_identity":evaluator})
        _write(grader/"verify.py","import sys\nsys.path.insert(0,'/grader')\nfrom nrb_v1.adapters import harbor_verify\nharbor_verify()\n")
        _write(directory/"tests/test.sh","#!/bin/sh\nset -eu\nexec python -I -B /grader/verify.py\n")
        (directory/"tests/test.sh").chmod(0o755)
        _write(directory/"tests/Dockerfile",_VERIFIER_DOCKERFILE.format(image=image))
        config=f'''schema_version = "1.4"
artifacts = ["/app/"]
[task]
name = "null-research-v1/{tid.lower()}-seed-{seed}"
description = {json.dumps(task['title'],ensure_ascii=False)}
[metadata]
benchmark_version = "1.1.0"
task_id = "{tid}"
seed = {seed}
score_kind = "automatic_only_70_points"
[agent]
timeout_sec = {float(task.get('time_budget_s',1800))}
network_mode = {json.dumps('allowlist' if hosts else 'no-network')}
{('allowed_hosts = '+json.dumps(hosts)) if hosts else ''}
[environment]
build_timeout_sec = 900.0
network_mode = "public"
cpus = 2
memory_mb = 2048
storage_mb = 4096
[verifier]
environment_mode = "separate"
timeout_sec = 300.0
user = "root"
[verifier.environment]
network_mode = "no-network"
cpus = 2
memory_mb = 1024
storage_mb = 2048
'''
        _write(directory/"task.toml",config)
    _write(dest/"README.md","# NRB V1 Harbor tasks\n\nBuild nrb-v1:local using environments/v1/Dockerfile before using these exports. No oracle solution is exported. Each candidate image contains only its task file and blank submission. The grader exists solely in a separate root-owned offline verifier; candidate code runs under UID65534. Keep separate verification enabled. Agent setup may install runtime using network; task execution defaults offline. Only explicit exact model API hosts can be allowed. Disable provider-side browsing and remote filesystem tools. Scalar reward is automatic/70; use report.json and later manual review for full judgments.\n")
    return _manifest(dest,"harbor",selected,seed,separate_verifier=True,include_oracle=False,image=image,agent_hosts=hosts)


def harbor_verify(grader_dir="/grader",candidate_dir="/app",logs_dir="/logs/verifier"):
    grader_dir,candidate_dir,logs_dir=map(Path,(grader_dir,candidate_dir,logs_dir))
    if (os.name!="posix" or os.geteuid()!=0 or os.environ.get("NRB_V1_IN_VERIFIER")!="1" or grader_dir.resolve()!=Path("/grader") or Path(__file__).resolve().parent!=grader_dir/"nrb_v1"):
        raise IncompleteGrade("Use the separately exported root verifier image")
    info=grader_dir.stat()
    if info.st_uid!=0 or info.st_mode&0o077:raise IncompleteGrade("Verifier files must be inaccessible to candidate UID")
    logs_dir.mkdir(parents=True,exist_ok=True);os.chown(logs_dir,0,0);logs_dir.chmod(0o755)
    if any((logs_dir/name).exists() or (logs_dir/name).is_symlink() for name in ("reward.txt","report.json")):
        raise ProvenanceError("Verifier output directory must be fresh")
    meta=json.loads((grader_dir/"case_identity.json").read_text())
    if meta["evaluator_identity"]!=identity():raise ProvenanceError("Verifier source/origin stamp changed")
    packet_path=candidate_dir/"task.md"
    integrity=packet_path.is_file() and not packet_path.is_symlink() and fingerprint(packet_path.read_bytes())==meta["packet_hash"]
    path=candidate_dir/"submission.json"
    output="INVALID_SUBMISSION"
    if path.is_file() and not path.is_symlink() and path.stat().st_size<=140*1024*1024:
        try:output=path.read_text(encoding="utf-8")
        except UnicodeError:pass
    report=score_output(meta["task_id"],meta["seed"],output,"container",meta["packet_hash"],meta["evaluator_identity"])
    report.update(adapter="harbor",input_integrity={"unchanged":integrity},comparison_eligible=integrity and report["auto_percent"] is not None,
                  execution_boundary="separate_offline_verifier_unprivileged_candidate_child",
                  verifier_log_permissions={"owner_uid":logs_dir.stat().st_uid,"mode":oct(stat.S_IMODE(logs_dir.stat().st_mode))})
    report["report_hash"]=seal(report);_write(logs_dir/"report.json",report)
    if not integrity:raise ProvenanceError("Candidate modified task input; no scalar reward emitted")
    if report["auto_percent"] is None:raise IncompleteGrade("Execution incomplete; no scalar reward emitted")
    _write(logs_dir/"reward.txt",f"{report['auto_percent']/100:.12g}\n")
    return report


def run_command(command,dest,selection="coding",seed=17,model_label="unspecified",harness_label="native",metadata=None,timeout=1800,execution="docker",image=None):
    if not isinstance(command,list) or not command or not all(isinstance(x,str) for x in command):raise ValueError("command-json must be an argv string list")
    selected=ids(selection)
    if any(t in ("X04","X05") for t in selected):
        raise ValueError("X04/X05 require complete media bundles; use generate-pack and a media-capable harness, not text-only run")
    dest=_fresh(dest);metadata=_redact(metadata or {})
    reports=[];runs=[]
    for tid in selected:
        directory=dest/tid;work=directory/"candidate";work.mkdir(parents=True)
        packet=candidate(tid,seed);task_path=work/("task."+packet["format"])
        _write(task_path,packet["content"])
        argv=[part.replace("{task}",str(task_path)).replace("{workdir}",str(work)) for part in command]
        prompt=packet["content"] if packet["format"]=="md" else "Open and fully inspect the self-contained local task file "+str(task_path)+". Deliver submission.json in this working directory."
        from .execution import _run
        try:
            outcome=_run(argv,work,prompt,timeout)
            status="timeout" if outcome["timed_out"] else "completed" if outcome["exit_code"]==0 else "harness_error"
            output_path=work/"submission.json"
            if output_path.is_file() and not output_path.is_symlink() and output_path.stat().st_size<=140*1024*1024:
                output=output_path.read_text()
            else:output=outcome["stdout"]
            _write(directory/"stdout.txt",outcome["stdout"]);_write(directory/"stderr.txt",outcome["stderr"])
        except OSError as exc:
            status="harness_error";output="";outcome={"wall_seconds":None,"exit_code":None,"error":str(exc)}
        unchanged=task_path.is_file() and not task_path.is_symlink() and fingerprint(task_path.read_bytes())==packet["packet_hash"]
        report=score_output(tid,seed,output,execution if status!="harness_error" else "none",packet["packet_hash"],image=image)
        report["generation"]={"status":status,"wall_seconds":outcome["wall_seconds"],"exit_code":outcome["exit_code"],"tokens":None,"cost":None,
                              "model_label":model_label,"harness_label":harness_label,"metadata":metadata,"timeout_seconds":timeout,
                              "execution_backend":execution,"execution_image":image,
                              "command_fingerprint":fingerprint(command),"execution_boundary":"host_process_not_a_generation_sandbox"}
        report.update(input_integrity={"unchanged":unchanged},comparison_eligible=unchanged and status!="harness_error")
        report["report_hash"]=seal(report);_write(directory/"report.json",report)
        try:_write(dest/"submissions"/(tid+".json"),parse_response(output,tid))
        except (ValueError,TypeError):pass
        reports.append(report);runs.append({"task_id":tid,"status":status,"input_unchanged":unchanged})
    result={"model_label":model_label,"harness_label":harness_label,"metadata":metadata,"runs":runs,"reports":reports,"summary":summarize(reports,selection)}
    if any(not r["comparison_eligible"] for r in reports):
        result["summary"]["mean_total"]=None
        for p in result["summary"]["profiles"].values():p.update(mean_total=None,automatic_mean_of_70=None)
    _write(dest/"run.json",result)
    return result

from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import sys
from . import __version__
from .artifacts import pack, parse_response, validate_submission
from .grading import attach_review, grade, review_packet, summarize
from .packets import freeze, public_metadata
from .provenance import identity
from .registry import ids, module, spec


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    text=json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n"
    if path:
        p=Path(path)
        p.parent.mkdir(parents=True,exist_ok=True)
        with p.open("x",encoding="utf-8") as f: f.write(text)
    else: print(text)


def main(argv=None):
    parser=argparse.ArgumentParser(prog="nrb-v1",description="NRB V1.0 offline task packets and research scoring")
    parser.add_argument("--version",action="version",version=__version__)
    sub=parser.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("list"); p.add_argument("--tasks",default="all")
    p=sub.add_parser("identity")
    p=sub.add_parser("export"); p.add_argument("--format",choices=["files","jsonl","promptfoo","harbor"],default="files")
    p.add_argument("--tasks",default="all");p.add_argument("--seed",type=int,default=17);p.add_argument("--dest",required=True)
    p.add_argument("--image",default="nrb-v1:local");p.add_argument("--agent-hosts",default="")
    p=sub.add_parser("pack");p.add_argument("--task",required=True);p.add_argument("--from-dir",required=True);p.add_argument("--out",required=True)
    for command in ("grade","review-packet"):
        p=sub.add_parser(command);p.add_argument("--task",required=True);p.add_argument("--submission",required=True)
        p.add_argument("--seed",type=int,default=17);p.add_argument("--execution",choices=["docker","none"],default="docker")
        p.add_argument("--timeout",type=float,default=120);p.add_argument("--image")
        if command=="grade":p.add_argument("--review");p.add_argument("--out")
        else:p.add_argument("--dest",required=True)
    p=sub.add_parser("grade-suite");p.add_argument("--submissions",required=True);p.add_argument("--reviews")
    p.add_argument("--tasks",default="coding");p.add_argument("--seed",type=int,default=17);p.add_argument("--execution",choices=["docker","none"],default="docker")
    p.add_argument("--timeout",type=float,default=120);p.add_argument("--image");p.add_argument("--out",required=True)
    p=sub.add_parser("summarize");p.add_argument("--reports",nargs="+",required=True);p.add_argument("--tasks",default="coding");p.add_argument("--out")
    p=sub.add_parser("selftest");p.add_argument("--tasks",default="coding");p.add_argument("--seeds",default="17")
    p.add_argument("--execution",choices=["trusted","docker"],default="trusted");p.add_argument("--timeout",type=float,default=120)
    p.add_argument("--image");p.add_argument("--out");p.add_argument("--include-mutants",action="store_true")
    p=sub.add_parser("run");p.add_argument("--command-json",required=True);p.add_argument("--tasks",default="coding")
    p.add_argument("--seed",type=int,default=17);p.add_argument("--dest",required=True);p.add_argument("--model-label",required=True)
    p.add_argument("--harness-label",required=True);p.add_argument("--metadata");p.add_argument("--timeout",type=float,default=1800)
    p.add_argument("--execution",choices=["docker","none"],default="docker");p.add_argument("--image")
    args=parser.parse_args(argv)
    try:
        if args.cmd=="list":write(None,[public_metadata(i) for i in ids(args.tasks)])
        elif args.cmd=="identity":write(None,identity())
        elif args.cmd=="pack":write(args.out,pack(args.task,args.from_dir))
        elif args.cmd=="export":
            if args.format=="files":result=freeze(args.dest,args.tasks,args.seed)
            else:
                from .adapters import export
                result=export(args.format,args.dest,args.tasks,args.seed,args.image,args.agent_hosts)
            print(json.dumps({"format":args.format,"destination":args.dest,"tasks":len(result["tasks"])},ensure_ascii=False))
        elif args.cmd in ("grade","review-packet"):
            submission=read(args.submission)
            if args.cmd=="review-packet":
                result=review_packet(args.task,submission,args.dest,args.seed,args.execution,args.timeout,args.image)
                write(None,result)
            else:
                result=(attach_review(submission,args.review) if args.review else grade(args.task,submission,args.seed,args.execution,args.timeout,args.image))
                if result["task_id"]!=args.task or result["seed"]!=args.seed:raise ValueError("Requested review task/seed differs")
                write(args.out,result)
        elif args.cmd=="grade-suite":
            reports=[]
            for task_id in ids(args.tasks):
                path=Path(args.submissions)/(task_id+".json")
                submission=read(path) if path.is_file() else {"task_id":task_id,"artifacts":{},"answer":{}}
                ledger=Path(args.reviews)/task_id/"review.json" if args.reviews else None
                result=attach_review(submission,ledger) if ledger and ledger.is_file() else grade(task_id,submission,args.seed,args.execution,args.timeout,args.image)
                if result["seed"]!=args.seed:raise ValueError("Review seed differs")
                reports.append(result)
            write(args.out,{"reports":reports,"summary":summarize(reports,args.tasks)})
        elif args.cmd=="summarize":
            reports=[]
            for path in args.reports:
                value=read(path)
                reports.extend(value["reports"] if isinstance(value,dict) and "reports" in value else value if isinstance(value,list) else [value])
            write(args.out,summarize(reports,args.tasks))
        elif args.cmd=="selftest":
            entries=[]
            for seed in map(int,args.seeds.split(",")):
                for task_id in ids(args.tasks):
                    if not task_id.startswith("C"):raise ValueError("Reference selftest is coding-only")
                    mod=module(task_id)
                    candidates=mod.mutants(seed) if args.include_mutants else {"reference":mod.reference_submission(seed)}
                    for label,submission in candidates.items():
                        result=grade(task_id,submission,seed,args.execution,args.timeout,args.image)
                        expected_pass=label=="reference"
                        observed=result["auto_percent"]==100
                        ok=(expected_pass==observed and result["execution"]["status"]!="unavailable")
                        entries.append({"task_id":task_id,"seed":seed,"label":label,"passed":ok,
                                        "auto_points":result["auto_points"],"tier_scores":result["tier_scores"],
                                        "execution_status":result["execution"]["status"],"execution_seconds":result["execution"]["wall_seconds"],
                                        "critical_failures":result["critical_failures"],"pending_items":result["pending_items"],
                                        "report_hash":result["report_hash"]})
            result={"kind":"reference_and_wrong_candidate_validation","not_model_performance":True,"api_provider_calls":0,
                    "evaluator_identity":identity(),"backend":args.execution,"entries":entries,"passed":all(e["passed"] for e in entries)}
            write(args.out,result)
            if not result["passed"]:return 1
        elif args.cmd=="run":
            from .adapters import run_command
            result=run_command(json.loads(args.command_json),args.dest,args.tasks,args.seed,args.model_label,args.harness_label,
                               read(args.metadata) if args.metadata else {},args.timeout,args.execution,args.image)
            write(None,{"destination":args.dest,"reports":len(result["reports"]),"summary":result["summary"]})
        return 0
    except (ValueError,KeyError,TypeError,OSError) as exc:
        print(f"nrb-v1: {type(exc).__name__}: {exc}",file=sys.stderr)
        return 2


if __name__=="__main__":sys.exit(main())

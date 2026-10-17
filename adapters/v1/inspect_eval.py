"""Inspect AI V1 response-only task and real mock-runtime validation.

The model-facing sample contains only the complete candidate packet. Scientific
scoring stays in nrb_v1; automatic scores never imply independent review passed.
"""
from __future__ import annotations

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import Score, Target, mean, scorer
from inspect_ai.solver import TaskState, generate

from nrb_v1.adapters import inspect_samples, score_output


@scorer(metrics=[mean()])
def nrb_v1_automatic(execution: str = "docker"):
    async def score(state: TaskState, target: Target) -> Score:
        meta = state.metadata
        try:
            report = score_output(meta["task_id"], meta["seed"], state.output.completion,
                                  execution=execution, packet_hash=meta.get("packet_hash"),
                                  evaluator_identity=meta.get("evaluator_identity"))
        except (ValueError, RuntimeError) as exc:
            return Score.unscored(reason="adapter_or_provenance_error", explanation=str(exc),
                                  metadata={"task_id":meta.get("task_id"),"seed":meta.get("seed")})
        if report.get("auto_percent") is None:
            return Score.unscored(reason="grading_incomplete", explanation="No complete automatic denominator; see canonical metadata.",
                                  metadata={"nrb_v1_report":report})
        return Score(value=report["auto_percent"] / 100,
                     answer=state.output.completion,
                     explanation="Automatic points / 70. Independent review remains pending.",
                     metadata={"nrb_v1_report":report})
    return score


@task
def null_research_v1(seed: int = 17, selection: str = "coding", execution: str = "docker"):
    return Task(dataset=[Sample(**record) for record in inspect_samples(selection=selection,seed=int(seed))],
                solver=generate(),scorer=nrb_v1_automatic(execution),
                metadata={"nrb_version":"1.0.0","nrb_track":"response_only",
                          "score_kind":"automatic_only","seed":int(seed),"selection":selection})


def run_smoke(dest, *, seed=17, expected_version="0.3.281"):
    """Run positive, negative and unavailable cases through real Inspect/mockllm.

    This imports host reference data solely for explicit evaluator validation.
    It does not add any oracle content to a candidate export.
    """
    from importlib.metadata import version
    import json
    import math
    import os
    from pathlib import Path
    from unittest.mock import patch
    from inspect_ai import eval as inspect_eval
    from inspect_ai.model import ModelOutput, ModelUsage, get_model
    from nrb_v1.adapters import summarize_inspect_log
    from nrb_v1.registry import module

    installed=version("inspect-ai")
    if installed != expected_version:
        raise RuntimeError(f"Expected inspect-ai {expected_version}; found {installed}")
    dest=Path(dest)
    if dest.exists() or dest.is_symlink():
        raise FileExistsError("Inspect smoke output directory must be new")
    dest=dest.resolve()
    dest.mkdir(parents=True)
    samples={row["id"]:row for row in inspect_samples(selection="C01,C04",seed=seed)}
    variants=[("positive","C01",module("C01").reference_submission(seed),"trusted",1.0),
              ("negative","C01",{"task_id":"C01","answer":{},"artifacts":{}},"trusted",0.0),
              ("unavailable","C04",module("C04").reference_submission(seed),"none",None)]
    entries=[]
    for label,task_id,submission,backend,expected in variants:
        local_task=Task(dataset=[Sample(**samples[task_id])],solver=generate(),
                        scorer=nrb_v1_automatic(backend),name="nrb-v1-"+label,
                        metadata={"not_model_performance":True,"validation_only":True})
        mock_output=ModelOutput.from_content("mockllm/model",json.dumps(submission,ensure_ascii=False))
        # Explicit synthetic usage prevents mockllm from downloading a tokenizer.
        mock_output.usage=ModelUsage(input_tokens=0,output_tokens=0,total_tokens=0)
        model=get_model("mockllm/model",custom_outputs=[mock_output])
        with patch.dict(os.environ,{"INSPECT_DISABLE_MODEL_API":"1",
                                     "XDG_DATA_HOME":str(dest/"xdg-data"),
                                     "XDG_CACHE_HOME":str(dest/"xdg-cache")}):
            logs=inspect_eval(local_task,model=model,display="none",log_dir=str(dest/label),
                              max_samples=1,log_samples=True,log_format="json")
        if len(logs)!=1 or logs[0].status!="success" or len(logs[0].samples or [])!=1:
            raise RuntimeError(f"Inspect mock eval failed for {label}: {logs[0].error if logs else 'no log'}")
        log=logs[0]
        recorded=next(iter(log.samples[0].scores.values()))
        canonical=(recorded.metadata or {}).get("nrb_v1_report")
        passed=(math.isnan(float(recorded.value)) and canonical is not None and canonical.get("auto_percent") is None
                if expected is None else recorded.value==expected and canonical is not None)
        if expected is not None:
            passed=passed and canonical["auto_points"]==70*expected and canonical["total"] is None
        summary=summarize_inspect_log(log,selection="coding")["summary"]
        # One evaluated task cannot turn the ten-task denominator into a full suite.
        missing=summary.get("missing_tasks",[])
        passed=passed and len(missing)==9
        entries.append({"label":label,"task_id":task_id,"expected_score":expected,
                        "score":None if expected is None else recorded.value,
                        "completion_status":canonical.get("completion_status") if canonical else None,
                        "missing_tasks":missing,"passed":bool(passed)})
    report={"framework":"inspect_ai","version":installed,"kind":"mock_runtime_smoke",
            "not_model_performance":True,"api_provider_calls":0,"log_format":"json",
            "usage_kind":"explicit_synthetic_zero_for_mock","entries":entries,
            "passed":all(e["passed"] for e in entries)}
    (dest/"smoke_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+"\n")
    if not report["passed"]:
        raise RuntimeError(f"Inspect smoke failed; see {dest/'smoke_report.json'}")
    return report


if __name__=="__main__":
    import argparse
    import json
    import tempfile
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke",action="store_true",required=True)
    parser.add_argument("--dest")
    parser.add_argument("--seed",type=int,default=17)
    parser.add_argument("--expected-version",default="0.3.281")
    args=parser.parse_args()
    if args.dest:
        result=run_smoke(args.dest,seed=args.seed,expected_version=args.expected_version)
    else:
        with tempfile.TemporaryDirectory(prefix="nrb-v1-inspect-smoke-") as temp:
            result=run_smoke(Path(temp)/"run",seed=args.seed,expected_version=args.expected_version)
    print(json.dumps(result,ensure_ascii=False,indent=2))

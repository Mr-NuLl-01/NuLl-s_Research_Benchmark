"""Inspect AI response-only track. Scientific grading stays in nrb.core."""
from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import Score, Target, mean, scorer
from inspect_ai.solver import TaskState, generate

from nrb.adapters import ProvenanceError, inspect_samples, score_output


@scorer(metrics=[mean()])
def nrb_automatic(execution: str = "docker"):
    async def score(state: TaskState, target: Target) -> Score:
        meta = state.metadata
        try:
            report = score_output(meta["task_id"], meta["seed"], state.output.completion,
                                  execution=execution, candidate_hash=meta["candidate_sha256"])
        except ProvenanceError as exc:
            return Score.unscored(reason="provenance_drift", explanation=str(exc))
        if report["auto_percent"] is None:
            return Score.unscored(reason="grading_incomplete", explanation="See metadata; this is not a model failure.",
                                  metadata={"nrb_report": report})
        return Score(value=report["auto_percent"] / 100, answer=state.output.completion,
                     explanation="Automatic points / 70. Independent 30-point quality review is pending.",
                     metadata={"nrb_report": report})
    return score


@task
def null_research(seed: int = 0, execution: str = "docker"):
    return Task(dataset=[Sample(**record) for record in inspect_samples(int(seed))],
                solver=generate(), scorer=nrb_automatic(execution),
                metadata={"nrb_track": "response_only", "score_kind": "automatic_only", "seed": int(seed)})

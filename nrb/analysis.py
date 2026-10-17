"""Paired descriptive comparison; task variants are not independent domains."""
from __future__ import annotations
from collections import defaultdict
import json
import math
import random


def paired_comparison(runs_a, runs_b, *, bootstrap_seed=7201, draws=4000):
    if len(runs_a) != len(runs_b) or not runs_a:
        raise ValueError("Supply the same nonzero number of explicitly paired run reports")
    if isinstance(draws, bool) or not isinstance(draws, int) or draws < 100:
        raise ValueError("Use at least 100 bootstrap draws")
    versions = {r.get("benchmark_version") for r in [*runs_a, *runs_b]}
    tracks = {r.get("track") for r in [*runs_a, *runs_b]}
    if len(versions) != 1 or None in versions:
        raise ValueError("All repeats must use one explicit benchmark version")
    if len(tracks) != 1:
        raise ValueError("All repeats must use the same track")

    def condition(run):
        metadata = run.get("metadata", {})
        if not isinstance(metadata, dict):
            raise ValueError("Run metadata must be an object")
        return {"model_label": run.get("model_label"), "harness_label": run.get("harness_label"),
                "metadata": {k: v for k, v in metadata.items() if k not in ("seed", "repetition", "run_id")}}

    conditions = []
    for arm in (runs_a, runs_b):
        configs = [condition(run) for run in arm]
        if len({json.dumps(c, sort_keys=True, allow_nan=False) for c in configs}) != 1:
            raise ValueError("Do not mix model, harness, or settings within a comparison arm")
        conditions.append(configs[0])
    groups = defaultdict(list)
    pairs = []
    family_set = None
    for repeat, (left, right) in enumerate(zip(runs_a, runs_b)):
        if left.get("benchmark_version") != right.get("benchmark_version"):
            raise ValueError("Benchmark versions differ")
        if left.get("track") != right.get("track"):
            raise ValueError("Tracks differ; compare them as different experimental conditions")
        la = {(r["task_id"], r["seed"]): r for r in left["reports"]}
        rb = {(r["task_id"], r["seed"]): r for r in right["reports"]}
        if not la or len(la) != len(left["reports"]) or len(rb) != len(right["reports"]) or set(la) != set(rb):
            raise ValueError("Task/seed sets differ or contain duplicates")
        if left.get("complete_auto") is False or right.get("complete_auto") is False:
            raise ValueError("An incomplete suite cannot enter comparison")
        families = {key[0] for key in la}
        if family_set is None:
            family_set = families
        elif families != family_set:
            raise ValueError("Task family sets differ between repeats")
        for key in sorted(la):
            a, b = la[key], rb[key]
            if a["case_hash"] != b["case_hash"]:
                raise ValueError("Paired inputs differ")
            if a["coverage"] != 1 or b["coverage"] != 1 or a["auto_percent"] is None or b["auto_percent"] is None:
                raise ValueError("Incomplete/infrastructure-unscored trials cannot enter comparison")
            for report in (a, b):
                score = report["auto_percent"]
                if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 100 or not math.isfinite(score):
                    raise ValueError("Automatic percentages must be finite values in [0,100]")
            delta = b["auto_percent"]-a["auto_percent"]
            groups[key[0]].append(delta)
            pairs.append({"task_id": key[0], "seed": key[1], "paired_run_index": repeat,
                          "a": a["auto_percent"], "b": b["auto_percent"], "delta_b_minus_a": delta})
    means = {key: sum(vals)/len(vals) for key, vals in sorted(groups.items())}
    overall = sum(means.values())/len(means)
    # Sample task families, not seeded instances as if they were new domains.
    rng = random.Random(bootstrap_seed)
    values = list(means.values())
    boot = sorted(sum(rng.choices(values, k=len(values)))/len(values) for _ in range(draws))
    def quantile(p):
        index = (len(boot)-1)*p
        low = math.floor(index)
        high = math.ceil(index)
        return boot[low]+(index-low)*(boot[high]-boot[low])
    return {"score_kind": "automatic_only_percent", "paired_observations": len(pairs),
            "benchmark_version": runs_a[0]["benchmark_version"], "track": runs_a[0].get("track"),
            "condition_a": conditions[0], "condition_b": conditions[1],
            "task_families": len(means), "family_mean_deltas": means,
            "macro_delta_b_minus_a": overall, "family_bootstrap_interval_95": [quantile(.025), quantile(.975)],
            "bootstrap_seed": bootstrap_seed, "bootstrap_draws": draws,
            "interpretation": "Descriptive paired comparison conditional on these task families/settings. Variants are clustered within family. This is not a population-wide capability confidence interval or an empirical difficulty calibration.",
            "pairs": pairs}

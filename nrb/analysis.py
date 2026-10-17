"""Paired descriptive comparison; task variants are not independent domains."""
from __future__ import annotations
from collections import defaultdict
import json
import math
import random
from .provenance import identity_from
from .core import validate_final_report


def _unfilled_metadata(value, path, *, required=False):
    """List unresolved configuration paths; values remain operator attestations.

    An empty skills list explicitly means no skills; nested empty lists can
    likewise declare no allowed resources. Other empty top-level containers
    cannot describe a required configuration. A nonempty outer object does not
    resolve nested template placeholders. The literal not_exposed is an
    explicit disclosure and is not a missing value.
    """
    if value is None or (isinstance(value, str) and (not value.strip() or "REPLACE" in value)):
        return [path]
    if isinstance(value, dict):
        if not value:
            return [path]
        return [missing for key, item in value.items()
                for missing in _unfilled_metadata(item, f"{path}.{key}")]
    if isinstance(value, list):
        if not value:
            return [path] if required and path != "skills" else []
        return [missing for index, item in enumerate(value)
                for missing in _unfilled_metadata(item, f"{path}[{index}]")]
    return []


def paired_comparison(runs_a, runs_b, *, bootstrap_seed=7201, draws=4000,
                      score_kind="automatic", mode="diagnostic"):
    if score_kind not in {"automatic", "reviewed"} or mode not in {"diagnostic", "controlled"}:
        raise ValueError("Choose automatic/reviewed score-kind and diagnostic/controlled mode")
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
    identities = [identity_from(run) for run in [*runs_a, *runs_b]]
    if any(item is None for item in identities) or len({json.dumps(x, sort_keys=True) for x in identities}) != 1:
        raise ValueError("Comparison requires one explicit evaluator identity; legacy or changed scoring is not comparable")
    identity = identities[0]
    missing_metadata = []
    required_metadata = ("isolation", "tool_policy", "model_version", "harness_version", "skills", "reasoning", "budget")
    for arm_name, arm in (("a", runs_a), ("b", runs_b)):
        for index, run in enumerate(arm):
            meta = run.get("metadata", {})
            if not isinstance(meta, dict):
                raise ValueError("Run metadata must be an object")
            absent = [missing for key in required_metadata
                      for missing in ([key] if key not in meta else _unfilled_metadata(meta[key], key, required=True))]
            absent += [key for key in ("model_label", "harness_label") if not run.get(key)]
            if identity.get("evaluator_commit") is None:
                absent.append("evaluator_commit")
            if absent:
                missing_metadata.append({"arm": arm_name, "run_index": index, "fields": absent})
    if mode == "controlled" and (missing_metadata or next(iter(tracks)) not in {"agent-controlled", "response_only"}):
        raise ValueError("Controlled comparison requires an explicit controlled track and complete model/tool/budget/isolation/evaluator metadata")

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
    labels = set()
    value_field = "auto_percent" if score_kind == "automatic" else "total"
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
            if any(identity_from(report) != identity for report in (a, b)):
                raise ValueError("Task report evaluator identity differs from the run identity")
            if a["case_hash"] != b["case_hash"]:
                raise ValueError("Paired inputs differ")
            if a["coverage"] != 1 or b["coverage"] != 1 or a["auto_percent"] is None or b["auto_percent"] is None:
                raise ValueError("Incomplete/infrastructure-unscored trials cannot enter comparison")
            for report in (a, b):
                validate_final_report(report)
                if report.get("protocol_violation") or report.get("status") == "protocol_violation" or report.get("comparison_eligible") is False:
                    raise ValueError("Protocol-invalid trials cannot enter comparison")
                if mode == "controlled" and report.get("completion_status") == "infrastructure_unscored":
                    raise ValueError("Mandatory execution infrastructure remains unscored")
                if score_kind == "reviewed":
                    if report.get("review_pending") or report.get("total") is None:
                        raise ValueError("Reviewed comparison requires all quality scores")
                    labels.add(report.get("score_label", "unverified_review"))
                score = report.get(value_field)
                if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 100 or not math.isfinite(score):
                    raise ValueError("Compared scores must be finite values in [0,100]")
            delta = b[value_field]-a[value_field]
            groups[key[0]].append(delta)
            pairs.append({"task_id": key[0], "seed": key[1], "paired_run_index": repeat,
                          "a": a[value_field], "b": b[value_field], "delta_b_minus_a": delta,
                          "completion_a": a.get("completion_status"), "completion_b": b.get("completion_status"),
                          "critical_failures_a": a.get("critical_failures", []), "critical_failures_b": b.get("critical_failures", []),
                          "pending_a": a.get("pending_items", []), "pending_b": b.get("pending_items", [])})
    if mode == "controlled" and score_kind == "reviewed" and len(labels) != 1:
        raise ValueError("Controlled reviewed comparison cannot pool human and LLM review conditions")
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
    return {"score_kind": "automatic_only_percent" if score_kind == "automatic" else "reviewed_total",
            "mode": mode, "missing_metadata": missing_metadata,
            "review_status": "mixed_provisional" if len(labels) > 1 else next(iter(labels), "not_used"),
            "paired_observations": len(pairs), **identity, "track": runs_a[0].get("track"),
            "condition_a": conditions[0], "condition_b": conditions[1],
            "task_families": len(means), "family_mean_deltas": means,
            "macro_delta_b_minus_a": overall, "family_bootstrap_interval_95": [quantile(.025), quantile(.975)],
            "bootstrap_seed": bootstrap_seed, "bootstrap_draws": draws,
            "interpretation": "Descriptive paired comparison conditional on these task families/settings. Variants are clustered within family. This is not a population-wide capability confidence interval or an empirical difficulty calibration.",
            "pairs": pairs}

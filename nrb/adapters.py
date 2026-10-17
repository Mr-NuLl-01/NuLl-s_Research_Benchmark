"""Framework adapters. All scientific scoring is delegated to nrb.core.

Framework exports are evaluator-side files. Never mount this repository or an
entire exported task directory in a candidate's shell environment.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile
import uuid


class ProvenanceError(RuntimeError):
    """The current evaluator does not match the exported candidate input."""


class IncompleteGrade(RuntimeError):
    """A dependency or verifier failure prevented a complete automatic grade."""


def _log_value(value):
    """Copy public log fields without requiring an optional framework import."""
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(k): _log_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_log_value(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    # Offline contract fixtures can use SimpleNamespace instead of Pydantic.
    if hasattr(value, "__dict__"):
        return _log_value(vars(value))
    return None


def _config_value(value):
    """Keep recorded settings while masking credential-named fields."""
    value = _log_value(value)
    if isinstance(value, dict):
        return {k: ("[REDACTED]" if re.search(
            r"api.?key|authorization|credential|password|secret|access.?token|refresh.?token", k, re.I)
            else _config_value(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [_config_value(v) for v in value]
    return value


def _settings_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     allow_nan=False).encode("utf-8")).hexdigest()


def candidate_sha256(case):
    from nrb.core import candidate_prompt
    return hashlib.sha256(candidate_prompt(case).encode("utf-8")).hexdigest()


def score_output(task_id, seed, output, execution="docker", *, candidate_hash=None, evaluator_id=None):
    from nrb.core import get_case, grade_submission
    from nrb.provenance import evaluator_identity
    if evaluator_id is not None and evaluator_id != evaluator_identity():
        raise ProvenanceError("Evaluator scoring source changed after export; restore the exact exported evaluator identity")
    case = get_case(task_id, int(seed))
    if candidate_hash is not None and candidate_sha256(case) != candidate_hash:
        raise ProvenanceError("Candidate prompt changed after export; restore the evaluator commit and seed used for this run")
    return grade_submission(case, output, execution=execution)


def inspect_samples(seed=0):
    """Inspect-shaped records; no optional dependency, target, or answer leakage."""
    from nrb.core import build_suite, candidate_prompt
    from nrb.provenance import evaluator_identity
    identity = evaluator_identity()
    return [{"id": case["id"], "input": candidate_prompt(case), "target": "",
             "metadata": {"task_id": case["id"], "seed": case["seed"], "domain": case["domain"],
                          "benchmark_version": case["benchmark_version"],
                          "case_hash": case["case_hash"], "candidate_sha256": candidate_sha256(case),
                          "evaluator_identity": identity}}
            for case in build_suite(seed)]


def summarize_inspect_log(log, *, epoch=1):
    """Recover canonical reports; missing samples keep the suite incomplete.

    Pass an Inspect EvalLog object, or a path (requires inspect-ai). Epochs are
    summarized separately; this helper never pools repeated task IDs.
    """
    from nrb.core import summarize
    if isinstance(log, (str, Path)):
        from inspect_ai.log import read_eval_log
        log = read_eval_log(log)
    if getattr(log, "invalidated", False):
        raise ProvenanceError("Inspect log contains invalidated samples")
    reports, unscored, seeds = [], [], set()
    unverified_identity = []
    for sample in log.samples or []:
        if sample.epoch != epoch:
            continue
        found = [(entry.metadata or {}).get("nrb_report") for entry in (sample.scores or {}).values()]
        found = [report for report in found if report is not None]
        if len(found) != 1:
            unscored.append(str(sample.id))
            continue
        report = found[0]
        if str(sample.id) != report["task_id"]:
            raise ProvenanceError("Inspect sample ID differs from the grader report")
        recorded_identity = (getattr(sample, "metadata", None) or {}).get("evaluator_identity")
        from nrb.provenance import identity_from
        canonical_identity = identity_from(report)
        if recorded_identity is not None and recorded_identity != canonical_identity:
            raise ProvenanceError("Inspect exported evaluator identity differs from the canonical report")
        if recorded_identity is None or canonical_identity is None:
            unverified_identity.append(str(sample.id))
        seeds.add(report.get("seed"))
        reports.append(report)
    if len(seeds) > 1:
        raise ProvenanceError("An Inspect summary must contain only one benchmark seed")
    result = summarize(reports)
    spec = _log_value(getattr(log, "eval", None)) or {}
    plan = _log_value(getattr(log, "plan", None)) or {}
    packages = spec.get("packages") or {}
    task_args = _config_value(spec.get("task_args"))
    metadata = {
        "harness_version": packages.get("inspect_ai") or packages.get("inspect-ai"),
        "model_version": None,
        "model_identity_kind": "inspect_eval_model",
        "model_args": _config_value(spec.get("model_args")),
        "model_generate_config": _config_value(spec.get("model_generate_config")),
        "plan_generate_config": _config_value(plan.get("config")),
        "plan_steps": _config_value(plan.get("steps")),
        "plan_finish": _config_value(plan.get("finish")),
        "task": spec.get("task"),
        "task_args": ({k: v for k, v in task_args.items() if k != "seed"}
                      if isinstance(task_args, dict) else None),
        "solver": spec.get("solver"),
        "solver_args": _config_value(spec.get("solver_args")),
        "evaluation_config": _config_value(spec.get("config")),
        "sandbox": _config_value(spec.get("sandbox")),
    }
    # A reported alias is not proof of a pinned provider-side model revision.
    missing_metadata = ["model_version"]
    for key, value in (("model_label", spec.get("model")),
                       ("harness_version", metadata["harness_version"]),
                       ("generation_config", metadata["model_generate_config"])):
        if value is None:
            missing_metadata.append(key)
    result.update(inspect_status=log.status, epoch=epoch, unscored_sample_ids=unscored,
                  track="response_only", score_kind="automatic_only", adapter="inspect_ai",
                  model_label=spec.get("model"), harness_label="inspect_ai", metadata=metadata,
                  metadata_incomplete=bool(missing_metadata), missing_metadata=missing_metadata,
                  not_model_performance=str(spec.get("model", "")).startswith("mockllm/"),
                  adapter_provenance={"unverified_export_identity_samples": unverified_identity},
                  source_log={"eval_id": spec.get("eval_id"), "run_id": spec.get("run_id"),
                              "created": spec.get("created"), "task_args": task_args})
    if log.status != "success" or unscored:
        result.update(complete_auto=False, auto_macro_percent=None, reviewed_macro_total=None)
    return result


def promptfoo_assertion(output, context):
    """promptfoo's documented get_assert(output, context) interface."""
    variables = context["vars"]
    report = score_output(variables["task_id"], variables["seed"], output,
                          execution=variables.get("execution", "docker"),
                          candidate_hash=variables["candidate_sha256"], evaluator_id=variables.get("evaluator_identity"))
    if report["auto_percent"] is None:
        raise IncompleteGrade("Automatic scoring incomplete; this is an evaluator/infrastructure error, not model accuracy. "
                              + json.dumps(report, ensure_ascii=False))
    # promptfoo requires a boolean. It means all deterministic checks passed,
    # not that the full 100-point research-quality review has passed.
    full_auto = report["auto_points"] == report["auto_max"] and not report["critical_failures"]
    return {"pass": full_auto, "score": report["auto_percent"] / 100,
            "reason": "NRB automatic-only score; independent 30-point review remains pending. "
                      + json.dumps(report, ensure_ascii=False),
            "named_scores": {"nrb_automatic": report["auto_percent"] / 100},
            "metadata": {"nrb_report": report}}


def summarize_promptfoo_results(data):
    """Recover canonical scores from one provider, one prompt, one repetition.

    Export each comparison arm separately. Framework errors and missing task
    rows invalidate the suite aggregate, even if promptfoo displays a mean of
    its remaining rows. No submitted code is rerun by this log conversion.
    """
    from nrb.core import get_case, summarize
    if isinstance(data, (str, Path)):
        data = json.loads(Path(data).read_text(encoding="utf-8"))
    envelope = data["results"]
    rows = envelope["results"]
    providers = {(r.get("provider", {}).get("id"), r.get("provider", {}).get("label")) for r in rows}
    prompts = {r.get("promptIdx") for r in rows}
    if len(providers) > 1 or len(prompts) > 1:
        raise ValueError("Summarize one provider and one prompt per results file; keep comparison arms separate")
    reports, errors, seeds, seen = [], [], set(), set()
    recovered_hashes, recovered_evaluator_identities, unverified_evaluator_identities = [], [], []
    mock = False
    prefix = "NRB automatic-only score; independent 30-point review remains pending. "

    def find_reports(grading):
        if not isinstance(grading, dict):
            return []
        report = (grading.get("metadata") or {}).get("nrb_report")
        reason = grading.get("reason", "")
        reason_report = json.loads(reason[len(prefix):]) if isinstance(reason, str) and reason.startswith(prefix) else None
        if report is not None:
            if reason_report is not None and report != reason_report:
                raise ProvenanceError("promptfoo canonical report metadata differs from its recorded reason")
            return [report]
        if reason_report is not None:
            return [reason_report]
        found = []
        for component in grading.get("componentResults") or []:
            found.extend(find_reports(component))
        return found

    for index, row in enumerate(rows):
        variables = row.get("vars") or row.get("testCase", {}).get("vars", {})
        task_id = variables.get("task_id")
        if task_id in seen:
            raise ValueError("Duplicate task rows; summarize repetitions separately")
        seen.add(task_id)
        seeds.add(variables.get("seed"))
        mock |= bool(((row.get("response") or {}).get("metadata") or {}).get("nrb_mock"))
        if row.get("failureReason") == 2:
            errors.append({"row": index, "task_id": task_id, "kind": "framework_error"})
            continue
        found = find_reports(row.get("gradingResult"))
        if len(found) != 1:
            errors.append({"row": index, "task_id": task_id, "kind": "canonical_report_missing_or_ambiguous"})
            continue
        report = found[0]
        from nrb.provenance import identity_from
        canonical_identity = identity_from(report)
        recorded_identity = variables.get("evaluator_identity")
        if recorded_identity is None or canonical_identity is None:
            unverified_evaluator_identities.append(task_id)
        if recorded_identity is not None:
            if not isinstance(recorded_identity, dict) or canonical_identity is None or set(recorded_identity) != set(canonical_identity):
                raise ProvenanceError("promptfoo exported evaluator identity is invalid or has no canonical report identity")
            for key, value in recorded_identity.items():
                if value == "[REDACTED]" and key in {"evaluator_digest", "evaluator_commit"}:
                    # Recover only from the exact logged canonical report. Never
                    # stamp historical rows with today's evaluator fingerprint.
                    if task_id not in recovered_evaluator_identities:
                        recovered_evaluator_identities.append(task_id)
                elif value != canonical_identity[key]:
                    raise ProvenanceError("promptfoo exported evaluator identity differs from canonical report")
        if task_id != report["task_id"] or int(variables["seed"]) != report["seed"]:
            raise ProvenanceError("promptfoo task identity differs from canonical report")
        case = get_case(task_id, report["seed"])
        expected_hash = candidate_sha256(case)
        recorded_hash = variables.get("candidate_sha256")
        recorded_prompt = variables.get("prompt")
        if recorded_hash == "[REDACTED]":
            # promptfoo 0.124.1 sanitizes SHA-looking variable values in JSON
            # exports. Its complete vars.prompt survives in the actual runtime
            # artifact. Rehash that exact logged input; never treat redaction as
            # permission to skip provenance or replace it from today's case.
            if not isinstance(recorded_prompt, str) or hashlib.sha256(
                    recorded_prompt.encode("utf-8")).hexdigest() != expected_hash:
                raise ProvenanceError("Redacted promptfoo hash requires an intact matching logged prompt")
            recovered_hashes.append(task_id)
        elif recorded_hash != expected_hash:
            raise ProvenanceError("promptfoo export does not match this evaluator commit")
        elif isinstance(recorded_prompt, str) and hashlib.sha256(
                recorded_prompt.encode("utf-8")).hexdigest() != expected_hash:
            raise ProvenanceError("promptfoo logged prompt differs from its candidate hash")
        if report.get("case_hash") != case["case_hash"]:
            raise ProvenanceError("promptfoo canonical report belongs to a different case")
        if report["auto_percent"] is not None and not math.isclose(float(row["score"]), report["auto_percent"] / 100, abs_tol=1e-10):
            raise ProvenanceError("promptfoo score was transformed or contains additional assertions")
        reports.append(report)
    if len(seeds) > 1:
        raise ProvenanceError("Mixed seeds; summarize one repetition and seed per file")
    result = summarize(reports)
    provider_id, provider_label = next(iter(providers), (None, None))
    config = data.get("config") or {}
    provider_configs = config.get("providers") or []
    if not isinstance(provider_configs, list):
        provider_configs = [provider_configs]
    selected = [p for p in provider_configs if isinstance(p, dict)
                and p.get("id") == provider_id and p.get("label") == provider_label]
    provider_config = _config_value(selected[0].get("config", {})) if len(selected) == 1 else None
    export_metadata = data.get("metadata") or {}
    metadata = {
        "harness_version": export_metadata.get("promptfooVersion"),
        "model_version": None,
        "model_identity_kind": "promptfoo_provider_id",
        "provider": {"id": provider_id, "label": provider_label, "config": provider_config},
        "provider_config_sha256": _settings_hash(provider_config) if provider_config is not None else None,
        "default_options": _config_value((config.get("defaultTest") or {}).get("options")),
        "evaluate_options": _config_value(config.get("evaluateOptions")),
        "runtime_options": _config_value(data.get("runtimeOptions")),
        "prompt_template_sha256": _settings_hash(config["prompts"]) if "prompts" in config else None,
        "test_options": {str((r.get("vars") or r.get("testCase", {}).get("vars", {})).get("task_id")):
                         _config_value((r.get("testCase") or {}).get("options")) for r in rows},
    }
    missing_metadata = ["model_version"]
    for key, value in (("provider_id", provider_id), ("harness_version", metadata["harness_version"]),
                       ("provider_config", provider_config)):
        if value is None:
            missing_metadata.append(key)
    result.update(adapter="promptfoo", score_kind="automatic_only", conversion_errors=errors,
                  promptfoo_stats=envelope["stats"], not_model_performance=mock,
                  model_label=provider_id, harness_label="promptfoo", metadata=metadata,
                  metadata_incomplete=bool(missing_metadata), missing_metadata=missing_metadata,
                  provenance={"hash_recovered_from_full_logged_prompt": recovered_hashes,
                              "evaluator_identity_recovered_from_canonical_report": recovered_evaluator_identities,
                              "unverified_export_evaluator_identity": unverified_evaluator_identities},
                  source_log={"eval_id": data.get("evalId"), "export_metadata": export_metadata})
    if errors or envelope["stats"]["errors"]:
        result.update(complete_auto=False, auto_macro_percent=None, reviewed_macro_total=None)
    return result


def promptfoo_mock_provider(prompt, options, context):
    """Offline smoke provider, deliberately not a model-performance baseline."""
    from nrb.core import get_case, reference_submission
    variables = context["vars"]
    case = get_case(variables["task_id"], int(variables["seed"]))
    if candidate_sha256(case) != variables["candidate_sha256"]:
        raise ProvenanceError("Mock provider export is stale")
    mode = (options or {}).get("config", {}).get("mode", "empty")
    if mode == "oracle":
        submission = reference_submission(case)
    elif mode == "empty":
        submission = {"task_id": case["id"], "answer": {}, "artifacts": {}}
    else:
        raise ValueError("Offline mock mode must be empty or oracle")
    return {"output": json.dumps(submission, ensure_ascii=False),
            "metadata": {"nrb_mock": True, "mode": mode, "not_model_performance": True}}


def promptfoo_command_provider(prompt, options, context):
    """Evaluate a real CLI agent through promptfoo, with a fresh native run.

    Configure ``command`` as an argv list. The agent's directory is not a
    security sandbox; run this evaluator on a dedicated disposable machine or
    supply a command wrapper that starts a separately isolated candidate.
    """
    from nrb.core import get_case
    from nrb.harness import run_command
    variables = context["vars"]
    case = get_case(variables["task_id"], int(variables["seed"]))
    if candidate_sha256(case) != variables["candidate_sha256"]:
        raise ProvenanceError("CLI provider export is stale")
    config = (options or {}).get("config", {})
    command = config.get("command")
    if not isinstance(command, list) or not command:
        raise ValueError("CLI provider requires config.command as a nonempty argv list")
    base = Path(config.get("workdir_root", tempfile.gettempdir()))
    dest = base / f"nrb-{case['id'].lower()}-{uuid.uuid4().hex}"
    record = run_command(case, command, dest, timeout=config.get("timeout_seconds", 900),
                         stdout_format=config.get("stdout_format", "plain"))
    if record["protocol_violation"]:
        raise ProvenanceError(f"Candidate protocol violation; see {record['logs_dir']}")
    if record["status"] in {"invalid_submission", "timeout", "output_limit_exceeded"}:
        output = "INVALID_SUBMISSION"
    elif record["status"] != "completed":
        raise RuntimeError(f"CLI run {record['status']}; see {record['logs_dir']}. No model correctness score assigned.")
    else:
        output = json.dumps(record["submission"], ensure_ascii=False)
    metadata = {key: record[key] for key in ("task_id", "seed", "candidate_sha256", "command_argv",
                                            "logs_dir", "status", "elapsed_seconds", "exit_code",
                                            "usage", "cost_usd", "cost_kind", "execution_boundary")}
    return {"output": output, "metadata": {"nrb_run": metadata}}


def _fresh(dest):
    dest = Path(dest)
    if dest.exists() or dest.is_symlink():
        raise FileExistsError(f"Export destination must be new: {dest}")
    dest.mkdir(parents=True)
    return dest


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _manifest(dest, adapter, cases, **kwargs):
    from nrb.provenance import evaluator_identity
    manifest = {"adapter": adapter, "task_count": len(cases), "evaluator_identity": evaluator_identity(),
                "cases": [{"task_id": c["id"], "seed": c["seed"],
                           "benchmark_version": c["benchmark_version"],
                           "case_hash": c["case_hash"], "candidate_sha256": candidate_sha256(c)} for c in cases],
                "files": {p.relative_to(dest).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sorted(dest.rglob("*")) if p.is_file()}, **kwargs}
    _write(dest / "export_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return manifest


def export_promptfoo(cases, dest, execution="docker"):
    """Export a self-contained promptfoo config; install this evaluator package."""
    from nrb.core import candidate_prompt
    from nrb.provenance import evaluator_identity
    identity = evaluator_identity()
    cases = list(cases)
    if execution not in {"docker", "none", "trusted"}:
        raise ValueError("Unsupported promptfoo execution backend")
    dest = _fresh(dest)
    _write(dest / "assertion.py", "from nrb.adapters import promptfoo_assertion as get_assert\n")
    _write(dest / "mock_provider.py", "from nrb.adapters import promptfoo_mock_provider as call_api\n")
    _write(dest / "command_provider.py", "from nrb.adapters import promptfoo_command_provider as call_api\n")
    config = {
        "description": "NRB automatic-only evaluation; mock provider is plumbing, not an AI result",
        "prompts": ["{{prompt}}"],
        "providers": [{"id": "file://mock_provider.py", "label": "offline-empty-smoke", "config": {"mode": "empty"}}],
        "defaultTest": {"assert": [{"type": "python", "value": "file://assertion.py", "metric": "NRB-auto"}]},
        "tests": [{"description": f"{c['id']} {c['title']}",
                   "vars": {"prompt": candidate_prompt(c), "task_id": c["id"], "seed": c["seed"],
                            "candidate_sha256": candidate_sha256(c), "execution": execution,
                            "evaluator_identity": identity}} for c in cases],
    }
    # JSON is also valid YAML; no YAML package is needed to export the config.
    _write(dest / "promptfooconfig.yaml", json.dumps(config, ensure_ascii=False, indent=2) + "\n")
    _write(dest / "README.md", "# promptfoo export\n\nRun `promptfoo eval -c promptfooconfig.yaml --no-cache`. "
           "Install the matching NRB evaluator first. Default provider returns an empty submission for an offline plumbing test. "
           "Replace only `providers` with your provider for actual model testing. Keep task inputs, seeds, and assertion unchanged. "
           "Oracle mock mode is evaluator self-testing only. A score is automatic points / 70, never the full reviewed score. "
           "Incomplete grading raises an error; do not include that trial in accuracy comparisons.\n")
    return _manifest(dest, "promptfoo", cases, execution=execution, default_provider="offline-empty-smoke",
                     validation="Python callback contract tests; promptfoo runtime must be validated on the target installation")


_HARBOR_AGENT_DOCKERFILE = '''FROM {python_image}
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends bash ca-certificates curl git && rm -rf /var/lib/apt/lists/*
COPY packet/ /app/
# A fresh blank sentinel makes absent model output a submission failure, not a
# missing-artifact infrastructure failure. It is not a previously scored answer.
RUN touch /app/submission.json
'''

_HARBOR_VERIFIER_DOCKERFILE = '''FROM {python_image}
WORKDIR /app
COPY grader/ /grader/
COPY test.sh /tests/test.sh
RUN mkdir -p /app /logs/verifier && chmod -R go-rwx /grader /tests /logs/verifier && chmod 700 /grader /tests /tests/test.sh
ENV NRB_CONTAINER_VERIFIER=1
'''

_HARBOR_VERIFY = '''import sys
sys.path.insert(0, "/grader")
from nrb.adapters import harbor_verify
harbor_verify()
'''


def export_harbor(cases, dest, *, python_image="python:3.12-slim", include_solution=False,
                  agent_hosts=None):
    """Export Harbor schema 1.4 tasks using a separate verifier container.

    ``environment/`` contains only OS provisioning and candidate packets.
    Package/expected/reference data are exclusively under ``tests/`` (and the
    optional oracle-only ``solution/``). Do not override separate verifier mode.
    """
    from nrb.core import candidate_prompt, reference_submission, write_candidate_packet
    from nrb.harness import _snapshot
    from nrb.provenance import evaluator_identity
    identity = evaluator_identity()
    cases = list(cases)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/:@-]*", python_image):
        raise ValueError("python_image must be a single container image reference")
    if agent_hosts is None:
        agent_hosts = []
    if (not isinstance(agent_hosts, (list, tuple))
            or not all(isinstance(x, str) and re.fullmatch(r"(?=.{1,253}\Z)(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?", x) for x in agent_hosts)
            or len(set(agent_hosts)) != len(agent_hosts)):
        raise ValueError("agent_hosts must contain exact DNS hostnames")
    dest = _fresh(dest)
    package_root = Path(__file__).resolve().parent
    for case in cases:
        task_dir = dest / case["id"].lower()
        packet = task_dir / "environment" / "packet"
        write_candidate_packet(case, packet)
        manifest = _snapshot(packet)
        instruction = candidate_prompt(case) + (
            "\n\n## Harbor delivery\nThe supplied files are in /app. Keep them unchanged. "
            "Write the complete JSON submission to /app/submission.json. "
            "Include every requested deliverable as full text in its artifacts object. "
            "A blank submission file is provided; replace its contents with your answer.\n"
        )
        _write(task_dir / "instruction.md", instruction)
        _write(task_dir / "environment" / "Dockerfile", _HARBOR_AGENT_DOCKERFILE.format(python_image=python_image))
        _write(task_dir / "environment" / ".dockerignore", "*\n!Dockerfile\n!packet/\n!packet/**\n")
        grader_dir = task_dir / "tests" / "grader"
        for path in sorted(package_root.rglob("*.py")):
            if not path.is_symlink() and "__pycache__" not in path.parts:
                target = grader_dir / "nrb" / path.relative_to(package_root)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
        # The digest includes policy bytes; the origin stamp is deliberately
        # outside the digest and preserves exporter commit identity in Docker.
        shutil.copyfile(package_root / "evaluation_policy.json", grader_dir / "nrb" / "evaluation_policy.json")
        _write(grader_dir / "nrb" / "_evaluator_origin.json", json.dumps(identity, indent=2) + "\n")
        meta = {"task_id": case["id"], "evaluator_identity": identity, "seed": case["seed"], "case_hash": case["case_hash"],
                "candidate_sha256": candidate_sha256(case), "candidate_files": manifest,
                "python_image": python_image, "execution": "container"}
        _write(grader_dir / "case_identity.json", json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
        _write(grader_dir / "verify.py", _HARBOR_VERIFY)
        _write(task_dir / "tests" / "test.sh", "#!/bin/sh\nset -eu\nexec python -I -B /grader/verify.py\n")
        (task_dir / "tests" / "test.sh").chmod(0o755)
        _write(task_dir / "tests" / "Dockerfile", _HARBOR_VERIFIER_DOCKERFILE.format(python_image=python_image))
        if include_solution:
            _write(task_dir / "solution" / "reference.json",
                   json.dumps(reference_submission(case), ensure_ascii=False, indent=2) + "\n")
            _write(task_dir / "solution" / "solve.sh",
                   "#!/bin/sh\nset -eu\ncp /solution/reference.json /app/submission.json\n")
            (task_dir / "solution" / "solve.sh").chmod(0o755)
        config = f'''schema_version = "1.4"
artifacts = ["/app/"]

[task]
name = "null-research/{case['id'].lower()}-seed-{case['seed']}"
description = {json.dumps(case['title'], ensure_ascii=False)}

[metadata]
benchmark_version = {json.dumps(case['benchmark_version'])}
task_id = {json.dumps(case['id'])}
seed = {case['seed']}
case_hash = {json.dumps(case['case_hash'])}
score_kind = "automatic_only_70_points"

[agent]
timeout_sec = 900.0
network_mode = {json.dumps("allowlist" if agent_hosts else "no-network")}
{("allowed_hosts = " + json.dumps(list(agent_hosts))) if agent_hosts else ""}

[environment]
build_timeout_sec = 900.0
network_mode = "public"
cpus = 2
memory_mb = 2048
storage_mb = 4096

[verifier]
environment_mode = "separate"
timeout_sec = 120.0
user = "root"

[verifier.environment]
network_mode = "no-network"
cpus = 1
memory_mb = 512
storage_mb = 2048
'''
        _write(task_dir / "task.toml", config)
    _write(dest / "README.md", "# NRB Harbor export\n\nOracle solutions are excluded by default; export with --include-oracle only for evaluator plumbing tests. "
           "For that opt-in export use `harbor run -p . -a oracle`, "
           "or replace `oracle` with the installed agent and specify its model. Tasks use schema 1.4 and a separate verifier. "
           "Pin the Python image digest and Harbor version before comparative runs. The agent image excludes all evaluator code. "
           "The verifier denies networking; submitted Python runs under UID 65534 and cannot read /grader. "
           "The scalar reward is automatic points / 70; the independent 30-point review remains pending. "
           "See the full `report.json`, input integrity, and coverage; absent reward on infrastructure/provenance failure is not a model score. "
           "Agent setup has network access for installing its runtime; agent runs are offline by default. "
           "An explicit --agent-hosts allowlist can permit the exact required model API hosts. "
           "Closed-track rules still prohibit remote search/source access through provider tools.\n")
    return _manifest(dest, "harbor", cases, schema_version="1.4", python_image=python_image,
                     separate_verifier=True, execution="container", include_solution=include_solution, agent_hosts=list(agent_hosts),
                     validation="Export format, content separation, and Python contracts tested; Harbor/Docker runtime not validated here")


def harbor_verify(grader_dir="/grader", candidate_dir="/app", logs_dir="/logs/verifier"):
    """Entry point inside the root-owned, network-disabled verifier container."""
    from nrb.core import MAX_SUBMISSION_BYTES, seal_report
    from nrb.harness import _integrity
    grader_dir, candidate_dir, logs_dir = Path(grader_dir), Path(candidate_dir), Path(logs_dir)
    if (os.name != "posix" or os.geteuid() != 0 or os.environ.get("NRB_CONTAINER_VERIFIER") != "1"
            or grader_dir.resolve() != Path("/grader")
            or Path(__file__).resolve().parent != grader_dir / "nrb"):
        raise IncompleteGrade("Harbor grading requires the dedicated exported verifier image; do not run it on a host checkout")
    info = grader_dir.stat()
    if info.st_uid != 0 or info.st_mode & 0o077:
        raise IncompleteGrade("/grader must be owned by root and inaccessible to other users")
    logs_dir.mkdir(parents=True, exist_ok=True)
    # Harbor mounts a host log directory over the image's directory and its
    # default host mode is 0777. Reapply ownership/permissions at runtime so
    # the unprivileged submitted Python cannot replace rewards or reports.
    # 0755 lets the host collect logs after the verifier exits.
    os.chown(logs_dir, 0, 0)
    logs_dir.chmod(0o755)
    # Refuse stale reward files in a reused verifier; never inherit an old pass.
    for filename in ("reward.txt", "reward.json"):
        if (logs_dir / filename).exists() or (logs_dir / filename).is_symlink():
            raise ProvenanceError("A fresh verifier log directory is required")
    meta = json.loads((grader_dir / "case_identity.json").read_text(encoding="utf-8"))
    from nrb.provenance import evaluator_identity
    if meta.get("evaluator_identity") != evaluator_identity():
        raise ProvenanceError("Exported verifier identity differs from its source/policy bytes or origin stamp")
    integrity = _integrity(candidate_dir, meta["candidate_files"])
    path = candidate_dir / "submission.json"
    if path.is_symlink():
        submission = "INVALID: symlink submission"
    elif path.exists():
        info = path.stat()
        if stat.S_ISREG(info.st_mode) and info.st_size <= MAX_SUBMISSION_BYTES:
            try:
                submission = path.read_text(encoding="utf-8")
            except UnicodeError:
                submission = "INVALID: submission is not UTF-8"
        else:
            submission = "INVALID: oversized or non-regular submission"
    else:
        submission = ""
    report = score_output(meta["task_id"], meta["seed"], submission, execution="container",
                          candidate_hash=meta["candidate_sha256"], evaluator_id=meta["evaluator_identity"])
    report["input_integrity"] = integrity
    report["adapter"] = "harbor"
    report["execution_boundary"] = "separate_network_disabled_container_with_unprivileged_candidate_child"
    report["verifier_log_permissions"] = {"owner_uid": logs_dir.stat().st_uid,
                                         "mode": oct(stat.S_IMODE(logs_dir.stat().st_mode))}
    report["comparison_eligible"] = integrity["unchanged"] and report["auto_percent"] is not None
    report["protocol_violation"] = None if integrity["unchanged"] else "candidate_input_modified"
    if not integrity["unchanged"]:
        report["status"] = "protocol_violation"
    # Candidate integrity and comparison eligibility are part of the automatic
    # evidence seal. Publish only after all adapter boundary fields are final.
    report = seal_report(report)
    _write(logs_dir / "report.json", json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if not integrity["unchanged"]:
        raise ProvenanceError("Candidate changed supplied input files; protocol violation recorded in report.json")
    if report["auto_percent"] is None:
        raise IncompleteGrade("Verifier could not complete all checks; see report.json. No numeric reward is emitted.")
    _write(logs_dir / "reward.txt", f"{report['auto_percent'] / 100:.12g}\n")
    return report

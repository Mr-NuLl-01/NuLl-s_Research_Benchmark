"""One task definition and one scorer, shared by every harness adapter."""
from __future__ import annotations
import hashlib
import importlib
import json
import math
from pathlib import Path, PurePosixPath
import re
from . import __version__
from .completion import (REVIEW_POLICY_VERSION, ESSENTIAL_AUTOMATIC, requirements,
                         blank_essential, refresh_completion, validate_essential)
from .provenance import evaluator_identity, identity_from, require_current_identity

TASK_IDS = tuple(f"NRB{i:02d}" for i in range(1, 11))
REQUIRED_ARTIFACTS = {task_id: ["reasoning.md"] for task_id in TASK_IDS}
REQUIRED_ARTIFACTS.update({"NRB03": ["reasoning.md", "solve.py"],
                           "NRB04": ["reasoning.md", "solution.py"], "NRB05": ["reasoning.md", "solution.py"],
                           "NRB09": ["figure.svg", "caption.md"],
                           "NRB10": ["audit.md", "revised_excerpt.md", "reproduce.md"]})
MAX_SUBMISSION_BYTES = 2_000_000


def canonical_json(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def fingerprint(obj):
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def safe_relative(path):
    if not isinstance(path, str) or not path or "\\" in path or "\x00" in path:
        raise ValueError("Artifact paths must be nonempty POSIX relative paths")
    p = PurePosixPath(path)
    if p.is_absolute() or any(x in ("", ".", "..") for x in path.split("/")):
        raise ValueError(f"Unsafe relative path: {path!r}")
    if any(x.startswith(".") for x in p.parts) or ":" in path:
        raise ValueError(f"Hidden paths and URI/drive paths are not allowed: {path!r}")
    return p


def task_module(task_id):
    if task_id not in TASK_IDS:
        raise ValueError(f"Unknown task {task_id!r}; choose one of {', '.join(TASK_IDS)}")
    return importlib.import_module(f"nrb.tasks.t{task_id[-2:]}")


def public_case(case):
    return {k: case[k] for k in ("id", "title", "domain", "seed", "benchmark_version", "prompt", "files", "rubric", "required_artifacts", "essential_review_requirements", "review_policy_version")}


def get_case(task_id, seed=0):
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**32:
        raise ValueError("seed must be an integer in [0, 2**32)")
    case = task_module(task_id).build(seed)
    case.update(seed=seed, benchmark_version=__version__)
    case["required_artifacts"] = list(REQUIRED_ARTIFACTS[task_id])
    case["essential_review_requirements"] = requirements(task_id)
    case["review_policy_version"] = REVIEW_POLICY_VERSION
    if case.get("id") != task_id:
        raise ValueError("Task module returned wrong ID")
    for key in ("title", "domain", "prompt", "files", "expected", "rubric"):
        if key not in case:
            raise ValueError(f"Task missing {key}")
    if len(case["rubric"]) != 3 or len({x["id"] for x in case["rubric"]}) != 3:
        raise ValueError("Each task needs three distinct human criteria")
    for name, content in case["files"].items():
        safe_relative(name)
        if not isinstance(content, str):
            raise ValueError("Candidate input files must be UTF-8 text")
    case["rubric_hash"] = fingerprint({"rubric": case["rubric"], "essential": case["essential_review_requirements"],
                                      "review_policy_version": REVIEW_POLICY_VERSION})
    case["case_hash"] = fingerprint(public_case(case))
    return case


def build_suite(seed=0):
    return [get_case(task_id, seed) for task_id in TASK_IDS]


def reference_submission(case):
    # Oracles must not alias grader-owned expected dictionaries. Mutation tests
    # and scoring must never change the answer key through a shared reference.
    return json.loads(canonical_json(task_module(case["id"]).reference(case)))


def candidate_prompt(case):
    sections = [f"# {case['id']} · {case['title']}", case["prompt"],
                "## 提交协议 / Submission contract\n"
                "返回一个 UTF-8 JSON 对象（可使用单个 json 代码块），或将该对象写入 submission.json。\n"
                '顶层格式：{"task_id":"' + case["id"] + '","answer":{...},"artifacts":{"relative/path":"完整文件内容"}}。\n'
                "answer 使用本题字段。代码、推导、图和修订稿放入 artifacts，字符串须包含完整内容，不能只返回本机路径。\n"
                "数值使用 JSON number，缺失使用 null；不接受 NaN/Infinity。不同题目独立完成。\n"
                "输入均为本基准原创构造的合成材料，不代表真实实验或真实未发表研究。\n"
                "封闭资料轨道只使用本题材料与通用知识。不得查找本基准源码、答案或评分器。\n"
                "每题自动核验 70 分，另有以下三项各 10 分的独立质量审阅。",
                json.dumps(case["rubric"], ensure_ascii=False, indent=2),
                "## 核心完成条件（独立于分数）\n以下责任逐项以 pass/fail/unassessed 审阅；高分不能补偿核心责任失败。\n"
                + json.dumps(case["essential_review_requirements"], ensure_ascii=False, indent=2),
                "Required artifacts: " + ", ".join(case["required_artifacts"])]
    for name, content in sorted(case["files"].items()):
        sections.extend([f"\n## 输入文件：{name}\n<BEGIN_INPUT_FILE>", content, "<END_INPUT_FILE>"])
    return "\n\n".join(sections) + "\n"


def write_candidate_packet(case, dest):
    dest = Path(dest)
    if dest.is_symlink():
        raise ValueError("Candidate destination cannot be a symlink")
    if dest.exists() and any(dest.iterdir()):
        raise FileExistsError(f"Refusing nonempty candidate directory: {dest}")
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "instruction.md").write_text(candidate_prompt(case), encoding="utf-8")
    for name, content in case["files"].items():
        target = dest / safe_relative(name)
        if name in ("instruction.md", "packet_manifest.json", "submission.json"):
            raise ValueError(f"Reserved input filename: {name}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    hashes = {str(p.relative_to(dest)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(dest.rglob("*")) if p.is_file()}
    manifest = {"task_id": case["id"], "seed": case["seed"], "benchmark_version": __version__,
                "case_hash": case["case_hash"], "files": hashes, "contains_answers": False}
    (dest / "packet_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def _unique_pairs(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"Duplicate JSON key: {key}")
        obj[key] = value
    return obj


def parse_submission(value):
    if isinstance(value, str):
        if len(value.encode("utf-8")) > MAX_SUBMISSION_BYTES:
            raise ValueError("Submission exceeds 2 MB")
        text = value.strip()
        fence = re.fullmatch(r"```(?:json)?\s*\n([\s\S]*?)\n```", text, re.IGNORECASE)
        if fence:
            text = fence.group(1)
        value = json.loads(text, object_pairs_hook=_unique_pairs,
                           parse_constant=lambda x: (_ for _ in ()).throw(ValueError(f"Nonfinite number: {x}")))
    if not isinstance(value, dict):
        raise ValueError("Submission must be a JSON object")
    serialized = canonical_json(value)
    if len(serialized.encode("utf-8")) > MAX_SUBMISSION_BYTES:
        raise ValueError("Submission exceeds 2 MB")
    if not isinstance(value.get("task_id"), str) or not isinstance(value.get("answer"), dict):
        raise ValueError("task_id string and answer object are required")
    artifacts = value.get("artifacts", {})
    if not isinstance(artifacts, dict) or len(artifacts) > 40:
        raise ValueError("artifacts must be an object with at most 40 files")
    for name, content in artifacts.items():
        safe_relative(name)
        if not isinstance(content, str):
            raise ValueError("Every artifact must contain UTF-8 text as a JSON string")
    value = dict(value)
    value["artifacts"] = dict(artifacts)
    return value


def _execution_payload(row):
    return {k: row.get(k) for k in
        ("id", "task_id", "case_hash", "submission_hash", "source_hash", "input_hash", "result_hash",
         "evaluator_identity", "execution", "execution_status", "status", "passed", "checks")}


def _automatic_payload(report):
    keys = ("task_id", "seed", "case_hash", "submission_hash", "benchmark_version", "evaluation_schema_version",
            "evaluator_commit", "evaluator_digest", "evaluator_digest_algorithm", "answer_key_hash", "rubric_hash",
            "review_policy_version", "auto_points", "auto_max", "scored_max", "auto_percent", "coverage",
            "automatic_critical_failures", "missing_artifacts", "delivery_complete", "status", "error",
            "protocol_violation", "comparison_eligible")
    payload = {k: report.get(k) for k in keys}
    payload["checks"] = [{k: row[k] for k in ("id", "points", "passed", "critical", "cases") if k in row}
                         for row in report.get("checks", [])]
    payload["mandatory_execution"] = [_execution_payload(row)
        for row in report.get("mandatory_execution", []) if row.get("id") != "render"]
    return payload


def seal_report(report):
    report = refresh_completion(report)
    report["automatic_report_hash"] = fingerprint(_automatic_payload(report))
    return report


def validate_automatic_report(report):
    mandatory = report.get("mandatory_execution", [])
    if not isinstance(mandatory, list) or any(not isinstance(x, dict) for x in mandatory):
        raise ValueError("Mandatory execution evidence must be a list of records")
    allowed = {"solve_reproduction"} if report.get("task_id") == "NRB03" else (
        {"render"} if report.get("task_id") == "NRB09" and report.get("review_pending") is False else set())
    if (any(not isinstance(x.get("id"), str) or x["id"] not in allowed for x in mandatory)
            or len({x["id"] for x in mandatory}) != len(mandatory)):
        raise ValueError("Unexpected or duplicate mandatory execution responsibility")
    if any(x.get("passed") is not None and type(x.get("passed")) is not bool for x in mandatory):
        raise ValueError("Mandatory execution outcomes must be Boolean or null")
    checks = report.get("checks")
    if not isinstance(checks, list) or not checks or any(not isinstance(x, dict) for x in checks):
        raise ValueError("Automatic report requires its original check records")
    if any(not isinstance(x.get("id"), str) for x in checks) or len({x["id"] for x in checks}) != len(checks):
        raise ValueError("Automatic check IDs must be distinct strings")
    for row in checks:
        value = row.get("points")
        if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value < 0:
            raise ValueError("Invalid check weight")
        if row.get("passed") is not None and type(row.get("passed")) is not bool:
            raise ValueError("Check outcomes must be Boolean or null")
    maximum = sum(x["points"] for x in checks)
    scored = sum(x["points"] for x in checks if x["passed"] is not None)
    points = sum(x["points"] for x in checks if x["passed"] is True)
    expected = {"auto_max": 70, "scored_max": scored, "auto_points": points, "coverage": scored / 70,
                "auto_percent": points / 70 * 100 if scored == 70 else None}
    if maximum != 70:
        raise ValueError("Automatic check weights must total70")
    for key, value in expected.items():
        actual = report.get(key)
        if value is None:
            valid = actual is None
        else:
            valid = not isinstance(actual, bool) and isinstance(actual, (int, float)) and math.isfinite(actual) and math.isclose(actual, value, rel_tol=1e-12, abs_tol=1e-12)
        if not valid:
            raise ValueError("Automatic report is internally inconsistent: " + key)
    if report.get("automatic_report_hash") != fingerprint(_automatic_payload(report)):
        raise ValueError("Automatic report content hash mismatch")
    return True


def _review_payload(report):
    return {k: report.get(k) for k in ("automatic_report_hash", "review", "review_points", "total",
             "review_pending", "essential_review", "mandatory_execution", "score_label",
             "completion_status", "quality_qualified", "critical_failures", "review_critical_failures",
             "pending_items", "completion_judgement", "qualification_threshold")}


def validate_final_report(report):
    """Check scores and completion from their records before any aggregation."""
    validate_automatic_report(report)
    essential_case = {"essential_review_requirements": requirements(report["task_id"])}
    validate_essential(essential_case, report.get("essential_review"))
    if report.get("review_pending") is True:
        if report.get("review_points") is not None or report.get("total") is not None:
            raise ValueError("Unreviewed reports cannot contain quality scores")
        if any(x["outcome"] != "unassessed" for x in report["essential_review"]):
            raise ValueError("Essential decisions require a bound review ledger")
    elif report.get("review_pending") is False:
        review = report.get("review")
        if not isinstance(review, dict) or identity_from(review) != identity_from(report):
            raise ValueError("Reviewed report lacks its matching evaluator-bound ledger")
        for key in ("task_id", "seed", "case_hash", "submission_hash", "rubric_hash", "review_policy_version", "automatic_report_hash"):
            if review.get(key) != report.get(key):
                raise ValueError("Reviewed ledger/report binding mismatch: " + key)
        entries = review.get("criteria")
        if (not isinstance(entries, list) or len(entries) != 3
                or any(not isinstance(x, dict) or not isinstance(x.get("id"), str) for x in entries)
                or len({x["id"] for x in entries}) != 3):
            raise ValueError("Reviewed report requires three distinct quality entries")
        points = 0
        for row in entries:
            score = row.get("score")
            if (isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score)
                    or not 0 <= score <= 10):
                raise ValueError("Invalid reviewed quality score")
            points += score
        expected_total = report["auto_points"] + points if report["coverage"] == 1 else None
        if report.get("review_points") != points or report.get("total") != expected_total:
            raise ValueError("Reviewed total is inconsistent with its bound quality entries")
        if report["essential_review"] != review.get("essential_review"):
            raise ValueError("Essential decisions differ from the bound review")
        kind = review.get("reviewer_type")
        if kind not in ("human", "llm") or report.get("score_label") != ("human_reviewed" if kind == "human" else "llm_reviewed_provisional"):
            raise ValueError("Reviewer identity/score label mismatch")
        if report.get("reviewed_report_hash") != fingerprint(_review_payload(report)):
            raise ValueError("Reviewed report content hash mismatch")
    else:
        raise ValueError("Explicit review_pending Boolean is required")
    expected = refresh_completion(report)
    keys = ("completion_status", "quality_qualified", "critical_failures", "review_critical_failures",
            "pending_items", "completion_judgement", "qualification_threshold")
    if canonical_json({k: report.get(k) for k in keys}) != canonical_json({k: expected.get(k) for k in keys}):
        raise ValueError("Completion fields are inconsistent with the scientific obligations and evidence")
    return True


def _report(case, checks, submission_hash=None, error=None):
    total_max = sum(c["points"] for c in checks)
    if not math.isclose(total_max, 70):
        raise ValueError(f"Grader weights for {case['id']} sum to {total_max}, not 70")
    if len({c["id"] for c in checks}) != len(checks):
        raise ValueError("Check IDs must be unique")
    for c in checks:
        if c["points"] < 0 or c["passed"] not in (True, False, None):
            raise ValueError("Invalid grader check")
    scored_max = sum(c["points"] for c in checks if c["passed"] is not None)
    points = sum(c["points"] for c in checks if c["passed"] is True)
    essential_auto = ESSENTIAL_AUTOMATIC.get(case["id"], set())
    for c in checks:
        c["critical"] = c.get("critical", False) or c["id"] in essential_auto
    critical = [c["id"] for c in checks if c.get("critical") and c["passed"] is False]
    report = {"task_id": case["id"], "seed": case["seed"], "case_hash": case["case_hash"],
            **evaluator_identity(), "submission_hash": submission_hash,
            "answer_key_hash": fingerprint(case["expected"]), "rubric_hash": case["rubric_hash"],
            "review_policy_version": REVIEW_POLICY_VERSION, "essential_review": blank_essential(case),
            "auto_points": points, "auto_max": 70, "scored_max": scored_max,
            "auto_percent": 100 * points / 70 if scored_max == 70 else None,
            "coverage": scored_max / 70, "checks": checks, "critical_failures": critical,
            "review_pending": True, "review_points": None, "total": None,
            "status": "complete_auto" if scored_max == 70 else "infrastructure_unscored",
            "error": error}
    return seal_report(report)


def grade_submission(case, submission, execution="none"):
    try:
        submission = parse_submission(submission)
        if submission["task_id"] != case["id"]:
            raise ValueError("Submission task_id does not match the requested task")
    except (ValueError, TypeError, RecursionError) as exc:
        return _report(case, [{"id": "submission_schema", "points": 70.0, "passed": False,
                              "detail": str(exc), "critical": True}], error="invalid_submission")
    digest = fingerprint(submission)
    try:
        checks = task_module(case["id"]).grade(case, submission, execution=execution)
        report = _report(case, checks, digest)
        missing = [p for p in case["required_artifacts"] if not submission["artifacts"].get(p, "").strip()]
        report.update(missing_artifacts=missing, delivery_complete=not missing)
        if case["id"] == "NRB03":
            receipt = task_module(case["id"]).reproduce_solution(case, submission, execution=execution)
            receipt["evaluator_identity"] = identity_from(report)
            report["mandatory_execution"] = [receipt]
        if missing:
            report["automatic_critical_failures"].append("required_artifacts")
        return seal_report(report)
    except Exception as exc:
        # A bug in a verifier is infrastructure failure, never a model failure.
        return _report(case, [{"id": "grader_error", "points": 70.0, "passed": None,
                              "detail": f"{type(exc).__name__}: {exc}", "critical": False}], digest,
                       error="grader_error")


def review_ledger(case, submission, report=None):
    """A blank evaluator-bound ledger; no quality or essential passes are filled."""
    report = grade_submission(case, submission) if report is None else report
    validate_automatic_report(report)
    return {"task_id": case["id"], "seed": case["seed"], "case_hash": case["case_hash"],
            "submission_hash": fingerprint(submission), **evaluator_identity(),
            "rubric_hash": case["rubric_hash"], "review_policy_version": REVIEW_POLICY_VERSION,
            "automatic_report_hash": report["automatic_report_hash"],
            "reviewer_id": "REPLACE", "reviewer_type": "human",
            "criteria": [{"id": c["id"], "score": None, "rationale": "", "evidence": ""} for c in case["rubric"]],
            "essential_review": blank_essential(case), "evidence_artifacts": {},
            "inspected_whole_figure": False, "inspected_at_180mm": False}


def _read_evidence(review, name, evidence_dir):
    item = review.get("evidence_artifacts", {}).get(name)
    if not isinstance(item, dict) or evidence_dir is None:
        raise ValueError("Required evaluator-side evidence is missing: " + name)
    base = Path(evidence_dir).resolve()
    path = base / safe_relative(item.get("file"))
    if path.is_symlink() or not path.resolve().is_relative_to(base) or not path.is_file():
        raise ValueError("Evidence must be a regular file inside the review packet")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != item.get("sha256"):
        raise ValueError("Review evidence bytes differ from their recorded hash")
    receipt = json.loads(data)
    if not isinstance(receipt, dict):
        raise ValueError("Review evidence receipt must be an object")
    return receipt, base


def _validate_execution_evidence(case, submission, review, essential, evidence_dir):
    if not isinstance(review.get("evidence_artifacts", {}), dict):
        raise ValueError("Review evidence_artifacts must be an object")
    outcomes = {item["id"]: item["outcome"] for item in essential}
    observed = []
    if case["id"] == "NRB03" and (outcomes.get("search_reproduced") == "pass" or
                                     "solve_reproduction" in review.get("evidence_artifacts", {})):
        receipt, _ = _read_evidence(review, "solve_reproduction", evidence_dir)
        expected = {"id": "solve_reproduction", "task_id": case["id"], "case_hash": case["case_hash"],
                    "submission_hash": fingerprint(submission), "evaluator_identity": evaluator_identity()}
        if any(receipt.get(k) != v for k, v in expected.items()):
            raise ValueError("Search reproduction belongs to a different submission or evaluator")
        source = submission["artifacts"].get("solve.py")
        source_hash = hashlib.sha256(source.encode("utf-8")).hexdigest() if isinstance(source, str) else None
        if receipt.get("source_hash") != source_hash:
            raise ValueError("Search execution receipt belongs to different code")
        if receipt.get("input_hash") != fingerprint(json.loads(case["files"]["design.json"])):
            raise ValueError("Search execution input hash mismatch")
        states = {"pass": True, "fail": False, "unassessed": None}
        state = receipt.get("status")
        if not isinstance(state, str) or state not in states or receipt.get("passed") is not states[state]:
            raise ValueError("Search execution status is inconsistent")
        if receipt.get("passed") is True:
            if (receipt.get("execution") not in {"docker", "container"} or receipt.get("execution_status") != "ok"
                    or not isinstance(receipt.get("result_hash"), str)
                    or not re.fullmatch(r"[0-9a-f]{64}", receipt["result_hash"])
                    or not isinstance(receipt.get("checks"), list) or not receipt["checks"]
                    or any(not isinstance(x, dict) or x.get("passed") is not True for x in receipt["checks"])):
                raise ValueError("Search pass requires successful isolated execution and result checks")
        if outcomes.get("search_reproduced") == "pass" and receipt.get("passed") is not True:
            raise ValueError("Search reproduction must actually pass before the essential responsibility can pass")
        observed.append(receipt)
    if case["id"] == "NRB09" and (outcomes.get("render_legibility") == "pass" or
                                     "render" in review.get("evidence_artifacts", {})):
        receipt, base = _read_evidence(review, "render", evidence_dir)
        if receipt.get("rendered") is not True:
            expected = {"case_hash": case["case_hash"], "submission_hash": fingerprint(submission),
                        "evaluator_identity": evaluator_identity()}
            if any(receipt.get(k) != v for k, v in expected.items()) or receipt.get("status") not in {"unsafe_svg", "unavailable"}:
                raise ValueError("Invalid failed/unavailable render receipt")
            if outcomes.get("render_legibility") == "pass":
                raise ValueError("Unrendered SVG cannot pass actual-render review")
            observed.append({"id": "render", "passed": False if receipt["status"] == "unsafe_svg" else None,
                             "detail": receipt.get("detail", "")})
            return observed
        png = base / safe_relative(review.get("render_png"))
        if png.is_symlink() or not png.resolve().is_relative_to(base):
            raise ValueError("Rendered image must be inside the review packet")
        from .rendering import validate_render_receipt
        errors = validate_render_receipt(receipt, submission["artifacts"].get("figure.svg", ""),
                    case_hash=case["case_hash"], submission_hash=fingerprint(submission),
                    evaluator_identity=evaluator_identity(), png_path=png)
        if errors:
            raise ValueError("Invalid actual-render evidence: " + "; ".join(errors))
        if outcomes.get("render_legibility") == "pass" and (review.get("inspected_whole_figure") is not True or review.get("inspected_at_180mm") is not True):
            raise ValueError("Render pass requires explicit whole-figure and 180mm inspection")
        observed.append({"id": "render", "passed": True, "detail": "Actual rendered bytes verified; readability remains a separate review judgement"})
    return observed


def attach_review(case, report, review, *, submission=None, evidence_dir=None):
    """Require an explicit, submission-bound reviewer ledger; never invent review points."""
    require_current_identity(report)
    require_current_identity(review)
    validate_automatic_report(report)
    if submission is None:
        raise ValueError("Original submission is required to bind review and report")
    submission = parse_submission(submission)
    for key, value in {"task_id": case["id"], "seed": case["seed"], "case_hash": case["case_hash"],
                       "submission_hash": fingerprint(submission), "rubric_hash": case["rubric_hash"],
                       "review_policy_version": REVIEW_POLICY_VERSION}.items():
        if report.get(key) != value or review.get(key) != value:
            raise ValueError("Report/review identity mismatch: " + key)
    if report.get("answer_key_hash") != fingerprint(case["expected"]):
        raise ValueError("Report answer key fingerprint mismatch")
    if review.get("automatic_report_hash") != report["automatic_report_hash"]:
        raise ValueError("Review belongs to different automatic grading results")
    if submission["task_id"] != case["id"]:
        raise ValueError("Original submission task mismatch")
    if review.get("task_id") != case["id"] or review.get("case_hash") != case["case_hash"]:
        raise ValueError("Review task/case hash mismatch")
    if review.get("submission_hash") != report["submission_hash"]:
        raise ValueError("Review submission hash mismatch")
    if (review.get("reviewer_type") not in ("human", "llm") or not isinstance(review.get("reviewer_id"), str)
            or not review["reviewer_id"].strip() or review["reviewer_id"].strip() == "REPLACE"):
        raise ValueError("Reviewer ID and type (human|llm) are required")
    entries = review.get("criteria", [])
    required = {c["id"] for c in case["rubric"]}
    if (not isinstance(entries, list) or len(entries) != 3 or any(not isinstance(x, dict) or not isinstance(x.get("id"), str) for x in entries)
            or {x.get("id") for x in entries} != required):
        raise ValueError("Review must score each of the three criteria exactly once")
    points = 0.0
    for entry in entries:
        s = entry.get("score")
        if isinstance(s, bool) or not isinstance(s, (int, float)) or not 0 <= s <= 10 or not math.isfinite(s):
            raise ValueError("Review scores must be finite numbers from 0 to 10")
        if not isinstance(entry.get("rationale"), str) or not entry["rationale"].strip():
            raise ValueError("Every review score requires a rationale")
        if not isinstance(entry.get("evidence"), str) or not entry["evidence"].strip():
            raise ValueError("Every review score requires submission-specific evidence")
        points += s
    result = dict(report)
    essential = validate_essential(case, review.get("essential_review"))
    observed = _validate_execution_evidence(case, submission, review, essential, evidence_dir)
    existing = {x["id"]: x for x in report.get("mandatory_execution", [])}
    for item in observed:
        if item["id"] not in existing:
            existing[item["id"]] = item
        elif ((item["id"] == "solve_reproduction" and _execution_payload(existing[item["id"]]) != _execution_payload(item))
              or existing[item["id"]].get("passed") != item["passed"]):
            raise ValueError("Review evidence disagrees with current mandatory execution result")
    result.update(review_pending=False, review_points=points, review=review,
                  essential_review=essential, mandatory_execution=list(existing.values()),
                  total=report["auto_points"] + points if report["coverage"] == 1 else None)
    result["score_label"] = "human_reviewed" if review["reviewer_type"] == "human" else "llm_reviewed_provisional"
    result = refresh_completion(result)
    result["reviewed_report_hash"] = fingerprint(_review_payload(result))
    validate_final_report(result)
    return result


def summarize(reports, expected_ids=TASK_IDS):
    reports = list(reports)
    ids = [r["task_id"] for r in reports]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate tasks: aggregate seeds/repeats separately before comparison")
    expected_ids = tuple(expected_ids)
    if set(ids) - set(expected_ids):
        raise ValueError("Summary contains tasks outside the declared denominator")
    versions = {r.get("benchmark_version") for r in reports}
    if len(versions) > 1:
        raise ValueError("Cannot summarize mixed benchmark versions")
    identities = [identity_from(r) for r in reports]
    if len({canonical_json(x) for x in identities}) > 1:
        raise ValueError("Cannot summarize mixed evaluator identities or legacy/current reports")
    identity = identities[0] if identities else evaluator_identity()
    verified = identity is not None
    if verified:
        for report in reports:
            validate_final_report(report)
    missing = sorted(set(expected_ids) - set(ids))
    complete = not missing and all(r["coverage"] == 1 and not r.get("protocol_violation")
                                  and r.get("comparison_eligible") is not False for r in reports)
    reviewed = complete and all(r.get("total") is not None for r in reports)
    n = len(reports)
    denominator = len(expected_ids)
    counts = {k: 0 for k in ("complete", "failed", "pending_review", "infrastructure_unscored", "legacy_unverified", "missing")}
    counts["missing"] = len(missing)
    for r in reports:
        status = r.get("completion_status", "legacy_unverified") if verified else "legacy_unverified"
        if status not in counts:
            raise ValueError("Unknown completion status")
        counts[status] += 1
    unknown = sum(counts[k] for k in ("pending_review", "infrastructure_unscored", "legacy_unverified", "missing"))
    review_types = {r.get("review", {}).get("reviewer_type") for r in reports if not r.get("review_pending", True)} - {None}
    review_status = ("mixed_human_llm_provisional" if len(review_types) > 1 else
                     "llm_reviewed_provisional" if review_types == {"llm"} else
                     ("human_reviewed" if reviewed else "partial_human_review") if review_types == {"human"}
                     else "unreviewed")
    confirmed_critical = sum(bool(r.get("critical_failures")) for r in reports)
    unresolved_critical = sum(not r.get("critical_failures") and
                              (r.get("completion_status") != "complete" or not verified) for r in reports) + len(missing)
    scores = [r["auto_percent"] for r in reports if r.get("auto_percent") is not None]
    result = {"benchmark_version": next(iter(versions)) if versions else __version__,
            **(identity or {}), "scoring_identity_status": "verified_content" if verified else "legacy_unverified",
            "comparison_eligible": complete and verified,
            "task_count": n, "expected_tasks": denominator,
            "missing_tasks": missing, "complete_auto": complete,
            "auto_macro_percent": sum(r["auto_percent"] for r in reports) / n if complete and n else None,
            "reviewed_macro_total": sum(r["total"] for r in reports) / n if reviewed and n else None,
            "automatic_critical_free_rate": sum(not r.get("automatic_critical_failures", r["critical_failures"]) for r in reports) / n if complete and n else None,
            "critical_free_rate": 1 - confirmed_critical / denominator if denominator and not unresolved_critical else None,
            "critical_failure_rate_bounds": [confirmed_critical / denominator, (confirmed_critical + unresolved_critical) / denominator] if denominator else None,
            "completion_counts": counts,
            "completion_rate": counts["complete"] / denominator if denominator and not unknown else None,
            "completion_rate_bounds": [counts["complete"] / denominator, (counts["complete"] + unknown) / denominator] if denominator else None,
            "pending_task_count": unknown,
            "review_status": review_status,
            "review_coverage": sum(not r["review_pending"] for r in reports) / denominator if denominator else 0,
            "min_task_auto_percent": min(scores) if scores else None,
            "min_task_reviewed_total": min(r["total"] for r in reports) if reviewed and n else None,
            "task_table": [{"task_id": r["task_id"], "auto_points": r["auto_points"], "auto_percent": r["auto_percent"],
                            "review_points": r.get("review_points"), "total": r.get("total"),
                            "completion_status": r.get("completion_status", "legacy_unverified"),
                            "quality_qualified": r.get("quality_qualified"), "critical_failures": r.get("critical_failures", []),
                            "pending_items": r.get("pending_items", ["legacy_unverified"])} for r in reports],
            "reports": reports}
    return result

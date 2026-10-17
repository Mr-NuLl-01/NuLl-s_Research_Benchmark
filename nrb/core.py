"""One task definition and one scorer, shared by every harness adapter."""
from __future__ import annotations
import hashlib
import importlib
import json
import math
from pathlib import Path, PurePosixPath
import re
from . import __version__

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
    return {k: case[k] for k in ("id", "title", "domain", "seed", "benchmark_version", "prompt", "files", "rubric", "required_artifacts")}


def get_case(task_id, seed=0):
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**32:
        raise ValueError("seed must be an integer in [0, 2**32)")
    case = task_module(task_id).build(seed)
    case.update(seed=seed, benchmark_version=__version__)
    case["required_artifacts"] = list(REQUIRED_ARTIFACTS[task_id])
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
    critical = [c["id"] for c in checks if c.get("critical") and c["passed"] is False]
    return {"task_id": case["id"], "seed": case["seed"], "case_hash": case["case_hash"],
            "benchmark_version": __version__, "submission_hash": submission_hash,
            "auto_points": points, "auto_max": 70, "scored_max": scored_max,
            "auto_percent": 100 * points / 70 if scored_max == 70 else None,
            "coverage": scored_max / 70, "checks": checks, "critical_failures": critical,
            "review_pending": True, "review_points": None, "total": None,
            "status": "complete_auto" if scored_max == 70 else "infrastructure_unscored",
            "error": error}


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
        if missing:
            report["critical_failures"].append("required_artifacts")
        return report
    except Exception as exc:
        # A bug in a verifier is infrastructure failure, never a model failure.
        return _report(case, [{"id": "grader_error", "points": 70.0, "passed": None,
                              "detail": f"{type(exc).__name__}: {exc}", "critical": False}], digest,
                       error="grader_error")


def attach_review(case, report, review):
    """Require an explicit, submission-bound reviewer ledger; never invent review points."""
    if review.get("task_id") != case["id"] or review.get("case_hash") != case["case_hash"]:
        raise ValueError("Review task/case hash mismatch")
    if review.get("submission_hash") != report["submission_hash"]:
        raise ValueError("Review submission hash mismatch")
    if review.get("reviewer_type") not in ("human", "llm") or not review.get("reviewer_id"):
        raise ValueError("Reviewer ID and type (human|llm) are required")
    entries = review.get("criteria", [])
    required = {c["id"] for c in case["rubric"]}
    if len(entries) != 3 or {x.get("id") for x in entries} != required:
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
    result.update(review_pending=False, review_points=points, review=review,
                  total=report["auto_points"] + points if report["coverage"] == 1 else None)
    result["score_label"] = "human_reviewed" if review["reviewer_type"] == "human" else "llm_reviewed_provisional"
    return result


def summarize(reports, expected_ids=TASK_IDS):
    reports = list(reports)
    ids = [r["task_id"] for r in reports]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate tasks: aggregate seeds/repeats separately before comparison")
    missing = sorted(set(expected_ids) - set(ids))
    complete = not missing and all(r["coverage"] == 1 for r in reports)
    reviewed = complete and all(r.get("total") is not None for r in reports)
    n = len(reports)
    return {"benchmark_version": __version__, "task_count": n, "expected_tasks": len(expected_ids),
            "missing_tasks": missing, "complete_auto": complete,
            "auto_macro_percent": sum(r["auto_percent"] for r in reports) / n if complete and n else None,
            "reviewed_macro_total": sum(r["total"] for r in reports) / n if reviewed and n else None,
            "critical_free_rate": sum(not r["critical_failures"] for r in reports) / n if complete and n else None,
            "review_coverage": sum(not r["review_pending"] for r in reports) / n if n else 0,
            "reports": reports}

from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import subprocess
from . import __version__


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def fingerprint(value):
    data = value if isinstance(value, bytes) else canonical(value).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def identity():
    root = Path(__file__).resolve().parent
    files = [*root.rglob("*.py"), root / "policy.json", root / "video_rubrics.json"]
    manifest = {p.relative_to(root).as_posix(): fingerprint(p.read_bytes()) for p in sorted(files)
                if "__pycache__" not in p.parts}
    digest = fingerprint({"algorithm": "sha256-path-content-v1", "files": manifest})
    try:
        proc = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True,
                              text=True, timeout=3, check=False)
        commit = proc.stdout.strip() if proc.returncode == 0 else None
        if commit and not re.fullmatch(r"[0-9a-f]{40}", commit):
            commit = None
    except (OSError, subprocess.SubprocessError):
        commit = None
    origin = root / "_origin.json"
    if origin.exists():
        origin_data = json.loads(origin.read_text())
        if origin_data["evaluator_digest"] != digest:
            raise ValueError("Exported evaluator source changed")
        commit = commit or origin_data.get("evaluator_commit")
    return {"benchmark_version": __version__, "scoring_schema": "nrb-v1.1",
            "evaluator_commit": commit, "evaluator_digest": digest,
            "digest_algorithm": "sha256-path-content-v1"}


def seal(report):
    return fingerprint({k: v for k, v in report.items() if k != "report_hash"})


def validate_report(report, current=True):
    if report.get("report_hash") != seal(report):
        raise ValueError("Report content fingerprint mismatch")
    if current and report.get("evaluator_identity") != identity():
        raise ValueError("Evaluator commit/content identity differs; regrade consistently")
    return report

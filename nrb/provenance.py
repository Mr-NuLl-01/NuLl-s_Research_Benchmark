"""Evaluator identity from actual installed scoring bytes, never from the prompt.

The digest covers all nrb Python sources (including hidden behavior cases and
reference calculations) and evaluation_policy.json. Regression tests, generated
questions, logs, documentation and the export-origin stamp are excluded.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import subprocess
from . import __version__

EVALUATION_SCHEMA_VERSION = "2.0"
DIGEST_ALGORITHM = "sha256-canonical-path-content-manifest-v1"
IDENTITY_FIELDS = ("benchmark_version", "evaluation_schema_version", "evaluator_commit",
                   "evaluator_digest", "evaluator_digest_algorithm")


def _canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def source_manifest(package_root=None):
    root = Path(package_root) if package_root is not None else Path(__file__).resolve().parent
    paths = sorted([*root.rglob("*.py"), root / "evaluation_policy.json"])
    manifest = {}
    for path in paths:
        if "__pycache__" in path.parts:
            continue
        if path.is_symlink() or not path.is_file():
            raise ValueError("Evaluator source must be present regular files: " + str(path))
        manifest["nrb/" + path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return manifest


def evaluator_digest(package_root=None):
    return hashlib.sha256(_canonical({"algorithm": DIGEST_ALGORITHM,
                                      "files": source_manifest(package_root)}).encode("utf-8")).hexdigest()


def _git_commit(root):
    try:
        proc = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                              capture_output=True, text=True, timeout=3, check=False)
        value = proc.stdout.strip()
        return value if proc.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", value) else None
    except (OSError, subprocess.SubprocessError):
        return None


def evaluator_identity(package_root=None):
    root = Path(package_root) if package_root is not None else Path(__file__).resolve().parent
    digest = evaluator_digest(root)
    commit = _git_commit(root)
    origin = root / "_evaluator_origin.json"
    if origin.is_file():
        stamp = json.loads(origin.read_text(encoding="utf-8"))
        if stamp.get("evaluator_digest") != digest:
            raise ValueError("Sealed evaluator source differs from its exported content fingerprint")
        recorded = stamp.get("evaluator_commit")
        if recorded is not None and not re.fullmatch(r"[0-9a-f]{40}", str(recorded)):
            raise ValueError("Invalid exported evaluator commit")
        if commit is None:
            commit = recorded
    return {"benchmark_version": __version__, "evaluation_schema_version": EVALUATION_SCHEMA_VERSION,
            "evaluator_commit": commit, "evaluator_digest": digest,
            "evaluator_digest_algorithm": DIGEST_ALGORITHM}


def identity_from(report):
    """Return None for legacy/unverified records; do not fill today's identity."""
    if not isinstance(report, dict) or any(k not in report for k in IDENTITY_FIELDS):
        return None
    digest, commit = report.get("evaluator_digest"), report.get("evaluator_commit")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        return None
    if commit is not None and (not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit)):
        return None
    if report.get("evaluator_digest_algorithm") != DIGEST_ALGORITHM:
        return None
    return {key: report[key] for key in IDENTITY_FIELDS}


def require_current_identity(report):
    actual = identity_from(report)
    if actual is None or actual != evaluator_identity():
        raise ValueError("Evaluator identity is legacy, missing, or differs from the current scoring source")
    return actual

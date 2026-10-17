"""A small, auditable subprocess bridge for CLI research agents.

The working directory is fresh and contains candidate inputs only. This is NOT
a security sandbox: use an externally isolated host/container for scored runs.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import threading
import time
from datetime import datetime, timezone
from typing import Any


MAX_OUTPUT_BYTES = 8 * 1024 * 1024
_SECRET_FLAG = re.compile(r"(?:api[-_]?key|access[-_]?token|auth[-_]?token|password|secret)", re.I)
_TOKEN = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{12,}|github_pat_[A-Za-z0-9_]{12,}|gh[pousr]_[A-Za-z0-9]{12,})\b")


class ReportedCLIError(ValueError):
    """A documented CLI envelope explicitly reports an unsuccessful run."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _redactor():
    # Values never leave this closure or appear in a manifest. This is a
    # best-effort transcript filter, not a substitute for an isolated account.
    secrets = sorted(
        {v for k, v in os.environ.items() if _SECRET_FLAG.search(k) and len(v) >= 8},
        key=len, reverse=True,
    )

    def redact(text: str) -> str:
        for value in secrets:
            text = text.replace(value, "[REDACTED]")
        return _TOKEN.sub("[REDACTED]", text)

    return redact


def _validate_command(command: list[str]) -> None:
    if not isinstance(command, list) or not command or not all(isinstance(s, str) and "\0" not in s for s in command):
        raise ValueError("command must be a nonempty argv list of strings")
    for arg in command:
        if (arg.startswith("-") and _SECRET_FLAG.search(arg)) or _TOKEN.search(arg):
            raise ValueError("Do not put credentials in argv; use the agent's normal authentication or environment")
        if re.search(r"https?://[^/@\s]+:[^/@\s]+@", arg):
            raise ValueError("Credential-bearing URLs are not allowed in argv")


def _stop_group(proc: subprocess.Popen) -> None:
    if os.name == "posix":
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    else:
        # Windows needs /T to include descendants. This branch is not claimed
        # runtime-validated on Linux.
        try:
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10, check=False)
        except (OSError, subprocess.TimeoutExpired):
            proc.kill()


def _snapshot(directory: Path) -> dict[str, str]:
    files = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError("Candidate packet must not contain symlinks")
        if path.is_file():
            files[path.relative_to(directory).as_posix()] = _sha(path.read_bytes())
    return files


def _integrity(directory: Path, manifest: dict[str, str]) -> dict[str, Any]:
    changed, missing, symlinks = [], [], []
    for rel, digest in manifest.items():
        path = directory / rel
        # Check every ancestor too; replacing a supplied directory with a
        # symlink must not cause the evaluator to read unrelated host files.
        parents = [directory.joinpath(*Path(rel).parts[:i]) for i in range(1, len(Path(rel).parts) + 1)]
        if any(p.is_symlink() for p in parents):
            symlinks.append(rel)
        elif not path.is_file():
            missing.append(rel)
        elif path.stat().st_size > MAX_OUTPUT_BYTES or _sha(path.read_bytes()) != digest:
            changed.append(rel)
    return {"unchanged": not (changed or missing or symlinks), "changed_files": changed,
            "missing_files": missing, "symlink_files": symlinks}


def unwrap_output(text: str, stdout_format: str = "plain") -> tuple[str, dict | None, float | None]:
    """Extract documented CLI result envelopes, never guess from random braces.

    Returns final text, provider-reported usage, provider-reported estimated cost.
    No token counts or prices are inferred by this project.
    """
    if stdout_format == "plain":
        return text, None, None
    if stdout_format == "codex-jsonl":
        final, usage = None, None
        for line in text.splitlines():
            if not line.strip():
                continue
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError("Invalid Codex JSONL event")
            if event.get("type") in ("turn.failed", "error"):
                raise ReportedCLIError("Codex reported a failed turn")
            if event.get("type") == "item.completed":
                item = event.get("item")
                if not isinstance(item, dict):
                    raise ValueError("Codex item.completed requires an item object")
                if item.get("type") == "agent_message":
                    if not isinstance(item.get("text"), str):
                        raise ValueError("Codex agent_message requires text")
                    final = item["text"]
            if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
                usage = {"source": "codex.turn.completed", "reported": event["usage"]}
        if not isinstance(final, str):
            raise ValueError("No final agent_message in Codex JSONL output")
        return final, usage, None
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("CLI JSON output must be an object")
    if stdout_format == "claude-json":
        if payload.get("is_error"):
            raise ReportedCLIError("Claude Code reported an error")
        final = payload.get("result")
        usage = None
        if isinstance(payload.get("usage"), dict):
            usage = {"source": "claude-code.result", "reported": payload["usage"],
                     "model_usage": payload.get("modelUsage")}
        cost = payload.get("total_cost_usd")
        if not isinstance(cost, (int, float)) or isinstance(cost, bool) or not math.isfinite(cost) or cost < 0:
            cost = None
    elif stdout_format == "gemini-json":
        if payload.get("error") is not None:
            raise ReportedCLIError("Gemini CLI reported an error")
        final = payload.get("response")
        usage = {"source": "gemini-cli.stats", "reported": payload["stats"]} if isinstance(payload.get("stats"), dict) else None
        cost = None
    else:
        raise ValueError("stdout_format must be plain, codex-jsonl, claude-json, or gemini-json")
    if not isinstance(final, str):
        raise ValueError("Missing final response string in CLI envelope")
    return final, usage, cost


def run_command(case: dict, command: list[str], workdir: Path, timeout: float = 600,
                *, stdout_format: str = "plain") -> dict:
    """Run a fresh attempt. Records execution facts; does not award points.

    ``command`` is executed directly, without shell interpolation. The complete
    prompt goes to stdin. Prefer ``submission.json`` written by the agent;
    otherwise parse the exact final response. Nonzero exit and dependency
    errors remain distinct from answer correctness.
    """
    from nrb.core import MAX_SUBMISSION_BYTES, candidate_prompt, parse_submission, write_candidate_packet

    _validate_command(command)
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be a positive finite number")
    if stdout_format not in {"plain", "codex-jsonl", "claude-json", "gemini-json"}:
        raise ValueError("Unknown stdout_format")
    workdir = Path(workdir).absolute()
    repository = Path(__file__).resolve().parents[1]
    if workdir.resolve().is_relative_to(repository):
        raise ValueError("Place candidate workdirs outside the evaluator repository")
    logdir = workdir.with_name(workdir.name + ".evaluator")
    if workdir.exists() or workdir.is_symlink() or logdir.exists() or logdir.is_symlink():
        raise FileExistsError("Fresh workdir and evaluator directory required; stale submissions are never reused")
    workdir.mkdir(parents=True)
    logdir.mkdir()
    write_candidate_packet(case, workdir)
    manifest = _snapshot(workdir)
    prompt = candidate_prompt(case) + (
        "\n\nRunner delivery: write the complete submission JSON to submission.json in the current directory, "
        "or return exactly that JSON on stdout. Keep all supplied input files unchanged. "
        "Put requested deliverables into the submission's artifacts object.\n"
    )
    redact = _redactor()
    base_prompt_sha = _sha(candidate_prompt(case).encode("utf-8"))
    record = {
        "task_id": case["id"], "seed": case.get("seed", 0), "candidate_sha256": base_prompt_sha,
        "prompt_sha256": _sha(prompt.encode("utf-8")), "command_argv": [redact(arg) for arg in command],
        "workdir": str(workdir), "logs_dir": str(logdir), "timeout_seconds": timeout,
        "stdout_format": stdout_format, "execution_boundary": "host_process_no_security_isolation",
        "started_utc": _utc(), "status": "starting", "infra_error": None, "output_error": None,
        "envelope_error": None,
        "exit_code": None, "usage": None, "cost_usd": None, "cost_kind": None, "submission": None,
        "submission_source": None, "submission_sha256": None,
    }
    (logdir / "input_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    # Retain the exact candidate prompt outside the candidate workdir for audit.
    (logdir / "prompt.txt").write_text(prompt, encoding="utf-8")
    start = time.monotonic()
    stdout, stderr = bytearray(), bytearray()
    counts = {"stdout": 0, "stderr": 0}
    output_limit = threading.Event()
    timed_out = False
    proc = None
    try:
        proc = subprocess.Popen(command, cwd=workdir, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, start_new_session=(os.name == "posix"))

        def drain(stream, target, name):
            try:
                while True:
                    chunk = stream.read(65536)
                    if not chunk:
                        break
                    counts[name] += len(chunk)
                    remaining = MAX_OUTPUT_BYTES - len(target)
                    target.extend(chunk[:max(0, remaining)])
                    if counts[name] > MAX_OUTPUT_BYTES:
                        output_limit.set()
                        _stop_group(proc)
            finally:
                stream.close()

        def feed():
            try:
                proc.stdin.write(prompt.encode("utf-8"))
                proc.stdin.flush()
            except (BrokenPipeError, OSError):
                pass
            finally:
                proc.stdin.close()

        threads = [threading.Thread(target=drain, args=(proc.stdout, stdout, "stdout"), daemon=True),
                   threading.Thread(target=drain, args=(proc.stderr, stderr, "stderr"), daemon=True),
                   threading.Thread(target=feed, daemon=True)]
        for thread in threads:
            thread.start()
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            _stop_group(proc)
            proc.wait(timeout=10)
        # A finished CLI must not leave background children running or holding
        # transcript pipes open. New POSIX session provides a process group.
        if os.name == "posix":
            _stop_group(proc)
        for thread in threads:
            thread.join(timeout=2)
        record["exit_code"] = proc.returncode
        record["status"] = ("timeout" if timed_out else "output_limit_exceeded" if output_limit.is_set()
                            else "command_error" if proc.returncode else "completed")
    except FileNotFoundError:
        record.update(status="infrastructure_error", infra_error="executable_not_found")
    except PermissionError:
        record.update(status="infrastructure_error", infra_error="executable_permission_denied")
    except OSError as exc:
        record.update(status="infrastructure_error", infra_error=f"os_error_{exc.errno}")
    finally:
        record["finished_utc"] = _utc()
        record["elapsed_seconds"] = round(time.monotonic() - start, 6)
        record["output_bytes"] = counts
        record["input_integrity"] = _integrity(workdir, manifest)

    out_text, err_text = stdout.decode("utf-8", "replace"), stderr.decode("utf-8", "replace")
    (logdir / "stdout.txt").write_text(redact(out_text), encoding="utf-8")
    (logdir / "stderr.txt").write_text(redact(err_text), encoding="utf-8")
    final_text = None
    try:
        final_text, usage, cost = unwrap_output(out_text, stdout_format)
        record.update(usage=usage, cost_usd=cost,
                      cost_kind="provider_reported_client_estimate" if cost is not None else None)
    except ReportedCLIError as exc:
        record.update(status="command_error", infra_error="cli_reported_error",
                      envelope_error=redact(str(exc)), output_error=redact(str(exc)))
    except (ValueError, TypeError, KeyError) as exc:
        record["output_error"] = redact(str(exc))
        record["envelope_error"] = redact(str(exc))

    submission_path = workdir / "submission.json"
    if record["status"] == "completed":
        try:
            if submission_path.is_symlink():
                raise ValueError("submission.json must not be a symlink")
            if submission_path.exists():
                info = submission_path.stat()
                if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_SUBMISSION_BYTES:
                    raise ValueError("submission.json must be a regular file under the submission size limit")
                final_text = submission_path.read_text(encoding="utf-8")
                record["submission_source"] = "file"
            else:
                record["submission_source"] = "stdout"
            if final_text is None:
                raise ValueError("No usable final submission")
            submission = parse_submission(final_text)
            record["submission"] = submission
            record["submission_sha256"] = _sha(final_text.encode("utf-8"))
            record["output_error"] = None
        except (ValueError, TypeError, UnicodeError, OSError) as exc:
            record.update(status="invalid_submission", output_error=redact(str(exc)))
    if not record["input_integrity"]["unchanged"]:
        record["protocol_violation"] = "candidate_input_modified"
    else:
        record["protocol_violation"] = None
    # Preserve original submission in-memory for scoring; redact logged content.
    logged = dict(record)
    logged.pop("submission", None)
    (logdir / "run.json").write_text(json.dumps(logged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return record

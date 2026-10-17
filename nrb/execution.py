"""Execute submitted pure Python through an explicit backend.

Docker is the supported isolation boundary. 'trusted' is ONLY for our own
reference/mutation tests; subprocess -I and resource limits are not a sandbox.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import stat

RUNNER = '''import contextlib, importlib.util, io, json, sys
source, payload = sys.argv[1:3]
spec = importlib.util.spec_from_file_location("candidate_solution", source)
module = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):
    spec.loader.exec_module(module)
    result = module.solve(json.load(open(payload, encoding="utf-8")))
print(json.dumps(result, allow_nan=False))
'''


def _limits():
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_CPU, (8, 8))
        resource.setrlimit(resource.RLIMIT_FSIZE, (4_000_000, 4_000_000))
        resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
        resource.setrlimit(resource.RLIMIT_AS, (512_000_000, 512_000_000))
    except (ImportError, ValueError, OSError):
        pass


def _container_limits():
    _limits()
    os.setgroups([])
    os.setgid(65534)
    os.setuid(65534)
    # Linux PR_SET_NO_NEW_PRIVS prevents regaining privilege through exec.
    import ctypes
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(38, 1, 0, 0, 0) != 0:
        os._exit(126)


def run_python(source, payload, execution="none", timeout=5):
    if execution == "none":
        return {"status": "unavailable", "result": None,
                "detail": "Code execution not enabled. Use Docker; trusted is reserved for repository self-tests."}
    if execution not in ("docker", "trusted", "container"):
        raise ValueError("execution must be none, docker, trusted, or container")
    if execution == "docker" and not shutil.which("docker"):
        return {"status": "unavailable", "result": None, "detail": "Docker executable unavailable"}
    if execution == "container":
        package_root = Path(__file__).resolve().parent.parent
        protected = package_root.stat()
        if (not sys.platform.startswith("linux") or os.geteuid() != 0
                or os.environ.get("NRB_CONTAINER_VERIFIER") != "1"
                or protected.st_uid != 0 or stat.S_IMODE(protected.st_mode) & 0o077):
            return {"status": "unavailable", "result": None,
                    "detail": "container mode requires a network-isolated verifier, root UID, NRB_CONTAINER_VERIFIER=1, and root-only mode700 grader directory"}
    if not isinstance(source, str) or len(source.encode("utf-8")) > 200_000:
        return {"status": "error", "result": None, "detail": "Missing or oversized Python source"}
    with tempfile.TemporaryDirectory(prefix="nrb-code-") as temp:
        root = Path(temp)
        (root / "solution.py").write_text(source, encoding="utf-8")
        (root / "payload.json").write_text(json.dumps(payload, allow_nan=False), encoding="utf-8")
        (root / "runner.py").write_text(RUNNER, encoding="utf-8")
        cidfile = root / "container.id"
        if execution == "docker":
            root.chmod(0o755)
            for p in root.iterdir():
                p.chmod(0o644)
            image = os.environ.get("NRB_PYTHON_IMAGE", "python:3.12-slim")
            cmd = ["docker", "run", "--rm", "--pull=never", "--cidfile", str(cidfile),
                   "--network=none", "--read-only", "--cap-drop=ALL",
                   "--security-opt=no-new-privileges", "--pids-limit=64", "--memory=256m", "--cpus=1",
                   "--user=65534:65534", "--tmpfs=/tmp:rw,noexec,nosuid,size=16m",
                   "--mount", f"type=bind,source={root},target=/task,readonly", image,
                   "python", "-I", "-B", "/task/runner.py", "/task/solution.py", "/task/payload.json"]
        else:
            cmd = [sys.executable, "-I", "-B", str(root / "runner.py"),
                   str(root / "solution.py"), str(root / "payload.json")]
            if execution == "container":
                root.chmod(0o755)
                for p in root.iterdir():
                    p.chmod(0o644)
        # No provider credentials or user environment reach the trusted child.
        child_env = {k: os.environ[k] for k in ("PATH", "SYSTEMROOT", "WINDIR", "DOCKER_HOST", "DOCKER_CONTEXT") if k in os.environ}
        kwargs = {"cwd": temp, "env": child_env, "start_new_session": os.name != "nt"}
        if execution == "trusted" and os.name != "nt":
            kwargs["preexec_fn"] = _limits
        elif execution == "container":
            kwargs["preexec_fn"] = _container_limits
        with open(root / "stdout.log", "w+b") as out, open(root / "stderr.log", "w+b") as err:
            try:
                proc = subprocess.Popen(cmd, stdout=out, stderr=err, **kwargs)
                try:
                    proc.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    if os.name != "nt":
                        os.killpg(proc.pid, signal.SIGKILL)
                    else:
                        proc.kill()
                    proc.wait()
                    if execution == "docker" and cidfile.exists():
                        cid = cidfile.read_text().strip()
                        subprocess.run(["docker", "rm", "-f", cid], capture_output=True, timeout=10)
                    return {"status": "timeout", "result": None, "detail": f"Exceeded {timeout}s"}
                out.seek(0)
                err.seek(0)
                stdout = out.read(2_000_001)
                stderr = err.read(4000).decode("utf-8", errors="replace")
                if proc.returncode != 0:
                    infra = execution == "docker" and proc.returncode in (125, 126, 127)
                    return {"status": "unavailable" if infra else "error", "result": None,
                            "detail": f"exit {proc.returncode}: {stderr}"}
                if len(stdout) > 2_000_000:
                    return {"status": "error", "result": None, "detail": "Output exceeds 2 MB"}
                data = json.loads(stdout, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
                detail = {"docker": "Executed in Docker", "container": "Executed as unprivileged child in external verifier container; grader directory inaccessible", "trusted": "Executed trusted repository code (not sandboxed)"}[execution]
                return {"status": "ok", "result": data, "detail": detail}
            except (OSError, ValueError) as exc:
                return {"status": "error", "result": None, "detail": f"{type(exc).__name__}: {exc}"}

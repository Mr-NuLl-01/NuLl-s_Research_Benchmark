#!/usr/bin/env python3
"""Inspect Harbor build separation, then probe a real offline candidate image.

This validates an offline Docker image with no agent or API calls. It does not
validate Harbor's live provider-host allowlist, provider tool restrictions, or
any raw host CLI boundary. Missing Docker is infrastructure-unavailable, never
an isolation pass.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nrb.adapters import export_harbor
from nrb.core import get_case
from nrb.provenance import evaluator_identity


class IsolationError(RuntimeError):
    pass


def check_build_context(task_dir):
    """Fail closed on extra COPY sources, grader/oracle files or symlinks."""
    task = Path(task_dir)
    environment = task / "environment"
    packet = environment / "packet"
    manifest_path = packet / "packet_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    allowed = {"Dockerfile", ".dockerignore", "packet/packet_manifest.json"}
    allowed.update("packet/" + name for name in manifest["files"])
    actual = set()
    allowed_directories = {"packet"}
    for name in allowed:
        allowed_directories.update(parent.as_posix() for parent in Path(name).parents if parent.as_posix() != ".")
    for path in environment.rglob("*"):
        if path.is_symlink():
            raise IsolationError("Candidate build context contains a symlink")
        relative = path.relative_to(environment).as_posix()
        if path.is_dir() and relative not in allowed_directories:
            raise IsolationError("Candidate build context contains an unexpected directory")
        if path.is_file():
            actual.add(relative)
    if actual != allowed:
        raise IsolationError("Candidate build context contains extra or missing files")
    dockerfile = (environment / "Dockerfile").read_text(encoding="utf-8")
    copies = [line.strip() for line in dockerfile.splitlines() if line.strip().upper().startswith(("COPY ", "ADD "))]
    if copies != ["COPY packet/ /app/"]:
        raise IsolationError("Only the candidate packet may be copied into the agent image")
    if any(word in dockerfile.lower() for word in ("/grader", "/solution", "docker.sock", "copy .", "mount=")):
        raise IsolationError("Candidate Dockerfile references evaluator content or a host mount")
    expected_ignore = "*\n!Dockerfile\n!packet/\n!packet/**\n"
    if (environment / ".dockerignore").read_text(encoding="utf-8") != expected_ignore:
        raise IsolationError("Candidate build .dockerignore must whitelist only packet content")
    if (task / "solution").exists():
        raise IsolationError("The isolation export must not contain an oracle solution")
    expected_files = dict(manifest["files"])
    expected_files["packet_manifest.json"] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    for name, digest in expected_files.items():
        path = packet / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise IsolationError("Candidate packet differs from its frozen manifest")
    return {"passed": True, "only_packet_copied": True, "oracle_excluded": True,
            "build_files": {name: hashlib.sha256((environment / name).read_bytes()).hexdigest() for name in sorted(actual)},
            "expected_candidate_files": expected_files}


def _run(argv, *, timeout, stdout_path=None, stderr_path=None):
    result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    if stdout_path is not None:
        Path(stdout_path).write_text(result.stdout, encoding="utf-8")
    if stderr_path is not None:
        Path(stderr_path).write_text(result.stderr, encoding="utf-8")
    return result


def run(output, *, python_image="python:3.12-slim", timeout=600):
    output = Path(output)
    materials = output.parent / (output.stem + "-materials")
    if output.exists() or output.is_symlink() or materials.exists() or materials.is_symlink():
        raise FileExistsError("Isolation report and material paths must be new")
    materials.mkdir(parents=True)
    exported = materials / "export"
    export_harbor([get_case("NRB01", 0)], exported, python_image=python_image, include_solution=False, agent_hosts=[])
    static = check_build_context(exported / "nrb01")
    report = {"schema_version": "nrb-candidate-isolation-v1", "kind": "offline_candidate_image_probe",
              "not_model_performance": True, "evaluator_identity": evaluator_identity(), "python_image": python_image,
              "scope": "Offline Docker candidate-image isolation only; no live API allowlist validation.",
              "api_provider_calls": 0, "static_build_context": static, "runtime_status": "unavailable", "passed": False,
              "materials": str(materials)}
    docker = shutil.which("docker")
    image = "nrb-isolation-probe-" + uuid.uuid4().hex
    container = None
    image_created = False
    try:
        if not docker:
            raise FileNotFoundError("Docker executable is not installed")
        info = _run([docker, "version", "--format", "{{json .}}"], timeout=30,
                    stdout_path=materials / "docker-version.json", stderr_path=materials / "docker-version-stderr.txt")
        if info.returncode:
            raise OSError("Docker daemon is unavailable; see docker-version-stderr.txt")
        build = _run([docker, "build", "--tag", image, str(exported / "nrb01" / "environment")], timeout=timeout,
                     stdout_path=materials / "build-stdout.txt", stderr_path=materials / "build-stderr.txt")
        if build.returncode:
            raise IsolationError("Candidate image build failed; see build logs")
        image_created = True
        image_info = _run([docker, "image", "inspect", image], timeout=30)
        if image_info.returncode:
            raise IsolationError("Could not inspect the actual candidate image")
        image_data = json.loads(image_info.stdout)[0]
        report["actual_image_id"] = image_data["Id"]
        report["actual_repo_digests"] = image_data.get("RepoDigests", [])
        (materials / "image-inspect.json").write_text(image_info.stdout, encoding="utf-8")
        probe = r'''
import hashlib,importlib.util,json,os,pathlib,socket,sys
expected=json.loads(sys.argv[1]); root=pathlib.Path('/app')
forbidden=['/grader','/solution','/tests','/app/nrb','/app/.git','/app/solution','/app/tests','/var/run/docker.sock','/run/docker.sock']
present=[p for p in forbidden if pathlib.Path(p).exists() or pathlib.Path(p).is_symlink()]
actual=sorted(str(p.relative_to(root)) for p in root.rglob('*') if p.is_file())
expected_names=sorted([*expected,'submission.json'])
unchanged=all((root/name).is_file() and not (root/name).is_symlink() and hashlib.sha256((root/name).read_bytes()).hexdigest()==digest for name,digest in expected.items())
interfaces=sorted(p.name for p in pathlib.Path('/sys/class/net').iterdir())
external_socket_blocked=False
try:
    with socket.create_connection(('198.51.100.1',443),timeout=1): pass
except OSError:
    external_socket_blocked=True
nrb_importable=importlib.util.find_spec('nrb') is not None
checks={'forbidden_paths_absent':not present,'nrb_not_importable':not nrb_importable,'only_candidate_files':actual==expected_names,'candidate_files_unchanged':unchanged,'blank_submission':(root/'submission.json').read_bytes()==b'','loopback_only':interfaces==['lo'],'external_socket_blocked':external_socket_blocked}
print(json.dumps({'checks':checks,'passed':all(checks.values()),'present_forbidden_paths':present,'candidate_files':actual,'network_interfaces':interfaces}))
'''
        create = _run([docker, "create", "--network", "none", "--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m",
                       "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--pids-limit", "64",
                       "--memory", "256m", "--cpus", "1", "--workdir", "/app", "--entrypoint", "python", image,
                       "-I", "-B", "-c", probe, json.dumps(static["expected_candidate_files"])], timeout=30)
        if create.returncode:
            raise IsolationError("Could not create the offline candidate probe container")
        container = create.stdout.strip()
        inspected = _run([docker, "inspect", container], timeout=30)
        if inspected.returncode:
            raise IsolationError("Could not inspect probe-container isolation settings")
        settings = json.loads(inspected.stdout)[0]
        host = settings["HostConfig"]
        mounts = settings.get("Mounts") or []
        has_host_mount = any(m.get("Type") != "tmpfs" or m.get("Destination") != "/tmp" or m.get("Source") not in (None, "") for m in mounts)
        if host.get("NetworkMode") != "none" or host.get("Privileged") or host.get("Binds") or has_host_mount:
            raise IsolationError("Probe has unexpected networking, privilege or host mounts")
        report["container_boundary"] = {"network_mode": host["NetworkMode"], "privileged": host["Privileged"],
                                         "host_bind_mounts": host.get("Binds"), "host_mounts": settings.get("Mounts")}
        executed = _run([docker, "start", "--attach", container], timeout=30,
                        stdout_path=materials / "probe-stdout.txt", stderr_path=materials / "probe-stderr.txt")
        if executed.returncode:
            raise IsolationError("Actual offline candidate probe failed to execute")
        result = json.loads(executed.stdout.strip())
        report.update(runtime_status="executed", runtime_probe=result, passed=result.get("passed") is True)
    except (FileNotFoundError, OSError) as exc:
        report.update(runtime_status="unavailable", error=str(exc))
    except (IsolationError, subprocess.SubprocessError, ValueError, KeyError) as exc:
        report.update(runtime_status="failed", error=str(exc))
    finally:
        if docker and container:
            _run([docker, "rm", "--force", container], timeout=30)
        if docker and image_created:
            _run([docker, "image", "rm", "--force", image], timeout=30)
    report["material_sha256"] = {str(p.relative_to(materials)): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in sorted(materials.rglob("*")) if p.is_file()}
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--python-image", default="python:3.12-slim")
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()
    report = run(args.out, python_image=args.python_image, timeout=args.timeout)
    print(json.dumps({"passed": report["passed"], "runtime_status": report["runtime_status"], "report": str(args.out)}))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

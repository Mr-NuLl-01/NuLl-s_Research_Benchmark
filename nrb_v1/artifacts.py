from __future__ import annotations
import base64
import json
from pathlib import Path, PurePosixPath
from .provenance import fingerprint

MAX_BYTES = 100 * 1024 * 1024


def safe_name(name):
    if not isinstance(name,str) or not name or "\\" in name or "\0" in name:
        raise ValueError("Unsafe artifact name")
    p=PurePosixPath(name)
    if p.is_absolute() or p.as_posix()!=name or name=="." or any(x in ("..", ".") for x in p.parts):
        raise ValueError("Unsafe artifact path")
    if name=="_driver_nrb.py": raise ValueError("Reserved evaluator driver filename")
    return p


def decode(value):
    if isinstance(value,str): return value.encode("utf-8")
    if isinstance(value,dict) and value.get("encoding")=="base64" and isinstance(value.get("data"),str):
        return base64.b64decode(value["data"],validate=True)
    raise ValueError("Artifact must be full UTF-8 text or {encoding:base64,data:...}")


def validate_submission(value, task_id=None):
    if not isinstance(value,dict) or not isinstance(value.get("artifacts"),dict):
        raise ValueError("Expected submission object with artifacts")
    if task_id is not None and value.get("task_id") != task_id:
        raise ValueError("Submission task_id mismatch")
    total=0
    names=set(value["artifacts"])
    for name, content in value["artifacts"].items():
        p=safe_name(name)
        if any(parent.as_posix() in names for parent in p.parents if parent.as_posix()!="."):
            raise ValueError("Artifact file/directory collision")
        total+=len(decode(content))
    if total>MAX_BYTES: raise ValueError("Artifact payload exceeds 100 MiB")
    try:
        json.dumps(value,allow_nan=False,ensure_ascii=False).encode("utf-8")
    except (ValueError,TypeError,OverflowError,RecursionError) as exc:
        raise ValueError("Submission must contain finite JSON values and valid UTF-8") from exc
    return value


def materialize(submission, dest):
    validate_submission(submission)
    dest=Path(dest)
    dest.mkdir(parents=True,exist_ok=False)
    manifest={}
    for name,value in submission["artifacts"].items():
        target=dest.joinpath(*safe_name(name).parts)
        target.parent.mkdir(parents=True,exist_ok=True)
        data=decode(value)
        target.write_bytes(data)
        manifest[name]={"sha256":fingerprint(data),"bytes":len(data)}
    return manifest


def pack(task_id, source):
    source=Path(source)
    if not source.is_dir() or source.is_symlink(): raise ValueError("Expected real artifact directory")
    artifacts={}
    for p in sorted(source.rglob("*")):
        if p.is_symlink(): raise ValueError("Symlink artifacts are not supported")
        if not p.is_file(): continue
        data=p.read_bytes()
        try: value=data.decode("utf-8")
        except UnicodeDecodeError: value={"encoding":"base64","data":base64.b64encode(data).decode("ascii")}
        artifacts[p.relative_to(source).as_posix()]=value
    return validate_submission({"task_id":task_id,"artifacts":artifacts,"answer":{}},task_id)


def parse_response(text, task_id):
    stripped=text.strip()
    if stripped.startswith("```"):
        stripped="\n".join(stripped.splitlines()[1:-1])
    value=json.loads(stripped)
    return validate_submission(value,task_id)

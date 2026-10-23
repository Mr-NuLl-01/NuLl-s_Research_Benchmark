#!/usr/bin/env python3
"""Build deterministic candidate/evaluator ZIPs for all twenty tasks, only in --out."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from nrb_v2 import __version__
from nrb_v2.grading import identity
from nrb_v2.packets import candidate, input_manifest
from nrb_v2.registry import ALL_IDS, MANUAL_IDS, OBJECTIVE_IDS, PYTHON_IDS, module, source_filename
from nrb_v2.subjective import blank_review, candidate_inputs

ZIP_DATE = (2026, 10, 23, 0, 0, 0)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def safe_relative(name: str) -> str:
    if not isinstance(name, str) or not name or "\\" in name or "\0" in name:
        raise ValueError("Unsafe package path: " + repr(name))
    path = PurePosixPath(name)
    if path.is_absolute() or path.as_posix() != name or name == "." or ".." in path.parts:
        raise ValueError("Unsafe package path: " + repr(name))
    return name


def source_bytes(relative: str) -> bytes:
    """Read an explicitly selected repository file, never an external symlink."""
    path = ROOT / safe_relative(relative)
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("Package source must be a regular repository file: " + relative)
    return path.read_bytes()


def archive(path: Path, name: str, files: dict[str, bytes], *, kind=None,
            task_id=None, mode=None, seed=None, details=None) -> dict:
    """The three-argument form remains compatible with package_phase1_delivery.py."""
    safe_relative(name)
    if "/" in name:
        raise ValueError("ZIP root must be one directory")
    if not files or "MANIFEST.json" in files:
        raise ValueError("A nonempty package is required; MANIFEST.json is reserved")
    for key, value in files.items():
        safe_relative(key)
        if not isinstance(value, bytes):
            raise TypeError("Package data must be bytes: " + key)
        if any(parent.as_posix() in files for parent in PurePosixPath(key).parents
               if parent.as_posix() != "."):
            raise ValueError("Package file/directory collision: " + key)
    metadata = {"kind": kind or name, "task_id": task_id, "mode": mode, "seed": seed}
    manifest = {"schema": "nrb-delivery-manifest-v2", "benchmark_version": __version__,
                **metadata, "zip_root": name,
                "files": [{"path": key, "bytes": len(value), "sha256": digest(value)}
                          for key, value in sorted(files.items())]}
    if details is not None:
        manifest["details"] = details
    payload = {**files, "MANIFEST.json": json_bytes(manifest)}
    path = Path(path)
    with path.open("xb") as stream:
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
            for relative, data in sorted(payload.items()):
                info = zipfile.ZipInfo(name + "/" + relative, date_time=ZIP_DATE)
                info.create_system = 3
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (0o100755 if relative.endswith((".sh", ".command")) else 0o100644) << 16
                output.writestr(info, data, compresslevel=9)
    with zipfile.ZipFile(path) as check:
        if check.testzip() is not None:
            raise ValueError("ZIP integrity check failed: " + str(path))
        for entry in manifest["files"]:
            actual = check.read(name + "/" + entry["path"])
            if len(actual) != entry["bytes"] or digest(actual) != entry["sha256"]:
                raise ValueError("ZIP content differs from its manifest: " + entry["path"])
    return {"name": path.name, "path": str(path.resolve()), **metadata, "zip_root": name,
            "bytes": path.stat().st_size, "sha256": digest(path.read_bytes()),
            "file_count": len(payload)}


def task_variants():
    """Twenty task identities, twenty-one separately deliverable conditions."""
    return [(tid, mode) for tid in ALL_IDS for mode in (("A", "B") if tid == "R06" else (None,))]


def candidate_bundle_files(task_id, mode=None, seed=17):
    if task_id not in ALL_IDS or (mode not in ("A", "B") if task_id == "R06" else mode is not None):
        raise ValueError("Unknown task or undeclared/unsupported mode")
    packet = candidate(task_id, seed)
    files = {task_id + ".md": packet["content"].encode("utf-8")}
    if task_id in MANUAL_IDS:
        for item in candidate_inputs(task_id, mode):
            # Replace the raw TASK.md with the canonical, versioned prompt.
            if item["source"] == f"tasks/v2.0/{task_id}.md":
                continue
            dest = safe_relative(item["path"])
            if dest in files:
                raise ValueError("Duplicate candidate filename: " + dest)
            files[dest] = source_bytes(item["source"])
    elif task_id == "L01":
        for name, content in module(task_id).candidate_files(seed).items():
            if name == task_id + ".md":
                continue
            safe_relative(name)
            if name in files:
                raise ValueError("Duplicate Lean candidate filename: " + name)
            files[name] = content.encode("utf-8") if isinstance(content, str) else content
    bound = input_manifest(task_id, seed, mode)
    actual = [{"path": name, "bytes": len(data), "sha256": digest(data)}
              for name, data in sorted(files.items())]
    if bound["files"] != actual:
        raise ValueError(f"{task_id}/{mode}: package inputs differ from packets.input_manifest")
    files["PACKET.json"] = json_bytes({"schema": "nrb-candidate-delivery-v2",
        "benchmark_version": __version__, "task_id": task_id, "mode": mode, "seed": seed,
        "packet_hash": packet["packet_hash"], "input_manifest_hash": bound["sha256"],
        "input_files": bound["files"]})
    condition = f"；模式 {mode}，另一模式的材料不能交给本次候选" if mode else ""
    files["README.txt"] = (
        f"NRB {__version__} · {task_id} · 种子 {seed}{condition}\n"
        f"在新会话中提供 {task_id}.md 和本目录随附的全部输入材料。\n"
        "这是一题的候选材料；评测者使用独立evaluator包。\n"
        "PACKET.json记录题面及输入身份，MANIFEST.json记录交付文件哈希。\n"
        "素材许可和出处保留在随附材料中。\n").encode("utf-8")
    return files


def collection_files(bundles, seed=17):
    files, index = {}, []
    for (tid, mode), bundle in bundles.items():
        folder = f"tasks/{tid}" + (f"/{mode}" if mode else "")
        for name, data in bundle.items():
            files[folder + "/" + name] = data
        packet = json.loads(bundle["PACKET.json"])
        index.append({"task_id": tid, "mode": mode, "directory": folder,
                      "prompt": folder + "/" + tid + ".md",
                      "packet_hash": packet["packet_hash"],
                      "input_manifest_hash": packet["input_manifest_hash"]})
    files["CATALOG.json"] = json_bytes({"benchmark_version": __version__, "seed": seed,
        "task_count": len(ALL_IDS), "condition_count": len(index), "tasks": index})
    files["README.txt"] = (
        f"NRB {__version__} · 全部20题候选材料 · 种子 {seed}\n\n"
        "本主包供评测者保存和分发。每次只把所选 tasks/<题号>/ 目录交给候选，使用新会话。\n"
        "R06计一道题：运行前选定A或B，只提供 tasks/R06/A/ 或 tasks/R06/B/ 其中一个目录。\n"
        "不能把整个主包交给候选；A候选不得接触B中的参考成片。\n"
        "PACKET.json和CATALOG.json标明题面、输入、种子和模式身份。评分器另见evaluator包。\n"
        "题数：8 Python + 3 Fortran + 1 Lean + 6科研主观题 + 2聊天题。\n").encode("utf-8")
    return files


def _tree_files(directory, suffixes=None):
    for path in sorted((ROOT / directory).rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.name == "_origin.json":
            continue
        if suffixes is None or path.suffix in suffixes:
            relative = path.relative_to(ROOT).as_posix()
            yield relative, source_bytes(relative)


def evaluator_files(seed=17):
    files = {}
    for directory in ("nrb_v1", "nrb_v2"):
        files.update(_tree_files(directory, {".py", ".json", ".lean"}))
    files.update(_tree_files("environments/v2"))
    release_dir = "release/" + __version__
    launchers = dict(_tree_files(release_dir))
    if not launchers:
        raise ValueError("Missing versioned release launchers: " + release_dir)
    files.update(launchers)
    for path, data in launchers.items():
        files[path.removeprefix(release_dir + "/")] = data
    for rel in ("LICENSE", "docs/v2.0/usage.zh-CN.md", "docs/v2.0/subjective-protocol.md",
                "docs/v2.0/package-format.md"):
        files[rel] = source_bytes(rel)
    for path in sorted((ROOT / "tasks/v2.0").glob("*.md")):
        rel = path.relative_to(ROOT).as_posix()
        files[rel] = source_bytes(rel)
    # Required for offline input_manifest/review identity; no recursive sources copy.
    for tid, mode in task_variants():
        if tid in MANUAL_IDS:
            for item in candidate_inputs(tid, mode):
                files[item["source"]] = source_bytes(item["source"])
    for tid in OBJECTIVE_IDS:
        filename = source_filename(tid)
        files[f"submissions/{tid}/PLACE-SUBMISSION-HERE.txt"] = (
            f"{tid}: copy your complete UTF-8 {filename} to submissions/{tid}/{filename}.\n"
            "The expected submission file is deliberately absent until you provide it.\n"
            "Do not copy this evaluator or its reference/control programs into a candidate session.\n"
        ).encode("utf-8")
    for tid in MANUAL_IDS:
        for mode in ("A", "B") if tid == "R06" else (None,):
            name = f"reviews/{tid}/" + (mode + "/" if mode else "") + "review.template.json"
            files[name] = json_bytes(blank_review(tid, mode))
    files["reviews/README.txt"] = (
        "7个人工评阅题，8份空模板（R06的A/B分别一份，题号仍只计一次）。\n"
        "复制所选模板为新的review.json，再填写评阅人、提交身份和逐项观察证据。\n"
        "未观察、未评阅保留unassessed/null；不要用空分或模板文件冒充实际成绩。\n"
        "运行 python -m nrb_v2 review review.json --out results/review-01.json。\n"
    ).encode("utf-8")
    files["RELEASE.json"] = json_bytes({"benchmark_version": __version__, "seed": seed,
        "task_ids": list(ALL_IDS), "objective_task_ids": list(OBJECTIVE_IDS),
        "manual_task_ids": list(MANUAL_IDS), "review_template_count": len(MANUAL_IDS) + 1,
        **identity()})
    files["README.md"] = f"""# NRB {__version__} · 本地验证与评阅

20题：13道自动评分，7道按观察证据评阅。这个包供评测者使用；模型接收对应的单题候选包。

## 评分

1. 把实际提交放入 `submissions/<题号>/`，文件名见目录内说明：Python为`solution.py`、Fortran为`solution.f90`、Lean为`proofs.json`、H02为`answer.json`。
2. 程序题首次使用运行 `Build-Environment` 脚本构建固定Docker环境；第一次构建需要网络，候选执行时断网。
3. 运行 `Grade-Results` 脚本，打开新的`results/`目录内`index.html`。未提交或环境不可用保留空分。

Windows使用`.cmd`，macOS使用`.command`，Linux使用`sh Build-Environment.sh`和`sh Grade-Results.sh`。宿主需要Python 3.11或更高版本。H02只校验JSON数字，不执行候选代码，可离线使用而无需Docker：

```bash
python -m nrb_v2 grade --task H02 --source submissions/H02/answer.json --out results/H02-01.json
```

主观任务使用`reviews/<题号>/review.template.json`；R06先选A/B，用对应子目录。实际观察后填写证据，再执行：

```bash
python -m nrb_v2 review review.json --out results/review-01.json
```

模板尚未观察时不会得到数值总分。七道人工题的协议见`docs/v2.0/subjective-protocol.md`。完整使用说明见`docs/v2.0/usage.zh-CN.md`。

## 文件与身份

包内保留评分模块、固定环境、版本启动脚本、静态题面，以及输入清单所需的授权材料；材料沿原路径保存，使离线题面/输入哈希和评阅模板可核验。`MANIFEST.json`列出文件SHA-256，`RELEASE.json`记录评分器身份。普通JSON/哈希是完整性记录，不是执行认证签名。

保留原始提交与每次报告；重复运行选择新文件名。本包没有模型成绩，参考程序和故意错误控制仅用于验证评分实现。
""".encode("utf-8")
    return files


def historical_files():
    files = {}
    for folder in ("tasks/v1.0", "tasks/v1.1"):
        for path in sorted((ROOT / folder).glob("*")):
            if path.is_file() and path.suffix in (".md", ".html", ".json"):
                rel = path.relative_to(ROOT).as_posix()
                files[rel] = source_bytes(rel)
    files["LICENSE"] = source_bytes("LICENSE")
    files["README.txt"] = (
        "Historical V1.0/V1.1 candidate packets. Do not compare V1 scores with V2.\n"
        "X04/X05 instruction files require their existing separate Drive media packages.\n"
        "Existing external links and original media are not changed by this packaging command.\n"
    ).encode("utf-8")
    return files


def build_release(out: Path, *, seed=17, include_historical=False, include_python_compat=False):
    if type(seed) is not int or not 0 <= seed < 2**32:
        raise ValueError("Seed must be an integer in [0, 2**32)")
    out = Path(out).resolve()
    prefix = "NRB-v" + __version__
    variants = task_variants()
    filenames = [f"{prefix}-{tid}" + (f"-{mode}" if mode else "") + "-candidate.zip"
                 for tid, mode in variants]
    filenames += [prefix + "-all-candidates.zip", prefix + "-evaluator.zip", "package-manifest.json"]
    if include_historical:
        filenames.append("NRB-v1.1-historical-candidates.zip")
    if include_python_compat:
        filenames += [prefix + "-python-candidates.zip", prefix + "-python-grader.zip"]
    collisions = [name for name in filenames if (out / name).exists() or (out / name).is_symlink()]
    if collisions:
        raise FileExistsError("Choose a new --out directory; existing delivery files: " + ", ".join(collisions))
    # Check all selected files and input identities before creating any ZIP.
    bundles = {(tid, mode): candidate_bundle_files(tid, mode, seed) for tid, mode in variants}
    evaluator = evaluator_files(seed)
    out.mkdir(parents=True, exist_ok=True)
    artifacts = []
    for (tid, mode), files in bundles.items():
        name = f"{prefix}-{tid}" + (f"-{mode}" if mode else "") + "-candidate"
        artifacts.append(archive(out / (name + ".zip"), name, files,
                                 kind="candidate", task_id=tid, mode=mode, seed=seed))
    name = prefix + "-all-candidates"
    artifacts.append(archive(out / (name + ".zip"), name, collection_files(bundles, seed),
                             kind="candidate_collection", seed=seed,
                             details={"task_count": 20, "condition_count": 21}))
    name = prefix + "-evaluator"
    artifacts.append(archive(out / (name + ".zip"), name, evaluator, kind="evaluator", seed=seed,
                             details={"objective_task_count": 13, "manual_task_count": 7,
                                      "review_template_count": 8}))
    if include_historical:
        name = "NRB-v1.1-historical-candidates"
        artifacts.append(archive(out / (name + ".zip"), name, historical_files(), kind="historical_candidates"))
    if include_python_compat:
        name = prefix + "-python-candidates"
        files = {tid + ".md": bundles[(tid, None)][tid + ".md"] for tid in PYTHON_IDS}
        files["README.txt"] = b"Eight Python candidate prompts. Supply only the selected task in a new session.\n"
        artifacts.append(archive(out / (name + ".zip"), name, files, kind="python_candidates_compat", seed=seed))
        name = prefix + "-python-grader"
        artifacts.append(archive(out / (name + ".zip"), name, evaluator, kind="python_grader_compat", seed=seed,
                                 details={"compatibility_name": True, "contents": "full twenty-task evaluator"}))
    report = {"schema": "nrb-release-packages-v2", "benchmark_version": __version__, "seed": seed,
              "task_count": len(ALL_IDS), "single_candidate_package_count": len(variants),
              "objective_task_count": len(OBJECTIVE_IDS), "manual_task_count": len(MANUAL_IDS),
              "artifacts": artifacts}
    with (out / "package-manifest.json").open("xb") as stream:
        stream.write(json_bytes(report))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="New delivery directory; existing packages are never overwritten")
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--include-historical", action="store_true", help="Also build the V1 instruction archive")
    parser.add_argument("--include-python-compat", action="store_true", help="Also emit the old Python bundle filenames")
    args = parser.parse_args()
    result = build_release(args.out, seed=args.seed, include_historical=args.include_historical,
                           include_python_compat=args.include_python_compat)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

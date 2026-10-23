#!/usr/bin/env python3
"""Build reproducible, separate candidate and evaluator ZIPs for V2 phase one."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from nrb_v2 import __version__
from nrb_v2.grading import identity
from nrb_v2.packets import candidate
from nrb_v2.registry import PYTHON_IDS


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def archive(path: Path, name: str, files: dict[str, bytes]) -> dict:
    manifest = {"schema": "nrb-delivery-manifest-v2", "benchmark_version": __version__,
                "kind": name, "files": [{"path": key, "bytes": len(value), "sha256": digest(value)}
                                          for key, value in sorted(files.items())]}
    files = {**files, "MANIFEST.json": (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()}
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for relative, data in sorted(files.items()):
            info = zipfile.ZipInfo(name + "/" + relative, date_time=(2026, 10, 23, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100755 if relative.endswith((".sh", ".command")) else 0o100644) << 16
            output.writestr(info, data)
    with zipfile.ZipFile(path) as check:
        assert check.testzip() is None
        for entry in manifest["files"]:
            actual = check.read(name + "/" + entry["path"])
            assert len(actual) == entry["bytes"] and digest(actual) == entry["sha256"]
    return {"name": path.name, "path": str(path), "bytes": path.stat().st_size,
            "sha256": digest(path.read_bytes()), "file_count": len(files)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    prefix = "NRB-v" + __version__
    prompts = {tid + ".md": candidate(tid)["content"].encode("utf-8") for tid in PYTHON_IDS}
    prompts["README.txt"] = ("NRB Python 第一轮候选题包\n仅把所选单题md交给被测模型，使用新会话。\n"
                              "提交solution.py，说明和自测可选。八题纯自动评分。\n"
                              "不要将评分器、参考解、仓库源码一并交给候选。\n"
                              "版本 " + __version__ + "；默认题面种子17。\n").encode("utf-8")
    candidates = archive(out / (prefix + "-python-candidates.zip"), prefix + "-python-candidates", prompts)

    grader = {}
    for directory in ("nrb_v1", "nrb_v2"):
        for path in sorted((ROOT / directory).rglob("*")):
            if path.is_file() and path.suffix in (".py", ".json") and "__pycache__" not in path.parts and path.name != "_origin.json":
                grader[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    for path in (ROOT / "release" / __version__).iterdir():
        if path.is_file():
            grader[path.name] = path.read_bytes()
    for rel in ("LICENSE", "environments/v2/Dockerfile", "docs/v2.0/usage.zh-CN.md"):
        grader[rel] = (ROOT / rel).read_bytes()
    grader["README.md"] = (ROOT / "docs/v2.0/usage.zh-CN.md").read_bytes()
    grader["RELEASE.json"] = (json.dumps({"benchmark_version": __version__, **identity()}, ensure_ascii=False, indent=2) + "\n").encode()
    for tid in PYTHON_IDS:
        grader[f"tasks/{tid}.md"] = candidate(tid)["content"].encode("utf-8")
        grader[f"submissions/{tid}/PLACE-SOLUTION-HERE.txt"] = (
            f"Place the complete UTF-8 solution.py for {tid} here.\nNo report.md or manual review is required.\n").encode()
    evaluator = archive(out / (prefix + "-python-grader.zip"), prefix + "-python-grader", grader)

    # Historical, frozen candidates only. Existing large video media retain
    # their separately verified Drive links; no answer or author demo is added.
    legacy = {}
    for folder in ("tasks/v1.0", "tasks/v1.1"):
        for path in sorted((ROOT / folder).glob("*")):
            if path.is_file() and path.suffix in (".md", ".html", ".json"):
                legacy[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    legacy["LICENSE"] = (ROOT / "LICENSE").read_bytes()
    legacy["README.txt"] = ("Historical V1.0/V1.1 candidate packets. Do not compare V1 scores with V2.\n"
                            "X04/X05 instruction files require their separate Drive media packages.\n"
                            "Preserve third-party licenses embedded in the HTML and media packages.\n").encode()
    historical = archive(out / "NRB-v1.1-historical-candidates.zip", "NRB-v1.1-historical-candidates", legacy)
    report = {"benchmark_version": __version__, "artifacts": [candidates, evaluator, historical]}
    (out / "package-manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

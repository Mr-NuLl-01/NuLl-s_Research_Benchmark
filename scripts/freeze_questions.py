"""Regenerate the public seed-0 packets; run from the evaluator checkout.

This is a maintainer command. It refuses to overwrite a destination; move the
old questions tree aside only after reviewing task and scoring changes.
"""
from pathlib import Path
import argparse
import json

from nrb.core import build_suite, write_candidate_packet
from nrb import __version__


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", default="questions")
    args = parser.parse_args()
    dest = Path(args.dest)
    if dest.exists() or dest.is_symlink():
        raise FileExistsError("Choose a new destination; existing packets are never silently replaced")
    dest.mkdir(parents=True)
    cases = build_suite(0)
    manifests = [write_candidate_packet(c, dest / c["id"]) for c in cases]
    (dest / "suite_manifest.json").write_text(json.dumps({
        "benchmark_version": __version__, "seed": 0, "tasks": manifests,
        "purpose": "Public development packets; no answers included in this directory"
    }, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    rows = ["# 完整 10 题 · seed 0", "",
            "此目录提供可直接阅读的完整题面、合成输入及质量量表。每个 `instruction.md` 已内嵌全部文本输入；同目录还提供原始文件，便于工具读取。", "",
            "请只把单题目录或新导出的题包交给被测 agent。本仓库其余目录含评分器和参考答案，不能暴露给候选系统。正式比较建议生成新的种子变体；公开种子不构成无污染保证。", "",
            "| ID | 任务 | 必需交付物 |", "|---|---|---|"]
    rows += [f"| [{c['id']}]({c['id']}/instruction.md) | {c['title']} | {', '.join(c['required_artifacts'])} |" for c in cases]
    rows += ["", "每题自动 70 分，三项独立质量审阅各 10 分。答题协议和自动核验对象见题面；分数含义、缺失处理及质量审阅流程见 [评分方法](../docs/scoring.md)。", "",
             "```bash", "python -m nrb export --format native --seed 17 --dest exports/native-s17", "```", ""]
    (dest / "README.md").write_text("\n".join(rows), encoding="utf-8")
    print(json.dumps({"destination": str(dest), "task_count": len(cases), "seed": 0}))


if __name__ == "__main__":
    main()

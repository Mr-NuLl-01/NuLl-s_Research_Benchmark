#!/usr/bin/env python3
"""One-command, versioned batch grading; code uses Docker and H02 verifies strict JSON."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import html
import json
from pathlib import Path
import subprocess
import sys


def write_html(folder: Path, summary: dict) -> None:
    escape = lambda value: html.escape(str(value))
    rows, details = [], []
    labels = {"passed": "全部通过", "failed": "检查失败", "unscored": "未评分 / 环境不可用",
              "not_submitted": "未提交", "submission_invalid": "提交文件不合法", "infrastructure_unscored": "环境不可用"}
    for entry in summary.get("entries", []):
        task = entry["task_id"]
        score = "—" if entry.get("score") is None else f'{entry["score"]:.2f}'
        file_name = entry.get("report_file")
        link = f'<a href="{escape(file_name)}">JSON报告</a>' if file_name else "—"
        rows.append(f'<tr><td><a href="#{escape(task)}">{escape(task)}</a></td><td>{escape(labels.get(entry["status"],entry["status"]))}</td><td>{score}</td><td>{link}</td></tr>')
        if entry.get("error"):
            details.append(f'<section id="{escape(task)}"><h2>{escape(task)} · 提交文件不合法</h2><p>{escape(entry["error"])}</p><p>修复后重新运行；本次没有评分。</p></section>')
        if file_name:
            report = json.loads((folder / file_name).read_text(encoding="utf-8"))
            checks = "".join(f'<tr><td>{escape(c["id"])}</td><td>{escape(c["tier"])}</td><td>{escape(c["weight"])}</td><td>{"通过" if c["passed"] is True else "失败" if c["passed"] is False else "未执行"}</td><td>{escape(c.get("detail", ""))}</td></tr>' for c in report.get("checks", []))
            error = report.get("execution", {}).get("error", "")
            details.append(f'<section id="{escape(task)}"><h2>{escape(task)} · {score} / 100</h2><p>{escape(error or "逐项检查如下。未执行保持空分。")}</p><div class="scroll"><table><thead><tr><th>检查</th><th>组</th><th>原权重</th><th>状态</th><th>说明</th></tr></thead><tbody>{checks}</tbody></table></div><p><a href="#top">返回汇总</a></p></section>')
    cov = summary.get("coverage", {})
    avg = summary.get("mean_score")
    mean = "十三道自动题未全部评分，不给完整均分" if avg is None else f"完整十三道自动题均分 {avg:.2f} / 100"
    subset = summary.get("subset_mean")
    subset_note = "尚无有效分数" if subset is None else f"已评分子集均分 {subset:.2f} / 100（覆盖 {cov.get('scored',0)} / 13）"
    title = "NRB 2.0 · 自动评分结果"
    document = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>
<style>body{{margin:auto;max-width:1100px;padding:40px 24px;font:16px/1.7 system-ui,sans-serif;background:#f6f7f9;color:#172d3b}}h1,h2{{line-height:1.3}}section{{background:white;padding:24px;margin-top:30px;border:1px solid #d8e1e5;border-radius:12px}}table{{width:100%;border-collapse:collapse;background:white}}td,th{{border-bottom:1px solid #dce2e5;padding:12px;text-align:left}}a{{color:#256a68}}.scroll{{overflow:auto}}.note{{padding:16px;background:#e6efee;border-left:4px solid #256a68}}code{{overflow-wrap:anywhere}}</style></head><body id="top">
<h1>{title}</h1><p>版本 {escape(summary.get("benchmark_version"))} · 种子 {escape(summary.get("seed"))} · {escape(summary.get("created_at"))}</p>
<p>已提交 {cov.get("submitted",0)} / 13 · 已评分 {cov.get("scored",0)} / 13 · 全通过 {cov.get("passed",0)} / 13</p><h2>{mean}</h2><p>{subset_note}</p>
<div class="note">这些是本地验证器产生的报告。把单题 JSON 导入私有网页即可保存模型记录。若 Docker 尚未运行，请先启动它并运行 Build-Environment，然后重新评分；环境缺失不是模型零分。</div>
<table><thead><tr><th>题目</th><th>状态</th><th>分数</th><th>导入网页</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
{''.join(details)}<p>结果目录：<code>{escape(folder)}</code></p><p>作者参考/错误控制不属于模型成绩。普通报告不是数字签名。</p></body></html>'''
    (folder / "index.html").write_text(document, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("submissions"))
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--seed", type=int, default=17, choices=[0, 17, 2026])
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    try:
        import numpy
        if numpy.__version__ != "2.3.5":
            raise ImportError("NumPy 2.3.5 is required")
    except ImportError:
        print("Run Build-Environment once, then use Grade-Results. The evaluator needs NumPy 2.3.5.", file=sys.stderr)
        return 2
    out = args.out_dir or Path("results") / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S-%fZ")
    if not out.is_absolute():
        out = root / out
    source = args.input if args.input.is_absolute() else root / args.input
    if out.exists():
        print("Output directory exists. Choose a new run directory; old attempts will not be overwritten.", file=sys.stderr)
        return 2
    argv = [sys.executable, "-m", "nrb_v2", "batch", "--input", str(source), "--out-dir", str(out),
            "--execution", "docker", "--seed", str(args.seed)]
    proc = subprocess.run(argv, cwd=root, check=False)
    summary_file = out / "summary.json"
    if summary_file.exists():
        summary = json.loads(summary_file.read_text(encoding="utf-8"))
        write_html(out, summary)
        print("\nOpen results: " + str(out / "index.html"))
        print("Import the per-task .json files into the private Benchmark website.")
    else:
        print("No score report was produced. Read the error above; no model score has been assigned.", file=sys.stderr)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())

"""Build candidate-only, single-file tasks. This module never calls an oracle."""
from __future__ import annotations
import html
import json
from pathlib import Path
from . import __version__
from .registry import CODING_IDS, ids, module, spec, rubric
from .provenance import fingerprint, identity

SUBMISSION_CONTRACT = '''
## 统一交付与本轮边界

本文件是完整候选任务。仅使用文件内材料、已安装的授权工具及一般知识；无需联网。
不要访问benchmark仓库、评分器、参考答案、历史提交或其他会话。不要修改原始输入。
每题使用新会话，不能把开发/审阅本题的上下文用于正式作答。工具、推理、skills、子agent和预算由评测者事先固定。

编程任务请交付一个UTF-8 `submission.json`，示例只说明格式，不含本题答案：
```json
{"task_id":"TASK_ID","artifacts":{"solution.py":"完整源代码文本","report.md":"完整科学说明","tests.py":"完整独立测试代码"},"answer":{}}
```
Fortran任务将 `solution.py` 换为题目指定的 `main.f90`。所有必需交付以本题列表为准。
只给文件名/路径、伪代码或承诺不等于交付；代码应与题目接口一致。报告说明假设、实际运行、未完成部分与运行命令。
允许编程工具的轨道应实际执行并修复；无工具轨道仍可提交源代码，但不得冒称已经运行。
评测者在另一环境实际编译/运行，按公开合同派生的新输入核验；代码必须解输入问题，不能只写死可见案例。

每道编程题自动70分：基础20、科学正确性30、压力/边界20；独立质量30分。
全部分数照常保留，核心科学/交付责任失败时不能靠其他分数补过。缺环境或尚未审阅保留未评。
公开量表0、2、4是锚点，允许1、3中间等级；质量项实际分=该项权重×等级/4。
建议至少保留12位有效数字，避免输出舍入损失；某字段更具体的精度约定优先。
'''


def candidate(task_id, seed=17):
    task = spec(task_id)
    if task_id in CODING_IDS:
        header = f"# NRB V{__version__} · {task_id} · {task['title']}\n\n"
        header += f"任务种子：{seed}。设计难度：{task['difficulty']}/5（待真实模型校准）。\n\n"
        text = header + module(task_id).prompt(seed) + SUBMISSION_CONTRACT.replace("TASK_ID", task_id)
        text += "\n## 核心完成责任\n\n" + "\n".join("- " + e["requirement"] for e in task["essential"])
        text += "\n\n## 质量评分表（30分）\n\n|维度|权重|0级|2级|4级|\n|---|---:|---|---|---|\n"
        for item in rubric(task_id):
            text += f"|{item['name']}|{item['weight']}|{item['anchors']['0']}|{item['anchors']['2']}|{item['anchors']['4']}|\n"
        return {"task_id":task_id,"seed":seed,"format":"md","content":text,"packet_hash":fingerprint(text.encode())}
    text = task["content"]
    return {"task_id":task_id,"seed":seed,"format":task.get("format","html"),"content":text,
            "packet_hash":fingerprint(text.encode())}


def public_metadata(task_id, seed=17):
    task, packet = spec(task_id), candidate(task_id, seed)
    return {"id":task_id,"title":task["title"],"track":task["track"],"difficulty":task["difficulty"],
            "difficulty_status":"design_prior_not_empirically_calibrated", "capabilities":task.get("capabilities",[]),
            "language":task.get("language"),"modality":task.get("modality",["text","code"]),
            "time_budget_s":task.get("time_budget_s"),"required_artifacts":task["required_artifacts"],
            "seed":seed,"packet_hash":packet["packet_hash"],"file":task_id+"."+packet["format"]}


def freeze(dest, selection="all", seed=17, replace=False):
    dest = Path(dest)
    if dest.exists() and not replace:
        raise FileExistsError("Use a new candidate directory: " + str(dest))
    dest.mkdir(parents=True, exist_ok=replace)
    selected = ids(selection)
    entries = []
    for task_id in selected:
        packet = candidate(task_id, seed)
        path = dest / (task_id + "." + packet["format"])
        path.write_text(packet["content"], encoding="utf-8")
        entries.append(public_metadata(task_id, seed))
    manifest = {"benchmark_version":__version__,"kind":"candidate_only_catalog","seed":seed,
                "tasks":entries,"note":"Only one task file is needed by each candidate; do not provide evaluator files."}
    (dest / "catalog.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    lines=["# V1.0 候选题包\n", "每题一个自包含文件。下载单题文件交给AI；不需要克隆仓库或让候选联网。\n",
           "代码题10道；科研题6道；可选扩展3道。设计难度为先验，尚未通过真实模型标定。\n",
           "|题号|任务|轨道|设计难度|单文件|\n|---|---|---|---:|---|\n"]
    for e in entries:
        lines.append(f"|{e['id']}|{e['title']}|{e['track']}|{e['difficulty']}/5|[{e['file']}]({e['file']})|\n")
    lines.append("\nHTML包含内嵌文献/图像。请下载后打开；只把GitHub预览截图交给候选会丢失材料。文字harness应传完整正文，并按多模态协议提供内嵌图像；无法看图需另列轨道。\n")
    (dest / "README.md").write_text("\n".join(lines),encoding="utf-8")
    return manifest

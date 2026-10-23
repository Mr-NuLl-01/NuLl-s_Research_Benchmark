"""Self-contained candidate packets. No reference solution or grader is exported."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
import re

from nrb_v1.provenance import fingerprint
from . import __version__
from .registry import ALL_IDS, MANUAL_IDS, OBJECTIVE_IDS, PYTHON_IDS, LEGACY, ids, module, spec

_TOLERANCES = {
    "P01": "浮点字段使用 |actual-expected| ≤ 1e-110 + 2e-11·|expected|；计数是精确整数。极小标准误差不能用常见默认绝对容差吞掉。",
    "P02": "浮点字段使用 |actual-expected| ≤ 1e-12 + 2e-12·|expected|；zero/uint32案例相对项为1e-12。组数是精确整数；随机流、排序和分位数规则是合同的一部分。",
    "P03": "浮点字段使用 |actual-expected| ≤ 2e-7 + 2e-9·|expected|。能量由约定的离散推进与边界通量计算，不用连续体解替代离散目标。",
    "P04": "复振幅的实部/虚部与R/T/A字段使用 |actual-expected| ≤ 2e-11 + 2e-9·|expected|。允许任何符合题面边界关系且数值稳定的组合算法。",
    "P05": "状态字段使用 |actual-expected| ≤ 2e-11 + 2e-9·|expected|；accepted_steps/rejected_steps必须是规定算法产生的精确整数。此题检验已公开的算法合同，不把其他正确ODE算法当作相同提交。",
    "P06": "浮点字段使用 |actual-expected| ≤ 2e-7 + 3e-6·|expected|；identifiable/clipped是布尔值。平坦代表点、绝对sigma和剖面阈值定义优先。",
    "P07": "浮点字段使用 |actual-expected| ≤ 4e-7 + 3e-7·|expected|。另外，评分器从返回的u独立重建题设有限体积方程；最大密度残差必须≤4e-7 W/m³。返回的residual_inf应与该重算值符合上述容差，四侧通量和全局收支也独立核对；不能仅把residual_inf写成0。",
    "P08": "浮点字段使用 |actual-expected| ≤ 2e-9 + 3e-5·|expected|；n/step/rng_state是精确整数，状态和重启字段按合同检查。restart_equal只要求本实现的同算法JSON往返一致，不要求跨不同实现逐位一致。",
}


def objective_prompt(task_id, seed=17):
    if type(seed) is not int or not 0 <= seed < 2**32:
        raise ValueError("Seed must be an integer in [0, 2**32)")
    task = spec(task_id)
    if task_id not in PYTHON_IDS:
        return f"NRB {__version__} · 题面种子 {seed}\n\n" + module(task_id).prompt(seed)
    text = module(task_id).prompt(seed).replace(LEGACY[task_id], task_id)
    # Replace the entire old common submission paragraph, preserving the science,
    # visible JSON input, and complete buggy starting programs.
    text = re.sub(r"\n## 提交与运行\n.*?(?=\n## 可见示例输入)", "\n", text, flags=re.S)
    text = text.replace("，另交report.md和tests.py", "")
    text = text.replace("、report.md和tests.py", "")
    text = text.replace("，并交report.md、tests.py", "")
    text = text.replace("自动70分/人工30分。", "")
    text = text.replace("自动70/人工30；", "")
    text = text.replace("自动70/人工30。", "")
    text = text.replace("报告需", "可选说明建议").replace("报告应", "可选说明建议")
    text = text.replace("报告至少", "可选说明可").replace("报告解释", "可选说明可解释")
    text = text.replace("但要在report.md逐类说明缺陷", "可在可选说明中逐类解释缺陷")
    text = text.replace("候选需在报告说明", "候选可在可选说明中说明")
    text = text.replace("report.md推导", "可选report.md可推导")
    text = text.replace("tests.py至少", "可选tests.py可")
    text = text.replace("report.md解释", "可选说明可解释")
    text = text.replace("report.md列出", "可选说明可列出")
    text = text.replace("tests.py应包括", "可选自测建议包括")
    text = text.replace("tests.py必须有", "可选自测建议包含")
    # V2 evaluates scientific behavior with the same pinned runtime for all
    # eight tasks. Library choice is not an unobservable manual-score gate.
    text = text.replace("实现Python标准库单文件", "实现Python单文件")
    text = text.replace("无网络、外部数据及第三方包。", "无网络、外部数据。")
    text = text.replace("提交标准库solution.py", "提交solution.py")
    text = text.replace("无第三方库、网络或外部数据。", "无网络或外部数据。")
    text = text.replace("只用Python标准库，离线、无外部数据。", "离线、无外部数据。")
    # Keep the task-specific human-readable interpretation after old tier labels.
    text = re.sub(r"分层：basic20，scientific30，stress20。", "", text)
    text = text.replace("basic20（", "基础检查（").replace("scientific30（", "科学检查（").replace("stress20（", "边界检查（")
    text = (f"NRB {__version__} · Python · 题面种子 {seed}\n"
            f"设计难度 {task['difficulty']}/5；尚未经过真实模型实测标定。\n\n" + text.rstrip())
    dependencies = "可用Python标准库、NumPy 2.3.5、SciPy 1.17.0；不需额外安装。"
    text += f"""

## 统一提交与自动评分

只需提交一个完整的 `solution.py`，公开 `solve(problem)`。题面中的方法解释、`report.md`、`tests.py`建议均为可选自检，没有人工分，也不阻止程序完成评分。候选只接收本题文件和本题允许的输入材料；不访问参考解、评分器源码、其他题目或旧作答。

离线环境为Python 3.12，{dependencies} `solution.py`顶层不得读取stdin、联网或执行测试；评分器导入后逐例调用solve。不得修改传入对象。返回值须可序列化为严格JSON，数值有限，不含NaN/Infinity；异常输入按题设抛ValueError，不用返回错误字符串代替。输出保留至少12位有效数字。

满分100，**全部来自实际程序检查**。基础/科学/边界检查的相对权重为20/30/20，统一按 `100 × 已通过权重 / 70` 换算。没有人工30分或手工确认步骤。全部检查通过标passed；部分通过保留部分分及逐项失败原因。执行环境不可用标unscored，分数为null，不作0分。

数值判据：{_TOLERANCES[task_id]}

自动成绩仅描述本题接口和既定科学/数值合同的通过情况。候选自述“已通过”不能替代验证；参考程序与故意错误程序的控制验证不计为模型成绩。
"""
    return text


def candidate(task_id, seed=17):
    if type(seed) is not int or not 0 <= seed < 2**32:
        raise ValueError("Seed must be an integer in [0, 2**32)")
    if task_id in OBJECTIVE_IDS:
        content = objective_prompt(task_id, seed)
    else:
        if task_id not in ALL_IDS: raise ValueError("Unknown task")
        content = f"NRB {__version__} · 题面种子 {seed}\n\n" + (Path(__file__).resolve().parents[1] / "tasks/v2.0" / (task_id + ".md")).read_text(encoding="utf-8")
    return {"task_id": task_id, "benchmark_version": __version__, "seed": seed,
            "format": "md", "content": content, "packet_hash": fingerprint(content.encode("utf-8"))}


@lru_cache(maxsize=128)
def input_manifest(task_id, seed=17, mode=None):
    """Bind the complete candidate input, including actual source media bytes.

    This is separate from packet_hash (the prompt text). Candidate archives use
    the same allowlists; evaluator packages carry their required source inputs.
    """
    content = candidate(task_id, seed)["content"].encode("utf-8")
    files = {task_id + ".md": content}
    root = Path(__file__).resolve().parents[1]
    if task_id in MANUAL_IDS:
        from .subjective import candidate_inputs
        for item in candidate_inputs(task_id, mode):
            if item["source"] == "tasks/v2.0/" + task_id + ".md":
                continue
            files[item["path"]] = (root / item["source"]).read_bytes()
    elif task_id == "L01":
        for name, value in module(task_id).candidate_files(seed).items():
            if name != task_id + ".md":
                files[name] = value.encode("utf-8") if isinstance(value, str) else value
    elif mode is not None:
        raise ValueError("This task has no modes")
    manifest = [{"path": name, "bytes": len(data), "sha256": fingerprint(data)}
                for name, data in sorted(files.items())]
    return {"files": manifest, "sha256": fingerprint(manifest)}


def catalog(seed=17):
    tasks = []
    for task_id in ids("all"):
        entry = spec(task_id)
        if task_id in ALL_IDS:
            packet = candidate(task_id, seed)
            entry.update(file=task_id + ".md", packet_hash=packet["packet_hash"], seed=seed)
        tasks.append(entry)
    return {"benchmark_version": __version__, "status": "complete", "ready_count": 20,
            "planned_count": 0, "total_count": 20, "tasks": tasks}


def export_tasks(destination, selection="all", seed=17):
    dest = Path(destination)
    dest.mkdir(parents=True, exist_ok=True)
    selected = ids(selection)
    entries = []
    for task_id in selected:
        packet = candidate(task_id, seed)
        path = dest / (task_id + ".md")
        if path.exists():
            raise FileExistsError("Refusing to overwrite an existing packet: " + str(path))
        path.write_text(packet["content"], encoding="utf-8")
        entries.append({"task_id": task_id, "file": path.name, "seed": seed, "sha256": packet["packet_hash"]})
    result = {"benchmark_version": __version__, "kind": "candidate_only", "tasks": entries}
    (dest / "manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (dest / "catalog.json").write_text(json.dumps(catalog(seed), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


generate = export_tasks

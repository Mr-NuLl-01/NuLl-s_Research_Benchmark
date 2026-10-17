from __future__ import annotations
import importlib
from .provenance import fingerprint

CODING_IDS = tuple(f"C{i:02d}" for i in range(1, 11))
RESEARCH_IDS = tuple(f"R{i:02d}" for i in range(1, 7))
OPTIONAL_IDS = tuple(f"X{i:02d}" for i in range(1, 4))


def module(task_id):
    if task_id not in CODING_IDS:
        raise ValueError("Not a coding task: " + task_id)
    return importlib.import_module("nrb_v1.tasks." + task_id.lower())


def research_tasks():
    mod = importlib.import_module("nrb_v1.research")
    return mod.tasks() if hasattr(mod, "tasks") else mod.TASKS


def spec(task_id):
    if task_id in CODING_IDS:
        return dict(module(task_id).TASK, track="coding", format="md")
    for task in research_tasks():
        if task["id"] == task_id:
            return task
    raise ValueError("Unknown task: " + task_id)


def ids(selection="required"):
    if selection == "coding": return list(CODING_IDS)
    if selection == "research": return list(RESEARCH_IDS)
    if selection == "optional": return list(OPTIONAL_IDS)
    if selection == "required": return [*CODING_IDS, *RESEARCH_IDS]
    if selection == "all": return [*CODING_IDS, *RESEARCH_IDS, *OPTIONAL_IDS]
    selected = selection.split(",")
    known = {*CODING_IDS, *RESEARCH_IDS, *OPTIONAL_IDS}
    if not selected or len(set(selected)) != len(selected) or any(t not in known for t in selected):
        raise ValueError("Unknown or duplicated task selection")
    return selected


def coding_rubric():
    return [
        {"id": "scientific_reasoning", "name": "科学解释与验证范围", "weight": 10,
         "anchors": {"0": "主要解释错误或缺失", "2": "主要结论正确，但假设/误差范围有缺口", "4": "假设、守恒、误差及适用范围准确且证据可复查"}},
        {"id": "verification", "name": "独立测试与复现", "weight": 10,
         "anchors": {"0": "无有效测试或虚构运行", "2": "有有效正常案例，缺关键边界/独立基准", "4": "独立解析/制造解/不变量与错误控制充分，运行记录真实"}},
        {"id": "engineering", "name": "实现与交接质量", "weight": 10,
         "anchors": {"0": "无法使用或接口混乱", "2": "可运行，组织与异常说明有缺陷", "4": "接口明确、可维护、依赖与运行方式清楚，无多余复杂化"}}
    ]


def rubric(task_id):
    return coding_rubric() if task_id in CODING_IDS else spec(task_id)["rubric"]


def validate_cases(task_id, cases):
    if not cases or len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Cases empty or duplicated")
    tiers = {k: 0.0 for k in ("basic", "scientific", "stress")}
    for case in cases:
        if case["tier"] not in tiers or case["weight"] <= 0:
            raise ValueError("Invalid tier or case weight")
        if "input" not in case or ("expected" not in case and "error" not in case):
            raise ValueError("Missing case contract")
        tiers[case["tier"]] += case["weight"]
    if any(abs(tiers[k] - v) > 1e-9 for k, v in {"basic":20,"scientific":30,"stress":20}.items()):
        raise ValueError(f"{task_id}: tier weights do not equal 20/30/20: {tiers}")
    return cases

"""Single catalog for the complete twenty-task benchmark."""
from __future__ import annotations

import importlib
from . import __version__

PYTHON_IDS = tuple(f"P{i:02d}" for i in range(1, 9))
FORTRAN_IDS = ("F01", "F02", "F03")
CODING_IDS = (*PYTHON_IDS, *FORTRAN_IDS, "L01")
OBJECTIVE_IDS = (*CODING_IDS, "H02")
MANUAL_IDS = (*(f"R{i:02d}" for i in range(1, 7)), "H01")
PLANNED_IDS = ()
ROUND2_IDS = ("F01", "F02", "F03", "L01", *(f"R{i:02d}" for i in range(1, 7)), "H01", "H02")
ALL_IDS = (*PYTHON_IDS, *ROUND2_IDS)
LEGACY = dict(zip(PYTHON_IDS, ("C01", "C02", "C03", "C04", "C05", "C07", "C08", "C10")))

_PLANS = [
    ("F01", "Fortran 非均匀网格守恒漂移扩散", "Fortran", 3, "SG通量、非均匀控制体与漂移方向", "automatic", "C06"),
    ("F02", "Fortran 隐式反应扩散与源汇账本", "Fortran", 4, "时间推进、正性与源汇守恒", "automatic", None),
    ("F03", "Fortran 自洽漂移扩散–Poisson", "Fortran", 5, "非线性耦合、阻尼迭代与规范平移", "automatic", "C09"),
    ("L01", "已有守恒结论的 Lean 形式化", "Lean", 4, "给定命题与条件、实际编译、公理依赖核验", "automatic", None),
    ("R01", "参考学习与可编辑科研 SVG", "主观科研", 4, "真实图例学习、科学语义与多面板组织", "manual", "R01"),
    ("R02", "小差异、宽动态范围与删失数据绘图", "主观科研", 4, "坐标尺度、数据语义与可复现图形", "manual", "R02"),
    ("R03", "保持事实与证据强度的英文润色", "主观科研", 3, "保守修改、事实台账与自然表达", "manual", "R03"),
    ("R04", "从图版与数据撰写结果和讨论", "主观科研", 4, "读图、定量表述与推断边界", "manual", "R04"),
    ("R05", "文献证据综合与有界方法复现", "主观科研", 5, "合并旧精读/综述题，保留证据与复现责任", "manual", "R05+R06"),
    ("R06", "视频修改与参考视觉重建", "主观科研", 4, "合并视频A/B为一道题的两种预先声明模式", "manual", "X04+X05"),
    ("H01", "聊天端单 HTML 科研工作台", "聊天端", 4, "离线交互、返回、空态与真实导出", "manual", "X01"),
    ("H02", "聊天端有回流网络的定量推理", "聊天端", 5, "产额、条件寿命、全局最优与可核验反例", "automatic", None),
]

_BRIEFS = {
    "P01": "CSV身份、单位与极小不确定度；区分重复记录和独立测量。",
    "P02": "独立组与技术重复、分层目标人群和确定性bootstrap。",
    "P03": "修复非均匀有限体积导热：界面热阻、隐式推进与能量账本。",
    "P04": "复折射率多层光学：s/p偏振、能流、倏逝波与极厚吸收层。",
    "P05": "按明确算法实现刚性积分：拒步回滚、右连续源与浮点硬停点。",
    "P06": "变量投影、绝对sigma、剖面似然区间和端点附近内部最小值。",
    "P07": "二维非均匀网格、方向各向异性、界面传递与边界积分通量。",
    "P08": "修复反应扩散反演链：离散切线、协方差、JSON重启与重新拟合自举。",
}


def module(task_id):
    if task_id in FORTRAN_IDS:
        return importlib.import_module("nrb_v2.tasks." + task_id.lower())
    if task_id == "L01":
        return importlib.import_module("nrb_v2.lean")
    if task_id == "H02":
        return importlib.import_module("nrb_v2.h02")
    if task_id not in PYTHON_IDS:
        raise ValueError(f"{task_id}: use the evidence-based review rubric")
    name = "nrb_v2.tasks.p06" if task_id == "P06" else "nrb_v1.tasks." + LEGACY[task_id].lower()
    return importlib.import_module(name)


def source_filename(task_id):
    if task_id in PYTHON_IDS: return "solution.py"
    if task_id in FORTRAN_IDS: return "solution.f90"
    if task_id == "L01": return "proofs.json"
    if task_id == "H02": return "answer.json"
    raise ValueError("This task requires an evidence-based review")


def spec(task_id):
    if task_id in PYTHON_IDS:
        item = dict(module(task_id).TASK)
        item.pop("essential", None)
        item.update(id=task_id, legacy_id=LEGACY[task_id], status="ready", category="Python",
                    track="python", scoring="automatic", max_score=100, required_artifacts=["solution.py"],
                    optional_artifacts=["report.md", "tests.py"], manual_review_required=False,
                    format="md", benchmark_version=__version__, brief=_BRIEFS[task_id],
                    difficulty_status="design_prior_not_empirically_calibrated")
        return item
    for tid, title, category, difficulty, brief, scoring, legacy in _PLANS:
        if tid == task_id:
            return dict(id=tid, title=title, category=category, difficulty=difficulty, brief=brief,
                        status="ready", phase=2, scoring=scoring, legacy_id=legacy,
                        language={"Fortran": "fortran", "Lean": "lean"}.get(category),
                        track={"Fortran":"fortran","Lean":"lean","主观科研":"research","聊天端":"chat"}[category], benchmark_version=__version__,
                        time_budget_s={"F01":1800,"F02":2700,"F03":3600,"L01":2400,"R01":3600,"R02":3600,"R03":1800,"R04":2400,"R05":7200,"R06":7200,"H01":2400,"H02":2400}[tid], max_score=100, format="md",
                        difficulty_status="design_prior_not_empirically_calibrated",
                        manual_review_required=scoring == "manual", required_artifacts=[source_filename(tid)] if scoring == "automatic" else ["见题面交付清单"])
    raise ValueError("Unknown task: " + str(task_id))


def ids(selection="all"):
    groups = {"all": ALL_IDS, "ready": ALL_IDS, "python": PYTHON_IDS,
              "coding": CODING_IDS, "objective": OBJECTIVE_IDS, "planned": PLANNED_IDS, "manual": MANUAL_IDS, "lean": ("L01",),
              "fortran": ("F01", "F02", "F03"), "research": tuple(f"R{i:02d}" for i in range(1, 7)),
              "chat": ("H01", "H02")}
    if selection in groups:
        return list(groups[selection])
    selected = selection.split(",")
    if not selected or len(set(selected)) != len(selected) or any(t not in ALL_IDS for t in selected):
        raise ValueError("Unknown or duplicate task selection")
    return selected


def cases(task_id, seed=17):
    if type(seed) is not int or not 0 <= seed < 2**32:
        raise ValueError("Seed must be an integer in [0, 2**32)")
    result = module(task_id).cases(seed)
    if not result or len({c["id"] for c in result}) != len(result):
        raise ValueError("Empty or duplicate case IDs")
    tier_weights = {tier: 0 for tier in ("basic", "scientific", "stress")}
    for case in result:
        if case["tier"] not in tier_weights or type(case["weight"]) not in (int, float) or case["weight"] <= 0:
            raise ValueError("Invalid case weight or tier")
        if "input" not in case or ("expected" not in case and "error" not in case):
            raise ValueError("Missing case input or expected behavior")
        tier_weights[case["tier"]] += case["weight"]
    if tier_weights != {"basic": 20, "scientific": 30, "stress": 20}:
        raise ValueError("Case weights must preserve 20/30/20 relative weights")
    return result


def case_manifest(task_id, seed=17):
    return [{"id": c["id"], "tier": c["tier"], "weight": c["weight"],
             "critical": bool(c.get("critical", False))} for c in cases(task_id, seed)]

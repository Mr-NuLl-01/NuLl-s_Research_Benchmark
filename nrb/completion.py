"""Explicit scientific completion obligations, separate from the 70+30 score."""
from __future__ import annotations
from copy import deepcopy

REVIEW_POLICY_VERSION = "essential-review-0.2.0"
QUALITY_THRESHOLD = 80

# These conditions are public responsibilities, not reference answers.
ESSENTIAL_REVIEW = {
    "NRB01": [
        ("evidence_scope", "贡献表述与直接证据、统计单位和适用范围一致，没有严重来源或因果误述。")],
    "NRB02": [
        ("equivalence_proof", "给出任意已知输入下的参数等价族论证，未以单次拟合代替可辨识性。"),
        ("intervention_conditions", "说明判别干预为何有效及需要保持不变的模型条件。")],
    "NRB03": [
        ("search_reproduced", "按公开 solve(problem) 入口实际执行必交搜索代码，结果与提交和精确最优层级一致；须有绑定的执行回执。"),
        ("optimality_explanation", "搜索、全部约束与最优性论证可复查，和交付代码相符。")],
    "NRB04": [
        ("conservation_explanation", "守恒、界面和边界说明与交付实现一致，无破坏核心科学含义的误述。")],
    "NRB05": [
        ("lifecycle_explanation", "试探、接受、拒步回滚及终止语义完整且与代码一致。")],
    "NRB06": [
        ("uncertainty_interpretation", "量纲、已知绝对方差和相关项的解释正确，无严重不确定度或频谱定义误述。")],
    "NRB07": [
        ("evaluation_scope", "按独立机器与验证选模解释结果，准确区分合成预测评测与真实训练验证。")],
    "NRB08": [
        ("existence_uniqueness", "完整证明存在唯一性，明确空间、范数和收缩条件。"),
        ("residual_bound_proof", "推导一般残差误差界，范数、常数和不等式方向一致。"),
        ("counterexample_explanation", "反例满足所检验前提并确实推翻指定结论，有可核查解释。")],
    "NRB09": [
        ("render_legibility", "实际查看绑定的渲染图，核对整图与180mm等效展示可读，无关键遮挡或近乎不可见内容。"),
        ("schematic_correctness", "示意部件、连接和箭头正确表达本题经典模型。"),
        ("caption_fidelity", "图注与实际数据、合成来源、给定模型和残差一致。")],
    "NRB10": [
        ("english_fidelity", "英文正文连贯可用，忠实保留给定证据强度、数值与结论范围。"),
        ("handoff_actionable", "交接清楚列明当前版本、已完成与待办工作，他人可据此接续。"),
        ("execution_honesty", "不把所提供日志冒称为本次实际执行，不虚构检查、平台或授权。")],
}

ESSENTIAL_AUTOMATIC = {
    "NRB01": {"current_source", "independent_units"},
    "NRB02": {"structural_rank", "scale_symmetry", "discriminating_intervention"},
    "NRB03": {"all_design_constraints", "global_optimality", "strict_runner_up"},
    "NRB08": {"weighted_induced_norm", "residual_certificate", "counterexample_validity"},
    "NRB10": {"handoff_revision", "handoff_status", "evidence_full_validation"},
}


def requirements(task_id):
    return [{"id": key, "requirement": text} for key, text in ESSENTIAL_REVIEW[task_id]]


def blank_essential(case):
    return [{**item, "outcome": "unassessed", "evidence": "", "rationale": ""}
            for item in case["essential_review_requirements"]]


def refresh_completion(report):
    """A confirmed failure takes precedence while all outstanding items survive."""
    report = dict(report)
    essential = report.get("essential_review", [])
    review_failures = [x["id"] for x in essential if x.get("outcome") == "fail"]
    automatic = list(dict.fromkeys(report.get("automatic_critical_failures", report.get("critical_failures", []))))
    report["automatic_critical_failures"] = automatic
    report["review_critical_failures"] = review_failures
    report["critical_failures"] = list(dict.fromkeys(automatic + ["essential:" + x for x in review_failures]))
    pending_auto = [x["id"] for x in report.get("checks", []) if x.get("passed") is None]
    pending_review = [x["id"] for x in essential if x.get("outcome") == "unassessed"]
    mandatory = report.get("mandatory_execution", [])
    for receipt in mandatory:
        if receipt.get("passed") is False:
            key = "execution:" + receipt["id"]
            if key not in report["critical_failures"]:
                report["critical_failures"].append(key)
    pending_execution = [x["id"] for x in mandatory if x.get("passed") is None]
    pending = (["automatic:" + x for x in pending_auto] + ["essential:" + x for x in pending_review]
               + ["execution:" + x for x in pending_execution]
               + (["quality_review"] if report.get("review_pending", True) else []))
    report["pending_items"] = pending
    infrastructure = bool(pending_auto or pending_execution or report.get("coverage") != 1
                          or report.get("protocol_violation")
                          or report.get("status") in {"infrastructure_unscored", "protocol_violation"})
    if report["critical_failures"] or report.get("delivery_complete") is False:
        status = "failed"
    elif infrastructure:
        status = "infrastructure_unscored"
    elif pending_review or not essential:
        status = "pending_review"
    else:
        status = "complete"
    report["completion_status"] = status
    total = report.get("total")
    report["quality_qualified"] = (False if status == "failed" or (total is not None and total < QUALITY_THRESHOLD)
                                   else True if status == "complete" and total is not None else None)
    report["qualification_threshold"] = QUALITY_THRESHOLD
    report["completion_judgement"] = report.get("score_label", "unreviewed")
    return report


def validate_essential(case, entries):
    required = {x["id"] for x in case["essential_review_requirements"]}
    if not isinstance(entries, list) or len(entries) != len(required) or any(not isinstance(x, dict) for x in entries):
        raise ValueError("Review must assess every essential responsibility exactly once")
    if any(not isinstance(x.get("id"), str) for x in entries) or {x.get("id") for x in entries} != required:
        raise ValueError("Essential review responsibilities do not match this case")
    for entry in entries:
        if not isinstance(entry.get("outcome"), str) or entry["outcome"] not in {"pass", "fail", "unassessed"}:
            raise ValueError("Essential outcomes must be pass, fail, or unassessed")
        if entry["outcome"] != "unassessed":
            for key in ("evidence", "rationale"):
                if not isinstance(entry.get(key), str) or not entry[key].strip():
                    raise ValueError("Essential pass/fail requires evidence and scientific rationale")
    return deepcopy(entries)

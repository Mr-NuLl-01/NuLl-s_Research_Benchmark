"""NRB03: exact finite minimax design for a generic calibration slope."""
from __future__ import annotations

import itertools
from fractions import Fraction
from functools import lru_cache
import hashlib
import json
import math
import random

from nrb.checks import check


def _mapping(value):
    return value if isinstance(value, dict) else {}


def _near(value, expected):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value) and math.isclose(value, expected, rel_tol=3e-7, abs_tol=1e-10)
    except (OverflowError, TypeError, ValueError):
        return False


def _shape(allocation, problem):
    return (isinstance(allocation, (list, tuple)) and len(allocation) == len(problem["x"])
            and all(type(n) is int for n in allocation))


def _bounds(allocation, problem):
    return _shape(allocation, problem) and all(0 <= n <= cap for n, cap in zip(allocation, problem["max_replicates"]))


def _constraints(allocation, problem):
    if not _bounds(allocation, problem):
        return False
    total = sum(allocation)
    return (problem["min_total"] <= total <= problem["max_total"]
            and sum(n*c for n, c in zip(allocation, problem["costs"])) <= problem["budget"]
            and allocation[2] >= problem["min_center"]
            and sum(allocation[:2]) >= problem["min_each_side"]
            and sum(allocation[3:]) >= problem["min_each_side"]
            and allocation[0]+allocation[4] <= problem["max_extreme_total"])


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


@lru_cache(maxsize=128)
def _profiles(serialized_problem):
    """Integer-scaled information entries from the public finite decimals.

    Fraction(str(value)) treats the decimal JSON values as the mathematical
    input rather than importing their binary floating-point representations.
    A common denominator per scenario makes enumeration mostly integer work.
    """
    problem = json.loads(serialized_problem)
    x = [Fraction(str(v)) for v in problem["x"]]
    profiles = []
    for scenario in problem["variance_scenarios"]:
        terms = [(1/Fraction(str(v)), xi/Fraction(str(v)), xi*xi/Fraction(str(v)))
                 for xi, v in zip(x, scenario)]
        denominator = math.lcm(*(term.denominator for row in terms for term in row))
        scaled = [tuple(int(term*denominator) for term in row) for row in terms]
        profiles.append((denominator, scaled))
    return profiles


def _exact_variances(allocation, problem):
    result = []
    for denominator, scaled in _profiles(_canonical(problem)):
        s0, s1, s2 = (sum(n*entry[j] for n, entry in zip(allocation, scaled)) for j in range(3))
        determinant = s0*s2-s1*s1
        if determinant <= 0:
            return None
        result.append(Fraction(s0*denominator, determinant))
    return result


def _variances(allocation, problem):
    """Displayed values; exact membership decisions use _exact_variances."""
    exact = _exact_variances(allocation, problem)
    return None if exact is None else [float(v) for v in exact]


@lru_cache(maxsize=128)
def _exact_search(serialized_problem):
    problem = json.loads(serialized_problem)
    rows = []
    for allocation in itertools.product(*(range(n+1) for n in problem["max_replicates"])):
        if not _constraints(allocation, problem):
            continue
        variances = _exact_variances(allocation, problem)
        if variances is not None:
            rows.append((max(variances), allocation, variances))
    rows.sort(key=lambda row: (row[0], row[1]))
    if not rows:
        raise ValueError("The generated design has no feasible allocations")
    best = rows[0]
    # This decimal threshold governs runner-up levels only. It never widens
    # the globally optimal set, which consists of exact minimizers.
    threshold = Fraction(1, 10**12)
    second = next((row for row in rows if row[0] > best[0]+threshold), None)
    if second is None:
        raise ValueError("The design has no strictly larger objective above the runner-up threshold")
    return best, second, len(rows)


def _solve(problem):
    best, second, count = _exact_search(_canonical(problem))
    n = best[1]
    return {
        "allocation": list(n), "total_cost": sum(c*k for c, k in zip(problem["costs"], n)),
        "total_measurements": sum(n), "scenario_slope_variances": [float(v) for v in best[2]],
        "worst_slope_variance": float(best[0]),
        "worst_scenario": best[2].index(best[0])+1,
        "feasible_allocation_count": count,
        "second_distinct_allocation": list(second[1]),
        "second_distinct_objective": float(second[0]), "objective_gap": float(second[0]-best[0]),
    }


def build(seed: int = 0) -> dict:
    rng = random.Random(f"nrb03-v1:design:{seed}")
    x = [-rng.randint(3, 5), -rng.randint(1, 2), 0, rng.randint(1, 2), rng.randint(3, 5)]
    base_profiles = [[1.0, 1.6, 2.2, 3.0, 5.5], [5.2, 3.3, 2.0, 1.6, 1.0],
                     [2.6, 1.3, 4.2, 1.4, 2.5]]
    profiles = [[round(v*rng.uniform(0.72, 1.35), 2) for v in row] for row in base_profiles]
    rng.shuffle(profiles)
    problem = {
        "provenance": "Original synthetic calibration-design instance; no real experiment data.",
        "model": "y=intercept+slope*x+epsilon; intercept and slope both unknown",
        "x": x,
        "costs": [rng.randint(1, 3), rng.randint(1, 3), 1, rng.randint(1, 3), rng.randint(1, 3)],
        "max_replicates": [rng.randint(3, 6), rng.randint(3, 6), rng.randint(3, 5),
                           rng.randint(3, 6), rng.randint(3, 6)],
        "budget": rng.randint(20, 28), "min_total": 8, "max_total": rng.randint(11, 14),
        "min_center": rng.randint(1, 2), "min_each_side": 2,
        "max_extreme_total": rng.randint(6, 9),
        "variance_scenarios": profiles,
        "variance_units": "sensor_reading squared; these are variances, NOT standard deviations",
        "assumptions": ["All replicate errors independent with zero mean.",
                        "The listed variance is per single measurement at each x.",
                        "The design must be chosen before the scenario is revealed.",
                        "A separate calibration identifies the true scenario before analysis; use its correct WLS weights.",
                        "The model is linear over these levels; center quota is an imposed practical constraint."],
        "objective": "minimize the maximum variance of the estimated slope across the three scenarios",
        "tie_policy": "Finite decimal inputs are exact. Any exact global minimizer is accepted; runner-up is the minimum objective strictly greater than the exact minimum plus 1e-12. Display tolerances do not widen either allocation set.",
    }
    answer = _solve(problem)
    prompt = """为一个通用线性量具的斜率校准分配有限测量次数。
design.json 给出五个输入水平、各次测量成本、每水平次数上限、预算与总次数约束，
以及三个候选单次测量方差情景。请求解离散的全局 minimax 设计，不能只把次数
均分、按成本分配、优化平均方差或把截距当作已知。三个情景无需设概率。

设计在情景揭示前选择；分析前可通过独立校准确知情景并使用正确加权最小二乘。
因此，对情景 s，信息矩阵为 sum_i [n_i/v_si]*[[1,x_i],[x_i,x_i^2]]，
目标是其逆矩阵中斜率方差的三个情景最大值。v_si 是方差，不是标准差。

除预算和各次数上限外，还必须满足：min_total<=sum(n)<=max_total，中心次数
n[2]>=min_center，左右两侧各至少 min_each_side 次，两个最外端总次数不超过
max_extreme_total。计数“feasible_allocation_count”时统计满足所有上述约束且
可估计截距/斜率的整数向量，每个向量只计一次。

提交 JSON：{"task_id":"NRB03","answer":{...},"artifacts":{"reasoning.md":"...","solve.py":"..."}}。
answer 精确结构：
{
 "allocation":[0,0,0,0,0], "total_cost":0, "total_measurements":0,
 "scenario_slope_variances":[0,0,0], "worst_slope_variance":0, "worst_scenario":1,
 "feasible_allocation_count":0,
 "second_distinct_allocation":[0,0,0,0,0],
 "second_distinct_objective":0, "objective_gap":0
}
worst_scenario 为 1 起始情景编号。任意全局最优向量均接受；second_distinct 是
严格次优目标（精确目标与精确最优值差大于 1e-12 的最小层级），并非另一并列最优向量。
公开有限小数定义精确输入；全局最优向量必须达到精确最小值，显示数值的容差不扩大最优集合。objective_gap
为该严格次优值减最优值。自动数值评分也检查你给出的实际分配的约束和方差，
不能只填写最优目标数字。reasoning.md 解释含未知截距的方差推导、鲁棒目标、
全局最优性证据与适用条件；solve.py 提供仅依赖标准 Python 的可复查枚举或等价算法。
solve.py 必须定义 solve(problem)：problem 是解析 design.json 后的字典，返回与上述 answer
字段、类型完全相同的字典，不含 task_id/artifacts 包装，不读其他文件。模块导入不得运行命令行入口。
独立质量验收必须实际调用该入口并核对其结果与所交答案及所选向量一致；未实际执行不能算完成复现。
不要声称这些合成情景来自实际测量。数值建议直接保留计算结果的浮点精度；如需缩短，至少保留 9 位有效数字。
使用科学计数法表示小量，不把谱密度、协方差或目标差舍入为零。
评分容差按字段定义，不要求输出额外无意义的小数。
"""
    rubric = [
        {"id": "design_derivation", "title": "设计目标与统计模型", "anchors": {
            "0": "使用方差均值、漏掉截距或混淆方差/标准差，未提出正确目标。",
            "5": "目标正确但信息矩阵、单次/重复方差或情景识别假设解释不全。",
            "10": "从 WLS 信息矩阵推导含未知截距的斜率方差，并明确 minimax 与分析假设。"}},
        {"id": "optimality_evidence", "title": "可复查的全局最优性", "anchors": {
            "0": "只报最优答案或声称搜索完成而没有代码/可复查证据。",
            "5": "有可运行搜索，但约束覆盖、并列值或严格次优处理不清楚。",
            "10": "独立可运行算法覆盖完整可行域，统计数目、并列值与次优差均可复查。"}},
        {"id": "design_interpretation", "title": "设计解释与适用边界", "anchors": {
            "0": "把合成优化结果宣称为真实实验最优或忽略模型假设。",
            "5": "解释最坏情景与预算约束，但缺乏对模型改变的具体影响判断。",
            "10": "解释最坏情景/实际活跃约束，讨论相关误差、未涵盖情景或模型曲率如何改变结论。"}},
    ]
    return {"id": "NRB03", "seed": seed, "title": "有限预算下的鲁棒校准设计",
            "domain": "experimental_design", "prompt": prompt,
            "files": {"design.json": json.dumps(problem, ensure_ascii=False, indent=2)+"\n"},
            "expected": {"answer": answer}, "rubric": rubric}


def reference(case: dict) -> dict:
    problem = json.loads(case["files"]["design.json"])
    answer = _solve(problem)
    n = answer["allocation"]
    active = []
    if answer["total_cost"] == problem["budget"]:
        active.append("预算上限")
    if sum(n) == problem["max_total"]:
        active.append("总测量次数上限")
    if n[2] == problem["min_center"]:
        active.append("中心最低次数")
    if sum(n[:2]) == problem["min_each_side"]:
        active.append("左侧最低次数")
    if sum(n[3:]) == problem["min_each_side"]:
        active.append("右侧最低次数")
    if n[0]+n[4] == problem["max_extreme_total"]:
        active.append("最外端合计上限")
    active.extend(f"水平 {i+1} 次数上限" for i, (ni, cap) in enumerate(zip(n, problem["max_replicates"]))
                  if ni == cap)
    reasoning = f"""# 鲁棒离散设计

定义 S0=sum(n_i/v_i)，S1=sum(n_i*x_i/v_i)，S2=sum(n_i*x_i^2/v_i)。
截距与斜率同时未知，因此信息矩阵逆的斜率元素为 S0/(S0*S2-S1^2)，
而不是 1/S2。独立重复使每个水平的信息随 n_i 线性增加。

枚举各 n_i 的整数上限内全部向量，逐项检查成本、总数、中心、左右与端点限制。
三个情景分别计算信息矩阵，以最大斜率方差排序。找到
{answer['feasible_allocation_count']} 个可行且可估计的分配；最优分配是
{answer['allocation']}，目标 {answer['worst_slope_variance']:.12g}，最坏情景编号
{answer['worst_scenario']}。严格次优分配 {answer['second_distinct_allocation']} 的
目标为 {answer['second_distinct_objective']:.12g}，间距 {answer['objective_gap']:.12g}。
这给出所列有限可行域上的穷举最优性证据。公开十进制按 Fraction(str(value)) 精确运算，
最优集合按精确相等判定；只有严格次优层级使用精确的 1e-12 间隔阈值。

本解实际达到等号的约束包括：{'、'.join(active) if active else '没有输入约束取等号'}。
三个情景的方差依次为 {answer['scenario_slope_variances']}；优化由其中最大值决定，
不能由较小情景补偿。较远的输入水平具有较大斜率信息，但其噪声、成本、配额和
截距相关性同时影响有效信息，所以单纯最大化输入跨度或均分次数都不是本问题的解法。

这种最优性依赖给定线性模型、独立误差、每次测量方差、分析前可确定情景，
以及列出的有限情景集合。共同漂移会使信息不再随重复数简单相加；未建模曲率会
引入偏差；额外情景可能改变 minimax 解。真实实验应检查这些条件，再评价迁移。
solve.py 仅用可见 design.json，可在独立目录执行：python solve.py design.json。
"""
    solver = '''"""Standard-library NRB03 enumeration. Import exposes solve(problem)."""
from fractions import Fraction
import itertools
import json
import math
import sys


def solve(p):
    x = [Fraction(str(v)) for v in p["x"]]
    profiles = []
    for scenario in p["variance_scenarios"]:
        entries = [(1/Fraction(str(v)), xi/Fraction(str(v)), xi*xi/Fraction(str(v)))
                   for xi, v in zip(x, scenario)]
        denominator = math.lcm(*(v.denominator for row in entries for v in row))
        profiles.append((denominator, [[int(v*denominator) for v in row] for row in entries]))
    rows = []
    for n in itertools.product(*(range(k+1) for k in p["max_replicates"])):
        if not p["min_total"] <= sum(n) <= p["max_total"]: continue
        if sum(a*b for a,b in zip(n,p["costs"])) > p["budget"]: continue
        if n[2] < p["min_center"]: continue
        if min(sum(n[:2]),sum(n[3:])) < p["min_each_side"]: continue
        if n[0]+n[4] > p["max_extreme_total"]: continue
        vv = []
        for denominator, entries in profiles:
            s0, s1, s2 = (sum(ni*row[j] for ni,row in zip(n,entries)) for j in range(3))
            determinant = s0*s2-s1*s1
            if determinant <= 0: break
            vv.append(Fraction(s0*denominator, determinant))
        if len(vv) == len(profiles): rows.append((max(vv),n,vv))
    rows.sort(key=lambda row:(row[0],row[1]))
    best = rows[0]
    second = next(row for row in rows if row[0] > best[0]+Fraction(1,10**12))
    return {"allocation":list(best[1]),
            "total_cost":sum(ni*c for ni,c in zip(best[1],p["costs"])),
            "total_measurements":sum(best[1]),
            "scenario_slope_variances":[float(v) for v in best[2]],
            "worst_slope_variance":float(best[0]),
            "worst_scenario":best[2].index(best[0])+1,
            "feasible_allocation_count":len(rows),
            "second_distinct_allocation":list(second[1]),
            "second_distinct_objective":float(second[0]),
            "objective_gap":float(second[0]-best[0])}


if __name__ == "__main__":
    with open(sys.argv[1] if len(sys.argv)>1 else "design.json",encoding="utf-8") as stream:
        answer = solve(json.load(stream))
    # CLI compatibility alias; solve(problem) itself returns exactly answer.
    print(json.dumps(dict(answer, feasible_count=answer["feasible_allocation_count"]),indent=2))
'''
    return {"task_id": "NRB03", "answer": answer,
            "artifacts": {"reasoning.md": reasoning, "solve.py": solver}}


def grade(case: dict, submission, execution="none") -> list:
    ans = _mapping(_mapping(submission).get("answer"))
    ex = case["expected"]["answer"]
    p = json.loads(case["files"]["design.json"])
    exact_best, exact_second, _ = _exact_search(_canonical(p))
    n = ans.get("allocation")
    shape, bounds, feasible = _shape(n, p), _bounds(n, p), _constraints(n, p)
    exact_v = _exact_variances(n, p) if bounds else None
    variances = [float(v) for v in exact_v] if exact_v is not None else None
    valid = feasible and exact_v is not None
    out = [check("integer_allocation", 5, shape, "每水平一个真正的非负整数次数。"),
           check("replicate_bounds", 5, bounds, "分配符合每水平上限。"),
           check("all_design_constraints", 10, valid, "预算、总数、中心、两侧与端点约束全部满足。", critical=True)]
    cost = sum(c*k for c, k in zip(p["costs"], n)) if bounds else None
    total = sum(n) if bounds else None
    out.append(check("reported_cost", 5, bounds and type(ans.get("total_cost")) is int
                     and ans["total_cost"] == cost, "报告实际分配的总成本。"))
    out.append(check("reported_count", 5, bounds and type(ans.get("total_measurements")) is int
                     and ans["total_measurements"] == total, "报告实际分配的总测量次数。"))
    submitted_v = ans.get("scenario_slope_variances")
    for i in range(3):
        value = submitted_v[i] if isinstance(submitted_v, list) and len(submitted_v) == 3 else None
        correct = variances is not None and _near(value, variances[i])
        out.append(check(f"scenario_variance_{i+1}", 5, correct,
                         "核验所交分配在该情景的含截距斜率方差。"))
    worst = max(variances) if variances is not None else None
    si = ans.get("worst_scenario")
    worst_correct = (variances is not None and _near(ans.get("worst_slope_variance"), worst)
                     and type(si) is int and 1 <= si <= 3 and exact_v[si-1] == max(exact_v))
    out.append(check("minimax_objective", 5, worst_correct, "取三个情景的最大值及其实际编号。"))
    out.append(check("global_optimality", 10, valid and max(exact_v) == exact_best[0],
                     "实际提交的可行分配达到精确全局最优；显示容差不扩大最优集合。", critical=True))
    second_n = ans.get("second_distinct_allocation")
    second_v = _exact_variances(second_n, p) if _constraints(second_n, p) else None
    second_ok = (second_v is not None
                 and max(second_v) > exact_best[0]+Fraction(1, 10**12)
                 and max(second_v) == exact_second[0]
                 and _near(ans.get("second_distinct_objective"), ex["second_distinct_objective"])
                 and _near(ans.get("objective_gap"), ex["objective_gap"]))
    out.append(check("strict_runner_up", 5, second_ok,
                     "严格次优分配、值与最优差共同一致；并列最优不算严格次优。", critical=True))
    out.append(check("feasible_search_count", 5,
                     type(ans.get("feasible_allocation_count")) is int
                     and ans["feasible_allocation_count"] == ex["feasible_allocation_count"],
                     "完整有限可行域的向量计数。"))
    return out


def reproduce_solution(case: dict, submission, execution="none") -> dict:
    """Actually run the mandatory solve(problem) artifact, outside 70 points.

    External submissions must use the existing isolated Docker/container path.
    ``trusted`` remains available only to repository-owned regression controls,
    under the same restrictions as nrb.execution.run_python. Backend absence
    is unassessed execution evidence, never a fabricated candidate failure.
    """
    from nrb.core import fingerprint
    from nrb.execution import run_python

    packet = _mapping(submission)
    source = _mapping(packet.get("artifacts")).get("solve.py")
    problem = json.loads(case["files"]["design.json"])
    receipt = {
        "id": "solve_reproduction", "task_id": case["id"],
        "case_hash": case.get("case_hash") or fingerprint({k: v for k, v in case.items() if k != "expected"}),
        "submission_hash": fingerprint(submission),
        "source_hash": hashlib.sha256(source.encode("utf-8")).hexdigest() if isinstance(source, str) else None,
        "input_hash": fingerprint(problem), "result_hash": None,
        "execution": execution, "status": "unassessed", "passed": None,
        "detail": "", "checks": [],
    }
    if not isinstance(source, str) or not source.strip():
        receipt.update(status="fail", passed=False, detail="Missing mandatory solve.py source")
        return receipt
    run = run_python(source, problem, execution=execution, timeout=5)
    receipt["execution_status"] = run["status"]
    receipt["detail"] = run["detail"]
    if run["status"] == "unavailable":
        return receipt
    if run["status"] != "ok":
        receipt.update(status="fail", passed=False)
        return receipt
    result = run["result"]
    receipt["result_hash"] = fingerprint(result)
    expected_keys = set(case["expected"]["answer"])
    shape = isinstance(result, dict) and set(result) == expected_keys
    checks = grade(case, {"answer": result}) if shape else []
    valid = shape and all(row["passed"] is True for row in checks)
    submitted = _mapping(packet.get("answer"))
    # Each answer is independently checked against the exact public problem.
    # Chosen vectors must agree, preventing a different valid result from
    # masquerading as a reproduction. Numeric output may be legally rounded;
    # alternative tied worst-scenario labels remain acceptable when exact.
    same_vectors = (shape and result.get("allocation") == submitted.get("allocation")
                    and result.get("second_distinct_allocation") == submitted.get("second_distinct_allocation"))
    consistent = (same_vectors and all(_near(result.get(k), submitted.get(k)) for k in
                  ("worst_slope_variance", "second_distinct_objective", "objective_gap"))
                  and isinstance(result.get("scenario_slope_variances"), list)
                  and len(result["scenario_slope_variances"]) == 3
                  and isinstance(submitted.get("scenario_slope_variances"), list)
                  and len(submitted["scenario_slope_variances"]) == 3
                  and all(_near(a, b) for a, b in zip(result["scenario_slope_variances"],
                                                    submitted["scenario_slope_variances"])))
    submission_valid = all(row["passed"] is True for row in grade(case, packet))
    receipt["checks"] = checks + [
        check("solve_return_contract", 0, shape, "solve(problem) returns exactly the declared answer dictionary."),
        check("solve_matches_submission", 0, consistent and submission_valid,
              "Both answers are scientifically valid and reproduce the same chosen vectors and their values."),
    ]
    receipt.update(status="pass" if valid and consistent and submission_valid else "fail",
                   passed=bool(valid and consistent and submission_valid))
    return receipt

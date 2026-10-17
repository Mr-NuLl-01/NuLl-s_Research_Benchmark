"""NRB08: affine contraction proof obligations and a checked counterexample."""
from __future__ import annotations

import cmath
import copy
import json
import math
import random

from nrb.checks import check


def _mapping(value):
    return value if isinstance(value, dict) else {}


def _finite(value):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except (OverflowError, TypeError, ValueError):
        return False


def _near(value, expected):
    return _finite(value) and math.isclose(value, expected, rel_tol=3e-7, abs_tol=1e-9)


def _vector(value, n):
    return isinstance(value, list) and len(value) == n and all(_finite(x) for x in value)


def _matrix(value, n):
    return isinstance(value, list) and len(value) == n and all(_vector(row, n) for row in value)


def _vnear(value, expected):
    return _vector(value, len(expected)) and all(_near(x, y) for x, y in zip(value, expected))


def _matvec(matrix, vector):
    return [sum(a*x for a, x in zip(row, vector)) for row in matrix]


def _solve_linear(matrix, right):
    """Small dense partial-pivot solve, no optional numerical dependency."""
    n = len(right)
    work = [[float(x) for x in row]+[float(b)] for row, b in zip(matrix, right)]
    for j in range(n):
        p = max(range(j, n), key=lambda i: abs(work[i][j]))
        if abs(work[p][j]) < 1e-13:
            raise ValueError("singular or numerically degenerate system")
        work[j], work[p] = work[p], work[j]
        pivot = work[j][j]
        work[j] = [x/pivot for x in work[j]]
        for i in range(n):
            if i == j:
                continue
            multiplier = work[i][j]
            work[i] = [x-multiplier*y for x, y in zip(work[i], work[j])]
    return [row[-1] for row in work]


def _fixed_point(matrix, right):
    n = len(right)
    return _solve_linear([[(1.0 if i == j else 0.0)-matrix[i][j] for j in range(n)]
                          for i in range(n)], right)


def _problem_values(problem):
    matrix, b, w, xhat = (problem[k] for k in ["A", "b", "weights", "x_hat"])
    q = max(sum(abs(a)*wj/wi for a, wj in zip(row, w)) for row, wi in zip(matrix, w))
    q0 = max(sum(abs(a) for a in row) for row in matrix)
    xstar = _fixed_point(matrix, b)
    ax = _matvec(matrix, xhat)
    residual = [v+bi-x for v, bi, x in zip(ax, b, xhat)]
    rnorm = max(abs(r)/wi for r, wi in zip(residual, w))
    error = max(abs(x-y)/wi for x, y, wi in zip(xhat, xstar, w))
    return {"weighted_operator_norm": q, "unweighted_operator_norm": q0,
            "fixed_point": xstar, "residual_vector": residual,
            "weighted_residual_norm": rnorm, "certified_weighted_error_bound": rnorm/(1-q),
            "actual_weighted_error": error}


def _counterexample_values(counterexample):
    c = _mapping(counterexample)
    matrix, b, xhat = c.get("A"), c.get("b"), c.get("x_hat")
    if not _matrix(matrix, 2) or not _vector(b, 2) or not _vector(xhat, 2):
        return None
    if any(abs(x) > 100 for row in matrix for x in row) or any(abs(x)>100 for x in b+xhat):
        return None
    trace = matrix[0][0]+matrix[1][1]
    determinant = matrix[0][0]*matrix[1][1]-matrix[0][1]*matrix[1][0]
    discriminant = cmath.sqrt(trace*trace-4*determinant)
    rho = max(abs((trace+discriminant)/2), abs((trace-discriminant)/2))
    if not math.isfinite(rho) or rho >= 1:
        return None
    try:
        xstar = _fixed_point(matrix, b)
    except (ValueError, OverflowError, ZeroDivisionError):
        return None
    residual = max(abs(v+bi-x) for v, bi, x in zip(_matvec(matrix, xhat), b, xhat))
    error = max(abs(x-y) for x, y in zip(xhat, xstar))
    return {"fixed_point": xstar, "spectral_radius": rho, "residual_infinity_norm": residual,
            "actual_infinity_error": error, "claimed_bound": residual/(1-rho)}


def build(seed: int = 0) -> dict:
    rng = random.Random(f"nrb08-v1:{seed}")
    weights = [1, 4, 16]
    rng.shuffle(weights)
    matrix = []
    for i in range(3):
        row = []
        for j in range(3):
            sign = rng.choice([-1, 1]) if i != j else 1
            base = sign*rng.randint(8, 25)/100
            row.append(round(base*weights[i]/weights[j], 12))
        matrix.append(row)
    target = [rng.randint(-12, 16)/4 for _ in range(3)]
    b = [round(x-a, 12) for x, a in zip(target, _matvec(matrix, target))]
    xhat = [round(x+wi*rng.choice([-1, 1])*rng.randint(1, 8)/100, 12)
            for x, wi in zip(target, weights)]
    problem = {"provenance": "Original synthetic affine system using classical linear algebra.",
               "A": matrix, "b": b, "weights": weights, "x_hat": xhat,
               "domain": "R^3", "map": "F(x)=A*x+b",
               "norm": "||v||_(infinity,w)=max_i |v_i|/weights_i",
               "residual_definition": "F(x_hat)-x_hat",
               "number_convention": "Displayed finite decimals define the input matrix and vectors.",
               "false_claim": "For every affine F with spectral radius rho(A)<1, in the ordinary infinity norm: ||x_hat-x_star|| <= ||F(x_hat)-x_hat||/(1-rho(A))."}
    values = _problem_values(problem)
    r = rng.randint(2, 7)/10
    big = rng.randint(15, 40)/10
    counterexample = {"A": [[r, big], [0.0, r]], "b": [0.0, 0.0],
                      "x_hat": [big/(1-r), 1.0]}
    counterexample.update(_counterexample_values(counterexample))
    answer = dict(values)
    answer["claims"] = {"unique_fixed_point": True,
                        "ordinary_infinity_contraction": values["unweighted_operator_norm"] < 1,
                        "spectral_radius_substitution_universally_valid": False}
    answer["counterexample"] = counterexample
    prompt = """对 affine.json 中 F:R^3->R^3, F(x)=Ax+b，完成解析证明、数值证书和反例。
使用指定权重的无穷范数，计算精确诱导算子范数 q（不是任选一个更松上界）以及
普通无穷范数下的算子范数。证明该系统固定点存在且唯一，求固定点，计算题定
候选点的残差向量、加权残差范数，以及残差推导出的误差上界和实际加权误差。

另外反驳文件中 false_claim：不能未经证明把同一范数下的收缩常数换为谱半径。
请自行给出 2x2 实矩阵、向量 b 和 x_hat；为了数值判别清楚，要求全部元素绝对值
<=100，rho(A)<=0.95，残差无穷范数>1e-8，并让实际误差至少为错误上界的 1.2 倍。
反例可以不同于题给 3x3 系统。评分器会由你交的矩阵重新求解和计算，不接受仅写
“非正规矩阵可能有问题”。必须区分一般定理证明、具体数值检验和反例的逻辑角色。

提交 JSON：{"task_id":"NRB08","answer":{...},"artifacts":{"reasoning.md":"..."}}。
answer 的精确结构：
{
 "weighted_operator_norm":0,"unweighted_operator_norm":0,
 "fixed_point":[0,0,0],"residual_vector":[0,0,0],"weighted_residual_norm":0,
 "certified_weighted_error_bound":0,"actual_weighted_error":0,
 "claims":{"unique_fixed_point":"boolean，由你判断","ordinary_infinity_contraction":"boolean，由你判断",
   "spectral_radius_substitution_universally_valid":"boolean，由你判断"},
 "counterexample":{"A":[[0,0],[0,0]],"b":[0,0],"x_hat":[0,0],
   "fixed_point":[0,0],"spectral_radius":0,"residual_infinity_norm":0,
   "actual_infinity_error":0,"claimed_bound":0}
}
claims 中三个字段的提交类型均为 JSON boolean；上面的类型说明不是待复制的取值。
reasoning.md 须包含：算子范数的推导、完备性与自映射条件、存在及唯一性论证、
对任意候选点成立的残差不等式推导，以及反例如何击破原命题。
普通无穷范数不收缩不能单独推出固定点不存在。数值保留至少 8 位有效数字；
解析公式给出理论证书，其小数展示是近似值。本题不要求有向舍入区间证书或 Lean。
"""
    rubric = [
        {"id": "contraction_proof", "title": "完整的定理责任", "anchors": {
            "0": "用一次数值试验充当存在唯一性证明，或混淆充分与必要条件。",
            "5": "引用收缩结论合理，但加权范数、自映射、完备性或唯一性有遗漏。",
            "10": "完整说明范数与收缩常数、R^3 完备自映射，以及存在和唯一性的推导。"}},
        {"id": "certificate_derivation", "title": "残差与误差的逻辑联系", "anchors": {
            "0": "把残差直接当误差或只列近似数值，没有一般不等式。",
            "5": "公式正确但缺少推导、范数一致性或数值/严格性边界。",
            "10": "从任意点推导 e<=r+qe 及证书，明确固定点误差与舍入近似的不同责任。"}},
        {"id": "counterexample_explanation", "title": "反例的有效性与解释", "anchors": {
            "0": "没有实际反例或只是说明收敛可能缓慢。",
            "5": "反例计算有效，但未指出谱半径不能替代给定范数的 Lipschitz 常数。",
            "10": "逐项核验原命题假设和失败结论，并解释非正规性/范数选择而不否定正确收缩定理。"}},
    ]
    return {"id": "NRB08", "seed": seed, "title": "仿射收缩的证明、反例与误差证书",
            "domain": "mathematical_certification", "prompt": prompt,
            "files": {"affine.json": json.dumps(problem, ensure_ascii=False, indent=2)+"\n"},
            "expected": {"answer": answer}, "rubric": rubric}


def reference(case: dict) -> dict:
    answer = copy.deepcopy(case["expected"]["answer"])
    problem = json.loads(case["files"]["affine.json"])
    answer.update(_problem_values(problem))
    ce = answer["counterexample"]
    r, big = ce["A"][0]
    reasoning = f"""# 定理与实例

令 D=diag(w)。||v||_(infinity,w)=||D^-1 v||_infinity，因此诱导范数为
q=||D^-1 A D||_infinity=max_i sum_j |A_ij|w_j/w_i。
上界由逐行三角不等式得到；选择达到最大行的输入符号可达到该行绝对值和，
所以这里给出的 q 是精确诱导范数。
本题 q={answer['weighted_operator_norm']:.12g}<1。所有权重正，R^3 在此范数下
完备，仿射映射仍映到 R^3。级数 sum_(k>=0) A^k b 由几何界收敛，其和满足
x*=Ax*+b。若另有固定点 z，则 ||x*-z||<=q||x*-z||，故二者相等。
这给出一般性存在唯一性责任；直接解 (I-A)x*=b 只是本实例的数值求值。

任取 xhat，记 r=F(xhat)-xhat 和 e=xhat-x*，则
||e||<=||xhat-F(xhat)||+||F(xhat)-F(x*)||<=||r||+q||e||。
所以 ||e||<=||r||/(1-q)。同一个加权范数必须用于 r、e 与 q。
解析不等式是理论证书；这里的小数值是公式的浮点求值，不冒称已做机器区间认证。

反例取 A=[[r,M],[0,r]]，b=0，xhat=[M/(1-r),1]，其中
r={r:g}，M={big:g}。两个特征值均为 r，固定点为零，而
F(xhat)-xhat=[0,-(1-r)]。因此残差无穷范数为 1-r，错误的谱半径上界为 1，
实际误差为 M/(1-r)={ce['actual_infinity_error']:.12g}>1。
谱半径约束渐近谱性质，不等于指定范数下的一步收缩常数；换范数时必须一起改变
向量范数与证书。该反例不否定正确的加权收缩定理。
"""
    return {"task_id": "NRB08", "answer": answer, "artifacts": {"reasoning.md": reasoning}}


def grade(case: dict, submission, execution="none") -> list:
    ans = _mapping(_mapping(submission).get("answer"))
    ex = case["expected"]["answer"]
    out = [check("weighted_induced_norm", 10,
                 _near(ans.get("weighted_operator_norm"), ex["weighted_operator_norm"]),
                 "精确加权诱导范数，而非谱半径或普通范数。", critical=True),
           check("ordinary_induced_norm", 5,
                 _near(ans.get("unweighted_operator_norm"), ex["unweighted_operator_norm"]),
                 "普通无穷范数的绝对行和最大值。"),
           check("fixed_point", 10, _vnear(ans.get("fixed_point"), ex["fixed_point"]),
                 "求解题给十进制矩阵的 (I-A)x=b。"),
           check("residual_vector", 5, _vnear(ans.get("residual_vector"), ex["residual_vector"]),
                 "方向必须为 F(x_hat)-x_hat。"),
           check("residual_norm", 5,
                 _near(ans.get("weighted_residual_norm"), ex["weighted_residual_norm"]),
                 "指定权重下的残差范数。"),
           check("residual_certificate", 10,
                 _near(ans.get("certified_weighted_error_bound"), ex["certified_weighted_error_bound"]),
                 "同一加权范数下的 r/(1-q) 解析上界。", critical=True),
           check("actual_error", 5, _near(ans.get("actual_weighted_error"), ex["actual_weighted_error"]),
                 "区分实际误差与其保守上界。")]
    counterexample = _mapping(ans.get("counterexample"))
    cv = _counterexample_values(counterexample)
    valid = (cv is not None and cv["spectral_radius"] <= 0.95+1e-12
             and cv["residual_infinity_norm"] > 1e-8
             and cv["actual_infinity_error"] >= 1.2*cv["claimed_bound"])
    out.append(check("counterexample_validity", 10, valid,
                     "从所交矩阵重新验证谱半径条件及被反驳的误差不等式。", critical=True))
    values_correct = (cv is not None and _vnear(counterexample.get("fixed_point"), cv["fixed_point"])
                      and all(_near(counterexample.get(k), cv[k]) for k in
                              ["spectral_radius", "residual_infinity_norm", "actual_infinity_error", "claimed_bound"]))
    out.append(check("counterexample_calculations", 5, values_correct,
                     "反例的特征值、固定点、残差及实际误差均由输入重算。"))
    claims = _mapping(ans.get("claims"))
    correct_claims = set(claims) == set(ex["claims"]) and all(claims.get(k) is v for k, v in ex["claims"].items())
    out.append(check("logical_claims", 5, correct_claims,
                     "区分固定点唯一、指定范数收缩及普适谱半径替换命题。"))
    return out

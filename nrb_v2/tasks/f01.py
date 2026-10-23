"""F01: stable nonuniform SG transport with an explicit binary64 domain."""
from __future__ import annotations

import copy
import json
import math
from nrb_v1.tasks import c06 as legacy

TASK = {**legacy.TASK, "id": "F01", "title": "Fortran 非均匀网格守恒漂移扩散",
        "required_artifacts": ["solution.f90"], "manual_review_required": False,
        "scoring": "automatic", "max_score": 100}
TASK.pop("essential", None)

FORTRAN = legacy.FORTRAN.replace(
    "if(any(h<=0)) call fail()",
    """if(any(h<1.e-8_real64).or.any(h>1000._real64)) call fail()
if(any(abs(x)>1000._real64).or.any(d/h<1.e-12_real64).or.any(d/h>1.e8_real64)) call fail()
if(any(abs(v)>1.e6_real64).or.any(s>1.e6_real64).or.any(k>1.e6_real64)) call fail()
if(left>1.e6_real64.or.right>1.e6_real64) call fail()""").replace(
    "f=-a(j)/diag(j-1)",
    "if(.not.ieee_is_finite(diag(j-1)).or.diag(j-1)<=1.e-280_real64) call fail()\n f=-a(j)/diag(j-1)").replace(
    "u(n-1)=rhs(n-2)/diag(n-2)",
    "if(.not.ieee_is_finite(diag(n-2)).or.diag(n-2)<=1.e-280_real64) call fail()\nu(n-1)=rhs(n-2)/diag(n-2)").replace(
    "flux=a*u(1:n-1)-b*u(2:n)",
    "if(.not.all(ieee_is_finite(u)).or.any(u<0).or.any(u>1.e100_real64)) call fail()\nflux=a*u(1:n-1)-b*u(2:n)").replace(
    "write(*,'(*(ES25.16E3,1X))') u",
    "if(.not.all(ieee_is_finite(flux)).or..not.ieee_is_finite(mass).or..not.ieee_is_finite(residual)) call fail()\nwrite(*,'(*(ES25.16E3,1X))') u")


def _reference(p):
    x, d, v, s, k = (p[key] for key in ("x", "diffusion", "velocity", "source", "decay"))
    n = len(x)
    if not (3 <= n <= 129 and len(d) == len(v) == n-1 and len(s) == len(k) == n-2):
        raise ValueError("invalid shapes")
    if any(not isinstance(z, (int, float)) or isinstance(z, bool) or not math.isfinite(z)
           for seq in (x, d, v, s, k, [p["left"], p["right"]]) for z in seq):
        raise ValueError("nonfinite input")
    h = [x[i+1]-x[i] for i in range(n-1)]
    if (any(not 1e-8 <= q <= 1000 for q in h) or any(abs(q)>1000 for q in x)
        or any(not 1e-12 <= d[i]/h[i] <= 1e8 for i in range(n-1))
        or any(abs(q)>1e6 for q in v) or any(not 0 <= q <= 1e6 for q in s+k+[p["left"],p["right"]])):
        raise ValueError("outside supported binary64 domain")
    pe = [v[i]*h[i]/d[i] for i in range(n-1)]
    if any(not math.isfinite(z) or abs(z)>2500 for z in pe):
        raise ValueError("unsupported Peclet")
    a = [d[i]/h[i]*legacy._bernoulli(-pe[i]) for i in range(n-1)]
    b = [d[i]/h[i]*legacy._bernoulli(pe[i]) for i in range(n-1)]
    diag = [b[i]+a[i+1]+k[i]*(h[i]+h[i+1])/2 for i in range(n-2)]
    for j in range(1, n-2):
        if not math.isfinite(diag[j-1]) or diag[j-1] <= 1e-280:
            raise ValueError("unresolved pivot")
        diag[j] -= a[j]*b[j]/diag[j-1]
    if not math.isfinite(diag[-1]) or diag[-1] <= 1e-280:
        raise ValueError("unresolved pivot")
    answer = legacy._reference(p)
    if any(not math.isfinite(q) or not 0 <= q <= 1e100 for q in answer["density"]):
        raise ValueError("unrepresentable positive solution")
    return answer


def _case(cid, tier, p, weight):
    case = dict(id=cid, tier=tier, input=p, weight=weight, critical=True, rtol=2e-8, atol=2e-8)
    try:
        case["expected"] = _reference(p)
        case["expected"]["residual_inf"] = 0.0
    except ValueError:
        case["error"] = "ValueError"
    return case


def cases(seed=17):
    old = legacy.cases(seed)
    out = [dict(c) for c in old[:5]]
    positive = copy.deepcopy(old[5]["input"])
    negative = copy.deepcopy(positive)
    negative.update(velocity=[-900.0]*40, left=0.2, right=0.8)
    out.extend([_case("peclet_2250_positive", "stress", positive, 4),
                _case("peclet_2250_negative", "stress", negative, 4),
                _case("near_zero_bernoulli", "stress", old[6]["input"], 4)])
    turning = dict(x=[0.0, 0.5, 1.0], diffusion=[0.001, 0.001],
                   velocity=[4.5, -4.5], source=[1.0], decay=[0.0], left=1.0, right=1.0)
    out.extend([_case("reject_unresolved_converging_flow", "stress", turning, 2),
                _case("reject_collapsed_cell", "stress", old[7]["input"], 2),
                _case("reject_negative_diffusion", "stress", old[8]["input"], 2)])
    outside = copy.deepcopy(positive); outside["velocity"] = [1200.0]*40
    out.append(_case("reject_peclet_over_2500", "stress", outside, 2))
    return out


fortran_input = legacy.fortran_input
parse_fortran = legacy.parse_fortran


def validate_output(case, output):
    if isinstance(output, dict) and isinstance(output.get("density"), list):
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or v < 0 for v in output["density"]):
            return False, "density must be a nonnegative finite real array"
    return legacy.validate_output(case, output)


def prompt(seed=17):
    p = next(c["input"] for c in cases(seed) if c["id"] == "heterogeneous_nonuniform")
    return '''# F01 · Fortran 非均匀网格守恒漂移扩散

实现一个标准 Fortran 2008 单文件程序 `solution.f90`。只提交源码；说明和自测可选，不设人工分。问题为公开经典输运方程的原创合成数据，不含私人研究数据。

## 方程与离散目标

正方向为 x 增大。x[m]、D[m²/s]>0、v[m/s]、密度u[m⁻³]、源s[m⁻³s⁻¹]≥0、衰减k[s⁻¹]≥0。
连续关系为 J=v*u-D*du/dx，dJ/dx+k*u=s。端点u固定且非负。

必须求解以下指定离散系统。边i连接节点i与i+1：

```
h_i = x_(i+1)-x_i
P_i = v_i*h_i/D_i
B(z) = z/(exp(z)-1), B(0)=1
a_i = (D_i/h_i)*B(-P_i), b_i = (D_i/h_i)*B(P_i)
J_i = a_i*u_i-b_i*u_(i+1)
w_i = (h_(i-1)+h_i)/2
(J_i-J_(i-1))/w_i+k_i*u_i=s_i  （内部节点）
```

不得用中心漂移替代SG通量。稳定处理零漂移、小参数、正负大P；正参数指数下溢为0可用于二进制64位系数。mass是全区间梯形积分 `sum(h_i*(u_i+u_(i+1))/2)`，单位m⁻²，不是kg。residual_inf是全部内部密度方程残差的最大绝对值。

## 输入与可表示范围

stdin依次为7行：`N`；`x[N]`；`diffusion[N-1]`；`velocity[N-1]`；`source[N-2]`；`decay[N-2]`；`left right`。测试按所列长度提供数值数组。

3≤N≤129，所有数有限，|x|≤1000；每边1e-8≤h≤1000，1e-12≤D/h≤1e8，|v|≤1e6，|P|≤2500；源、衰减、两端密度均在[0,1e6]。不满足这些范围输出单独一行 `ERROR`。

另外明确拒绝无法在本协议中解析的极限：将SG系数装成三对角矩阵，主对角为 `b_left+a_right+k*w`，下对角为`-a_left`，上对角为`-b_right`。从左到右消元，每个更新后主元须有限且大于1e-280；否则输出ERROR。所得密度须有限、非负且≤1e100，否则也输出ERROR。此项是公开的计算域判据，不宣称连续方程无解。强烈向内漂移且无衰减时，指数下溢可使矩阵丢失可解析主元，不应返回NaN或伪造零残差。合法测试解的原始残差可在给定精度内解析。

## 输出和自动评分

成功输出3行：`density[N]`；`flux[N-1]`；`mass residual_inf`。用real64、至少16位有效数字，不输出提示文字。错误仅输出ERROR并正常退出。无外部库、文件或网络。

编译：`gfortran -std=f2008 -O2 -fcheck=all -ffree-line-length-none solution.f90 -o solver`。每个案例运行限30秒，整次执行含编译默认120秒；用户设置的更短预算优先。评分器独立从返回密度重建通量、积分及守恒残差。数值比较为`|a-e|≤2e-8+2e-8*|e|`；原始残差与所报残差均不得超过2e-8。错误输入检查也是自动检查。

基础/科学/边界检查相对权重20/30/20；百分制为通过权重/70×100。全部通过才标passed，部分通过保留部分分。编译错误或运行错误计对应失败；编译器/容器缺失为unscored，不记模型0分。候选只获得本题文件，不访问验证器或参考解。

## 可见输入示例

以下JSON说明输入映射，实际程序使用上述7行stdin协议；它不是要求解析JSON。

```json
'''+json.dumps(p, ensure_ascii=False, indent=2)+'''
```

设计难度3/5，尚未由真实模型成绩标定。方法来源：Scharfetter & Gummel (1969), DOI https://doi.org/10.1109/T-ED.1969.16566；NIST Sesame离散化文档 https://sesame.readthedocs.io/en/latest/physics/discretization.html 。势号与流号以本题为准。
'''


def reference_submission(seed=17):
    return {"task_id": "F01", "answer": {}, "artifacts": {"solution.f90": FORTRAN}}


def mutants(seed=17):
    variants = {
        "central_drift": FORTRAN.replace("a(i)=d(i)/h(i)*bern(-z)", "a(i)=d(i)/h(i)+v(i)/2").replace("b(i)=d(i)/h(i)*bern(z)", "b(i)=d(i)/h(i)-v(i)/2"),
        "uniform_control_volume": FORTRAN.replace("w=(h(1:n-2)+h(2:n-1))/2", "w=h(1)"),
        "wrong_right_boundary": FORTRAN.replace("rhs(n-2)=rhs(n-2)+b(n-1)*right", "rhs(n-2)=rhs(n-2)+a(n-1)*right"),
        "reversed_velocity": FORTRAN.replace("z=v(i)*h(i)/d(i)", "z=-v(i)*h(i)/d(i)"),
    }
    return {"reference": reference_submission(seed), **{
        k: {"task_id": "F01", "answer": {}, "artifacts": {"solution.f90": src}} for k, src in variants.items()}}

"""F03: actual positive roots of a bounded nonlinear DD--Poisson system."""
from __future__ import annotations

import copy
import json
import math
import random
from nrb_v1.tasks import c09 as legacy

TASK = {**legacy.TASK, "id": "F03", "title": "Fortran 自洽漂移扩散–Poisson",
        "required_artifacts": ["solution.f90"], "manual_review_required": False,
        "scoring": "automatic", "max_score": 100}
TASK.pop("essential", None)

FORTRAN = legacy.FORTRAN.replace(
    "if(lam2<=0) call fail()", "if(lam2<.035_real64.or.lam2>4._real64) call fail()").replace(
    "m=2*(n-2);h=1._real64/(n-1)", "m=2*(n-2);h=1._real64/(n-1)").replace(
    "if(.not.all(ieee_is_finite([pl,pr,nl,nr])).or.nl<=0.or.nr<=0) call fail()",
    """if(.not.all(ieee_is_finite([pl,pr,nl,nr]))) call fail()
if(abs(pl)>8.or.abs(pr)>8.or.nl<.2_real64.or.nr<.2_real64.or.nl>3.or.nr>3) call fail()""").replace(
    "if(.not.all(ieee_is_finite(diffusion)).or.any(diffusion<=0)) call fail()",
    "if(.not.all(ieee_is_finite(diffusion)).or.any(diffusion<.5_real64).or.any(diffusion>1.5_real64)) call fail()").replace(
    "if(.not.all(ieee_is_finite(charge)).or..not.all(ieee_is_finite(source))) call fail()",
    """if(.not.all(ieee_is_finite(charge)).or..not.all(ieee_is_finite(source))) call fail()
if(any(abs(charge)>100).or.any(abs(source)>1000)) call fail()""")

fortran_input = legacy.fortran_input
parse_fortran = legacy.parse_fortran
validate_output = legacy.validate_output


def cases(seed=17):
    old = legacy.cases(seed)
    out = copy.deepcopy(old[:5])
    out.append(dict(copy.deepcopy(old[5]), weight=6))
    out.append(dict(copy.deepcopy(old[6]), weight=4))
    rng = random.Random(seed + 30303)
    n=65; x=[i/(n-1) for i in range(n)]
    shift=-3.0-rng.random()
    phi=[shift+.35*t+.15*math.sin(2*math.pi*t) for t in x]
    density=[1+.18*math.cos(math.pi*t)+.06*math.sin(3*math.pi*t) for t in x]
    d=[.5+rng.random() for _ in range(n-1)]
    p,e=legacy._manufactured(phi,density,d,.04)
    out.append(dict(id="maximum_grid_negative_gauge",tier="stress",input=p,expected=e,
                    weight=4,critical=True,rtol=3e-7,atol=8e-8))
    for cid,key,value in [
        ("reject_unsupported_screening","lambda_squared",.001),
        ("reject_zero_contact_density","density_right",0.0),
        ("reject_diffusion_outside_domain","diffusion",[.1]*(n-1)),
    ]:
        bad=copy.deepcopy(p);bad[key]=value
        out.append(dict(id=cid,tier="stress",input=bad,error="ValueError",weight=2,
                        critical=True,rtol=3e-7,atol=8e-8))
    return out


def prompt(seed=17):
    example = next(c["input"] for c in cases(seed) if c["id"] == "coupled_manufactured_sources")
    return '''# F03 · Fortran 自洽单载流子漂移扩散–Poisson

编写标准Fortran 2008单文件程序 `solution.f90`，求解下列明确有限的非线性离散系统。只提交完整源码，说明和自测可选，不设人工分。这是公开经典方法的原创合成题，不要求建立真实器件模拟器。

## 方程和符号

所有量无量纲。x∈[0,1]均匀N节点，h=1/(N-1)；势ψ以热电压归一化，n以参考浓度归一化，D以参考扩散系数归一化，lambda_squared是归一化屏蔽长度的平方。

```
B(z)=z/(exp(z)-1), B(0)=1
Δψ_i=ψ_(i+1)-ψ_i
J_i=(D_i/h)[B(-Δψ_i)*n_i-B(Δψ_i)*n_(i+1)]
Rψ_i=lambda_squared*(2ψ_i-ψ_(i-1)-ψ_(i+1))/h²+n_i-charge_i
Rn_i=(J_i-J_(i-1))/h-source_i
```

两个内部残差必须同时为零。charge是有符号固定背景，source是有符号净产生；不要擅自取绝对值、截断或增加复合。ψ与n在左右端分别给定Dirichlet值。成功解必须有严格正密度；可以使用log(n)、阻尼Newton或其他实际收敛方法。不能用冻结电势、强制n=charge、输出裁剪或把残差写成0代替自洽求解。

## 有限测试域

N为4至65的整数，0.035≤lambda_squared≤4，0.5≤D_i≤1.5，0.2≤两端密度≤3，|两端势|≤8，|charge_i|≤100，|source_i|≤1000，所有值有限。违反这些范围输出ERROR。测试按指定长度提供数组。合法测试族由平衡或光滑离散制造解生成，保证存在内部|ψ|≤8、0.2≤n≤3的正解；不要求处理无正解、分岔或此域外问题。若迭代失败必须输出ERROR，不能把未收敛结果当成功。

本题不主张非线性系统全局唯一，也不只认一个参考解：任何满足边界、严格正性、原始两组残差和SG通量的一致正解均可得分。对势整体加常数、同时平移两端势，不改变密度和边通量；两端Dirichlet条件已固定规范，不能额外将左端势强制为0。符号完全按本题定义。

## 输入输出

stdin为5行：

1. `N lambda_squared`
2. `potential_left potential_right density_left density_right`
3. `diffusion[N-1]`
4. `charge[N-2]`
5. `source[N-2]`

成功stdout为4行：`potential[N]`；`density[N]`；`flux[N-1]`；`residual_inf`。residual_inf为原始Rψ和Rn中绝对值的最大值。失败只输出单独ERROR并正常退出。使用real64，至少16位有效数字，无提示文字、外部库、网络或输入外文件。

编译选项：`gfortran -std=f2008 -O2 -fcheck=all -ffree-line-length-none`。每个案例最多30秒，整次执行含编译默认120秒；用户设置的更短预算优先。

## 自动判据

评分器从返回ψ和n独立重算通量、泊松残差和连续性残差。边界和通量采用`|actual-expected|≤8e-8+3e-7*|expected|`，重算原始残差必须≤8e-8；所报残差必须非负、≤8e-8，并与重算值相容。n必须严格为正。测试同时包含平衡零流、带流状态、异质D、非零净源、规范平移、N=65以及域外拒绝。

基础/科学/边界相对权重20/30/20，百分制为通过权重/70×100。没有人工分。全部检查通过才标passed；编译/运行错误为失败，编译器或容器缺失为unscored。候选只接收本题，不接收评分器和参考解。

## 可见输入示例

以下JSON仅说明stdin的映射，不要求程序解析JSON，不提供正确输出。

```json
'''+json.dumps(example,ensure_ascii=False,indent=2)+'''
```

设计难度5/5，尚未由真实模型成绩标定。方法来源：Scharfetter & Gummel (1969), https://doi.org/10.1109/T-ED.1969.16566；NIST Sesame离散化文档 https://sesame.readthedocs.io/en/latest/physics/discretization.html 。
'''


def reference_submission(seed=17):
    return {"task_id":"F03","answer":{},"artifacts":{"solution.f90":FORTRAN}}


def mutants(seed=17):
    variants={
        "wrong_poisson_mesh_scale":FORTRAN.replace("a=lam2/(h*h)","a=lam2/h"),
        "remove_gauge_boundary":FORTRAN.replace("p(1)=pl;p(n)=pr;den(1)=nl;den(n)=nr","p(1)=0;p(n)=pr-pl;den(1)=nl;den(n)=nr"),
        "drift_sign_reversal":FORTRAN.replace("dz=p(ii+1)-p(ii)","dz=p(ii)-p(ii+1)").replace("dz=p(edge+1)-p(edge)","dz=p(edge)-p(edge+1)").replace("dr=diffusion(edge)/h*(-dbern(-dz)*den(edge)-dbern(dz)*den(edge+1))","dr=-diffusion(edge)/h*(-dbern(-dz)*den(edge)-dbern(dz)*den(edge+1))"),
        "discard_net_source":FORTRAN.replace("do i=2,n-1\n q=", "source=0\ndo i=2,n-1\n q="),
    }
    return {"reference":reference_submission(seed),**{
        k:{"task_id":"F03","answer":{},"artifacts":{"solution.f90":src}} for k,src in variants.items()}}

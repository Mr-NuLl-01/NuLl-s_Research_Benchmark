"""V2 repair: optimize the entire unimodal closed interval, including end basins."""
from __future__ import annotations

import copy
import math
from nrb_v1.tasks import c07 as old

TASK = dict(old.TASK, id="P06", required_artifacts=["solution.py"])

_old_search = old.SOLUTION[old.SOLUTION.index("    # Search all local basins"):old.SOLUTION.index("    parts=[_project")]
_new_search = '''    # The contract's nonflat profile is unimodal on the WHOLE interval.
    # The coverage grid defines only the numerical flatness convention.
    grid=[lo+(hi-lo)*i/256 for i in range(257)]
    vals=[profile(d) for d in grid]
    flat=max(vals)-min(vals)<=1e-16*max(1.,max(vals))
    if flat:
        best=lo
    else:
        ratio=(math.sqrt(5)-1)/2
        a,b=lo,hi
        c=b-ratio*(b-a);d=a+ratio*(b-a)
        fc,fd=profile(c),profile(d)
        for _ in range(110):
            if fc<fd:
                b,d,fd=d,c,fc;c=b-ratio*(b-a);fc=profile(c)
            else:
                a,c,fc=c,d,fd;d=a+ratio*(b-a);fd=profile(d)
        dh=(a+b)/2
        best=min((profile(lo),lo),(profile(hi),hi),(profile(dh),dh))[1]
'''
SOLUTION = old.SOLUTION.replace(_old_search, _new_search)


def _solve(p):
    ns={};exec(SOLUTION,ns);return ns["solve"](p)


def cases(seed=17):
    result=copy.deepcopy(old.cases(seed))
    for case in result:
        if "expected" in case:case["expected"]=_solve(case["input"])
        if case["id"] in ("structurally_flat","weak_full_interval"):case["weight"]=2
        if case["id"] in ("reject_zero_sigma", "reject_unresolved_times"):case["weight"]=2
    # Three distinct times alone do not guarantee a numerically resolved
    # exp(-D lambda t) / baseline design. This explicit domain rule is public.
    unresolved=dict(length=1.,bounds=[.01,.2],delta_chi2=3.841458820694124,
                    experiments=[dict(time=[0.,1e-15,2e-15,3e-15], value=[.8]*4, sigma=[.01]*4)])
    result.append(dict(id="reject_unresolved_nuisance",tier="stress",input=unresolved,
                       error="ValueError",weight=2,critical=True,rtol=0,atol=0))
    lo,hi=.015,.4
    for label,d in (("lower_endpoint_interior_minimum",lo+(hi-lo)*1e-4),
                    ("upper_endpoint_interior_minimum",hi-(hi-lo)*1e-4)):
        times=[0,.12,.35,.75,1.3,2.1,3.4,5,7,9]
        p=dict(length=2.3,bounds=[lo,hi],delta_chi2=3.841458820694124,
               experiments=[dict(time=times,value=[.4+1.2*math.exp(-d*math.pi**2*t/2.3**2) for t in times],sigma=[.004]*len(times))])
        result.append(dict(id=label,tier="stress",input=p,expected=_solve(p),weight=5,critical=True,rtol=3e-6,atol=2e-7))
    return result


def reference_submission(seed=17):
    return dict(task_id="P06",artifacts={"solution.py":SOLUTION},answer={})


def mutants(seed=17):
    result={"reference":reference_submission(seed)}
    replacements={
        "discard_baseline": ("baseline=my-amplitude*mx","baseline=0.0"),
        "ignore_sigma": ("w=[1/(v*v) for v in sigma]","w=[1.0 for v in sigma]"),
        "conditional_information": ("information=math.fsum(a*(b-md-slope*(c-mx))**2 for a,b,c in zip(w,derivative,x))", "information=math.fsum(a*b*b for a,b in zip(w,derivative))"),
    }
    for label,(a,b) in replacements.items():
        result[label]=dict(task_id="P06",artifacts={"solution.py":SOLUTION.replace(a,b)},answer={})
    result["legacy_grid_misses_endpoint_minimum"]=dict(task_id="P06",artifacts={"solution.py":old.SOLUTION},answer={})
    return result


def prompt(seed=17):
    text=old.prompt(seed)
    text=text.replace("测试族的非平坦剖面只有一个局部极小。", "测试族的非平坦剖面在整个闭区间上先不增后不减，最小区域唯一（允许数值平台）。内部最优点可能任意接近两个端点；不能只细化网格内点的局部最小。")
    text=text.replace("若剖面数值平坦（全范围χ²差≤1e-16*max(1,maxχ²)）", "若剖面数值平坦（在含两端点的257个等间距D探针上，χ²差≤1e-16*max(1,maxχ²)）")
    return text+"\n\nV2 修订：固定探针只定义平坦判据，不限定优化搜索区间。评测包含位于边界附近的内部真值；闭区间全局最小与端点候选都必须正确处理。\n\n数值定义域：令w_i=1/sigma_i²，x_i=exp[-D(pi/L)²t_i]，mx=Σw_i x_i/Σw_i。对数值可解的线性幅度/基线设计，要求Σw_i(x_i-mx)² > 1e-26 Σw_i；若任一实验在257个含端点等间距探针或优化/区间求值时违反此条件，则抛ValueError。常数观测y但设计满秩时仍是合法不可识别案例，不能仅因y常数就拒绝。\n"


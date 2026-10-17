"""NRB04: conservative diffusion on a nonuniform finite-volume mesh.

All examples are generated, dimensionless classroom heat-transport problems.
The grader's matrix assembly and the submitted reference's face-flux update
are separate implementations of the same public contract.
"""

from __future__ import annotations

import copy
import json
import math
import random

from nrb.checks import check, numbers_close
from nrb.execution import run_python


REFERENCE_SOURCE = '''import math

def solve(payload):
    def finite_number(value):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return False
        try:
            return math.isfinite(value)
        except OverflowError:
            return False
    edges = payload.get("edges", [])
    if not isinstance(edges, list) or len(edges) < 2 or not all(finite_number(x) for x in edges):
        raise ValueError("edges must contain at least two finite numbers")
    n = len(edges) - 1
    widths = [edges[i+1] - edges[i] for i in range(n)]
    if min(widths) <= 0:
        raise ValueError("edges must strictly increase")
    arrays = {}
    for key in ("conductivity", "capacity", "temperature", "source"):
        arr = payload.get(key)
        if not isinstance(arr, list) or len(arr) != n or not all(finite_number(x) for x in arr):
            raise ValueError("cell arrays must have equal length and finite numbers")
        arrays[key] = arr[:]
    k, c = arrays["conductivity"], arrays["capacity"]
    if min(k) <= 0 or min(c) <= 0:
        raise ValueError("conductivity and capacity must be positive")
    dt, steps = payload.get("dt"), payload.get("steps")
    if not finite_number(dt) or dt <= 0 or not isinstance(steps, int) or isinstance(steps, bool) or steps < 0:
        raise ValueError("invalid dt or steps")
    boundaries = [payload.get("left"), payload.get("right")]
    for bc in boundaries:
        if not isinstance(bc, dict) or bc.get("kind") not in ("flux", "temperature") or not finite_number(bc.get("value")):
            raise ValueError("invalid boundary")
    left, right = boundaries
    conductance = [1.0 / (widths[i]/(2*k[i]) + widths[i+1]/(2*k[i+1])) for i in range(n-1)]
    boundary_g = [2*k[0]/widths[0] if left["kind"] == "temperature" else 0.0,
                  2*k[-1]/widths[-1] if right["kind"] == "temperature" else 0.0]
    cap = [c[i]*widths[i] for i in range(n)]
    out_g = [0.0]*n
    out_g[0] += boundary_g[0]
    out_g[-1] += boundary_g[1]
    for i, g in enumerate(conductance):
        out_g[i] += g
        out_g[i+1] += g
    dt_bound = min((cap[i]/out_g[i] for i in range(n) if out_g[i] > 0), default=math.inf)
    if dt > dt_bound*(1+1e-12):
        raise ValueError("explicit positivity stability bound exceeded")
    def flux(u):
        q_left = left["value"] if left["kind"] == "flux" else boundary_g[0]*(left["value"]-u[0])
        q_right = right["value"] if right["kind"] == "flux" else boundary_g[1]*(u[-1]-right["value"])
        return [q_left] + [g*(u[i]-u[i+1]) for i, g in enumerate(conductance)] + [q_right]
    u = arrays["temperature"]
    energy_initial = sum(a*b for a, b in zip(cap, u))
    energy_input = 0.0
    total_source = sum(widths[i]*arrays["source"][i] for i in range(n))
    for _ in range(steps):
        q = flux(u)
        energy_input += dt*(q[0]-q[-1]+total_source)
        u = [u[i] + dt*(q[i]-q[i+1]+widths[i]*arrays["source"][i])/cap[i] for i in range(n)]
    return {"temperature": u, "face_flux": flux(u),
            "energy_initial": energy_initial,
            "energy_final": sum(a*b for a, b in zip(cap, u)),
            "energy_input": energy_input}
'''


STARTER_SOURCE = '''def solve(payload):
    # This starter is deliberately wrong; repair the numerical method and validation.
    edges = payload["edges"]
    n = len(edges)-1
    dx = (edges[-1]-edges[0])/n
    u = payload["temperature"][:]
    old_energy = sum(u)*dx
    for _ in range(payload["steps"]):
        q = [payload["left"]["value"]]
        for i in range(n-1):
            k = (payload["conductivity"][i]+payload["conductivity"][i+1])/2
            q.append(k*(u[i]-u[i+1])/dx)
        q.append(payload["right"]["value"])
        for i in range(n):
            u[i] += payload["dt"]*(q[i]-q[i+1]+payload["source"][i])/dx
    return {"temperature": u, "face_flux": q, "energy_initial": old_energy,
            "energy_final": sum(u)*dx, "energy_input": 0.0}
'''


def _conductances(p):
    h = [b-a for a, b in zip(p["edges"], p["edges"][1:])]
    internal = [2.0/(h[i]/p["conductivity"][i] + h[i+1]/p["conductivity"][i+1]) for i in range(len(h)-1)]
    gl = 2*p["conductivity"][0]/h[0] if p["left"]["kind"] == "temperature" else 0.0
    gr = 2*p["conductivity"][-1]/h[-1] if p["right"]["kind"] == "temperature" else 0.0
    return h, internal, gl, gr


def _stability_limit(p):
    h, g, gl, gr = _conductances(p)
    outgoing = [0.0]*len(h)
    outgoing[0] += gl
    outgoing[-1] += gr
    for i, value in enumerate(g):
        outgoing[i] += value
        outgoing[i+1] += value
    return min((p["capacity"][i]*h[i]/value for i, value in enumerate(outgoing) if value), default=math.inf)


def _oracle(p):
    """Assemble the linear operator; do not call the reference source."""
    h, g, gl, gr = _conductances(p)
    n = len(h)
    cap = [p["capacity"][i]*h[i] for i in range(n)]
    a = [[0.0]*n for _ in range(n)]
    b = [p["source"][i]*h[i] for i in range(n)]
    for i, value in enumerate(g):
        a[i][i] -= value
        a[i+1][i+1] -= value
        a[i][i+1] += value
        a[i+1][i] += value
    if p["left"]["kind"] == "temperature":
        a[0][0] -= gl
        b[0] += gl*p["left"]["value"]
    else:
        b[0] += p["left"]["value"]
    if p["right"]["kind"] == "temperature":
        a[-1][-1] -= gr
        b[-1] += gr*p["right"]["value"]
    else:
        b[-1] -= p["right"]["value"]
    u = list(p["temperature"])
    e0 = math.fsum(x*y for x, y in zip(cap, u))
    energy_input = 0.0
    for _ in range(p["steps"]):
        rates = [math.fsum(a[i][j]*u[j] for j in range(n))+b[i] for i in range(n)]
        energy_input += p["dt"]*math.fsum(rates)
        u = [u[i]+p["dt"]*rates[i]/cap[i] for i in range(n)]
    ql = p["left"]["value"] if not gl else gl*(p["left"]["value"]-u[0])
    qr = p["right"]["value"] if not gr else gr*(u[-1]-p["right"]["value"])
    return {"temperature": u,
            "face_flux": [ql]+[value*(u[i]-u[i+1]) for i, value in enumerate(g)]+[qr],
            "energy_initial": e0,
            "energy_final": math.fsum(x*y for x, y in zip(cap, u)),
            "energy_input": energy_input}


def _generated(rng, n=4, left="flux", right="flux"):
    edges = [0.0]
    for _ in range(n):
        edges.append(edges[-1]+rng.uniform(0.12, 0.83))
    p = {"edges": edges,
         "conductivity": [10**rng.uniform(-0.8, 0.8) for _ in range(n)],
         "capacity": [rng.uniform(0.7, 2.4) for _ in range(n)],
         "temperature": [rng.uniform(1.0, 3.5) for _ in range(n)],
         "source": [rng.uniform(-0.1, 0.4) for _ in range(n)],
         "left": {"kind": left, "value": rng.uniform(0.1, 0.6)},
         "right": {"kind": right, "value": rng.uniform(0.05, 0.3)},
         "steps": rng.randint(2, 8)}
    bound = _stability_limit(p)
    p["dt"] = 0.37*bound if math.isfinite(bound) else 0.03
    return p


def _hidden_with_groups(seed):
    rng = random.Random(f"NRB04:hidden:{seed}")
    cases = []
    p = _generated(rng, 5)
    p["source"] = [0.0]*5
    p["left"]["value"] = p["right"]["value"] = 0.0
    cases.append(("insulated_nonuniform", p, "ok"))
    p = _generated(rng, 4)
    p["conductivity"] = [0.03, 11.0, 0.08, 4.0]
    p["dt"] = 0.29*_stability_limit(p)
    cases.append(("discontinuous_conductivity", p, "ok"))
    cases.append(("flux_source_capacity", _generated(rng, 3), "ok"))
    cases.append(("two_temperature_boundaries", _generated(rng, 5, "temperature", "temperature"), "ok"))
    cases.append(("mixed_boundary", _generated(rng, 4, "flux", "temperature"), "ok"))
    p = _generated(rng, 1)
    cases.append(("one_cell_flux", p, "ok"))
    p = _generated(rng, 3, "temperature", "flux")
    p["steps"] = 0
    cases.append(("zero_step_flux_at_initial_state", p, "ok"))
    p = _generated(rng, 3)
    p["edges"][1] = p["edges"][0]
    cases.append(("reject_nonincreasing_edges", p, "ValueError"))
    p = _generated(rng, 3)
    p["capacity"][1] = -0.5
    cases.append(("reject_invalid_capacity", p, "ValueError"))
    p = _generated(rng, 4, "temperature", "temperature")
    p["dt"] = 1.4*_stability_limit(p)
    cases.append(("reject_unstable_step", p, "ValueError"))

    # The harness materializes these JSON-safe descriptors only inside the
    # candidate process, so strict JSON transport and execution remain intact.
    def extra(name, field, value, group):
        item = _generated(rng, 3)
        if isinstance(field, tuple):
            item[field[0]][field[1]] = value
        else:
            item[field] = value
        cases.append((name, item, "ValueError"))
        members[group].append(name)

    members = {name: [name] for name, _, _ in cases}
    for boundary in ("left", "right", "both"):
        p = _generated(rng, 1,
                       "temperature" if boundary in ("left", "both") else "flux",
                       "temperature" if boundary in ("right", "both") else "flux")
        name = "one_cell_temperature_" + boundary
        cases.append((name, p, "ok"))
        members["two_temperature_boundaries"].append(name)
    for value, tag in ((0.0, "zero"), (-1.0, "negative")):
        extra("reject_"+tag+"_conductivity", ("conductivity", 1), value, "discontinuous_conductivity")
    for key in ("edges", "conductivity", "capacity", "temperature", "source"):
        group = "reject_nonincreasing_edges" if key == "edges" else "reject_invalid_capacity"
        extra("reject_boolean_"+key, (key, 1), True, group)
        for token in ("nan", "inf", "-inf"):
            extra("reject_"+token+"_"+key, (key, 1), {"__nrb_float__": token}, group)
        extra("reject_nonlist_"+key, key, "not a list", group)
        if key != "edges":
            extra("reject_short_"+key, key, [1.0, 1.0], group)
            extra("reject_long_"+key, key, [1.0]*4, group)
    extra("reject_too_few_edges", "edges", [0.0], "reject_nonincreasing_edges")
    for boundary in ("left", "right"):
        for value, tag in ((None, "object"), ({"kind": "unknown", "value": 0.0}, "kind"),
                           ({"kind": "flux"}, "missing_value"),
                           ({"kind": "flux", "value": True}, "boolean_value")):
            extra("reject_"+boundary+"_"+tag, boundary, value, "mixed_boundary")
        for token in ("nan", "inf", "-inf"):
            extra("reject_"+boundary+"_"+token, boundary,
                  {"kind": "temperature", "value": {"__nrb_float__": token}}, "mixed_boundary")
    for value, tag in ((True, "boolean"), (1.0, "float"), (-1, "negative"), ("2", "string")):
        extra("reject_"+tag+"_steps", "steps", value, "zero_step_flux_at_initial_state")
    for token in ("nan", "inf", "-inf"):
        extra("reject_"+token+"_steps", "steps", {"__nrb_float__": token}, "zero_step_flux_at_initial_state")
    extra("reject_zero_capacity", ("capacity", 1), 0.0, "reject_invalid_capacity")
    for value, tag in ((True, "boolean"), (0.0, "zero"), (-0.1, "negative")):
        extra("reject_"+tag+"_dt", "dt", value, "reject_unstable_step")
    for token in ("nan", "inf", "-inf"):
        extra("reject_"+token+"_dt", "dt", {"__nrb_float__": token}, "reject_unstable_step")
    p = _generated(rng, 1, "temperature", "temperature")
    p["dt"], p["steps"] = 1.4*_stability_limit(p), 0
    name = "reject_unstable_zero_step_single_cell"
    cases.append((name, p, "ValueError"))
    members["reject_unstable_step"].append(name)
    # A single cell has two independent half-cell boundary conductances.
    p = {"edges": [0.0, 2.0], "conductivity": [4.0], "capacity": [3.0],
         "temperature": [5.0], "source": [2.0], "steps": 1,
         "left": {"kind": "temperature", "value": 1.0},
         "right": {"kind": "temperature", "value": 7.0}}
    threshold = 0.75*(1.0+1e-12)
    for dt, name, state in ((threshold, "stability_threshold_inclusive", "ok"),
                             (math.nextafter(threshold, math.inf), "reject_above_stability_threshold", "ValueError")):
        item = copy.deepcopy(p)
        item["dt"] = dt
        cases.append((name, item, state))
        members["reject_unstable_step"].append(name)
    return cases, members


def _hidden(seed):
    return _hidden_with_groups(seed)[0]


def build(seed=0):
    rng = random.Random(f"NRB04:visible:{seed}")
    visible = _generated(rng, rng.randint(3, 5), "temperature", "flux")
    hidden, hidden_groups = _hidden_with_groups(seed)
    contract = """# Public API: scalar heat transport

All quantities are dimensionless synthetic classroom values; cross-section is 1.
`solve(payload)` receives JSON: edges[n+1], conductivity[n] > 0,
capacity[n] > 0 (volumetric), temperature[n], source[n] (per unit volume),
dt > 0, integer steps >= 0, and left/right boundary objects.
Each boundary is {"kind": "flux" | "temperature", "value": finite_number}.
A numeric input is a Python int or float representable as a finite binary64
value; bool is excluded. Numeric strings are invalid. IEEE NaN and both
infinities are invalid, including direct Python API calls (JSON transport itself
remains strict). Edges strictly increase; arrays must be lists with the specified
length. steps must have Python int type, so 1.0 and True are invalid step counts.
Raise ValueError for invalid inputs or violation of the stability bound below.

Let h_i=edges[i+1]-edges[i]. For a face between i and i+1,
g=1/(h_i/(2*k_i)+h_(i+1)/(2*k_(i+1))), and q=g*(u_i-u_(i+1)).
Every q, including prescribed boundary fluxes, is positive toward increasing x.
Temperature boundaries are at the domain face, a half-cell from the cell center:
q_left=2*k_0/h_0*(T_left-u_0), q_right=2*k_last/h_last*(u_last-T_right).
The update is simultaneous forward Euler:
u_i(new)=u_i+dt*(q_i-q_(i+1)+source_i*h_i)/(capacity_i*h_i).
Use the old state for every flux in a step.

Reject dt > (1+1e-12)*min_i(capacity_i*h_i/sum_g_i), where sum_g_i is
the sum of state-dependent conductances leaving that cell. Prescribed-flux
boundaries contribute zero; cells with sum_g_i=0 place no restriction.
Validate this bound even if steps=0.

Return exactly the physically defined fields (extra fields are ignored):
temperature[n], face_flux[n+1] evaluated at the FINAL state,
energy_initial, energy_final, energy_input.
Energy is sum(capacity_i*h_i*u_i); energy_input is the sum over steps of
dt*(q_left-q_right+sum(source_i*h_i)), using that step's old-state fluxes.
steps=0 must return unchanged temperatures and zero energy_input.
Only Python standard library modules are available.
"""
    prompt = """你接手一段一维热扩散教学程序。网格不均匀，各单元的导热率和体积热容不同。
输入均为本测试生成的无量纲数据。请依据 API.md，以只读的 starter.py 为起点，在新的 solution.py 中实现修复；说明守恒关系、界面串联热阻、
边界通量方向、显式步长限制，以及你实际执行了哪些验证。不要把数值例子描述为实验数据。

必须返回 JSON 外层 {"task_id":"NRB04","answer":{"visible_result":{"temperature":[number],
"face_flux":[number],"energy_initial":number,"energy_final":number,"energy_input":number}},
"artifacts":{"solution.py":"完整 Python 源码字符串","reasoning.md":"推导与实际验证说明"}}。
visible_result 是 input.json 的结果；数组长度须遵循该输入。solution.py 必须提供 solve(payload)。
评分会在未展示的有效与无效输入上运行代码。推导质量另按人工量规评分。"""
    return {"id": "NRB04", "seed": seed, "title": "非均匀网格上的守恒热扩散修复", "domain": "numerical-code-repair",
            "prompt": prompt,
            "files": {"API.md": contract, "input.json": json.dumps(visible, indent=2), "starter.py": STARTER_SOURCE},
            "expected": {"visible": _oracle(visible), "hidden": hidden, "hidden_groups": hidden_groups},
            "rubric": [
                {"id": "derivation", "title": "离散物理与误差解释", "anchors": {"0": "没有推导，或守恒/边界方向解释错误。", "5": "说明主要离散关系，但未清楚区分导热率、单元热容量及边界距离。", "10": "从单元热量平衡推导面热阻、源项、边界方向和非负权重步长条件，明确时间/空间离散误差。"}},
                {"id": "verification", "title": "有效验证与执行诚实性", "anchors": {"0": "无可核验验证，或把未执行测试写成已通过。", "5": "展示一个有效守恒或解析例，并准确说明执行范围。", "10": "使用机制不同的例子检验守恒、异质界面、边界条件及拒绝非法输入；给出可复现命令/结果并如实说明范围。"}},
                {"id": "maintainability", "title": "代码可维护性", "anchors": {"0": "代码不可读或仅硬编码可见输出。", "5": "功能结构可读，存在冗余或输入异常说明不足。", "10": "接口、验证、通量和更新分工清楚，简洁且可扩展；说明具体已修复缺陷，无不必要依赖。"}}]}


def reference(case):
    return {"task_id": "NRB04", "answer": {"visible_result": copy.deepcopy(case["expected"]["visible"])},
            "artifacts": {"solution.py": REFERENCE_SOURCE,
                          "reasoning.md": "参考实现按面串联热阻计算通量，并同步更新单元热量。每步内通量成对抵消，热量改变量等于边界输入加体积源项。步长由更新矩阵非负对角权重限制。参考输出是生成器的矩阵离散计算；运行记录由测试运行器单独产生，本文件不声称任何外部执行。"}}


def _batch_source(source):
    return source + '''

_nrb_original_solve = solve
def _nrb_materialize(value):
    if isinstance(value, dict):
        if set(value) == {"__nrb_float__"}:
            return float(value["__nrb_float__"])
        return {key: _nrb_materialize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_nrb_materialize(item) for item in value]
    return value

def solve(payload):
    results = []
    for item in payload["nrb_cases"]:
        try:
            results.append({"status": "ok", "result": _nrb_original_solve(_nrb_materialize(item))})
        except Exception as exc:
            results.append({"status": "error", "type": type(exc).__name__})
    return {"nrb_results": results}
'''


def grade(case, submission, execution="none"):
    ans = submission.get("answer", {}) if isinstance(submission, dict) else {}
    ans = ans if isinstance(ans, dict) else {}
    actual = ans.get("visible_result", {})
    actual = actual if isinstance(actual, dict) else {}
    wanted = case["expected"]["visible"]
    results = [check("visible_temperature", 8, numbers_close(actual.get("temperature"), wanted["temperature"]), "可见输入的最终单元温度。"),
               check("visible_face_flux", 4, numbers_close(actual.get("face_flux"), wanted["face_flux"]), "最终状态面通量；并非最后一次更新前的旧通量。"),
               check("visible_initial_energy", 4, numbers_close(actual.get("energy_initial"), wanted["energy_initial"]), "按体积热容与单元宽度积分。"),
               check("visible_energy_balance", 4, numbers_close({key: actual.get(key) for key in ("energy_final", "energy_input")}, {key: wanted[key] for key in ("energy_final", "energy_input")}), "最终热量及累积外部输入。", critical=True)]
    artifacts = submission.get("artifacts", {}) if isinstance(submission, dict) else {}
    source = artifacts.get("solution.py") if isinstance(artifacts, dict) else None
    hidden = case["expected"]["hidden"]
    groups = case["expected"]["hidden_groups"]
    critical = {"insulated_nonuniform", "flux_source_capacity"}
    if not isinstance(source, str) or not source.strip():
        return results + [check(name, 5, False, "缺少 solution.py。", critical=name in critical) for name in groups]
    run = run_python(_batch_source(source), {"nrb_cases": [p for _, p, _ in hidden]}, execution=execution, timeout=5)
    if run.get("status") == "unavailable":
        return results + [check(name, 5, None, run.get("detail", "未启用代码执行；此项未评。"), critical=name in critical) for name in groups]
    output = run.get("result")
    batch = output.get("nrb_results") if isinstance(output, dict) else None
    outcomes = {}
    for i, (name, p, state) in enumerate(hidden):
        observed = batch[i] if isinstance(batch, list) and i < len(batch) and isinstance(batch[i], dict) else {}
        if state == "ValueError":
            passed = observed.get("status") == "error" and observed.get("type") == "ValueError"
        else:
            result = observed.get("result")
            oracle = _oracle(p)
            passed = observed.get("status") == "ok" and isinstance(result, dict) and numbers_close({key: result.get(key) for key in oracle}, oracle)
        outcomes[name] = passed
    for name, members in groups.items():
        failed = [member for member in members if not outcomes[member]]
        detail = "组内逐例核对；失败案例：" + (", ".join(failed) if failed else "无")
        if run.get("status") != "ok":
            detail += "；" + run.get("detail", "代码执行失败。")
        row = check(name, 5, not failed, detail, critical=name in critical)
        row["cases"] = [{"id": member, "passed": outcomes[member]} for member in members]
        results.append(row)
    return results

"""NRB05: deterministic adaptive backward-Euler scheduling for test ODEs."""

from __future__ import annotations

import copy
from decimal import Decimal, localcontext
import json
import random

from nrb.checks import check, numbers_close
from nrb.execution import run_python


REFERENCE_SOURCE = '''import math

def solve(payload):
    def number(x):
        return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)
    y0 = payload.get("y0")
    if number(y0):
        y = [float(y0)]
    elif isinstance(y0, list) and y0 and all(number(x) for x in y0):
        y = [float(x) for x in y0]
    else:
        raise ValueError("invalid y0")
    n = len(y)
    def vector(key):
        value = payload.get(key)
        if number(value):
            return [float(value)]*n
        if isinstance(value, list) and len(value) == n and all(number(x) for x in value):
            return [float(x) for x in value]
        raise ValueError("invalid vector: " + key)
    rates, atol, rtol, floor = [vector(key) for key in ("rates", "atol", "rtol", "scale_floor")]
    if min(rates) < 0 or min(atol) <= 0 or min(rtol) < 0 or min(floor) < 0:
        raise ValueError("invalid rates or tolerances")
    for key in ("t_end", "dt_initial", "dt_min", "dt_max"):
        if not number(payload.get(key)):
            raise ValueError("invalid time setting")
    end = float(payload["t_end"])
    dt_min, dt_max = float(payload["dt_min"]), float(payload["dt_max"])
    proposed = float(payload["dt_initial"])
    budget = payload.get("max_trials")
    if end < 0 or dt_min <= 0 or dt_max < dt_min or not dt_min <= proposed <= dt_max:
        raise ValueError("invalid time range")
    if not isinstance(budget, int) or isinstance(budget, bool) or budget < 1:
        raise ValueError("invalid max_trials")
    t, accepted, rejected = 0.0, 0, 0
    history = [{"t": t, "y": y[:]}]
    attempts = []
    status = "finished"
    while t < end:
        if len(attempts) >= budget:
            status = "max_trials_reached"
            break
        remaining = end-t
        h = min(proposed, remaining)
        if t+h <= t:
            status = "time_stalled"
            break
        full = [v/(1+r*h) for v, r in zip(y, rates)]
        half_state = [v/(1+r*h/2) for v, r in zip(y, rates)]
        two_half = [v/(1+r*h/2) for v, r in zip(half_state, rates)]
        error = max(abs(a-b)/(atol[i]+rtol[i]*max(abs(a), abs(b), floor[i]))
                    for i, (a, b) in enumerate(zip(full, two_half)))
        accept = error <= 1.0
        attempts.append({"t": t, "h": h, "error": error, "accepted": accept,
                         "y_before": y[:], "y_trial": two_half[:]})
        if accept:
            y = two_half
            t = end if h == remaining else t+h
            accepted += 1
            history.append({"t": t, "y": y[:]})
            factor = 2.0 if error == 0 else min(2.0, max(0.2, 0.9/math.sqrt(error)))
        else:
            rejected += 1
            if h <= dt_min*(1+1e-12):
                status = "dt_min_reached"
                break
            factor = min(0.9, max(0.2, 0.9/math.sqrt(error)))
        proposed = min(dt_max, max(dt_min, h*factor))
    return {"status": status, "t": t, "y": y, "accepted_steps": accepted,
            "rejected_steps": rejected, "history": history, "attempts": attempts}
'''


STARTER_SOURCE = '''def solve(payload):
    # Intentionally defective scheduler: scalar only, no rejection rollback.
    y = payload["y0"]
    rate = payload["rates"]
    t = 0.0
    dt = payload["dt_initial"]
    history = [{"t": t, "y": [y]}]
    while t < payload["t_end"]:
        full = y/(1+rate*dt)
        half = y/(1+rate*dt/2)**2
        y = half
        error = abs(half-full)/payload["atol"]
        if error > 1:
            dt /= 2
        t += dt
        history.append({"t": t, "y": [y]})
    return {"status": "finished", "t": t, "y": [y], "history": history,
            "accepted_steps": len(history)-1, "rejected_steps": 0, "attempts": []}
'''


def _oracle(payload):
    """Independent Decimal recurrence, with a documented double-time guard."""
    with localcontext() as ctx:
        ctx.prec = 45
        D = lambda v: Decimal(str(v))
        y0 = payload["y0"]
        y = [D(v) for v in (y0 if isinstance(y0, list) else [y0])]
        def vec(key):
            values = payload[key]
            return [D(v) for v in values] if isinstance(values, list) else [D(values)]*len(y)
        rates, absolute, relative, floor = [vec(key) for key in ("rates", "atol", "rtol", "scale_floor")]
        end, minimum, maximum, h_next = [D(payload[key]) for key in ("t_end", "dt_min", "dt_max", "dt_initial")]
        zero, one, two, half, safety = D(0), D(1), D(2), D("0.2"), D("0.9")
        t = zero
        states = [{"t": 0.0, "y": [float(v) for v in y]}]
        attempts, accept_count, reject_count = [], 0, 0
        status = "finished"
        while t < end:
            if len(attempts) == payload["max_trials"]:
                status = "max_trials_reached"
                break
            h = min(h_next, end-t)
            if float(t)+float(h) <= float(t):
                status = "time_stalled"
                break
            direct = [v/(one+r*h) for v, r in zip(y, rates)]
            stage = [v/(one+r*h/two) for v, r in zip(y, rates)]
            candidate = [v/(one+r*h/two) for v, r in zip(stage, rates)]
            err = max(abs(d-c)/(absolute[i]+relative[i]*max(abs(d), abs(c), floor[i]))
                      for i, (d, c) in enumerate(zip(direct, candidate)))
            accepted = err <= one
            attempts.append({"t": float(t), "h": float(h), "error": float(err), "accepted": accepted,
                             "y_before": [float(v) for v in y], "y_trial": [float(v) for v in candidate]})
            if accepted:
                t += h
                y = candidate
                accept_count += 1
                states.append({"t": float(t), "y": [float(v) for v in y]})
                multiplier = two if err == zero else max(half, min(two, safety/err.sqrt()))
            else:
                reject_count += 1
                if h <= minimum*(one+D("1e-12")):
                    status = "dt_min_reached"
                    break
                multiplier = max(half, min(safety, safety/err.sqrt()))
            h_next = max(minimum, min(maximum, h*multiplier))
        return {"status": status, "t": float(t), "y": [float(v) for v in y],
                "accepted_steps": accept_count, "rejected_steps": reject_count,
                "history": states, "attempts": attempts}


def _base(rng):
    return {"y0": [rng.uniform(0.5, 2.0), rng.uniform(0.6, 1.8)],
            "rates": [rng.uniform(0.3, 1.5), rng.uniform(4.0, 8.0)],
            "atol": [0.00003, 0.00005], "rtol": rng.uniform(0.018, 0.035),
            "scale_floor": 0.015, "t_end": rng.uniform(0.45, 0.75),
            "dt_initial": 0.3, "dt_min": 0.00001, "dt_max": 0.4, "max_trials": 1200}


def _hidden(seed):
    rng = random.Random(f"NRB05:hidden:{seed}")
    cases = [("vector_rejection_and_rollback", _base(rng), "ok")]
    p = _base(rng)
    p.update(y0=-1.2-rng.random(), rates=2.3+rng.random(), atol=0.00004)
    cases.append(("scalar_negative_state", p, "ok"))
    p = _base(rng)
    p.update(y0=[1.5, 0.0, 0.00003], rates=[0.0, 30.0, 17.0], atol=[0.00001]*3,
             rtol=[0.01, 0.02, 0.03], scale_floor=[0.0, 0.05, 0.2])
    cases.append(("zero_mode_and_vector_floors", p, "ok"))
    p = _base(rng)
    p.update(y0=1.0, rates=200.0, atol=1e-12, rtol=1e-9,
             dt_initial=0.05, dt_min=0.01, dt_max=0.05, t_end=0.1)
    cases.append(("finite_minimum_step_failure", p, "ok"))
    p = _base(rng)
    p.update(y0=1.0, rates=0.0, atol=0.01, dt_initial=0.13, dt_min=0.08,
             dt_max=0.2, t_end=0.345)
    cases.append(("final_clip_below_minimum", p, "ok"))
    p = _base(rng)
    p.update(max_trials=2)
    cases.append(("attempt_budget_preserves_last_accepted_state", p, "ok"))
    p = _base(rng)
    p.update(t_end=0.0)
    cases.append(("zero_horizon", p, "ok"))
    p = _base(rng)
    p.update(y0=2.0, rates=5.0, atol=1e-14, rtol=1e-10,
             dt_initial=0.08, dt_min=0.08, dt_max=0.2, t_end=0.03)
    cases.append(("failed_clipped_endpoint_is_not_committed", p, "ok"))
    p = _base(rng)
    p["atol"] = 0.0
    cases.append(("reject_zero_absolute_tolerance", p, "ValueError"))
    p = _base(rng)
    p["rates"] = [1.0, 2.0, 3.0]
    cases.append(("reject_vector_shape_mismatch", p, "ValueError"))
    return cases


def build(seed=0):
    visible = _base(random.Random(f"NRB05:visible:{seed}"))
    contract = """# Public API: adaptive test-equation integrator

Integrate independent classical decay equations y_i'=-rates_i*y_i from 0 to t_end.
This is a synthetic numerical-analysis exercise with dimensionless inputs.
solve(payload) accepts y0 as a finite scalar or nonempty list. rates, atol, rtol,
scale_floor each accept a scalar (broadcast) or a list of the same length.
rates >= 0, atol > 0, rtol >= 0, scale_floor >= 0. All values are finite;
booleans are invalid numeric inputs. t_end >= 0; 0 < dt_min <= dt_initial <= dt_max;
max_trials is an integer >= 1. Invalid inputs raise ValueError.

Start t=0, state=y0, proposed=dt_initial. While t<t_end:
1. Stop with max_trials_reached if the attempt budget has been exhausted.
2. Set h=min(proposed,t_end-t). If floating-point t+h<=t, stop time_stalled.
3. From the unchanged committed state, compute full=y/(1+rates*h) and
   two_half=y/(1+rates*h/2)^2, componentwise.
4. E=max_i(abs(full_i-two_half_i)/(atol_i+rtol_i*
   max(abs(full_i),abs(two_half_i),scale_floor_i))). Accept iff E<=1.
5. Record the attempt with t,h,error=E,accepted,y_before,y_trial=two_half.
6. On acceptance ONLY, commit two_half and advance t by the ACTUAL h. If h
   equals the remaining interval, set t exactly to t_end. Append committed history.
   Set factor=2 if E=0; otherwise clamp(0.9/sqrt(E),0.2,2).
7. On rejection, keep t and y unchanged. If h<=dt_min*(1+1e-12), stop with
   dt_min_reached after recording the rejection. Otherwise set
   factor=clamp(0.9/sqrt(E),0.2,0.9).
8. Set proposed=clamp(h*factor,dt_min,dt_max). Continue.

A final endpoint-clipped h below dt_min is permitted once; a failed clipped
attempt terminates under rule 7. Do not claim finished after failure. The final
state must be the last accepted state. No Richardson extrapolation is allowed.
Successful completion has status finished. t_end=0 gives no attempts.
All returned y arrays are lists even for a scalar input.

Output fields:
status (finished | dt_min_reached | max_trials_reached | time_stalled), t, y,
accepted_steps, rejected_steps,
history=[{t,y},...] including the initial and every accepted state,
attempts=[{t,h,error,accepted,y_before,y_trial},...].
Only standard library Python is available. Numeric comparisons use float tolerances;
the grader does not require a particular code style.
"""
    prompt = """请以只读的 starter.py 为起点，在新的 solution.py 中修复自适应后向欧拉教学程序：它必须按 API.md 的确定性调度策略处理标量与向量衰减，
拒绝步必须回滚，达到最小步长时必须有限终止并保留真实执行状态。根据全步与两次半步的误差估计解释
步长指数，区分局部误差估计与全局阶数。提交 input.json 的完整轨迹和修复代码。

严格输出 JSON：{"task_id":"NRB05","answer":{"visible_result":{"status":"finished|dt_min_reached|max_trials_reached|time_stalled",
"t":number,"y":[number],"accepted_steps":integer,"rejected_steps":integer,
"history":[{"t":number,"y":[number]}],"attempts":[{"t":number,"h":number,"error":number,
"accepted":boolean,"y_before":[number],"y_trial":[number]}]}},
"artifacts":{"solution.py":"完整源码，提供 solve(payload)","reasoning.md":"方法、缺陷修复及真实验证说明"}}。
status 必须取其中一个枚举值，不得照抄竖线分隔模板。隐藏评分使用新的输入与异常情形。"""
    return {"id": "NRB05", "seed": seed, "title": "自适应积分器的回滚与终止", "domain": "adaptive-numerics",
            "prompt": prompt,
            "files": {"API.md": contract, "input.json": json.dumps(visible, indent=2), "starter.py": STARTER_SOURCE},
            "expected": {"visible": _oracle(visible), "hidden": _hidden(seed)},
            "rubric": [
                {"id": "numerical_reasoning", "title": "误差与方法阶数", "anchors": {"0": "误解接受状态或宣称该方法为高阶而无推导。", "5": "正确描述后向欧拉和步长缩放，但局部/全局误差区分不完整。", "10": "说明全步与两半步差的二阶小步长尺度、平方根控制器、一阶全局精度及所用相对误差分母；条件清楚。"}},
                {"id": "lifecycle", "title": "状态生命周期与失败语义", "anchors": {"0": "把失败当完成，或拒绝步仍推进状态。", "5": "正确说明回滚，但对端点截断、最小步长或预算解释不完整。", "10": "清楚区分试探、接受、回滚、端点及终止状态；给出能发现状态污染的验证，准确报告尚未运行的部分。"}},
                {"id": "engineering", "title": "实现与交付", "anchors": {"0": "不可复用、硬编码或无法解释接口。", "5": "代码可读并有基本验证说明。", "10": "输入验证、单步计算、状态提交和轨迹记录职责清楚；报告实际验证命令、有限终止证据和具体限制。"}}]}


def reference(case):
    return {"task_id": "NRB05", "answer": {"visible_result": copy.deepcopy(case["expected"]["visible"])},
            "artifacts": {"solution.py": REFERENCE_SOURCE,
                          "reasoning.md": "后向欧拉全步与两次半步的差在小步长下是 O(h²)，因此该局部差控制器使用 E^(-1/2)。接受两次半步仍为一阶全局方法。试探状态独立保存；只在 E<=1 时提交。最小步长失败和预算耗尽返回最后接受状态。此参考文本未记录外部运行；执行结果由验证记录提供。"}}


def _batch_source(source):
    return source + '''

_nrb_original_solve = solve
def solve(payload):
    records = []
    for item in payload["nrb_cases"]:
        try:
            records.append({"status": "ok", "result": _nrb_original_solve(item)})
        except Exception as exc:
            records.append({"status": "error", "type": type(exc).__name__})
    return {"nrb_results": records}
'''


def grade(case, submission, execution="none"):
    ans = submission.get("answer", {}) if isinstance(submission, dict) else {}
    ans = ans if isinstance(ans, dict) else {}
    value = ans.get("visible_result", {})
    value = value if isinstance(value, dict) else {}
    expected = case["expected"]["visible"]
    groups = [("visible_final_state", ("t", "y")),
              ("visible_status_and_counts", ("status", "accepted_steps", "rejected_steps")),
              ("visible_committed_history", ("history",)),
              ("visible_attempt_trace", ("attempts",))]
    results = [check(name, 5, numbers_close({key: value.get(key) for key in keys}, {key: expected[key] for key in keys}),
                     "按独立高精度递推核对可见结果。", critical=name == "visible_status_and_counts") for name, keys in groups]
    artifacts = submission.get("artifacts", {}) if isinstance(submission, dict) else {}
    source = artifacts.get("solution.py") if isinstance(artifacts, dict) else None
    hidden = case["expected"]["hidden"]
    if not isinstance(source, str) or not source.strip():
        return results+[check(name, 5, False, "缺少 solution.py。") for name, _, _ in hidden]
    run = run_python(_batch_source(source), {"nrb_cases": [p for _, p, _ in hidden]}, execution=execution, timeout=5)
    if run.get("status") == "unavailable":
        return results+[check(name, 5, None, run.get("detail", "未启用代码执行；此项未评。")) for name, _, _ in hidden]
    result = run.get("result")
    batch = result.get("nrb_results") if isinstance(result, dict) else None
    for i, (name, payload, state) in enumerate(hidden):
        observed = batch[i] if isinstance(batch, list) and i < len(batch) and isinstance(batch[i], dict) else {}
        if state == "ValueError":
            passed = observed.get("status") == "error" and observed.get("type") == state
        else:
            actual = observed.get("result")
            oracle = _oracle(payload)
            passed = observed.get("status") == "ok" and isinstance(actual, dict) and numbers_close({key: actual.get(key) for key in oracle}, oracle, rtol=2e-7, atol=1e-10)
        results.append(check(name, 5, passed,
                             "按独立高精度行为参考核对调度轨迹。" if run.get("status") == "ok" else run.get("detail", "执行失败。"),
                             critical=name in ("vector_rejection_and_rollback", "finite_minimum_step_failure", "failed_clipped_endpoint_is_not_committed")))
    return results

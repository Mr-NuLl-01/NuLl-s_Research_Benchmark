"""NRB05: deterministic adaptive backward-Euler scheduling for test ODEs."""

from __future__ import annotations

import copy
from decimal import Decimal, localcontext
import json
import math
import random

from nrb.checks import check, numbers_close
from nrb.execution import run_python


REFERENCE_SOURCE = '''import math

def solve(payload):
    def number(x):
        if not isinstance(x, (int, float)) or isinstance(x, bool):
            return False
        try:
            return math.isfinite(x)
        except OverflowError:
            return False
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
    start = payload.get("t_start", 0.0)
    if not number(start):
        raise ValueError("invalid t_start")
    start, end = float(start), float(payload["t_end"])
    dt_min, dt_max = float(payload["dt_min"]), float(payload["dt_max"])
    proposed = float(payload["dt_initial"])
    budget = payload.get("max_trials")
    if end < 0 or start > end or dt_min <= 0 or dt_max < dt_min or not dt_min <= proposed <= dt_max:
        raise ValueError("invalid time range")
    if not isinstance(budget, int) or isinstance(budget, bool) or budget < 1:
        raise ValueError("invalid max_trials")
    t, accepted, rejected = start, 0, 0
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
    """Independent high-precision states with public binary64 control semantics.

    Decimal computes the reported numerical states. A parallel binary64 state
    computes the discontinuous accept/reject and step-size decisions; Decimal
    clocks or threshold decisions would define a different scheduler near E=1
    and adjacent floating-point endpoint values.
    """
    with localcontext() as ctx:
        ctx.prec = 65
        D = lambda v: Decimal.from_float(float(v))
        y0 = payload["y0"]
        initial = y0 if isinstance(y0, list) else [y0]
        y, control_y = [D(v) for v in initial], [float(v) for v in initial]
        def vec(key):
            values = payload[key]
            return [float(v) for v in values] if isinstance(values, list) else [float(values)]*len(y)
        rates, absolute, relative, floor = [vec(key) for key in ("rates", "atol", "rtol", "scale_floor")]
        end, minimum, maximum, h_next = [float(payload[key]) for key in ("t_end", "dt_min", "dt_max", "dt_initial")]
        one, two = D(1), D(2)
        t = float(payload.get("t_start", 0.0))
        states = [{"t": t, "y": [float(v) for v in y]}]
        attempts, accept_count, reject_count = [], 0, 0
        status = "finished"
        while t < end:
            if len(attempts) == payload["max_trials"]:
                status = "max_trials_reached"
                break
            remaining = end-t
            h = min(h_next, remaining)
            if t+h <= t:
                status = "time_stalled"
                break
            candidate, control_trial, component_errors = [], [], []
            for i in range(len(y)):
                # Two backward-Euler half steps, independently evaluated in
                # high precision; no reference source is executed or imported.
                divisor = one+D(rates[i])*D(h)/two
                candidate.append((y[i]/divisor)/divisor)
                rate_step = rates[i]*h
                direct = control_y[i]/(1.0+rate_step)
                half_divisor = 1.0+rate_step/2.0
                trial = (control_y[i]/half_divisor)/half_divisor
                control_trial.append(trial)
                scale = absolute[i]+relative[i]*max(abs(direct), abs(trial), floor[i])
                component_errors.append(abs(direct-trial)/scale)
            error = max(component_errors)
            accepted = error <= 1.0
            attempts.append({"t": t, "h": h, "error": error, "accepted": accepted,
                             "y_before": [float(v) for v in y], "y_trial": [float(v) for v in candidate]})
            if accepted:
                t = end if h == remaining else t+h
                y, control_y = candidate, control_trial
                accept_count += 1
                states.append({"t": t, "y": [float(v) for v in y]})
                multiplier = 2.0 if error == 0 else max(0.2, min(2.0, 0.9/math.sqrt(error)))
            else:
                reject_count += 1
                if h <= minimum*(1.0+1e-12):
                    status = "dt_min_reached"
                    break
                multiplier = max(0.2, min(0.9, 0.9/math.sqrt(error)))
            h_next = max(minimum, min(maximum, h*multiplier))
        return {"status": status, "t": t, "y": [float(v) for v in y],
                "accepted_steps": accept_count, "rejected_steps": reject_count,
                "history": states, "attempts": attempts}


def _base(rng):
    return {"y0": [rng.uniform(0.5, 2.0), rng.uniform(0.6, 1.8)],
            "rates": [rng.uniform(0.3, 1.5), rng.uniform(4.0, 8.0)],
            "atol": [0.00003, 0.00005], "rtol": rng.uniform(0.018, 0.035),
            "scale_floor": 0.015, "t_end": rng.uniform(0.45, 0.75),
            "dt_initial": 0.3, "dt_min": 0.00001, "dt_max": 0.4, "max_trials": 1200}


def _hidden_with_groups(seed):
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
    members = {name: [name] for name, _, _ in cases}
    def extra(name, field, value, group):
        item = _base(rng)
        if isinstance(field, tuple):
            item[field[0]][field[1]] = value
        else:
            item[field] = value
        cases.append((name, item, "ValueError"))
        members[group].append(name)

    for value, tag in ((-1.0, "negative"), (True, "boolean")):
        extra("reject_"+tag+"_rates", ("rates", 0), value, "zero_mode_and_vector_floors")
    for token in ("nan", "inf", "-inf"):
        extra("reject_"+token+"_rates", ("rates", 0), {"__nrb_float__": token}, "zero_mode_and_vector_floors")
    for key in ("t_end", "dt_initial", "dt_min", "dt_max"):
        extra("reject_boolean_"+key, key, True, "final_clip_below_minimum")
        for token in ("nan", "inf", "-inf"):
            extra("reject_"+token+"_"+key, key, {"__nrb_float__": token}, "final_clip_below_minimum")
    for key, value, tag in (("t_end", -1.0, "negative_horizon"),
                            ("dt_min", 0.0, "zero_minimum"),
                            ("dt_min", -0.1, "negative_minimum"),
                            ("dt_max", 1e-6, "reversed_bounds"),
                            ("dt_initial", 1e-6, "initial_below_minimum"),
                            ("dt_initial", 0.5, "initial_above_maximum")):
        extra("reject_"+tag, key, value, "final_clip_below_minimum")
    for value, tag in ((True, "boolean"), (2.0, "float"), (2.5, "fractional"),
                       (0, "zero"), (-1, "negative"), ("2", "string")):
        extra("reject_"+tag+"_budget", "max_trials", value, "attempt_budget_preserves_last_accepted_state")
    for key in ("y0", "atol", "rtol", "scale_floor"):
        extra("reject_boolean_"+key, key, True, "reject_zero_absolute_tolerance")
        for token in ("nan", "inf", "-inf"):
            extra("reject_"+token+"_"+key, key, {"__nrb_float__": token}, "reject_zero_absolute_tolerance")
    extra("reject_negative_rtol", "rtol", -0.1, "reject_zero_absolute_tolerance")
    extra("reject_negative_scale_floor", "scale_floor", -0.1, "reject_zero_absolute_tolerance")
    extra("reject_empty_y0", "y0", [], "reject_vector_shape_mismatch")
    for key in ("atol", "rtol", "scale_floor"):
        extra("reject_shape_"+key, key, [0.1], "reject_vector_shape_mismatch")
    # These exact powers and integers make full=4, two_half=3. Thus E=1
    # exactly when atol=1, with neighboring binary64 tolerances on each side.
    for atol, tag in ((1.0, "exact"), (math.nextafter(1.0, math.inf), "below"),
                      (math.nextafter(1.0, 0.0), "above")):
        p = {"y0": 12.0, "rates": 2.0, "atol": atol, "rtol": 0.0, "scale_floor": 0.0,
             "t_end": 1.0, "dt_initial": 1.0, "dt_min": 1.0, "dt_max": 1.0, "max_trials": 3}
        name = "acceptance_error_"+tag+"_one"
        cases.append((name, p, "ok"))
        members["vector_rejection_and_rollback"].append(name)
    p = {"y0": 1.0, "rates": 0.0, "atol": 1.0, "rtol": 0.0, "scale_floor": 0.0,
         "t_end": math.nextafter(0.3, math.inf), "dt_initial": 0.1,
         "dt_min": 0.01, "dt_max": 0.2, "max_trials": 5}
    cases.append(("adjacent_binary64_endpoint", p, "ok"))
    members["final_clip_below_minimum"].append("adjacent_binary64_endpoint")
    p = dict(p, dt_initial=0.3, dt_max=0.3)
    cases.append(("adjacent_endpoint_requires_final_step", p, "ok"))
    members["final_clip_below_minimum"].append("adjacent_endpoint_requires_final_step")
    p = {"y0": 1.0, "rates": 0.0, "atol": 1.0, "rtol": 0.0, "scale_floor": 0.0,
         "t_start": 1e16, "t_end": 1e16+4.0, "dt_initial": 1.0,
         "dt_min": 0.5, "dt_max": 2.0, "max_trials": 5}
    cases.append(("continuation_time_stalled", p, "ok"))
    members["attempt_budget_preserves_last_accepted_state"].append("continuation_time_stalled")
    p = dict(p, t_start=2.0, t_end=2.3, dt_initial=0.1, dt_min=0.01, dt_max=0.2)
    cases.append(("nonzero_continuation", p, "ok"))
    members["scalar_negative_state"].append("nonzero_continuation")
    p = dict(p, t_end=2.0)
    cases.append(("nonzero_zero_horizon", p, "ok"))
    members["zero_horizon"].append("nonzero_zero_horizon")
    extra("reject_boolean_t_start", "t_start", True, "zero_horizon")
    for token in ("nan", "inf", "-inf"):
        extra("reject_"+token+"_t_start", "t_start", {"__nrb_float__": token}, "zero_horizon")
    extra("reject_start_after_end", "t_start", 1.0, "zero_horizon")
    return cases, members


def _hidden(seed):
    return _hidden_with_groups(seed)[0]


def build(seed=0):
    visible = _base(random.Random(f"NRB05:visible:{seed}"))
    hidden, hidden_groups = _hidden_with_groups(seed)
    contract = """# Public API: adaptive test-equation integrator

Integrate independent classical decay equations y_i'=-rates_i*y_i from t_start
to t_end. Optional t_start defaults to 0; it is an absolute initial time, and
y0 is the state at that time. t_start must be finite, nonboolean and <=t_end.
This is a synthetic numerical-analysis exercise with dimensionless inputs.
solve(payload) accepts y0 as a finite scalar or nonempty list. rates, atol, rtol,
scale_floor each accept a scalar (broadcast) or a list of the same length.
rates >= 0, atol > 0, rtol >= 0, scale_floor >= 0. All values are finite;
booleans and numeric strings are invalid numeric inputs. A number is a Python
int or float representable as a finite binary64 value; IEEE NaN and infinities
are invalid even in direct Python API calls (JSON transport remains strict).
t_end >= 0; 0 < dt_min <= dt_initial <= dt_max;
max_trials must have Python int type and be >= 1, so 2.0 and True are invalid.
Invalid inputs raise ValueError. All scheduling, error comparisons and time
arithmetic use binary64 floats. E<=1 is inclusive with no extra acceptance
tolerance; a value just above 1 is rejected. Do not use a higher-precision clock
to create an extra endpoint step that binary64 addition already completed.

Start t=t_start (default 0), state=y0, proposed=dt_initial. While t<t_end:
1. Stop with max_trials_reached if the attempt budget has been exhausted.
2. Set h=min(proposed,t_end-t). If floating-point t+h<=t, stop time_stalled.
3. From the unchanged committed state, compute full=y/(1+rates*h) and
   half=y/(1+rates*h/2), then two_half=half/(1+rates*h/2), componentwise.
   Use two successive divisions and binary64 operations for the acceptance
   decision, including the indicated multiplication/division order.
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
Successful completion has status finished. t_start=t_end gives no attempts;
this includes the default-start t_end=0 case. Large absolute continuation times
may trigger time_stalled even when h is positive; do not advance or record an
attempt when binary64 t+h<=t.
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
            "expected": {"visible": _oracle(visible), "hidden": hidden, "hidden_groups": hidden_groups},
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
def _nrb_materialize(value):
    if isinstance(value, dict):
        if set(value) == {"__nrb_float__"}:
            return float(value["__nrb_float__"])
        return {key: _nrb_materialize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_nrb_materialize(item) for item in value]
    return value

def solve(payload):
    records = []
    for item in payload["nrb_cases"]:
        try:
            records.append({"status": "ok", "result": _nrb_original_solve(_nrb_materialize(item))})
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
                     "按高精度状态递推及 binary64 调度语义核对可见结果。", critical=name == "visible_status_and_counts") for name, keys in groups]
    artifacts = submission.get("artifacts", {}) if isinstance(submission, dict) else {}
    source = artifacts.get("solution.py") if isinstance(artifacts, dict) else None
    hidden = case["expected"]["hidden"]
    groups = case["expected"]["hidden_groups"]
    critical = {"vector_rejection_and_rollback", "finite_minimum_step_failure", "failed_clipped_endpoint_is_not_committed"}
    if not isinstance(source, str) or not source.strip():
        return results+[check(name, 5, False, "缺少 solution.py。", critical=name in critical) for name in groups]
    run = run_python(_batch_source(source), {"nrb_cases": [p for _, p, _ in hidden]}, execution=execution, timeout=5)
    if run.get("status") == "unavailable":
        return results+[check(name, 5, None, run.get("detail", "未启用代码执行；此项未评。"), critical=name in critical) for name in groups]
    result = run.get("result")
    batch = result.get("nrb_results") if isinstance(result, dict) else None
    outcomes = {}
    for i, (name, payload, state) in enumerate(hidden):
        observed = batch[i] if isinstance(batch, list) and i < len(batch) and isinstance(batch[i], dict) else {}
        if state == "ValueError":
            passed = observed.get("status") == "error" and observed.get("type") == state
        else:
            actual = observed.get("result")
            oracle = _oracle(payload)
            passed = observed.get("status") == "ok" and isinstance(actual, dict) and numbers_close({key: actual.get(key) for key in oracle}, oracle, rtol=2e-7, atol=1e-10)
        outcomes[name] = passed
    for name, members in groups.items():
        failed = [member for member in members if not outcomes[member]]
        detail = "组内逐例核对；失败案例：" + (", ".join(failed) if failed else "无")
        if run.get("status") != "ok":
            detail += "；" + run.get("detail", "执行失败。")
        row = check(name, 5, not failed, detail, critical=name in critical)
        row["cases"] = [{"id": member, "passed": outcomes[member]} for member in members]
        results.append(row)
    return results

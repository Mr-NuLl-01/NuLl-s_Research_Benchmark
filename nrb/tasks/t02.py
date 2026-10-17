"""NRB02: structural identifiability of an original classical heat experiment."""
from __future__ import annotations

import copy
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
        return math.isfinite(value) and math.isclose(value, expected, rel_tol=3e-6, abs_tol=1e-9)
    except (OverflowError, TypeError, ValueError):
        return False


def _step_response(t, power, capacity, conductance, gain, offset):
    return offset + gain * power/conductance * (-math.expm1(-conductance*t/capacity))


def _infer_step(data):
    """Infer from visible equal-time increments, independent of generator parameters."""
    rows = data["observations"]
    offset = rows[0][1]
    d1, d2 = rows[1][1]-offset, rows[2][1]-rows[1][1]
    ratio = d2/d1
    tau = -(rows[1][0]-rows[0][0])/math.log(ratio)
    amplitude = d1/(1-ratio)
    return tau, amplitude/data["power_W"], offset


def build(seed: int = 0) -> dict:
    rng = random.Random(f"nrb02-v1:{seed}")
    capacity = rng.randint(40, 180) / 2
    conductance = rng.randint(15, 64) / 10
    gain = rng.randint(45, 170) / 100
    offset = rng.randint(-25, 35) / 100
    power = rng.randint(30, 95) / 10
    delta_capacity = rng.randint(20, 90) / 2
    dt = rng.randint(15, 65) / 10
    tau = capacity/conductance
    tau_new = (capacity+delta_capacity)/conductance
    baseline = {"provenance": "original deterministic synthetic observations, not measured data",
                "power_W": power, "initial_temperature_difference_K": 0,
                "observations": [[round(i*dt, 10), round(_step_response(i*dt, power, capacity,
                                      conductance, gain, offset), 14)] for i in range(6)],
                "columns": ["time_s", "sensor_reading"], "noise": "none; rounded to 14 decimal places"}
    intervention = {"provenance": "original deterministic synthetic intervention observations",
                    "power_W": power, "added_capacity_J_per_K": delta_capacity,
                    "assumptions": "Only C changes to C+delta_C; G, gain and offset are unchanged.",
                    "initial_temperature_difference_K": 0,
                    "observations": [[round(i*dt, 10), round(_step_response(i*dt, power,
                                          capacity+delta_capacity, conductance, gain, offset), 14)]
                                     for i in range(6)],
                    "columns": ["time_s", "sensor_reading"]}
    choices = [
        ("double_power", "仅将已校准输入功率加倍，仍只测同一传感器读数。"),
        ("denser_times", "对原功率任意延长时间并加密采样，不引入新绝对标定。"),
        ("known_capacity", f"加入精确已知的 {delta_capacity:g} J/K 热容，且验证 G、传感器增益及偏移均不变。"),
        ("repeat_original", "重复原实验 100 次，保持所有物理配置与测量通道不变。"),
    ]
    rng.shuffle(choices)
    menu = {f"I{i}": text for i, (_, text) in enumerate(choices, 1)}
    choice = next(f"I{i}" for i, (kind, _) in enumerate(choices, 1) if kind == "known_capacity")
    ranks = {f"I{i}": 4 if kind == "known_capacity" else 3
             for i, (kind, _) in enumerate(choices, 1)}
    test_power = rng.randint(25, 120)/10
    on_time = rng.randint(50, 250)/10
    after_time = on_time+rng.randint(30, 180)/10
    prediction = {"configuration": "original C (added capacity removed)", "power_W": test_power,
                  "pulse_on_interval_s": [0, on_time], "observation_times_s": [on_time, after_time],
                  "initial_temperature_difference_K": 0}
    at_off = _step_response(on_time, test_power, capacity, conductance, gain, offset)
    late = offset + (at_off-offset)*math.exp(-(after_time-on_time)/tau)
    answer = {
        "baseline": {"tau_s": tau, "steady_gain_per_W": gain/conductance, "offset": offset},
        "structural_rank": 3,
        "scale_powers_C_G_gain_offset": [1, 1, 1, 0],
        "nonidentifiable_parameters": ["C_J_per_K", "G_W_per_K", "sensor_gain"],
        "chosen_intervention": choice,
        "rank_after_interventions": ranks,
        "recovered": {"C_J_per_K": capacity, "G_W_per_K": conductance,
                      "sensor_gain": gain, "intervention_tau_s": tau_new},
        "prediction_readings": [at_off, late],
    }
    prompt = """一个经典集中热容系统满足
C*dtheta/dt=P(t)-G*theta，y(t)=b+alpha*theta(t)，theta=T-T_ambient。
C>0、G>0、alpha>0 和偏移 b 均未知；输入功率已做绝对校准，时间单位为秒，
初态 theta(0)=0。baseline.json 给出无噪声合成阶跃数据（仅小数舍入）。

请完成以下工作：从基线识别可辨识的组合；证明任意已知输入波形下仍存在的参数
等价族；给出四个参数关于连续完整响应的局部结构秩（不是有限差分数值阈值）；
比较 interventions.json 的四个方案，并选择真正破除尺度退化的那个。
intervention_observations.json 是加入已知热容后的已完成合成实验；结合两轮数据
恢复绝对参数。最后对 prediction.json 的新脉冲给出关断瞬间及其后读数。
所有数值均为合成教学数据，不应解释为某个真实样品的拟合。

提交 JSON：{"task_id":"NRB02","answer":{...},"artifacts":{"reasoning.md":"..."}}。
answer 的精确结构：
{
 "baseline":{"tau_s":0,"steady_gain_per_W":0,"offset":0},
 "structural_rank":0,
 "scale_powers_C_G_gain_offset":[0,0,0,0],
 "nonidentifiable_parameters":["C_J_per_K","G_W_per_K","sensor_gain"],
 "chosen_intervention":"I1|I2|I3|I4",
 "rank_after_interventions":{"I1":0,"I2":0,"I3":0,"I4":0},
 "recovered":{"C_J_per_K":0,"G_W_per_K":0,"sensor_gain":0,"intervention_tau_s":0},
 "prediction_readings":[0,0]
}
steady_gain_per_W 指 y 的稳态变化除以 P，非温度增益。scale_powers 表示把四个参数
分别乘以 s 的对应指数，s>0；将 C 的指数规范为 +1。
rank_after_interventions 指原数据加该方案的新数据后，对原四个未知量的结构秩。
reasoning.md 应推导组合、等价性及破退化条件，解释额外采样为何不一定增加结构秩，
并说明“无噪声可唯一恢复”与有噪声时的实用可辨识性差别。提供可复查计算。
数值建议直接保留计算结果的浮点精度；如需缩短，至少保留 9 位有效数字。
使用科学计数法表示小量，不把谱密度、协方差或目标差舍入为零。
评分容差按字段定义，不要求输出额外无意义的小数。
"""
    rubric = [
        {"id": "identifiability_proof", "title": "结构可辨识性推导", "anchors": {
            "0": "直接报告唯一拟合参数，未识别退化或把数值优化成功当作唯一性。",
            "5": "识别比例退化，但只对单一阶跃说明，或结构秩论证不完整。",
            "10": "从微分方程给出任意已知输入下的尺度等价性，推导三个独立组合与秩。"}},
        {"id": "intervention_design", "title": "判别实验与模型假设", "anchors": {
            "0": "所选方案不破退化，或者忽略加入附件同时改变其他参数。",
            "5": "方案正确但缺少参数恢复公式、保持条件或实际校验。",
            "10": "推导两时间常数恢复公式，明确 G/增益不变的验证及扰动带来的限制。"}},
        {"id": "prediction_and_uncertainty", "title": "独立预测与实际精度", "anchors": {
            "0": "只抄拟合值，未解释脉冲预测或声称无噪声结果代表现实精度。",
            "5": "脉冲与偏移处理正确，但未讨论差分恢复的误差放大。",
            "10": "给出分段解析预测和可复查计算，讨论小时间常数差导致的不稳定及验证措施。"}},
    ]
    dump = lambda obj: json.dumps(obj, ensure_ascii=False, indent=2)+"\n"
    return {"id": "NRB02", "seed": seed, "title": "热响应中的参数退化与判别实验",
            "domain": "identifiability", "prompt": prompt,
            "files": {"baseline.json": dump(baseline), "interventions.json": dump(menu),
                      "intervention_observations.json": dump(intervention), "prediction.json": dump(prediction)},
            "expected": {"answer": answer}, "rubric": rubric}


def reference(case: dict) -> dict:
    baseline = json.loads(case["files"]["baseline.json"])
    intervention = json.loads(case["files"]["intervention_observations.json"])
    tau, k, b = _infer_step(baseline)
    tau_new, _, _ = _infer_step(intervention)
    g = intervention["added_capacity_J_per_K"]/(tau_new-tau)
    c, alpha = tau*g, k*g
    ans = copy.deepcopy(case["expected"]["answer"])
    # Reconstruct the numerical reference from candidate-visible observations.
    ans["baseline"] = {"tau_s": tau, "steady_gain_per_W": k, "offset": b}
    ans["recovered"] = {"C_J_per_K": c, "G_W_per_K": g,
                        "sensor_gain": alpha, "intervention_tau_s": tau_new}
    pred = json.loads(case["files"]["prediction.json"])
    t1, t2 = pred["observation_times_s"]
    y1 = b+k*pred["power_W"]*(-math.expm1(-t1/tau))
    ans["prediction_readings"] = [y1, b+(y1-b)*math.exp(-(t2-t1)/tau)]
    reasoning = """# 解析识别与验证

令 z=y-b=alpha*theta，则 z'=-(G/C)z+(alpha/C)P。
响应仅依赖 b、G/C、alpha/C；也可用 b、tau=C/G、K=alpha/G 表示。
对任意 s>0，(C,G,alpha,b)->(sC,sG,salpha,b) 保持上式和零初态，
故所有已知输入波形的输出相同；增加功率、采样密度或重复次数都不消除这一族。
三个组合在正参数域独立且从非零阶跃完整曲线可恢复，故结构秩为 3。

基线曲线 y=b+KP(1-exp(-t/tau))。等距采样时，连续两段增量之比
r=(y(2dt)-y(dt))/(y(dt)-y(0))=exp(-dt/tau)，因此 tau=-dt/log(r)，
K=(y(dt)-b)/(P*(1-r))。这里使用给定舍入后的可见数据计算。

加入已知 DeltaC 且 G、alpha、b 保持后，tau_new=(C+DeltaC)/G，
G=DeltaC/(tau_new-tau)，C=G*tau，alpha=G*K。只要 DeltaC>0，
两个时间常数之差非零，原四个未知量的秩升至 4。
真实实验必须独立核查附件未改变散热路径、传感器接触或电子增益；否则多出来的
未知量会破坏这一恢复逻辑，不能将拟合成功视作验证。

新脉冲在关断前给出 y=b+KP_test(1-exp(-t/tau))；关断后只将 y-b
按 exp(-(t-t_off)/tau) 衰减。偏移本身不衰减。独立脉冲残差可检验模型响应。

这是结构可辨识性，不是噪声下的精度保证。G 的分母是两个时间常数的差，若其差
很小，时间常数误差会放大；一阶相对误差含 -(delta_tau_new-delta_tau)/(tau_new-tau)。
选择可产生足够时间常数分离且仍保持 G/alpha 的已知附件，并传播两轮拟合的联合
不确定度，才可评价真实参数精度。
"""
    return {"task_id": "NRB02", "answer": ans, "artifacts": {"reasoning.md": reasoning}}


def grade(case: dict, submission, execution="none") -> list:
    ans = _mapping(_mapping(submission).get("answer"))
    ex = case["expected"]["answer"]
    baseline = _mapping(ans.get("baseline"))
    out = [check(f"baseline_{k}", 5, _near(baseline.get(k), v),
                 "从阶跃响应识别的输出组合。") for k, v in ex["baseline"].items()]
    out.append(check("structural_rank", 5,
                     type(ans.get("structural_rank")) is int and ans["structural_rank"] == 3,
                     "原四未知量仅有三个独立响应组合。", critical=True))
    powers = ans.get("scale_powers_C_G_gain_offset")
    valid_powers = (isinstance(powers, list) and len(powers) == 4
                    and all(_near(x, y) for x, y in zip(powers, [1, 1, 1, 0])))
    out.append(check("scale_symmetry", 5, valid_powers, "保持输出的整族尺度变换。", critical=True))
    params = ans.get("nonidentifiable_parameters")
    valid_params = (isinstance(params, list) and all(isinstance(x, str) for x in params)
                    and len(params) == 3 and set(params) == set(ex["nonidentifiable_parameters"]))
    out.append(check("individual_parameters", 5, valid_params,
                     "基线不能分别识别 C、G 和传感器增益。"))
    out.append(check("discriminating_intervention", 5,
                     ans.get("chosen_intervention") == ex["chosen_intervention"],
                     "额外独立绝对尺度约束才能破退化。", critical=True))
    ranks = _mapping(ans.get("rank_after_interventions"))
    out.append(check("intervention_rank_comparison", 5,
                     ranks == ex["rank_after_interventions"]
                     and all(type(x) is int for x in ranks.values()),
                     "逐项区分结构信息增加与重复/加密采样。"))
    recovered = _mapping(ans.get("recovered"))
    out.extend(check(f"recovered_{k}", 5, _near(recovered.get(k), v),
                     "由两个时间常数和已知附加热容恢复。") for k, v in ex["recovered"].items())
    pred = ans.get("prediction_readings")
    for i, v in enumerate(ex["prediction_readings"]):
        value = pred[i] if isinstance(pred, list) and len(pred) == 2 else None
        out.append(check(f"pulse_prediction_{i}", 5, _near(value, v),
                         "原热容配置的新功率脉冲；传感器偏移不随冷却衰减。"))
    return out

"""NRB01: a fully synthetic, versioned evidence packet; no real study data."""
from __future__ import annotations

import copy
import csv
import io
import json
import math
import random
import statistics

from nrb.checks import check


def _mapping(value):
    return value if isinstance(value, dict) else {}


def _near(value, expected):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value) and math.isclose(value, expected, rel_tol=2e-6, abs_tol=1e-9)
    except (OverflowError, TypeError, ValueError):
        return False


def build(seed: int = 0) -> dict:
    rng = random.Random(f"nrb01-v1:{seed}")
    ids = [f"SRC-{v:03d}" for v in rng.sample(range(101, 999), 6)]
    preliminary, corrected, field, replication, simulation, commentary = ids
    n = rng.randint(7, 11)
    repeats = rng.randint(3, 5)
    improvement = rng.uniform(0.17, 0.39)
    before = [round(rng.uniform(1.2, 3.8), 3) for _ in range(n)]
    after = [round(x * (1-improvement) + rng.uniform(-0.12, 0.12), 3) for x in before]
    # A substantive correction, not merely a renamed source.
    old_after = [round(x - rng.uniform(0.13, 0.31), 3) for x in after]
    diffs = [x-y for x, y in zip(before, after)]
    mean_before, mean_after = statistics.mean(before), statistics.mean(after)
    relative = 100 * (mean_before-mean_after) / mean_before
    threshold = math.floor(relative) + (5 if rng.choice([False, True]) else -5)
    randomized = rng.choice([False, True])
    independent_replication = rng.choice([False, True])
    ablation_zero = rng.choice([False, True])
    duration = rng.randint(8, 24)
    full_gain = [round(rng.uniform(0.15, 0.4), 3) for _ in range(4)]
    ablation_gain = ([0.0]*4 if ablation_zero else
                     [0.0, round(rng.uniform(0.03, 0.09), 3), 0.0,
                      round(rng.uniform(0.01, 0.05), 3)])

    stream = io.StringIO()
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(["instrument_id", "baseline_error_K", "corrected_error_K"])
    for i, (x, y) in enumerate(zip(before, after), 1):
        writer.writerow([f"CAL-{i:02d}", x, y])

    field_design = (
        "24 个记录器在同一作业周期内完全随机分配校正与基线模式，各 12 个；"
        "没有退出或缺失，处理无互相干扰，分配独立于两个潜在误差结果。"
        "处理组平均绝对误差为 0.91 K，基线组为 1.24 K。"
        if randomized else
        "校正模式只部署在地点 A，基线模式只部署在地点 B。两地点温度范围、"
        "维护频率和设备年龄均不同，没有随机分配、匹配或协变量调整。"
        "处理组平均绝对误差为 0.91 K，基线组为 1.24 K。"
    )
    rep_design = (
        "本记录使用新购置、此前未使用的 9 个记录器，重新采集原始数据；"
        "序列号 REP-01 至 REP-09，与 CAL 系列无交集。没有复用原研究数据。"
        if independent_replication else
        f"本记录重新绘制 {preliminary} 的 CAL 系列相同原始数据，采用不同归一化；"
        f"没有新增样本，数值校正遵循 {corrected}。"
    )
    packet = f"""# 合成证据包：通用温度记录器的校正方法

**所有研究、数值、来源卡片和标识符均为本 benchmark 原创合成材料。**
它们不是实际论文，不存在对应 DOI。本题只评价固定证据包的阅读、计算和论断审计，
不评价联网检索覆盖率。卡片完整列明本题所允许使用的证据；不得添加想象中的补充材料。

## {preliminary} — 首版台架实验记录（已被数值更正）
来源类型：原始实验记录 v1。对同一批 {n} 个记录器进行前后配对比较。
每个记录器每个模式记录 {repeats} 次；表中单位是设备内重复的平均值。
基线设备均值（K）：{json.dumps(before)}。
首版校正设备均值（K）：{json.dumps(old_after)}。
测试仅在 20、25、30 °C 三个设定点，单日完成。
首版图注将总重复次数 {n * repeats} 错称为独立设备数。
元数据明确指向 {corrected} 为当前更正记录。

## {corrected} — 数据及样本数更正（当前有效）
来源类型：作者确认的原始记录更正 v2。
首版导出程序额外减去了一个偏移，故校正列数值错误。
本卡片随附 corrected_table.csv 完整替代首版的校正数值。
独立设备数为 {n}；每个设备内有 {repeats} 个技术重复，这些重复不是独立设备。
设备之间独立；跨设备标准误使用设备配对差值，样本 SD 使用 n-1 分母。
本更正没有扩大测试温度范围或时长。baseline_error_K 与 corrected_error_K 都是
同一设备在该台架协议下的平均绝对误差，不是有符号温差。

## {field} — 外场比较记录
来源类型：{'原始随机分配实验' if randomized else '原始观察性记录'}。
{field_design}
记录时长为 {duration} 天。没有更长期数据。这里的设计陈述作为本题给定假设。

## {replication} — 后续比较记录
来源类型：{'独立原始采样' if independent_replication else '旧数据再分析'}。
{rep_design}

## {simulation} — 模块消融计算
来源类型：合成仿真原始输出；只报告四个离散参数点。正数代表优于基线，零代表相同。
保留模块 M 的收益：{json.dumps(full_gain)}。
移除模块 M、其余输入完全保持时的收益：{json.dumps(ablation_gain)}。
这些数值是确定性合成输出，不是实际记录器的机理实验，也没有对网格外参数的证明。

## {commentary} — 新闻式二次摘要
来源类型：二次评论。其措辞为“该校正技术长期适用于所有温度并揭示唯一机制”。
该评论不包含新样本、长期观察或额外计算，仅链接上面五份记录。
"""
    claims = {
        "C1": f"当前有效台架表的设备平均绝对误差相对下降至少 {threshold}%。",
        "C2": f"台架中的 {n * repeats} 个技术重复可以作为 {n * repeats} 个独立设备，计算跨设备均值差的标准误。",
        "C3": f"在 {field} 明示的设计假设下，校正组与基线组的样本均值差是该实验人群平均因果效应的无偏估计。",
        "C4": f"{replication} 使用了区别于原台架实验的新独立样本。",
        "C5": f"在 {simulation} 报告的四个参数点内，正收益的出现都需要模块 M 存在。",
        "C6": "该校正方法连续运行一年后的实际误差仍然低于基线。",
    }
    verdicts = {
        "C1": "supported" if relative >= threshold else "contradicted",
        "C2": "contradicted",
        "C3": "supported" if randomized else "insufficient",
        "C4": "supported" if independent_replication else "contradicted",
        "C5": "supported" if ablation_zero else "contradicted",
        "C6": "insufficient",
    }
    required = {"C1": [corrected], "C2": [corrected], "C3": [field],
                "C4": [replication], "C5": [simulation], "C6": [field]}
    allowed = {"C1": [corrected, preliminary], "C2": [corrected, preliminary],
               "C3": [field], "C4": [replication, corrected, preliminary],
               "C5": [simulation], "C6": [field, commentary]}
    roles = {preliminary: "superseded_primary", corrected: "current_correction",
             field: "randomized_primary" if randomized else "observational_primary",
             replication: "independent_primary" if independent_replication else "reanalysis",
             simulation: "simulation", commentary: "secondary_commentary"}
    answer = {
        "authoritative_table_source": corrected,
        "independent_units": n,
        "calculations": {"mean_baseline_K": mean_before, "mean_corrected_K": mean_after,
                         "relative_reduction_percent": relative,
                         "paired_mean_difference_K": statistics.mean(diffs),
                         "paired_standard_error_K": statistics.stdev(diffs)/math.sqrt(n)},
        "claims": {c: {"verdict": v, "sources": required[c]} for c, v in verdicts.items()},
        "source_roles": roles,
        "defensible_contribution": "bounded_empirical_improvement",
    }
    prompt = """审计这个完整合成证据包。先确定当前有效数据和独立统计单位，再复算
配对统计量，逐条判断 claims.json 的六个论断。分类含义：supported=在论断限定范围内
有直接支持；contradicted=证据给出不相容结果；insufficient=现有证据不足以判定。
每个论断列出直接支持该判断的最少来源，可加相关版本来源，不能把所有来源统一粘贴。
给出谨慎但保留实质价值的贡献表述，不得把合成材料当作真实论文。

提交一个 JSON 对象：{"task_id":"NRB01","answer":{...},"artifacts":{"reasoning.md":"..."}}。
answer 的精确结构（数字必须为 JSON number）：
{
  "authoritative_table_source":"SRC-xxx",
  "independent_units":0,
  "calculations":{"mean_baseline_K":0,"mean_corrected_K":0,
    "relative_reduction_percent":0,"paired_mean_difference_K":0,"paired_standard_error_K":0},
  "claims":{"C1":{"verdict":"supported|contradicted|insufficient","sources":["SRC-xxx"]},
    "C2":{...},"C3":{...},"C4":{...},"C5":{...},"C6":{...}},
  "source_roles":{"SRC-xxx":"角色", ...},
  "defensible_contribution":"bounded_empirical_improvement|universal_long_term_superiority|unique_mechanism_proof"
}
source_roles 必须覆盖六个来源；角色值从 superseded_primary, current_correction,
randomized_primary, observational_primary, independent_primary, reanalysis, simulation,
secondary_commentary 中按证据选择。reasoning.md 中逐条给出理由、统计公式、来源位置、
因果与推广边界，以及一段可接受的贡献表述和下一项最有价值的验证。
配对差定义为 baseline-corrected；相对下降使用设备均值之差除以基线设备均值，
不是逐设备百分比的平均。数值建议直接保留计算结果的浮点精度；如需缩短，至少保留 9 位有效数字。
使用科学计数法表示小量，不把谱密度、协方差或目标差舍入为零。
评分容差按字段定义，不要求输出额外无意义的小数。中文或英文论证均可。
"""
    rubric = [
        {"id": "evidence_reasoning", "title": "来源判断与论断边界", "anchors": {
            "0": "没有逐条证据推理，或将合成卡片伪装成真实文献。",
            "5": "主要判断有解释，但遗漏版本优先、因果假设或网格外边界。",
            "10": "逐条定位直接证据；解释更正、独立性、因果及缺失证据，限定范围准确。"}},
        {"id": "statistical_reasoning", "title": "配对分析与统计单位", "anchors": {
            "0": "仅报数字，或者将技术重复充作独立设备。",
            "5": "公式大体正确，但样本 SD、均值百分比或可复查计算有缺口。",
            "10": "推导与可复查计算一致，解释配对单位、n-1 分母及技术重复的角色。"}},
        {"id": "contribution_framing", "title": "有价值且有边界的研究表述", "anchors": {
            "0": "宣称普适性、唯一机制、真实发表或因先例/局限而否定全部价值。",
            "5": "保留合理贡献并指出局限，但下一步验证与证据缺口联系较弱。",
            "10": "给出可独立阅读的贡献段落，并提出针对最关键缺口的判别性验证。"}},
    ]
    return {"id": "NRB01", "seed": seed, "title": "版本冲突下的证据与贡献审计",
            "domain": "evidence_audit", "prompt": prompt,
            "files": {"evidence_packet.md": packet, "corrected_table.csv": stream.getvalue(),
                      "claims.json": json.dumps(claims, ensure_ascii=False, indent=2)+"\n"},
            "expected": {"answer": answer, "required_sources": required, "allowed_sources": allowed},
            "rubric": rubric}


def reference(case: dict) -> dict:
    ans = copy.deepcopy(case["expected"]["answer"])
    roles = set(ans["source_roles"].values())
    reasons = {
        "C1": f"按当前表复算相对下降为 {ans['calculations']['relative_reduction_percent']:.10g}%，与 claims.json 的阈值比较。",
        "C2": f"更正记录明确给出 {ans['independent_units']} 个独立设备，设备内重复不能增加这个数目。",
        "C3": ("外场记录明确给出随机分配、没有退出、无干扰及分配独立于潜在结果；在这些题定假设下组间差是无偏估计。"
               if "randomized_primary" in roles else
               "外场处理与地点完全混杂，并存在维护及设备年龄差异；该记录未提供消除混杂的设计或分析。"),
        "C4": ("后续记录列出与 CAL 系列不重合的 REP 序列，并明确重新采集数据。"
               if "independent_primary" in roles else
               "后续记录明确复用 CAL 原始数据并重新归一化，没有新增独立样本。"),
        "C5": ("四个所报计算点的移除模块结果全为零；仅在这个已报告网格内支持条件性必要。"
               if ans["claims"]["C5"]["verdict"] == "supported" else
               "移除模块后仍有正收益的计算点，因此存在该命题在所报网格内的直接反例。"),
        "C6": "外场记录的明确时长不足一年；二次评论没有增加更长期数据，所以一年性能尚无证据。",
    }
    rows = [f"- {cid}: {row['verdict']}，直接来源 {', '.join(row['sources'])}。{reasons[cid]}"
            for cid, row in ans["claims"].items()]
    reasoning = f"""# 合成证据的参考推理

本答复只使用本题提供的原创合成卡片；没有声称检索或读过真实论文。
当前有效表为 {ans['authoritative_table_source']}，独立设备 n={ans['independent_units']}。
先以设备内平均值形成配对差 d_i=baseline_i-corrected_i，再使用
mean(d)、s_d=sqrt(sum((d_i-mean(d))^2)/(n-1)) 与 SE=s_d/sqrt(n)。
相对下降为 100*(mean(baseline)-mean(corrected))/mean(baseline)。
技术重复提高设备内均值精度，但并不增加独立设备数。

{chr(10).join(rows)}

C1 应使用更正后的数据；C2 的跨设备推断必须保留设备统计单位。
C3 依赖外场记录是否明确随机分配、无退出和无干扰；观察性组间差异本身不能
排除地点、维护和设备年龄的混杂。C4 由新原始样本或重复使用的来源记录决定。
C5 只评价给定消融的四个计算点：移除后仍有正收益即反驳该范围内的必要性，
全部为零则只支持该计算范围内的条件性必要性，不能升级为真实器件的唯一机制。
C6 缺少一年运行数据，二次评论并未补上这个证据缺口。

可接受的贡献是：在给定三个温度设定点的配对台架协议中，这批记录器的平均绝对误差
经校正后下降；结论由当前有效原始表支持。其增量价值在于这个受限协议下的实证改善，
不需要声称普适优越性。下一步可对新设备随机分组，在预设长时窗口持续测试，预先
固定误差指标并记录退出与工况；这直接检验独立重复性和长期推广边界。
"""
    return {"task_id": "NRB01", "answer": ans, "artifacts": {"reasoning.md": reasoning}}


def grade(case: dict, submission, execution="none") -> list:
    ans = _mapping(_mapping(submission).get("answer"))
    ex = case["expected"]["answer"]
    claims = _mapping(ans.get("claims"))
    checks = []
    for cid, expected in ex["claims"].items():
        row = _mapping(claims.get(cid))
        checks.append(check(f"{cid}_verdict", 3, row.get("verdict") == expected["verdict"],
                            "判断必须与直接证据及限定范围一致。"))
        sources = row.get("sources")
        valid_sources = isinstance(sources, list) and all(isinstance(x, str) for x in sources)
        actual = set(sources) if valid_sources else set()
        required = set(case["expected"]["required_sources"][cid])
        allowed = set(case["expected"]["allowed_sources"][cid])
        checks.append(check(f"{cid}_sources", 2,
                            valid_sources and required <= actual <= allowed
                            and len(actual) == len(sources),
                            "来源必须覆盖直接证据；无关来源堆砌不计分。"))
    checks.append(check("current_source", 5,
                        ans.get("authoritative_table_source") == ex["authoritative_table_source"],
                        "采用当前有效更正记录。", critical=True))
    checks.append(check("independent_units", 5,
                        type(ans.get("independent_units")) is int
                        and ans["independent_units"] == ex["independent_units"],
                        "独立设备数，而非技术重复次数。", critical=True))
    calc, exp_calc = _mapping(ans.get("calculations")), ex["calculations"]
    checks.append(check("corrected_means", 5,
                        all(_near(calc.get(k), exp_calc[k]) for k in ["mean_baseline_K", "mean_corrected_K"]),
                        "从当前表复算的两个设备均值。"))
    for key in ["relative_reduction_percent", "paired_mean_difference_K", "paired_standard_error_K"]:
        checks.append(check(key, 5, _near(calc.get(key), exp_calc[key]),
                            "以独立配对设备和题定分母计算。"))
    checks.append(check("source_roles", 5, _mapping(ans.get("source_roles")) == ex["source_roles"],
                        "区分原始更正、随机/观察、独立/再分析、仿真及二次来源。"))
    checks.append(check("bounded_contribution", 5,
                        ans.get("defensible_contribution") == ex["defensible_contribution"],
                        "保留受限实证价值，同时守住真实证据强度。"))
    return checks

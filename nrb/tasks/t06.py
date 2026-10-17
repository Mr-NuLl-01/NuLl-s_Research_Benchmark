"""NRB06: generated non-optical sensor metrology with covariance and PSD."""

from __future__ import annotations

import copy
import csv
import io
import json
import math
import random

from nrb.checks import check, numbers_close


def _csv(rows, fields):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def _integrate_psd(frequencies, psd, low, high):
    total = 0.0
    for i in range(len(frequencies)-1):
        left, right = max(low, frequencies[i]), min(high, frequencies[i+1])
        if right <= left:
            continue
        slope = (psd[i+1]-psd[i])/(frequencies[i+1]-frequencies[i])
        value_left = psd[i]+slope*(left-frequencies[i])
        value_right = psd[i]+slope*(right-frequencies[i])
        total += (right-left)*(value_left+value_right)/2
    return total


def _calculate(rows, noise, measured):
    valid = [row for row in rows if row["status"] == "valid"]
    xs = [row["reference_mm"] for row in valid]
    ys = [row["voltage_mV"]*1e-3 for row in valid]
    weights = [1/(row["sigma_mV"]*1e-3)**2 for row in valid]
    sw = math.fsum(weights)
    sx = math.fsum(w*x for w, x in zip(weights, xs))
    sy = math.fsum(w*y for w, y in zip(weights, ys))
    sxx = math.fsum(w*x*x for w, x in zip(weights, xs))
    sxy = math.fsum(w*x*y for w, x, y in zip(weights, xs, ys))
    det = sw*sxx-sx*sx
    intercept = (sxx*sy-sx*sxy)/det
    slope = (sw*sxy-sx*sy)/det
    caa, cab, cbb = sxx/det, -sx/det, sw/det
    covariance = [[caa, cab], [cab, cbb]]
    chi2 = math.fsum(w*(y-intercept-slope*x)**2 for w, x, y in zip(weights, xs, ys))
    vm = measured["mean_voltage_mV"]*1e-3
    sigma_v2 = (measured["repeatability_sigma_mean_mV"]*1e-3)**2 + (measured["display_step_mV"]*1e-3)**2/12
    x = (vm-intercept)/slope
    terms = {"sample_voltage": sigma_v2/slope**2,
             "intercept": caa/slope**2,
             "slope": x*x*cbb/slope**2,
             "coefficient_covariance": 2*x*cab/slope**2}
    ux = math.sqrt(math.fsum(terms.values()))
    psd = [(row["value"]*1e-6)**2 if row["unit"] == "uV/sqrt(Hz)" else row["value"] for row in noise]
    frequencies = [row["frequency_Hz"] for row in noise]
    area = _integrate_psd(frequencies, psd, measured["band_low_Hz"], measured["band_high_Hz"])
    rms_v = math.sqrt(area)
    return {"included_calibration_ids": [row["id"] for row in valid],
            "calibration": {"intercept_V": intercept, "slope_V_per_mm": slope,
                            "covariance_ab": covariance, "chi2": chi2, "degrees_of_freedom": len(valid)-2},
            "displacement_mm": x,
            "variance_terms_mm2": terms,
            "standard_uncertainty_mm": ux, "expanded_k2_mm": 2*ux,
            "psd_V2_per_Hz": psd,
            "noise_integral_V2": area,
            "noise_rms_V": rms_v, "noise_rms_mm": rms_v/abs(slope)}


def build(seed=0):
    rng = random.Random(f"NRB06:{seed}")
    intercept = rng.uniform(0.07, 0.19)
    slope = rng.uniform(0.32, 0.61)
    xscale = rng.uniform(0.8, 1.15)
    rows = []
    for i, base_x in enumerate((0.0, 0.5, 1.2, 1.7, 2.4, 3.1, 4.0)):
        x = round(base_x*xscale, 5)
        sigma = round(rng.uniform(1.7, 5.2), 5)
        voltage = 1000*(intercept+slope*x) + rng.gauss(0.0, sigma*1.4)
        rows.append({"id": f"C{i+1:02d}", "reference_mm": x, "voltage_mV": round(voltage, 6),
                     "sigma_mV": sigma, "status": "valid"})
    rows.insert(rng.randrange(1, len(rows)), {"id": "C_SAT", "reference_mm": round(5.4*xscale, 5),
                                             "voltage_mV": 2100.0, "sigma_mV": 3.0, "status": "saturated"})
    freq_scale = rng.uniform(0.8, 1.4)
    frequencies = [round(x*freq_scale, 4) for x in (4, 23, 75, 190, 580, 1500, 3800)]
    noise = []
    noise_level = rng.uniform(0.5, 1.6)*1e-12
    for i, f in enumerate(frequencies):
        s = noise_level*(1+48/(f+5))*(1+rng.uniform(-0.06, 0.06))
        if (i+seed) % 2 == 0:
            value, unit = math.sqrt(s)*1e6, "uV/sqrt(Hz)"
        else:
            value, unit = s, "V^2/Hz"
        noise.append({"frequency_Hz": f, "value": value, "unit": unit})
    measurement = {"mean_voltage_mV": round(1000*(intercept+slope*rng.uniform(1.9, 2.8)*xscale), 6),
                   "repeatability_sigma_mean_mV": round(rng.uniform(1.1, 2.7), 6),
                   "display_step_mV": round(rng.uniform(0.7, 1.6), 6),
                   "band_low_Hz": round(rng.uniform(29, 56)*freq_scale, 4),
                   "band_high_Hz": round(rng.uniform(1850, 2750)*freq_scale, 4)}
    policy = """# Synthetic sensor metrology contract

These are generated exercise data for a generic displacement transducer. They
do not originate from a real instrument, person, project, or experiment.

Calibration: use status=valid rows only, preserving file order in returned IDs.
Reference positions x in mm are exact for this exercise. Convert mV to V.
Fit V=a+b*x by weighted least squares with w_i=1/sigma_i^2. The supplied sigma_i
are known independent absolute voltage standard uncertainties. Use
Cov(a,b)=(X^T W X)^(-1), ordered [a,b]; do NOT multiply it by reduced chi-square.
Report chi-square and n-2 separately. Flagged saturated points are not valid fit data.

Unknown sample: x=(V_mean-a)/b. Its voltage mean is independent of the calibration.
The provided repeatability_sigma_mean_mV is already the standard uncertainty
of the mean, not the standard deviation of individual readings. Independent
display rounding has a uniform distribution over +/-display_step_mV/2.
Therefore Var(V_mean)=sigma_mean^2+display_step^2/12, after unit conversion.
First-order uncertainty propagation must retain the fitted a,b covariance.
Report each contribution in mm^2: sample_voltage, intercept, slope,
coefficient_covariance (which may be negative), plus standard_uncertainty_mm.
expanded_k2_mm=2*standard_uncertainty_mm; the name does not assert exact 95% coverage.

Noise: every row is an independent format-tagged spectral sample from the SAME
one-sided voltage-noise spectrum at positive f. uV/sqrt(Hz) means ASD; convert
to V/sqrt(Hz) and square. V^2/Hz is already PSD. Report PSD in file order.
Between tabulated knots, PSD (not ASD) varies linearly. An ideal measurement
filter has |H|^2=1 inside the stated [band_low_Hz,band_high_Hz], zero outside.
Integrate PSD over the exact band including partial end intervals. As the
spectrum is one-sided, do not insert an extra factor of two. Return the integral
in V^2, its square root in V, and that RMS divided by abs(b) in mm.
This separate spectral calculation must not be added a second time to the given
repeatability uncertainty. No spectral extrapolation is needed.
"""
    prompt = """为通用位移传感器完成一份可复核的校准与噪声分析。数据全部为生成的教学数据。
处理饱和标志与单位，按 DATA_README.md 拟合校准、传播相关参数不确定度，再积分混合 ASD/PSD 格式
的单边噪声谱。说明哪些量是给定假设，哪些量由数据计算；不得把 k=2 自动说成严格的 95% 区间。

输出严格 JSON：{"task_id":"NRB06","answer":{"included_calibration_ids":["id"],
"calibration":{"intercept_V":number,"slope_V_per_mm":number,"covariance_ab":[[number,number],[number,number]],
"chi2":number,"degrees_of_freedom":integer},"displacement_mm":number,
"variance_terms_mm2":{"sample_voltage":number,"intercept":number,"slope":number,"coefficient_covariance":number},
"standard_uncertainty_mm":number,"expanded_k2_mm":number,"psd_V2_per_Hz":[number],
"noise_integral_V2":number,"noise_rms_V":number,"noise_rms_mm":number},
"artifacts":{"reasoning.md":"含公式、单位、关键中间量与复现方法的说明"}}。
答案须保留足够有效位数，尤其不能将小的谱密度或协方差四舍五入为零。"""
    return {"id": "NRB06", "seed": seed, "title": "传感器校准、噪声谱与相关不确定度", "domain": "metrology-and-uncertainty",
            "prompt": prompt,
            "files": {"calibration.csv": _csv(rows, ["id", "reference_mm", "voltage_mV", "sigma_mV", "status"]),
                      "noise.csv": _csv(noise, ["frequency_Hz", "value", "unit"]),
                      "measurement.json": json.dumps(measurement, indent=2), "DATA_README.md": policy},
            "expected": {"answer": _calculate(rows, noise, measurement), "rows": rows, "noise": noise, "measurement": measurement},
            "rubric": [
                {"id": "traceability", "title": "单位、数据选择与计算可追溯性", "anchors": {"0": "忽略单位/质量标志或捏造实验出处。", "5": "主要单位和数据选择正确，但复现步骤不完整。", "10": "明确生成数据与给定假设，逐项记录转换、排除规则和可复现计算；数值有效位合理。"}},
                {"id": "uncertainty", "title": "不确定度解释", "anchors": {"0": "混淆标准差、均值不确定度和扩展不确定度，或忽略协方差。", "5": "使用协方差但对绝对权重、量化误差或覆盖率解释不足。", "10": "给出雅可比、协方差项和独立性条件，解释为何不按残差重标定、为何 k=2 不等于自动精确 95%。"}},
                {"id": "spectrum", "title": "谱定义与可解释报告", "anchors": {"0": "把 ASD 当 PSD 积分或混淆单边/双边谱。", "5": "谱处理正确，但滤波带宽、插值或噪声换算解释不完整。", "10": "清楚区分 ASD/PSD、单边谱、PSD 插值和带内积分，给出量纲检查并说明谱积分与重复性项不可重复计入。"}}]}


def reference(case):
    return {"task_id": "NRB06", "answer": copy.deepcopy(case["expected"]["answer"]),
            "artifacts": {"reasoning.md": "用已知绝对 sigma 构造 W，对 X=[1,x] 做 WLS；参数协方差是 (XᵀWX)⁻¹，不乘约化卡方。未知位置 x=(V-a)/b 的雅可比为 (1/b,-1/b,-x/b)，保留 2*x*Cov(a,b)/b²。均值电压方差加入独立均匀显示舍入 q²/12。谱先全部转换成单边 PSD，再在线性 PSD 插值下对精确通带做分段梯形积分，最后开方。数据为合成练习；k=2 仅是指定扩展因子。"}}


def grade(case, submission, execution="none"):
    answer = submission.get("answer", {}) if isinstance(submission, dict) else {}
    answer = answer if isinstance(answer, dict) else {}
    wanted = case["expected"]["answer"]
    cal = answer.get("calibration", {})
    cal = cal if isinstance(cal, dict) else {}
    terms = answer.get("variance_terms_mm2", {})
    terms = terms if isinstance(terms, dict) else {}
    def subset(values, keys):
        return {key: values.get(key) for key in keys}
    return [
        check("quality_flag_selection", 5, numbers_close(answer.get("included_calibration_ids"), wanted["included_calibration_ids"]), "仅使用有效校准行，并保留文件顺序。"),
        check("weighted_calibration", 10, numbers_close(subset(cal, ("intercept_V", "slope_V_per_mm")), subset(wanted["calibration"], ("intercept_V", "slope_V_per_mm")), rtol=2e-6, atol=1e-10), "WLS 系数与 mV 到 V 转换。"),
        check("absolute_covariance", 10, numbers_close(cal.get("covariance_ab"), wanted["calibration"]["covariance_ab"], rtol=2e-6, atol=1e-18), "绝对已知权重的协方差，不按约化卡方缩放。", critical=True),
        check("fit_diagnostic", 5, numbers_close(subset(cal, ("chi2", "degrees_of_freedom")), subset(wanted["calibration"], ("chi2", "degrees_of_freedom")), rtol=2e-6, atol=1e-9), "残差卡方和自由度单独报告。"),
        check("inverse_calibration", 5, numbers_close(answer.get("displacement_mm"), wanted["displacement_mm"], rtol=2e-6, atol=1e-9), "样品均值的逆校准。"),
        check("independent_variance_terms", 5, numbers_close(subset(terms, ("sample_voltage", "intercept", "slope")), subset(wanted["variance_terms_mm2"], ("sample_voltage", "intercept", "slope")), rtol=3e-6, atol=1e-17), "均值、显示量化和参数方差贡献。"),
        check("covariance_variance_term", 5, numbers_close(terms.get("coefficient_covariance"), wanted["variance_terms_mm2"]["coefficient_covariance"], rtol=3e-6, atol=1e-17), "正确保留带符号的参数协方差贡献。", critical=True),
        check("combined_uncertainty", 5, numbers_close(subset(answer, ("standard_uncertainty_mm", "expanded_k2_mm")), subset(wanted, ("standard_uncertainty_mm", "expanded_k2_mm")), rtol=3e-6, atol=1e-12), "标准不确定度与指定 k=2 扩展值。"),
        check("asd_to_psd", 8, numbers_close(answer.get("psd_V2_per_Hz"), wanted["psd_V2_per_Hz"], rtol=3e-6, atol=1e-24), "小量专用绝对容差，零谱不能误获分。", critical=True),
        check("partial_band_integral", 6, numbers_close(answer.get("noise_integral_V2"), wanted["noise_integral_V2"], rtol=3e-6, atol=1e-22), "在线性 PSD 插值下积分完整与部分区间。"),
        check("rms_and_input_referred_noise", 6, numbers_close(subset(answer, ("noise_rms_V", "noise_rms_mm")), subset(wanted, ("noise_rms_V", "noise_rms_mm")), rtol=3e-6, atol=1e-14), "平方根及除以校准灵敏度。")]

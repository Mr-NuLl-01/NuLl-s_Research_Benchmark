# NRB06 · 传感器校准、噪声谱与相关不确定度

为通用位移传感器完成一份可复核的校准与噪声分析。数据全部为生成的教学数据。
处理饱和标志与单位，按 DATA_README.md 拟合校准、传播相关参数不确定度，再积分混合 ASD/PSD 格式
的单边噪声谱。说明哪些量是给定假设，哪些量由数据计算；不得把 k=2 自动说成严格的 95% 区间。

输出严格 JSON：{"task_id":"NRB06","answer":{"included_calibration_ids":["id"],
"calibration":{"intercept_V":number,"slope_V_per_mm":number,"covariance_ab":[[number,number],[number,number]],
"chi2":number,"degrees_of_freedom":integer},"displacement_mm":number,
"variance_terms_mm2":{"sample_voltage":number,"intercept":number,"slope":number,"coefficient_covariance":number},
"standard_uncertainty_mm":number,"expanded_k2_mm":number,"psd_V2_per_Hz":[number],
"noise_integral_V2":number,"noise_rms_V":number,"noise_rms_mm":number},
"artifacts":{"reasoning.md":"含公式、单位、关键中间量与复现方法的说明"}}。
答案须保留足够有效位数，尤其不能将小的谱密度或协方差四舍五入为零。

## 提交协议 / Submission contract
返回一个 UTF-8 JSON 对象（可使用单个 json 代码块），或将该对象写入 submission.json。
顶层格式：{"task_id":"NRB06","answer":{...},"artifacts":{"relative/path":"完整文件内容"}}。
answer 使用本题字段。代码、推导、图和修订稿放入 artifacts，字符串须包含完整内容，不能只返回本机路径。
数值使用 JSON number，缺失使用 null；不接受 NaN/Infinity。不同题目独立完成。
输入均为本基准原创构造的合成材料，不代表真实实验或真实未发表研究。
封闭资料轨道只使用本题材料与通用知识。不得查找本基准源码、答案或评分器。
每题自动核验 70 分，另有以下三项各 10 分的独立质量审阅。

[
  {
    "id": "traceability",
    "title": "单位、数据选择与计算可追溯性",
    "anchors": {
      "0": "忽略单位/质量标志或捏造实验出处。",
      "5": "主要单位和数据选择正确，但复现步骤不完整。",
      "10": "明确生成数据与给定假设，逐项记录转换、排除规则和可复现计算；数值有效位合理。"
    }
  },
  {
    "id": "uncertainty",
    "title": "不确定度解释",
    "anchors": {
      "0": "混淆标准差、均值不确定度和扩展不确定度，或忽略协方差。",
      "5": "使用协方差但对绝对权重、量化误差或覆盖率解释不足。",
      "10": "给出雅可比、协方差项和独立性条件，解释为何不按残差重标定、为何 k=2 不等于自动精确 95%。"
    }
  },
  {
    "id": "spectrum",
    "title": "谱定义与可解释报告",
    "anchors": {
      "0": "把 ASD 当 PSD 积分或混淆单边/双边谱。",
      "5": "谱处理正确，但滤波带宽、插值或噪声换算解释不完整。",
      "10": "清楚区分 ASD/PSD、单边谱、PSD 插值和带内积分，给出量纲检查并说明谱积分与重复性项不可重复计入。"
    }
  }
]

Required artifacts: reasoning.md


## 输入文件：DATA_README.md
<BEGIN_INPUT_FILE>

# Synthetic sensor metrology contract

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


<END_INPUT_FILE>


## 输入文件：calibration.csv
<BEGIN_INPUT_FILE>

id,reference_mm,voltage_mV,sigma_mV,status
C01,0.0,86.195872,4.20023,valid
C02,0.5661,403.956003,4.36708,valid
C_SAT,6.11389,2100.0,3.0,saturated
C03,1.35864,848.131429,4.34317,valid
C04,1.92474,1177.072751,3.99133,valid
C05,2.71728,1635.328949,3.22854,valid
C06,3.50983,2085.398519,4.92806,valid
C07,4.52881,2661.331065,4.8673,valid


<END_INPUT_FILE>


## 输入文件：measurement.json
<BEGIN_INPUT_FILE>

{
  "mean_voltage_mV": 1623.060309,
  "repeatability_sigma_mean_mV": 1.561912,
  "display_step_mV": 1.058606,
  "band_low_Hz": 37.8753,
  "band_high_Hz": 2106.0035
}

<END_INPUT_FILE>


## 输入文件：noise.csv
<BEGIN_INPUT_FILE>

frequency_Hz,value,unit
4.3794,2.135205783806579,uV/sqrt(Hz)
25.1815,2.0876058682124458e-12,V^2/Hz
82.1136,1.0918631686667544,uV/sqrt(Hz)
208.0212,9.290390097497839e-13,V^2/Hz
635.0122,0.9123487203530728,uV/sqrt(Hz)
1642.273,8.083281025767375e-13,V^2/Hz
4160.4249,0.8731030636040518,uV/sqrt(Hz)


<END_INPUT_FILE>

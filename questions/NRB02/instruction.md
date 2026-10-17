# NRB02 · 热响应中的参数退化与判别实验

一个经典集中热容系统满足
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
数字保留至少 6 位有效数字。


## 提交协议 / Submission contract
返回一个 UTF-8 JSON 对象（可使用单个 json 代码块），或将该对象写入 submission.json。
顶层格式：{"task_id":"NRB02","answer":{...},"artifacts":{"relative/path":"完整文件内容"}}。
answer 使用本题字段。代码、推导、图和修订稿放入 artifacts，字符串须包含完整内容，不能只返回本机路径。
数值使用 JSON number，缺失使用 null；不接受 NaN/Infinity。不同题目独立完成。
输入均为本基准原创构造的合成材料，不代表真实实验或真实未发表研究。
封闭资料轨道只使用本题材料与通用知识。不得查找本基准源码、答案或评分器。
每题自动核验 70 分，另有以下三项各 10 分的独立质量审阅。

[
  {
    "id": "identifiability_proof",
    "title": "结构可辨识性推导",
    "anchors": {
      "0": "直接报告唯一拟合参数，未识别退化或把数值优化成功当作唯一性。",
      "5": "识别比例退化，但只对单一阶跃说明，或结构秩论证不完整。",
      "10": "从微分方程给出任意已知输入下的尺度等价性，推导三个独立组合与秩。"
    }
  },
  {
    "id": "intervention_design",
    "title": "判别实验与模型假设",
    "anchors": {
      "0": "所选方案不破退化，或者忽略加入附件同时改变其他参数。",
      "5": "方案正确但缺少参数恢复公式、保持条件或实际校验。",
      "10": "推导两时间常数恢复公式，明确 G/增益不变的验证及扰动带来的限制。"
    }
  },
  {
    "id": "prediction_and_uncertainty",
    "title": "独立预测与实际精度",
    "anchors": {
      "0": "只抄拟合值，未解释脉冲预测或声称无噪声结果代表现实精度。",
      "5": "脉冲与偏移处理正确，但未讨论差分恢复的误差放大。",
      "10": "给出分段解析预测和可复查计算，讨论小时间常数差导致的不稳定及验证措施。"
    }
  }
]

Required artifacts: reasoning.md


## 输入文件：baseline.json
<BEGIN_INPUT_FILE>

{
  "provenance": "original deterministic synthetic observations, not measured data",
  "power_W": 8.6,
  "initial_temperature_difference_K": 0,
  "observations": [
    [
      0.0,
      0.02
    ],
    [
      1.7,
      0.40616796443105
    ],
    [
      3.4,
      0.74827477179635
    ],
    [
      5.1,
      1.05134773078226
    ],
    [
      6.8,
      1.31984054206501
    ],
    [
      8.5,
      1.55769874608202
    ]
  ],
  "columns": [
    "time_s",
    "sensor_reading"
  ],
  "noise": "none; rounded to 14 decimal places"
}


<END_INPUT_FILE>


## 输入文件：intervention_observations.json
<BEGIN_INPUT_FILE>

{
  "provenance": "original deterministic synthetic intervention observations",
  "power_W": 8.6,
  "added_capacity_J_per_K": 41.5,
  "assumptions": "Only C changes to C+delta_C; G, gain and offset are unchanged.",
  "initial_temperature_difference_K": 0,
  "observations": [
    [
      0.0,
      0.02
    ],
    [
      1.7,
      0.22346733928642
    ],
    [
      3.4,
      0.41470280950264
    ],
    [
      5.1,
      0.59444175530631
    ],
    [
      6.8,
      0.76337531455705
    ],
    [
      8.5,
      0.92215307590153
    ]
  ],
  "columns": [
    "time_s",
    "sensor_reading"
  ]
}


<END_INPUT_FILE>


## 输入文件：interventions.json
<BEGIN_INPUT_FILE>

{
  "I1": "重复原实验 100 次，保持所有物理配置与测量通道不变。",
  "I2": "仅将已校准输入功率加倍，仍只测同一传感器读数。",
  "I3": "加入精确已知的 41.5 J/K 热容，且验证 G、传感器增益及偏移均不变。",
  "I4": "对原功率任意延长时间并加密采样，不引入新绝对标定。"
}


<END_INPUT_FILE>


## 输入文件：prediction.json
<BEGIN_INPUT_FILE>

{
  "configuration": "original C (added capacity removed)",
  "power_W": 3.2,
  "pulse_on_interval_s": [
    0,
    24.4
  ],
  "observation_times_s": [
    24.4,
    35.7
  ],
  "initial_temperature_difference_K": 0
}


<END_INPUT_FILE>

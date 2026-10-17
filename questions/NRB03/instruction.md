# NRB03 · 有限预算下的鲁棒校准设计

为一个通用线性量具的斜率校准分配有限测量次数。
design.json 给出五个输入水平、各次测量成本、每水平次数上限、预算与总次数约束，
以及三个候选单次测量方差情景。请求解离散的全局 minimax 设计，不能只把次数
均分、按成本分配、优化平均方差或把截距当作已知。三个情景无需设概率。

设计在情景揭示前选择；分析前可通过独立校准确知情景并使用正确加权最小二乘。
因此，对情景 s，信息矩阵为 sum_i [n_i/v_si]*[[1,x_i],[x_i,x_i^2]]，
目标是其逆矩阵中斜率方差的三个情景最大值。v_si 是方差，不是标准差。

除预算和各次数上限外，还必须满足：min_total<=sum(n)<=max_total，中心次数
n[2]>=min_center，左右两侧各至少 min_each_side 次，两个最外端总次数不超过
max_extreme_total。计数“feasible_allocation_count”时统计满足所有上述约束且
可估计截距/斜率的整数向量，每个向量只计一次。

提交 JSON：{"task_id":"NRB03","answer":{...},"artifacts":{"reasoning.md":"...","solve.py":"..."}}。
answer 精确结构：
{
 "allocation":[0,0,0,0,0], "total_cost":0, "total_measurements":0,
 "scenario_slope_variances":[0,0,0], "worst_slope_variance":0, "worst_scenario":1,
 "feasible_allocation_count":0,
 "second_distinct_allocation":[0,0,0,0,0],
 "second_distinct_objective":0, "objective_gap":0
}
worst_scenario 为 1 起始情景编号。任意全局最优向量均接受；second_distinct 是
严格次优目标（精确目标与精确最优值差大于 1e-12 的最小层级），并非另一并列最优向量。
公开有限小数定义精确输入；全局最优向量必须达到精确最小值，显示数值的容差不扩大最优集合。objective_gap
为该严格次优值减最优值。自动数值评分也检查你给出的实际分配的约束和方差，
不能只填写最优目标数字。reasoning.md 解释含未知截距的方差推导、鲁棒目标、
全局最优性证据与适用条件；solve.py 提供仅依赖标准 Python 的可复查枚举或等价算法。
solve.py 必须定义 solve(problem)：problem 是解析 design.json 后的字典，返回与上述 answer
字段、类型完全相同的字典，不含 task_id/artifacts 包装，不读其他文件。模块导入不得运行命令行入口。
独立质量验收必须实际调用该入口并核对其结果与所交答案及所选向量一致；未实际执行不能算完成复现。
不要声称这些合成情景来自实际测量。数值建议直接保留计算结果的浮点精度；如需缩短，至少保留 9 位有效数字。
使用科学计数法表示小量，不把谱密度、协方差或目标差舍入为零。
评分容差按字段定义，不要求输出额外无意义的小数。


## 提交协议 / Submission contract
返回一个 UTF-8 JSON 对象（可使用单个 json 代码块），或将该对象写入 submission.json。
顶层格式：{"task_id":"NRB03","answer":{...},"artifacts":{"relative/path":"完整文件内容"}}。
answer 使用本题字段。代码、推导、图和修订稿放入 artifacts，字符串须包含完整内容，不能只返回本机路径。
数值使用 JSON number，缺失使用 null；不接受 NaN/Infinity。不同题目独立完成。
输入均为本基准原创构造的合成材料，不代表真实实验或真实未发表研究。
封闭资料轨道只使用本题材料与通用知识。不得查找本基准源码、答案或评分器。
每题自动核验 70 分，另有以下三项各 10 分的独立质量审阅。

[
  {
    "id": "design_derivation",
    "title": "设计目标与统计模型",
    "anchors": {
      "0": "使用方差均值、漏掉截距或混淆方差/标准差，未提出正确目标。",
      "5": "目标正确但信息矩阵、单次/重复方差或情景识别假设解释不全。",
      "10": "从 WLS 信息矩阵推导含未知截距的斜率方差，并明确 minimax 与分析假设。"
    }
  },
  {
    "id": "optimality_evidence",
    "title": "可复查的全局最优性",
    "anchors": {
      "0": "只报最优答案或声称搜索完成而没有代码/可复查证据。",
      "5": "有可运行搜索，但约束覆盖、并列值或严格次优处理不清楚。",
      "10": "独立可运行算法覆盖完整可行域，统计数目、并列值与次优差均可复查。"
    }
  },
  {
    "id": "design_interpretation",
    "title": "设计解释与适用边界",
    "anchors": {
      "0": "把合成优化结果宣称为真实实验最优或忽略模型假设。",
      "5": "解释最坏情景与预算约束，但缺乏对模型改变的具体影响判断。",
      "10": "解释最坏情景/实际活跃约束，讨论相关误差、未涵盖情景或模型曲率如何改变结论。"
    }
  }
]

## 核心完成条件（独立于分数）
以下责任逐项以 pass/fail/unassessed 审阅；高分不能补偿核心责任失败。
[
  {
    "id": "search_reproduced",
    "requirement": "按公开 solve(problem) 入口实际执行必交搜索代码，结果与提交和精确最优层级一致；须有绑定的执行回执。"
  },
  {
    "id": "optimality_explanation",
    "requirement": "搜索、全部约束与最优性论证可复查，和交付代码相符。"
  }
]

Required artifacts: reasoning.md, solve.py


## 输入文件：design.json
<BEGIN_INPUT_FILE>

{
  "provenance": "Original synthetic calibration-design instance; no real experiment data.",
  "model": "y=intercept+slope*x+epsilon; intercept and slope both unknown",
  "x": [
    -5,
    -2,
    0,
    1,
    3
  ],
  "costs": [
    3,
    1,
    1,
    1,
    3
  ],
  "max_replicates": [
    5,
    4,
    3,
    6,
    3
  ],
  "budget": 28,
  "min_total": 8,
  "max_total": 12,
  "min_center": 2,
  "min_each_side": 2,
  "max_extreme_total": 6,
  "variance_scenarios": [
    [
      3.75,
      3.49,
      2.66,
      1.64,
      1.02
    ],
    [
      2.84,
      1.06,
      3.18,
      1.08,
      2.52
    ],
    [
      0.83,
      1.75,
      2.84,
      3.25,
      6.39
    ]
  ],
  "variance_units": "sensor_reading squared; these are variances, NOT standard deviations",
  "assumptions": [
    "All replicate errors independent with zero mean.",
    "The listed variance is per single measurement at each x.",
    "The design must be chosen before the scenario is revealed.",
    "A separate calibration identifies the true scenario before analysis; use its correct WLS weights.",
    "The model is linear over these levels; center quota is an imposed practical constraint."
  ],
  "objective": "minimize the maximum variance of the estimated slope across the three scenarios",
  "tie_policy": "Finite decimal inputs are exact. Any exact global minimizer is accepted; runner-up is the minimum objective strictly greater than the exact minimum plus 1e-12. Display tolerances do not widen either allocation set."
}


<END_INPUT_FILE>

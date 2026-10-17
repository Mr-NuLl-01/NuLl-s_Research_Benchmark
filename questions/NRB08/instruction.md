# NRB08 · 仿射收缩的证明、反例与误差证书

对 affine.json 中 F:R^3->R^3, F(x)=Ax+b，完成解析证明、数值证书和反例。
使用指定权重的无穷范数，计算精确诱导算子范数 q（不是任选一个更松上界）以及
普通无穷范数下的算子范数。证明该系统固定点存在且唯一，求固定点，计算题定
候选点的残差向量、加权残差范数，以及残差推导出的误差上界和实际加权误差。

另外反驳文件中 false_claim：不能未经证明把同一范数下的收缩常数换为谱半径。
请自行给出 2x2 实矩阵、向量 b 和 x_hat；为了数值判别清楚，要求全部元素绝对值
<=100，rho(A)<=0.95，残差无穷范数>1e-8，并让实际误差至少为错误上界的 1.2 倍。
反例可以不同于题给 3x3 系统。评分器会由你交的矩阵重新求解和计算，不接受仅写
“非正规矩阵可能有问题”。必须区分一般定理证明、具体数值检验和反例的逻辑角色。

提交 JSON：{"task_id":"NRB08","answer":{...},"artifacts":{"reasoning.md":"..."}}。
answer 的精确结构：
{
 "weighted_operator_norm":0,"unweighted_operator_norm":0,
 "fixed_point":[0,0,0],"residual_vector":[0,0,0],"weighted_residual_norm":0,
 "certified_weighted_error_bound":0,"actual_weighted_error":0,
 "claims":{"unique_fixed_point":"boolean，由你判断","ordinary_infinity_contraction":"boolean，由你判断",
   "spectral_radius_substitution_universally_valid":"boolean，由你判断"},
 "counterexample":{"A":[[0,0],[0,0]],"b":[0,0],"x_hat":[0,0],
   "fixed_point":[0,0],"spectral_radius":0,"residual_infinity_norm":0,
   "actual_infinity_error":0,"claimed_bound":0}
}
claims 中三个字段的提交类型均为 JSON boolean；上面的类型说明不是待复制的取值。
reasoning.md 须包含：算子范数的推导、完备性与自映射条件、存在及唯一性论证、
对任意候选点成立的残差不等式推导，以及反例如何击破原命题。
普通无穷范数不收缩不能单独推出固定点不存在。数值保留至少 8 位有效数字；
解析公式给出理论证书，其小数展示是近似值。本题不要求有向舍入区间证书或 Lean。


## 提交协议 / Submission contract
返回一个 UTF-8 JSON 对象（可使用单个 json 代码块），或将该对象写入 submission.json。
顶层格式：{"task_id":"NRB08","answer":{...},"artifacts":{"relative/path":"完整文件内容"}}。
answer 使用本题字段。代码、推导、图和修订稿放入 artifacts，字符串须包含完整内容，不能只返回本机路径。
数值使用 JSON number，缺失使用 null；不接受 NaN/Infinity。不同题目独立完成。
输入均为本基准原创构造的合成材料，不代表真实实验或真实未发表研究。
封闭资料轨道只使用本题材料与通用知识。不得查找本基准源码、答案或评分器。
每题自动核验 70 分，另有以下三项各 10 分的独立质量审阅。

[
  {
    "id": "contraction_proof",
    "title": "完整的定理责任",
    "anchors": {
      "0": "用一次数值试验充当存在唯一性证明，或混淆充分与必要条件。",
      "5": "引用收缩结论合理，但加权范数、自映射、完备性或唯一性有遗漏。",
      "10": "完整说明范数与收缩常数、R^3 完备自映射，以及存在和唯一性的推导。"
    }
  },
  {
    "id": "certificate_derivation",
    "title": "残差与误差的逻辑联系",
    "anchors": {
      "0": "把残差直接当误差或只列近似数值，没有一般不等式。",
      "5": "公式正确但缺少推导、范数一致性或数值/严格性边界。",
      "10": "从任意点推导 e<=r+qe 及证书，明确固定点误差与舍入近似的不同责任。"
    }
  },
  {
    "id": "counterexample_explanation",
    "title": "反例的有效性与解释",
    "anchors": {
      "0": "没有实际反例或只是说明收敛可能缓慢。",
      "5": "反例计算有效，但未指出谱半径不能替代给定范数的 Lipschitz 常数。",
      "10": "逐项核验原命题假设和失败结论，并解释非正规性/范数选择而不否定正确收缩定理。"
    }
  }
]

## 核心完成条件（独立于分数）
以下责任逐项以 pass/fail/unassessed 审阅；高分不能补偿核心责任失败。
[
  {
    "id": "existence_uniqueness",
    "requirement": "完整证明存在唯一性，明确空间、范数和收缩条件。"
  },
  {
    "id": "residual_bound_proof",
    "requirement": "推导一般残差误差界，范数、常数和不等式方向一致。"
  },
  {
    "id": "counterexample_explanation",
    "requirement": "反例满足所检验前提并确实推翻指定结论，有可核查解释。"
  }
]

Required artifacts: reasoning.md


## 输入文件：affine.json
<BEGIN_INPUT_FILE>

{
  "provenance": "Original synthetic affine system using classical linear algebra.",
  "A": [
    [
      0.13,
      0.01125,
      0.0425
    ],
    [
      1.44,
      0.17,
      0.56
    ],
    [
      0.48,
      -0.025,
      0.12
    ]
  ],
  "b": [
    -2.4696875,
    3.1875,
    2.86625
  ],
  "weights": [
    1,
    16,
    4
  ],
  "x_hat": [
    -2.72,
    -0.39,
    1.87
  ],
  "domain": "R^3",
  "map": "F(x)=A*x+b",
  "norm": "||v||_(infinity,w)=max_i |v_i|/weights_i",
  "residual_definition": "F(x_hat)-x_hat",
  "number_convention": "Displayed finite decimals define the input matrix and vectors.",
  "false_claim": "For every affine F with spectral radius rho(A)<1, in the ordinary infinity norm: ||x_hat-x_star|| <= ||F(x_hat)-x_hat||/(1-rho(A))."
}


<END_INPUT_FILE>

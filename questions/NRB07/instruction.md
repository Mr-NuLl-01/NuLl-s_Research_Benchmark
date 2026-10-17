# NRB07 · 重复测量下的数据泄漏与分组评测

审阅一份通用机械状态分类评测。每台机器有重复读数，原始按读数划分的数据集可能泄漏。
所有表格和预测均为合成数据。请查出跨划分的机器，按预先固定的规则修复划分；用验证集 macro-F1
选定模型，再报告该模型的测试指标和以机器为单位的 bootstrap 不确定度。不要用测试成绩重新选模型。
必须按 row_id 连接文件，并严格遵守 protocol.json 的指标、空分母及分位数定义。

返回 JSON：{"task_id":"NRB07","answer":{"leaked_machine_ids":["按字典序列出的机器 ID"],
"repaired_group_split":{"每个 machine_id":"train|validation|test 中的单个值"},
"validation_macro_f1":{"model_a":number,"model_b":number},"selected_model":"model_a|model_b 中的单个值",
"test_confusion_matrix":[[integer,integer,integer],[integer,integer,integer],[integer,integer,integer]],
"test_per_class":{"intact":{"precision":number,"recall":number,"f1":number},
"surface_wear":{"precision":number,"recall":number,"f1":number},"joint_loose":{"precision":number,"recall":number,"f1":number}},
"test_metrics":{"accuracy":number,"macro_f1":number,"balanced_accuracy":number},
"test_sample_size":{"readings":integer,"independent_machines":integer},
"bootstrap":{"replicates":integer,"macro_f1_mean":number,"macro_f1_standard_error":number,"percentile95":[number,number]}},
"artifacts":{"reasoning.md":"数据泄漏判断、冻结选择、复现方法和不确定度解释"}}。
上述字符串模板必须替换为真实值。人工评分关注评测解释，不按关键词数量计分。

## 提交协议 / Submission contract
返回一个 UTF-8 JSON 对象（可使用单个 json 代码块），或将该对象写入 submission.json。
顶层格式：{"task_id":"NRB07","answer":{...},"artifacts":{"relative/path":"完整文件内容"}}。
answer 使用本题字段。代码、推导、图和修订稿放入 artifacts，字符串须包含完整内容，不能只返回本机路径。
数值使用 JSON number，缺失使用 null；不接受 NaN/Infinity。不同题目独立完成。
输入均为本基准原创构造的合成材料，不代表真实实验或真实未发表研究。
封闭资料轨道只使用本题材料与通用知识。不得查找本基准源码、答案或评分器。
每题自动核验 70 分，另有以下三项各 10 分的独立质量审阅。

[
  {
    "id": "leakage_reasoning",
    "title": "独立单位与泄漏",
    "anchors": {
      "0": "把重复读数当独立样本，或保留跨划分机器。",
      "5": "识别分组泄漏并正确修复，但未清楚解释泛化对象。",
      "10": "解释同机相关性、预期泛化单位和划分规则；说明如何核对跨文件 ID、每组唯一归属及冻结的数据边界。"
    }
  },
  {
    "id": "selection_metrics",
    "title": "选择协议与指标含义",
    "anchors": {
      "0": "用测试集选择模型、替换指标或夸大结果。",
      "5": "正确执行验证集选择与测试指标，但未解释类别不均衡的影响。",
      "10": "清楚说明验证/测试职责、macro-F1 与 accuracy/均衡准确率差异，保留固定标签和空分母规则；准确报告实际验证范围。"
    }
  },
  {
    "id": "uncertainty_limits",
    "title": "不确定度与可复现报告",
    "anchors": {
      "0": "错误按读数独立 bootstrap，或声称精确保证覆盖率。",
      "5": "使用机器 bootstrap 并说明样本量，但区间解释或复现细节不足。",
      "10": "解释整组抽样、重复组权重、固定模型、bootstrap 标准误与百分位区间，区分读数与独立机器数，并说明小样本与外部推广限制。"
    }
  }
]

Required artifacts: reasoning.md


## 输入文件：DATA_README.md
<BEGIN_INPUT_FILE>

# Generated repeated-machine exercise

records.csv and predictions.csv are synthetic benchmark inputs, not observations
from actual machines or the results of training an actual classifier. Every
machine supplies repeated readings of the same underlying mechanical condition.
The proposed row-level split is deliberately unreliable. Machine identity is
the independent grouping unit. Labels and repeat counts are intentionally
imbalanced. The split rule in protocol.json is fixed before inspecting predictions.

Join predictions to records by row_id, never by line number. File orders differ.
The supplied predictions are frozen candidate predictions; do not train,
threshold-tune, or alter them. Apply the declared validation metric to select
the model once. Test predictions are only for evaluating that selected model.

For uncertainty use the provided exact cluster bootstrap index plan. It removes
random-generator/version differences between implementations. Resampling rows
independently or discarding repeated sampled machine IDs changes the estimand.
The number of readings is not the number of independent machines. A bootstrap
percentile interval in this small synthetic exercise is not a guarantee of
population coverage or performance on a different manufacturing environment.


<END_INPUT_FILE>


## 输入文件：bootstrap_plan.json
<BEGIN_INPUT_FILE>

[["MF72375","MF13D40","MF72375","MAF5FBF","MFA038E","MF13D40","MDA8534","MF13D40","MF13D40"],["MD4EA8D","MFD0C43","MFD0C43","MCB8B78","MF72375","MF72375","MDA8534","MCDE833","MF72375"],["MF72375","MAF5FBF","MD4EA8D","MCB8B78","MCDE833","MFD0C43","MCB8B78","MAF5FBF","MAF5FBF"],["MFA038E","MAF5FBF","MDA8534","MCDE833","MFD0C43","MFA038E","MCDE833","MCDE833","MFA038E"],["MCB8B78","MFA038E","MFD0C43","MCDE833","MAF5FBF","MF72375","MD4EA8D","MF72375","MCDE833"],["MFD0C43","MAF5FBF","MF13D40","MF13D40","MFA038E","MFD0C43","MCB8B78","MFD0C43","MF72375"],["MD4EA8D","MFD0C43","MDA8534","MCDE833","MCB8B78","MCB8B78","MF13D40","MAF5FBF","MDA8534"],["MCDE833","MAF5FBF","MFD0C43","MFA038E","MFA038E","MF72375","MFD0C43","MCB8B78","MAF5FBF"],["MFA038E","MFA038E","MF13D40","MAF5FBF","MAF5FBF","MF72375","MFD0C43","MCDE833","MDA8534"],["MF72375","MFA038E","MF72375","MD4EA8D","MCB8B78","MCB8B78","MFD0C43","MCB8B78","MAF5FBF"],["MCB8B78","MCDE833","MAF5FBF","MCDE833","MCB8B78","MCB8B78","MCDE833","MAF5FBF","MCB8B78"],["MD4EA8D","MCB8B78","MD4EA8D","MFA038E","MFD0C43","MCDE833","MDA8534","MDA8534","MFA038E"],["MD4EA8D","MFA038E","MD4EA8D","MF13D40","MD4EA8D","MAF5FBF","MCDE833","MCB8B78","MF72375"],["MD4EA8D","MF72375","MCB8B78","MAF5FBF","MFA038E","MCDE833","MFA038E","MDA8534","MD4EA8D"],["MAF5FBF","MAF5FBF","MF72375","MAF5FBF","MAF5FBF","MCDE833","MAF5FBF","MCDE833","MF13D40"],["MF72375","MD4EA8D","MF72375","MCB8B78","MCDE833","MDA8534","MFD0C43","MFA038E","MFA038E"],["MD4EA8D","MCB8B78","MD4EA8D","MF13D40","MD4EA8D","MCDE833","MFD0C43","MD4EA8D","MFA038E"],["MDA8534","MCB8B78","MF72375","MCB8B78","MCB8B78","MCB8B78","MFA038E","MCB8B78","MCB8B78"],["MCB8B78","MAF5FBF","MFA038E","MFA038E","MCDE833","MCB8B78","MF13D40","MAF5FBF","MF13D40"],["MFD0C43","MD4EA8D","MFD0C43","MF13D40","MF72375","MDA8534","MCB8B78","MCDE833","MCDE833"],["MCB8B78","MDA8534","MF13D40","MF13D40","MAF5FBF","MF72375","MFA038E","MD4EA8D","MCB8B78"],["MFD0C43","MCDE833","MD4EA8D","MD4EA8D","MCB8B78","MFD0C43","MD4EA8D","MD4EA8D","MDA8534"],["MD4EA8D","MFA038E","MCB8B78","MD4EA8D","MFA038E","MCDE833","MCB8B78","MCDE833","MFA038E"],["MAF5FBF","MDA8534","MDA8534","MFD0C43","MFA038E","MAF5FBF","MF72375","MCDE833","MCB8B78"],["MDA8534","MCB8B78","MFD0C43","MFA038E","MAF5FBF","MDA8534","MFD0C43","MFD0C43","MCB8B78"],["MFA038E","MF13D40","MFD0C43","MDA8534","MFD0C43","MFA038E","MFA038E","MF72375","MFD0C43"],["MD4EA8D","MAF5FBF","MAF5FBF","MF13D40","MFD0C43","MF13D40","MDA8534","MD4EA8D","MCDE833"],["MCDE833","MCB8B78","MAF5FBF","MD4EA8D","MCB8B78","MF72375","MCDE833","MF72375","MCB8B78"],["MD4EA8D","MFA038E","MCB8B78","MFD0C43","MD4EA8D","MAF5FBF","MAF5FBF","MD4EA8D","MD4EA8D"],["MCDE833","MCDE833","MAF5FBF","MDA8534","MF72375","MF72375","MDA8534","MAF5FBF","MCB8B78"],["MCDE833","MF72375","MDA8534","MF72375","MCB8B78","MFD0C43","MCDE833","MFD0C43","MFD0C43"],["MFD0C43","MFA038E","MD4EA8D","MF13D40","MF72375","MAF5FBF","MD4EA8D","MFD0C43","MF72375"],["MD4EA8D","MCB8B78","MAF5FBF","MCB8B78","MCDE833","MFA038E","MFD0C43","MDA8534","MFA038E"],["MCDE833","MF72375","MFD0C43","MFA038E","MAF5FBF","MCDE833","MFA038E","MF72375","MF13D40"],["MCB8B78","MF13D40","MDA8534","MF13D40","MF13D40","MCDE833","MDA8534","MF72375","MFA038E"],["MCB8B78","MF72375","MD4EA8D","MCB8B78","MD4EA8D","MD4EA8D","MDA8534","MAF5FBF","MDA8534"],["MD4EA8D","MCB8B78","MF13D40","MD4EA8D","MF13D40","MAF5FBF","MF13D40","MAF5FBF","MF72375"],["MFA038E","MF72375","MF72375","MFD0C43","MD4EA8D","MCB8B78","MAF5FBF","MFA038E","MCB8B78"],["MF13D40","MD4EA8D","MCB8B78","MDA8534","MF72375","MAF5FBF","MCB8B78","MD4EA8D","MFD0C43"],["MFA038E","MFD0C43","MCB8B78","MFA038E","MCB8B78","MF13D40","MFA038E","MCDE833","MDA8534"],["MFA038E","MF72375","MCDE833","MD4EA8D","MCDE833","MDA8534","MDA8534","MF72375","MF72375"],["MAF5FBF","MCB8B78","MF13D40","MDA8534","MFD0C43","MCDE833","MFD0C43","MFD0C43","MCB8B78"],["MD4EA8D","MF72375","MFD0C43","MF13D40","MF72375","MFA038E","MAF5FBF","MFA038E","MF13D40"],["MCDE833","MFD0C43","MFA038E","MFA038E","MFD0C43","MDA8534","MDA8534","MCB8B78","MFA038E"],["MF13D40","MAF5FBF","MFD0C43","MFD0C43","MD4EA8D","MCB8B78","MDA8534","MAF5FBF","MDA8534"],["MF13D40","MD4EA8D","MFA038E","MFA038E","MFA038E","MFD0C43","MDA8534","MF72375","MF13D40"],["MFA038E","MCDE833","MCDE833","MCB8B78","MF72375","MD4EA8D","MF72375","MCB8B78","MFA038E"],["MFD0C43","MFD0C43","MCDE833","MFA038E","MDA8534","MCDE833","MCDE833","MAF5FBF","MD4EA8D"],["MD4EA8D","MFA038E","MDA8534","MFA038E","MF72375","MCB8B78","MD4EA8D","MFA038E","MAF5FBF"],["MF13D40","MAF5FBF","MF13D40","MFA038E","MFD0C43","MCB8B78","MF13D40","MF72375","MFD0C43"],["MF72375","MDA8534","MDA8534","MFA038E","MCDE833","MCB8B78","MFD0C43","MDA8534","MFD0C43"],["MCDE833","MFD0C43","MD4EA8D","MCB8B78","MCB8B78","MF72375","MDA8534","MFA038E","MF72375"],["MAF5FBF","MDA8534","MDA8534","MCDE833","MF72375","MF13D40","MCDE833","MFD0C43","MFD0C43"],["MFA038E","MCDE833","MFA038E","MFA038E","MCDE833","MD4EA8D","MAF5FBF","MFD0C43","MDA8534"],["MD4EA8D","MAF5FBF","MFD0C43","MF72375","MFD0C43","MAF5FBF","MCDE833","MCB8B78","MF72375"],["MF13D40","MFD0C43","MDA8534","MFA038E","MCB8B78","MFA038E","MCB8B78","MF13D40","MCDE833"],["MFD0C43","MCB8B78","MCB8B78","MCDE833","MF13D40","MDA8534","MAF5FBF","MAF5FBF","MFD0C43"],["MFA038E","MF72375","MDA8534","MAF5FBF","MF13D40","MF72375","MCDE833","MCB8B78","MCB8B78"],["MF13D40","MCDE833","MFA038E","MAF5FBF","MD4EA8D","MCB8B78","MAF5FBF","MCB8B78","MFA038E"],["MD4EA8D","MAF5FBF","MF13D40","MCDE833","MDA8534","MFA038E","MCDE833","MD4EA8D","MCDE833"],["MD4EA8D","MCDE833","MCDE833","MDA8534","MDA8534","MDA8534","MAF5FBF","MDA8534","MDA8534"],["MDA8534","MCDE833","MFD0C43","MF72375","MF72375","MCB8B78","MAF5FBF","MAF5FBF","MF72375"],["MCB8B78","MAF5FBF","MCB8B78","MCB8B78","MDA8534","MD4EA8D","MF13D40","MDA8534","MF72375"],["MCB8B78","MCDE833","MAF5FBF","MDA8534","MDA8534","MCDE833","MFD0C43","MCB8B78","MDA8534"],["MF13D40","MAF5FBF","MAF5FBF","MCB8B78","MF72375","MD4EA8D","MF13D40","MAF5FBF","MFD0C43"],["MDA8534","MF13D40","MFA038E","MF72375","MFA038E","MDA8534","MFA038E","MD4EA8D","MF72375"],["MFA038E","MCB8B78","MDA8534","MFA038E","MCDE833","MD4EA8D","MF72375","MF13D40","MAF5FBF"],["MAF5FBF","MFD0C43","MFA038E","MD4EA8D","MDA8534","MCB8B78","MDA8534","MF13D40","MAF5FBF"],["MCB8B78","MF13D40","MDA8534","MFD0C43","MDA8534","MFA038E","MAF5FBF","MF72375","MD4EA8D"],["MCB8B78","MCB8B78","MF13D40","MF72375","MDA8534","MFD0C43","MAF5FBF","MD4EA8D","MFA038E"],["MCDE833","MF13D40","MCB8B78","MFD0C43","MFA038E","MCB8B78","MD4EA8D","MAF5FBF","MF72375"],["MFD0C43","MAF5FBF","MAF5FBF","MAF5FBF","MF72375","MFD0C43","MFA038E","MFA038E","MF13D40"],["MF13D40","MCB8B78","MF13D40","MF72375","MF72375","MD4EA8D","MDA8534","MF72375","MFD0C43"],["MAF5FBF","MCB8B78","MD4EA8D","MD4EA8D","MF72375","MCDE833","MD4EA8D","MF13D40","MFD0C43"],["MDA8534","MFD0C43","MDA8534","MDA8534","MDA8534","MF13D40","MAF5FBF","MFD0C43","MAF5FBF"],["MFD0C43","MFA038E","MF72375","MAF5FBF","MFD0C43","MFA038E","MFA038E","MF72375","MCB8B78"],["MD4EA8D","MCB8B78","MFD0C43","MFA038E","MF13D40","MD4EA8D","MFA038E","MFD0C43","MAF5FBF"],["MDA8534","MD4EA8D","MF13D40","MFA038E","MF13D40","MF13D40","MF13D40","MFA038E","MFD0C43"],["MCB8B78","MF72375","MF72375","MF13D40","MD4EA8D","MF72375","MD4EA8D","MF72375","MCB8B78"],["MFD0C43","MDA8534","MFA038E","MCDE833","MFD0C43","MCDE833","MF13D40","MD4EA8D","MCB8B78"],["MCB8B78","MAF5FBF","MCB8B78","MF72375","MD4EA8D","MFA038E","MF72375","MF72375","MCB8B78"],["MD4EA8D","MF72375","MD4EA8D","MFD0C43","MAF5FBF","MFA038E","MDA8534","MCDE833","MF13D40"],["MFD0C43","MCB8B78","MDA8534","MCDE833","MAF5FBF","MD4EA8D","MF72375","MCDE833","MAF5FBF"],["MFA038E","MF72375","MCDE833","MCDE833","MCB8B78","MFD0C43","MFA038E","MFD0C43","MDA8534"],["MCDE833","MAF5FBF","MFD0C43","MFD0C43","MFD0C43","MD4EA8D","MD4EA8D","MF13D40","MDA8534"],["MFD0C43","MF13D40","MF13D40","MCB8B78","MFD0C43","MFD0C43","MF72375","MDA8534","MF72375"],["MAF5FBF","MAF5FBF","MD4EA8D","MCB8B78","MF72375","MF13D40","MF72375","MF72375","MCDE833"],["MF13D40","MF13D40","MF13D40","MD4EA8D","MCB8B78","MF13D40","MFA038E","MFD0C43","MFA038E"],["MCDE833","MAF5FBF","MD4EA8D","MD4EA8D","MFD0C43","MDA8534","MCDE833","MFD0C43","MDA8534"],["MF72375","MAF5FBF","MD4EA8D","MFA038E","MCDE833","MFA038E","MAF5FBF","MD4EA8D","MD4EA8D"],["MCDE833","MD4EA8D","MFD0C43","MFD0C43","MAF5FBF","MAF5FBF","MAF5FBF","MFA038E","MCDE833"],["MCDE833","MFD0C43","MF72375","MDA8534","MCB8B78","MFD0C43","MF13D40","MCB8B78","MCB8B78"],["MCB8B78","MFA038E","MDA8534","MF13D40","MD4EA8D","MCDE833","MDA8534","MDA8534","MF72375"],["MCB8B78","MCDE833","MDA8534","MDA8534","MAF5FBF","MAF5FBF","MCDE833","MF13D40","MDA8534"],["MFA038E","MFA038E","MD4EA8D","MAF5FBF","MDA8534","MCB8B78","MF13D40","MAF5FBF","MCDE833"],["MFA038E","MDA8534","MAF5FBF","MCB8B78","MDA8534","MFD0C43","MF13D40","MAF5FBF","MCB8B78"],["MF72375","MD4EA8D","MF13D40","MF72375","MF72375","MF13D40","MDA8534","MFD0C43","MDA8534"],["MFA038E","MAF5FBF","MCB8B78","MCDE833","MCDE833","MCB8B78","MDA8534","MCB8B78","MF72375"],["MFA038E","MCDE833","MFD0C43","MCB8B78","MCDE833","MF13D40","MFA038E","MCDE833","MCDE833"],["MFD0C43","MD4EA8D","MDA8534","MFD0C43","MDA8534","MCB8B78","MCB8B78","MAF5FBF","MFA038E"],["MDA8534","MCB8B78","MFA038E","MF72375","MFD0C43","MF72375","MF13D40","MAF5FBF","MAF5FBF"],["MF72375","MFA038E","MD4EA8D","MFD0C43","MDA8534","MF72375","MF13D40","MF13D40","MFD0C43"],["MDA8534","MDA8534","MF72375","MFA038E","MAF5FBF","MAF5FBF","MF13D40","MFD0C43","MDA8534"],["MD4EA8D","MF13D40","MAF5FBF","MFA038E","MF13D40","MCDE833","MFD0C43","MF72375","MAF5FBF"],["MD4EA8D","MF72375","MFA038E","MFA038E","MCB8B78","MAF5FBF","MFD0C43","MF72375","MF72375"],["MFD0C43","MDA8534","MDA8534","MFD0C43","MD4EA8D","MFA038E","MF13D40","MAF5FBF","MCB8B78"],["MF13D40","MDA8534","MFD0C43","MFA038E","MDA8534","MFA038E","MFD0C43","MDA8534","MF13D40"],["MDA8534","MF13D40","MFD0C43","MFA038E","MAF5FBF","MDA8534","MFA038E","MCDE833","MDA8534"],["MF13D40","MCDE833","MDA8534","MFD0C43","MCB8B78","MF72375","MDA8534","MF13D40","MCDE833"],["MDA8534","MDA8534","MD4EA8D","MCB8B78","MD4EA8D","MDA8534","MCDE833","MAF5FBF","MAF5FBF"],["MF13D40","MAF5FBF","MFD0C43","MCDE833","MF72375","MF72375","MAF5FBF","MFA038E","MF72375"],["MFD0C43","MFA038E","MCDE833","MDA8534","MFA038E","MF72375","MDA8534","MFD0C43","MAF5FBF"],["MFD0C43","MFD0C43","MF72375","MD4EA8D","MD4EA8D","MAF5FBF","MCB8B78","MFA038E","MAF5FBF"],["MF72375","MAF5FBF","MD4EA8D","MF72375","MF72375","MAF5FBF","MCB8B78","MFD0C43","MF72375"],["MF72375","MAF5FBF","MFD0C43","MFD0C43","MF13D40","MCDE833","MDA8534","MD4EA8D","MF13D40"],["MAF5FBF","MDA8534","MD4EA8D","MF13D40","MF13D40","MF72375","MCB8B78","MF13D40","MCDE833"],["MFA038E","MD4EA8D","MCB8B78","MFA038E","MFA038E","MCB8B78","MF72375","MD4EA8D","MFA038E"],["MFD0C43","MFA038E","MF13D40","MF72375","MFD0C43","MCDE833","MDA8534","MAF5FBF","MF13D40"],["MCDE833","MCDE833","MDA8534","MFD0C43","MF13D40","MFD0C43","MCB8B78","MAF5FBF","MF13D40"],["MF72375","MDA8534","MFA038E","MFA038E","MAF5FBF","MCDE833","MFD0C43","MCDE833","MF13D40"],["MAF5FBF","MDA8534","MFD0C43","MCB8B78","MCB8B78","MF13D40","MAF5FBF","MD4EA8D","MDA8534"],["MDA8534","MF72375","MAF5FBF","MF72375","MD4EA8D","MDA8534","MF72375","MCDE833","MCB8B78"],["MCDE833","MAF5FBF","MD4EA8D","MD4EA8D","MD4EA8D","MDA8534","MD4EA8D","MFA038E","MD4EA8D"],["MF72375","MCDE833","MD4EA8D","MCDE833","MFA038E","MCDE833","MF72375","MCDE833","MCDE833"],["MCB8B78","MCB8B78","MD4EA8D","MAF5FBF","MF13D40","MCB8B78","MF13D40","MDA8534","MFA038E"],["MCDE833","MAF5FBF","MAF5FBF","MCDE833","MDA8534","MFA038E","MDA8534","MFA038E","MFD0C43"],["MFA038E","MCB8B78","MF13D40","MD4EA8D","MCDE833","MCDE833","MF72375","MD4EA8D","MAF5FBF"],["MF72375","MF72375","MF13D40","MDA8534","MF13D40","MFA038E","MFA038E","MCDE833","MF72375"],["MFA038E","MF72375","MF13D40","MCDE833","MCB8B78","MF13D40","MF72375","MF72375","MAF5FBF"],["MCB8B78","MFD0C43","MF72375","MD4EA8D","MAF5FBF","MD4EA8D","MAF5FBF","MF13D40","MCB8B78"],["MF72375","MFA038E","MFD0C43","MFA038E","MFA038E","MDA8534","MAF5FBF","MF72375","MDA8534"],["MF72375","MDA8534","MFA038E","MF13D40","MDA8534","MD4EA8D","MCB8B78","MDA8534","MFD0C43"],["MFD0C43","MF72375","MCDE833","MD4EA8D","MAF5FBF","MCDE833","MD4EA8D","MDA8534","MF13D40"],["MF72375","MD4EA8D","MD4EA8D","MF13D40","MCDE833","MF13D40","MF13D40","MAF5FBF","MD4EA8D"],["MCDE833","MD4EA8D","MCB8B78","MF72375","MAF5FBF","MF72375","MF72375","MFA038E","MCDE833"],["MDA8534","MCB8B78","MF72375","MCDE833","MFA038E","MF13D40","MDA8534","MD4EA8D","MF13D40"],["MD4EA8D","MF13D40","MFA038E","MAF5FBF","MAF5FBF","MFA038E","MCB8B78","MF13D40","MFA038E"],["MF13D40","MAF5FBF","MFD0C43","MF13D40","MDA8534","MCDE833","MCDE833","MFA038E","MF72375"],["MCB8B78","MAF5FBF","MCB8B78","MD4EA8D","MCB8B78","MF72375","MF13D40","MDA8534","MCB8B78"],["MF13D40","MCDE833","MFA038E","MF72375","MFD0C43","MAF5FBF","MF13D40","MFA038E","MCDE833"],["MCB8B78","MD4EA8D","MCDE833","MFD0C43","MF72375","MFD0C43","MD4EA8D","MCB8B78","MF72375"],["MAF5FBF","MCB8B78","MDA8534","MAF5FBF","MF13D40","MD4EA8D","MCDE833","MFD0C43","MCDE833"],["MF72375","MFA038E","MCB8B78","MCDE833","MCB8B78","MFA038E","MAF5FBF","MCDE833","MF72375"],["MAF5FBF","MCDE833","MF13D40","MAF5FBF","MF13D40","MFD0C43","MCDE833","MD4EA8D","MFA038E"],["MCDE833","MDA8534","MAF5FBF","MCDE833","MF72375","MDA8534","MCB8B78","MFA038E","MCDE833"],["MF72375","MAF5FBF","MF13D40","MFD0C43","MFD0C43","MAF5FBF","MFD0C43","MD4EA8D","MFA038E"],["MF13D40","MF72375","MDA8534","MFD0C43","MCB8B78","MFA038E","MF13D40","MF13D40","MF72375"],["MDA8534","MFD0C43","MCDE833","MCB8B78","MCDE833","MAF5FBF","MCDE833","MFD0C43","MFD0C43"],["MCB8B78","MF72375","MF13D40","MDA8534","MCB8B78","MF13D40","MCB8B78","MCDE833","MDA8534"],["MFA038E","MF72375","MAF5FBF","MCB8B78","MFA038E","MAF5FBF","MF13D40","MFD0C43","MF13D40"],["MDA8534","MFD0C43","MD4EA8D","MF13D40","MAF5FBF","MCDE833","MF13D40","MDA8534","MFD0C43"],["MCB8B78","MF72375","MFA038E","MCDE833","MCB8B78","MFA038E","MFA038E","MCB8B78","MF13D40"],["MAF5FBF","MDA8534","MDA8534","MFD0C43","MFD0C43","MD4EA8D","MF72375","MFD0C43","MAF5FBF"],["MD4EA8D","MF13D40","MAF5FBF","MF72375","MF13D40","MFA038E","MF72375","MFA038E","MF72375"],["MAF5FBF","MF13D40","MFD0C43","MDA8534","MFD0C43","MCB8B78","MFA038E","MCDE833","MD4EA8D"],["MFD0C43","MF72375","MCB8B78","MFD0C43","MCB8B78","MD4EA8D","MF72375","MCDE833","MF13D40"],["MAF5FBF","MCDE833","MDA8534","MCDE833","MFD0C43","MCB8B78","MF72375","MF13D40","MFA038E"],["MF72375","MFD0C43","MCB8B78","MCB8B78","MCB8B78","MF13D40","MCB8B78","MCB8B78","MAF5FBF"],["MFA038E","MCDE833","MCDE833","MFD0C43","MCDE833","MFA038E","MD4EA8D","MFA038E","MFD0C43"],["MF72375","MCB8B78","MFA038E","MFA038E","MCDE833","MDA8534","MD4EA8D","MCB8B78","MDA8534"],["MDA8534","MAF5FBF","MAF5FBF","MF72375","MCB8B78","MD4EA8D","MCB8B78","MF13D40","MFA038E"],["MFA038E","MF72375","MAF5FBF","MAF5FBF","MDA8534","MFD0C43","MFA038E","MCB8B78","MFD0C43"],["MD4EA8D","MAF5FBF","MCB8B78","MCB8B78","MCB8B78","MCDE833","MAF5FBF","MDA8534","MAF5FBF"],["MFA038E","MDA8534","MCDE833","MD4EA8D","MF72375","MF13D40","MDA8534","MFD0C43","MFD0C43"],["MF72375","MFD0C43","MF72375","MFD0C43","MCB8B78","MFA038E","MDA8534","MFA038E","MCDE833"],["MCDE833","MCDE833","MDA8534","MAF5FBF","MFD0C43","MAF5FBF","MCB8B78","MF13D40","MD4EA8D"],["MCB8B78","MF72375","MD4EA8D","MF13D40","MCB8B78","MAF5FBF","MF13D40","MF13D40","MDA8534"],["MCB8B78","MF72375","MFD0C43","MCB8B78","MAF5FBF","MF72375","MFA038E","MDA8534","MCDE833"],["MF72375","MDA8534","MF13D40","MAF5FBF","MFD0C43","MF13D40","MFA038E","MDA8534","MFA038E"],["MFD0C43","MF13D40","MAF5FBF","MF13D40","MCB8B78","MFD0C43","MFD0C43","MCDE833","MCDE833"],["MFD0C43","MFA038E","MCB8B78","MCDE833","MDA8534","MD4EA8D","MAF5FBF","MCB8B78","MF72375"],["MF72375","MFA038E","MAF5FBF","MFD0C43","MAF5FBF","MF72375","MAF5FBF","MDA8534","MFD0C43"],["MDA8534","MAF5FBF","MDA8534","MCB8B78","MFD0C43","MCB8B78","MCB8B78","MAF5FBF","MF72375"],["MFA038E","MFA038E","MF72375","MFA038E","MFA038E","MFA038E","MFD0C43","MCDE833","MFA038E"],["MAF5FBF","MFD0C43","MDA8534","MCB8B78","MFD0C43","MDA8534","MFA038E","MD4EA8D","MFA038E"],["MF72375","MAF5FBF","MAF5FBF","MCB8B78","MCB8B78","MAF5FBF","MAF5FBF","MCDE833","MF13D40"],["MCDE833","MF13D40","MF72375","MF72375","MDA8534","MCDE833","MCB8B78","MD4EA8D","MFD0C43"],["MCDE833","MCDE833","MFA038E","MD4EA8D","MAF5FBF","MCDE833","MCB8B78","MD4EA8D","MCB8B78"],["MAF5FBF","MF72375","MFA038E","MCB8B78","MDA8534","MCB8B78","MCB8B78","MF13D40","MCDE833"],["MDA8534","MDA8534","MAF5FBF","MF72375","MAF5FBF","MD4EA8D","MAF5FBF","MCB8B78","MCDE833"],["MFD0C43","MCDE833","MD4EA8D","MFD0C43","MCB8B78","MFA038E","MF13D40","MFD0C43","MAF5FBF"],["MD4EA8D","MF13D40","MDA8534","MAF5FBF","MFA038E","MF13D40","MCDE833","MF13D40","MCDE833"],["MDA8534","MDA8534","MAF5FBF","MCB8B78","MDA8534","MFA038E","MD4EA8D","MDA8534","MFD0C43"],["MF13D40","MDA8534","MFA038E","MF13D40","MF72375","MDA8534","MF72375","MAF5FBF","MF13D40"],["MFA038E","MAF5FBF","MFA038E","MFA038E","MFD0C43","MCDE833","MAF5FBF","MD4EA8D","MD4EA8D"],["MD4EA8D","MCDE833","MFA038E","MFA038E","MFA038E","MFA038E","MAF5FBF","MFA038E","MD4EA8D"],["MDA8534","MAF5FBF","MCB8B78","MD4EA8D","MDA8534","MF72375","MD4EA8D","MF72375","MF13D40"],["MFD0C43","MFA038E","MCDE833","MFD0C43","MAF5FBF","MDA8534","MF13D40","MF72375","MFA038E"],["MD4EA8D","MF72375","MAF5FBF","MF72375","MCB8B78","MCDE833","MAF5FBF","MCDE833","MCDE833"],["MCDE833","MCDE833","MF72375","MFA038E","MCB8B78","MF72375","MCB8B78","MFD0C43","MDA8534"],["MFA038E","MDA8534","MD4EA8D","MDA8534","MCB8B78","MFA038E","MDA8534","MF13D40","MAF5FBF"],["MF72375","MD4EA8D","MDA8534","MCDE833","MFD0C43","MF72375","MDA8534","MFA038E","MCDE833"],["MDA8534","MAF5FBF","MCB8B78","MDA8534","MCDE833","MD4EA8D","MD4EA8D","MD4EA8D","MFD0C43"],["MAF5FBF","MCDE833","MDA8534","MDA8534","MAF5FBF","MDA8534","MDA8534","MF13D40","MAF5FBF"],["MF13D40","MDA8534","MAF5FBF","MF72375","MD4EA8D","MFA038E","MF13D40","MD4EA8D","MAF5FBF"],["MCDE833","MF72375","MF13D40","MF13D40","MAF5FBF","MD4EA8D","MF72375","MFD0C43","MF72375"],["MF72375","MDA8534","MD4EA8D","MCDE833","MFA038E","MAF5FBF","MAF5FBF","MDA8534","MCDE833"],["MCDE833","MFA038E","MCB8B78","MAF5FBF","MAF5FBF","MFA038E","MF13D40","MFD0C43","MCDE833"],["MDA8534","MFD0C43","MF13D40","MFA038E","MD4EA8D","MDA8534","MFD0C43","MFA038E","MFD0C43"]]

<END_INPUT_FILE>


## 输入文件：predictions.csv
<BEGIN_INPUT_FILE>

row_id,model_a,model_b
R0153,surface_wear,intact
R0037,intact,intact
R0203,surface_wear,surface_wear
R0221,joint_loose,joint_loose
R0152,surface_wear,surface_wear
R0090,intact,intact
R0033,intact,joint_loose
R0150,surface_wear,intact
R0138,intact,intact
R0110,intact,intact
R0050,intact,surface_wear
R0035,joint_loose,intact
R0159,surface_wear,surface_wear
R0031,intact,intact
R0139,surface_wear,intact
R0111,intact,intact
R0180,surface_wear,surface_wear
R0018,intact,joint_loose
R0185,surface_wear,intact
R0141,intact,intact
R0011,intact,intact
R0093,intact,intact
R0151,surface_wear,intact
R0172,surface_wear,intact
R0095,joint_loose,intact
R0208,joint_loose,surface_wear
R0250,joint_loose,joint_loose
R0246,surface_wear,joint_loose
R0148,surface_wear,surface_wear
R0157,surface_wear,surface_wear
R0047,surface_wear,joint_loose
R0154,surface_wear,surface_wear
R0086,surface_wear,intact
R0160,surface_wear,joint_loose
R0092,intact,intact
R0078,intact,surface_wear
R0120,joint_loose,intact
R0043,intact,intact
R0219,joint_loose,joint_loose
R0117,intact,intact
R0006,intact,joint_loose
R0205,surface_wear,surface_wear
R0104,intact,intact
R0144,intact,intact
R0235,joint_loose,joint_loose
R0237,joint_loose,joint_loose
R0044,joint_loose,intact
R0087,surface_wear,intact
R0169,joint_loose,surface_wear
R0248,joint_loose,joint_loose
R0054,intact,intact
R0178,surface_wear,joint_loose
R0021,intact,intact
R0124,intact,intact
R0147,surface_wear,surface_wear
R0100,intact,intact
R0133,intact,intact
R0253,intact,joint_loose
R0165,joint_loose,intact
R0097,intact,intact
R0089,surface_wear,intact
R0070,intact,intact
R0049,intact,joint_loose
R0123,intact,intact
R0118,intact,intact
R0036,intact,surface_wear
R0024,intact,surface_wear
R0025,intact,intact
R0127,intact,intact
R0134,surface_wear,intact
R0175,surface_wear,surface_wear
R0182,joint_loose,surface_wear
R0242,joint_loose,intact
R0142,intact,intact
R0075,joint_loose,intact
R0158,surface_wear,surface_wear
R0140,joint_loose,intact
R0252,surface_wear,joint_loose
R0045,surface_wear,intact
R0034,intact,intact
R0214,joint_loose,surface_wear
R0096,intact,intact
R0125,surface_wear,intact
R0155,surface_wear,surface_wear
R0194,surface_wear,surface_wear
R0004,surface_wear,intact
R0226,joint_loose,surface_wear
R0228,joint_loose,joint_loose
R0072,intact,intact
R0082,intact,intact
R0005,joint_loose,intact
R0131,surface_wear,intact
R0145,joint_loose,intact
R0105,intact,intact
R0217,joint_loose,surface_wear
R0065,joint_loose,surface_wear
R0243,joint_loose,intact
R0240,intact,intact
R0099,intact,intact
R0200,intact,surface_wear
R0003,joint_loose,joint_loose
R0220,intact,joint_loose
R0173,surface_wear,surface_wear
R0085,intact,intact
R0074,joint_loose,joint_loose
R0196,joint_loose,surface_wear
R0102,intact,intact
R0188,surface_wear,surface_wear
R0230,joint_loose,joint_loose
R0068,surface_wear,intact
R0098,joint_loose,intact
R0007,intact,intact
R0071,intact,intact
R0233,surface_wear,surface_wear
R0167,surface_wear,surface_wear
R0156,surface_wear,intact
R0143,intact,intact
R0027,surface_wear,joint_loose
R0040,intact,intact
R0067,intact,surface_wear
R0026,intact,joint_loose
R0161,surface_wear,surface_wear
R0249,surface_wear,joint_loose
R0231,joint_loose,joint_loose
R0193,surface_wear,surface_wear
R0064,intact,joint_loose
R0229,joint_loose,joint_loose
R0017,intact,intact
R0079,intact,joint_loose
R0179,surface_wear,surface_wear
R0223,joint_loose,joint_loose
R0042,intact,intact
R0206,joint_loose,surface_wear
R0212,surface_wear,surface_wear
R0146,joint_loose,intact
R0061,surface_wear,intact
R0126,surface_wear,joint_loose
R0121,surface_wear,intact
R0041,intact,surface_wear
R0052,intact,intact
R0063,joint_loose,intact
R0066,intact,surface_wear
R0195,surface_wear,surface_wear
R0057,intact,intact
R0083,intact,joint_loose
R0234,joint_loose,joint_loose
R0198,joint_loose,surface_wear
R0201,intact,surface_wear
R0189,surface_wear,surface_wear
R0244,joint_loose,surface_wear
R0218,surface_wear,surface_wear
R0216,joint_loose,joint_loose
R0204,intact,surface_wear
R0192,surface_wear,surface_wear
R0094,surface_wear,intact
R0177,surface_wear,joint_loose
R0129,joint_loose,intact
R0002,intact,surface_wear
R0122,joint_loose,intact
R0176,surface_wear,surface_wear
R0081,joint_loose,intact
R0053,joint_loose,intact
R0168,surface_wear,surface_wear
R0119,surface_wear,intact
R0023,intact,joint_loose
R0014,intact,intact
R0135,surface_wear,intact
R0010,intact,intact
R0091,joint_loose,intact
R0032,surface_wear,surface_wear
R0181,surface_wear,surface_wear
R0247,intact,surface_wear
R0211,surface_wear,surface_wear
R0164,surface_wear,joint_loose
R0174,intact,surface_wear
R0113,intact,intact
R0020,intact,intact
R0232,surface_wear,surface_wear
R0166,intact,surface_wear
R0170,surface_wear,joint_loose
R0069,intact,intact
R0016,intact,intact
R0191,joint_loose,surface_wear
R0130,intact,surface_wear
R0171,intact,surface_wear
R0013,intact,intact
R0128,surface_wear,intact
R0012,joint_loose,intact
R0236,joint_loose,intact
R0101,surface_wear,intact
R0215,intact,joint_loose
R0187,surface_wear,surface_wear
R0039,joint_loose,intact
R0001,intact,intact
R0163,surface_wear,surface_wear
R0222,joint_loose,surface_wear
R0009,surface_wear,intact
R0149,intact,joint_loose
R0059,intact,intact
R0114,intact,intact
R0058,intact,joint_loose
R0080,intact,intact
R0199,intact,surface_wear
R0076,joint_loose,intact
R0088,intact,intact
R0029,intact,intact
R0207,joint_loose,surface_wear
R0162,surface_wear,surface_wear
R0008,intact,surface_wear
R0028,intact,intact
R0210,surface_wear,intact
R0108,intact,intact
R0048,intact,intact
R0038,intact,intact
R0183,surface_wear,joint_loose
R0019,intact,intact
R0239,surface_wear,surface_wear
R0062,intact,intact
R0103,surface_wear,intact
R0030,intact,intact
R0213,intact,surface_wear
R0055,surface_wear,intact
R0251,intact,joint_loose
R0060,intact,intact
R0106,surface_wear,intact
R0015,intact,surface_wear
R0084,intact,intact
R0254,surface_wear,joint_loose
R0202,intact,surface_wear
R0137,joint_loose,joint_loose
R0225,intact,joint_loose
R0022,intact,intact
R0136,surface_wear,intact
R0197,joint_loose,surface_wear
R0056,intact,surface_wear
R0107,joint_loose,intact
R0238,joint_loose,surface_wear
R0186,surface_wear,surface_wear
R0245,joint_loose,surface_wear
R0077,surface_wear,intact
R0190,surface_wear,joint_loose
R0227,joint_loose,joint_loose
R0115,joint_loose,intact
R0051,intact,surface_wear
R0132,intact,surface_wear
R0224,joint_loose,joint_loose
R0046,intact,intact
R0241,joint_loose,surface_wear
R0116,intact,intact
R0112,intact,joint_loose
R0184,surface_wear,surface_wear
R0109,intact,intact
R0209,joint_loose,joint_loose
R0073,surface_wear,intact


<END_INPUT_FILE>


## 输入文件：protocol.json
<BEGIN_INPUT_FILE>

{
  "label_order": [
    "intact",
    "surface_wear",
    "joint_loose"
  ],
  "split_rule": "Within each true class, sort all distinct machine_id strings lexicographically. The first 7 machines are train, the next 2 validation, the last 3 test. Apply one split to every reading of a machine.",
  "selection": "Choose the model with greatest row-level macro-F1 on the repaired validation split. Exact ties use lexicographically smaller model name. Freeze it before test evaluation.",
  "metric_definition": "Confusion matrix rows=true labels, columns=predicted labels, in label_order. Precision/recall/F1 with a zero denominator are zero. Macro-F1 and balanced accuracy average over all three fixed labels, including labels absent from a resample.",
  "bootstrap_definition": "Each bootstrap_plan.json row samples all nine test-machine clusters with replacement. Include ALL readings every time a machine is selected; preserve duplicate selections. Keep the selected classifier fixed. Report sample SD (ddof=1) of replicate macro-F1 as bootstrap standard error. Percentile endpoints use linear interpolation: h=(B-1)*p, between floor(h) and ceil(h).",
  "synthetic": true
}

<END_INPUT_FILE>


## 输入文件：records.csv
<BEGIN_INPUT_FILE>

row_id,machine_id,repeat_index,label,proposed_split
R0050,M4F995D,7,intact,train
R0253,MFA038E,2,joint_loose,train
R0173,M86EE70,7,surface_wear,train
R0019,M4BFBBE,8,intact,train
R0208,MD4EA8D,2,surface_wear,validation
R0243,ME70DDA,2,joint_loose,test
R0134,MDA8534,10,intact,train
R0197,MCB8B78,3,surface_wear,test
R0191,MC90E54,2,surface_wear,validation
R0018,M4BFBBE,7,intact,test
R0195,MCB8B78,1,surface_wear,train
R0082,M8A3655,11,intact,test
R0140,MFD0C43,6,intact,train
R0015,M4BFBBE,4,intact,train
R0234,M8B4EB9,4,joint_loose,train
R0146,MFD0C43,12,intact,validation
R0056,M4F995D,13,intact,train
R0103,MAA515F,4,intact,validation
R0101,MAA515F,2,intact,train
R0026,M4CB21E,3,intact,train
R0157,M4C63C9,2,surface_wear,test
R0211,MD4EA8D,5,surface_wear,test
R0172,M86EE70,6,surface_wear,train
R0007,M22C1BE,7,intact,train
R0212,MD4EA8D,6,surface_wear,train
R0005,M22C1BE,5,intact,train
R0177,M9F5B1B,4,surface_wear,test
R0187,MC78CD7,5,surface_wear,test
R0021,M4BFBBE,10,intact,train
R0138,MFD0C43,4,intact,test
R0112,MAF5FBF,2,intact,train
R0062,M5A67B9,6,intact,train
R0204,MCDE833,4,surface_wear,test
R0169,M86EE70,3,surface_wear,validation
R0155,M3FC92F,4,surface_wear,test
R0179,MA49AA0,2,surface_wear,validation
R0044,M4F995D,1,intact,train
R0070,M5A67B9,14,intact,train
R0160,M618A8F,1,surface_wear,validation
R0037,M4D2491,4,intact,test
R0165,M618A8F,6,surface_wear,test
R0142,MFD0C43,8,intact,train
R0110,MAA515F,11,intact,train
R0166,M618A8F,7,surface_wear,validation
R0174,M9F5B1B,1,surface_wear,train
R0239,MD9B562,1,joint_loose,validation
R0104,MAA515F,5,intact,test
R0247,MF13D40,2,joint_loose,train
R0027,M4CB21E,4,intact,validation
R0176,M9F5B1B,3,surface_wear,train
R0230,M72C962,2,joint_loose,train
R0188,MC78CD7,6,surface_wear,test
R0083,M8A3655,12,intact,validation
R0127,MDA8534,3,intact,test
R0131,MDA8534,7,intact,test
R0077,M8A3655,6,intact,train
R0080,M8A3655,9,intact,train
R0144,MFD0C43,10,intact,train
R0076,M8A3655,5,intact,test
R0175,M9F5B1B,2,surface_wear,validation
R0011,M22C1BE,11,intact,train
R0073,M8A3655,2,intact,train
R0198,MCB8B78,4,surface_wear,train
R0122,MAF5FBF,12,intact,validation
R0108,MAA515F,9,intact,test
R0123,MAF5FBF,13,intact,train
R0084,MAA36DB,1,intact,validation
R0182,MA49AA0,5,surface_wear,validation
R0133,MDA8534,9,intact,train
R0113,MAF5FBF,3,intact,train
R0161,M618A8F,2,surface_wear,train
R0094,MAA36DB,11,intact,train
R0061,M5A67B9,5,intact,train
R0202,MCDE833,2,surface_wear,validation
R0093,MAA36DB,10,intact,validation
R0072,M8A3655,1,intact,test
R0250,MF72375,3,joint_loose,train
R0150,M17823B,4,surface_wear,test
R0057,M5A67B9,1,intact,train
R0100,MAA515F,1,intact,train
R0135,MFD0C43,1,intact,validation
R0075,M8A3655,4,intact,validation
R0109,MAA515F,10,intact,train
R0048,M4F995D,5,intact,train
R0235,MD71618,1,joint_loose,validation
R0097,MAA36DB,14,intact,train
R0154,M3FC92F,3,surface_wear,test
R0038,M4D2491,5,intact,validation
R0216,M0947E7,3,joint_loose,train
R0065,M5A67B9,9,intact,train
R0248,MF72375,1,joint_loose,validation
R0129,MDA8534,5,intact,test
R0095,MAA36DB,12,intact,train
R0203,MCDE833,3,surface_wear,validation
R0147,M17823B,1,surface_wear,train
R0114,MAF5FBF,4,intact,train
R0125,MDA8534,1,intact,train
R0049,M4F995D,6,intact,test
R0199,MCB8B78,5,surface_wear,validation
R0159,M4C63C9,4,surface_wear,validation
R0060,M5A67B9,4,intact,test
R0228,M707E4D,3,joint_loose,test
R0251,MF72375,4,joint_loose,validation
R0171,M86EE70,5,surface_wear,test
R0210,MD4EA8D,4,surface_wear,validation
R0040,M4D2491,7,intact,train
R0090,MAA36DB,7,intact,validation
R0014,M4BFBBE,3,intact,validation
R0220,M3C3F99,3,joint_loose,validation
R0213,MD4EA8D,7,surface_wear,train
R0063,M5A67B9,7,intact,test
R0168,M86EE70,2,surface_wear,test
R0231,M8B4EB9,1,joint_loose,test
R0163,M618A8F,4,surface_wear,validation
R0008,M22C1BE,8,intact,train
R0132,MDA8534,8,intact,train
R0209,MD4EA8D,3,surface_wear,train
R0226,M707E4D,1,joint_loose,train
R0170,M86EE70,4,surface_wear,validation
R0193,MC90E54,4,surface_wear,train
R0164,M618A8F,5,surface_wear,test
R0096,MAA36DB,13,intact,train
R0107,MAA515F,8,intact,train
R0222,M6BEF38,1,joint_loose,train
R0009,M22C1BE,9,intact,test
R0029,M4CB21E,6,intact,train
R0091,MAA36DB,8,intact,test
R0087,MAA36DB,4,intact,validation
R0149,M17823B,3,surface_wear,train
R0035,M4D2491,2,intact,test
R0016,M4BFBBE,5,intact,test
R0098,MAA36DB,15,intact,train
R0192,MC90E54,3,surface_wear,test
R0236,MD71618,2,joint_loose,validation
R0036,M4D2491,3,intact,train
R0130,MDA8534,6,intact,validation
R0183,MC78CD7,1,surface_wear,train
R0252,MFA038E,1,joint_loose,train
R0054,M4F995D,11,intact,validation
R0117,MAF5FBF,7,intact,test
R0137,MFD0C43,3,intact,test
R0152,M3FC92F,1,surface_wear,train
R0214,M0947E7,1,joint_loose,test
R0079,M8A3655,8,intact,train
R0013,M4BFBBE,2,intact,train
R0058,M5A67B9,2,intact,train
R0180,MA49AA0,3,surface_wear,test
R0001,M22C1BE,1,intact,train
R0030,M4CB21E,7,intact,test
R0088,MAA36DB,5,intact,train
R0206,MCDE833,6,surface_wear,test
R0068,M5A67B9,12,intact,validation
R0017,M4BFBBE,6,intact,train
R0020,M4BFBBE,9,intact,validation
R0240,MD9B562,2,joint_loose,train
R0074,M8A3655,3,intact,train
R0190,MC90E54,1,surface_wear,train
R0059,M5A67B9,3,intact,train
R0194,MC90E54,5,surface_wear,train
R0010,M22C1BE,10,intact,validation
R0071,M5A67B9,15,intact,train
R0224,M6BEF38,3,joint_loose,train
R0106,MAA515F,7,intact,train
R0151,M17823B,5,surface_wear,test
R0121,MAF5FBF,11,intact,train
R0003,M22C1BE,3,intact,train
R0227,M707E4D,2,joint_loose,train
R0053,M4F995D,10,intact,test
R0046,M4F995D,3,intact,test
R0181,MA49AA0,4,surface_wear,validation
R0042,M4D2491,9,intact,train
R0237,MD71618,3,joint_loose,test
R0229,M72C962,1,joint_loose,train
R0102,MAA515F,3,intact,validation
R0052,M4F995D,9,intact,train
R0254,MFA038E,3,joint_loose,train
R0086,MAA36DB,3,intact,train
R0136,MFD0C43,2,intact,validation
R0039,M4D2491,6,intact,train
R0069,M5A67B9,13,intact,test
R0120,MAF5FBF,10,intact,train
R0153,M3FC92F,2,surface_wear,train
R0099,MAA36DB,16,intact,validation
R0089,MAA36DB,6,intact,train
R0223,M6BEF38,2,joint_loose,validation
R0067,M5A67B9,11,intact,test
R0006,M22C1BE,6,intact,train
R0051,M4F995D,8,intact,train
R0022,M4BFBBE,11,intact,validation
R0024,M4CB21E,1,intact,test
R0232,M8B4EB9,2,joint_loose,train
R0032,M4CB21E,9,intact,test
R0196,MCB8B78,2,surface_wear,train
R0156,M4C63C9,1,surface_wear,validation
R0145,MFD0C43,11,intact,train
R0041,M4D2491,8,intact,test
R0225,M6BEF38,4,joint_loose,validation
R0215,M0947E7,2,joint_loose,train
R0126,MDA8534,2,intact,train
R0055,M4F995D,12,intact,validation
R0124,MAF5FBF,14,intact,train
R0246,MF13D40,1,joint_loose,train
R0249,MF72375,2,joint_loose,train
R0064,M5A67B9,8,intact,train
R0118,MAF5FBF,8,intact,validation
R0245,ME70DDA,4,joint_loose,validation
R0012,M4BFBBE,1,intact,validation
R0221,M3C3F99,4,joint_loose,train
R0148,M17823B,2,surface_wear,train
R0031,M4CB21E,8,intact,train
R0085,MAA36DB,2,intact,validation
R0128,MDA8534,4,intact,test
R0078,M8A3655,7,intact,test
R0045,M4F995D,2,intact,validation
R0207,MD4EA8D,1,surface_wear,test
R0034,M4D2491,1,intact,train
R0178,MA49AA0,1,surface_wear,train
R0205,MCDE833,5,surface_wear,test
R0081,M8A3655,10,intact,test
R0023,M4BFBBE,12,intact,train
R0233,M8B4EB9,3,joint_loose,train
R0217,M0947E7,4,joint_loose,validation
R0111,MAF5FBF,1,intact,train
R0241,MD9B562,3,joint_loose,test
R0025,M4CB21E,2,intact,validation
R0185,MC78CD7,3,surface_wear,validation
R0141,MFD0C43,7,intact,train
R0200,MCB8B78,6,surface_wear,test
R0244,ME70DDA,3,joint_loose,train
R0184,MC78CD7,2,surface_wear,train
R0201,MCDE833,1,surface_wear,validation
R0047,M4F995D,4,intact,validation
R0092,MAA36DB,9,intact,train
R0167,M86EE70,1,surface_wear,test
R0238,MD71618,4,joint_loose,train
R0143,MFD0C43,9,intact,train
R0119,MAF5FBF,9,intact,train
R0242,ME70DDA,1,joint_loose,train
R0028,M4CB21E,5,intact,validation
R0162,M618A8F,3,surface_wear,test
R0186,MC78CD7,4,surface_wear,train
R0218,M3C3F99,1,joint_loose,test
R0115,MAF5FBF,5,intact,train
R0189,MC78CD7,7,surface_wear,test
R0105,MAA515F,6,intact,train
R0033,M4CB21E,10,intact,train
R0066,M5A67B9,10,intact,test
R0004,M22C1BE,4,intact,train
R0116,MAF5FBF,6,intact,train
R0043,M4D2491,10,intact,train
R0219,M3C3F99,2,joint_loose,validation
R0002,M22C1BE,2,intact,validation
R0158,M4C63C9,3,surface_wear,test
R0139,MFD0C43,5,intact,test


<END_INPUT_FILE>

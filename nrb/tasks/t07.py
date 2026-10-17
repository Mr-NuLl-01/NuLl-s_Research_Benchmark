"""NRB07: generated machine-group leakage, metrics and cluster bootstrap."""

from __future__ import annotations

import copy
import csv
import io
import json
import math
import random

from nrb.checks import check, numbers_close


LABELS = ["intact", "surface_wear", "joint_loose"]
MODELS = ["model_a", "model_b"]


def _csv(rows, fields):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def _confusion(records, predictions, model):
    matrix = [[0]*len(LABELS) for _ in LABELS]
    index = {label: i for i, label in enumerate(LABELS)}
    for row in records:
        matrix[index[row["label"]]][index[predictions[row["row_id"]][model]]] += 1
    return matrix


def _metrics(matrix):
    n = len(matrix)
    classes = {}
    total = sum(sum(row) for row in matrix)
    for i, label in enumerate(LABELS):
        actual = sum(matrix[i])
        predicted = sum(matrix[j][i] for j in range(n))
        true_positive = matrix[i][i]
        precision = true_positive/predicted if predicted else 0.0
        recall = true_positive/actual if actual else 0.0
        denominator = actual+predicted
        f1 = 2*true_positive/denominator if denominator else 0.0
        classes[label] = {"precision": precision, "recall": recall, "f1": f1}
    return {"per_class": classes,
            "accuracy": sum(matrix[i][i] for i in range(n))/total if total else 0.0,
            "macro_f1": sum(row["f1"] for row in classes.values())/n,
            "balanced_accuracy": sum(row["recall"] for row in classes.values())/n}


def _quantile(values, probability):
    ordered = sorted(values)
    position = (len(ordered)-1)*probability
    lower = math.floor(position)
    upper = math.ceil(position)
    return ordered[lower]+(position-lower)*(ordered[upper]-ordered[lower])


def _calculate(records, predictions, split, plan):
    proposed = {}
    for row in records:
        proposed.setdefault(row["machine_id"], set()).add(row["proposed_split"])
    leaked = sorted(machine for machine, parts in proposed.items() if len(parts) > 1)
    validation = [row for row in records if split[row["machine_id"]] == "validation"]
    test = [row for row in records if split[row["machine_id"]] == "test"]
    val_scores = {model: _metrics(_confusion(validation, predictions, model))["macro_f1"] for model in MODELS}
    selected = min(MODELS, key=lambda model: (-val_scores[model], model))
    confusion = _confusion(test, predictions, selected)
    metrics = _metrics(confusion)
    machines = sorted({row["machine_id"] for row in test})
    cluster_matrices = {machine: _confusion([row for row in test if row["machine_id"] == machine], predictions, selected) for machine in machines}
    bootstrap = []
    for resample in plan:
        matrix = [[sum(cluster_matrices[machine][i][j] for machine in resample) for j in range(len(LABELS))] for i in range(len(LABELS))]
        bootstrap.append(_metrics(matrix)["macro_f1"])
    mean = math.fsum(bootstrap)/len(bootstrap)
    se = math.sqrt(math.fsum((value-mean)**2 for value in bootstrap)/(len(bootstrap)-1))
    return {"leaked_machine_ids": leaked, "repaired_group_split": copy.deepcopy(split),
            "validation_macro_f1": val_scores, "selected_model": selected,
            "test_confusion_matrix": confusion, "test_per_class": metrics["per_class"],
            "test_metrics": {key: metrics[key] for key in ("accuracy", "macro_f1", "balanced_accuracy")},
            "test_sample_size": {"readings": len(test), "independent_machines": len(machines)},
            "bootstrap": {"replicates": len(plan), "macro_f1_mean": mean,
                          "macro_f1_standard_error": se,
                          "percentile95": [_quantile(bootstrap, 0.025), _quantile(bootstrap, 0.975)]}}


def build(seed=0):
    rng = random.Random(f"NRB07:{seed}")
    used = set()
    by_label = {}
    for label in LABELS:
        groups = []
        while len(groups) < 12:
            machine = "M"+f"{rng.randrange(16**6):06X}"
            if machine not in used:
                used.add(machine)
                groups.append(machine)
        by_label[label] = sorted(groups)
    split = {}
    for label in LABELS:
        for i, machine in enumerate(by_label[label]):
            split[machine] = "train" if i < 7 else "validation" if i < 9 else "test"
    records = []
    for class_index, label in enumerate(LABELS):
        for machine in by_label[label]:
            low, high = ((10, 16), (4, 7), (2, 4))[class_index]
            size = rng.randint(low, high)
            choices = rng.choices(["train", "validation", "test"], weights=[0.6, 0.2, 0.2], k=size)
            for repeat in range(size):
                records.append({"row_id": f"R{len(records)+1:04d}", "machine_id": machine,
                                "repeat_index": repeat+1, "label": label, "proposed_split": choices[repeat]})
    rng.shuffle(records)
    validation = [row for row in records if split[row["machine_id"]] == "validation"]
    test = [row for row in records if split[row["machine_id"]] == "test"]
    macro_favored = MODELS[rng.randrange(2)]
    other = MODELS[1-MODELS.index(macro_favored)]
    group_effect = {model: {machine: rng.uniform(-0.13, 0.10) for machine in sorted(used)} for model in MODELS}
    predictions = {}
    # Rejection sampling chooses exercise instances with distinct, meaningful
    # decisions: macro-F1 and accuracy disagree on validation, and the test set
    # would tempt improper model reselection. It is not a real model experiment.
    for attempt in range(5000):
        predictions = {}
        for row in records:
            item = {}
            class_index = LABELS.index(row["label"])
            part = split[row["machine_id"]]
            for model in MODELS:
                if part == "validation":
                    probability = (0.64, 0.82, 0.80)[class_index] if model == macro_favored else (0.985, 0.52, 0.10)[class_index]
                elif part == "test":
                    probability = 0.52 if model == macro_favored else 0.83
                else:
                    probability = 0.72
                probability = min(0.995, max(0.015, probability+group_effect[model][row["machine_id"]]))
                item[model] = row["label"] if rng.random() < probability else rng.choice([label for label in LABELS if label != row["label"]])
            predictions[row["row_id"]] = item
        val = {model: _metrics(_confusion(validation, predictions, model)) for model in MODELS}
        holdout = {model: _metrics(_confusion(test, predictions, model)) for model in MODELS}
        if (val[macro_favored]["macro_f1"] > val[other]["macro_f1"]+0.03
                and val[macro_favored]["accuracy"] < val[other]["accuracy"]-0.02
                and holdout[macro_favored]["macro_f1"] < holdout[other]["macro_f1"]-0.06):
            break
    else:
        raise RuntimeError("Could not generate a discriminative grouped instance")
    test_machines = sorted(machine for machine, part in split.items() if part == "test")
    plan = [[rng.choice(test_machines) for _ in test_machines] for _ in range(199)]
    protocol = {"label_order": LABELS,
                "split_rule": "Within each true class, sort all distinct machine_id strings lexicographically. The first 7 machines are train, the next 2 validation, the last 3 test. Apply one split to every reading of a machine.",
                "selection": "Choose the model with greatest row-level macro-F1 on the repaired validation split. Exact ties use lexicographically smaller model name. Freeze it before test evaluation.",
                "metric_definition": "Confusion matrix rows=true labels, columns=predicted labels, in label_order. Precision/recall/F1 with a zero denominator are zero. Macro-F1 and balanced accuracy average over all three fixed labels, including labels absent from a resample.",
                "bootstrap_definition": "Each bootstrap_plan.json row samples all nine test-machine clusters with replacement. Include ALL readings every time a machine is selected; preserve duplicate selections. Keep the selected classifier fixed. Report sample SD (ddof=1) of replicate macro-F1 as bootstrap standard error. Percentile endpoints use linear interpolation: h=(B-1)*p, between floor(h) and ceil(h).",
                "synthetic": True}
    note = """# Generated repeated-machine exercise

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
"""
    prediction_rows = [{"row_id": row_id, **values} for row_id, values in predictions.items()]
    rng.shuffle(prediction_rows)
    prompt = """审阅一份通用机械状态分类评测。每台机器有重复读数，原始按读数划分的数据集可能泄漏。
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
上述字符串模板必须替换为真实值。人工评分关注评测解释，不按关键词数量计分。"""
    return {"id": "NRB07", "seed": seed, "title": "重复测量下的数据泄漏与分组评测", "domain": "grouped-evaluation",
            "prompt": prompt,
            "files": {"records.csv": _csv(records, ["row_id", "machine_id", "repeat_index", "label", "proposed_split"]),
                      "predictions.csv": _csv(prediction_rows, ["row_id", "model_a", "model_b"]),
                      "protocol.json": json.dumps(protocol, indent=2),
                      "bootstrap_plan.json": json.dumps(plan, separators=(",", ":")),
                      "DATA_README.md": note},
            "expected": {"answer": _calculate(records, predictions, split, plan),
                         "records": records, "predictions": predictions, "split": split, "plan": plan,
                         "generation_attempts": attempt+1},
            "rubric": [
                {"id": "leakage_reasoning", "title": "独立单位与泄漏", "anchors": {"0": "把重复读数当独立样本，或保留跨划分机器。", "5": "识别分组泄漏并正确修复，但未清楚解释泛化对象。", "10": "解释同机相关性、预期泛化单位和划分规则；说明如何核对跨文件 ID、每组唯一归属及冻结的数据边界。"}},
                {"id": "selection_metrics", "title": "选择协议与指标含义", "anchors": {"0": "用测试集选择模型、替换指标或夸大结果。", "5": "正确执行验证集选择与测试指标，但未解释类别不均衡的影响。", "10": "清楚说明验证/测试职责、macro-F1 与 accuracy/均衡准确率差异，保留固定标签和空分母规则；准确报告实际验证范围。"}},
                {"id": "uncertainty_limits", "title": "不确定度与可复现报告", "anchors": {"0": "错误按读数独立 bootstrap，或声称精确保证覆盖率。", "5": "使用机器 bootstrap 并说明样本量，但区间解释或复现细节不足。", "10": "解释整组抽样、重复组权重、固定模型、bootstrap 标准误与百分位区间，区分读数与独立机器数，并说明小样本与外部推广限制。"}}]}


def reference(case):
    return {"task_id": "NRB07", "answer": copy.deepcopy(case["expected"]["answer"]),
            "artifacts": {"reasoning.md": "以 machine_id 定义独立单位；跨划分重复读数造成组泄漏。先应用类内机器排序的冻结划分，用 row_id 连接乱序文件。按验证 macro-F1 一次性选择模型，测试只评估所选模型。bootstrap 逐次重采样整台机器并保留重复抽中次数；固定三类与模型，计算指定线性插值百分位和 ddof=1 标准误。合成小样本不能支持真实机器总体性能或严格覆盖率主张。"}}


def grade(case, submission, execution="none"):
    answer = submission.get("answer", {}) if isinstance(submission, dict) else {}
    answer = answer if isinstance(answer, dict) else {}
    expected = case["expected"]["answer"]
    split = answer.get("repaired_group_split")
    wanted_split = expected["repaired_group_split"]
    valid_keys = isinstance(split, dict) and set(split) == set(wanted_split)
    return [
        check("group_leakage_inventory", 10, numbers_close(answer.get("leaked_machine_ids"), expected["leaked_machine_ids"]), "按原始 proposed_split 精确列出跨划分机器。", critical=True),
        check("split_machine_coverage", 5, valid_keys, "每台机器恰有一个输出归属，无缺失或多余机器。"),
        check("frozen_group_partition", 5, numbers_close(split, wanted_split), "按预先给定类内排序划分，所有重复读数共享组归属。", critical=True),
        check("validation_only_selection", 5, numbers_close(answer.get("selected_model"), expected["selected_model"]), "选择按验证 macro-F1；构造中 accuracy 与测试重选会给出不同决策。", critical=True),
        check("validation_macro_f1", 5, numbers_close(answer.get("validation_macro_f1"), expected["validation_macro_f1"], rtol=2e-6, atol=1e-10), "两个候选的验证集宏平均 F1。"),
        check("test_confusion_orientation", 10, numbers_close(answer.get("test_confusion_matrix"), expected["test_confusion_matrix"], rtol=0, atol=0), "所选模型的测试混淆矩阵，真实标签为行。"),
        check("test_class_metrics", 10, numbers_close(answer.get("test_per_class"), expected["test_per_class"], rtol=2e-6, atol=1e-10), "逐类 precision、recall 和 F1，固定三类。"),
        check("test_aggregates", 5, numbers_close(answer.get("test_metrics"), expected["test_metrics"], rtol=2e-6, atol=1e-10), "区分总准确率、宏 F1 与均衡准确率。"),
        check("cluster_bootstrap", 10, numbers_close(answer.get("bootstrap"), expected["bootstrap"], rtol=3e-6, atol=1e-10), "整组重采样、重复次数、ddof=1 和明确分位数定义。"),
        check("independent_sample_size", 5, numbers_close(answer.get("test_sample_size"), expected["test_sample_size"], rtol=0, atol=0), "分别报告测试读数数目和独立机器数。")]

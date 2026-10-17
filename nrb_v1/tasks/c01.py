"""V1.0 public synthetic coding task; hidden expectations stay host-side."""
from __future__ import annotations
import copy
import json

TASK = {'id': 'C01', 'title': '仪器 CSV 清洗、单位与测量不确定度', 'language': 'python', 'difficulty': 1, 'capabilities': ['csv', 'units', 'uncertainty', 'data-validation'], 'time_budget_s': 900, 'required_artifacts': ['solution.py', 'report.md', 'tests.py'], 'essential': [{'id': 'api', 'requirement': 'solution.py 提供 solve(problem)，返回约定的 JSON 可序列化值，错误输入抛 ValueError。'}, {'id': 'science', 'requirement': 'report.md 解释科学定义、算法、单位、验证依据及适用范围。'}, {'id': 'tests', 'requirement': 'tests.py 包含可运行且有断言的独立测试，至少覆盖一个非平凡性质和一个边界。'}]}

SOURCE = 'import csv\nimport io\nimport math\n\ndef solve(problem):\n    if not isinstance(problem, dict) or not isinstance(problem.get("csv"), str):\n        raise ValueError("csv must be text")\n    missing = {"", "NA", "N/A", "null"}\n    records = {}\n    skipped = 0\n    try:\n        reader = csv.DictReader(io.StringIO(problem["csv"].lstrip("\\ufeff")), strict=True)\n        if reader.fieldnames is None or [x.strip() for x in reader.fieldnames] != ["sample", "replicate", "value", "unit", "sigma", "status"]:\n            raise ValueError("header")\n        for raw in reader:\n            if None in raw or any(v is None for v in raw.values()):\n                raise ValueError("row width")\n            row = {k.strip(): v.strip() for k, v in raw.items()}\n            if row["status"] not in {"ok", "reject"}:\n                raise ValueError("status")\n            if not row["sample"] or not row["replicate"]:\n                raise ValueError("identity")\n            if row["status"] == "reject" or row["value"] in missing or row["sigma"] in missing:\n                skipped += 1\n                continue\n            if row["unit"] not in {"K", "C", "mK"}:\n                raise ValueError("unit")\n            value, sigma = float(row["value"]), float(row["sigma"])\n            if not math.isfinite(value) or not math.isfinite(sigma) or sigma <= 0:\n                raise ValueError("number")\n            factor = 0.001 if row["unit"] == "mK" else 1.0\n            temperature = value * factor + (273.15 if row["unit"] == "C" else 0.0)\n            uncertainty = sigma * factor\n            if not 0 <= temperature <= 1e6 or not 1e-100 <= uncertainty <= 1e6:\n                raise ValueError("below absolute zero")\n            # Last usable row wins; skipped rows never erase an earlier usable value.\n            records[(row["sample"], row["replicate"])] = (temperature, uncertainty)\n    except (csv.Error, TypeError, OverflowError) as exc:\n        raise ValueError("invalid CSV") from exc\n    groups = {}\n    for (sample, replicate), pair in records.items():\n        groups.setdefault(sample, []).append((replicate, pair))\n    output = []\n    for sample in sorted(groups):\n        pairs = [pair for _, pair in sorted(groups[sample])]\n        # Scale inverse variances so small valid uncertainties do not overflow.\n        scale = min(sigma for _, sigma in pairs)\n        weights = [(scale / sigma) ** 2 for _, sigma in pairs]\n        total = math.fsum(weights)\n        mean = math.fsum(w * v for w, (v, _) in zip(weights, pairs)) / total\n        se = scale / math.sqrt(total)\n        chi2 = math.fsum(((v - mean) / sigma) ** 2 for v, sigma in pairs)\n        output.append({"sample": sample, "n": len(pairs), "mean_K": mean,\n                       "standard_error_K": se, "chi2": chi2})\n    return {"samples": output, "n_usable": len(records), "n_skipped": skipped}\n'

CONTRACT = '## 科学任务\n实现温度仪器 CSV 清洗和逆方差加权汇总。输入唯一必需字段 `csv` 是完整 CSV 字符串。\n表头（允许字段名两侧空白，顺序严格相同）为 `sample,replicate,value,unit,sigma,status`；允许开头 BOM、CRLF、CSV 引号及被引号保护的逗号。每行恰好六列；全空行由标准 csv 解析器忽略。\n所有单元格去首尾空白。sample/replicate 是非空、区分大小写的字符串；status 只能为 ok/reject。\n先验证列数、身份和 status。之后 reject 行，或 value/sigma 为区分大小写的缺失标记 `""`、`NA`、`N/A`、`null` 的行，计入 n_skipped 并跳过；这些行的 unit 和数值不再验证。\n其余行 unit 只能为 K、C、mK；value、sigma 必须是有限实数，sigma>0。K=value、C=value+273.15、mK=value/1000；sigma 是标准不确定度，C 与 K 的 sigma 相同，mK 的 sigma 除以1000，绝不可给 sigma 加273.15。换算温度必须>=0 K。\n重复键(sample,replicate)采用文件中最后一条可用行；被跳过行不覆盖旧记录。不要把重复行当独立重复。\n每个 sample 按字典序输出：w_i=1/sigma_i²，mean_K=Σw_i T_i/Σw_i，standard_error_K=1/sqrt(Σw_i)，chi2=Σ((T_i-mean_K)/sigma_i)²；sigma 是已知独立测量误差，不能用样本SD替代。汇总只按不同 replicate 计数。\n返回严格结构 `{"samples":[{"sample":str,"n":int,"mean_K":float,"standard_error_K":float,"chi2":float},...],"n_usable":int,"n_skipped":int}`。无可用行时 samples=[]，n_usable=0。n_skipped 统计物理行而非唯一键。\n有效范围：最多20000行；温度0..1e6 K，换算sigma为1e-100..1e6 K，数据设计使chi2有限。其余输入错误抛ValueError，不接受NaN、Infinity。无需输出逐行诊断。'

_namespace = {}
exec(compile(SOURCE, "<reference-solution>", "exec"), _namespace)
_solve = _namespace["solve"]

def prompt(seed=17):
    visible = {'csv': 'sample,replicate,value,unit,sigma,status\nB,1,273150,mK,1000,ok\nA,1,0,C,1,ok\nA,2,275.15,K,2,ok\n'}
    return ("# " + TASK["id"] + " — " + TASK["title"] + "\n\n" + CONTRACT +
        "\n\n## 提交与运行\n离线环境：Python 3.12；可用标准库、NumPy 2.3.5、SciPy 1.17.0。"
        "无需网络、外部数据或额外安装。本文件是独立完整题面。"
        "提交 solution.py、report.md、tests.py；solution.py 顶层不得读取 stdin、联网或执行测试。"
        "评分器导入后调用 solve(problem)，problem 是一个 JSON 对象，返回值必须严格可 JSON 序列化"
        "（不含 NaN/Infinity），不要打印。异常输入必须抛出 ValueError。"
        "report.md 解释公式、单位、边界条件、复杂度和验证，tests.py 用断言验证实现。"
        "A/basic 测基础契约，B/scientific 测科学语义，C/stress 测数值与边界鲁棒性。"
        "编程自动测试合计 70 分，其余 30 分由人工评价报告与测试；难度标签为设计意图，未经实测校准。"
        "浮点结果保留至少 12 位有效数字，允许按字段容差比较。"
        "\n\n## 可见示例输入（不提供正确输出）\n```json\n" +
        json.dumps(visible, ensure_ascii=False, indent=2) + "\n```\n")

def reference_submission(seed=17):
    return {"task_id": TASK["id"], "artifacts": {"solution.py": SOURCE,
        "report.md": REPORT, "tests.py": SAMPLE_TESTS}, "answer": {}}

def mutants(seed=17):
    result = {"reference": reference_submission(seed)}
    for label, source in MUTANT_SOURCES.items():
        entry = reference_submission(seed)
        entry["artifacts"]["solution.py"] = source
        result[label] = entry
    return result

def cases(seed=17):
    shift = int(seed) % 11
    header = "sample,replicate,value,unit,sigma,status\n"
    rows = [
        ("parse_units", "basic", header + 'B,1,273150,mK,1000,ok\nA,1,0,C,1,ok\nA,2,275.15,K,2,ok\n', 12),
        ("empty", "basic", header, 8),
        ("duplicates_missing", "scientific", header + 'A,1,20,C,0.2,ok\nA,1,294.15,K,0.1,ok\nA,1,NA,bad,0,ok\nA,2,296150,mK,400,ok\nB,1,garbage,bad,0,reject\n', 15),
        ("quoted_bom", "scientific", '\ufeff' + header.replace('\n','\r\n') + '"chip, left", r1 , 300 , K , 0.2 , ok\r\n"chip, left",r2,302,K,0.5,ok\r\n', 15),
        ("scaled_variance", "stress", header + f'A,1,{300+shift},K,1e-100,ok\nA,2,{301+shift},K,2e-100,ok\n', 10),
    ]
    import csv as _csv
    import io as _io
    import random as _random
    rng = _random.Random(f"C01-v1:{int(seed)}")
    for index, (cid, tier, text, weight) in enumerate(rows):
        if tier != "scientific":
            continue
        offset, sigma_factor = rng.uniform(-3, 3), rng.uniform(0.6, 1.8)
        table = list(_csv.reader(_io.StringIO(text.lstrip("\ufeff"))))
        for row in table[1:]:
            if row[5].strip() != "ok" or row[2].strip() in {"", "NA", "N/A", "null"}:
                continue
            unit = row[3].strip()
            row[2] = format(float(row[2]) + offset * (1000 if unit == "mK" else 1), ".17g")
            row[4] = format(float(row[4]) * sigma_factor, ".17g")
        stream = _io.StringIO()
        _csv.writer(stream, lineterminator="\r\n" if "\r\n" in text else "\n").writerows(table)
        rows[index] = (cid, tier, ("\ufeff" if text.startswith("\ufeff") else "") + stream.getvalue(), weight)
    out = [{"id":i,"tier":tier,"input":{"csv":csv},"expected":_solve({"csv":csv}),"weight":w,"critical":i in {"duplicates_missing","parse_units"},"rtol":2e-11,"atol":1e-110} for i,tier,csv,w in rows]
    for i, body in enumerate(['A,1,NaN,K,1,ok\n', 'A,1,300,K,0,ok\n', 'A,1,1,F,1,ok\n', 'A,1,-300,C,1,ok\n', 'A,1,300,K,1,ok,extra\n']):
        out.append({"id":f"invalid_{i}","tier":"stress","input":{"csv":header+body},"error":"ValueError","weight":2,"critical":False,"rtol":0,"atol":0})
    return out


REPORT = '# 方法与验证\n以(sample,replicate)作为测量身份，先按规范过滤被拒绝或缺失行，再让最后一条可用记录覆盖旧值。这样技术性导出重复不会缩小标准误；缺失修订不会删除旧的有效测量。CSV使用标准库解析，支持引号内逗号、BOM及CRLF，逐字段去空白，未知单位与非有限实数均拒绝。\n\n温度的C→K变换是加273.15；标准不确定度是温差，因此只缩放而不加偏移。mK温度与sigma同时乘0.001。已知、独立、无协方差的sigma下，加权均值是逆方差加权，标准误为1/sqrt(sum(1/sigma²))；chi2度量围绕共同温度模型的失配，未将它当作样本标准差。实现以最小sigma缩放权重，避免1/sigma²对极小sigma溢出，均值和方差归一化不受此共同缩放影响。\n\n独立检验使用273.15和277.15 K、sigma分别1和2 K，其解析加权均值273.95 K、标准误sqrt(0.8) K、chi2=3.2；另测重复键、缺失记录、含逗号标识与极小sigma。参考tests.py提供更小的单位一致性检验。时间O(R+U log U)，空间O(U)，R是行数，U是不同可用身份数。\n\n推断范围仅是该CSV所给测量的已知误差汇总。相关误差、仪器漂移、校准偏差、不同样本间的总体方差均未建模；chi2大也不能自行证明特定机理。'

SAMPLE_TESTS = 'from solution import solve\nh = "sample,replicate,value,unit,sigma,status\\n"\nr = solve({"csv": h + "x,1,0,C,1,ok\\nx,2,273150,mK,1000,ok\\n"})\nassert abs(r["samples"][0]["mean_K"] - 273.15) < 1e-12\nassert abs(r["samples"][0]["standard_error_K"] - 2**-0.5) < 1e-12\nassert solve({"csv": h})["samples"] == []\n'

MUTANT_SOURCES = {'duplicate_first': SOURCE.replace('records[(row["sample"], row["replicate"])] = (temperature, uncertainty)', 'records.setdefault((row["sample"], row["replicate"]), (temperature, uncertainty))'), 'unweighted_summary': SOURCE.replace('weights = [(scale / sigma) ** 2 for _, sigma in pairs]', 'weights = [1.0 for _ in pairs]')}

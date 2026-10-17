"""V1.0 public synthetic coding task; hidden expectations stay host-side."""
from __future__ import annotations
import copy
import json

TASK = {'id': 'C02', 'title': '独立组与分层 bootstrap 模型比较', 'language': 'python', 'difficulty': 2, 'capabilities': ['clustered-data', 'bootstrap', 'deterministic-statistics'], 'time_budget_s': 900, 'required_artifacts': ['solution.py', 'report.md', 'tests.py'], 'essential': [{'id': 'api', 'requirement': 'solution.py 提供 solve(problem)，返回约定的 JSON 可序列化值，错误输入抛 ValueError。'}, {'id': 'science', 'requirement': 'report.md 解释科学定义、算法、单位、验证依据及适用范围。'}, {'id': 'tests', 'requirement': 'tests.py 包含可运行且有断言的独立测试，至少覆盖一个非平凡性质和一个边界。'}]}

SOURCE = 'import math\n\ndef solve(problem):\n    try:\n        rows = problem["rows"]\n        B, seed = problem["bootstrap_replicates"], problem["seed"]\n        if not isinstance(rows, list) or not rows or len(rows)>20000 or isinstance(B, bool) or not isinstance(B, int) or not 1 <= B <= 20000:\n            raise ValueError("rows or bootstrap count")\n        if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**32:\n            raise ValueError("seed")\n        units, seen = {}, set()\n        for row in rows:\n            stratum, group, repeat = row["stratum"], row["group"], row["repeat"]\n            if any(not isinstance(v, str) or not v for v in [stratum, group, repeat]):\n                raise ValueError("identifier")\n            key = (stratum, group, repeat)\n            if key in seen:\n                raise ValueError("duplicate repeat")\n            seen.add(key)\n            a, b = row["loss_a"], row["loss_b"]\n            if any(isinstance(v, bool) or not isinstance(v, (int,float)) or not math.isfinite(v) or not 0 <= v <= 1e6 for v in [a,b]):\n                raise ValueError("loss")\n            units.setdefault((stratum, group), []).append((repeat, a-b))\n        if len(units)>2000: raise ValueError("too many groups")\n        strata = {}\n        for (stratum, group), values in sorted(units.items()):\n            d = math.fsum(v for _, v in sorted(values)) / len(values)\n            strata.setdefault(stratum, []).append(d)\n        names = sorted(strata)\n        means = [math.fsum(strata[s])/len(strata[s]) for s in names]\n        estimate = math.fsum(means) / len(names)\n        samples = []\n        state = seed\n        for _ in range(B):\n            vals = []\n            for s in names:\n                group_values = strata[s]\n                n = len(group_values)\n                selected = []\n                for _ in range(n):\n                    state = (1664525 * state + 1013904223) % 2**32\n                    index = (state * n) // 2**32\n                    selected.append(group_values[index])\n                vals.append(math.fsum(selected)/n)\n            samples.append(math.fsum(vals)/len(names))\n        ordered = sorted(samples)\n        def quantile(p):\n            h = (B-1)*p\n            lo = math.floor(h)\n            hi = min(lo+1, B-1)\n            return ordered[lo] + (h-lo)*(ordered[hi]-ordered[lo])\n        return {"estimate": estimate, "ci95": [quantile(0.025),quantile(0.975)],\n                "bootstrap_nonpositive_fraction": (1+sum(v <= 0 for v in samples))/(B+1),\n                "n_groups": len(units), "strata": [{"stratum":s,"n_groups":len(strata[s]),"mean_difference":m} for s,m in zip(names,means)]}\n    except (KeyError, TypeError, OverflowError) as exc:\n        raise ValueError("invalid problem") from exc\n'

CONTRACT = '## 科学任务\n比较两个预测模型在嵌套重复实验上的损失，避免把同一独立组内的技术重复当独立样本。\n输入 `rows` 为非空列表；每行含非空字符串 stratum、group、repeat 和有限非负数字 loss_a、loss_b。独立单位为(stratum,group)，repeat 只在该单位内标记技术重复；相同三元组重复是错误。不同stratum可重用group名。每个技术重复的配对差 d=loss_a-loss_b，正数表示 B 较优。\n先对各组技术重复的 d 取算术均值，再对每个stratum内的组均值等权平均，最后对不同stratum等权平均，得estimate。不是按行加权，也不是按各stratum的组数加权。\n输入另含 bootstrap_replicates（整数1..20000）及seed（32位无符号整数）。执行分层组bootstrap：stratum与group按Python字符串字典序排序；每个重复依次访问stratum，在有n组的stratum中有放回抽n组；每抽一次更新LCG状态 x=(1664525*x+1013904223) mod 2^32，并用 index=(x*n)//2^32（从0起），状态从seed开始且贯穿全部重复，不重置。每个bootstrap样本按同一分层等权公式汇总。无技术重复重采样。\n95%区间对B个排序bootstrap值取0.025和0.975线性分位数：h=(B-1)p，Q=(1-frac(h))*x_floor(h)+frac(h)*x_ceil(h)。bootstrap_nonpositive_fraction=(1+bootstrap值<=0的数量)/(B+1)，这是预定义描述量，不声称是严格假设检验p值。\n返回 `{"estimate":float,"ci95":[lo,hi],"bootstrap_nonpositive_fraction":float,"n_groups":int,"strata":[{"stratum":str,"n_groups":int,"mean_difference":float},...]}`，strata按字典序。\n范围：最多2000个组，20000行，损失<=1e6；测试规模保证算法在预算内。组可能只有一个重复，stratum可能只有一个组，B可能为1。非法输入抛ValueError。\n报告需说明独立单位、等权目标人群、区间的条件含义及单组层的不确定性局限。'

_namespace = {}
exec(compile(SOURCE, "<reference-solution>", "exec"), _namespace)
_solve = _namespace["solve"]

def prompt(seed=17):
    visible = {'rows': [{'stratum': 'A', 'group': 'one', 'repeat': '0', 'loss_a': 4, 'loss_b': 2}, {'stratum': 'A', 'group': 'one', 'repeat': '1', 'loss_a': 2, 'loss_b': 2}], 'bootstrap_replicates': 1, 'seed': 17}
    visible["seed"] = int(seed) % 2**32
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
    def rows(spec):
        return [{"stratum":s,"group":g,"repeat":str(i),"loss_a":a,"loss_b":b} for s,g,pairs in spec for i,(a,b) in enumerate(pairs)]
    fixtures = [
        ("one_group", "basic", [("A","one",[(4,2),(2,2)])], 1, 10),
        ("paired_groups", "basic", [("A","x",[(4,2)]),("A","y",[(1,2)]),("A","z",[(5,1)])], 101, 10),
        ("unequal_technical_repeats", "scientific", [("A","x",[(6,1)]*7),("A","y",[(1,5)]),("B","x",[(2,1)]),("B","z",[(2,4)]),("B","a",[(4,1)])], 257, 15),
        ("stratum_target", "scientific", [], 61, 15),
    ]
    fixtures[3] = ("stratum_target","scientific",[("a","0",[(0,9)])]+[("z",str(i),[(10+i,1)]) for i in range(7)],61,15)
    out=[]
    for i,tier,spec,B,w in fixtures:
        p={"rows":rows(spec),"bootstrap_replicates":B,"seed":int(seed)%2**32}
        out.append({"id":i,"tier":tier,"input":p,"expected":_solve(p),"weight":w,"critical":tier=="scientific","rtol":2e-12,"atol":1e-12})
    p={"rows":rows([("a","g",[(0,0)]),("b","g",[(2,2)])]),"bootstrap_replicates":2,"seed":2**32-1}
    out.append({"id":"zero_and_uint32","tier":"stress","input":p,"expected":_solve(p),"weight":10,"critical":False,"rtol":1e-12,"atol":1e-12})
    for i,p in enumerate([{"rows":[],"bootstrap_replicates":2,"seed":1},{"rows":[{"stratum":"a","group":"g","repeat":"r","loss_a":1,"loss_b":0}]*2,"bootstrap_replicates":2,"seed":1}]):
        out.append({"id":f"invalid_{i}","tier":"stress","input":p,"error":"ValueError","weight":5,"critical":False,"rtol":0,"atol":0})
    return out


REPORT = '# 统计目标与实现\n每个(stratum,group)才是独立采样单位，先平均组内技术重复的配对损失差。层内组等权、层间再等权，目标是各层占同样权重的合成人群平均模型差；它与按行平均或按层组数加权的总体不是同一估计量。loss_a-loss_b为正仅表示本定义下B的损失较小。\n\nBootstrap保持层数不变，在各层独立有放回重采样其组均值；不能拆散配对，也不能在技术重复层面重采样。LCG及整数索引完全按题面执行，单组层仍消耗一次随机数；ID排序确保输入行置换不改变结果。对排序的B个结果按(B-1)p插值，以避免不同统计包的默认分位数定义差异。加一的非正比例是题目指定描述统计量，没有严格假设检验的零分布保证。\n\n验证包括单组的点质量分布、技术重复数不等的反例、层大小不等的反例、手工重放7次LCG抽样以及行顺序置换。独立组bootstrap仍以观测组代表目标组为前提；一个组的层无法估计该层的组间变异，多做bootstrap重复不能创造独立信息。未声称区间具有精确的有限样本95%覆盖。\n\n预处理O(R log R)，bootstrap时间O(BG)、内存O(R+B)，G为独立组数。报告输出独立组数而非技术重复数。'

SAMPLE_TESTS = 'from solution import solve\np={"rows":[{"stratum":"a","group":"g","repeat":"1","loss_a":4,"loss_b":1}],"bootstrap_replicates":3,"seed":0}\nr=solve(p)\nassert r["estimate"] == 3 and r["ci95"] == [3,3]\nassert r["bootstrap_nonpositive_fraction"] == 0.25\np["rows"][0]["loss_a"]=1\nassert solve(p)["bootstrap_nonpositive_fraction"] == 1\n'

MUTANT_SOURCES = {'technical_pseudoreplication': SOURCE.replace('d = math.fsum(v for _, v in sorted(values)) / len(values)', 'd = math.fsum(v for _, v in sorted(values))').replace('strata.setdefault(stratum, []).append(d)', 'strata.setdefault(stratum, []).extend([d / len(values)] * len(values))'), 'pooled_strata': SOURCE.replace('estimate = math.fsum(means) / len(names)', 'estimate = math.fsum(math.fsum(strata[s]) for s in names) / len(units)')}

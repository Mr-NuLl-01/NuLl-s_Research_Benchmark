"""V1.0 public synthetic coding task; hidden expectations stay host-side."""
from __future__ import annotations
import copy
import json

TASK = {'id': 'C05', 'title': '带源项时间表的刚性反应自适应积分', 'language': 'python', 'difficulty': 5, 'capabilities': ['stiff-integration', 'adaptive-steps', 'rollback', 'floating-point-endpoints'], 'time_budget_s': 1800, 'required_artifacts': ['solution.py', 'report.md', 'tests.py'], 'essential': [{'id': 'api', 'requirement': 'solution.py 提供 solve(problem)，返回约定的 JSON 可序列化值，错误输入抛 ValueError。'}, {'id': 'science', 'requirement': 'report.md 解释科学定义、算法、单位、验证依据及适用范围。'}, {'id': 'tests', 'requirement': 'tests.py 包含可运行且有断言的独立测试，至少覆盖一个非平凡性质和一个边界。'}]}

SOURCE = 'import bisect\nimport math\n\ndef solve(problem):\n    try:\n        def finite(v):\n            return not isinstance(v,bool) and isinstance(v,(int,float)) and math.isfinite(v)\n        t0,t1=problem["t0_s"],problem["t1_s"]\n        initial=problem["initial"]\n        rates=problem["rates_s_inv"]\n        schedule=problem["source_schedule"]\n        observations=problem["observation_times_s"]\n        atol,rtol=problem["atol"],problem["rtol"]\n        h=problem["initial_step_s"]\n        if not finite(t0) or not finite(t1) or not 0<t1-t0<=1e9:\n            raise ValueError("interval")\n        if not isinstance(initial,list) or len(initial)!=2 or any(not finite(v) or v<0 for v in initial):\n            raise ValueError("initial")\n        if not isinstance(rates,list) or len(rates)!=3 or any(not finite(v) or v<0 for v in rates):\n            raise ValueError("rates")\n        if any(not finite(v) or v<=0 for v in [atol,rtol,h]):\n            raise ValueError("tolerances")\n        if not isinstance(schedule,list) or not schedule or schedule[0][0]!=t0:\n            raise ValueError("schedule origin")\n        if any(not isinstance(v,list) or len(v)!=2 or not finite(v[0]) or not finite(v[1]) or v[1]<0 or not t0<=v[0]<t1 for v in schedule):\n            raise ValueError("schedule")\n        if any(schedule[i][0]>=schedule[i+1][0] for i in range(len(schedule)-1)):\n            raise ValueError("schedule order")\n        if not isinstance(observations,list) or not observations or any(not finite(v) or not t0<=v<=t1 for v in observations) or any(observations[i]>=observations[i+1] for i in range(len(observations)-1)):\n            raise ValueError("observation order")\n        # Shift the clock before stepping: large absolute timestamps must not\n        # make a valid small step fail t+h==t or erase an endpoint remainder.\n        breaks=[v[0]-t0 for v in schedule]\n        targets=sorted(set([v-t0 for v in observations]+breaks+[t1-t0]))\n        wanted={v-t0:v for v in observations}\n        kf,kr,decay=rates\n        def backward(y,step,q):\n            a=1+step*(kf+decay)\n            b=-step*kr\n            c=-step*kf\n            d=1+step*(kr+decay)\n            determinant=1+step*(kf+kr+2*decay)+step*step*decay*(kf+kr+decay)\n            rhs0=y[0]+step*q\n            rhs1=y[1]\n            return [(d*rhs0-b*rhs1)/determinant, (a*rhs1-c*rhs0)/determinant]\n        y=list(initial)\n        tau=0.0\n        accepted=rejected=0\n        result=[]\n        for target in targets:\n            while tau<target:\n                if accepted+rejected>=200000:\n                    raise ValueError("trial budget exceeded")\n                trial=min(h,target-tau)\n                if trial<=0 or tau+trial==tau:\n                    raise ValueError("step cannot advance local clock")\n                q=schedule[bisect.bisect_right(breaks,tau)-1][1]\n                full=backward(y,trial,q)\n                half=backward(backward(y,0.5*trial,q),0.5*trial,q)\n                error=max(abs(half[i]-full[i])/(atol+rtol*max(abs(y[i]),abs(half[i]))) for i in range(2))\n                factor=5.0 if error==0 else min(5.0,max(0.2,0.9/math.sqrt(error)))\n                if error<=1:\n                    y=half\n                    tau=target if trial==target-tau else tau+trial\n                    accepted+=1\n                else:\n                    rejected+=1\n                h=trial*factor\n            if target in wanted:\n                result.append({"time_s":wanted[target],"state":list(y)})\n        return {"observations":result,"accepted_steps":accepted,"rejected_steps":rejected}\n    except (KeyError,TypeError,IndexError,OverflowError,ZeroDivisionError) as exc:\n        raise ValueError("invalid problem") from exc\n'

CONTRACT = '## 科学任务：刚性反应的自适应隐式积分与时间表切换\n两组分A/B的非负浓度状态y=[a,b]，时间单位s：da/dt=-(kf+d)a+kr*b+q(t)，db/dt=kf*a-(kr+d)b。rates_s_inv=[kf,kr,d]均有限非负，q是向A注入浓度/秒的非负分段常数，初值非负。该线性系统可高度刚性；必须实现以下**规定的自适应算法**，不能用解析解、solve_ivp或固定步长替代返回结果与计数。\n输入：t0_s、t1_s（0<t1-t0<=1e9），initial=[a0,b0]，rates_s_inv，source_schedule=[[time,q],...]；schedule非空，首时间严格等于t0，其余严格递增且<t1，采用右连续q。observation_times_s非空、严格递增、位于闭区间[t0,t1]。atol、rtol、initial_step_s均正且有限。initial为浓度，atol同浓度单位，rtol无量纲。\n算法细节（本题算法是评测对象）：\n1. 先把内部时钟全部平移为tau=t-t0，所有schedule/observation/末端时间以输入浮点数作减法得到偏移；这样大绝对时间戳下仍能用小内部步长。排序去重后的全部schedule偏移、observation偏移和(t1-t0)组成硬停点，包含tau=0。只在所要求的observation时刻输出，保留原输入time_s。\n2. 初始建议步长h=initial_step_s，y=initial。向下一个硬停点target推进时，trial=min(h,target-tau)，在当前右连续q下算一次后向Euler全步Y_full，再从**同一旧y**算两个trial/2半步得Y_half。线性后向Euler为 `(I-step*M)Y=y+step*[q,0]`，M=[[-(kf+d),kr],[kf,-(kr+d)]]。推荐将2×2行列式展开为 `1+step*(kf+kr+2*d)+step²*d*(kf+kr+d)`，避免快交换率时大数相减。\n3. e=max_i |Y_half_i-Y_full_i|/(atol+rtol*max(|old_y_i|,|Y_half_i|))。e<=1接受，状态取Y_half；否则拒绝，tau与y完全回滚。无Richardson外推、无非负截断。\n4. 无论接收或拒绝，factor=5（e=0），否则min(5,max(0.2,0.9/sqrt(e)))；h=trial*factor。e=1算接受。接受后若trial恰等于target-old_tau，令tau=target精确落点，否则tau=old_tau+trial；严禁以固定epsilon忽略末端剩余区间。遇schedule停点后下一步用新q；h沿用，不能重置。零长度停点不做试步，不增加计数。\n5. accepted_steps/rejected_steps分别只计相应试步。总试步达到200000仍需推进、trial不能推进本地时钟、或非法输入均抛ValueError。本题有效科学案例远低于此上限。浮点范围保证中间值有限；无需求解输入无法表示的时间差。\n返回 `{"observations":[{"time_s":原输入时间,"state":[a,b]},...],"accepted_steps":int,"rejected_steps":int}`，观察顺序相同。状态约按1e-9相对容差比较，步数必须符合规定算法。为了计数可重复，使用IEEE binary64及普通math.sqrt，不能把误差比较换成isclose。所有合法输入都是JSON数值，不接受bool。\n报告解释刚性、拒绝回滚、硬停点左右语义、局部误差与全局误差的区别，以及d=0,q=0时a+b守恒和精确平衡态不变。该算法是教学型一阶自适应积分器，容差不等于严格全局误差证书。'

_namespace = {}
exec(compile(SOURCE, "<reference-solution>", "exec"), _namespace)
_solve = _namespace["solve"]

def _kinetic_variation(seed):
    import random
    rng = random.Random(f"C05-v1:{int(seed)}")
    return ([rng.uniform(600, 1600), rng.uniform(2, 5), rng.uniform(0.1, 0.3)],
            [rng.uniform(400, 900), rng.uniform(1, 4), rng.uniform(0.05, 0.2)],
            [rng.uniform(0.8, 1.2), rng.uniform(0.8, 1.2)])

def prompt(seed=17):
    visible = {'t0_s': 0, 't1_s': 1.0, 'initial': [1, 0], 'rates_s_inv': [800, 3, 0.2], 'source_schedule': [[0, 0], [0.17, 4], [0.55, 0.5]], 'observation_times_s': [0, 0.17, 0.4, 0.55, 1], 'initial_step_s': 0.6, 'atol': 1e-07, 'rtol': 1e-05}
    _, schedule_rates, strengths = _kinetic_variation(seed)
    visible["rates_s_inv"] = schedule_rates
    for entry, factor in zip(visible["source_schedule"][1:], strengths):
        entry[1] *= factor
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
    def p(k=(2,1,0),initial=(1,0),stop=1,q=None,times=None,h=0.3,t0=0,atol=1e-7,rtol=1e-5):
        return {"t0_s":t0,"t1_s":t0+stop,"initial":list(initial),"rates_s_inv":list(k),"source_schedule":q or [[t0,0]],"observation_times_s":times or [t0,t0+stop],"initial_step_s":h,"atol":atol,"rtol":rtol}
    fixtures=[
        ("equilibrium","basic",p(initial=(1,2)),10),
        ("zero_rates_source","basic",p(k=(0,0,0),initial=(0,0),q=[[0,3]],times=[0,0.25,1]),10),
        ("stiff_rollback","scientific",p(k=(800,3,0.2),stop=0.8,times=[0,0.01,0.2,0.8],h=0.8),15),
        ("right_continuous_schedule","scientific",p(k=(7,2,0.1),stop=1.0,q=[[0,0],[0.17,4],[0.55,0.5]],times=[0,0.17,0.4,0.55,1],h=0.6),15),
        ("large_absolute_clock","stress",p(k=(3,2,0),stop=0.01,t0=1e12,h=1e-5,times=[1e12,1e12+0.002,1e12+0.01]),7),
        ("floating_endpoint","stress",p(k=(0,0,0.1),stop=0.3,initial=(0.3+int(seed)%3,0.1),times=[0,0.1,0.2,0.3],h=0.1),7),
        ("single_observation","stress",p(k=(0,0,0),stop=0.7,q=[[0,2],[0.2,5]],times=[0.2]),2),
    ]
    stiff_rates, schedule_rates, strengths = _kinetic_variation(seed)
    for cid, tier, problem, weight in fixtures:
        if cid == "stiff_rollback":
            problem["rates_s_inv"] = stiff_rates
        elif cid == "right_continuous_schedule":
            problem["rates_s_inv"] = schedule_rates
            for entry, factor in zip(problem["source_schedule"][1:], strengths):
                entry[1] *= factor
    out=[{"id":i,"tier":tier,"input":v,"expected":_solve(v),"weight":w,"critical":tier=="scientific" or i=="large_absolute_clock","rtol":2e-9,"atol":2e-11} for i,tier,v,w in fixtures]
    for i,pb in enumerate([p(times=[0.2,0.2]),p(k=(-1,1,0))]):
        out.append({"id":f"invalid_{i}","tier":"stress","input":pb,"error":"ValueError","weight":2,"critical":False,"rtol":0,"atol":0})
    return out


REPORT = '# 自适应积分与调度\n该算法解两个非负组分的线性可逆交换、共同移除与分段常数注入。快速交换和慢移除可产生尺度分离；后向Euler避免显式稳定步长限制，但仍需误差控制。全步和两个半步从同一旧状态开始；两半步与全步的差用于一阶局部误差指标，接受两半步值，不做外推。\n\n拒绝试步必须同时保持旧状态和旧时间。建议h在每次尝试后用规定的有界平方根控制器更新。源项变化与观察时间均为硬停点，不能跨越源项跳变后再插值；到达变化点之前最后一步用旧q，到达之后用右连续新q。调度点不重置h，零长度停点不计数。\n\n先平移时间为tau=t-t0，再按剩余间隔裁剪试步，接受最后裁剪步时显式赋tau=target。这避免大绝对时间戳吞掉小步，也避免固定epsilon错误丢失末段；不把算法走不动的情况伪装成完成。2×2系统行列式用展开的正项计算，避免kf*kr大项相消。\n\n独立验证包括平衡态不动、d=q=0时a+b守恒、单向解析指数衰减/交换解、零反应率的精确分段线性注入、会发生拒绝的刚性初始层、以及二进制可表示时间平移后状态与步数完全一致。计数是规定算法的执行轨迹，不是数学误差证书。一步局部容差不能保证同量级全局误差；没有声称本方法替代通用高阶刚性求解器。总试步上限200000，每步常数开销，空间随输出和停点数线性。'

SAMPLE_TESTS = 'from solution import solve\np=dict(t0_s=0,t1_s=1,initial=[1,2],rates_s_inv=[2,1,0],source_schedule=[[0,0]],observation_times_s=[0,0.5,1],atol=1e-8,rtol=1e-6,initial_step_s=0.1)\nr=solve(p)\nassert r["rejected_steps"] == 0\nassert all(abs(o["state"][0]-1)<1e-12 and abs(o["state"][1]-2)<1e-12 for o in r["observations"])\np["initial"]=[1,0]\nr=solve(p)\nassert all(abs(sum(o["state"])-1)<1e-10 for o in r["observations"])\nassert r["rejected_steps"] > 0\n'

MUTANT_SOURCES = {'accept_rejected_state': SOURCE.replace('else:\n                    rejected+=1', 'else:\n                    y=half\n                    rejected+=1'), 'left_continuous_source': SOURCE.replace('bisect.bisect_right(breaks,tau)-1', 'max(0,bisect.bisect_left(breaks,tau)-1)'), 'discard_small_remainder': SOURCE.replace('while tau<target:', 'while tau<target and target-tau>1e-3:')}

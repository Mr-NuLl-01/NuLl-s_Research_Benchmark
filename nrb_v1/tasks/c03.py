"""V1.0 public synthetic coding task; hidden expectations stay host-side."""
from __future__ import annotations
import copy
import json

TASK = {'id': 'C03', 'title': '修复分层导热有限体积求解器', 'language': 'python', 'difficulty': 3, 'capabilities': ['debugging', 'finite-volume', 'conservation', 'implicit-methods'], 'time_budget_s': 900, 'required_artifacts': ['solution.py', 'report.md', 'tests.py'], 'essential': [{'id': 'api', 'requirement': 'solution.py 提供 solve(problem)，返回约定的 JSON 可序列化值，错误输入抛 ValueError。'}, {'id': 'science', 'requirement': 'report.md 解释科学定义、算法、单位、验证依据及适用范围。'}, {'id': 'tests', 'requirement': 'tests.py 包含可运行且有断言的独立测试，至少覆盖一个非平凡性质和一个边界。'}]}

SOURCE = 'import math\n\ndef solve(problem):\n    try:\n        dx, k, capacity, initial = [problem[key] for key in ["dx_m", "k_W_mK", "capacity_J_m3K", "initial_K"]]\n        n = len(dx)\n        if not 1 <= n <= 2000 or any(not isinstance(v,list) or len(v) != n for v in [dx,k,capacity,initial]):\n            raise ValueError("length")\n        def finite_number(v):\n            return not isinstance(v,bool) and isinstance(v,(int,float)) and math.isfinite(v)\n        if any(not finite_number(v) or v <= 0 for arr in [dx,k,capacity] for v in arr) or any(not finite_number(v) for v in initial):\n            raise ValueError("physical parameters")\n        dt, steps = problem["dt_s"], problem["steps"]\n        if not finite_number(dt) or dt <= 0 or isinstance(steps,bool) or not isinstance(steps,int) or not 0 <= steps <= 10000:\n            raise ValueError("time")\n        source = problem["source_W_m3"]\n        if not isinstance(source,list) or len(source)!=n or any(not finite_number(v) for v in source):\n            raise ValueError("source")\n        boundaries=[]\n        for side in ["left","right"]:\n            bc=problem[side]\n            if not isinstance(bc,dict) or bc.get("kind") not in {"insulated","fixed"}:\n                raise ValueError("boundary")\n            if bc["kind"] == "fixed" and not finite_number(bc.get("temperature_K")):\n                raise ValueError("boundary temperature")\n            boundaries.append(bc)\n        conductance = [2.0/(dx[i]/k[i]+dx[i+1]/k[i+1]) for i in range(n-1)]\n        mass = [capacity[i]*dx[i] for i in range(n)]\n        lower=[0.0]*n\n        upper=[0.0]*n\n        diagonal=[mass[i]/dt for i in range(n)]\n        forcing=[source[i]*dx[i] for i in range(n)]\n        for i,g in enumerate(conductance):\n            diagonal[i]+=g\n            diagonal[i+1]+=g\n            upper[i]=-g\n            lower[i+1]=-g\n        edges=[]\n        for index,bc in zip([0,n-1],boundaries):\n            if bc["kind"]=="fixed":\n                g=2*k[index]/dx[index]\n                diagonal[index]+=g\n                forcing[index]+=g*bc["temperature_K"]\n                edges.append((index,g,bc["temperature_K"]))\n        temperature=list(initial)\n        boundary_energy=0.0\n        for _ in range(steps):\n            rhs=[mass[i]/dt*temperature[i]+forcing[i] for i in range(n)]\n            b=diagonal.copy()\n            for i in range(1,n):\n                multiplier=lower[i]/b[i-1]\n                b[i]-=multiplier*upper[i-1]\n                rhs[i]-=multiplier*rhs[i-1]\n            new=[0.0]*n\n            new[-1]=rhs[-1]/b[-1]\n            for i in range(n-2,-1,-1):\n                new[i]=(rhs[i]-upper[i]*new[i+1])/b[i]\n            boundary_energy += dt*math.fsum(g*(tb-new[i]) for i,g,tb in edges)\n            temperature=new\n        change=math.fsum(m*(t-t0) for m,t,t0 in zip(mass,temperature,initial))\n        return {"temperature_K":temperature,"energy_change_J_m2":change,\n                "boundary_energy_J_m2":boundary_energy,\n                "source_energy_J_m2":steps*dt*math.fsum(s*d for s,d in zip(source,dx))}\n    except (KeyError,TypeError,OverflowError,ZeroDivisionError) as exc:\n        raise ValueError("invalid problem") from exc\n'

CONTRACT = '## 科学任务：修复一个有多处独立缺陷的有限体积求解器\n求解一维、单位横截面积的分层导热离散模型。每个单元是均匀温度T_i；不是节点边界值。\n输入同长列表 dx_m>0（单元宽m）、k_W_mK>0（导热率W/(m K)）、capacity_J_m3K>0（体积热容J/(m³ K)）、initial_K（有限初温K）、source_W_m3（常数体热源W/m³，可负）；另有dt_s>0、整数steps>=0。\nleft/right 各为 `{"kind":"insulated"}` 或 `{"kind":"fixed","temperature_K":有限数}`。fixed指定单元外表面的温度，不能直接覆盖端单元温度。允许一个单元，此时左右边界作用都需累加。\n数学模型定义：M_i=C_i dx_i，内部面导热G_(i,i+1)=2/(dx_i/k_i+dx_(i+1)/k_(i+1))，热流从j进入i为G_ij(T_j-T_i)。固定边界G_b=2k_i/dx_i，流入为G_b(T_b-T_i)；绝热边界流为0。体热源对单元输入S_i dx_i。\n采用后向Euler，完整同时求解：\nM_i(T_i^(m+1)-T_i^m)/dt=Σ邻面G_ij(T_j^(m+1)-T_i^(m+1))+Σ固定边界G_b(T_b-T_i^(m+1))+S_i dx_i。\n输出 `{"temperature_K":[...],"energy_change_J_m2":Σ M_i(T_i^steps-T_i^0),"boundary_energy_J_m2":dt*Σ步Σ固定边界G_b(T_b-T_i^new),"source_energy_J_m2":steps*dt*Σ S_i dx_i}`。总能量单位J/m²，正号表示进入板材。steps=0原样初值且三项能量为0。不得修改输入。\n有效规模1..2000单元、0..10000步，测试参数正且有限、量级使三对角系统数值可解。应O(steps*n)时间、O(n)内存，不要用显式时间推进替代此离散模型。非法输入抛ValueError。自动容差温度约1e-9相对、能量约1e-7绝对（小数值另设）。报告应解释错误、界面热阻、单元体积与能量守恒；区分离散模型验证和连续PDE收敛声明。\n下面是待修复的完整有缺陷起点；可以重写，但要在report.md逐类说明缺陷。它不是权威公式，以上离散定义才是规范。\n```python\ndef solve(problem):\n    T = problem["initial_K"]\n    dx = problem["dx_m"]\n    k = problem["k_W_mK"]\n    c = problem["capacity_J_m3K"]\n    dt = problem["dt_s"]\n    for step in range(problem["steps"]):\n        for i in range(1, len(T)-1):\n            # In-place forward update, arithmetic k, no cell volume.\n            T[i] += dt / c[i] * ((k[i]+k[i+1])/2*(T[i+1]-T[i])\n                - (k[i-1]+k[i])/2*(T[i]-T[i-1])) / dx[i]**2\n        T[0] = problem["left"].get("temperature_K", T[1])\n        T[-1] = problem["right"].get("temperature_K", T[-2])\n    return {"temperature_K":T,"energy_change_J_m2":0,\n            "boundary_energy_J_m2":0,"source_energy_J_m2":0}\n```'

_namespace = {}
exec(compile(SOURCE, "<reference-solution>", "exec"), _namespace)
_solve = _namespace["solve"]

def prompt(seed=17):
    visible = {'dx_m': [0.2], 'k_W_mK': [3], 'capacity_J_m3K': [20], 'initial_K': [300], 'source_W_m3': [0], 'left': {'kind': 'fixed', 'temperature_K': 280}, 'right': {'kind': 'fixed', 'temperature_K': 320}, 'dt_s': 0.1, 'steps': 3}
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
    def p(dx,k,c,T,source,left,right,dt,steps):
        return dict(dx_m=dx,k_W_mK=k,capacity_J_m3K=c,initial_K=T,source_W_m3=source,left=left,right=right,dt_s=dt,steps=steps)
    ins={"kind":"insulated"}
    fixed=lambda t:{"kind":"fixed","temperature_K":t}
    fixtures=[
        ("one_cell_two_boundaries","basic",p([0.2],[3],[20],[300],[0],fixed(280),fixed(320),0.1,3),10),
        ("zero_steps","basic",p([1,2],[1,2],[3,4],[2,7],[0,0],ins,ins,0.1,0),10),
        ("heterogeneous_conservative","scientific",p([0.1,0.3,0.07],[0.01,20,0.2],[200,50,700],[300,400,270],[0,0,0],ins,ins,0.7,30),15),
        ("source_fixed_mix","scientific",p([0.02,0.03,0.04,0.01],[1,0.05,7,2],[1000,2000,3000,4000],[310,280,300,330],[20,-3,11,0],fixed(295),ins,0.2,13),15),
        ("one_cell_source","stress",p([0.01],[2],[5],[1],[3],ins,ins,0.1,9),5),
        ("stiff_implicit","stress",p([0.01]*40,[3]*40,[2]*40,[273+((i+int(seed))%9) for i in range(40)],[0]*40,ins,ins,10,8),10),
    ]
    import random as _random
    rng = _random.Random(f"C03-v1:{int(seed)}")
    for cid, tier, problem, weight in fixtures:
        if tier == "scientific":
            for key in ("dx_m", "k_W_mK", "capacity_J_m3K"):
                problem[key] = [value * rng.uniform(0.75, 1.25) for value in problem[key]]
            problem["initial_K"] = [value + rng.uniform(-2, 2) for value in problem["initial_K"]]
            problem["source_W_m3"] = [value * rng.uniform(0.8, 1.2) for value in problem["source_W_m3"]]
    out=[{"id":i,"tier":tier,"input":v,"expected":_solve(v),"weight":w,"critical":i in {"one_cell_two_boundaries","heterogeneous_conservative","source_fixed_mix"},"rtol":2e-9,"atol":2e-7} for i,tier,v,w in fixtures]
    bad=p([0],[1],[2],[3],[0],ins,ins,0.1,1)
    out.append({"id":"nonpositive_width","tier":"stress","input":bad,"error":"ValueError","weight":5,"critical":False,"rtol":0,"atol":0})
    return out


REPORT = '# 修复说明与离散模型\n起点代码把显式更新误当隐式更新、就地修改使后续单元使用新旧混合状态、忽略体积热容与宽度权重、使用算术导热率、错误覆盖边界单元、遗漏体热源，且对一个单元访问越界，能量项也只是零占位。参考解依据规范重新组装三对角后向Euler系统，而不保留这些不一致更新。\n\n相邻单元中心之间由两段半单元热阻串联，所以G=1/(dx_i/(2k_i)+dx_j/(2k_j))。左右面共享同一G，流量等大反向，在总能量和中严格抵消。边界面到中心仅半个单元距离，所以固定温度边界G=2k/dx；一个单元同时与左右两个储库换热，两项相加。热容量M=C dx是单位面积热容，热源贡献S dx是单位面积功率。\n\n每步系统主对角为M/dt加所有相邻与边界导热，非对角为-G，右端为M/dt*T_old+S dx+sum(G*T_boundary)。Thomas消元时间与空间均线性。能量账使用新时刻边界温度，和离散隐式方程一致。\n\n独立检验：均匀双单元绝热系统的平均温度不变、对比模态每步乘(1+2G dt/M)^(-1)；任意合法网格总能量变化等于积分边界输入加体热源；无源时温度不超出初值与固定边界的包络。验证对象是给定网格与步长的离散模型，不是对连续PDE的一般收敛证明，也未把大步隐式稳定性等同时间精度。'

SAMPLE_TESTS = 'from solution import solve\np=dict(dx_m=[1.0],k_W_mK=[2.0],capacity_J_m3K=[3.0],initial_K=[4.0],source_W_m3=[6.0],left={"kind":"insulated"},right={"kind":"insulated"},dt_s=0.5,steps=2)\nr=solve(p)\nassert abs(r["temperature_K"][0]-6.0)<1e-12\nassert abs(r["energy_change_J_m2"]-r["source_energy_J_m2"])<1e-12\nassert p["initial_K"]==[4.0]\n'

MUTANT_SOURCES = {'arithmetic_interface': SOURCE.replace('2.0/(dx[i]/k[i]+dx[i+1]/k[i+1])', '(k[i]+k[i+1])/(dx[i]+dx[i+1])'), 'lost_left_boundary_one_cell': SOURCE.replace('edges=[]', 'edges=[]\n        if n == 1: boundaries[0] = {"kind":"insulated"}')}

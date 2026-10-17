"""V1.0 public synthetic coding task; hidden expectations stay host-side."""
from __future__ import annotations
import copy
import json

TASK = {'id': 'C04', 'title': '被动吸收多层薄膜的稳定光学传输', 'language': 'python', 'difficulty': 4, 'capabilities': ['complex-optics', 'transfer-matrix', 'numerical-stability', 'polarization'], 'time_budget_s': 1800, 'required_artifacts': ['solution.py', 'report.md', 'tests.py'], 'essential': [{'id': 'api', 'requirement': 'solution.py 提供 solve(problem)，返回约定的 JSON 可序列化值，错误输入抛 ValueError。'}, {'id': 'science', 'requirement': 'report.md 解释科学定义、算法、单位、验证依据及适用范围。'}, {'id': 'tests', 'requirement': 'tests.py 包含可运行且有断言的独立测试，至少覆盖一个非平凡性质和一个边界。'}]}

SOURCE = 'import cmath\nimport math\n\ndef solve(problem):\n    try:\n        wavelengths=problem["wavelengths_nm"]\n        indices=problem["indices"]\n        thickness=problem["thickness_nm"]\n        angle=problem["angle_deg"]\n        pol=problem["polarization"]\n        def finite(v):\n            return not isinstance(v,bool) and isinstance(v,(int,float)) and math.isfinite(v)\n        if not isinstance(wavelengths,list) or not wavelengths or len(wavelengths)>1000 or any(not finite(v) or not 1e-3<=v<=1e9 for v in wavelengths):\n            raise ValueError("wavelengths")\n        if not isinstance(indices,list) or not 2<=len(indices)<=1002 or not isinstance(thickness,list) or len(thickness)!=len(indices)-2:\n            raise ValueError("layer count")\n        if any(not finite(v) or not 0<=v<=1e12 for v in thickness) or not finite(angle) or not 0<=angle<90 or pol not in {"s","p"}:\n            raise ValueError("thickness, angle or polarization")\n        n=[]\n        for pair in indices:\n            if not isinstance(pair,list) or len(pair)!=2 or any(not finite(v) for v in pair) or not 0.1<=pair[0]<=8 or not 0<=pair[1]<=15:\n                raise ValueError("index")\n            n.append(complex(*pair))\n        if n[0].imag!=0 or n[-1].imag!=0:\n            raise ValueError("half spaces must be lossless")\n        u=n[0].real*math.sin(math.radians(angle))\n        w=[]\n        for value in n:\n            z=cmath.sqrt(value*value-u*u)\n            if z.imag<0 or (z.imag==0 and z.real<0):\n                z=-z\n            if abs(z)<1e-12:\n                raise ValueError("critical angle singularity excluded")\n            w.append(z)\n        q=w if pol=="s" else [value*value/z for value,z in zip(n,w)]\n        result=[]\n        for wavelength in wavelengths:\n            reflection=0j\n            transmission=1+0j\n            for j in range(len(n)-2,-1,-1):\n                r=(q[j]-q[j+1])/(q[j]+q[j+1])\n                t=2*q[j]/(q[j]+q[j+1])\n                phase=cmath.exp(2j*math.pi*w[j+1]*thickness[j]/wavelength) if j<len(thickness) else 1+0j\n                denominator=1+r*reflection*phase*phase\n                transmission=t*transmission*phase/denominator\n                reflection=(r+reflection*phase*phase)/denominator\n            R=abs(reflection)**2\n            T=abs(transmission)**2*q[-1].real/q[0].real\n            result.append({"r":[reflection.real,reflection.imag],"t":[transmission.real,transmission.imag],"R":R,"T":T,"A":1-R-T})\n        return {"spectra":result}\n    except (KeyError,TypeError,OverflowError,ZeroDivisionError) as exc:\n        raise ValueError("invalid problem") from exc\n'

CONTRACT = '## 科学任务：稳定的相干薄膜传输计算\n实现各向同性、非磁、平面平行、光学完全相干多层膜的反射与透射。时间约定 exp(-iωt)，正向场exp(+ik_z z)，折射率n=n_re+i n_im，n_im>=0为被动吸收。\n输入：wavelengths_nm 非空真空波长列表（每项1e-3..1e9 nm）；indices 为从入射到出射的折射率列表，每项 `[n_re,n_im]`、n_re>0、n_im>=0；第一与最后为半无限无吸收介质(n_im=0)，中间为有限层；thickness_nm 按相同顺序给出中间层非负厚度（长度len(indices)-2）。所有nm单位必须一致。angle_deg 为入射光相对法线的角度[0,90)，polarization 为s/p。折射率不随波长变化。\n为避免常见p波反射符号差异，本题统一以**切向电场**为复振幅。令u=n_0 sin(theta_0)，w_j=sqrt(n_j²-u²)，选Im(w)>=0的支路；若Im(w)=0，选Re(w)>=0。s波光学导纳q_j=w_j，p波q_j=n_j²/w_j。\n界面振幅r_ij=(q_i-q_j)/(q_i+q_j)，t_ij=2q_i/(q_i+q_j)。传播相位δ_j=2πw_j d_j/λ。在每个介质内切向电场为E_j(z)=a_j exp(i2πw_j z/λ)+b_j exp(-i2πw_j z/λ)，对应切向磁场（忽略共同常数）为q_j[a_j exp(i2πw_j z/λ)-b_j exp(-i2πw_j z/λ)]。界面两侧这两个总场连续；入射振幅a_0=1，最终半空间无返回波b_last=0，总反射r=b_0，总透射t为最终半空间入口的a_last。所有有限层前向/后向振幅均以该层入口为z=0。\n请从这些物理边界关系自行构造多层组合算法，并选择能处理极厚吸收层的数值表示。不能直接相乘会产生增长指数的未缩放传输矩阵后再依赖最终相消；不得把吸收层厚度裁剪为固定值。本题不提供稳定组合的更新递推，候选需在报告说明其推导、实现与验证。\n返回 `{"spectra":[{"r":[re,im],"t":[re,im],"R":float,"T":float,"A":float},...]}`，与输入波长顺序一致。R=|r|²，T=Re(q_last)/Re(q_0)*|t|²，A=1-R-T。不得用T=|t|²替代功率透射；不得强行裁剪A为0来遮蔽误差。全反射的出射导纳实部为0，T=0；允许有限层倏逝场。\n范围：0..1000有限层、至多1000波长；n_re为0.1..8、n_im为0..15，厚度0..1e12 nm，输入保证所有|w_j|>=1e-12（恰临界奇点不在物理域，遇到则ValueError）。无需求各层吸收、非相干平均、色散、增益或各向异性。其他非法输入抛ValueError。\n报告至少说明支路选择、s/p定义、功率归一化、无损R+T=1与厚吸收层极限，并解释如何避免复sin/cos及增长指数溢出。基本公式可参照公开原始推导 Steven J. Byrnes, “Multilayer optical calculations”, arXiv:1603.02720；题面已包含解题所需全部定义，不需联网。'

_namespace = {}
exec(compile(SOURCE, "<reference-solution>", "exec"), _namespace)
_solve = _namespace["solve"]

def _optical_variation(seed):
    import random
    rng = random.Random(f"C04-v1:{int(seed)}")
    return (rng.uniform(42, 65),
            [value * rng.uniform(0.8, 1.2) for value in [95, 137, 24]],
            [2.2 * rng.uniform(0.9, 1.1), 0.13 * rng.uniform(0.6, 1.4)])

def prompt(seed=17):
    visible = {'indices': [[1, 0], [1.46, 0], [2.2, 0.13], [0.6, 3.7], [1.52, 0]], 'thickness_nm': [95, 137, 24], 'angle_deg': 53, 'polarization': 's', 'wavelengths_nm': [400, 550, 800]}
    angle, thickness, index = _optical_variation(seed)
    visible["angle_deg"] = angle
    visible["thickness_nm"] = thickness
    visible["indices"][2] = index
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
    def p(n,d,angle=0,pol="s",wl=None):
        return {"indices":n,"thickness_nm":d,"angle_deg":angle,"polarization":pol,"wavelengths_nm":wl or [400,550,800]}
    air=[1,0]
    fixtures=[
        ("interface_power","basic",p([air,[1.5,0]],[]),10),
        ("quarterwave","basic",p([air,[2,0],[1.5,0]],[550/8],wl=[550]),10),
        ("oblique_absorbing_s","scientific",p([air,[1.46,0],[2.2,0.13],[0.6,3.7],[1.52,0]],[95,137,24],53,"s"),10),
        ("oblique_absorbing_p","scientific",p([air,[1.46,0],[2.2,0.13],[0.6,3.7],[1.52,0]],[95,137,24],53,"p"),10),
        ("brewster_and_lossless","scientific",p([air,[1.7,0]],[],59.53445508054013,"p",[532]),10),
        ("opaque_layer","stress",p([air,[0.4,8],[1.5,0]],[1e12],71,"p"),6),
        ("evanescent_substrate","stress",p([[1.5,0],[1,0]],[],60,"s"),5),
        ("long_bragg","stress",p([air]+[[2.3,0],[1.45,0]]*70+[[1.52,0]],[550/(4*2.3),550/(4*1.45)]*70,15,"p",[531+(int(seed)%7),550,611]),5),
    ]
    varied_angle, varied_thickness, varied_index = _optical_variation(seed)
    for cid, tier, problem, weight in fixtures:
        if cid in {"oblique_absorbing_s", "oblique_absorbing_p"}:
            problem["angle_deg"] = varied_angle
            problem["thickness_nm"] = list(varied_thickness)
            problem["indices"][2] = list(varied_index)
    out=[{"id":i,"tier":tier,"input":v,"expected":_solve(v),"weight":w,"critical":tier=="scientific" or i=="opaque_layer","rtol":2e-9,"atol":2e-11} for i,tier,v,w in fixtures]
    bad=p([air,[1.5,-0.1]],[])
    out.append({"id":"gain_rejected","tier":"stress","input":bad,"error":"ValueError","weight":4,"critical":False,"rtol":0,"atol":0})
    return out


REPORT = '# 光学约定与稳定实现\n使用exp(-iωt)及正向exp(+ik_z z)，吸收介质n_im>=0；sqrt支路选使正向传播衰减的w。题目限定各向同性、非磁、被动有限层与无损入/出射半空间，因此正常入射功率可用正的Re(q0)归一。s波q=w；p波q=n²/w，因为本题振幅是切向电场，这与某些文献使用全电场且反射p振幅有额外符号的约定不同。\n\n界面和有限层通过右到左的反射/透射递推合并。传播只出现p=exp(iδ)，其模不大于1；没有exp(-iδ)增长因子，也不形成巨大的复sin/cos后再相消。极厚吸收层使p自然下溢为0，对应背界面影响消失、透射为0；未人为裁厚或clip吸收。\n\nR=|r|²，但T必须乘Re(q_out)/Re(q_in)的导纳比。相干吸收A=1-R-T保留数值残差，不强制为非负。倏逝出射波的导纳实部为0，因此T=0，仍可有复反射相位。最接近临界的奇点按题面排除。\n\n独立验证使用场/通量特征矩阵而非相同递推，对多层有吸收的s/p在斜入射逐项比较复r,t；另检查单界面解析Fresnel功率、Brewster角、无损R+T=1、全反射及极厚层向前界面反射极限。复杂度O(Nλ*N层)，额外内存O(N层+Nλ)。这些是有限案例与解析性质检查，没有声称覆盖所有复折射率或连续参数域，也未包含增益、各向异性、粗糙和非相干厚层。\n\n公开原始理论来源：Steven J. Byrnes, Multilayer optical calculations, arXiv:1603.02720（https://arxiv.org/abs/1603.02720），第3、4、5节；作者实现 https://github.com/sbyrnes321/tmm 。参考代码由本benchmark按题面约定独立编写。'

SAMPLE_TESTS = 'from solution import solve\np=dict(indices=[[1,0],[1.5,0]],thickness_nm=[],angle_deg=0,polarization="s",wavelengths_nm=[550])\nr=solve(p)["spectra"][0]\nassert abs(r["R"]-0.04)<1e-12\nassert abs(r["T"]-0.96)<1e-12\np["indices"]=[[1,0],[2,0],[1.5,0]]\np["thickness_nm"]=[100]\nassert abs(solve(p)["spectra"][0]["A"])<1e-12\n'

MUTANT_SOURCES = {'amplitude_as_power': SOURCE.replace('T=abs(transmission)**2*q[-1].real/q[0].real', 'T=abs(transmission)**2'), 'ignore_p_polarization': SOURCE.replace('q=w if pol=="s" else [value*value/z for value,z in zip(n,w)]', 'q=w'), 'opaque_cutoff': SOURCE.replace('w[j+1]*thickness[j]/wavelength', 'w[j+1]*min(thickness[j], 10.0)/wavelength')}

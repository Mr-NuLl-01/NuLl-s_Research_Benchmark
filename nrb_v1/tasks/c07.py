"""C07: variable-projection inverse diffusion with absolute profile uncertainty."""
from __future__ import annotations

import json
import math
import random

TASK = {
    'id':'C07','title':'带独立基线与幅度的逆热扩散：剖面似然与退化诊断',
    'language':'python','difficulty':4,'capabilities':['inverse_problem','variable_projection','profile_likelihood','identifiability'],
    'time_budget_s':2400, "execution_budget_s": 12,'required_artifacts':['solution.py','report.md','tests.py'],
    'essential':[
        {'id':'nuisance','requirement':'同时消除每条实验的独立幅度和基线，使用已知异方差'},
        {'id':'profile','requirement':'对非线性扩散系数构造绝对χ²剖面区间并标记边界截断'},
        {'id':'rank','requirement':'区分有限最小二乘点估计与参数不可识别'},
    ],
}


SOLUTION = r'''import math

def _project(experiment, diffusion, length):
    t,y,sigma=(experiment[k] for k in ('time','value','sigma'))
    rate=math.pi**2/length**2
    x=[math.exp(-diffusion*rate*v) for v in t]
    w=[1/(v*v) for v in sigma]
    sw=math.fsum(w)
    mx=math.fsum(a*b for a,b in zip(w,x))/sw
    my=math.fsum(a*b for a,b in zip(w,y))/sw
    vx=math.fsum(a*(b-mx)**2 for a,b in zip(w,x))
    if vx <= 1e-26*sw:
        raise ValueError('unresolved linear nuisance design')
    amplitude=math.fsum(a*(b-mx)*(c-my) for a,b,c in zip(w,x,y))/vx
    baseline=my-amplitude*mx
    residual=[(baseline+amplitude*a-b)/s for a,b,s in zip(x,y,sigma)]
    chi2=math.fsum(a*a for a in residual)
    # Schur-complement information: remove the two nuisance columns.
    derivative=[-rate*a*b*amplitude for a,b in zip(t,x)]
    md=math.fsum(a*b for a,b in zip(w,derivative))/sw
    slope=math.fsum(a*(b-mx)*(c-md) for a,b,c in zip(w,x,derivative))/vx
    information=math.fsum(a*(b-md-slope*(c-mx))**2 for a,b,c in zip(w,derivative,x))
    return chi2,amplitude,baseline,information

def solve(problem):
    lo,hi=problem['bounds']
    length=problem['length']
    delta=problem.get('delta_chi2',3.841458820694124)
    experiments=problem['experiments']
    scalars=[lo,hi,length,delta]
    if not all(math.isfinite(z) for z in scalars) or not (0<lo<hi and length>0 and delta>0) or not experiments:
        raise ValueError('invalid inverse problem')
    for e in experiments:
        t,y,s=(e[k] for k in ('time','value','sigma'))
        if (len(t)<4 or len(y)!=len(t) or len(s)!=len(t) or
            len(set(t))<3 or min(t)<0 or min(s)<=0 or
            any(not math.isfinite(z) for a in (t,y,s) for z in a)):
            raise ValueError('invalid observations')
        if (hi*math.pi**2/length**2)*max(t)>80:
            raise ValueError('unsupported exponential range')
    def profile(d):
        return math.fsum(_project(e,d,length)[0] for e in experiments)
    # Search all local basins on a fixed coverage mesh; refine each bracket.
    grid=[lo+(hi-lo)*i/256 for i in range(257)]
    vals=[profile(d) for d in grid]
    flat=max(vals)-min(vals)<=1e-16*max(1.,max(vals))
    candidates=[(vals[0],lo),(vals[-1],hi)]
    if not flat:
        ratio=(math.sqrt(5)-1)/2
        for j in range(1,256):
            if vals[j]<=vals[j-1] and vals[j]<=vals[j+1]:
                a,b=grid[j-1],grid[j+1]
                c=b-ratio*(b-a);d=a+ratio*(b-a)
                fc,fd=profile(c),profile(d)
                for _ in range(90):
                    if fc<fd:
                        b,d,fd=d,c,fc;c=b-ratio*(b-a);fc=profile(c)
                    else:
                        a,c,fc=c,d,fd;d=a+ratio*(b-a);fd=profile(d)
                dh=(a+b)/2;candidates.append((profile(dh),dh))
    if flat:
        best=lo
    else:
        best=min(candidates)[1]
    parts=[_project(e,best,length) for e in experiments]
    chi2=math.fsum(a[0] for a in parts)
    information=math.fsum(a[3] for a in parts)
    threshold=chi2+delta
    def endpoint(bound):
        if profile(bound)<=threshold:
            return bound,True
        a,b=sorted((bound,best))
        lower=bound<best
        for _ in range(85):
            middle=(a+b)/2
            inside=profile(middle)<=threshold
            if inside==lower:b=middle
            else:a=middle
        return (a+b)/2,False
    left,left_clipped=endpoint(lo);right,right_clipped=endpoint(hi)
    return {'diffusion':best,'nuisance':[[a[1],a[2]] for a in parts],
            'chi2':chi2,'information':information,
            'identifiable':information>1e-10,
            'interval':[left,right],'clipped':[left_clipped,right_clipped]}
'''


def _solve(p):
    ns={};exec(SOLUTION,ns);return ns['solve'](p)


def cases(seed=17):
    rng=random.Random(seed)
    def make(d=.12,bounds=(.015,.4),noise=True,nexp=2,scale=1.,constant=False):
        length=2.3
        experiments=[]
        for j in range(nexp):
            t=[0.,.12,.35,.75,1.3,2.1,3.4,5.,7.,9.]
            a=(.8+.6*rng.random())*(-1 if j%2 else 1)
            baseline=.4+.2*j
            s=[scale*(.012+.003*(i%3)) for i in range(len(t))]
            y=[baseline+(0 if constant else a)*math.exp(-d*math.pi**2/length**2*x)+(s[i]*rng.gauss(0,1) if noise else 0) for i,x in enumerate(t)]
            experiments.append(dict(time=t,value=y,sigma=s))
        return dict(length=length,bounds=list(bounds),experiments=experiments,delta_chi2=3.841458820694124)
    samples=[('noiseless_nuisance','basic',make(noise=False,nexp=1),10),
             ('known_sigma_scale','basic',make(noise=False,nexp=2),10),
             ('heteroscedastic_shared_D','scientific',make(d=.08+.05*rng.random(),nexp=3),10),
             ('negative_amplitude','scientific',make(d=.19,nexp=2),10),
             ('one_sided_profile','scientific',make(d=.035,bounds=(.04,.35),noise=False,nexp=1),10),
             ('structurally_flat','stress',make(noise=False,nexp=2,constant=True),7),
             ('weak_full_interval','stress',make(d=.11,noise=False,nexp=1,scale=20),7)]
    bad=make();bad['experiments'][0]['sigma'][2]=0;samples.append(('reject_zero_sigma','stress',bad,3))
    bad=make();bad['experiments'][0]['time']=[1.]*10;samples.append(('reject_unresolved_times','stress',bad,3))
    out=[]
    for cid,tier,p,w in samples:
        case=dict(id=cid,tier=tier,input=p,weight=w,critical=True,rtol=3e-6,atol=2e-7)
        try:case['expected']=_solve(p)
        except ValueError:case['error']='ValueError'
        out.append(case)
    return out


def prompt(seed=17):
    rng=random.Random(seed+7007)
    t=[0.,.2,.5,1.,2.,3.,5.,8.]
    p=dict(length=2.3,bounds=[.015,.4],experiments=[dict(time=t,value=[.4+1.1*math.exp(-.13*math.pi**2*x/2.3**2)+rng.gauss(0,.015) for x in t],sigma=[.015]*len(t))],delta_chi2=3.841458820694124)
    return '''# C07 逆热扩散：独立 nuisance 参数、剖面区间和不可识别性
实现Python标准库单文件 solution.py，公开函数 solve(problem)->JSON可序列化字典，另交report.md和tests.py。无网络、外部数据及第三方包。自动70分/人工30分。

一维长度L[m]、两端温度固定的均匀杆，已经隔离出第一空间本征模。第e次实验的传感器记录是
y_e(t)=b_e+a_e exp[-D(pi/L)^2 t]+epsilon，epsilon独立N(0,sigma_e(t)^2)。t单位s，D单位m²/s，a/b/y/sigma单位K。每条实验有自己的未知幅度a_e（允许负值）和基线b_e；仅D共享。sigma是已知绝对标准差，不得用拟合残差重新缩放。

problem含length、bounds=[D_min,D_max]、experiments=[{time,value,sigma}]和delta_chi2。0<D_min<D_max，每条实验≥4点、≥3个不同非负时间，sigma>0，所有数有限，最大D*(pi/L)^2*t≤80。非法输入raise ValueError。
在每个D处用加权线性最小二乘精确消去(a_e,b_e)，得到χ²_profile(D)。求闭区间上全局极小；测试族的非平坦剖面只有一个局部极小。若剖面数值平坦（全范围χ²差≤1e-16*max(1,maxχ²)），选择D_min作为确定性代表。

返回diffusion、nuisance（每实验[a,b]）、chi2、information、identifiable、interval和clipped。information=Σ_e ||(I-P_e) W_e^(1/2) g_e||²，其中g_e,i=-a_e*(pi/L)^2*t_i*exp[-D*(pi/L)^2*t_i]，P_e投影到W^(1/2)[exp(-Dλt),1]的列空间。identifiable精确定义为information>1e-10；不可将优化器成功等同于可识别。
interval是包含最优D的连通剖面集合χ²≤χ²_min+delta_chi2的端点；clipped=[left,right]为端点是否触及搜索边界。若整个范围满足阈值，返回整个bounds及[true,true]。该阈值是指定的似然比构造，不声称有限样本精确覆盖；不使用D_hat±标准差代替它。

数值要求：稳定处理几乎常数的观测、绝对sigma缩放和边界最优。report.md推导变量投影与Schur补信息，讨论a≈0时的结构退化和边界覆盖解释。tests.py至少用无噪声真值与已知sigma整体缩放的独立关系检验。
可见示例输入（未给正确输出）：
'''+json.dumps(p,ensure_ascii=False,indent=2)+'''
分层：basic20，scientific30，stress20。数据跨种子改变。参考原始方法：Golub & Pereyra, SIAM J. Numerical Analysis 10 (1973) 413–432, DOI 10.1137/0710036；已知误差的χ²定义以上式为准。'''


def reference_submission(seed=17):
    return {'task_id':'C07','answer':{},'artifacts':{
        'solution.py':SOLUTION,
        'report.md':'# 方法\n固定D后以加权中心化解二列线性回归，避免正规方程行列式的抵消。外层覆盖搜索加黄金分割求一维极小，再对指定绝对χ²阈值二分求区间。投影后的导数范数给Schur补信息；a=0时D不可识别，代表点不等于物理估计。sigma是仪器给出的绝对误差，不乘残差方差。区间在边界截断时不保证常规渐近覆盖。\n',
        'tests.py':'''import math
from solution import solve
def problem(sigma):
    t=[0,.2,.7,1.5,3.,6.]
    return dict(length=2.,bounds=[.02,.3],experiments=[dict(time=t,value=[.8+1.3*math.exp(-.11*math.pi**2*x/4) for x in t],sigma=[sigma]*6)])
def test_noiseless_and_absolute_sigma():
    a,b=solve(problem(.01)),solve(problem(.02))
    assert abs(a['diffusion']-.11)<1e-7
    assert abs(a['nuisance'][0][0]-1.3)<1e-6
    assert abs(a['nuisance'][0][1]-.8)<1e-6
    assert abs(a['information']/b['information']-4)<1e-5
    assert b['interval'][0]<a['interval'][0]<a['interval'][1]<b['interval'][1]
if __name__=='__main__':test_noiseless_and_absolute_sigma()
'''}}


def mutants(seed=17):
    variants={
        'discard_baseline':SOLUTION.replace('baseline=my-amplitude*mx','baseline=0.0'),
        'ignore_heteroscedastic_sigma':SOLUTION.replace('w=[1/(v*v) for v in sigma]','w=[1.0 for v in sigma]'),
        'conditional_information':SOLUTION.replace('information=math.fsum(a*(b-md-slope*(c-mx))**2 for a,b,c in zip(w,derivative,x))','information=math.fsum(a*b*b for a,b in zip(w,derivative))'),
    }
    out={'reference':reference_submission(seed)}
    for label,src in variants.items():
        sub=reference_submission(seed);sub['artifacts']['solution.py']=src;out[label]=sub
    return out

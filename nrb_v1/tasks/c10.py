"""C10: repair a coupled simulation / tangent / inverse / checkpoint workflow."""
from __future__ import annotations

import json
import math
import random

TASK={
    'id':'C10','title':'修复反应扩散反演流水线：切线导数、守恒、重启和参数自举',
    'language':'python','difficulty':5,
    'capabilities':['multibug_repair','reaction_diffusion','discrete_sensitivity','inverse_problem','reproducible_uncertainty','checkpoint'],
    'time_budget_s':4500, "execution_budget_s": 25,'required_artifacts':['solution.py','report.md','tests.py'],
    'essential':[
        {'id':'physics','requirement':'隐式两物种转化严格守恒，且切线导数针对离散更新'},
        {'id':'inference','requirement':'已知绝对sigma的加权双参数反演、秩诊断及正确协方差'},
        {'id':'restart','requirement':'JSON重启完整保留物理状态与参数切线状态'},
        {'id':'uncertainty','requirement':'指定独立伪随机流的参数自举可复现并真正重拟合'},
    ],
}


SOLUTION=r'''import math
import json

TANGENTS=('dA_dD','dA_dk','dB_dD','dB_dk')

def _inverse(matrix):
    n=len(matrix)
    a=[list(row)+[float(i==j) for j in range(n)] for i,row in enumerate(matrix)]
    for k in range(n):
        p=max(range(k,n),key=lambda i:abs(a[i][k]))
        if abs(a[p][k])<1e-18:raise ValueError('singular update')
        a[k],a[p]=a[p],a[k]
        v=a[k][k];a[k]=[z/v for z in a[k]]
        for i in range(n):
            if i!=k:
                q=a[i][k];a[i]=[x-q*y for x,y in zip(a[i],a[k])]
    return [row[n:] for row in a]

def _multiply(a,x):return [math.fsum(v*w for v,w in zip(row,x)) for row in a]

def _lap(x,length):
    n=len(x);h=length/n
    return [(x[(i-1)%n]-2*x[i]+x[(i+1)%n])/(h*h) for i in range(n)]

def _operators(s):
    n=s['n'];r=s['dt']*s['D']/(s['length']/n)**2
    a=[[0.]*n for _ in range(n)];b=[[0.]*n for _ in range(n)]
    for i in range(n):
        a[i][i]=1+2*r+s['dt']*s['k'];b[i][i]=1+2*r
        for j in ((i-1)%n,(i+1)%n):a[i][j]-=r;b[i][j]-=r
    return _inverse(a),_inverse(b)

def _advance(s,operators):
    ia,ib=operators;dt,k,length=s['dt'],s['k'],s['length']
    a=_multiply(ia,s['A'])
    b=_multiply(ib,[x+dt*k*y for x,y in zip(s['B'],a)])
    lap_a,lap_b=_lap(a,length),_lap(b,length)
    ad=_multiply(ia,[x+dt*y for x,y in zip(s['dA_dD'],lap_a)])
    ak=_multiply(ia,[x-dt*y for x,y in zip(s['dA_dk'],a)])
    bd=_multiply(ib,[x+dt*k*y+dt*z for x,y,z in zip(s['dB_dD'],ad,lap_b)])
    bk=_multiply(ib,[x+dt*y+dt*k*z for x,y,z in zip(s['dB_dk'],a,ak)])
    out=dict(s)
    out.update(A=a,B=b,dA_dD=ad,dA_dk=ak,dB_dD=bd,dB_dk=bk,step=s['step']+1)
    return out

def _validate_state(s):
    n=s['n']
    if not isinstance(n,int) or not 3<=n<=32 or not isinstance(s['step'],int) or s['step']<0:
        raise ValueError('state indices')
    if any(not math.isfinite(s[k]) for k in ('length','D','k','dt')) or s['length']<=0 or s['dt']<=0 or s['D']<0 or s['k']<0:
        raise ValueError('state parameters')
    for key in ('A','B')+TANGENTS:
        if len(s[key])!=n or any(not math.isfinite(z) for z in s[key]):raise ValueError('state vectors')
    if min(s['A']+s['B'])<0:raise ValueError('negative concentration')

def _initial(p,D,k):
    n=len(p['A0'])
    s=dict(n=n,length=p['length'],D=D,k=k,dt=p['dt'],step=0,A=list(p['A0']),B=list(p['B0']))
    s.update({key:[0.]*n for key in TANGENTS})
    _validate_state(s)
    return s

def _resume(state,target):
    _validate_state(state)
    if not isinstance(target,int) or not state['step']<=target<=200:raise ValueError('target step')
    s=json.loads(json.dumps(state,allow_nan=False))
    operators=_operators(s)
    for _ in range(s['step'],target):s=_advance(s,operators)
    return s

def _predictions(p,parameters,observations):
    s=_initial(p,*parameters);operators=_operators(s)
    maximum=max(o['step'] for o in observations)
    by_step={}
    for j,o in enumerate(observations):
        if not isinstance(o['step'],int) or not 0<=o['step']<=200 or o['species'] not in ('A','B') or not isinstance(o['index'],int) or not 0<=o['index']<s['n']:
            raise ValueError('observation indices')
        if not math.isfinite(o['value']) or not math.isfinite(o['sigma']) or o['sigma']<=0:raise ValueError('observation uncertainty')
        by_step.setdefault(o['step'],[]).append(j)
    predicted=[0.]*len(observations);jacobian=[[0.,0.] for _ in observations]
    for step in range(maximum+1):
        for j in by_step.get(step,[]):
            o=observations[j];species=o['species'];i=o['index']
            predicted[j]=s[species][i]
            jacobian[j]=[s['d'+species+'_dD'][i],s['d'+species+'_dk'][i]]
        if step<maximum:s=_advance(s,operators)
    return predicted,jacobian

def _fit(p,observations,start):
    bounds=p['bounds'];theta=list(start);damping=1e-3
    def evaluate(t):
        prediction,jac=_predictions(p,t,observations)
        residual=[(x-o['value'])/o['sigma'] for x,o in zip(prediction,observations)]
        jj=[[v/o['sigma'] for v in row] for row,o in zip(jac,observations)]
        return math.fsum(v*v for v in residual),prediction,jj,residual
    value,pred,jac,res=evaluate(theta)
    for _ in range(100):
        a=math.fsum(row[0]**2 for row in jac);b=math.fsum(row[0]*row[1] for row in jac);c=math.fsum(row[1]**2 for row in jac)
        g=math.fsum(row[0]*r for row,r in zip(jac,res));h=math.fsum(row[1]*r for row,r in zip(jac,res))
        if max(abs(g),abs(h))<1e-9:break
        aa=a+damping*max(a,1.);cc=c+damping*max(c,1.);det=aa*cc-b*b
        change=[(-cc*g+b*h)/det,(b*g-aa*h)/det]
        trial=[max(bounds[i][0],min(bounds[i][1],theta[i]+change[i])) for i in range(2)]
        new,pj,jj,rr=evaluate(trial)
        if new<value:
            movement=max(abs(trial[i]-theta[i]) for i in range(2))
            theta,value,pred,jac,res=trial,new,pj,jj,rr;damping=max(1e-12,damping/3)
            if movement<1e-11:break
        else:
            damping*=10
            if damping>1e14:break
    return theta,value,pred,jac

def _normal(state):
    state=(1664525*state+1013904223)%(2**32);u=(state+.5)/(2**32)
    state=(1664525*state+1013904223)%(2**32);v=(state+.5)/(2**32)
    return math.sqrt(-2*math.log(u))*math.cos(2*math.pi*v),state

def solve(problem):
    mode=problem['mode']
    if mode=='resume':
        final=_resume(problem['checkpoint'],problem['steps'])
        return {'final':final,'mass':final['length']/final['n']*math.fsum(final['A']+final['B'])}
    if mode=='simulate':
        s=_initial(problem,problem['D'],problem['k'])
        steps,cp_at=problem['steps'],problem['checkpoint_at']
        if not isinstance(steps,int) or not isinstance(cp_at,int) or not 0<=cp_at<=steps<=200:raise ValueError('step count')
        operators=_operators(s);checkpoint=s if cp_at==0 else None
        for step in range(1,steps+1):
            s=_advance(s,operators)
            if step==cp_at:checkpoint=s
        checkpoint=json.loads(json.dumps(checkpoint,allow_nan=False))
        resumed=_resume(checkpoint,steps)
        return {'final':s,'checkpoint':checkpoint,'restart_equal':s==resumed,
                'mass':s['length']/s['n']*math.fsum(s['A']+s['B'])}
    if mode!='infer':raise ValueError('unknown mode')
    observations=problem['observations'];bounds=problem['bounds'];start=problem['initial_guess']
    count=problem.get('bootstrap_replicates',0);seed=problem.get('bootstrap_seed',1)
    if (not observations or len(observations)<4 or len(bounds)!=2 or len(start)!=2 or
        any(len(row)!=2 for row in bounds) or
        any(not math.isfinite(z) for row in bounds for z in row) or
        any(not (0<=bounds[i][0]<bounds[i][1] and bounds[i][0]<=start[i]<=bounds[i][1]) for i in range(2)) or
        not isinstance(count,int) or count not in (0,2,3,4,5,6,7,8,9,10,11,12) or
        not isinstance(seed,int) or not 0<=seed<2**32):raise ValueError('inverse contract')
    theta,chi2,pred,jac=_fit(problem,observations,start)
    a=math.fsum(row[0]**2 for row in jac);b=math.fsum(row[0]*row[1] for row in jac);c=math.fsum(row[1]**2 for row in jac)
    det=a*c-b*b
    identifiable=a>1e-12 and c>1e-12 and det>1e-10*max(a*c,1e-30)
    covariance=[[c/det,-b/det],[-b/det,a/det]] if identifiable else None
    bootstrap=None
    if identifiable and count:
        samples=[];state=seed
        for _ in range(count):
            synthetic=[]
            for prediction,o in zip(pred,observations):
                normal,state=_normal(state)
                synthetic.append(dict(o,value=prediction+o['sigma']*normal))
            samples.append(_fit(problem,synthetic,theta)[0])
        mean=[math.fsum(t[i] for t in samples)/count for i in range(2)]
        cov=[[math.fsum((t[i]-mean[i])*(t[j]-mean[j]) for t in samples)/(count-1) for j in range(2)] for i in range(2)]
        bootstrap={'mean':mean,'covariance':cov,'rng_state':state}
    return {'parameters':theta if identifiable else None,'predicted':pred,'chi2':chi2,
            'identifiable':identifiable,'covariance':covariance,'bootstrap':bootstrap}
'''


STARTER=(SOLUTION
    .replace("zip(s['B'],a)","zip(s['B'],s['A'])")
    .replace("ad=_multiply(ia,[x+dt*y", "ad=_multiply(ia,[x-dt*y")
    .replace("operators=_operators(s)\n    for _ in range(s['step'],target)","s.update({key:[0.]*s['n'] for key in TANGENTS})\n    operators=_operators(s)\n    for _ in range(s['step'],target)")
    .replace("covariance=[[c/det,-b/det],[-b/det,a/det]] if identifiable else None","covariance=[[c/det*chi2/(len(observations)-2),-b/det*chi2/(len(observations)-2)],[-b/det*chi2/(len(observations)-2),a/det*chi2/(len(observations)-2)]] if identifiable else None")
    .replace("for _ in range(count):\n            synthetic=[]", "for _ in range(count):\n            state=seed\n            synthetic=[]"))


def _solve(p):
    ns={};exec(SOLUTION,ns);return ns['solve'](p)


def cases(seed=17):
    rng=random.Random(seed)
    def simulation(n=8):
        return dict(mode='simulate',length=1.7,dt=.06,steps=18,checkpoint_at=7,D=.035,k=.55,
                    A0=[1+.3*math.cos(2*math.pi*i/n)+.1*math.sin(4*math.pi*i/n) for i in range(n)],
                    B0=[.2+.05*math.sin(2*math.pi*i/n) for i in range(n)])
    def inverse(noisy,bootstrap=0,uniform=False):
        p=simulation();p.update(mode='infer',bounds=[[.005,.12],[.05,1.2]],initial_guess=[.04,.4],bootstrap_replicates=bootstrap,bootstrap_seed=rng.randrange(2**32))
        p.pop('D');p.pop('k');p.pop('checkpoint_at');p.pop('steps')
        if uniform:p['A0']=[1.]*8;p['B0']=[.2]*8
        observations=[dict(step=step,species=sp,index=i,value=0.,sigma=.004*(1+.3*(i%3))) for step in (2,5,10,16) for sp,i in [('A',0),('A',2),('A',5),('B',1)]]
        ns={};exec(SOLUTION,ns)
        truth=[.025+.015*rng.random(),.45+.15*rng.random()]
        values,_=ns['_predictions'](p,truth,observations)
        for o,v in zip(observations,values):o['value']=v+(o['sigma']*rng.gauss(0,1) if noisy else 0)
        p['observations']=observations
        return p
    p=simulation(5);p.update(D=0.,k=.7,dt=.12,steps=13,checkpoint_at=4)
    specs=[('pure_reaction_conservation','basic',p,10)]
    p=simulation(8);p.update(k=0.,D=.1,steps=11,checkpoint_at=0);specs.append(('periodic_diffusion_mode','basic',p,10))
    p=simulation(9);p['A0']=[.5+rng.random() for _ in range(9)];p['B0']=[.1+.2*rng.random() for _ in range(9)];specs.append(('coupled_discrete_tangents','scientific',p,10))
    specs.append(('noiseless_two_parameter_inverse','scientific',inverse(False),10))
    specs.append(('absolute_sigma_parametric_bootstrap','scientific',inverse(True,4),10))
    p=simulation(10);p.update(steps=25,checkpoint_at=10);cp=_solve(p)['checkpoint']
    specs.append(('resume_nonzero_tangent_state','stress',dict(mode='resume',checkpoint=cp,steps=25),6))
    p=simulation(11);p.update(D=.3,k=5.,dt=.2,steps=9,checkpoint_at=5);specs.append(('stiff_positive_conservative','stress',p,5))
    specs.append(('rank_deficient_uniform_initial','stress',inverse(False,4,True),5))
    p=simulation();p['A0'][0]=-.1;specs.append(('reject_negative_initial','stress',p,2))
    p=dict(mode='resume',checkpoint=dict(cp),steps=25);p['checkpoint']['dA_dD']=[0.];specs.append(('reject_incomplete_checkpoint','stress',p,2))
    out=[]
    for cid,tier,p,w in specs:
        case=dict(id=cid,tier=tier,input=p,weight=w,critical=True,rtol=3e-5,atol=2e-9)
        try:case['expected']=_solve(p)
        except ValueError:case['error']='ValueError'
        out.append(case)
    return out


def prompt(seed=17):
    rng=random.Random(seed+1010);n=9
    p=dict(mode='simulate',length=1.7,dt=.06,steps=18,checkpoint_at=7,D=.035,k=.55,
           A0=[.5+rng.random() for _ in range(n)],B0=[.1+.2*rng.random() for _ in range(n)])
    return '''# C10 修复科学流水线：周期反应扩散、离散切线、反演、自举和重启
下面提供一个可运行但含多处相互作用错误的单文件起点。请修复或重写solution.py，暴露solve(problem)->JSON字典，并交report.md、tests.py。只用Python标准库，离线、无外部数据。自动70/人工30。此题的难点是物理/离散推导与统计约定的一致性。

模型：长度L[m]的周期环，N个均匀节点（间距h=L/N，不包含重复末点）。A、B浓度[mol/m³]满足A_t=D*Lap(A)-k*A，B_t=D*Lap(B)+k*A，D[m²/s]、k[s⁻¹]≥0。周期Lap(z)_i=(z_(i-1)-2z_i+z_(i+1))/h²。必须使用**全耦合后向Euler**离散：
Ma*A_new=A_old，Ma=I-dt*D*Lap+dt*k*I；
Mb*B_new=B_old+dt*k*A_new，Mb=I-dt*D*Lap。
两物种单位横截面积的总物质量h*Σ(A+B)每步守恒（接口名mass，单位mol/m²，并非质量kg），非负初值保持非负。不可用连续时间解析解、显式Euler或不同反应时间层替代指定更新。

同时传播相对于D和k的离散切线；初始浓度与参数独立，初始切线全零。切线针对上述离散时间步求导，必须包括B对A_new的耦合。切线质量导数应为零。不能以错误物理模型的有限差分充当正确性证据。

三种API模式：
1) mode='simulate'：输入length、dt、steps、checkpoint_at、D、k、A0、B0。返回final（完整状态，下述字段）、checkpoint（checkpoint_at步的完整状态）、restart_equal（对checkpoint进行JSON往返再继续到steps，与完整运行逐字段浮点相等）、mass。完整状态字段为n,length,D,k,dt,step,A,B,dA_dD,dA_dk,dB_dD,dB_dk。所有向量长n。检查点必须保留切线，不能仅恢复物理浓度。
2) mode='resume'：输入checkpoint、steps，继续既有步号至指定总步号；返回final、mass。不能重置已有切线。
3) mode='infer'：输入length、dt、A0、B0、bounds=[[Dmin,Dmax],[kmin,kmax]]、initial_guess=[D,k]、observations。每条观测={step,species:'A'或'B',index,value,sigma}，预测是指定步和节点的浓度。使用已知绝对sigma最小化Σ((prediction-value)/sigma)²；不能再乘残差方差。返回parameters=[D,k]、predicted、chi2、identifiable、covariance、bootstrap。令J为预测对D/k的切线除以sigma，H=JᵀJ=[[a,b],[b,c]]，det=ac-b²；identifiable精确定义为a>1e-12且c>1e-12且det>1e-10*max(ac,1e-30)。满秩时covariance=H⁻¹；不满秩则parameters,covariance,bootstrap全部为null，仍返回拟合预测和chi2。测试族满秩目标在给定界内唯一内点，秩缺失族不要求给不可识别坐标一个数值答案。

参数自举：bootstrap_replicates为0或2..12；0时bootstrap=null。满秩且次数B>0时，以最优预测为中心，逐次/按观测原顺序加sigma*z，再从原最优参数重新拟合。使用独立持续流，不在重复间重设种子：uint32 state初值bootstrap_seed；每个正态消耗两次state=(1664525*state+1013904223) mod 2^32，u=(state+0.5)/2^32，v为第二次更新相同映射；z=sqrt(-2log(u))*cos(2pi*v)，不缓存另一个正态。返回bootstrap={mean:[D,k],covariance:2x2样本协方差(分母B-1),rng_state:最后state}。这里是有限次指定参数自举，不宣称精确置信覆盖。

支持3≤N≤32、0≤总步数≤200、L,dt>0、有限非负D/k与初始浓度，sigma>0；所有形状/索引正确、所有数有限；至少4条观测。非法输入raise ValueError。检查点切线可正可负。数值结果比较约rtol=3e-5、atol=2e-9；restart_equal要求本实现相同运算在JSON往返后精确一致，不要求跨不同算法逐比特一致。

report.md列出你找到的错误、每个修复的方程依据、切线更新、协方差单位/已知sigma约定，以及对随机流与重启的验证。tests.py必须有独立纯反应解析递推、周期Fourier离散放大因子、中心差分切线核验和重启/质量测试。不得只断言函数能运行。

可见示例输入（未给正确输出）：
'''+json.dumps(p,ensure_ascii=False,indent=2)+'''

待修复起点（允许整体重写，但遵守上述API与科学合同）：
```python
'''+STARTER+'''
```
basic20（纯反应/纯扩散），scientific30（离散切线、双参数反演、绝对sigma自举），stress20（非零切线重启、刚性正性、秩缺失、非法输入）。该题只使用经典公开合成模型。'''


def reference_submission(seed=17):
    return {'task_id':'C10','answer':{},'artifacts':{
        'solution.py':SOLUTION,
        'report.md':'# 修复与证据\nB的反应源必须使用当前A_new，才能与A损失逐步相消。D切线右端为旧切线+dt*Lap(new)，k对A切线右端为旧切线-dt*A_new；B的两条切线同时含当前A切线贡献。重启保留四条切线，否则后续梯度不再针对原初值问题。已知sigma时协方差为(JᵀWJ)⁻¹，不能乘χ²/自由度。自举每次生成新噪声并重新拟合，随机状态跨重复持续。后向Euler与连续指数衰减不同，应以离散放大因子测试。环上两物种总量以及两参数的总量切线均守恒；仅有守恒还不能证明空间算子正确，因此独立验证周期Fourier模。\n',
        'tests.py':'''import math,json
from solution import solve
def test_fourier_reaction_tangents_restart():
    n=8;L=1.3;D=.04;k=.6;dt=.08;steps=9
    p=dict(mode='simulate',length=L,dt=dt,steps=steps,checkpoint_at=4,D=D,k=k,A0=[1+.2*math.cos(2*math.pi*i/n) for i in range(n)],B0=[.3]*n)
    r=solve(p);lam=4*math.sin(math.pi/n)**2/(L/n)**2
    exact=[(1+dt*k)**(-steps)+.2*math.cos(2*math.pi*i/n)*(1+dt*(k+D*lam))**(-steps) for i in range(n)]
    assert max(abs(a-b) for a,b in zip(exact,r['final']['A']))<1e-11
    assert abs(r['mass']-L*1.3)<1e-11 and r['restart_equal']
    assert abs(sum(r['final']['dA_dD']+r['final']['dB_dD']))<1e-10
    eps=1e-6
    plus=solve(dict(p,D=D+eps))['final'];minus=solve(dict(p,D=D-eps))['final']
    for species in ('A','B'):
        assert max(abs((a-b)/(2*eps)-c) for a,b,c in zip(plus[species],minus[species],r['final']['d'+species+'_dD']))<2e-7
    resumed=solve(dict(mode='resume',checkpoint=json.loads(json.dumps(r['checkpoint'])),steps=steps))
    assert resumed['final']==r['final']
if __name__=='__main__':test_fourier_reaction_tangents_restart()
'''}}


def mutants(seed=17):
    variants={
        'lagged_reaction_transfer':SOLUTION.replace("zip(s['B'],a)","zip(s['B'],s['A'])"),
        'reset_checkpoint_tangents':SOLUTION.replace("operators=_operators(s)\n    for _ in range(s['step'],target)","s.update({key:[0.]*s['n'] for key in TANGENTS})\n    operators=_operators(s)\n    for _ in range(s['step'],target)"),
        'relative_sigma_covariance':SOLUTION.replace("covariance=[[c/det,-b/det],[-b/det,a/det]] if identifiable else None","covariance=[[c/det*chi2/(len(observations)-2),-b/det*chi2/(len(observations)-2)],[-b/det*chi2/(len(observations)-2),a/det*chi2/(len(observations)-2)]] if identifiable else None"),
        'reuse_bootstrap_noise':SOLUTION.replace("for _ in range(count):\n            synthetic=[]","for _ in range(count):\n            state=seed\n            synthetic=[]"),
    }
    out={'reference':reference_submission(seed)}
    for label,src in variants.items():
        sub=reference_submission(seed);sub['artifacts']['solution.py']=src;out[label]=sub
    return out

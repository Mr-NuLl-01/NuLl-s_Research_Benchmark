"""F02: cell-centred backward Euler with independently reconstructed ledgers."""
from __future__ import annotations

import copy
import json
import math
import random

from nrb_v1.grading import compare_value

TASK = {"id":"F02","title":"Fortran 隐式反应扩散与累计源汇",
        "language":"fortran","difficulty":4,"time_budget_s":2700,
        "execution_budget_s":15,"required_artifacts":["solution.f90"],
        "capabilities":["finite_volume","backward_euler","nonuniform_grid","conservation_ledger","fortran"],
        "scoring":"automatic","max_score":100,"manual_review_required":False}

FORTRAN = r'''program reaction_diffusion
use, intrinsic :: iso_fortran_env, only: real64
use, intrinsic :: ieee_arithmetic, only: ieee_is_finite
implicit none
integer :: n,m,i,j,step,ios
real(real64) :: left,right,t,f,mi,mf,lin,rout,added,removed,balance,maxres
real(real64), allocatable :: w(:),d(:),k(:),u(:),old(:),dt(:),s(:,:),g(:),flux(:)
real(real64), allocatable :: hist(:,:),diag(:),rhs(:),upper(:),res(:),scale(:)
read(*,*,iostat=ios) n,m
if(ios/=0) call fail()
if(n<2.or.n>64.or.m<0.or.m>120) call fail()
allocate(w(n),d(n),k(n),u(n),old(n),dt(m),s(n,m),g(0:n),flux(0:n))
allocate(hist(n,0:m),diag(n),rhs(n),upper(n-1),res(n),scale(n))
read(*,*,iostat=ios) w
if(ios/=0) call fail()
read(*,*,iostat=ios) d
if(ios/=0) call fail()
read(*,*,iostat=ios) k
if(ios/=0) call fail()
read(*,*,iostat=ios) u
if(ios/=0) call fail()
read(*,*,iostat=ios) left,right
if(ios/=0) call fail()
if(m>0) then
 read(*,*,iostat=ios) dt
else
 read(*,*,iostat=ios)
end if
if(ios/=0) call fail()
do step=1,m
 read(*,*,iostat=ios) s(:,step)
 if(ios/=0) call fail()
end do
if(.not.all(ieee_is_finite(w)).or..not.all(ieee_is_finite(d))) call fail()
if(.not.all(ieee_is_finite(k)).or..not.all(ieee_is_finite(u))) call fail()
if(.not.all(ieee_is_finite(dt)).or..not.all(ieee_is_finite(s))) call fail()
if(.not.all(ieee_is_finite([left,right]))) call fail()
if(any(w<1.e-4_real64).or.any(w>2)) call fail()
if(any(d<1.e-6_real64).or.any(d>10)) call fail()
if(any(k<0).or.any(k>100).or.any(u<0).or.any(u>100)) call fail()
if(any(s<0).or.any(s>100).or.left<0.or.left>100.or.right<0.or.right>100) call fail()
if(any(dt<1.e-7_real64).or.any(dt>10)) call fail()
g(0)=2*d(1)/w(1);g(n)=2*d(n)/w(n)
do i=1,n-1
 g(i)=1/(w(i)/(2*d(i))+w(i+1)/(2*d(i+1)))
end do
hist(:,0)=u
mi=sum(w*u);lin=0;rout=0;added=0;removed=0;maxres=0
call face_flux(u,flux)
do step=1,m
 old=u;t=dt(step)
 diag=w+t*(g(0:n-1)+g(1:n)+w*k)
 upper=-t*g(1:n-1)
 rhs=w*old+t*w*s(:,step)
 rhs(1)=rhs(1)+t*g(0)*left
 rhs(n)=rhs(n)+t*g(n)*right
 do j=2,n
  f=upper(j-1)/diag(j-1)
  diag(j)=diag(j)-f*upper(j-1)
  rhs(j)=rhs(j)-f*rhs(j-1)
 end do
 u(n)=rhs(n)/diag(n)
 do j=n-1,1,-1
  u(j)=(rhs(j)-upper(j)*u(j+1))/diag(j)
 end do
 if(.not.all(ieee_is_finite(u)).or.any(u<0)) call fail()
 hist(:,step)=u
 call face_flux(u,flux)
 lin=lin+t*flux(0);rout=rout+t*flux(n)
 added=added+t*sum(w*s(:,step))
 removed=removed+t*sum(w*k*u)
 res=w*(u-old)-t*(flux(0:n-1)-flux(1:n)+w*s(:,step)-w*k*u)
 scale=1+abs(w*u)+abs(w*old)+t*(abs(flux(0:n-1))+abs(flux(1:n))+w*(s(:,step)+k*u))
 maxres=max(maxres,maxval(abs(res)/scale))
end do
mf=sum(w*u)
balance=abs(mf-mi-(lin-rout+added-removed))
write(*,'(I0,1X,I0)') n,m
do step=0,m
 write(*,'(*(ES25.16E3,1X))') hist(:,step)
end do
write(*,'(*(ES25.16E3,1X))') flux
write(*,'(*(ES25.16E3,1X))') mi,mf,lin,rout,added,removed,balance,maxres
contains
subroutine face_flux(state,faces)
 real(real64),intent(in)::state(n)
 real(real64),intent(out)::faces(0:n)
 integer::q
 faces(0)=g(0)*(left-state(1))
 do q=1,n-1
  faces(q)=g(q)*(state(q)-state(q+1))
 end do
 faces(n)=g(n)*(state(n)-right)
end subroutine
subroutine fail()
 write(*,'(A)') 'ERROR'
 stop
end subroutine
end program
'''


def _validate_input(p):
    n=len(p["widths"]);m=len(p["dt"])
    if not 2<=n<=64 or not 0<=m<=120:
        raise ValueError("unsupported shape")
    if any(len(p[key])!=n for key in ("diffusion","decay","initial")) or len(p["source"])!=m or any(len(s)!=n for s in p["source"]):
        raise ValueError("invalid array lengths")
    ranges=[(p["widths"],1e-4,2),(p["diffusion"],1e-6,10),(p["decay"],0,100),
            (p["initial"],0,100),(p["dt"],1e-7,10),([p["left"],p["right"]],0,100),
            ([v for s in p["source"] for v in s],0,100)]
    for values,lo,hi in ranges:
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not lo<=v<=hi for v in values):
            raise ValueError("outside supported range")
    return n,m


def _conductances(p):
    w,d=p["widths"],p["diffusion"]
    return [2*d[0]/w[0]]+[1/(w[i]/(2*d[i])+w[i+1]/(2*d[i+1])) for i in range(len(w)-1)]+[2*d[-1]/w[-1]]


def _flux(p,u,g=None):
    g=_conductances(p) if g is None else g
    return [g[0]*(p["left"]-u[0])]+[g[i]*(u[i-1]-u[i]) for i in range(1,len(u))]+[g[-1]*(u[-1]-p["right"])]


def _diagnostics(p,history):
    w,k=p["widths"],p["decay"];g=_conductances(p)
    left=right=source=decay=maximum=0.0
    for j,dt in enumerate(p["dt"]):
        previous,u=history[j],history[j+1];flux=_flux(p,u,g)
        left+=dt*flux[0];right+=dt*flux[-1]
        source+=dt*math.fsum(w[i]*p["source"][j][i] for i in range(len(w)))
        decay+=dt*math.fsum(w[i]*k[i]*u[i] for i in range(len(w)))
        for i,wi in enumerate(w):
            residual=wi*(u[i]-previous[i])-dt*(flux[i]-flux[i+1]+wi*p["source"][j][i]-wi*k[i]*u[i])
            scale=1+abs(wi*u[i])+abs(wi*previous[i])+dt*(abs(flux[i])+abs(flux[i+1])+wi*(p["source"][j][i]+k[i]*u[i]))
            maximum=max(maximum,abs(residual)/scale)
    initial=math.fsum(wi*ui for wi,ui in zip(w,history[0]))
    final=math.fsum(wi*ui for wi,ui in zip(w,history[-1]))
    return dict(initial_mass=initial,final_mass=final,left_in=left,right_out=right,
                source_added=source,decay_removed=decay,
                balance_residual=abs(final-initial-(left-right+source-decay)),max_step_residual=maximum)


def _reference(p):
    """Independent dense linear solve; the Fortran control uses Thomas elimination."""
    import numpy as np
    n,m=_validate_input(p)
    w=np.asarray(p["widths"],dtype=float);k=np.asarray(p["decay"],dtype=float);g=np.asarray(_conductances(p))
    u=np.asarray(p["initial"],dtype=float);history=[u.tolist()]
    for j,dt in enumerate(p["dt"]):
        mat=np.diag(w+dt*(g[:-1]+g[1:]+w*k))+np.diag(-dt*g[1:-1],1)+np.diag(-dt*g[1:-1],-1)
        rhs=w*u+dt*w*np.asarray(p["source"][j])
        rhs[0]+=dt*g[0]*p["left"];rhs[-1]+=dt*g[-1]*p["right"]
        u=np.linalg.solve(mat,rhs);history.append(u.tolist())
    return dict(n=n,steps=m,history=history,flux=_flux(p,history[-1]),**_diagnostics(p,history))


def fortran_input(p):
    n,m=len(p["widths"]),len(p["dt"])
    rows=[f"{n} {m}"]
    rows += [" ".join(format(v,".17g") for v in p[key]) for key in ("widths","diffusion","decay","initial")]
    rows += [f"{p['left']:.17g} {p['right']:.17g}"," ".join(format(v,".17g") for v in p["dt"])]
    rows += [" ".join(format(v,".17g") for v in row) for row in p["source"]]
    return "\n".join(rows)+"\n"


def parse_fortran(stdout):
    if stdout.strip()=="ERROR":
        return {"error":"ValueError"}
    tokens=stdout.split()
    try:
        n,m=int(tokens[0]),int(tokens[1])
    except (ValueError,IndexError):
        raise ValueError("output must begin with integer N M") from None
    if not (2<=n<=64 and 0<=m<=120) or len(tokens)!=2+n*(m+1)+(n+1)+8:
        raise ValueError("F02 output length/header mismatch")
    values=[float(s.replace("D","E").replace("d","e")) for s in tokens[2:]]
    if not all(math.isfinite(v) for v in values):
        raise ValueError("nonfinite F02 output")
    history=[values[j*n:(j+1)*n] for j in range(m+1)]
    offset=n*(m+1)
    names=("initial_mass","final_mass","left_in","right_out","source_added","decay_removed","balance_residual","max_step_residual")
    return dict(n=n,steps=m,history=history,flux=values[offset:offset+n+1],**dict(zip(names,values[-8:])))


def validate_output(case,output):
    try:
        primary={k:v for k,v in case["expected"].items() if k not in ("balance_residual","max_step_residual")}
        ok,why=compare_value(output,primary,case.get("rtol",2e-9),case.get("atol",2e-10),
                             exact_integer_paths=frozenset({"result.n","result.steps"}))
        if not ok:
            return ok,why
        history=output["history"];p=case["input"]
        if any(v<0 for row in history for v in row):
            return False,"negative density in returned trajectory"
        metrics=_diagnostics(p,history)
        scale=max(1,metrics["initial_mass"],metrics["final_mass"],abs(metrics["left_in"])+abs(metrics["right_out"])+metrics["source_added"]+metrics["decay_removed"])
        for key,value in metrics.items():
            tolerance=(2e-9*scale if key=="balance_residual" else 2e-10 if key=="max_step_residual"
                       else 2e-10+2e-9*abs(value))
            if (not math.isfinite(value) or isinstance(output[key],bool) or not isinstance(output[key],(int,float))
                or not math.isfinite(output[key]) or abs(output[key]-value)>tolerance):
                return False,"ledger/trajectory inconsistency: "+key
        recomputed_flux=_flux(p,history[-1])
        if any(abs(a-b)>2e-10+2e-9*abs(b) for a,b in zip(output["flux"],recomputed_flux)):
            return False,"final flux does not follow the half-cell/harmonic face law"
        if metrics["max_step_residual"]>2e-10 or not 0<=output["max_step_residual"]<=2e-10:
            return False,"recomputed backward-Euler residual exceeds 2e-10"
        if metrics["balance_residual"]>2e-9*scale or not 0<=output["balance_residual"]<=2e-9*scale:
            return False,"global source/sink ledger does not close"
        return True,""
    except (KeyError,TypeError,ValueError,IndexError,OverflowError,ZeroDivisionError):
        return False,"malformed reaction-diffusion trajectory"


def _case(cid,tier,p,weight):
    case=dict(id=cid,tier=tier,input=p,weight=weight,critical=True,rtol=2e-9,atol=2e-10)
    try:
        case["expected"]=_reference(p)
    except ValueError:
        case["error"]="ValueError"
    return case


def cases(seed=17):
    rng=random.Random(seed+20202)
    def base(n=7,m=4):
        return dict(widths=[.1]*n,diffusion=[.25]*n,decay=[0.0]*n,initial=[0.0]*n,
                    left=0.0,right=0.0,dt=[.1]*m,source=[[0.0]*n for _ in range(m)])
    out=[]
    p=base(5,3);p.update(initial=[1.25]*5,left=1.25,right=1.25,decay=[.8]*5,source=[[1.0]*5 for _ in range(3)])
    out.append(_case("uniform_source_sink_equilibrium","basic",p,8))
    p=base(2,1);p.update(widths=[.2,.3],diffusion=[.6,.2],initial=[.4,.8],left=1.1,right=.1,dt=[.25])
    out.append(_case("two_cells_half_boundary","basic",p,6))
    p=base(6,0);p.update(initial=[.3,.5,1.2,.7,.9,.4],left=.1,right=1.4)
    out.append(_case("zero_step_identity","basic",p,6))
    p=base(17,9)
    p.update(widths=[.02+.1*rng.random() for _ in range(17)],diffusion=[.03+.5*rng.random() for _ in range(17)],
             decay=[.1+2*rng.random() for _ in range(17)],initial=[.3+rng.random() for _ in range(17)],
             left=.2,right=1.2,dt=[.01+.2*rng.random() for _ in range(9)],
             source=[[.2+1.5*rng.random() for _ in range(17)] for _ in range(9)])
    out.append(_case("nonuniform_heterogeneous_schedule","scientific",p,10))
    p=base(11,8);p.update(left=.1,right=.2,initial=[3.0]*11,decay=[.7]*11)
    out.append(_case("outward_flux_signed_ledger","scientific",p,10))
    p=base(9,6);p.update(dt=[.001,.002,.1,.4,.002,.08],decay=[1+i*.2 for i in range(9)],
                        source=[[float((j+2*i)%5) for i in range(9)] for j in range(6)],left=.15,right=.7)
    out.append(_case("piecewise_source_right_interval","scientific",p,10))
    p=base(23,5);p.update(diffusion=[1e-4]*23,decay=[100.0]*23,initial=[2.0]*23,dt=[1.0,2.0,.7,3.0,1.3],
                         source=[[1.0+i*.03 for i in range(23)] for _ in range(5)])
    out.append(_case("stiff_loss_positive_backward_euler","stress",p,5))
    p=base(64,120);p.update(widths=[.005+(i%5)*.001 for i in range(64)],diffusion=[.03+(i%3)*.04 for i in range(64)],
                           decay=[.2]*64,initial=[.5]*64,left=.3,right=.8,dt=[.003]*120,
                           source=[[.1 if j<60 else .4 for _ in range(64)] for j in range(120)])
    out.append(_case("maximum_grid_cumulative_ledger","stress",p,5))
    p=base(7,3);p.update(dt=[1e-7,1e-6,.1],left=1.0,right=.2,initial=[.9]*7)
    out.append(_case("tiny_step_then_large_step","stress",p,4))
    p=base();p["widths"][2]=0.0
    out.append(_case("reject_zero_cell_width","stress",p,2))
    p=base();p["dt"][1]=-0.1
    out.append(_case("reject_negative_time_step","stress",p,2))
    p=base();p["source"][1][2]=-0.01
    out.append(_case("reject_negative_source","stress",p,2))
    return out


def prompt(seed=17):
    p=copy.deepcopy(next(c["input"] for c in cases(seed) if c["id"]=="two_cells_half_boundary"))
    return '''# F02 · Fortran 隐式反应扩散与累计源汇

提交一个标准Fortran 2008程序 `solution.f90`，完成指定有限体积时间推进和完整收支账本。只有源码是必交项，没有人工分。数据为原创合成数据。

## 空间模型

一维N个相邻控制体，单元宽w_i[m]，扩散系数D_i[m²/s]在单元内常数，一级衰减k_i[s⁻¹]≥0，单元平均密度u_i[m⁻³]。两个外端固定Dirichlet密度uL、uR≥0。取正x方向的粒子通量：

```
g_0 = 2D_1/w_1
g_i = 1 / (w_i/(2D_i)+w_(i+1)/(2D_(i+1)))    i=1…N-1
g_N = 2D_N/w_N
J_0 = g_0*(uL-u_1)
J_i = g_i*(u_i-u_(i+1))                     i=1…N-1
J_N = g_N*(u_N-uR)
```

边界到单元中心是半个单元，异质界面使用上述串联热阻形式的扩散导通系数；不能取算术平均D或把边界距离当整宽。

## 时间推进：后向Euler

提供M个正时间步dt_j和M行源s_(j,i)[m⁻³s⁻¹]≥0。第j行源在第j个时间区间恒定，使用新状态通量及新状态衰减：

```
w_i*(u_i^j-u_i^(j-1)) = dt_j * [J_(i-1)^j-J_i^j+w_i*s_(j,i)-w_i*k_i*u_i^j]
```

必须求解这个离散问题，不用显式Euler、Crank–Nicolson、连续解析解或自适应子步替代它。无需自适应时间控制。非负输入应得到非负状态，不允许通过事后截断掩盖错误。

## 账本

所有积分量按单位横截面积计，单位m⁻²。`initial_mass=sum(w*u^0)`，`final_mass=sum(w*u^M)`。这里mass是粒子数面密度，不是kg。

```
left_in       = sum_j dt_j*J_0^j
right_out     = sum_j dt_j*J_N^j
source_added  = sum_j dt_j*sum_i w_i*s_(j,i)
decay_removed = sum_j dt_j*sum_i w_i*k_i*u_i^j
balance_residual = abs(final_mass-initial_mass-(left_in-right_out+source_added-decay_removed))
```

left_in和right_out是有符号量，不能取绝对值。M=0时状态不变、四个累计量为0，但仍输出初始状态对应的边通量。

对每步每单元，令r为上面时间离散方程的左端减右端，尺度
`q=1+abs(w_i*u_i^j)+abs(w_i*u_i^(j-1))+dt_j*(abs(J_(i-1)^j)+abs(J_i^j)+w_i*(s_(j,i)+k_i*u_i^j))`。
输出`max_step_residual=max(abs(r)/q)`；M=0取0。该量只检查指定离散方程，不是连续方程的时间离散误差。

## 输入与范围

stdin：第1行`N M`；接下来4行分别为`widths[N]`、`diffusion[N]`、`decay[N]`、`initial[N]`；第6行`left right`；第7行`dt[M]`（M=0也保留空行）；随后M行`source[j][N]`。

2≤N≤64，0≤M≤120；数组按指定长度提供，数值有限；w∈[1e-4,2]，D∈[1e-6,10]，k、u^0、两端密度、所有源∈[0,100]，dt∈[1e-7,10]。范围外或读取失败只输出单独ERROR并正常退出；不需要支持范围外极端数值。

成功输出：

1. 第一行整数`N M`。
2. 接下来M+1行，每行N个值，依次为初始u^0和每步u^1…u^M。
3. 一行N+1个最终通量`J_0…J_N`。
4. 最后一行8个值，顺序为`initial_mass final_mass left_in right_out source_added decay_removed balance_residual max_step_residual`。

使用real64、至少16位有效数字；无额外提示文字、第三方库、文件或网络。编译选项`gfortran -std=f2008 -O2 -fcheck=all -ffree-line-length-none`。每例上限30秒，整次含编译默认120秒；用户指定更短预算优先。

## 自动评分

每个轨迹点、通量与质量/源汇累计量采用`|actual-expected|≤2e-10+2e-9*|expected|`；N和M精确。评分器用独立稠密线性求解器作为参考，并从候选全轨迹重算所有源汇和每步残差；不能用自报账本替代重算。max_step_residual的上限为2e-10；balance_residual的上限为2e-9×max(1,initial_mass,final_mass,abs(left_in)+abs(right_out)+source_added+decay_removed)。两个残差诊断均须非负、自报和重算值均不超过各自上限，二者差也不超过该上限；不要求不同合法浮点求解器报告逐位相同的舍入残差。密度必须非负。

基础/科学/边界相对权重20/30/20，分数为通过权重/70×100；全部通过才标passed。编译或运行失败计失败，环境缺失为unscored。候选只接收本题，不访问参考解和验证器。

## 可见输入

下列JSON仅描述stdin映射，不要求解析JSON，不含正确输出。

```json
'''+json.dumps(p,ensure_ascii=False,indent=2)+'''
```

设计难度4/5，尚未用真实模型成绩标定。有限体积和隐式时间推进背景可参考NIST FiPy公开文档 https://pages.nist.gov/fipy/en/latest/numerical/discret.html 。具体符号、输入域和账本以本题为准。
'''


def reference_submission(seed=17):
    return {"task_id":"F02","answer":{},"artifacts":{"solution.f90":FORTRAN}}


def mutants(seed=17):
    variants={
        "full_cell_boundary_distance":FORTRAN.replace("g(0)=2*d(1)/w(1);g(n)=2*d(n)/w(n)","g(0)=d(1)/w(1);g(n)=d(n)/w(n)"),
        "arithmetic_interface_diffusion":FORTRAN.replace("g(i)=1/(w(i)/(2*d(i))+w(i+1)/(2*d(i+1)))","g(i)=(d(i)+d(i+1))/(w(i)+w(i+1))"),
        "old_state_decay_ledger":FORTRAN.replace("removed=removed+t*sum(w*k*u)","removed=removed+t*sum(w*k*old)"),
        "unsigned_left_flux_ledger":FORTRAN.replace("lin=lin+t*flux(0)","lin=lin+t*abs(flux(0))"),
        "half_time_step":FORTRAN.replace("old=u;t=dt(step)","old=u;t=dt(step)/2"),
    }
    return {"reference":reference_submission(seed),**{
        name:{"task_id":"F02","answer":{},"artifacts":{"solution.f90":src}} for name,src in variants.items()}}

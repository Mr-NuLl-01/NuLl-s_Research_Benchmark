"""C09: finite, specified, one-carrier nonlinear DD–Poisson BVP."""
from __future__ import annotations

import json
import math
import random

TASK={
    'id':'C09','title':'Fortran 自洽单载流子漂移扩散–Poisson 非线性边值系统',
    'language':'fortran','difficulty':5,
    'capabilities':['nonlinear_pde','coupled_poisson_transport','newton_globalization','fortran','gauge_invariance'],
    'time_budget_s':3600, "execution_budget_s": 15,'required_artifacts':['main.f90','report.md','tests.py'],
    'essential':[
        {'id':'self_consistency','requirement':'同时求解给定离散Poisson与SG连续性方程，而非冻结电势'},
        {'id':'positivity','requirement':'正密度和阻尼非线性收敛，不能裁剪输出掩盖残差'},
        {'id':'verification','requirement':'平衡零流、带流制造解、规范平移和网格检验'},
    ],
}


FORTRAN=r'''program coupled
use, intrinsic :: iso_fortran_env, only: real64
use, intrinsic :: ieee_arithmetic, only: ieee_is_finite
implicit none
integer :: n,m,i,j,it,ls,ios,q
real(real64) :: lam2,pl,pr,nl,nr,h,alpha,norm0,norm1
logical :: accepted,ok
real(real64),allocatable :: diffusion(:),charge(:),source(:),z(:),zt(:),r(:),rt(:),jac(:,:),jt(:,:),delta(:)
real(real64),allocatable :: phi(:),density(:),flux(:)
read(*,*,iostat=ios) n,lam2
if(ios/=0) call fail()
if(n<4.or.n>65.or..not.ieee_is_finite(lam2)) call fail()
if(lam2<=0) call fail()
m=2*(n-2);h=1._real64/(n-1)
allocate(diffusion(n-1),charge(n-2),source(n-2),z(m),zt(m),r(m),rt(m),jac(m,m),jt(m,m),delta(m))
allocate(phi(n),density(n),flux(n-1))
read(*,*,iostat=ios) pl,pr,nl,nr
if(ios/=0) call fail()
if(.not.all(ieee_is_finite([pl,pr,nl,nr])).or.nl<=0.or.nr<=0) call fail()
read(*,*,iostat=ios) diffusion
if(ios/=0) call fail()
read(*,*,iostat=ios) charge
if(ios/=0) call fail()
read(*,*,iostat=ios) source
if(ios/=0) call fail()
if(.not.all(ieee_is_finite(diffusion)).or.any(diffusion<=0)) call fail()
if(.not.all(ieee_is_finite(charge)).or..not.all(ieee_is_finite(source))) call fail()
do i=2,n-1
 q=2*(i-2)+1
 z(q)=pl+(pr-pl)*(i-1)/(n-1)
 z(q+1)=log(nl)+(log(nr)-log(nl))*(i-1)/(n-1)
end do
call evaluate(z,r,jac)
do it=1,100
 norm0=maxval(abs(r))
 if(norm0<2.e-10_real64) exit
 call linear(jac,-r,delta,ok)
 if(.not.ok) call fail()
 alpha=1;accepted=.false.
 do ls=1,35
  zt=z+alpha*delta
  if(maxval(abs(zt(1:m:2)))<50.and.maxval(abs(zt(2:m:2)))<20) then
   call evaluate(zt,rt,jt)
   norm1=maxval(abs(rt))
   if(norm1<norm0*(1-1.e-4_real64*alpha).or.norm1<2.e-10_real64) then
    accepted=.true.;exit
   end if
  end if
  alpha=alpha/2
 end do
 if(.not.accepted) call fail()
 z=zt;r=rt;jac=jt
end do
call evaluate(z,r,jac)
if(maxval(abs(r))>5.e-9_real64) call fail()
call state(z,phi,density,flux)
write(*,'(*(ES25.16E3,1X))') phi
write(*,'(*(ES25.16E3,1X))') density
write(*,'(*(ES25.16E3,1X))') flux
write(*,'(*(ES25.16E3,1X))') maxval(abs(r))
contains
function bern(t) result(v)
 real(real64),intent(in)::t
 real(real64)::v,e
 if(abs(t)<1.e-4_real64) then
  v=1-t/2+t*t/12-t**4/720+t**6/30240
 else if(t>50) then
  e=exp(-t);v=t*e/(1-e)
 else
  v=t/(exp(t)-1)
 end if
end function
function dbern(t) result(v)
 real(real64),intent(in)::t
 real(real64)::v,e
 if(abs(t)<1.e-3_real64) then
  v=-.5_real64+t/6-t**3/180+t**5/5040-t**7/151200
 else if(t>50) then
  e=exp(-t);v=e*(1-t-e)/(1-e)**2
 else if(t< -50) then
  e=exp(t);v=(-1+e-t*e)/(1-e)**2
 else
  e=exp(t);v=(e-1-t*e)/(e-1)**2
 end if
end function
subroutine state(zz,p,den,f)
 real(real64),intent(in)::zz(m)
 real(real64),intent(out)::p(n),den(n),f(n-1)
 real(real64)::dz
 integer::ii,qq
 p(1)=pl;p(n)=pr;den(1)=nl;den(n)=nr
 do ii=2,n-1
  qq=2*(ii-2)+1;p(ii)=zz(qq);den(ii)=exp(zz(qq+1))
 end do
 do ii=1,n-1
  dz=p(ii+1)-p(ii)
  f(ii)=diffusion(ii)/h*(bern(-dz)*den(ii)-bern(dz)*den(ii+1))
 end do
end subroutine
subroutine evaluate(zz,res,aj)
 real(real64),intent(in)::zz(m)
 real(real64),intent(out)::res(m),aj(m,m)
 real(real64)::p(n),den(n),f(n-1),a,dz,dr,dl,du,sgn
 integer::ii,rr,edge,side,ll,cc
 call state(zz,p,den,f)
 res=0;aj=0
 a=lam2/(h*h)
 do ii=2,n-1
  rr=2*(ii-2)+1
  res(rr)=a*(2*p(ii)-p(ii-1)-p(ii+1))+den(ii)-charge(ii-1)
  aj(rr,rr)=2*a;aj(rr,rr+1)=den(ii)
  if(ii>2) aj(rr,rr-2)=-a
  if(ii<n-1) aj(rr,rr+2)=-a
  res(rr+1)=(f(ii)-f(ii-1))/h-source(ii-1)
  do side=0,1
   edge=ii-1+side;sgn=real(2*side-1,real64)/h
   dz=p(edge+1)-p(edge)
   dr=diffusion(edge)/h*(-dbern(-dz)*den(edge)-dbern(dz)*den(edge+1))
   dl=diffusion(edge)/h*bern(-dz)*den(edge)
   du=-diffusion(edge)/h*bern(dz)*den(edge+1)
   ll=edge
   if(ll>=2.and.ll<=n-1) then
    cc=2*(ll-2)+1
    aj(rr+1,cc)=aj(rr+1,cc)-sgn*dr
    aj(rr+1,cc+1)=aj(rr+1,cc+1)+sgn*dl
   end if
   ll=edge+1
   if(ll>=2.and.ll<=n-1) then
    cc=2*(ll-2)+1
    aj(rr+1,cc)=aj(rr+1,cc)+sgn*dr
    aj(rr+1,cc+1)=aj(rr+1,cc+1)+sgn*du
   end if
  end do
 end do
end subroutine
subroutine linear(ain,bin,solution,success)
 real(real64),intent(in)::ain(m,m),bin(m)
 real(real64),intent(out)::solution(m)
 logical,intent(out)::success
 real(real64)::mat(m,m),bb(m),temp(m),pivot,factor,tmp
 integer::kk,ii,pp
 mat=ain;bb=bin;success=.false.
 do kk=1,m
  pp=kk+maxloc(abs(mat(kk:m,kk)),dim=1)-1
  pivot=mat(pp,kk)
  if(abs(pivot)<1.e-16_real64) return
  if(pp/=kk) then
   temp=mat(kk,:);mat(kk,:)=mat(pp,:);mat(pp,:)=temp
   tmp=bb(kk);bb(kk)=bb(pp);bb(pp)=tmp
  end if
  do ii=kk+1,m
   factor=mat(ii,kk)/mat(kk,kk)
   mat(ii,kk:m)=mat(ii,kk:m)-factor*mat(kk,kk:m)
   bb(ii)=bb(ii)-factor*bb(kk)
  end do
 end do
 do ii=m,1,-1
  solution(ii)=(bb(ii)-sum(mat(ii,ii+1:m)*solution(ii+1:m)))/mat(ii,ii)
 end do
 success=all(ieee_is_finite(solution))
end subroutine
subroutine fail()
 write(*,'(A)') 'ERROR'
 stop
end subroutine
end program
'''


def _bern(z):
    return 1-z/2+z*z/12-z**4/720+z**6/30240 if abs(z)<1e-4 else z/math.expm1(z)


def _flux(phi,density,d):
    h=1/(len(phi)-1)
    return [d[i]/h*(_bern(phi[i]-phi[i+1])*density[i]-_bern(phi[i+1]-phi[i])*density[i+1]) for i in range(len(d))]


def _manufactured(phi,density,d,lam2):
    n=len(phi);h=1/(n-1);flux=_flux(phi,density,d)
    charge=[lam2*(2*phi[i]-phi[i-1]-phi[i+1])/h**2+density[i] for i in range(1,n-1)]
    source=[(flux[i]-flux[i-1])/h for i in range(1,n-1)]
    p=dict(n=n,lambda_squared=lam2,potential_left=phi[0],potential_right=phi[-1],density_left=density[0],density_right=density[-1],diffusion=d,charge=charge,source=source)
    expected=dict(potential=phi,density=density,flux=flux,residual_inf=0.)
    return p,expected


def fortran_input(p):
    return '\n'.join([f"{p['n']} {p['lambda_squared']:.17g}",
        ' '.join(format(p[k],'.17g') for k in ('potential_left','potential_right','density_left','density_right'))]+
        [' '.join(format(v,'.17g') for v in p[k]) for k in ('diffusion','charge','source')])+'\n'


def parse_fortran(stdout):
    if stdout.strip()=='ERROR':return {'error':'ValueError'}
    v=[float(z.replace('D','E')) for z in stdout.split()]
    if len(v)<12 or len(v)%3 or not all(math.isfinite(z) for z in v):raise ValueError('malformed C09 output')
    n=len(v)//3
    return dict(potential=v[:n],density=v[n:2*n],flux=v[2*n:-1],residual_inf=v[-1])


def validate_output(case,output):
    """Accept an actual positive root, without claiming global nonlinear uniqueness."""
    try:
        p=case['input'];n=p['n'];h=1/(n-1)
        phi=output['potential'];density=output['density'];reported_flux=output['flux'];reported=output['residual_inf']
        if not (isinstance(phi,list) and isinstance(density,list) and isinstance(reported_flux,list) and len(phi)==len(density)==n and len(reported_flux)==n-1):
            return False,'nonlinear solution shape mismatch'
        values=phi+density+reported_flux+[reported]
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in values):
            return False,'nonfinite nonlinear solution'
        if min(density)<=0:return False,'density must be strictly positive'
        if any(abs(a-b)>8e-8+3e-7*abs(b) for a,b in zip([phi[0],phi[-1],density[0],density[-1]],[p['potential_left'],p['potential_right'],p['density_left'],p['density_right']])):
            return False,'Dirichlet contact mismatch'
        flux=_flux(phi,density,p['diffusion'])
        if not all(math.isfinite(v) for v in flux):return False,'nonfinite recomputed flux'
        if any(abs(a-b)>8e-8+3e-7*abs(b) for a,b in zip(reported_flux,flux)):
            return False,'reported flux is inconsistent with the specified SG law'
        residual=max([abs(p['lambda_squared']*(2*phi[i]-phi[i-1]-phi[i+1])/h**2+density[i]-p['charge'][i-1]) for i in range(1,n-1)]+
                     [abs((flux[i]-flux[i-1])/h-p['source'][i-1]) for i in range(1,n-1)])
        if not math.isfinite(residual) or residual>8e-8:return False,'original coupled residual exceeds 8e-8'
        if reported<0 or reported>8e-8 or abs(reported-residual)>8e-8:
            return False,'reported residual is inconsistent with the original equations'
        return True,''
    except (KeyError,TypeError,ValueError,OverflowError,ZeroDivisionError):
        return False,'invalid nonlinear solution object'


def cases(seed=17):
    rng=random.Random(seed)
    out=[]
    def add(cid,tier,pair,w):
        p,e=pair;out.append(dict(id=cid,tier=tier,input=p,expected=e,weight=w,critical=True,rtol=3e-7,atol=8e-8))
    n=9;add('neutral_equilibrium','basic',_manufactured([0.]*n,[1.]*n,[1.]*(n-1),.2),10)
    n=13;v=.35+.4*rng.random();d=.6+.6*rng.random();left=.6+.4*rng.random();right=.3+.3*rng.random()
    phi=[v*i/(n-1) for i in range(n)]
    density=[left+(right-left)*math.expm1(v*i/(n-1))/math.expm1(v) for i in range(n)]
    add('affine_potential_nonzero_current','basic',_manufactured(phi,density,[d]*(n-1),.15),10)
    n=17;amp=.18+.18*rng.random();offset=-.16+.1*rng.random();scale=.9+.2*rng.random()
    phi=[amp*math.sin(math.pi*i/(n-1))+offset for i in range(n)];density=[scale*math.exp(v) for v in phi]
    add('boltzmann_zero_flux','scientific',_manufactured(phi,density,[.7+.2*rng.random() for _ in range(n-1)],.3),10)
    def curved(n,lam2,shift=0.):
        amp=.12+.06*rng.random();x=[i/(n-1) for i in range(n)]
        pl=-.3+.2*rng.random();pr=.1+.2*rng.random()
        mean=.9+.2*rng.random();cosine=.1+.12*rng.random();sine=.03+.05*rng.random();mode=rng.choice((2,3,4))
        phi=[shift+pl+(pr-pl)*t+amp*math.sin(2*math.pi*t) for t in x]
        den=[mean+cosine*math.cos(math.pi*t)+sine*math.sin(mode*math.pi*t) for t in x]
        d=[.6+.7*rng.random() for _ in range(n-1)]
        return _manufactured(phi,den,d,lam2)
    pair=curved(21,.1);add('coupled_manufactured_sources','scientific',pair,10)
    p,e=pair
    shifted=dict(p);shifted['potential_left']+=4.;shifted['potential_right']+=4.
    es=dict(e);es['potential']=[z+4 for z in e['potential']]
    add('potential_gauge_shift','scientific',(shifted,es),10)
    add('screening_refined','stress',curved(41,.035),8)
    n=25;field=1e-10+1e-9*rng.random();mean=.9+.2*rng.random();slope=.1+.2*rng.random()
    phi=[field*i/(n-1) for i in range(n)];den=[mean+slope*i/(n-1) for i in range(n)]
    add('small_field_cancellation','stress',_manufactured(phi,den,[1.]*(n-1),.6),6)
    for cid,key,value in [('reject_negative_screening','lambda_squared',-.1),('reject_zero_contact_density','density_right',0.)]:
        p=dict(pair[0]);p[key]=value
        out.append(dict(id=cid,tier='stress',input=p,error='ValueError',weight=3,critical=True,rtol=3e-7,atol=8e-8))
    return out


def prompt(seed=17):
    rng=random.Random(seed+9009);n=11;x=[i/(n-1) for i in range(n)]
    p,_=_manufactured([-.2+.4*t+.12*math.sin(2*math.pi*t) for t in x],
                      [1+.15*math.cos(math.pi*t) for t in x],[.7+.4*rng.random() for _ in range(n-1)],.12)
    return '''# C09 自洽非线性漂移扩散–Poisson（Fortran 2008）
这是一个明确有限的公开经典合成数学模型，不要求真实半导体器件模拟器。提交main.f90、report.md、tests.py；只用标准Fortran，双精度，自动70/人工30。

所有量已无量纲化：x∈[0,1]，势ψ以热电压为单位，密度n以参考浓度为单位，D以参考扩散系数为单位，lambda_squared为归一化屏蔽长度的平方。均匀N节点，h=1/(N-1)。边通量
J_i=(D_i/h)[B(-(ψ_(i+1)-ψ_i))*n_i-B(ψ_(i+1)-ψ_i)*n_(i+1)]，B(z)=z/(exp(z)-1)，B(0)=1。
两个内部离散残差必须同时为零：
Rψ_i=lambda_squared*(2ψ_i-ψ_(i-1)-ψ_(i+1))/h²+n_i-charge_i；
Rn_i=(J_i-J_(i-1))/h-source_i。
charge是固定背景项，可以有符号；source是规定的净产生项，也可以有符号。仅一个载流子、稳态、常温、无复合和隧穿；不引入额外物理。ψ与n在左右端分别给定Dirichlet值，n>0。

合法输入N∈[4,65]，lambda_squared>0，D_i>0，边界n>0，其他数有限。测试的合法族为平衡或光滑离散制造解；保证存在内部|ψ|≤6、0.2≤n≤3的正解，lambda_squared≥0.035、0.5≤D≤1.5。这里不声称一般非线性系统全局唯一；满足指定边界、严格正密度和原始残差的任一解均可接受。不要求支持分岔、极端注入或无正解数据。非法形状/非正系数输出ERROR；迭代确实失败也必须输出ERROR，不能输出未经收敛的结果。建议使用log(n)变量、解析/一致数值Jacobian、阻尼或连续化；不能逐点裁剪密度后声称收敛。

stdin：第1行N lambda_squared；第2行potential_left potential_right density_left density_right；第3行diffusion[N-1]；第4行charge[N-2]；第5行source[N-2]。每行数值，无JSON。输出只含数值：第1行potential[N]；第2行density[N]；第3行flux[N-1]；第4行residual_inf（以上两组原始残差的最大绝对值）。非法输入仅输出ERROR。评估独立重算原始两组残差，要求最大值≤8e-8，并核对边界、严格正性及输出流与SG定义的一致性；不只比较自报收敛指标。

report.md完整列出残差与边界消元，说明密度正性、迭代停止与失败条件；独立核对n=A*exp(ψ)时零流、非零流制造解以及ψ→ψ+C而n/charge/source不变时的规范平移。明确两个Dirichlet势已固定规范；不能额外强行设ψ_left=0。tests.py应实际编译/运行Fortran并做独立物理/数学关系检验。可用gfortran -std=f2008 -O2 -fcheck=all -ffree-line-length-none。
可见示例输入（不含正确解）：
'''+json.dumps(p,ensure_ascii=False,indent=2)+'''
分层basic20、scientific30、stress20；种子改变背景、源和材料。方法背景：Scharfetter & Gummel, DOI 10.1109/T-ED.1969.16566；NIST Sesame公开离散化文档。这里的势号、载流子号和离散残差完全按本题定义，不可套用不同电子电流约定。'''


def reference_submission(seed=17):
    return {'task_id':'C09','answer':{},'artifacts':{
        'main.f90':FORTRAN,
        'report.md':'# 残差与验证\n联立求ψ和u=log(n)，泊松行对ψ为三对角lambda_squared/h²，对u的局部导数为exp(u)。连续性行由相邻两个SG通量及B的解析导数组装。每步用带部分选主元的稠密解求Newton方向，并对原始残差无穷范数回溯；迭代停止阈值2e-10，最终残差大于5e-9或线搜索/线性求解失败输出ERROR。对数变量不对输出裁剪。n=A exp(ψ)使两项因B(-z)=exp(z)B(z)精确抵消；电势整体加常数保留每条边增量，边界同时平移则密度和流不变。两个边界已固定规范。制造解源由独立给定的节点ψ、n计算，不以收敛日志代替方程检验。这里没有一般全局唯一性证明；自动评分独立检查任一正解是否满足原始方程与边界。模型仅涵盖题设稳态一载流子有限离散问题。\n',
        'tests.py':'''import pathlib,subprocess,tempfile,math
def test_equilibrium_and_gauge_compiled():
    source=pathlib.Path(__file__).with_name('main.f90')
    with tempfile.TemporaryDirectory() as td:
        exe=str(pathlib.Path(td)/'solver')
        subprocess.run(['gfortran','-std=f2008','-O2','-fcheck=all','-ffree-line-length-none',str(source),'-o',exe],check=True)
        n=11;h=1/(n-1);lam2=.2
        potential=[-.1+.25*math.sin(math.pi*i*h) for i in range(n)]
        density=[math.exp(x) for x in potential]
        charge=[-lam2*(potential[i+1]-2*potential[i]+potential[i-1])/h**2+density[i] for i in range(1,n-1)]
        answers=[]
        for shift in (0.,3.):
            rows=[str(n)+' '+str(lam2),' '.join(map(str,[potential[0]+shift,potential[-1]+shift,density[0],density[-1]])),' '.join(['1']*(n-1)),' '.join(map(str,charge)),' '.join(['0']*(n-2))]
            v=[float(x) for x in subprocess.check_output([exe],input=chr(10).join(rows)+chr(10),text=True).split()]
            assert len(v)==3*n
            assert max(abs(a-b-shift) for a,b in zip(v[:n],potential))<1e-8
            assert max(abs(a-b) for a,b in zip(v[n:2*n],density))<1e-8
            assert max(abs(z) for z in v[2*n:-1])<1e-8
            assert v[-1]<1e-8
            answers.append(v)
        assert max(abs(a-b) for a,b in zip(answers[0][n:2*n],answers[1][n:2*n]))<1e-8
if __name__=='__main__':test_equilibrium_and_gauge_compiled()
'''}}


def mutants(seed=17):
    variants={
        'wrong_poisson_mesh_scale':FORTRAN.replace('a=lam2/(h*h)','a=lam2/h'),
        'remove_gauge_boundary':FORTRAN.replace('p(1)=pl;p(n)=pr;den(1)=nl;den(n)=nr','p(1)=0;p(n)=pr-pl;den(1)=nl;den(n)=nr'),
        'drift_sign_reversal':FORTRAN.replace('dz=p(ii+1)-p(ii)','dz=p(ii)-p(ii+1)').replace('dz=p(edge+1)-p(edge)','dz=p(edge)-p(edge+1)').replace('dr=diffusion(edge)/h*(-dbern(-dz)*den(edge)-dbern(dz)*den(edge+1))','dr=-diffusion(edge)/h*(-dbern(-dz)*den(edge)-dbern(dz)*den(edge+1))'),
    }
    out={'reference':reference_submission(seed)}
    for label,src in variants.items():
        sub=reference_submission(seed);sub['artifacts']['main.f90']=src;out[label]=sub
    return out

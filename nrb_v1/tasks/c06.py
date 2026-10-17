"""C06: conservative exponential-fitting transport (public synthetic data)."""
from __future__ import annotations

import json
import math
import random

TASK = {
    "id": "C06", "title": "Fortran 非均匀网格守恒漂移扩散边值问题",
    "language": "fortran", "difficulty": 3,
    "capabilities": ["scharfetter_gummel", "finite_volume", "fortran", "numerical_stability"],
    "time_budget_s": 1800, "execution_budget_s": 8,
    "required_artifacts": ["main.f90", "report.md", "tests.py"],
    "essential": [
        {"id": "conservation", "requirement": "逐控制体满足带源和衰减的离散守恒"},
        {"id": "limits", "requirement": "零漂移、反向漂移和大网格 Peclet 数均稳定"},
        {"id": "boundaries", "requirement": "保留非均匀控制体宽度与两个 Dirichlet 边界"},
    ],
}


def _bernoulli(z):
    if abs(z) < 1e-4:
        return 1-z/2+z*z/12-z**4/720+z**6/30240
    if z > 50:
        return z*math.exp(-z)/(1-math.exp(-z))
    return z/math.expm1(z)


def _reference(p):
    x, d, v, src, decay = (p[k] for k in ("x", "diffusion", "velocity", "source", "decay"))
    n = len(x)
    if (not 3 <= n <= 129 or len(d) != n-1 or len(v) != n-1 or
            len(src) != n-2 or len(decay) != n-2 or
            any(not math.isfinite(z) for a in (x,d,v,src,decay,[p['left'],p['right']]) for z in a) or
            any(x[i+1] <= x[i] for i in range(n-1)) or min(d) <= 0 or
            min(src) < 0 or min(decay) < 0 or min(p['left'],p['right']) < 0):
        raise ValueError("invalid transport problem")
    h = [x[i+1]-x[i] for i in range(n-1)]
    if any(not math.isfinite(v[i]*h[i]/d[i]) or abs(v[i]*h[i]/d[i])>2500 for i in range(n-1)):
        raise ValueError('unsupported Peclet number')
    aa = [d[i]/h[i]*_bernoulli(-v[i]*h[i]/d[i]) for i in range(n-1)]
    bb = [d[i]/h[i]*_bernoulli(v[i]*h[i]/d[i]) for i in range(n-1)]
    w = [(h[i]+h[i+1])/2 for i in range(n-2)]
    diag = [bb[i]+aa[i+1]+decay[i]*w[i] for i in range(n-2)]
    rhs = [src[i]*w[i] for i in range(n-2)]
    rhs[0] += aa[0]*p['left']
    rhs[-1] += bb[-1]*p['right']
    for j in range(1,n-2):
        f = -aa[j]/diag[j-1]
        diag[j] -= f*(-bb[j])
        rhs[j] -= f*rhs[j-1]
    interior = [0.0]*(n-2)
    interior[-1] = rhs[-1]/diag[-1]
    for j in range(n-4,-1,-1):
        interior[j] = (rhs[j]+bb[j+1]*interior[j+1])/diag[j]
    u = [p['left']]+interior+[p['right']]
    flux = [aa[i]*u[i]-bb[i]*u[i+1] for i in range(n-1)]
    residual = max(abs((flux[j+1]-flux[j])/w[j]+decay[j]*u[j+1]-src[j]) for j in range(n-2))
    mass = sum(h[i]*(u[i]+u[i+1])/2 for i in range(n-1))
    return dict(density=u,flux=flux,mass=mass,residual_inf=residual)


FORTRAN = r'''program transport
use, intrinsic :: iso_fortran_env, only: real64
use, intrinsic :: ieee_arithmetic, only: ieee_is_finite
implicit none
integer :: n, i, j, ios
real(real64), allocatable :: x(:),d(:),v(:),s(:),k(:),h(:),w(:),a(:),b(:),diag(:),rhs(:),u(:),flux(:)
real(real64) :: left,right,f,z,mass,residual
read(*,*,iostat=ios) n
if(ios/=0) call fail()
if(n<3.or.n>129) call fail()
allocate(x(n),d(n-1),v(n-1),s(n-2),k(n-2),h(n-1),w(n-2),a(n-1),b(n-1),diag(n-2),rhs(n-2),u(n),flux(n-1))
read(*,*,iostat=ios) x
if(ios/=0) call fail()
read(*,*,iostat=ios) d
if(ios/=0) call fail()
read(*,*,iostat=ios) v
if(ios/=0) call fail()
read(*,*,iostat=ios) s
if(ios/=0) call fail()
read(*,*,iostat=ios) k
if(ios/=0) call fail()
read(*,*,iostat=ios) left,right
if(ios/=0) call fail()
if(.not.all(ieee_is_finite(x)).or..not.all(ieee_is_finite(d)).or..not.all(ieee_is_finite(v))) call fail()
if(.not.all(ieee_is_finite(s)).or..not.all(ieee_is_finite(k))) call fail()
if(.not.ieee_is_finite(left).or..not.ieee_is_finite(right)) call fail()
if(any(d<=0).or.any(s<0).or.any(k<0).or.left<0.or.right<0) call fail()
h=x(2:n)-x(1:n-1)
if(any(h<=0)) call fail()
do i=1,n-1
 z=v(i)*h(i)/d(i)
 if(.not.ieee_is_finite(z).or.abs(z)>2500) call fail()
 a(i)=d(i)/h(i)*bern(-z)
 b(i)=d(i)/h(i)*bern(z)
end do
w=(h(1:n-2)+h(2:n-1))/2
diag=b(1:n-2)+a(2:n-1)+k*w
rhs=s*w
rhs(1)=rhs(1)+a(1)*left
rhs(n-2)=rhs(n-2)+b(n-1)*right
do j=2,n-2
 f=-a(j)/diag(j-1)
 diag(j)=diag(j)-f*(-b(j))
 rhs(j)=rhs(j)-f*rhs(j-1)
end do
u(1)=left
u(n)=right
u(n-1)=rhs(n-2)/diag(n-2)
do j=n-3,1,-1
 u(j+1)=(rhs(j)+b(j+1)*u(j+2))/diag(j)
end do
flux=a*u(1:n-1)-b*u(2:n)
mass=sum(h*(u(1:n-1)+u(2:n))/2)
residual=maxval(abs((flux(2:n-1)-flux(1:n-2))/w+k*u(2:n-1)-s))
write(*,'(*(ES25.16E3,1X))') u
write(*,'(*(ES25.16E3,1X))') flux
write(*,'(*(ES25.16E3,1X))') mass,residual
contains
function bern(t) result(val)
 real(real64),intent(in)::t
 real(real64)::val,e
 if(abs(t)<1.e-4_real64) then
  val=1-t/2+t*t/12-t**4/720+t**6/30240
 else if(t>50) then
  e=exp(-t)
  val=t*e/(1-e)
 else
  val=t/(exp(t)-1)
 end if
end function
subroutine fail()
 write(*,'(A)') 'ERROR'
 stop
end subroutine
end program
'''


def fortran_input(p):
    return '\n'.join([str(len(p['x']))]+[' '.join(format(z,'.17g') for z in p[k]) for k in ('x','diffusion','velocity','source','decay')]+[f"{p['left']:.17g} {p['right']:.17g}"])+ '\n'


def parse_fortran(stdout):
    if stdout.strip() == 'ERROR':
        return {'error':'ValueError'}
    values = [float(s.replace('D','E')) for s in stdout.split()]
    if len(values) < 7 or len(values)%2 != 1 or not all(math.isfinite(z) for z in values):
        raise ValueError('malformed C06 output')
    n=(len(values)-1)//2
    return dict(density=values[:n],flux=values[n:2*n-1],mass=values[-2],residual_inf=values[-1])


def validate_output(case, output):
    """Bind diagnostics to the returned density, not the reference solution.

    Field, flux, mass, and boundary comparisons retain the case's numerical
    tolerances.  The raw density-equation residual instead has the fixed 2e-8
    absolute limit stated in the task; a small field error need not satisfy it.
    Reported/recomputed residuals may differ by that same absolute tolerance
    because equivalent floating-point evaluations need not agree bit for bit.
    """
    from ..grading import compare_value

    try:
        rtol, atol = case.get('rtol', 2e-8), case.get('atol', 2e-8)
        ok, detail = compare_value(output, case['expected'], rtol, atol, exact_integer_paths=frozenset())
        if not ok:
            return ok, detail
        p = case['input']
        u = output['density']
        n = len(p['x'])
        close = lambda a, b: abs(a-b) <= atol+rtol*abs(b)
        if not close(u[0], p['left']) or not close(u[-1], p['right']):
            return False, 'Dirichlet boundary mismatch'

        # Re-evaluate the specified face law directly; do not reuse the
        # tridiagonal solve or the candidate's reported flux in the residual.
        h = [p['x'][i+1]-p['x'][i] for i in range(n-1)]
        flux = []
        for i in range(n-1):
            pe = p['velocity'][i]*h[i]/p['diffusion'][i]
            a = p['diffusion'][i]/h[i]*_bernoulli(-pe)
            b = p['diffusion'][i]/h[i]*_bernoulli(pe)
            flux.append(a*u[i]-b*u[i+1])
        mass = math.fsum(h[i]*(u[i]+u[i+1])/2 for i in range(n-1))
        residual = max(abs((flux[i+1]-flux[i])/((h[i]+h[i+1])/2)
                           +p['decay'][i]*u[i+1]-p['source'][i])
                       for i in range(n-2))
        if not all(math.isfinite(z) for z in flux+[mass, residual]):
            return False, 'nonfinite recomputed transport diagnostic'
        if any(not close(a, b) for a, b in zip(output['flux'], flux)):
            return False, 'reported flux is inconsistent with the specified SG law'
        if not close(output['mass'], mass):
            return False, 'reported mass is inconsistent with the returned density'
        if residual > 2e-8:
            return False, 'recomputed transport residual exceeds 2e-8'
        reported = output['residual_inf']
        if reported < 0 or abs(reported-residual) > 2e-8:
            return False, 'reported residual is inconsistent with the original equations'
        return True, ''
    except (KeyError, IndexError, TypeError, ValueError, OverflowError, ZeroDivisionError):
        return False, 'invalid transport solution object'


def _case(cid,tier,p,weight,critical=True):
    try:
        expected=_reference(p)
    except ValueError:
        return dict(id=cid,tier=tier,input=p,error='ValueError',weight=weight,critical=critical,rtol=2e-8,atol=2e-8)
    expected['residual_inf']=0.0
    return dict(id=cid,tier=tier,input=p,expected=expected,weight=weight,critical=critical,rtol=2e-8,atol=2e-8)


def cases(seed=17):
    rng=random.Random(seed)
    def base(n=11):
        return dict(x=[i/(n-1) for i in range(n)],diffusion=[1.]*(n-1),velocity=[0.]*(n-1),source=[0.]*(n-2),decay=[0.]*(n-2),left=.3,right=1.2)
    out=[]
    p=base(7);out.append(_case('zero_drift_linear','basic',p,10))
    p=base(9);p.update(left=1.,right=1.,source=[2.] *7,decay=[2.]*7);out.append(_case('constant_reaction_balance','basic',p,10))
    p=base(19);p.update(velocity=[2.3]*18,left=.8,right=.2);out.append(_case('constant_drift_exponential','scientific',p,10))
    p=base(23);p['x']=[(i/22)**1.6 for i in range(23)];p['diffusion']=[.2+rng.random() for _ in range(22)];p['velocity']=[rng.uniform(-3,3) for _ in range(22)];p['source']=[rng.uniform(.1,1) for _ in range(21)];p['decay']=[rng.uniform(.1,2) for _ in range(21)];out.append(_case('heterogeneous_nonuniform','scientific',p,10))
    p=base(17);p.update(velocity=[-4.]*16,diffusion=[.07]*16,left=.6,right=1.4);out.append(_case('negative_drift_boundary_layer','scientific',p,10))
    p=base(41);p.update(velocity=[900.]*40,diffusion=[.01]*40,left=.8,right=.2,source=[.1]*39,decay=[.3]*39);out.append(_case('peclet_2250_positive','stress',p,8))
    p=base(31);p.update(velocity=[(-1)**i*1e-11 for i in range(30)]);out.append(_case('near_zero_bernoulli','stress',p,6))
    p=base(5);p['x'][2]=p['x'][1];out.append(_case('reject_collapsed_cell','stress',p,3))
    p=base(5);p['diffusion'][1]=-1;out.append(_case('reject_negative_diffusion','stress',p,3))
    return out


def prompt(seed=17):
    rng=random.Random(seed+6006)
    p=dict(x=[(i/10)**1.4 for i in range(11)],diffusion=[.3+.7*rng.random() for _ in range(10)],velocity=[rng.uniform(-2,2) for _ in range(10)],source=[.2]*9,decay=[.5]*9,left=.3,right=1.2)
    return '''# C06 非均匀网格上的守恒漂移扩散（Fortran 2008）
实现公开经典一维合成输运问题；不涉及任何真实器件或私人研究。只用标准 Fortran，提交 main.f90、report.md、tests.py。自动检查70分，人工检查推导、独立测试与解释30分。

物理量：x[m]、D[m²/s]>0、v[m/s]，密度u[m⁻³]，体源s[m⁻³s⁻¹]≥0，一级衰减k[s⁻¹]≥0。J=v*u-D*du/dx；稳态 dJ/dx+k*u=s。给定两个非负 Dirichlet 边界。网格可不均匀；D和v在每条边恒定，s和k在内部节点控制体恒定。

必须实现以下离散问题，不能用中心漂移近似替代。h_i=x_(i+1)-x_i，P_i=v_i*h_i/D_i，B(z)=z/(exp(z)-1)，B(0)=1：
J_i=(D_i/h_i)[B(-P_i)u_i-B(P_i)u_(i+1)]；
w_i=(h_(i-1)+h_i)/2，(J_i-J_(i-1))/w_i+k_i*u_i=s_i，i为内部节点。
稳定计算B，处理零漂移和|P|至2500；解释为什么正源与非负边界应给非负密度。mass为全区间梯形积分，即单位横截面积的粒子数[m⁻²]（接口名沿用mass，并非质量kg）；residual_inf为上述内部残差最大绝对值。切勿把积分源与密度源、左右通量符号混淆。

stdin采用数值行协议：第1行节点数n；之后依次是x[n]、diffusion[n-1]、velocity[n-1]、source[n-2]、decay[n-2]（每数组一行）；最后一行left right。3≤n≤129。有限实数、严格递增x、D>0、s,k,left,right≥0，且|P|≤2500；不满足输出单独ERROR。合法输出只含数值：第1行density[n]；第2行flux[n-1]；第3行mass residual_inf。使用双精度，不输出提示文字。无外部库、网络或数据文件。数值比较约为rtol=2e-8、atol=2e-8，原始残差也需小于2e-8。

report.md给出矩阵系数、边界项、尺度/单位、Bernoulli函数的稳定分支，以及至少一个独立解析测试和一个反向漂移/大P测试。tests.py应为独立可运行测试，不以参考数值表充当推导。

可见示例输入（JSON仅说明输入映射，执行时按上述stdin转换；未提供正确输出）：
'''+json.dumps(p,ensure_ascii=False,indent=2)+'''

评估分层：basic 20（扩散极限、平衡），scientific 30（漂移、非均匀/异质、边界层），stress 20（大P、小P及非法网格）。数据由种子改变，禁止查表。方法来源：Scharfetter & Gummel, IEEE TED 16 (1969), DOI 10.1109/T-ED.1969.16566；NIST Sesame项目的公开离散化文档。'''


def reference_submission(seed=17):
    return {'task_id':'C06','answer':{},'artifacts':{
        'main.f90':FORTRAN,
        'report.md':'# C06 方法\n以边通量装配三对角M矩阵，内部行对角为b_left+a_right+k*w，非对角为-a_left和-b_right。Dirichlet值移至右端。零漂移B=1退化为保守扩散；常系数无源的指数解在网格节点精确。Bernoulli小参数用泰勒级数，大正参数用exp(-P)以避免溢出。所有物理量按题设SI单位。独立测试覆盖线性解和常平衡，另外必须在评估中编译实际Fortran运行。\n',
        'tests.py':'''import math,pathlib,subprocess,tempfile
def test_compiled_nonuniform_analytic_transport():
    x=[0,.03,.13,.5,1.];D=.4;v=1.3;left=.7;right=1.4
    with tempfile.TemporaryDirectory() as td:
        exe=str(pathlib.Path(td)/'solver')
        subprocess.run(['gfortran','-std=f2008','-O2','-fcheck=all','-ffree-line-length-none',str(pathlib.Path(__file__).with_name('main.f90')),'-o',exe],check=True)
        rows=[str(len(x)),' '.join(map(str,x)),' '.join([str(D)]*4),' '.join([str(v)]*4),'0 0 0','0 0 0',str(left)+' '+str(right)]
        numbers=[float(z) for z in subprocess.check_output([exe],input=chr(10).join(rows)+chr(10),text=True).split()]
    exact=[left+(right-left)*math.expm1(v*t/D)/math.expm1(v/D) for t in x]
    assert max(abs(a-b) for a,b in zip(numbers[:5],exact))<1e-11
    current=v*left-v*(right-left)/math.expm1(v/D)
    assert max(abs(z-current) for z in numbers[5:9])<1e-11
    assert numbers[-1]<1e-10
if __name__=='__main__':test_compiled_nonuniform_analytic_transport()
'''}}


def mutants(seed=17):
    base=reference_submission(seed)
    out={'reference':base}
    for label,source in {
        'central_drift':FORTRAN.replace('a(i)=d(i)/h(i)*bern(-z)','a(i)=d(i)/h(i)+v(i)/2').replace('b(i)=d(i)/h(i)*bern(z)','b(i)=d(i)/h(i)-v(i)/2'),
        'uniform_control_volume':FORTRAN.replace('w=(h(1:n-2)+h(2:n-1))/2','w=h(1)'),
        'wrong_right_boundary':FORTRAN.replace('rhs(n-2)=rhs(n-2)+b(n-1)*right','rhs(n-2)=rhs(n-2)+a(n-1)*right'),
    }.items():
        sub=dict(base);sub['artifacts']=dict(base['artifacts']);sub['artifacts']['main.f90']=source;out[label]=sub
    return out

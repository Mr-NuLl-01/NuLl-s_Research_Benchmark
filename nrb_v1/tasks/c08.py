"""C08: nonuniform 2-D heterogeneous diagonal-anisotropic elliptic problem."""
from __future__ import annotations

import json
import math
import random

TASK={
    'id':'C08','title':'二维异质各向异性椭圆方程：守恒通量与制造解',
    'language':'python','difficulty':4,
    'capabilities':['elliptic_pde','heterogeneity','anisotropy','manufactured_solution','conservation'],
    'time_budget_s':2400, "execution_budget_s": 12,'required_artifacts':['solution.py','report.md','tests.py'],
    'essential':[
        {'id':'operator','requirement':'使用非均匀控制体和方向相关的谐均面系数'},
        {'id':'flux','requirement':'输出与线性系统同一离散定义的四侧外向积分通量'},
        {'id':'verification','requirement':'独立制造解、全局守恒和网格细化检验'},
    ],
}

SOLUTION=r'''import math

def solve(problem):
    x,y=problem['x'],problem['y']
    kx,ky,f,boundary=(problem[k] for k in ('kx','ky','source','boundary'))
    nx,ny=len(x),len(y)
    if not (3<=nx<=41 and 3<=ny<=41):raise ValueError('grid size')
    if any(not math.isfinite(z) for z in x+y) or any(x[i]>=x[i+1] for i in range(nx-1)) or any(y[j]>=y[j+1] for j in range(ny-1)):
        raise ValueError('grid coordinates')
    for a in (kx,ky,f,boundary):
        if len(a)!=ny or any(len(row)!=nx for row in a) or any(not math.isfinite(z) for row in a for z in row):raise ValueError('field shape')
    if min(z for row in kx+ky for z in row)<=0:raise ValueError('conductivity')
    hx=[x[i+1]-x[i] for i in range(nx-1)]
    hy=[y[j+1]-y[j] for j in range(ny-1)]
    wx=[0.]+[(hx[i-1]+hx[i])/2 for i in range(1,nx-1)]+[0.]
    wy=[0.]+[(hy[j-1]+hy[j])/2 for j in range(1,ny-1)]+[0.]
    def harmonic(a,b):return 2*a*b/(a+b)
    fx=[[harmonic(kx[j][i],kx[j][i+1]) for i in range(nx-1)] for j in range(ny)]
    fy=[[harmonic(ky[j][i],ky[j+1][i]) for i in range(nx)] for j in range(ny-1)]
    count=(nx-2)*(ny-2)
    diag=[0.]*count;rhs=[0.]*count;off=[[] for _ in range(count)]
    def index(i,j):return (j-1)*(nx-2)+i-1
    for j in range(1,ny-1):
        for i in range(1,nx-1):
            row=index(i,j)
            weights=[(i-1,j,fx[j][i-1]*wy[j]/hx[i-1]),(i+1,j,fx[j][i]*wy[j]/hx[i]),
                     (i,j-1,fy[j-1][i]*wx[i]/hy[j-1]),(i,j+1,fy[j][i]*wx[i]/hy[j])]
            diag[row]=math.fsum(w for _,_,w in weights)
            rhs[row]=f[j][i]*wx[i]*wy[j]
            for ii,jj,w in weights:
                if 0<ii<nx-1 and 0<jj<ny-1:off[row].append((index(ii,jj),-w))
                else:rhs[row]+=w*boundary[jj][ii]
    def multiply(v):return [diag[i]*v[i]+math.fsum(w*v[j] for j,w in off[i]) for i in range(count)]
    def dot(a,b):return math.fsum(x*y for x,y in zip(a,b))
    # Integrated control volumes give a symmetric positive definite operator.
    u=[0.]*count;r=list(rhs);z=[r[i]/diag[i] for i in range(count)];p=list(z)
    rz=dot(r,z);target=1e-24*max(1.,dot(rhs,rhs))
    for _ in range(max(100,12*count)):
        if dot(r,r)<=target:break
        ap=multiply(p);alpha=rz/dot(p,ap)
        u=[a+alpha*b for a,b in zip(u,p)]
        r=[a-alpha*b for a,b in zip(r,ap)]
        z=[r[i]/diag[i] for i in range(count)];new=dot(r,z)
        p=[z[i]+new/rz*p[i] for i in range(count)];rz=new
    else:raise ValueError('elliptic solve did not converge')
    field=[list(row) for row in boundary]
    for j in range(1,ny-1):
        for i in range(1,nx-1):field[j][i]=u[index(i,j)]
    west=math.fsum(fx[j][0]*(field[j][1]-field[j][0])/hx[0]*wy[j] for j in range(1,ny-1))
    east=math.fsum(-fx[j][-1]*(field[j][-1]-field[j][-2])/hx[-1]*wy[j] for j in range(1,ny-1))
    south=math.fsum(fy[0][i]*(field[1][i]-field[0][i])/hy[0]*wx[i] for i in range(1,nx-1))
    north=math.fsum(-fy[-1][i]*(field[-1][i]-field[-2][i])/hy[-1]*wx[i] for i in range(1,nx-1))
    source=math.fsum(f[j][i]*wx[i]*wy[j] for j in range(1,ny-1) for i in range(1,nx-1))
    au=multiply(u)
    residual=max(abs(au[index(i,j)]-rhs[index(i,j)])/(wx[i]*wy[j]) for j in range(1,ny-1) for i in range(1,nx-1))
    return {'field':field,'boundary_flux':[west,east,south,north],
            'integrated_source':source,'residual_inf':residual}
'''


def _solve(p):
    ns={};exec(SOLUTION,ns);return ns['solve'](p)


def _manufactured(x,y,kx,ky,u):
    """Build forcing independently by direct face divergence (not solver assembly)."""
    nx,ny=len(x),len(y)
    f=[[0.]*nx for _ in y]
    for j in range(1,ny-1):
        for i in range(1,nx-1):
            dx0=x[i]-x[i-1];dx1=x[i+1]-x[i]
            dy0=y[j]-y[j-1];dy1=y[j+1]-y[j]
            hm=lambda a,b:2/(1/a+1/b)
            ql=-hm(kx[j][i-1],kx[j][i])*(u[j][i]-u[j][i-1])/dx0
            qr=-hm(kx[j][i],kx[j][i+1])*(u[j][i+1]-u[j][i])/dx1
            qb=-hm(ky[j-1][i],ky[j][i])*(u[j][i]-u[j-1][i])/dy0
            qt=-hm(ky[j][i],ky[j+1][i])*(u[j+1][i]-u[j][i])/dy1
            f[j][i]=(qr-ql)/((dx0+dx1)/2)+(qt-qb)/((dy0+dy1)/2)
    return dict(x=x,y=y,kx=kx,ky=ky,source=f,boundary=u)


def validate_output(case, output):
    """Recompute face divergence and integrals from the returned temperature.

    Keep the existing numerical-match tolerances for fields and integrals.
    The residual has its existing absolute 4e-7 tolerance, independent of field
    amplitude or mesh spacing.  The same absolute tolerance accommodates the
    rounding difference between face-divergence and assembled-matrix residuals.
    """
    from ..grading import compare_value

    try:
        rtol, atol = case.get('rtol', 3e-7), case.get('atol', 4e-7)
        ok, detail = compare_value(output, case['expected'], rtol, atol, exact_integer_paths=frozenset())
        if not ok:
            return ok, detail
        p = case['input']
        u = output['field']
        nx, ny = len(p['x']), len(p['y'])
        close = lambda a, b: abs(a-b) <= atol+rtol*abs(b)
        if any(not close(u[j][i], p['boundary'][j][i])
               for j in range(ny) for i in range(nx)
               if j in (0, ny-1) or i in (0, nx-1)):
            return False, 'Dirichlet boundary mismatch'
        hx = [p['x'][i+1]-p['x'][i] for i in range(nx-1)]
        hy = [p['y'][j+1]-p['y'][j] for j in range(ny-1)]
        wx = [(hx[i-1]+hx[i])/2 for i in range(1, nx-1)]
        wy = [(hy[j-1]+hy[j])/2 for j in range(1, ny-1)]

        def harmonic(a, b):
            # Algebraically 2*a*b/(a+b), without the intermediate product.
            lo, hi = min(a, b), max(a, b)
            return lo*(2/(1+lo/hi))

        def qx(j, i):
            k = harmonic(p['kx'][j][i], p['kx'][j][i+1])
            return -k*(u[j][i+1]-u[j][i])/hx[i]

        def qy(j, i):
            k = harmonic(p['ky'][j][i], p['ky'][j+1][i])
            return -k*(u[j+1][i]-u[j][i])/hy[j]

        # This face-divergence path is independent of SOLUTION's integrated
        # matrix assembly and its reported residual or boundary-flux totals.
        residuals = []
        source_terms = []
        for j in range(1, ny-1):
            for i in range(1, nx-1):
                residuals.append(abs((qx(j, i)-qx(j, i-1))/wx[i-1]
                                     +(qy(j, i)-qy(j-1, i))/wy[j-1]
                                     -p['source'][j][i]))
                source_terms.append(p['source'][j][i]*wx[i-1]*wy[j-1])
        flux = [math.fsum(-qx(j, 0)*wy[j-1] for j in range(1, ny-1)),
                math.fsum(qx(j, nx-2)*wy[j-1] for j in range(1, ny-1)),
                math.fsum(-qy(0, i)*wx[i-1] for i in range(1, nx-1)),
                math.fsum(qy(ny-2, i)*wx[i-1] for i in range(1, nx-1))]
        source = math.fsum(source_terms)
        if not all(math.isfinite(z) for z in residuals+flux+[source]):
            return False, 'nonfinite recomputed elliptic diagnostic'
        residual = max(residuals)
        if any(not close(a, b) for a, b in zip(output['boundary_flux'], flux)):
            return False, 'reported boundary flux is inconsistent with the returned field'
        if not close(output['integrated_source'], source):
            return False, 'reported integrated source is inconsistent with the input'
        if residual > 4e-7:
            return False, 'recomputed elliptic residual exceeds 4e-7'
        reported = output['residual_inf']
        if reported < 0 or abs(reported-residual) > 4e-7:
            return False, 'reported residual is inconsistent with the original equations'
        return True, ''
    except (KeyError, IndexError, TypeError, ValueError, OverflowError, ZeroDivisionError):
        return False, 'invalid elliptic solution object'


def cases(seed=17):
    rng=random.Random(seed)
    truths={}
    def make(nx,ny,kind):
        x=[(i/(nx-1))**(1.3 if kind=='heterogeneous' else 1) for i in range(nx)]
        y=[1.4*(j/(ny-1))**(1.2 if kind=='heterogeneous' else 1) for j in range(ny)]
        kx=[[1. for _ in x] for _ in y];ky=[[1. for _ in x] for _ in y]
        if kind=='anisotropic':kx=[[7.]*nx for _ in y];ky=[[.3]*nx for _ in y]
        if kind=='heterogeneous':
            kx=[[.2+(4 if xx>.48 else 0)+.1*rng.random() for xx in x] for yy in y]
            ky=[[.4+2*(yy> .7)+.2*rng.random() for xx in x] for yy in y]
        if kind=='contrast':
            kx=[[.02 if xx<.5 else 20. for xx in x] for yy in y]
            ky=[[.15 if yy<.7 else 8. for xx in x] for yy in y]
        offset=.1+.3*rng.random();slope_x=.1+.4*rng.random();slope_y=-.3+.6*rng.random()
        if kind=='linear':u=[[offset+slope_x*xx+slope_y*yy for xx in x] for yy in y]
        else:
            amplitude=.6+.6*rng.random();secondary=.08+.16*rng.random()
            mode_x=rng.choice((2,3));mode_y=rng.choice((2,3))
            u=[[offset+slope_x*xx+slope_y*yy+amplitude*math.sin(math.pi*xx)*math.sin(math.pi*yy/1.4)+secondary*math.sin(mode_x*math.pi*xx)*math.sin(mode_y*math.pi*yy/1.4) for xx in x] for yy in y]
        p=_manufactured(x,y,kx,ky,u)
        truths[id(p)]=u
        p['boundary']=[[z if j in (0,ny-1) or i in (0,nx-1) else 0. for i,z in enumerate(row)] for j,row in enumerate(u)]
        return p
    specs=[('affine_harmonic','basic',make(8,7,'linear'),10),
           ('isotropic_manufactured','basic',make(9,8,'isotropic'),10),
           ('directional_anisotropy','scientific',make(13,10,'anisotropic'),10),
           ('nonuniform_interfaces','scientific',make(12,11,'heterogeneous'),10),
           ('refined_manufactured','scientific',make(25,19,'anisotropic'),10),
           ('high_contrast_interfaces','stress',make(27,23,'contrast'),8),
           ('rectangular_nonuniform','stress',make(17,29,'heterogeneous'),6)]
    bad=make(5,5,'linear');bad['kx'][2][2]=0;specs.append(('reject_zero_conductivity','stress',bad,3))
    bad=make(5,5,'linear');bad['y'][2]=bad['y'][1];specs.append(('reject_collapsed_y','stress',bad,3))
    out=[]
    for cid,tier,p,w in specs:
        case=dict(id=cid,tier=tier,input=p,weight=w,critical=True,rtol=3e-7,atol=4e-7)
        try:
            expected=_solve(p)
            # The independent prescribed field is the discrete exact solution.
            expected['field']=[list(row) for row in truths[id(p)]]
            expected['residual_inf']=0.
            case['expected']=expected
        except ValueError:case['error']='ValueError'
        out.append(case)
    return out


def prompt(seed=17):
    nx,ny=7,6
    x=[i/(nx-1) for i in range(nx)];y=[1.4*j/(ny-1) for j in range(ny)]
    p=dict(x=x,y=y,kx=[[7.]*nx for _ in y],ky=[[.3]*nx for _ in y],
           source=[[(7*math.pi**2+.3*(math.pi/1.4)**2)*math.sin(math.pi*xx)*math.sin(math.pi*yy/1.4) for xx in x] for yy in y],
           boundary=[[.2+.1*xx+.05*yy if i in (0,nx-1) or j in (0,ny-1) else 0. for i,xx in enumerate(x)] for j,yy in enumerate(y)])
    return '''# C08 二维异质、方向各向异性稳态传热
提交标准库solution.py（solve(problem)->JSON对象）、report.md和tests.py。自动70/人工30；无第三方库、网络或外部数据。

矩形域上 -∂x(kx ∂x u)-∂y(ky ∂y u)=f，u为温度[K]，坐标[m]，kx/ky[W/(m K)]，f[W/m³]；按单位厚度计算通量[W/m]。这里只考察与坐标对齐的正对角导热张量，无混合导数。给定全部外边界Dirichlet温度，网格可不均匀。

输入x[nx],y[ny]和形状[ny][nx]的kx、ky、source、boundary；数组第一索引是y。仅boundary四周使用，其内部值必须忽略。3≤nx,ny≤41，坐标严格递增、所有数有限、kx/ky>0，否则raise ValueError。
必须求以下指定离散问题。x方向边面系数Kx_(j,i+1/2)=2*kx[j][i]*kx[j][i+1]/(kx[j][i]+kx[j][i+1])，y方向同理（此谐均定义是合同的一部分）。qx=-Kx*(u_right-u_left)/hx，qy=-Ky*(u_top-u_bottom)/hy。内部控制体宽wx=(hx_left+hx_right)/2，wy类似；(qx_right-qx_left)/wx+(qy_top-qy_bottom)/wy=f。不要直接对非均匀网格套均匀五点公式。

返回field[ny][nx]、boundary_flux=[west,east,south,north]、integrated_source、residual_inf。残差是上述密度方程的最大绝对值。integrated_source=Σ内部f*wx*wy。边界通量是**内部控制体并集**的外向积分通量：west=-Σ_j qx_(j,1/2)*wy_j、east=+Σ_j qx_(j,nx-3/2)*wy_j；south/north类似，对应和只遍历另一坐标的内部节点。它们位于最外层内部控制体表面，不能把它们解读为连续几何外边界的二阶法向导数；Σ四侧通量应等于integrated_source。不要添加角点半权重。

report.md解释积分装配为何对称正定、材料界面面系数、通量方向，以及一个连续制造解的网格细化试验。tests.py应包括独立的仿射解、连续正弦制造解误差比及全局源/通量守恒，不能只回调同一个装配器产生真值。
可见示例输入（内部boundary数值仅为占位，未给正确输出）：
'''+json.dumps({**p,'boundary':[[z if j in (0,len(p['y'])-1) or i in (0,len(p['x'])-1) else 0. for i,z in enumerate(row)] for j,row in enumerate(p['boundary'])]},ensure_ascii=False,indent=2)+'''
basic20（仿射/制造解），scientific30（各向异性、界面、细化），stress20（高对比、矩形非均匀、非法输入）。NIST FiPy的公开有限体积理论文档可作背景；这里的方程与面平均定义以题设为准。'''


def reference_submission(seed=17):
    return {'task_id':'C08','answer':{},'artifacts':{
        'solution.py':SOLUTION,
        'report.md':'# 方法\n控制体方程乘wx*wy后，水平方向边导通系数为Kx*wy/hx，垂直方向为Ky*wx/hy。共享边贡献在两行相同，Dirichlet消元后为SPD。用Jacobi预条件共轭梯度求解。所有输出通量直接使用同一边梯度；内部边在全局和中相消，只剩四侧控制面。谐均是题设界面合同，不能替换算术均值。连续正弦源的规则网格误差应约二阶，但离散制造解用于把装配错误与截断误差分开。\n',
        'tests.py':'''import math
from solution import solve
def problem(n):
    x=[i/(n-1) for i in range(n)];y=x[:]
    one=[[1.]*n for _ in x]
    f=[[2*math.pi**2*math.sin(math.pi*a)*math.sin(math.pi*b) for a in x] for b in y]
    boundary=[[0.]*n for _ in x]
    return dict(x=x,y=y,kx=one,ky=one,source=f,boundary=boundary)
def test_continuum_refinement_and_balance():
    errors=[]
    for n in (9,17):
        p=problem(n);r=solve(p)
        errors.append(max(abs(r['field'][j][i]-math.sin(math.pi*x)*math.sin(math.pi*y)) for j,y in enumerate(p['y']) for i,x in enumerate(p['x'])))
        assert abs(sum(r['boundary_flux'])-r['integrated_source'])<1e-8
    assert 3.8<errors[0]/errors[1]<4.2
if __name__=='__main__':test_continuum_refinement_and_balance()
'''}}


def mutants(seed=17):
    variants={
        'arithmetic_interface':SOLUTION.replace('def harmonic(a,b):return 2*a*b/(a+b)','def harmonic(a,b):return (a+b)/2'),
        'swap_tensor_directions':SOLUTION.replace("kx,ky,f,boundary=(problem[k] for k in ('kx','ky','source','boundary'))","ky,kx,f,boundary=(problem[k] for k in ('kx','ky','source','boundary'))"),
        'reverse_west_flux':SOLUTION.replace("'boundary_flux':[west,east,south,north]","'boundary_flux':[-west,east,south,north]"),
    }
    out={'reference':reference_submission(seed)}
    for label,src in variants.items():
        sub=reference_submission(seed);sub['artifacts']['solution.py']=src;out[label]=sub
    return out

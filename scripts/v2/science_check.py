"""Scoped independent mathematics checks for the current Python task modules.

Run from any working directory with Python, NumPy and SciPy installed:
    python scripts/v2/science_check.py --out /tmp/science-check-current.json

Output is printed and optionally written to a NEW file. This is reviewer-side
validation, not a candidate model evaluation or an execution-isolation test.
"""
import copy
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize_scalar, least_squares

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from nrb_v1.tasks import c04,c05,c08,c10
from nrb_v2.tasks import p06
from nrb_v1.grading import compare_value,EXACT_INTEGER_PATHS


def load_source(source):
    ns={};exec(source,ns);return ns['solve']


def optics_boundary_system(p):
    n=np.array([complex(*v) for v in p['indices']])
    w=np.sqrt(n*n-(n[0].real*math.sin(math.radians(p['angle_deg'])))**2)
    w=np.array([-z if z.imag<0 or (z.imag==0 and z.real<0) else z for z in w])
    q=w if p['polarization']=='s' else n*n/w
    count=len(n);result=[]
    for wl in p['wavelengths_nm']:
        matrix=np.zeros((2*count,2*count),complex);rhs=np.zeros(2*count,complex)
        matrix[0,0]=1;rhs[0]=1
        matrix[1,-1]=1
        for j in range(count-1):
            phase=1 if j==0 else np.exp(2j*np.pi*w[j]*p['thickness_nm'][j-1]/wl)
            row=2+2*j
            matrix[row,2*j]=phase;matrix[row,2*j+1]=1/phase
            matrix[row,2*j+2]=-1;matrix[row,2*j+3]=-1
            matrix[row+1,2*j]=q[j]*phase;matrix[row+1,2*j+1]=-q[j]/phase
            matrix[row+1,2*j+2]=-q[j+1];matrix[row+1,2*j+3]=q[j+1]
        v=np.linalg.solve(matrix,rhs);r,t=v[1],v[-2]
        R=abs(r)**2;T=abs(t)**2*q[-1].real/q[0].real
        result.append(dict(r=[float(r.real),float(r.imag)],t=[float(t.real),float(t.imag)],R=float(R),T=float(T),A=float(1-R-T)))
    return {'spectra':result}


def independent_profile(p,d):
    parts=[]
    for e in p['experiments']:
        t=np.asarray(e['time']);y=np.asarray(e['value']);sigma=np.asarray(e['sigma'])
        x=np.exp(-d*np.pi**2*t/p['length']**2)
        X=np.column_stack([x,np.ones(len(x))])/sigma[:,None]
        coef=np.linalg.lstsq(X,y/sigma,rcond=None)[0]
        residual=X@coef-y/sigma
        derivative=-coef[0]*np.pi**2/p['length']**2*t*x/sigma
        projected=derivative-X@np.linalg.lstsq(X,derivative,rcond=None)[0]
        parts.append((float(residual@residual),coef.tolist(),float(projected@projected)))
    return sum(v[0] for v in parts),parts


def independent_modal_predictions(p,theta,obs):
    D,k=theta;n=len(p['A0']);dt=p['dt'];L=p['length']
    eigen=4*np.sin(np.pi*np.arange(n)/n)**2/(L/n)**2
    A0=np.fft.fft(p['A0']);total0=np.fft.fft(np.asarray(p['A0'])+np.asarray(p['B0']))
    predictions=[];jac=[]
    for o in obs:
        steps=o['step'];fa=1+dt*(k+D*eigen);ft=1+dt*D*eigen
        A=np.fft.ifft(A0*fa**(-steps)).real
        total=np.fft.ifft(total0*ft**(-steps)).real
        Ad=np.fft.ifft(-steps*dt*eigen*A0*fa**(-steps-1)).real
        Ak=np.fft.ifft(-steps*dt*A0*fa**(-steps-1)).real
        Td=np.fft.ifft(-steps*dt*eigen*total0*ft**(-steps-1)).real
        i=o['index']
        predictions.append(float(A[i] if o['species']=='A' else total[i]-A[i]))
        jac.append([float(Ad[i]),float(Ak[i])] if o['species']=='A' else [float(Td[i]-Ad[i]),float(-Ak[i])])
    return np.array(predictions),np.array(jac)


def main(output=None):
    report={}
    optical=[]
    for seed in [0,17,2026]:
        for c in c04.cases(seed):
            if 'error' in c or c['id'] in ('opaque_layer','long_bragg'):continue
            out=optics_boundary_system(c['input'])
            passed,why=compare_value(out,c['expected'],c['rtol'],c['atol'],exact_integer_paths=frozenset())
            optical.append(dict(seed=seed,case=c['id'],passed=passed,detail=why))
    report['optics_boundary_system']=optical
    start=c05.SOURCE.index('        def backward(');end=c05.SOURCE.index('        y=list(initial)')
    replacement='''        def backward(y,step,q):
            import numpy as np
            matrix=np.array([[1+step*(kf+decay),-step*kr],[-step*kf,1+step*(kr+decay)]])
            return np.linalg.solve(matrix,np.array([y[0]+step*q,y[1]])).tolist()
'''
    alternative=load_source(c05.SOURCE[:start]+replacement+c05.SOURCE[end:])
    counts=[]
    for seed in [0,17,91,2026]:
        for c in c05.cases(seed):
            if 'error' in c:continue
            out=alternative(copy.deepcopy(c['input']))
            passed,why=compare_value(out,c['expected'],c['rtol'],c['atol'],exact_integer_paths=EXACT_INTEGER_PATHS['C05'])
            counts.append(dict(seed=seed,case=c['id'],passed=passed,detail=why,reference_counts=[c['expected'][k] for k in ['accepted_steps','rejected_steps']],alternative_counts=[out[k] for k in ['accepted_steps','rejected_steps']]))
    report['adaptive_numpy_solve']=counts
    inverse=[]
    for c in p06.cases(17):
        if 'error' in c or c['id']=='structurally_flat':continue
        p=c['input'];lo,hi=p['bounds']
        opt=minimize_scalar(lambda d:independent_profile(p,d)[0],bounds=(lo,hi),method='bounded',options={'xatol':1e-14})
        d=min((independent_profile(p,z)[0],z) for z in [lo,hi,opt.x])[1]
        chi,parts=independent_profile(p,d)
        ref=c['expected']
        inverse.append(dict(case=c['id'],reference_D=ref['diffusion'],independent_D=d,D_error=abs(d-ref['diffusion']),chi2_error=abs(chi-ref['chi2']),information_rel_error=abs(sum(z[2] for z in parts)-ref['information'])/max(1e-20,abs(ref['information']))))
    report['inverse_heat_qr_and_bounded_search']=inverse
    tiny=dict(length=1.,bounds=[.01,.2],experiments=[dict(time=[0,1e-15,2e-15,3e-15],value=[.8]*4,sigma=[.01]*4)])
    try:report['inverse_contract_tiny_times']={'output':p06._solve(tiny)}
    except Exception as e:report['inverse_contract_tiny_times']={'exception':type(e).__name__,'message':str(e),'input':tiny}
    pipeline=[]
    for c in c10.cases(17):
        if 'error' in c or c['input']['mode']!='infer':continue
        p=c['input'];obs=p['observations'];sig=np.array([o['sigma'] for o in obs]);target=np.array([o['value'] for o in obs])
        def fun(v):return (independent_modal_predictions(p,v,obs)[0]-target)/sig
        def jac(v):return independent_modal_predictions(p,v,obs)[1]/sig[:,None]
        bounds=np.array(p['bounds']).T
        fit=least_squares(fun,p['initial_guess'],jac=jac,bounds=bounds,ftol=1e-13,xtol=1e-13,gtol=1e-13,max_nfev=300)
        pred,j=independent_modal_predictions(p,fit.x,obs);J=j/sig[:,None];h=J.T@J
        a,b,covc=h[0,0],h[0,1],h[1,1];det=a*covc-b*b
        ident=bool(a>1e-12 and covc>1e-12 and det>1e-10*max(a*covc,1e-30))
        ref=c['expected']
        entry=dict(case=c['id'],reference_parameters=ref['parameters'],independent_parameters=fit.x.tolist() if ident else None,identifiable_match=ident==ref['identifiable'],prediction_max_error=float(np.max(np.abs(pred-ref['predicted']))),chi2_error=abs(float(fun(fit.x)@fun(fit.x))-ref['chi2']))
        if ident:
            cov=np.linalg.inv(h);entry['covariance_max_absolute_error']=float(np.max(np.abs(cov-ref['covariance'])))
        pipeline.append(entry)
    report['pipeline_fourier_and_scipy_fit']=pipeline
    payload=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
    if output is not None:
        out=Path(output).expanduser().resolve()
        out.parent.mkdir(parents=True,exist_ok=True)
        with out.open('x',encoding='utf-8') as stream:
            stream.write(payload)
    print(payload,end='')

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',help='Optional new JSON output path; existing files are never overwritten')
    main(parser.parse_args().out)

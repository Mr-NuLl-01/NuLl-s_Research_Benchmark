"""Supplementary direct elliptic/Fourier/bootstrap verification.

Run with Python, NumPy and SciPy installed, from any working directory:
    python scripts/v2/science_check_extra.py --out /tmp/science-check-extra-current.json

This imports only reviewer helpers from the sibling science_check.py. It does
not run candidate models, the V2 CLI, Docker or report authenticity checks.
"""
import json, math
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve
from science_check import c08,c10,compare_value,independent_modal_predictions


def modal_resume(s,target):
    n=s['n'];dt=s['dt'];steps=target-s['step']
    eig=4*np.sin(np.pi*np.arange(n)/n)**2/(s['length']/n)**2
    a0=np.fft.fft(s['A']);t0=np.fft.fft(np.array(s['A'])+np.array(s['B']))
    fa=1+dt*(s['k']+s['D']*eig);ft=1+dt*s['D']*eig
    a=a0*fa**(-steps);total=t0*ft**(-steps)
    ad=np.fft.fft(s['dA_dD'])*fa**(-steps)-steps*dt*eig*a0*fa**(-steps-1)
    ak=np.fft.fft(s['dA_dk'])*fa**(-steps)-steps*dt*a0*fa**(-steps-1)
    td=np.fft.fft(np.array(s['dA_dD'])+np.array(s['dB_dD']))*ft**(-steps)-steps*dt*eig*t0*ft**(-steps-1)
    tk=np.fft.fft(np.array(s['dA_dk'])+np.array(s['dB_dk']))*ft**(-steps)
    out=dict(s,step=target)
    for key,value in [('A',a),('B',total-a),('dA_dD',ad),('dA_dk',ak),('dB_dD',td-ad),('dB_dk',tk-ak)]:
        out[key]=np.fft.ifft(value).real.tolist()
    return out


def elliptic(p):
    x=np.asarray(p['x']);y=np.asarray(p['y']);nx=len(x);ny=len(y)
    kx=np.asarray(p['kx']);ky=np.asarray(p['ky']);src=np.asarray(p['source']);u=np.array(p['boundary'],float)
    hx=np.diff(x);hy=np.diff(y);wx=(hx[:-1]+hx[1:])/2;wy=(hy[:-1]+hy[1:])/2
    fx=2/(1/kx[:,:-1]+1/kx[:,1:]);fy=2/(1/ky[:-1,:]+1/ky[1:,:])
    a=lil_matrix(((nx-2)*(ny-2),(nx-2)*(ny-2)));b=[]
    idx=lambda i,j:(j-1)*(nx-2)+i-1
    for j in range(1,ny-1):
        for i in range(1,nx-1):
            row=idx(i,j);rhs=src[j,i]
            terms=[(i-1,j,fx[j,i-1]/hx[i-1]/wx[i-1]),(i+1,j,fx[j,i]/hx[i]/wx[i-1]),(i,j-1,fy[j-1,i]/hy[j-1]/wy[j-1]),(i,j+1,fy[j,i]/hy[j]/wy[j-1])]
            for ii,jj,w in terms:
                a[row,row]+=w
                if 0<ii<nx-1 and 0<jj<ny-1:a[row,idx(ii,jj)]-=w
                else:rhs+=w*u[jj,ii]
            b.append(rhs)
    u[1:-1,1:-1]=spsolve(a.tocsr(),b).reshape((ny-2,nx-2))
    qx=-fx*np.diff(u,axis=1)/hx[None,:];qy=-fy*np.diff(u,axis=0)/hy[:,None]
    r=(qx[1:-1,1:]-qx[1:-1,:-1])/wx[None,:]+(qy[1:,1:-1]-qy[:-1,1:-1])/wy[:,None]-src[1:-1,1:-1]
    flux=[float(np.dot(-qx[1:-1,0],wy)),float(np.dot(qx[1:-1,-1],wy)),float(np.dot(-qy[0,1:-1],wx)),float(np.dot(qy[-1,1:-1],wx))]
    return dict(field=u.tolist(),boundary_flux=flux,integrated_source=float(np.sum(src[1:-1,1:-1]*wy[:,None]*wx[None,:])),residual_inf=float(np.max(np.abs(r))))


def main(output=None):
    report={'elliptic':[],'modal_state_resume':[],'bootstrap':[]}
    for case in c08.cases(17):
        if 'error' in case:continue
        out=elliptic(case['input']);ok,detail=c08.validate_output(case,out)
        report['elliptic'].append(dict(case=case['id'],passed=ok,detail=detail,residual=out['residual_inf']))

    for case in c10.cases(17):
        if 'error' in case:continue
        p=case['input'];ref=case['expected']
        if p['mode'] in ('simulate','resume'):
            if p['mode']=='resume':s=p['checkpoint']
            else:
                s=dict(n=len(p['A0']),length=p['length'],D=p['D'],k=p['k'],dt=p['dt'],step=0,A=p['A0'],B=p['B0'])
                s.update({key:[0.]*s['n'] for key in ('dA_dD','dA_dk','dB_dD','dB_dk')})
            out=modal_resume(s,p['steps'])
            ok,detail=compare_value(out,ref['final'],case['rtol'],case['atol'],exact_integer_paths=frozenset({'result.n','result.step'}))
            report['modal_state_resume'].append(dict(case=case['id'],passed=ok,detail=detail))
        elif ref['identifiable'] and p.get('bootstrap_replicates',0):
            obs=p['observations'];sig=np.array([o['sigma'] for o in obs]);target=np.array([o['value'] for o in obs]);bounds=np.array(p['bounds']).T
            def fun(v,values):return (independent_modal_predictions(p,v,obs)[0]-values)/sig
            def jac(v):return independent_modal_predictions(p,v,obs)[1]/sig[:,None]
            def fit(start,values):return least_squares(lambda v:fun(v,values),start,jac=jac,bounds=bounds,ftol=1e-13,xtol=1e-13,gtol=1e-13,max_nfev=300).x
            theta=fit(p['initial_guess'],target);pred=independent_modal_predictions(p,theta,obs)[0]
            state=p['bootstrap_seed'];samples=[]
            for _ in range(p['bootstrap_replicates']):
                noise=[]
                for o in obs:
                    state=(1664525*state+1013904223)%2**32;u=(state+.5)/2**32
                    state=(1664525*state+1013904223)%2**32;v=(state+.5)/2**32
                    noise.append(math.sqrt(-2*math.log(u))*math.cos(2*math.pi*v))
                samples.append(fit(theta,pred+sig*np.array(noise)))
            out=dict(mean=np.mean(samples,axis=0).tolist(),covariance=np.cov(np.array(samples),rowvar=False,ddof=1).tolist(),rng_state=state)
            ok,detail=compare_value(out,ref['bootstrap'],case['rtol'],case['atol'],exact_integer_paths=frozenset({'result.rng_state'}))
            report['bootstrap'].append(dict(case=case['id'],passed=ok,detail=detail,mean_error=float(np.max(np.abs(np.array(out['mean'])-ref['bootstrap']['mean']))),covariance_error=float(np.max(np.abs(np.array(out['covariance'])-ref['bootstrap']['covariance'])))))

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

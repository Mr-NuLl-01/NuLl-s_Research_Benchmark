"""Independent mathematics, compiled Fortran, and executable controls for C06–C10.

These are scoped reference/control checks, not ratings of any commercial model.
"""
from __future__ import annotations

import copy
import importlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from nrb_v1.grading import compare_value, grade

MODULES=[importlib.import_module(f'nrb_v1.tasks.c{i:02d}') for i in range(6,11)]
C06,C07,C08,C09,C10=MODULES


def candidate(module,source=None):
    namespace={}
    exec(compile(source or module.SOLUTION,'solution.py','exec'),namespace)
    return namespace['solve']


class CompiledCandidates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which('gfortran'):
            raise unittest.SkipTest('gfortran unavailable: compiled scientific checks not scored')
        cls.temp=tempfile.TemporaryDirectory()
        cls.executables={}
        for module in (C06,C09):
            p=Path(cls.temp.name)/module.TASK['id'];p.mkdir()
            source=p/'main.f90';source.write_text(module.FORTRAN)
            exe=p/'solver'
            subprocess.run(['gfortran','-std=f2008','-O2','-fcheck=all','-ffree-line-length-none',str(source),'-o',str(exe)],check=True,capture_output=True,text=True)
            cls.executables[module.TASK['id']]=exe

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls,'temp'):cls.temp.cleanup()

    def run_fortran(self,module,p):
        result=subprocess.run([str(self.executables[module.TASK['id']])],input=module.fortran_input(p),text=True,capture_output=True,check=True,timeout=10)
        return module.parse_fortran(result.stdout)

    def test_c06_nonuniform_exponential_is_exact(self):
        x=[0.,.03,.13,.5,1.]
        diffusion,velocity,left,right=.4,1.3,.7,1.4
        p=dict(x=x,diffusion=[diffusion]*4,velocity=[velocity]*4,source=[0.]*3,decay=[0.]*3,left=left,right=right)
        r=self.run_fortran(C06,p)
        exact=[left+(right-left)*math.expm1(velocity*t/diffusion)/math.expm1(velocity/diffusion) for t in x]
        current=velocity*left-velocity*(right-left)/math.expm1(velocity/diffusion)
        self.assertLess(max(abs(a-b) for a,b in zip(r['density'],exact)),1e-12)
        self.assertLess(max(abs(v-current) for v in r['flux']),1e-12)
        self.assertLess(r['residual_inf'],1e-10)

    def test_c06_source_decay_conservation_and_positive_high_peclet(self):
        for c in C06.cases(91):
            if 'expected' not in c:continue
            p=c['input'];r=self.run_fortran(C06,p)
            x=p['x'];u=r['density'];h=[b-a for a,b in zip(x,x[1:])]
            widths=[(a+b)/2 for a,b in zip(h,h[1:])]
            source=math.fsum(s*w for s,w in zip(p['source'],widths))
            loss=math.fsum(k*v*w for k,v,w in zip(p['decay'],u[1:-1],widths))
            self.assertAlmostEqual(r['flux'][-1]-r['flux'][0]+loss,source,delta=1e-9)
            self.assertGreaterEqual(min(u),-1e-12)

    def test_c09_independent_boltzmann_equilibrium_and_gauge(self):
        n=15;h=1/(n-1);lam2=.17
        phi=[-.12+.27*math.sin(math.pi*i/(n-1)) for i in range(n)]
        density=[1.1*math.exp(v) for v in phi]
        charge=[-lam2*(phi[i+1]-2*phi[i]+phi[i-1])/h**2+density[i] for i in range(1,n-1)]
        p=dict(n=n,lambda_squared=lam2,potential_left=phi[0],potential_right=phi[-1],density_left=density[0],density_right=density[-1],diffusion=[.9]*(n-1),charge=charge,source=[0.]*(n-2))
        a=self.run_fortran(C09,p)
        self.assertLess(max(abs(v-w) for v,w in zip(a['potential'],phi)),1e-8)
        self.assertLess(max(abs(v-w) for v,w in zip(a['density'],density)),1e-8)
        self.assertLess(max(abs(v) for v in a['flux']),1e-8)
        p['potential_left']+=3.7;p['potential_right']+=3.7
        b=self.run_fortran(C09,p)
        self.assertLess(max(abs(v+3.7-w) for v,w in zip(a['potential'],b['potential'])),1e-8)
        self.assertLess(max(abs(v-w) for v,w in zip(a['density'],b['density'])),1e-8)

    def test_c09_independent_current_solution_and_original_residual(self):
        n=19;h=1/(n-1);field=.6;left=.7;right=1.3;diffusion=.8
        phi=[field*i*h for i in range(n)]
        exact=[left+(right-left)*math.expm1(v)/math.expm1(field) for v in phi]
        # Affine potential has zero discrete Laplacian, hence charge=n exactly.
        p=dict(n=n,lambda_squared=.23,potential_left=0.,potential_right=field,density_left=left,density_right=right,diffusion=[diffusion]*(n-1),charge=exact[1:-1],source=[0.]*(n-2))
        r=self.run_fortran(C09,p)
        self.assertLess(max(abs(a-b) for a,b in zip(r['density'],exact)),1e-8)
        j=diffusion*(field*left-field*(right-left)/math.expm1(field))
        self.assertLess(max(abs(v-j) for v in r['flux']),1e-8)
        # Recompute the original nonlinear equations, independent of reported residual.
        for i in range(1,n-1):
            potential_residual=.23*(2*r['potential'][i]-r['potential'][i-1]-r['potential'][i+1])/h**2+r['density'][i]-p['charge'][i-1]
            self.assertLess(abs(potential_residual),1e-8)
            self.assertLess(abs(r['flux'][i]-r['flux'][i-1])/h,1e-8)


class IndependentPythonScience(unittest.TestCase):
    def test_c09_validator_recomputes_science_instead_of_trusting_claims(self):
        case=C09.cases()[3]
        self.assertTrue(C09.validate_output(case,case['expected'])[0])
        wrong=copy.deepcopy(case['expected']);wrong['density'][3]*=1.01;wrong['residual_inf']=0.
        self.assertFalse(C09.validate_output(case,wrong)[0])
        wrong=copy.deepcopy(case['expected']);wrong['flux']=[0.]*len(wrong['flux'])
        self.assertFalse(C09.validate_output(case,wrong)[0])
        for malformed in ({},None,{'potential':[], 'density':[], 'flux':[], 'residual_inf':0.}):
            self.assertFalse(C09.validate_output(case,malformed)[0])
        for value in (10**1000,'not a number',float('nan'),float('inf'),1e308):
            wrong=copy.deepcopy(case['expected']);wrong['potential'][3]=value
            self.assertFalse(C09.validate_output(case,wrong)[0])

    def test_c07_true_nuisance_and_absolute_sigma_scaling(self):
        solve=candidate(C07);t=[0.,.2,.7,1.5,3.,6.]
        p=dict(length=2.,bounds=[.02,.3],experiments=[dict(time=t,value=[.8+1.3*math.exp(-.11*math.pi**2*x/4) for x in t],sigma=[.01]*6)])
        a=solve(p);q=copy.deepcopy(p);q['experiments'][0]['sigma']=[.02]*6;b=solve(q)
        self.assertAlmostEqual(a['diffusion'],.11,delta=1e-7)
        self.assertAlmostEqual(a['nuisance'][0][0],1.3,delta=1e-6)
        self.assertAlmostEqual(a['nuisance'][0][1],.8,delta=1e-6)
        self.assertAlmostEqual(a['information']/b['information'],4.,delta=1e-5)
        self.assertLess(b['interval'][0],a['interval'][0]);self.assertGreater(b['interval'][1],a['interval'][1])
        # At a zero-residual optimum, half the profile curvature equals Schur information.
        rate=math.pi**2/4;weights=[1e4]*len(t)
        def profile(d):
            x=[math.exp(-d*rate*v) for v in t];y=p['experiments'][0]['value']
            mx=sum(x)/len(x);my=sum(y)/len(y)
            slope=sum((a-mx)*(b-my) for a,b in zip(x,y))/sum((a-mx)**2 for a in x)
            intercept=my-slope*mx
            return sum(w*(intercept+slope*a-b)**2 for w,a,b in zip(weights,x,y))
        eps=1e-5;curvature=(profile(.11+eps)+profile(.11-eps)-2*profile(.11))/(2*eps**2)
        self.assertAlmostEqual(curvature/a['information'],1.,delta=1e-6)

    def test_c07_constant_signal_is_not_an_estimate_of_diffusion(self):
        p=dict(length=1.,bounds=[.01,.2],experiments=[dict(time=[0.,.2,.7,1.5,3.],value=[.8]*5,sigma=[.01]*5)])
        r=candidate(C07)(p)
        self.assertFalse(r['identifiable']);self.assertEqual(r['diffusion'],.01)
        self.assertEqual(r['interval'],p['bounds']);self.assertEqual(r['clipped'],[True,True])

    def test_c08_continuum_refinement_flux_and_ignore_interior_boundary(self):
        solve=candidate(C08);errors=[]
        for n in (9,17,33):
            x=[i/(n-1) for i in range(n)]
            source=[[(2.+.3)*math.pi**2*math.sin(math.pi*xx)*math.sin(math.pi*yy) for xx in x] for yy in x]
            p=dict(x=x,y=x[:],kx=[[2.]*n for _ in x],ky=[[.3]*n for _ in x],source=source,boundary=[[0.]*n for _ in x])
            r=solve(p)
            errors.append(max(abs(r['field'][j][i]-math.sin(math.pi*xx)*math.sin(math.pi*yy)) for j,yy in enumerate(x) for i,xx in enumerate(x)))
            self.assertAlmostEqual(sum(r['boundary_flux']),r['integrated_source'],delta=1e-8)
            if n==9:
                for j in range(1,n-1):
                    for i in range(1,n-1):p['boundary'][j][i]=12345.
                rr=solve(p)
                self.assertTrue(compare_value(rr,r,rtol=1e-12,atol=1e-12)[0])
        self.assertTrue(all(3.8<a/b<4.2 for a,b in zip(errors,errors[1:])))

    def test_c10_discrete_fourier_exact_tangents_and_conserved_derivative(self):
        solve=candidate(C10)
        n=8;length=1.3;d=.04;k=.6;dt=.08;steps=9
        p=dict(mode='simulate',length=length,dt=dt,steps=steps,checkpoint_at=4,D=d,k=k,A0=[1+.2*math.cos(2*math.pi*i/n) for i in range(n)],B0=[.3]*n)
        r=solve(p);s=r['final'];eigenvalue=4*math.sin(math.pi/n)**2/(length/n)**2
        for i in range(n):
            mode=.2*math.cos(2*math.pi*i/n)
            a=(1+dt*k)**(-steps)+mode*(1+dt*(k+d*eigenvalue))**(-steps)
            ad=-mode*steps*dt*eigenvalue*(1+dt*(k+d*eigenvalue))**(-steps-1)
            ak=-steps*dt*(1+dt*k)**(-steps-1)-mode*steps*dt*(1+dt*(k+d*eigenvalue))**(-steps-1)
            total=1.3+mode*(1+dt*d*eigenvalue)**(-steps)
            total_d=-mode*steps*dt*eigenvalue*(1+dt*d*eigenvalue)**(-steps-1)
            for key,value in [('A',a),('B',total-a),('dA_dD',ad),('dA_dk',ak),('dB_dD',total_d-ad),('dB_dk',-ak)]:
                self.assertAlmostEqual(s[key][i],value,delta=1e-11)
        self.assertAlmostEqual(r['mass'],1.3*length,delta=1e-11)
        self.assertTrue(r['restart_equal'])
        for parameter in ('D','k'):
            self.assertAlmostEqual(sum(s['dA_d'+parameter]+s['dB_d'+parameter]),0.,delta=1e-10)
            eps=1e-6
            plus=solve(dict(p,**{parameter:p[parameter]+eps}))['final']
            minus=solve(dict(p,**{parameter:p[parameter]-eps}))['final']
            for species in ('A','B'):
                error=max(abs((a-b)/(2*eps)-c) for a,b,c in zip(plus[species],minus[species],s['d'+species+'_d'+parameter]))
                self.assertLess(error,2e-7)
        resumed=solve(dict(mode='resume',checkpoint=json.loads(json.dumps(r['checkpoint'])),steps=steps))
        self.assertEqual(resumed['final'],s)

    def test_c10_inverse_from_independent_modal_formula_and_rng(self):
        solve=candidate(C10);n=8;length=1.3;d=.04;k=.6;dt=.08
        eigenvalue=4*math.sin(math.pi/n)**2/(length/n)**2
        observations=[];jac=[]
        for step in (2,5,9,15):
            for species,i in [('A',0),('A',2),('B',4)]:
                mode=.2*math.cos(2*math.pi*i/n)
                a=(1+dt*k)**(-step)+mode*(1+dt*(k+d*eigenvalue))**(-step)
                ad=-mode*step*dt*eigenvalue*(1+dt*(k+d*eigenvalue))**(-step-1)
                ak=-step*dt*(1+dt*k)**(-step-1)-mode*step*dt*(1+dt*(k+d*eigenvalue))**(-step-1)
                total=1.3+mode*(1+dt*d*eigenvalue)**(-step)
                total_d=-mode*step*dt*eigenvalue*(1+dt*d*eigenvalue)**(-step-1)
                observations.append(dict(step=step,species=species,index=i,value=a if species=='A' else total-a,sigma=.004))
                jac.append([ad/.004,ak/.004] if species=='A' else [(total_d-ad)/.004,-ak/.004])
        p=dict(mode='infer',length=length,dt=dt,A0=[1+.2*math.cos(2*math.pi*i/n) for i in range(n)],B0=[.3]*n,bounds=[[.005,.12],[.05,1.2]],initial_guess=[.03,.4],observations=observations,bootstrap_replicates=3,bootstrap_seed=123456)
        r=solve(p)
        self.assertAlmostEqual(r['parameters'][0],d,delta=1e-8);self.assertAlmostEqual(r['parameters'][1],k,delta=1e-8)
        a=sum(row[0]**2 for row in jac);b=sum(row[0]*row[1] for row in jac);c=sum(row[1]**2 for row in jac);det=a*c-b*b
        cov=[[c/det,-b/det],[-b/det,a/det]]
        self.assertTrue(compare_value(r['covariance'],cov,rtol=1e-7,atol=1e-12)[0])
        state=123456
        for _ in range(2*3*len(observations)):state=(1664525*state+1013904223) & 0xffffffff
        self.assertEqual(r['bootstrap']['rng_state'],state)
        self.assertGreater(r['bootstrap']['covariance'][0][0],0.)
        self.assertEqual(solve(p),r)


class ExecutableContractsAndControls(unittest.TestCase):
    def test_manufactured_truth_changes_with_seed(self):
        for module,key in ((C08,'field'),(C09,'density')):
            a={c['id']:c for c in module.cases(0) if 'expected' in c}
            b={c['id']:c for c in module.cases(17) if 'expected' in c}
            changed=[cid for cid in a if a[cid]['expected'][key]!=b[cid]['expected'][key]]
            self.assertGreaterEqual(len(changed),len(a)-1)

    def test_prompts_are_independent_of_hidden_case_factory(self):
        for module in MODULES:
            with self.subTest(task=module.TASK['id']):
                with patch.object(module,'cases',side_effect=AssertionError('private cases called by prompt')):
                    text=module.prompt(91)
                self.assertIn('可见示例输入',text)
                self.assertNotIn('"expected"',text)

    def test_reference_candidates_multiple_seeds_actual_subprocess(self):
        for module in MODULES:
            if module.TASK['language']=='fortran' and not shutil.which('gfortran'):continue
            for seed in (0,17,2026):
                with self.subTest(task=module.TASK['id'],seed=seed):
                    cases=module.cases(seed)
                    self.assertEqual({tier:sum(c['weight'] for c in cases if c['tier']==tier) for tier in ('basic','scientific','stress')},{'basic':20,'scientific':30,'stress':20})
                    r=grade(module.TASK['id'],module.reference_submission(seed),seed,backend='trusted',timeout=30)
                    self.assertEqual(r['execution']['status'],'executed')
                    self.assertEqual(r['auto_points'],70,[c for c in r['checks'] if not c['passed']])
                    self.assertEqual(r['completion_status'],'pending_review')

    def test_mutants_fail_real_execution_with_scientific_score_gradient(self):
        expected={
            'C06':{'central_drift':32,'uniform_control_volume':60,'wrong_right_boundary':32},
            'C07':{'discard_baseline':6,'ignore_heteroscedastic_sigma':13,'conditional_information':13},
            'C08':{'arithmetic_interface':46,'swap_tensor_directions':26,'reverse_west_flux':6},
            'C09':{'wrong_poisson_mesh_scale':32,'remove_gauge_boundary':32,'drift_sign_reversal':22},
            'C10':{'lagged_reaction_transfer':14,'reset_checkpoint_tangents':39,'relative_sigma_covariance':50,'reuse_bootstrap_noise':60},
        }
        for module in MODULES:
            if module.TASK['language']=='fortran' and not shutil.which('gfortran'):continue
            variants=module.mutants(17)
            self.assertGreaterEqual(len(variants)-1,2)
            for label,submission in variants.items():
                if label=='reference':continue
                with self.subTest(task=module.TASK['id'],mutant=label):
                    r=grade(module.TASK['id'],submission,17,backend='trusted',timeout=30)
                    self.assertEqual(r['auto_points'],expected[module.TASK['id']][label])
                    self.assertEqual(r['completion_status'],'failed')

    def test_shipped_candidate_tests_run_as_files(self):
        for module in MODULES:
            if module.TASK['language']=='fortran' and not shutil.which('gfortran'):continue
            with self.subTest(task=module.TASK['id']),tempfile.TemporaryDirectory() as td:
                p=Path(td)
                for name,text in module.reference_submission()['artifacts'].items():(p/name).write_text(text)
                result=subprocess.run([sys.executable,str(p/'tests.py')],cwd=p,text=True,capture_output=True,timeout=20)
                self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':unittest.main()

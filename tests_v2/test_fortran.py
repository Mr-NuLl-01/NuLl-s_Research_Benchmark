"""Compiled controls and independent identities for the three V2 Fortran tasks."""
from __future__ import annotations

import copy
import math
import shutil
import unittest
from unittest.mock import patch

from nrb_v2.fortran import execute
from nrb_v2.tasks import f01, f02, f03


MODULES=(f01,f02,f03)


def outcomes(mod, submission, seed=17, selected=None):
    fixtures=mod.cases(seed) if selected is None else selected
    result=execute(mod,submission,fixtures,backend="trusted",timeout=120)
    if result["status"]!="executed":
        raise AssertionError(result)
    passed=[]
    for c,r in zip(fixtures,result["records"]):
        if "error" in c:
            ok=r.get("ok") is False and r.get("error")==c["error"]
        else:
            ok=r.get("ok") is True and mod.validate_output(c,r["value"])[0]
        passed.append(ok)
    return fixtures,result,passed


class FortranContractTests(unittest.TestCase):
    def test_missing_docker_compiler_is_environment_unscored(self):
        class Process:
            returncode=127
            stdout=""
            stderr="exec: gfortran: executable file not found"
        with patch("nrb_v2.fortran.shutil.which",return_value="/usr/bin/docker"), \
             patch("nrb_v2.fortran.subprocess.run",return_value=Process()):
            result=execute(f01,f01.reference_submission(),f01.cases(),backend="docker",image="python-only:local")
        self.assertEqual(result["status"],"unavailable")
        self.assertEqual(result["backend"],"docker")
        self.assertEqual(result["records"],[])
        self.assertIn("compiler/container unavailable",result["error"])

    def test_weights_and_public_source_only_contract(self):
        for mod in MODULES:
            fixtures=mod.cases(17)
            self.assertEqual(len({c["id"] for c in fixtures}),len(fixtures))
            self.assertEqual({tier:sum(c["weight"] for c in fixtures if c["tier"]==tier)
                              for tier in ("basic","scientific","stress")},
                             {"basic":20,"scientific":30,"stress":20})
            self.assertEqual(mod.TASK["required_artifacts"],["solution.f90"])
            self.assertFalse(mod.TASK["manual_review_required"])
            self.assertEqual(set(mod.reference_submission()["artifacts"]),{"solution.f90"})
            self.assertIn("solution.f90",mod.prompt(17))

    def test_nonrepresentable_sg_limit_is_an_explicit_rejection(self):
        case=next(c for c in f01.cases() if c["id"]=="reject_unresolved_converging_flow")
        self.assertEqual(case["error"],"ValueError")
        with self.assertRaises(ValueError):
            f01._reference(case["input"])
        self.assertIn("1e-280",f01.prompt())

    def test_f02_two_cell_closed_form_not_same_linear_solver(self):
        p=next(c["input"] for c in f02.cases() if c["id"]=="two_cells_half_boundary")
        w0,w1=p["widths"];d0,d1=p["diffusion"];dt=p["dt"][0]
        gl=2*d0/w0;gm=1/(w0/(2*d0)+w1/(2*d1));gr=2*d1/w1
        a=w0+dt*(gl+gm);c=w1+dt*(gm+gr);b=-dt*gm
        r0=w0*p["initial"][0]+dt*gl*p["left"]
        r1=w1*p["initial"][1]+dt*gr*p["right"]
        exact=[(c*r0-b*r1)/(a*c-b*b),(a*r1-b*r0)/(a*c-b*b)]
        result=f02._reference(p)
        for actual,expected in zip(result["history"][-1],exact):
            self.assertAlmostEqual(actual,expected,delta=2e-15)
        self.assertLess(result["balance_residual"],1e-14)

    def test_f02_cannot_forge_ledger_or_final_only_solution(self):
        case=next(c for c in f02.cases() if c["id"]=="nonuniform_heterogeneous_schedule")
        answer=copy.deepcopy(case["expected"])
        answer["decay_removed"]+=.01
        self.assertFalse(f02.validate_output(case,answer)[0])
        answer=copy.deepcopy(case["expected"])
        answer["history"][3][5]+=.01
        answer["balance_residual"]=answer["max_step_residual"]=0.0
        self.assertFalse(f02.validate_output(case,answer)[0])

    def test_f03_accepts_equations_not_reference_coordinate_identity(self):
        # Changing a stored target coordinate cannot determine acceptance;
        # only the problem's original boundary/positive-root equations do.
        case=copy.deepcopy(f03.cases()[0]);answer=copy.deepcopy(case["expected"])
        case["expected"]["potential"]=[999.0]*len(answer["potential"])
        self.assertTrue(f03.validate_output(case,answer)[0])
        answer["potential"][3]+=.001
        answer["residual_inf"]=0.0
        self.assertFalse(f03.validate_output(case,answer)[0])

    def test_parsers_reject_nonfinite_and_wrong_shapes(self):
        for mod in MODULES:
            self.assertEqual(mod.parse_fortran("ERROR\n"),{"error":"ValueError"})
            with self.assertRaises(ValueError):
                mod.parse_fortran("nan nan nan")
        with self.assertRaises(ValueError):
            f02.parse_fortran("2 0 1 2 3")


@unittest.skipUnless(shutil.which("gfortran"),"gfortran unavailable: native controls not run")
class FortranNativeTests(unittest.TestCase):
    def test_references_three_seeds_actual_compile(self):
        for mod in MODULES:
            for seed in (0,17,2026):
                with self.subTest(task=mod.TASK["id"],seed=seed):
                    fixtures,result,passed=outcomes(mod,mod.reference_submission(seed),seed)
                    failures=[(c["id"],r) for c,r,ok in zip(fixtures,result["records"],passed) if not ok]
                    self.assertEqual(failures,[])
                    self.assertIn("GNU Fortran",result["compiler"])

    def test_scientific_mutants_do_not_receive_full_score(self):
        for mod in MODULES:
            for name,submission in mod.mutants(17).items():
                if name=="reference":
                    continue
                with self.subTest(task=mod.TASK["id"],mutant=name):
                    fixtures,result,passed=outcomes(mod,submission)
                    self.assertFalse(all(passed))
                    self.assertTrue(any(not ok and "expected" in c for c,ok in zip(fixtures,passed)))

    def test_f01_independent_exponential_solution_and_reverse_flux(self):
        x=[0,.03,.13,.5,1.0];d=.4;v=1.3;left=.7;right=1.4
        for sign in (1,-1):
            vel=sign*v
            p=dict(x=x,diffusion=[d]*4,velocity=[vel]*4,source=[0.0]*3,decay=[0.0]*3,left=left,right=right)
            exact=[left+(right-left)*math.expm1(vel*t/d)/math.expm1(vel/d) for t in x]
            current=vel*left-vel*(right-left)/math.expm1(vel/d)
            case=dict(id="analytic",input=p)
            result=execute(f01,f01.reference_submission(),[case],backend="trusted")
            self.assertTrue(result["records"][0]["ok"])
            actual=result["records"][0]["value"]
            for a,e in zip(actual["density"],exact):
                self.assertAlmostEqual(a,e,delta=3e-13)
            for a in actual["flux"]:
                self.assertAlmostEqual(a,current,delta=3e-13)

    def test_compile_error_cannot_collect_error_case_points(self):
        bad={"task_id":"F01","answer":{},"artifacts":{"solution.f90":"this is not Fortran"}}
        fixtures,result,passed=outcomes(f01,bad)
        self.assertFalse(any(passed))
        self.assertTrue(all(r["error"]=="CompileError" for r in result["records"]))

    def test_disabled_execution_remains_unscored(self):
        result=execute(f02,f02.reference_submission(),f02.cases(),backend="none")
        self.assertEqual(result["status"],"unavailable")
        self.assertEqual(result["records"],[])


if __name__=="__main__":
    unittest.main()

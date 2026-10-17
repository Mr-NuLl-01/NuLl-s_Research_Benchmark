"""Independent scoped scientific checks and executable negative controls for C01–C05."""
from __future__ import annotations
import cmath
import copy
import importlib
import json
import math
import unittest

MODULES = [importlib.import_module(f"nrb_v1.tasks.c{i:02d}") for i in range(1, 6)]


def candidate(source):
    namespace = {"__name__": "candidate_solution"}
    exec(compile(source, "solution.py", "exec"), namespace)
    return namespace["solve"]


def close(actual, expected, rtol=2e-9, atol=2e-11):
    if isinstance(expected, dict):
        return isinstance(actual, dict) and actual.keys() == expected.keys() and all(close(actual[k], v, rtol, atol) for k, v in expected.items())
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(close(a, e, rtol, atol) for a, e in zip(actual, expected))
    if isinstance(expected, float):
        return isinstance(actual, (int, float)) and not isinstance(actual, bool) and math.isfinite(actual) and math.isclose(actual, expected, rel_tol=rtol, abs_tol=atol)
    return type(actual) is type(expected) and actual == expected


class ContractsAndControls(unittest.TestCase):
    def test_case_tiers_weights_and_reference_execution(self):
        for module in MODULES:
            for seed in (0, 17, 2026):
                with self.subTest(task=module.TASK["id"], seed=seed):
                    cases = module.cases(seed)
                    self.assertEqual({tier: sum(c["weight"] for c in cases if c["tier"] == tier) for tier in ("basic", "scientific", "stress")}, {"basic": 20, "scientific": 30, "stress": 20})
                    run = candidate(module.reference_submission(seed)["artifacts"]["solution.py"])
                    for case in cases:
                        original = copy.deepcopy(case["input"])
                        if "error" in case:
                            with self.assertRaises(ValueError):
                                run(copy.deepcopy(original))
                        else:
                            result = run(case["input"])
                            self.assertTrue(close(result, case["expected"], case["rtol"], case["atol"]), case["id"])
                            json.dumps(result, allow_nan=False)
                            self.assertEqual(case["input"], original, case["id"])
                    prompt = module.prompt(seed)
                    self.assertIn("可见示例输入", prompt)
                    self.assertNotIn('"expected"', prompt)

    def test_each_mutant_fails_actual_execution(self):
        for module in MODULES:
            cases = module.cases(17)
            self.assertGreaterEqual(len(module.mutants()) - 1, 2)
            for label, entry in module.mutants().items():
                if label == "reference":
                    continue
                with self.subTest(task=module.TASK["id"], mutant=label):
                    run = candidate(entry["artifacts"]["solution.py"])
                    failures = []
                    for case in cases:
                        try:
                            result = run(copy.deepcopy(case["input"]))
                            passed = "error" not in case and close(result, case["expected"], case["rtol"], case["atol"])
                        except Exception as exc:
                            passed = case.get("error") == type(exc).__name__
                        if not passed:
                            failures.append(case["id"])
                    self.assertTrue(failures, "Mutant survived all executable cases")

    def test_candidate_sample_tests_are_executable(self):
        import sys
        import types
        for module in MODULES:
            with self.subTest(task=module.TASK["id"]):
                solution = types.ModuleType("solution")
                exec(compile(module.SOURCE, "solution.py", "exec"), solution.__dict__)
                old = sys.modules.get("solution")
                sys.modules["solution"] = solution
                try:
                    exec(compile(module.SAMPLE_TESTS, "tests.py", "exec"), {})
                finally:
                    if old is None:
                        sys.modules.pop("solution", None)
                    else:
                        sys.modules["solution"] = old


class IndependentScientificProperties(unittest.TestCase):
    def test_c01_known_inverse_variance_and_duplicate_identity(self):
        solve = candidate(MODULES[0].SOURCE)
        header = "sample,replicate,value,unit,sigma,status\n"
        p = {"csv": header + "x,r1,0,C,1,ok\nx,r2,277.15,K,2,ok\nx,r2,NA,mK,1,ok\n"}
        r = solve(p)
        group = r["samples"][0]
        self.assertAlmostEqual(group["mean_K"], 273.95, places=11)
        self.assertAlmostEqual(group["standard_error_K"], math.sqrt(0.8), places=12)
        self.assertAlmostEqual(group["chi2"], 3.2, places=10)
        self.assertEqual((r["n_usable"], r["n_skipped"]), (2, 1))
        empty = solve({"csv": header + "x,r,NA,bad,0,ok\n"})
        self.assertEqual(empty, {"samples": [], "n_usable": 0, "n_skipped": 1})

    def test_c02_independent_bootstrap_and_permutation(self):
        solve = candidate(MODULES[1].SOURCE)
        rows = [dict(stratum="a", group="x", repeat="1", loss_a=5, loss_b=1),
                dict(stratum="a", group="x", repeat="2", loss_a=1, loss_b=1),
                dict(stratum="a", group="y", repeat="1", loss_a=1, loss_b=2),
                dict(stratum="b", group="z", repeat="1", loss_a=3, loss_b=2)]
        p = dict(rows=rows, bootstrap_replicates=7, seed=123)
        r = solve(p)
        # Group values a=[2,-1], b=[1]; target equal-weights the two strata.
        self.assertEqual(r["estimate"], 0.75)
        state, values = 123, []
        for _ in range(7):
            selections=[]
            for _ in range(2):
                state=(1664525*state+1013904223) & 0xffffffff
                selections.append([2,-1][state >> 31])
            state=(1664525*state+1013904223) & 0xffffffff  # singleton stratum still consumes RNG
            values.append((sum(selections)/2+1)/2)
        ordered = sorted(values)
        self.assertAlmostEqual(r["ci95"][0], ordered[0]+0.15*(ordered[1]-ordered[0]))
        self.assertAlmostEqual(r["ci95"][1], ordered[5]+0.85*(ordered[6]-ordered[5]))
        self.assertEqual(r["bootstrap_nonpositive_fraction"], (1+sum(v <= 0 for v in values))/8)
        self.assertEqual(r, solve({**p, "rows": list(reversed(rows))}))

    def test_c03_two_cell_mode_and_exact_energy_balance(self):
        solve = candidate(MODULES[2].SOURCE)
        p = dict(dx_m=[0.4,0.4], k_W_mK=[2,2], capacity_J_m3K=[3,3], initial_K=[4,2], source_W_m3=[0,0], left={"kind":"insulated"}, right={"kind":"insulated"}, dt_s=0.2, steps=4)
        r=solve(p)
        factor = (1+2*(2/0.4)*0.2/(3*0.4))**-4
        self.assertAlmostEqual(r["temperature_K"][0], 3+factor, places=12)
        self.assertAlmostEqual(r["temperature_K"][1], 3-factor, places=12)
        self.assertAlmostEqual(r["energy_change_J_m2"], 0, places=12)
        for case in MODULES[2].cases():
            if "expected" in case:
                value=solve(case["input"])
                self.assertAlmostEqual(value["energy_change_J_m2"], value["boundary_energy_J_m2"]+value["source_energy_J_m2"], delta=2e-7)
                if all(v == 0 for v in case["input"]["source_W_m3"]):
                    boundary_t=[v["temperature_K"] for v in [case["input"]["left"],case["input"]["right"]] if v["kind"]=="fixed"]
                    self.assertGreaterEqual(min(value["temperature_K"]), min(case["input"]["initial_K"]+boundary_t)-1e-8)
                    self.assertLessEqual(max(value["temperature_K"]), max(case["input"]["initial_K"]+boundary_t)+1e-8)

    def test_c04_independent_characteristic_matrices(self):
        solve=candidate(MODULES[3].SOURCE)
        # Independent field/flux characteristic matrices, not the reference recursion.
        for pol in ("s", "p"):
            p=dict(indices=[[1,0],[1.46,0],[2.2,0.13],[0.6,3.7],[1.52,0]], thickness_nm=[95,137,24], angle_deg=53, polarization=pol, wavelengths_nm=[400,550,800])
            n=[complex(*pair) for pair in p["indices"]]
            u=math.sin(math.radians(53))
            w=[cmath.sqrt(v*v-u*u) for v in n]
            q=w if pol=="s" else [v*v/z for v,z in zip(n,w)]
            for wl, result in zip(p["wavelengths_nm"], solve(p)["spectra"]):
                a,b,c,d=1+0j,0j,0j,1+0j
                for index, thick in enumerate(p["thickness_nm"],1):
                    delta=2*math.pi*w[index]*thick/wl
                    cc,ss=cmath.cos(delta),cmath.sin(delta)
                    aa,bb,ccc,dd=cc,-1j*ss/q[index],-1j*q[index]*ss,cc
                    a,b,c,d=a*aa+b*ccc,a*bb+b*dd,c*aa+d*ccc,c*bb+d*dd
                den=q[0]*(a+b*q[-1])+c+d*q[-1]
                rr=(q[0]*(a+b*q[-1])-c-d*q[-1])/den
                tt=2*q[0]/den
                self.assertAlmostEqual(abs(complex(*result["r"])-rr),0,delta=2e-12)
                self.assertAlmostEqual(abs(complex(*result["t"])-tt),0,delta=2e-12)
                self.assertGreaterEqual(result["A"],-1e-12)

    def test_c04_lossless_and_opaque_limits(self):
        solve=candidate(MODULES[3].SOURCE)
        for pol in ("s","p"):
            for angle in (0,32,71):
                p=dict(indices=[[1,0],[2.1,0],[1.33,0],[1.5,0]],thickness_nm=[121,377],angle_deg=angle,polarization=pol,wavelengths_nm=[390,650,1100])
                self.assertTrue(all(abs(r["R"]+r["T"]-1)<2e-12 for r in solve(p)["spectra"]))
            p=dict(indices=[[1,0],[0.4,8],[1.5,0]],thickness_nm=[1e12],angle_deg=0,polarization=pol,wavelengths_nm=[550])
            r=solve(p)["spectra"][0]
            expected=abs((1-complex(0.4,8))/(1+complex(0.4,8)))**2
            self.assertAlmostEqual(r["R"],expected,delta=1e-13)
            self.assertEqual(r["T"],0)

    def test_c05_conservation_exact_forcing_and_analytic_decay(self):
        solve=candidate(MODULES[4].SOURCE)
        p=dict(t0_s=0,t1_s=0.4,initial=[1,0],rates_s_inv=[100,3,0],source_schedule=[[0,0]],observation_times_s=[0,0.02,0.4],initial_step_s=0.4,atol=1e-8,rtol=1e-6)
        r=solve(p)
        self.assertGreater(r["rejected_steps"],0)
        for point in r["observations"]:
            self.assertAlmostEqual(sum(point["state"]),1,delta=2e-11)
            exact=3/103+100/103*math.exp(-103*point["time_s"])
            # First-order global error is broader than the local tolerance.
            self.assertAlmostEqual(point["state"][0],exact,delta=2e-4)
            self.assertGreaterEqual(min(point["state"]),0)
        p.update(initial=[0,0],rates_s_inv=[0,0,0],source_schedule=[[0,2],[0.1,5]],observation_times_s=[0,0.1,0.4])
        r=solve(p)
        self.assertAlmostEqual(r["observations"][1]["state"][0],0.2,delta=1e-13)
        self.assertAlmostEqual(r["observations"][2]["state"][0],1.7,delta=1e-13)

    def test_c05_clock_translation_invariance(self):
        solve=candidate(MODULES[4].SOURCE)
        # Binary-exact timestamps ensure the shifted input interval is identical.
        p=dict(t0_s=0,t1_s=0.015625,initial=[1,0],rates_s_inv=[3,2,0],source_schedule=[[0,0],[0.0078125,1]],observation_times_s=[0,0.0078125,0.015625],initial_step_s=1e-6,atol=1e-7,rtol=1e-5)
        r=solve(p)
        p["t0_s"]+=2**40
        p["t1_s"]+=2**40
        p["source_schedule"]=[[t+2**40,q] for t,q in p["source_schedule"]]
        p["observation_times_s"]=[t+2**40 for t in p["observation_times_s"]]
        shifted=solve(p)
        self.assertEqual((r["accepted_steps"],r["rejected_steps"]),(shifted["accepted_steps"],shifted["rejected_steps"]))
        self.assertEqual([v["state"] for v in r["observations"]],[v["state"] for v in shifted["observations"]])


if __name__ == "__main__":
    unittest.main()

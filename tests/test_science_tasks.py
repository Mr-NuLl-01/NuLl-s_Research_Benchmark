"""Independent arithmetic oracles and discriminating mutants for four tasks.

These tests validate task mechanics; they are not AI/harness performance measurements.
"""
from __future__ import annotations

import copy
import csv
import io
import itertools
import json
import math
from fractions import Fraction
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import unittest

from nrb.tasks import t01, t02, t03, t08


MODULES = (t01, t02, t03, t08)


def score(module, case, submission):
    return sum(c["points"] for c in module.grade(case, submission) if c["passed"] is True)


def rational_solve(matrix, rhs):
    """Fraction-only Gaussian elimination used independently of task code."""
    a = [[Fraction(str(x)) for x in row]+[Fraction(str(b))] for row, b in zip(matrix, rhs)]
    for k in range(len(rhs)):
        row = next(i for i in range(k, len(rhs)) if a[i][k] != 0)
        a[k], a[row] = a[row], a[k]
        for i in range(k+1, len(rhs)):
            f = a[i][k]/a[k][k]
            for j in range(k, len(rhs)+1):
                a[i][j] -= f*a[k][j]
    x = [Fraction(0)]*len(rhs)
    for i in reversed(range(len(rhs))):
        x[i] = (a[i][-1]-sum(a[i][j]*x[j] for j in range(i+1, len(rhs))))/a[i][i]
    return x


class TaskContractTests(unittest.TestCase):
    def test_references_and_seeds(self):
        for module in MODULES:
            serializations = set()
            for seed in (0, 1, 2, 17, 100, -7):
                case = module.build(seed)
                with self.subTest(task=case["id"], seed=seed):
                    self.assertEqual(case, module.build(seed))
                    self.assertEqual(case["seed"], seed)
                    self.assertEqual(len(case["rubric"]), 3)
                    for criterion in case["rubric"]:
                        self.assertEqual(set(criterion["anchors"]), {"0", "5", "10"})
                    result = module.reference(case)
                    checks = module.grade(case, result)
                    self.assertEqual(sum(c["points"] for c in checks), 70)
                    self.assertEqual(len({c["id"] for c in checks}), len(checks))
                    self.assertEqual(score(module, case, result), 70)
                    self.assertEqual(score(module, case, {}), 0)
                    serializations.add(json.dumps(case["files"], sort_keys=True))
            self.assertEqual(len(serializations), 6)

    def test_malformed_answers_do_not_crash(self):
        bad_values = [None, {}, [], "wrong", float("nan"), float("inf"), True, 10**400]
        for module in MODULES:
            case = module.build(0)
            ref = module.reference(case)
            for whole in (None, [], "text", {"answer": []}):
                with self.subTest(task=case["id"], whole=type(whole).__name__):
                    self.assertEqual(sum(c["points"] for c in module.grade(case, whole)), 70)
            for key in ref["answer"]:
                for bad in bad_values:
                    mutant = copy.deepcopy(ref)
                    mutant["answer"][key] = bad
                    with self.subTest(task=case["id"], field=key, bad=type(bad).__name__):
                        self.assertEqual(sum(c["points"] for c in module.grade(case, mutant)), 70)


class EvidenceTaskTests(unittest.TestCase):
    def test_visible_table_statistics(self):
        case = t01.build(37)
        rows = list(csv.DictReader(io.StringIO(case["files"]["corrected_table.csv"])))
        before = [Fraction(r["baseline_error_K"]) for r in rows]
        after = [Fraction(r["corrected_error_K"]) for r in rows]
        differences = [b-a for b, a in zip(before, after)]
        mean_before, mean_after = sum(before)/len(rows), sum(after)/len(rows)
        mean_d = sum(differences)/len(rows)
        se_squared = sum((x-mean_d)**2 for x in differences)/(len(rows)*(len(rows)-1))
        answer = t01.reference(case)["answer"]
        values = answer["calculations"]
        self.assertAlmostEqual(values["mean_baseline_K"], float(mean_before), places=12)
        self.assertAlmostEqual(values["mean_corrected_K"], float(mean_after), places=12)
        self.assertAlmostEqual(values["relative_reduction_percent"],
                               float(100*(mean_before-mean_after)/mean_before), places=11)
        self.assertAlmostEqual(values["paired_standard_error_K"], math.sqrt(float(se_squared)), places=12)

    def test_source_verdicts_materially_vary(self):
        seen = {cid: set() for cid in ("C1", "C3", "C4", "C5")}
        for seed in range(16):
            a = t01.reference(t01.build(seed))["answer"]
            for cid in seen:
                seen[cid].add(a["claims"][cid]["verdict"])
        for cid, values in seen.items():
            self.assertGreater(len(values), 1, cid)

    def test_pseudoreplication_and_citation_spam_lose_points(self):
        case = t01.build(0)
        ref = t01.reference(case)
        mutant = copy.deepcopy(ref)
        a = mutant["answer"]
        a["independent_units"] *= 3
        a["calculations"]["paired_standard_error_K"] /= math.sqrt(3)
        a["claims"]["C2"]["verdict"] = "supported"
        for row in a["claims"].values():
            row["sources"] = list(a["source_roles"])
        self.assertLessEqual(score(t01, case, mutant), 45)

    def test_fake_source_is_not_credit(self):
        case = t01.build(1)
        mutant = t01.reference(case)
        mutant["answer"]["claims"]["C1"]["sources"] = ["doi:10.fake/not-a-source"]
        checks = {c["id"]: c for c in t01.grade(case, mutant)}
        self.assertFalse(checks["C1_sources"]["passed"])


class ThermalTaskTests(unittest.TestCase):
    def test_response_equivalence_for_nonstep_input(self):
        case = t02.build(8)
        a = t02.reference(case)["answer"]
        c, g, alpha = [a["recovered"][k] for k in ("C_J_per_K", "G_W_per_K", "sensor_gain")]
        b = a["baseline"]["offset"]
        scaled_c, scaled_g, scaled_alpha = (v*3.7 for v in (c, g, alpha))
        theta = scaled_theta = 0.0
        # Segment-by-segment exact ODE integration; unequal powers and durations.
        for power, duration in [(2.0, 1.3), (0.0, 7.5), (5.5, 2.7), (1.2, 11.0)]:
            decay = math.exp(-g*duration/c)
            theta = theta*decay+power/g*(1-decay)
            decay_scaled = math.exp(-scaled_g*duration/scaled_c)
            scaled_theta = scaled_theta*decay_scaled+power/scaled_g*(1-decay_scaled)
            self.assertAlmostEqual(b+alpha*theta, b+scaled_alpha*scaled_theta, places=13)

    def test_recovered_parameters_predict_all_visible_points(self):
        case = t02.build(29)
        a = t02.reference(case)["answer"]
        c, g, alpha = [a["recovered"][k] for k in ("C_J_per_K", "G_W_per_K", "sensor_gain")]
        b = a["baseline"]["offset"]
        for filename in ["baseline.json", "intervention_observations.json"]:
            data = json.loads(case["files"][filename])
            local_c = c+data.get("added_capacity_J_per_K", 0)
            for t, y in data["observations"]:
                predicted = b+alpha*data["power_W"]/g*(1-math.exp(-g*t/local_c))
                self.assertAlmostEqual(y, predicted, places=10)

    def test_more_data_is_not_new_structural_information(self):
        case = t02.build(0)
        mutant = t02.reference(case)
        a = mutant["answer"]
        wrong = next(k for k, rank in a["rank_after_interventions"].items() if rank == 3)
        a["chosen_intervention"] = wrong
        a["structural_rank"] = 4
        a["scale_powers_C_G_gain_offset"] = [0, 0, 0, 0]
        a["nonidentifiable_parameters"] = []
        self.assertEqual(score(t02, case, mutant), 50)

    def test_sensor_offset_must_not_decay(self):
        case = t02.build(3)
        mutant = t02.reference(case)
        a = mutant["answer"]
        pred = json.loads(case["files"]["prediction.json"])
        t1, t2 = pred["observation_times_s"]
        a["prediction_readings"][1] = a["prediction_readings"][0]*math.exp(-(t2-t1)/a["baseline"]["tau_s"])
        self.assertEqual(score(t02, case, mutant), 65)


class DesignTaskTests(unittest.TestCase):
    def test_exact_fraction_enumeration_with_centered_information(self):
        case = t03.build(0)
        p = json.loads(case["files"]["design.json"])
        x = list(map(Fraction, p["x"]))
        inv = [[1/Fraction(str(v)) for v in row] for row in p["variance_scenarios"]]
        rows = []
        for ns in itertools.product(*(range(cap+1) for cap in p["max_replicates"])):
            if not p["min_total"] <= sum(ns) <= p["max_total"]:
                continue
            if sum(n*c for n, c in zip(ns, p["costs"])) > p["budget"]:
                continue
            if ns[2] < p["min_center"] or sum(ns[:2]) < p["min_each_side"] or sum(ns[3:]) < p["min_each_side"]:
                continue
            if ns[0]+ns[4] > p["max_extreme_total"]:
                continue
            vv = []
            for inv_v in inv:
                ws = [n*v for n, v in zip(ns, inv_v)]
                center = sum(w*xi for w, xi in zip(ws, x))/sum(ws)
                info = sum(w*(xi-center)**2 for w, xi in zip(ws, x))
                vv.append(1/info)
            rows.append((max(vv), ns))
        rows.sort()
        best = rows[0]
        second = next(row for row in rows if float(row[0]-best[0]) > 1e-12)
        a = t03.reference(case)["answer"]
        self.assertEqual(a["feasible_allocation_count"], len(rows))
        self.assertAlmostEqual(a["worst_slope_variance"], float(best[0]), places=12)
        self.assertAlmostEqual(a["second_distinct_objective"], float(second[0]), places=12)
        self.assertEqual(tuple(a["allocation"]), best[1])

    def test_reference_script_runs_without_benchmark_imports(self):
        case = t03.build(2)
        ref = t03.reference(case)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/"solve.py").write_text(ref["artifacts"]["solve.py"], encoding="utf-8")
            (root/"design.json").write_text(case["files"]["design.json"], encoding="utf-8")
            result = subprocess.run([sys.executable, "solve.py", "design.json"], cwd=root,
                                    text=True, capture_output=True, check=True, timeout=20)
        data = json.loads(result.stdout)
        self.assertEqual(data["allocation"], ref["answer"]["allocation"])
        self.assertEqual(data["feasible_count"], ref["answer"]["feasible_allocation_count"])

    def test_average_scenario_optimization_is_distinguished(self):
        case = t03.build(0)
        p = json.loads(case["files"]["design.json"])
        average_designs = []
        for ns in itertools.product(*(range(k+1) for k in p["max_replicates"])):
            if not t03._constraints(ns, p):
                continue
            vv = t03._variances(ns, p)
            average_designs.append((sum(vv)/3, ns, vv))
        _, ns, vv = min(average_designs)
        mutant = t03.reference(case)
        a = mutant["answer"]
        a.update(allocation=list(ns), total_cost=sum(n*c for n, c in zip(ns, p["costs"])),
                 total_measurements=sum(ns), scenario_slope_variances=vv,
                 worst_slope_variance=max(vv), worst_scenario=vv.index(max(vv))+1)
        checks = {c["id"]: c for c in t03.grade(case, mutant)}
        self.assertFalse(checks["global_optimality"]["passed"])
        self.assertEqual(score(t03, case, mutant), 60)

    def test_reported_optimum_does_not_hide_infeasible_allocation(self):
        case = t03.build(5)
        mutant = t03.reference(case)
        mutant["answer"]["allocation"] = [100, 100, 100, 100, 100]
        checks = {c["id"]: c for c in t03.grade(case, mutant)}
        self.assertFalse(checks["all_design_constraints"]["passed"])
        self.assertFalse(checks["global_optimality"]["passed"])


class ContractionTaskTests(unittest.TestCase):
    def test_fraction_oracle_for_certificate(self):
        for seed in (0, 4, 21):
            case = t08.build(seed)
            p = json.loads(case["files"]["affine.json"])
            a = [[Fraction(str(x)) for x in row] for row in p["A"]]
            b = [Fraction(str(x)) for x in p["b"]]
            x = [Fraction(str(v)) for v in p["x_hat"]]
            w = list(map(Fraction, p["weights"]))
            q = max(sum(abs(v)*wj/wi for v, wj in zip(row, w)) for row, wi in zip(a, w))
            iminus = [[Fraction(int(i == j))-a[i][j] for j in range(3)] for i in range(3)]
            star = rational_solve(iminus, b)
            residual = [sum(v*y for v, y in zip(row, x))+bi-xi for row, bi, xi in zip(a, b, x)]
            rnorm = max(abs(r)/wi for r, wi in zip(residual, w))
            error = max(abs(xi-si)/wi for xi, si, wi in zip(x, star, w))
            bound = rnorm/(1-q)
            self.assertLess(q, 1)
            self.assertLessEqual(error, bound)
            expected = t08.reference(case)["answer"]
            self.assertAlmostEqual(expected["weighted_operator_norm"], float(q), places=13)
            self.assertAlmostEqual(expected["certified_weighted_error_bound"], float(bound), places=12)
            for calculated, exact in zip(expected["fixed_point"], star):
                self.assertAlmostEqual(calculated, float(exact), places=11)

    def test_alternate_valid_counterexample_is_accepted(self):
        case = t08.build(0)
        answer = t08.reference(case)
        ce = {"A": [[0.2, 3.0], [0.0, 0.4]], "b": [0.0, 0.0], "x_hat": [3.75, 1.0],
              "fixed_point": [0.0, 0.0], "spectral_radius": 0.4,
              "residual_infinity_norm": 0.6, "actual_infinity_error": 3.75, "claimed_bound": 1.0}
        answer["answer"]["counterexample"] = ce
        self.assertEqual(score(t08, case, answer), 70)

    def test_non_counterexample_is_rejected(self):
        case = t08.build(0)
        mutant = t08.reference(case)
        ce = {"A": [[0.5, 0.0], [0.0, 0.5]], "b": [0.0, 0.0], "x_hat": [2.0, 1.0],
              "fixed_point": [0.0, 0.0], "spectral_radius": 0.5,
              "residual_infinity_norm": 1.0, "actual_infinity_error": 2.0, "claimed_bound": 2.0}
        mutant["answer"]["counterexample"] = ce
        checks = {c["id"]: c for c in t08.grade(case, mutant)}
        self.assertFalse(checks["counterexample_validity"]["passed"])
        self.assertTrue(checks["counterexample_calculations"]["passed"])
        self.assertEqual(score(t08, case, mutant), 60)

    def test_residual_is_not_error_certificate(self):
        case = t08.build(0)
        mutant = t08.reference(case)
        mutant["answer"]["certified_weighted_error_bound"] = mutant["answer"]["weighted_residual_norm"]
        self.assertEqual(score(t08, case, mutant), 60)


if __name__ == "__main__":
    unittest.main()

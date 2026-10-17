"""v0.2 numerical contracts and narrowly scoped submitted-code controls.

Only repository-owned sources execute under the trusted backend. The invalid
input controls change one validation responsibility at a time: for the matching
class they return normally instead of raising the API-required ValueError.
They do not obtain credit merely because the reference validator rejects data.
"""

from __future__ import annotations

import csv
import io
import json
import math
import random
import unittest
from unittest.mock import patch

from nrb.checks import numbers_close
from nrb.execution import run_python
from nrb.tasks import t04, t05, t06


def earned(rows):
    return sum(row["points"] for row in rows if row["passed"] is True)


def case_outcomes(rows):
    return {item["id"]: item["passed"] for row in rows for item in row.get("cases", [])}


def materialize(value):
    if isinstance(value, dict):
        if set(value) == {"__nrb_float__"}:
            return float(value["__nrb_float__"])
        return {key: materialize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [materialize(item) for item in value]
    return value


def walk(value):
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def invalid_acceptor(module, predicate):
    """Wrong candidate: suppress only the selected class's ValueError."""
    return module.REFERENCE_SOURCE + '''
_validated_solve = solve
def _walk(value):
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)
def solve(p):
    try:
        return _validated_solve(p)
    except ValueError:
        if ''' + predicate + ''':
            return {}
        raise
'''


COMMON_CONTROLS = (
    ("boolean numeric input", "any(isinstance(v, bool) for v in _walk(p))"),
    ("nonfinite numeric input", "any(isinstance(v, float) and not math.isfinite(v) for v in _walk(p))"),
)


class GroupedBehaviorContracts(unittest.TestCase):
    def test_expanded_cases_are_partitioned_into_exactly_ten_five_point_groups(self):
        for module in (t04, t05):
            for seed in (0, 17, 101):
                with self.subTest(task=module.__name__, seed=seed):
                    case = module.build(seed)
                    hidden = case["expected"]["hidden"]
                    groups = case["expected"]["hidden_groups"]
                    self.assertEqual(len(groups), 10)
                    grouped = [name for members in groups.values() for name in members]
                    self.assertEqual(len(grouped), len(set(grouped)))
                    self.assertEqual(set(grouped), {name for name, _, _ in hidden})
                    # Nonfinite values are not injected into strict JSON transport.
                    json.dumps(hidden, allow_nan=False)
                    checks = module.grade(case, module.reference(case), execution="trusted")
                    self.assertEqual(sum(row["points"] for row in checks), 70)
                    behavior = [row for row in checks if "cases" in row]
                    self.assertEqual(len(behavior), 10)
                    self.assertEqual(sum(row["points"] for row in behavior), 50)
                    self.assertEqual(earned(checks), 70, checks)
                    self.assertEqual(len(case_outcomes(checks)), len(hidden))

    def test_unavailable_execution_and_missing_code_keep_fifty_point_weight(self):
        for module in (t04, t05):
            case = module.build(17)
            rows = module.grade(case, module.reference(case), execution="none")
            self.assertEqual(sum(row["points"] for row in rows if row["passed"] is None), 50)
            submission = module.reference(case)
            del submission["artifacts"]["solution.py"]
            rows = module.grade(case, submission, execution="none")
            self.assertEqual(len(rows), 14)
            self.assertEqual(sum(row["points"] for row in rows), 70)
            self.assertEqual(earned(rows), 20)
            self.assertFalse(any(row["passed"] is None for row in rows))

    def assert_validation_controls(self, module, controls, separately_covered=()):
        case = module.build(17)
        hidden = case["expected"]["hidden"]
        new_invalid = {name for name, _, state in hidden[10:] if state == "ValueError"}
        covered = set(separately_covered)
        for label, predicate in COMMON_CONTROLS + controls:
            with self.subTest(task=module.__name__, responsibility=label):
                selected = {
                    name for name, payload, state in hidden if state == "ValueError"
                    and eval(predicate, {"_walk": walk, "math": math, "p": materialize(payload)})
                }
                self.assertTrue(selected, label)
                submission = module.reference(case)
                submission["artifacts"]["solution.py"] = invalid_acceptor(module, predicate)
                rows = module.grade(case, submission, execution="trusted")
                outcomes = case_outcomes(rows)
                self.assertEqual({name for name, passed in outcomes.items() if not passed}, selected)
                covered.update(selected)
                self.assertLess(earned(rows), 70)
                for row in rows:
                    failed = [entry["id"] for entry in row.get("cases", []) if not entry["passed"]]
                    for name in failed:
                        self.assertIn(name, row["detail"])
                    if "cases" in row:
                        self.assertEqual(row["points"], 5)
                        self.assertEqual(row["passed"], not failed)
        self.assertLessEqual(new_invalid, covered, "Every added rejection class needs a submitted-code control")

    def test_t04_added_invalid_classes_reject_narrowly_wrong_candidates(self):
        self.assert_validation_controls(t04, (
            ("cell array shape", "any(not isinstance(p[k], list) or len(p[k]) != len(p['edges'])-1 for k in ('conductivity','capacity','temperature','source'))"),
            ("edge container and length", "not isinstance(p['edges'], list) or len(p['edges']) < 2"),
            ("nonpositive conductivity", "any(isinstance(v,(int,float)) and not isinstance(v,bool) and v <= 0 for v in p['conductivity'])"),
            ("nonpositive capacity", "any(isinstance(v,(int,float)) and not isinstance(v,bool) and v <= 0 for v in p['capacity'])"),
            ("boundary kind and object", "any(not isinstance(b,dict) or b.get('kind') not in ('flux','temperature') or 'value' not in b for b in (p['left'],p['right']))"),
            ("integer steps", "not isinstance(p['steps'],int) or isinstance(p['steps'],bool) or p['steps'] < 0"),
            ("positive dt", "isinstance(p['dt'],(int,float)) and p['dt'] <= 0"),
        ), separately_covered=("reject_unstable_zero_step_single_cell", "reject_above_stability_threshold"))
        # Stability validity is checked with an analytic single-cell bound,
        # separately from invalid-shape/NaN predicates that cannot be divided.
        case = t04.build(17)
        source = t04.REFERENCE_SOURCE.replace("dt_bound*(1+1e-12)", "dt_bound*100")
        submission = t04.reference(case)
        submission["artifacts"]["solution.py"] = source
        outcomes = case_outcomes(t04.grade(case, submission, execution="trusted"))
        for name in ("reject_unstable_step", "reject_unstable_zero_step_single_cell", "reject_above_stability_threshold"):
            self.assertFalse(outcomes[name])

    def test_t05_added_invalid_classes_reject_narrowly_wrong_candidates(self):
        self.assert_validation_controls(t05, (
            ("negative rates", "any(isinstance(v,(int,float)) and not isinstance(v,bool) and v < 0 for v in (p['rates'] if isinstance(p['rates'],list) else [p['rates']]))"),
            ("step bounds", "all(isinstance(p[k],(int,float)) and not isinstance(p[k],bool) and math.isfinite(p[k]) for k in ('t_end','dt_min','dt_initial','dt_max')) and (p['t_end'] < 0 or p['dt_min'] <= 0 or not p['dt_min'] <= p['dt_initial'] <= p['dt_max'])"),
            ("continuation time ordering", "isinstance(p.get('t_start',0),(int,float)) and p.get('t_start',0) > p['t_end']"),
            ("integer trial budget", "not isinstance(p['max_trials'],int) or isinstance(p['max_trials'],bool) or p['max_trials'] < 1"),
            ("tolerance sign", "any(isinstance(v,(int,float)) and (v <= 0 if k=='atol' else v < 0) for k in ('atol','rtol','scale_floor') for v in (p[k] if isinstance(p[k],list) else [p[k]]))"),
            ("vector shape", "(isinstance(p['y0'],list) and not p['y0']) or any(isinstance(p[k],list) and len(p[k]) != (len(p['y0']) if isinstance(p['y0'],list) else 1) for k in ('rates','atol','rtol','scale_floor'))"),
        ))


class AnalyticBoundaryContracts(unittest.TestCase):
    def test_single_cell_dirichlet_has_both_boundary_conductances(self):
        p = {"edges": [0.0, 2.0], "conductivity": [4.0], "capacity": [3.0],
             "temperature": [5.0], "source": [2.0], "dt": 0.1, "steps": 1,
             "left": {"kind": "temperature", "value": 1.0},
             "right": {"kind": "temperature", "value": 7.0}}
        expected = {"temperature": [74/15], "face_flux": [-236/15, -124/15],
                    "energy_initial": 30.0, "energy_final": 29.6, "energy_input": -0.4}
        self.assertTrue(numbers_close(t04._oracle(p), expected))
        result = run_python(t04.REFERENCE_SOURCE, p, execution="trusted")
        self.assertEqual(result["status"], "ok")
        self.assertTrue(numbers_close(result["result"], expected))
        case = t04.build(17)
        source = t04.REFERENCE_SOURCE.replace(
            '2*k[-1]/widths[-1] if right["kind"] == "temperature" else 0.0',
            '2*k[-1]/widths[-1] if right["kind"] == "temperature" and n > 1 else 0.0')
        submission = t04.reference(case)
        submission["artifacts"]["solution.py"] = source
        outcomes = case_outcomes(t04.grade(case, submission, execution="trusted"))
        self.assertFalse(outcomes["one_cell_temperature_both"])
        self.assertFalse(outcomes["one_cell_temperature_right"])

    def test_t04_stability_tolerance_is_inclusive_at_the_binary64_threshold(self):
        case = t04.build(17)
        submission = t04.reference(case)
        submission["artifacts"]["solution.py"] = t04.REFERENCE_SOURCE.replace("dt_bound*(1+1e-12)", "dt_bound")
        rows = t04.grade(case, submission, execution="trusted")
        self.assertFalse(case_outcomes(rows)["stability_threshold_inclusive"])

    def test_E_one_is_inclusive_and_the_next_float_above_one_is_rejected(self):
        case = t05.build(17)
        cases = {name: p for name, p, state in case["expected"]["hidden"] if name.startswith("acceptance_error_")}
        for tag, accepted in (("exact", True), ("below", True), ("above", False)):
            with self.subTest(error=tag):
                result = t05._oracle(cases["acceptance_error_"+tag+"_one"])
                attempt = result["attempts"][0]
                self.assertEqual(attempt["accepted"], accepted)
                self.assertEqual(attempt["y_trial"], [3.0])
                self.assertEqual(result["y"], [3.0] if accepted else [12.0])
                self.assertEqual(result["status"], "finished" if accepted else "dt_min_reached")
                if tag == "exact":
                    self.assertEqual(attempt["error"], 1.0)
        for source, rejected_case in (
            (t05.REFERENCE_SOURCE.replace("error <= 1.0", "error < 1.0"), "acceptance_error_exact_one"),
            (t05.REFERENCE_SOURCE.replace("error <= 1.0", "error <= 1.0+1e-12"), "acceptance_error_above_one"),
        ):
            submission = t05.reference(case)
            submission["artifacts"]["solution.py"] = source
            self.assertFalse(case_outcomes(t05.grade(case, submission, execution="trusted"))[rejected_case])

    def test_absolute_continuation_time_makes_stall_guard_directly_testable(self):
        case = t05.build(17)
        p = next(p for name, p, state in case["expected"]["hidden"] if name == "continuation_time_stalled")
        self.assertLess(p["t_start"], p["t_end"])
        self.assertGreater(p["dt_initial"], 0)
        self.assertEqual(p["t_start"]+p["dt_initial"], p["t_start"])
        expected = {"status": "time_stalled", "t": 1e16, "y": [1.0],
                    "accepted_steps": 0, "rejected_steps": 0,
                    "history": [{"t": 1e16, "y": [1.0]}], "attempts": []}
        self.assertEqual(t05._oracle(p), expected)
        result = run_python(t05.REFERENCE_SOURCE, p, execution="trusted")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["result"], expected)
        submission = t05.reference(case)
        submission["artifacts"]["solution.py"] = t05.REFERENCE_SOURCE.replace("if t+h <= t:", "if False:")
        outcomes = case_outcomes(t05.grade(case, submission, execution="trusted"))
        self.assertFalse(outcomes["continuation_time_stalled"])
        # A second narrow mutant ignores the new optional continuation field.
        submission["artifacts"]["solution.py"] = t05.REFERENCE_SOURCE.replace('start = payload.get("t_start", 0.0)', 'start = 0.0')
        outcomes = case_outcomes(t05.grade(case, submission, execution="trusted"))
        for name in ("continuation_time_stalled", "nonzero_continuation", "nonzero_zero_horizon"):
            self.assertFalse(outcomes[name])

    def test_adjacent_endpoints_follow_float_arithmetic_without_epsilon_termination(self):
        case = t05.build(17)
        cases = {name: p for name, p, state in case["expected"]["hidden"] if name.startswith("adjacent_")}
        for name, p in cases.items():
            result = t05._oracle(p)
            self.assertEqual(result["t"], math.nextafter(0.3, math.inf))
            self.assertEqual(result["accepted_steps"], 2, name)
            self.assertEqual(result["y"], [1.0])
        tiny = t05._oracle(cases["adjacent_endpoint_requires_final_step"])
        self.assertEqual(tiny["attempts"][-1]["h"], math.ulp(0.3))
        submission = t05.reference(case)
        submission["artifacts"]["solution.py"] = t05.REFERENCE_SOURCE.replace("while t < end:", "while t < end-1e-12:")
        outcomes = case_outcomes(t05.grade(case, submission, execution="trusted"))
        self.assertFalse(outcomes["adjacent_endpoint_requires_final_step"])


class MetrologyGenerationContracts(unittest.TestCase):
    def test_gaussian_interface_receives_the_reported_absolute_sigma(self):
        calls = []
        real_random = random.Random

        class SpyRandom(real_random):
            def gauss(self, mu, sigma):
                calls.append((mu, sigma))
                return 0.0

        with patch.object(t06.random, "Random", SpyRandom):
            case = t06.build(17)
        rows = list(csv.DictReader(io.StringIO(case["files"]["calibration.csv"])))
        sigma = [float(row["sigma_mV"]) for row in rows if row["status"] == "valid"]
        self.assertEqual(calls, [(0.0, value) for value in sigma])
        self.assertEqual(len(calls), 7)

    def test_updated_seed_expectations_recompute_from_public_csv(self):
        for seed in (0, 17, 101):
            with self.subTest(seed=seed):
                case = t06.build(seed)
                rows = [dict(row, reference_mm=float(row["reference_mm"]), voltage_mV=float(row["voltage_mV"]), sigma_mV=float(row["sigma_mV"]))
                        for row in csv.DictReader(io.StringIO(case["files"]["calibration.csv"]))]
                noise = [dict(row, frequency_Hz=float(row["frequency_Hz"]), value=float(row["value"]))
                         for row in csv.DictReader(io.StringIO(case["files"]["noise.csv"]))]
                measured = json.loads(case["files"]["measurement.json"])
                answer = t06._calculate(rows, noise, measured)
                self.assertEqual(answer, case["expected"]["answer"])
                submission = t06.reference(case)
                submission["answer"] = answer
                self.assertEqual(earned(t06.grade(case, submission)), 70)

    def test_centered_weighted_fit_independently_checks_absolute_covariance(self):
        case = t06.build(17)
        rows = [row for row in csv.DictReader(io.StringIO(case["files"]["calibration.csv"])) if row["status"] == "valid"]
        x = [float(row["reference_mm"]) for row in rows]
        w = [1/(float(row["sigma_mV"])*1e-3)**2 for row in rows]
        total = math.fsum(w)
        mean = math.fsum(a*b for a,b in zip(w,x))/total
        centered = math.fsum(a*(b-mean)**2 for a,b in zip(w,x))
        independent = [[1/total+mean*mean/centered, -mean/centered],
                       [-mean/centered, 1/centered]]
        expected = case["expected"]["answer"]["calibration"]
        self.assertTrue(numbers_close(expected["covariance_ab"], independent, rtol=1e-12, atol=1e-20))
        submission = t06.reference(case)
        factor = expected["chi2"]/expected["degrees_of_freedom"]
        submission["answer"]["calibration"]["covariance_ab"] = [[value*factor for value in row] for row in independent]
        self.assertFalse(next(row for row in t06.grade(case, submission) if row["id"] == "absolute_covariance")["passed"])
        submission = t06.reference(case)
        submission["answer"]["psd_V2_per_Hz"] = [row["value"]*1e-6 if row["unit"] == "uV/sqrt(Hz)" else row["value"] for row in case["expected"]["noise"]]
        self.assertFalse(next(row for row in t06.grade(case, submission) if row["id"] == "asd_to_psd")["passed"])

    def test_noise_and_covariance_negative_controls_still_fail(self):
        case = t06.build(17)
        for responsibility in ("absolute_covariance", "asd_to_psd", "covariance_variance_term", "partial_band_integral"):
            with self.subTest(responsibility=responsibility):
                submission = t06.reference(case)
                a = submission["answer"]
                if responsibility == "absolute_covariance":
                    a["calibration"]["covariance_ab"] = [[0.0, 0.0], [0.0, 0.0]]
                elif responsibility == "asd_to_psd":
                    a["psd_V2_per_Hz"] = [0.0]*len(a["psd_V2_per_Hz"])
                elif responsibility == "covariance_variance_term":
                    a["variance_terms_mm2"]["coefficient_covariance"] = 0.0
                else:
                    a["noise_integral_V2"] *= 2.0
                row = next(row for row in t06.grade(case, submission) if row["id"] == responsibility)
                self.assertFalse(row["passed"])


if __name__ == "__main__":
    unittest.main()

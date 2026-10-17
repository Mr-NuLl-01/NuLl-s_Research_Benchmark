"""Numerical oracles, behavioral mutations and grading failure modes.

Only repository-owned reference and deliberately constructed mutant code is
executed with the trusted backend. These tests are not a model evaluation or
an assertion that trusted subprocess execution isolates hostile submissions.
"""

from __future__ import annotations

import copy
import math
import statistics
import unittest

from nrb.checks import numbers_close
from nrb.execution import run_python
from nrb.tasks import t04, t05, t06, t07


MODULES = (t04, t05, t06, t07)


def earned(checks):
    return sum(row["points"] for row in checks if row["passed"] is True)


class NumericalTaskContracts(unittest.TestCase):
    def test_references_receive_seventy_on_multiple_seeds(self):
        for module in MODULES:
            for seed in (0, 1, 9, 2026):
                with self.subTest(task=module.__name__, seed=seed):
                    case = module.build(seed)
                    checks = module.grade(case, module.reference(case), execution="trusted")
                    self.assertEqual(sum(row["points"] for row in checks), 70)
                    self.assertEqual(earned(checks), 70, [row for row in checks if row["passed"] is not True])

    def test_variants_change_data_and_reference_results(self):
        for module in MODULES:
            with self.subTest(task=module.__name__):
                first, other = module.build(4), module.build(5)
                self.assertEqual(first, module.build(4))
                self.assertNotEqual(first["files"], other["files"])
                self.assertNotEqual(module.reference(first)["answer"], module.reference(other)["answer"])

    def test_human_rubrics_have_three_anchored_dimensions(self):
        for module in MODULES:
            case = module.build(3)
            self.assertEqual(len(case["rubric"]), 3)
            self.assertEqual(len({row["id"] for row in case["rubric"]}), 3)
            for row in case["rubric"]:
                self.assertEqual(set(row["anchors"]), {"0", "5", "10"})

    def test_missing_and_malformed_structured_answers_do_not_crash_or_score(self):
        for module in MODULES:
            case = module.build(0)
            for answer in ({}, None, [], {"answer": []}, {"answer": {"visible_result": "bad", "calibration": 3, "variance_terms_mm2": []}}):
                with self.subTest(task=module.__name__, answer=answer):
                    checks = module.grade(case, answer)
                    self.assertEqual(sum(row["points"] for row in checks), 70)
                    self.assertEqual(earned(checks), 0)
                    self.assertTrue(all(row["passed"] is False for row in checks))

    def test_code_backend_unavailable_is_ungraded_not_failure(self):
        for module in (t04, t05):
            case = module.build(0)
            checks = module.grade(case, module.reference(case), execution="none")
            self.assertEqual(earned(checks), 20)
            self.assertEqual(sum(row["points"] for row in checks if row["passed"] is None), 50)

    def test_missing_code_is_a_real_failure_even_without_backend(self):
        for module in (t04, t05):
            case = module.build(0)
            submission = module.reference(case)
            del submission["artifacts"]["solution.py"]
            checks = module.grade(case, submission, execution="none")
            self.assertEqual(earned(checks), 20)
            self.assertFalse(any(row["passed"] is None for row in checks))


class FiniteVolumeOracleTests(unittest.TestCase):
    def test_two_cell_resistance_and_capacity_analytic_example(self):
        payload = {"edges": [0.0, 0.25, 1.0], "conductivity": [1.0, 3.0], "capacity": [2.0, 1.0],
                   "temperature": [4.0, 0.0], "source": [0.0, 0.0], "dt": 0.05, "steps": 1,
                   "left": {"kind": "flux", "value": 0.0}, "right": {"kind": "flux", "value": 0.0}}
        # Face resistance .25/(2*1)+.75/(2*3)=.25; initial heat flow=16.
        expected = {"temperature": [2.4, 16/15], "face_flux": [0, 16/3, 0],
                    "energy_initial": 2.0, "energy_final": 2.0, "energy_input": 0.0}
        self.assertTrue(numbers_close(t04._oracle(payload), expected))
        result = run_python(t04.REFERENCE_SOURCE, payload, execution="trusted")
        self.assertEqual(result["status"], "ok")
        self.assertTrue(numbers_close(result["result"], expected))

    def test_one_cell_temperature_boundaries_have_half_cell_resistance(self):
        payload = {"edges": [0.0, 2.0], "conductivity": [4.0], "capacity": [3.0],
                   "temperature": [5.0], "source": [2.0], "dt": 0.1, "steps": 1,
                   "left": {"kind": "temperature", "value": 1.0},
                   "right": {"kind": "temperature", "value": 7.0}}
        result = t04._oracle(payload)
        self.assertAlmostEqual(result["temperature"][0], 5-0.4/6)
        self.assertAlmostEqual(result["energy_input"], -0.4)
        self.assertAlmostEqual(result["energy_final"]-result["energy_initial"], -0.4)

    def test_all_valid_hidden_cases_satisfy_discrete_energy_balance(self):
        for seed in (0, 13, 2026):
            for name, payload, status in t04._hidden(seed):
                if status == "ok":
                    result = t04._oracle(payload)
                    self.assertAlmostEqual(result["energy_final"]-result["energy_initial"], result["energy_input"], places=11, msg=name)

    def test_arithmetic_interface_mutant_loses_behavior_points(self):
        case = t04.build(1)
        submission = t04.reference(case)
        old = "1.0 / (widths[i]/(2*k[i]) + widths[i+1]/(2*k[i+1]))"
        new = "(k[i]+k[i+1]) / (widths[i]+widths[i+1])"
        self.assertIn(old, submission["artifacts"]["solution.py"])
        submission["artifacts"]["solution.py"] = submission["artifacts"]["solution.py"].replace(old, new)
        checks = t04.grade(case, submission, execution="trusted")
        failed = {row["id"] for row in checks if row["passed"] is False}
        self.assertIn("discontinuous_conductivity", failed)
        self.assertLessEqual(earned(checks), 50)

    def test_buggy_starter_is_rejected_despite_correct_visible_answer(self):
        case = t04.build(0)
        submission = t04.reference(case)
        submission["artifacts"]["solution.py"] = t04.STARTER_SOURCE
        self.assertLessEqual(earned(t04.grade(case, submission, execution="trusted")), 40)


class AdaptiveOracleTests(unittest.TestCase):
    def test_rejection_preserves_time_and_state(self):
        result = t05._oracle(t05.build(0)["expected"]["hidden"][0][1])
        self.assertGreater(result["rejected_steps"], 0)
        for previous, following in zip(result["attempts"], result["attempts"][1:]):
            if not previous["accepted"]:
                self.assertEqual(previous["t"], following["t"])
                self.assertEqual(previous["y_before"], following["y_before"])
        self.assertEqual(len(result["history"]), result["accepted_steps"]+1)
        self.assertEqual(len(result["attempts"]), result["accepted_steps"]+result["rejected_steps"])

    def test_minimum_step_failure_is_finite_and_uncommitted(self):
        for name, payload, _ in t05._hidden(3):
            if name in ("finite_minimum_step_failure", "failed_clipped_endpoint_is_not_committed"):
                result = t05._oracle(payload)
                self.assertEqual(result["status"], "dt_min_reached")
                self.assertEqual(result["t"], 0)
                self.assertEqual(result["accepted_steps"], 0)
                self.assertLess(result["rejected_steps"], 10)
                self.assertEqual(result["y"], [payload["y0"]])

    def test_zero_decay_has_exact_endpoint_and_final_subminimum_step(self):
        payload = next(payload for name, payload, _ in t05._hidden(4) if name == "final_clip_below_minimum")
        result = run_python(t05.REFERENCE_SOURCE, payload, execution="trusted")["result"]
        self.assertEqual(result["status"], "finished")
        self.assertEqual(result["t"], 0.345)
        self.assertEqual(result["y"], [1.0])
        self.assertLess(result["attempts"][-1]["h"], payload["dt_min"])
        self.assertEqual(result["accepted_steps"], 3)

    def test_state_commit_on_rejection_mutant_fails(self):
        case = t05.build(3)
        submission = t05.reference(case)
        source = submission["artifacts"]["solution.py"]
        submission["artifacts"]["solution.py"] = source.replace("        if accept:\n", "        y = two_half\n        if accept:\n")
        checks = t05.grade(case, submission, execution="trusted")
        failed = {row["id"] for row in checks if row["passed"] is False}
        self.assertIn("vector_rejection_and_rollback", failed)
        self.assertIn("finite_minimum_step_failure", failed)
        self.assertLess(earned(checks), 50)

    def test_zero_absolute_tolerance_and_shape_are_rejected_as_valueerror(self):
        payloads = [payload for _, payload, status in t05._hidden(0) if status == "ValueError"]
        result = run_python(t05._batch_source(t05.REFERENCE_SOURCE), {"nrb_cases": payloads}, execution="trusted")
        self.assertEqual(result["status"], "ok")
        self.assertTrue(all(item == {"status": "error", "type": "ValueError"} for item in result["result"]["nrb_results"]))


class MetrologyOracleTests(unittest.TestCase):
    def test_analytic_weighted_fit_covariance_and_uncertainty(self):
        rows = [{"id": str(i), "reference_mm": i, "voltage_mV": 1000+2000*i, "sigma_mV": 1000, "status": "valid"} for i in range(3)]
        noise = [{"frequency_Hz": 0, "value": 4, "unit": "V^2/Hz"}, {"frequency_Hz": 10, "value": 4, "unit": "V^2/Hz"}]
        measurement = {"mean_voltage_mV": 3000, "repeatability_sigma_mean_mV": 100, "display_step_mV": 0, "band_low_Hz": 0, "band_high_Hz": 10}
        result = t06._calculate(rows, noise, measurement)
        self.assertAlmostEqual(result["calibration"]["intercept_V"], 1)
        self.assertAlmostEqual(result["calibration"]["slope_V_per_mm"], 2)
        self.assertTrue(numbers_close(result["calibration"]["covariance_ab"], [[5/6, -1/2], [-1/2, 1/2]]))
        self.assertAlmostEqual(result["standard_uncertainty_mm"]**2, (0.01+1/3)/4)
        self.assertAlmostEqual(result["variance_terms_mm2"]["coefficient_covariance"], -0.25)
        self.assertAlmostEqual(result["noise_integral_V2"], 40)
        self.assertAlmostEqual(result["noise_rms_mm"], math.sqrt(40)/2)

    def test_psd_partial_interval_matches_analytic_linear_function(self):
        # S(f)=2+3*f integrates to [2*f+1.5*f^2] between 2 and 7.
        result = t06._integrate_psd([0, 4, 10], [2, 14, 32], 2, 7)
        self.assertAlmostEqual(result, (14+1.5*49)-(4+1.5*4))

    def test_zero_spectrum_and_covariance_cannot_pass_absolute_tolerance(self):
        case = t06.build(0)
        submission = t06.reference(case)
        submission["answer"]["psd_V2_per_Hz"] = [0.0]*len(submission["answer"]["psd_V2_per_Hz"])
        submission["answer"]["calibration"]["covariance_ab"] = [[0.0, 0.0], [0.0, 0.0]]
        failed = {row["id"] for row in t06.grade(case, submission) if row["passed"] is False}
        self.assertIn("asd_to_psd", failed)
        self.assertIn("absolute_covariance", failed)

    def test_ignoring_correlation_is_detected(self):
        case = t06.build(7)
        submission = t06.reference(case)
        terms = submission["answer"]["variance_terms_mm2"]
        self.assertLess(terms["coefficient_covariance"], 0)
        terms["coefficient_covariance"] = 0.0
        naive = math.sqrt(sum(terms.values()))
        submission["answer"]["standard_uncertainty_mm"] = naive
        submission["answer"]["expanded_k2_mm"] = 2*naive
        failed = {row["id"] for row in t06.grade(case, submission) if row["passed"] is False}
        self.assertIn("covariance_variance_term", failed)
        self.assertIn("combined_uncertainty", failed)


class GroupedEvaluationTests(unittest.TestCase):
    def test_class_metrics_match_hand_calculation(self):
        matrix = [[8, 2, 0], [1, 1, 2], [0, 1, 2]]
        result = t07._metrics(matrix)
        self.assertAlmostEqual(result["accuracy"], 11/17)
        self.assertAlmostEqual(result["macro_f1"], (16/19+1/4+4/7)/3)
        self.assertAlmostEqual(result["balanced_accuracy"], (8/10+1/4+2/3)/3)
        self.assertAlmostEqual(result["per_class"]["joint_loose"]["precision"], 1/2)

    def test_selection_instances_distinguish_macro_accuracy_and_test_reselection(self):
        winners = set()
        for seed in range(8):
            case = t07.build(seed)
            data = case["expected"]
            chosen = data["answer"]["selected_model"]
            winners.add(chosen)
            for part, key in (("validation", "accuracy"), ("test", "macro_f1")):
                rows = [row for row in data["records"] if data["split"][row["machine_id"]] == part]
                scores = {model: t07._metrics(t07._confusion(rows, data["predictions"], model))[key] for model in t07.MODELS}
                self.assertNotEqual(max(scores, key=scores.get), chosen)
        self.assertEqual(winners, set(t07.MODELS))

    def test_cluster_bootstrap_matches_direct_row_expansion(self):
        data = t07.build(7)["expected"]
        chosen = data["answer"]["selected_model"]
        rows_by_group = {}
        for row in data["records"]:
            if data["split"][row["machine_id"]] == "test":
                rows_by_group.setdefault(row["machine_id"], []).append(row)
        values = []
        for sample in data["plan"]:
            rows = [row for machine in sample for row in rows_by_group[machine]]
            matrix = [[0]*3 for _ in range(3)]
            for row in rows:
                true = t07.LABELS.index(row["label"])
                pred = t07.LABELS.index(data["predictions"][row["row_id"]][chosen])
                matrix[true][pred] += 1
            f1s = []
            for i in range(3):
                denominator = sum(matrix[i])+sum(matrix[j][i] for j in range(3))
                f1s.append(2*matrix[i][i]/denominator if denominator else 0)
            values.append(sum(f1s)/3)
        expected = data["answer"]["bootstrap"]
        self.assertAlmostEqual(statistics.mean(values), expected["macro_f1_mean"])
        self.assertAlmostEqual(statistics.stdev(values), expected["macro_f1_standard_error"])
        ordered = sorted(values)
        for probability, endpoint in zip((0.025, 0.975), expected["percentile95"]):
            index = (len(ordered)-1)*probability
            lo = int(index)
            self.assertAlmostEqual(ordered[lo]*(1-index+lo)+ordered[lo+1]*(index-lo), endpoint)

    def test_deduplicated_cluster_resampling_mutant_is_detected(self):
        case = t07.build(7)
        data = case["expected"]
        wrong = t07._calculate(data["records"], data["predictions"], data["split"], [sorted(set(sample)) for sample in data["plan"]])
        submission = t07.reference(case)
        submission["answer"]["bootstrap"] = wrong["bootstrap"]
        self.assertFalse(next(row["passed"] for row in t07.grade(case, submission) if row["id"] == "cluster_bootstrap"))

    def test_transposing_confusion_matrix_is_detected(self):
        case = t07.build(0)
        submission = t07.reference(case)
        matrix = submission["answer"]["test_confusion_matrix"]
        submission["answer"]["test_confusion_matrix"] = list(map(list, zip(*matrix)))
        self.assertFalse(next(row["passed"] for row in t07.grade(case, submission) if row["id"] == "test_confusion_orientation"))


if __name__ == "__main__":
    unittest.main()

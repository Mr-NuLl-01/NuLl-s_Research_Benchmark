"""Public-safe v0.2 science contracts and discriminating candidate controls."""
from __future__ import annotations

import copy
from fractions import Fraction
import hashlib
import itertools
import json
import unittest

from nrb.tasks import t03, t08, t10


def checks(module, case, submission):
    return {row["id"]: row for row in module.grade(case, submission)}


def score(module, case, submission):
    return sum(row["points"] for row in module.grade(case, submission) if row["passed"])


def tiny_design(tied=False):
    """Four feasible designs: exact ties/near ties and close strict levels.

    Two duplicated x levels per side are intentional: different settings can
    have equal x but distinct costs/noise. The 2e-13 near-optimal difference
    is below the strict-runner-up threshold; the 1e-9 strict gap is above it
    but far below the display tolerance used in the old vector grader.
    """
    problem = {
        "x": [-1, -1, 0, 1, 1], "costs": [1]*5,
        "max_replicates": [1, 1, 0, 1, 1], "budget": 2,
        "min_total": 2, "max_total": 2, "min_center": 0,
        "min_each_side": 1, "max_extreme_total": 2,
        "variance_scenarios": [[1, 1 if tied else 1.0000000000008, 1, 1, 1.000000004]]*3,
    }
    case = t03.build(0)
    case["files"]["design.json"] = json.dumps(problem)
    case["expected"]["answer"] = t03._solve(problem)
    return case, problem


def allocation_answer(case, allocation=None, second=None):
    packet = t03.reference(case)
    answer = packet["answer"]
    problem = json.loads(case["files"]["design.json"])
    if allocation is not None:
        variances = t03._variances(allocation, problem)
        answer.update(allocation=allocation, total_measurements=sum(allocation),
                      total_cost=sum(n*c for n, c in zip(allocation, problem["costs"])),
                      scenario_slope_variances=variances, worst_slope_variance=max(variances),
                      worst_scenario=variances.index(max(variances))+1)
    if second is not None:
        variances = t03._exact_variances(second, problem)
        best = t03._exact_search(t03._canonical(problem))[0][0]
        answer.update(second_distinct_allocation=second, second_distinct_objective=float(max(variances)),
                      objective_gap=float(max(variances)-best))
    return packet


class ExactDesignMembershipTests(unittest.TestCase):
    def test_exact_decimal_oracle_agrees_with_independent_formula(self):
        case, problem = tiny_design()
        for n in itertools.product(range(2), repeat=5):
            if not t03._constraints(n, problem):
                continue
            x = [Fraction(str(v)) for v in problem["x"]]
            vv = []
            for scenario in problem["variance_scenarios"]:
                weights = [Fraction(ni)/Fraction(str(v)) for ni, v in zip(n, scenario)]
                center = sum(w*xi for w, xi in zip(weights, x))/sum(weights)
                vv.append(1/sum(w*(xi-center)**2 for w, xi in zip(weights, x)))
            self.assertEqual(t03._exact_variances(n, problem), vv)
        self.assertEqual(t03._exact_variances([0, 1, 0, 1, 0], problem)[0]-Fraction(1, 2),
                         Fraction(1, 5_000_000_000_000))

    def test_small_gap_vector_is_not_exactly_optimal(self):
        case, _ = tiny_design()
        mutant = allocation_answer(case, [0, 1, 0, 1, 0])
        rows = checks(t03, case, mutant)
        self.assertTrue(rows["all_design_constraints"]["passed"])
        self.assertTrue(rows["minimax_objective"]["passed"])
        self.assertFalse(rows["global_optimality"]["passed"])
        self.assertEqual(score(t03, case, mutant), 60)

    def test_only_exact_threshold_runner_up_level_is_accepted(self):
        case, _ = tiny_design()
        for vector in ([1, 0, 0, 1, 0], [0, 1, 0, 1, 0], [0, 1, 0, 0, 1]):
            with self.subTest(vector=vector):
                mutant = allocation_answer(case, second=vector)
                self.assertFalse(checks(t03, case, mutant)["strict_runner_up"]["passed"])
        self.assertTrue(checks(t03, case, t03.reference(case))["strict_runner_up"]["passed"])

    def test_runner_up_threshold_is_strict_at_exact_decimal_boundary(self):
        case, problem = tiny_design()
        problem["variance_scenarios"] = [[1, 1.000000000004, 1, 1, 1.000000000008]]*3
        case["files"]["design.json"] = json.dumps(problem)
        case["expected"]["answer"] = t03._solve(problem)
        boundary = [0, 1, 0, 1, 0]
        exact = t03._exact_variances(boundary, problem)[0]
        self.assertEqual(exact-Fraction(1, 2), Fraction(1, 10**12))
        self.assertFalse(checks(t03, case, allocation_answer(case, second=boundary))["strict_runner_up"]["passed"])
        accepted = allocation_answer(case, second=[1, 0, 0, 0, 1])
        self.assertEqual(score(t03, case, accepted), 70)

    def test_different_exact_global_and_runner_up_ties_are_legal(self):
        case, _ = tiny_design(tied=True)
        alternate = allocation_answer(case, [1, 0, 0, 1, 0], [1, 0, 0, 0, 1])
        self.assertEqual(score(t03, case, alternate), 70)
        tied_as_second = allocation_answer(case, second=[0, 1, 0, 1, 0])
        self.assertFalse(checks(t03, case, tied_as_second)["strict_runner_up"]["passed"])


class MandatorySolverReproductionTests(unittest.TestCase):
    def test_actual_reference_entrypoint_reproduces_multiple_public_instances(self):
        for seed in (0, 17, 101):
            with self.subTest(seed=seed):
                case = t03.build(seed)
                submission = t03.reference(case)
                receipt = t03.reproduce_solution(case, submission, execution="trusted")
                self.assertEqual(receipt["status"], "pass", receipt)
                self.assertTrue(receipt["passed"])
                self.assertEqual(receipt["execution_status"], "ok")
                self.assertTrue(all(row["passed"] for row in receipt["checks"]))
                for name in ("case_hash", "submission_hash", "source_hash", "input_hash", "result_hash"):
                    self.assertEqual(len(receipt[name]), 64)
                self.assertEqual(receipt["source_hash"], hashlib.sha256(submission["artifacts"]["solve.py"].encode()).hexdigest())

    def test_same_valid_alternate_choice_is_reproduced(self):
        case, _ = tiny_design(tied=True)
        alternate = allocation_answer(case, [1, 0, 0, 1, 0])
        source = alternate["artifacts"]["solve.py"]
        alternate["artifacts"]["solve.py"] = source.replace("best = rows[0]", "best = next(row for row in rows if row[1] == (1,0,0,1,0))")
        self.assertEqual(t03.reproduce_solution(case, alternate, execution="trusted")["status"], "pass")
        # Correct but unrelated tied output is not evidence that the submitted
        # vector and reported values were actually reproduced by this code.
        alternate["artifacts"]["solve.py"] = source
        self.assertEqual(t03.reproduce_solution(case, alternate, execution="trusted")["status"], "fail")

    def test_wrong_missing_and_malformed_solver_cannot_pass(self):
        case = t03.build(0)
        for source in ("", "def solve(problem):\n    return {}\n",
                       "def solve(problem):\n    raise ValueError('broken search')\n"):
            submission = t03.reference(case)
            submission["artifacts"]["solve.py"] = source
            receipt = t03.reproduce_solution(case, submission, execution="trusted")
            self.assertEqual(receipt["status"], "fail")
        submission = t03.reference(case)
        malformed = dict(submission["answer"], scenario_slope_variances=4)
        submission["artifacts"]["solve.py"] = "def solve(problem):\n    return "+repr(malformed)+"\n"
        self.assertEqual(t03.reproduce_solution(case, submission, execution="trusted")["status"], "fail")

    def test_no_backend_is_unassessed_and_missing_source_is_failure(self):
        case = t03.build(0)
        submission = t03.reference(case)
        receipt = t03.reproduce_solution(case, submission, execution="none")
        self.assertEqual(receipt["status"], "unassessed")
        self.assertIsNone(receipt["passed"])
        self.assertIsNone(receipt["result_hash"])
        del submission["artifacts"]["solve.py"]
        self.assertEqual(t03.reproduce_solution(case, submission, execution="none")["status"], "fail")


class EvidenceAndTemplateTests(unittest.TestCase):
    def test_claim_schema_does_not_fill_boolean_answers(self):
        case = t08.build(0)
        for key in ("unique_fixed_point", "ordinary_infinity_contraction", "spectral_radius_substitution_universally_valid"):
            self.assertIn(f'"{key}":"boolean，由你判断"', case["prompt"])
            self.assertNotIn(f'"{key}":true', case["prompt"])
            self.assertNotIn(f'"{key}":false', case["prompt"])
        packet = t08.reference(case)
        packet["answer"]["claims"] = {key: "boolean，由你判断" for key in packet["answer"]["claims"]}
        self.assertFalse(checks(t08, case, packet)["logical_claims"]["passed"])

    def test_eight_evidence_variants_are_coherent_from_public_files(self):
        results = {key: set() for key in ("current_arithmetic", "legacy_summary", "rendering", "cross_platform")}
        statuses = set()
        for seed in range(8):
            case = t10.build(seed)
            packet = t10.reference(case)
            self.assertEqual(score(t10, case, packet), 70)
            answer = packet["answer"]
            manifest = json.loads(case["files"]["bundle/manifest.json"])
            for path, digest in manifest.items():
                match = hashlib.sha256(case["files"][path].encode()).hexdigest() == digest
                self.assertEqual(answer["integrity"][path], "match" if match else "mismatch")
            current = json.loads(case["files"]["logs/current.json"])
            legacy = json.loads(case["files"]["logs/legacy.json"])
            active = case["expected"]["source_revision"]
            self.assertIn(active, case["files"]["current_request.md"])
            # Independent visible-state derivation, not a second call to the
            # task's evidence helper or copying its expected answer object.
            same = current.get("source_revision") == active
            if not same:
                arithmetic = "insufficient"
            elif current["arithmetic_status"] == "not_run":
                arithmetic = "not_run"
            elif current["scope"] != "calibration arithmetic only":
                arithmetic = "insufficient"
            else:
                arithmetic = "pass_from_supplied_log" if current["exit_code"] == 0 else "fail_from_supplied_log"
            self.assertEqual(answer["evidence"]["current_arithmetic"], arithmetic)
            for field, log_key in (("rendering", "render_check"), ("cross_platform", "other_platform_checks")):
                wanted = ({"pass": "pass_from_supplied_log", "fail": "fail_from_supplied_log", "not_run": "not_run"}[current[log_key]]
                          if same else "insufficient")
                self.assertEqual(answer["evidence"][field], wanted)
            legacy_state = ("insufficient" if not legacy.get("source_revision") else
                            "same_revision" if legacy["source_revision"] == active else "stale_revision")
            self.assertEqual(answer["evidence"]["legacy_summary"], legacy_state)
            full = (all(value == "match" for value in answer["integrity"].values())
                    and all(answer["evidence"][key] == "pass_from_supplied_log" for key in
                            ("current_arithmetic", "rendering", "cross_platform")))
            self.assertIs(answer["evidence"]["full_validation"], full)
            self.assertIs(answer["handoff"]["new_simulations_authorized"], False)
            for key in results:
                results[key].add(answer["evidence"][key])
            statuses.add(answer["handoff"]["status"])
        for key in ("current_arithmetic", "rendering", "cross_platform"):
            self.assertEqual(results[key], set(t10.EVIDENCE_RESULTS))
        self.assertEqual(results["legacy_summary"], {"same_revision", "stale_revision", "insufficient"})
        self.assertEqual(statuses, {"needs_integrity_repair", "checks_pending", "ready_for_author_review"})

    def test_old_incomplete_template_is_wrong_for_positive_evidence(self):
        case = t10.build(7)
        packet = t10.reference(case)
        self.assertTrue(packet["answer"]["evidence"]["full_validation"])
        packet["answer"]["evidence"] = {"current_arithmetic": "pass_from_supplied_log", "legacy_summary": "stale_revision",
                                              "rendering": "not_run", "cross_platform": "not_run", "full_validation": False}
        packet["answer"]["handoff"]["status"] = "needs_repair_and_review"
        rows = checks(t10, case, packet)
        for key in ("evidence_rendering", "evidence_cross_platform", "evidence_full_validation", "handoff_status"):
            self.assertFalse(rows[key]["passed"])
        self.assertLess(score(t10, case, packet), 70)

    def test_schema_is_types_and_empty_or_copied_schema_has_no_judgment_credit(self):
        case = t10.build(7)
        prompt = case["prompt"]
        self.assertIn('"full_validation":"boolean，由你判断"', prompt)
        self.assertNotIn('"full_validation":false', prompt)
        self.assertNotIn('"full_validation":true', prompt)
        packet = t10.reference(case)
        packet["answer"]["evidence"] = {key: "" for key in packet["answer"]["evidence"]}
        self.assertTrue(all(not row["passed"] for key, row in checks(t10, case, packet).items() if key.startswith("evidence_")))
        self.assertEqual(score(t10, case, {}), 0)


if __name__ == "__main__":
    unittest.main()

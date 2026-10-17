import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from nrb.core import (get_case, reference_submission, grade_submission, parse_submission,
                      write_candidate_packet, summarize, attach_review, fingerprint, safe_relative)
from nrb.checks import close, numbers_close
from nrb.analysis import paired_comparison


class CoreContracts(unittest.TestCase):
    def test_strict_json_and_safe_artifacts(self):
        valid = '{"task_id":"NRB09","answer":{}}'
        self.assertEqual(parse_submission(valid)["task_id"], "NRB09")
        self.assertEqual(parse_submission("```json\n"+valid+"\n```")["task_id"], "NRB09")
        for text in ('{"task_id":"NRB09","answer":{"a":NaN}}', '{"task_id":"NRB09","answer":{},"answer":{}}', 'Text '+valid, '[]'):
            with self.assertRaises(ValueError):
                parse_submission(text)
        for path in ("../escape.py", "/tmp/x", "C:/x", "a/../x", "a\\x", ".git/config", "a//b"):
            with self.assertRaises(ValueError):
                safe_relative(path)

    def test_bool_nonfinite_not_numeric_answers(self):
        self.assertFalse(close(True, 1))
        self.assertFalse(close(float("inf"), 1))
        self.assertFalse(numbers_close([1], [1, 2]))

    def test_public_packet_contains_no_oracle(self):
        c = get_case("NRB10", 9)
        with tempfile.TemporaryDirectory() as root:
            dest = Path(root)/"packet"
            manifest = write_candidate_packet(c, dest)
            self.assertFalse(manifest["contains_answers"])
            self.assertFalse(any(p.name in ("expected.json", "reference.json", "t10.py") for p in dest.rglob("*")))
            self.assertEqual((dest/"bundle/values.csv").read_text(), c["files"]["bundle/values.csv"])
            with self.assertRaises(FileExistsError):
                write_candidate_packet(c, dest)

    def test_missing_review_is_not_zero_or_full_score(self):
        c = get_case("NRB10", 0)
        r = grade_submission(c, reference_submission(c))
        self.assertEqual(r["auto_percent"], 100)
        self.assertIsNone(r["total"])
        self.assertTrue(r["review_pending"])

    def test_reference_does_not_alias_expected_answers(self):
        c = get_case("NRB10", 0)
        s = reference_submission(c)
        s["answer"]["integrity"]["bundle/model.txt"] = "wrong"
        self.assertNotEqual(c["expected"]["integrity"]["bundle/model.txt"], "wrong")

    def test_review_bound_to_exact_submission_and_case(self):
        c = get_case("NRB10", 0)
        s = reference_submission(c)
        r = grade_submission(c, s)
        review = {"task_id": c["id"], "case_hash": c["case_hash"], "submission_hash": fingerprint(s),
                  "reviewer_id": "test-human", "reviewer_type": "human",
                  "criteria": [{"id": x["id"], "score": 5, "rationale": "Test fixture only", "evidence": "Test fixture only"} for x in c["rubric"]]}
        out = attach_review(c, r, review)
        self.assertEqual(out["total"], 85)
        review["submission_hash"] = "wrong"
        with self.assertRaises(ValueError):
            attach_review(c, r, review)

    def test_invalid_model_json_is_zero_but_grader_error_is_unscored(self):
        c = get_case("NRB10", 0)
        r = grade_submission(c, "not json")
        self.assertEqual((r["auto_points"], r["coverage"]), (0, 1))
        with patch("nrb.tasks.t10.grade", side_effect=RuntimeError("broken verifier")):
            r = grade_submission(c, reference_submission(c))
        self.assertIsNone(r["auto_percent"])
        self.assertEqual(r["error"], "grader_error")

    def test_missing_tasks_cannot_inflate_macro(self):
        c = get_case("NRB10", 0)
        r = grade_submission(c, reference_submission(c))
        self.assertIsNone(summarize([r])["auto_macro_percent"])
        with self.assertRaises(ValueError):
            summarize([r, r])

    def test_paired_comparison_uses_equal_inputs_and_family_clusters(self):
        c = get_case("NRB10", 0)
        a = grade_submission(c, reference_submission(c))
        b = copy.deepcopy(a)
        b["auto_percent"] = 80
        left = {"benchmark_version": "0.1.0", "reports": [a]}
        right = {"benchmark_version": "0.1.0", "reports": [b]}
        result = paired_comparison([left, left], [right, right])
        self.assertEqual(result["task_families"], 1)
        self.assertEqual(result["macro_delta_b_minus_a"], -20)
        b["case_hash"] = "different"
        with self.assertRaises(ValueError):
            paired_comparison([left], [right])

    def test_comparison_rejects_empty_or_mixed_experimental_conditions(self):
        empty = {"benchmark_version": "0.1.0", "reports": []}
        with self.assertRaises(ValueError):
            paired_comparison([empty], [empty])
        case = get_case("NRB10", 0)
        report = grade_submission(case, reference_submission(case))
        run = {"benchmark_version": "0.1.0", "track": "agent-controlled",
               "model_label": "model-a", "harness_label": "harness-a",
               "metadata": {"budget": 900, "repetition": 1}, "reports": [report]}
        for key, value in (("benchmark_version", "0.2.0"), ("track", "agent-diagnostic"),
                           ("model_label", "model-x"), ("harness_label", "harness-x"),
                           ("metadata", {"budget": 1800, "repetition": 2})):
            different = copy.deepcopy(run)
            different[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                paired_comparison([run, different], [run, different])
        repeat = copy.deepcopy(run)
        repeat["metadata"]["repetition"] = 2
        self.assertEqual(paired_comparison([run, repeat], [run, repeat])["macro_delta_b_minus_a"], 0)


class VisualAndHandoffTasks(unittest.TestCase):
    def test_oracles_and_seeded_data(self):
        for task in ("NRB09", "NRB10"):
            hashes = set()
            for seed in (0, 17, 42):
                c = get_case(task, seed)
                hashes.add(c["case_hash"])
                self.assertEqual(grade_submission(c, reference_submission(c))["auto_points"], 70)
            self.assertEqual(len(hashes), 3)

    def test_svg_coordinates_not_just_answer_metadata_are_graded(self):
        c = get_case("NRB09", 0)
        s = reference_submission(c)
        s["artifacts"]["figure.svg"] = s["artifacts"]["figure.svg"].replace('id="observations"', 'id="wrong-observations"')
        r = grade_submission(c, s)
        self.assertLess(r["auto_points"], 70)
        self.assertIn("observation_geometry", r["critical_failures"])

    def test_svg_rejects_external_and_active_content(self):
        c = get_case("NRB09", 0)
        for extra in ('<script>alert(1)</script>', '<image href="https://example.com/data.png"/>'):
            s = reference_submission(c)
            s["artifacts"]["figure.svg"] = s["artifacts"]["figure.svg"].replace('</svg>', extra+'</svg>')
            r = grade_submission(c, s)
            self.assertFalse(next(x["passed"] for x in r["checks"] if x["id"] == "editable_svg"))

    def test_css_hidden_figure_and_external_stylesheet_cannot_pass(self):
        c = get_case("NRB09", 0)
        original = reference_submission(c)
        variants = [original["artifacts"]["figure.svg"].replace('<g font-family=', '<g style="display:none" font-family=', 1),
                    '<?xml-stylesheet type="text/css" href="https://example.invalid/style.css"?>'+original["artifacts"]["figure.svg"]]
        for svg in variants:
            s = copy.deepcopy(original)
            s["artifacts"]["figure.svg"] = svg
            report = grade_submission(c, s)
            self.assertEqual(report["coverage"], 1)
            self.assertIn("observation_geometry", report["critical_failures"])
            self.assertLess(report["auto_points"], 70)

    def test_definition_only_graphics_are_not_visible_evidence(self):
        import xml.etree.ElementTree as ET
        c = get_case("NRB09", 0)
        s = reference_submission(c)
        root = ET.fromstring(s["artifacts"]["figure.svg"])
        group = next(n for n in root if n.tag.endswith("g"))
        group.tag = "{http://www.w3.org/2000/svg}defs"
        s["artifacts"]["figure.svg"] = ET.tostring(root, encoding="unicode")
        report = grade_submission(c, s)
        self.assertEqual(report["coverage"], 1)
        self.assertIn("observation_geometry", report["critical_failures"])
        self.assertLess(report["auto_points"], 70)

    def test_equivalent_svg_coordinate_scaling_preserves_geometry_score(self):
        import re
        import xml.etree.ElementTree as ET
        c = get_case("NRB09", 0)
        s = reference_submission(c)
        root = ET.fromstring(s["artifacts"]["figure.svg"])
        inside_defs = set()
        for node in root.iter():
            if node.tag.split("}")[-1] == "defs":
                inside_defs.update(node.iter())
        pattern = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?")
        scaled = lambda value: format(float(value)*.01, ".14g")
        attributes = {"x", "y", "x1", "x2", "y1", "y2", "cx", "cy", "r", "rx", "ry", "width", "height", "font-size", "stroke-width"}
        for node in root.iter():
            if node in inside_defs:
                continue
            for key, value in list(node.attrib.items()):
                if key in attributes and pattern.fullmatch(value):
                    node.set(key, scaled(value))
                elif key in ("points", "d", "viewBox", "stroke-dasharray"):
                    node.set(key, pattern.sub(lambda m: scaled(m.group()), value))
                elif key == "transform" and value.startswith("rotate("):
                    numbers = pattern.findall(value)
                    node.set(key, "rotate("+numbers[0]+" "+" ".join(scaled(v) for v in numbers[1:])+")")
        s["artifacts"]["figure.svg"] = ET.tostring(root, encoding="unicode")
        for bounds in s["answer"]["panel_bounds"].values():
            bounds[:] = [value*.01 for value in bounds]
        self.assertEqual(grade_submission(c, s)["auto_points"], 70)

    def test_oversized_candidate_numbers_are_wrong_answers_not_outages(self):
        for task, keys in (("NRB09", ("panel_bounds", "signal", 0)),
                           ("NRB10", ("computed", "rmse_mm"))):
            c = get_case(task, 0)
            s = reference_submission(c)
            value = s["answer"]
            for key in keys[:-1]:
                value = value[key]
            value[keys[-1]] = 10**400
            report = grade_submission(c, s)
            self.assertEqual(report["coverage"], 1)
            self.assertIsNone(report["error"])
            self.assertLess(report["auto_points"], 70)

    def test_equivalent_negative_claim_labels_preserve_handoff_score(self):
        c = get_case("NRB10", 0)
        s = reference_submission(c)
        s["answer"]["claims"].update(C2="unsupported", C3="overstated")
        self.assertEqual(grade_submission(c, s)["auto_points"], 70)
        s["answer"]["claims"]["C1"] = []
        report = grade_submission(c, s)
        self.assertEqual(report["coverage"], 1)
        self.assertLess(report["auto_points"], 70)

    def test_corrupt_handoff_hash_and_false_pass_are_detected(self):
        c = get_case("NRB10", 17)
        s = reference_submission(c)
        s["answer"]["evidence"]["full_validation"] = True
        s["artifacts"]["revised_excerpt.md"] += "Changed after hashing."
        r = grade_submission(c, s)
        self.assertIn("evidence_full_validation", r["critical_failures"])
        self.assertFalse(next(x["passed"] for x in r["checks"] if x["id"] == "artifact_byte_hashes"))

    def test_empty_tasks_do_not_crash_or_pass(self):
        for task in ("NRB09", "NRB10"):
            c = get_case(task, 0)
            r = grade_submission(c, {"task_id": task, "answer": {}})
            self.assertEqual(r["coverage"], 1)
            self.assertEqual(r["auto_points"], 0)


if __name__ == "__main__":
    unittest.main()

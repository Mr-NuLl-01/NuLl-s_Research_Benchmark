"""NRB09 physical visibility, safe rendering and material-binding controls."""
import copy
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from nrb.core import fingerprint, get_case, reference_submission
from nrb.rendering import (RendererUnavailable, UnsafeSVG, parse_static_svg, render_svg,
                           renderer_identity, validate_render_receipt)
from nrb.tasks import t09
from scripts.check_rendering import negative_controls


class FigureVisibility(unittest.TestCase):
    def setUp(self):
        self.case = get_case("NRB09", 0)
        self.oracle = reference_submission(self.case)

    def checks(self, submission):
        return {c["id"]: c for c in t09.grade(self.case, submission)}

    def mutate_node(self, ident, **attrs):
        submission = copy.deepcopy(self.oracle)
        root = ET.fromstring(submission["artifacts"]["figure.svg"])
        node = next(n for n in root.iter() if n.attrib.get("id") == ident)
        node.attrib.update(attrs)
        submission["artifacts"]["figure.svg"] = ET.tostring(root, encoding="unicode")
        return submission

    def test_oracle_and_required_negative_controls(self):
        self.assertEqual(sum(c["points"] for c in self.checks(self.oracle).values() if c["passed"]), 70)
        variants = negative_controls(self.oracle)
        self.assertEqual(set(variants), {"minimalpoint", "zerostroke", "whitecover", "emptydiagram", "offcanvastext", "nestedopacity", "emptymarker"})
        for name, submission in variants.items():
            checks = self.checks(submission)
            with self.subTest(name=name):
                if name == "whitecover":
                    # Deliberate limit: opaque occlusion is not certified by XML.
                    # Core acceptance must remain pending until actual review.
                    self.assertTrue(all(c["passed"] for c in checks.values()))
                else:
                    self.assertTrue(any(c["passed"] is False for c in checks.values()))

    def test_physical_point_and_stroke_limits(self):
        # 180/1200=.15 mm per unit: diameter 1.32 units is below .2 mm.
        s = self.mutate_node("observations")
        root = ET.fromstring(s["artifacts"]["figure.svg"])
        group = next(n for n in root.iter() if n.attrib.get("id") == "observations")
        for node in group:
            node.set("r", "0.66")
        s["artifacts"]["figure.svg"] = ET.tostring(root, encoding="unicode")
        self.assertFalse(self.checks(s)["observation_geometry"]["passed"])
        self.assertFalse(self.checks(self.mutate_node("signal-model", **{"stroke-width": "0.53"}))["model_geometry"]["passed"])
        self.assertTrue(self.checks(self.mutate_node("signal-model", **{"stroke-width": "0.54"}))["model_geometry"]["passed"])

    def test_nested_opacity_and_inherited_paint(self):
        self.assertFalse(self.checks(negative_controls(self.oracle)["nestedopacity"])["observation_geometry"]["passed"])
        self.assertFalse(self.checks(self.mutate_node("observations", **{"fill-opacity": ".2"}))["observation_geometry"]["passed"])
        self.assertFalse(self.checks(self.mutate_node("signal-model", opacity=".2"))["model_geometry"]["passed"])

    def test_nonempty_group_and_marker_with_content_are_valid(self):
        s = copy.deepcopy(self.oracle)
        root = ET.fromstring(s["artifacts"]["figure.svg"])
        mass = next(n for n in root.iter() if n.attrib.get("id") == "mass")
        attrs = dict(mass.attrib)
        mass.tag = "{http://www.w3.org/2000/svg}g"
        mass.attrib.clear()
        mass.set("id", "mass")
        attrs.pop("id")
        ET.SubElement(mass, "{http://www.w3.org/2000/svg}rect", attrs)
        s["artifacts"]["figure.svg"] = ET.tostring(root, encoding="unicode")
        self.assertTrue(self.checks(s)["schematic_direction"]["passed"])
        for ident, attr in (("mass", {"x": "99999"}), ("displacement-arrow", {"x1": "99999", "x2": "100010"})):
            self.assertFalse(self.checks(self.mutate_node(ident, **attr))["schematic_direction"]["passed"])
        s = self.mutate_node("arrow", markerWidth="0.000001", markerHeight="0.000001")
        self.assertFalse(self.checks(s)["schematic_direction"]["passed"])

    def test_marker_contents_outside_marker_viewport_do_not_count(self):
        s = copy.deepcopy(self.oracle)
        s["artifacts"]["figure.svg"] = s["artifacts"]["figure.svg"].replace('d="M0,0 L7,3.5 L0,7 Z"', 'd="M1000,1000 L1007,1003.5 L1000,1007 Z"')
        self.assertFalse(self.checks(s)["schematic_direction"]["passed"])
        self.assertFalse(self.checks(self.mutate_node("arrow", refX="100000"))["schematic_direction"]["passed"])

    def test_rejects_active_external_entity_and_effect_resources(self):
        svg = self.oracle["artifacts"]["figure.svg"]
        for unsafe in ('<!DOCTYPE svg [<!ENTITY e SYSTEM "file:///etc/passwd">]>' + svg,
                       svg.replace('</svg>', '<use href="file:///etc/passwd"/></svg>'),
                       svg.replace('</svg>', '<image href="https://example.invalid/figure.png"/></svg>'),
                       svg.replace('<g font-family=', '<g style="display:none" font-family=', 1),
                       svg.replace('fill="#FFFFFF"', 'fill="url(file:///etc/passwd)"', 1),
                       svg.replace('</svg>', '<script>1</script></svg>')):
            with self.subTest(unsafe=unsafe[-80:]), self.assertRaises(UnsafeSVG):
                parse_static_svg(unsafe)

    def test_equivalent_coordinate_scaling(self):
        # Existing protocol permits rescaling viewBox units, not just 1200x720.
        import re
        root = ET.fromstring(self.oracle["artifacts"]["figure.svg"])
        definitions = set()
        for node in root.iter():
            if node.tag.endswith("defs"):
                definitions.update(node.iter())
        pattern = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?")
        scale = lambda v: format(float(v)*.01, ".14g")
        attrs = {"x", "y", "x1", "x2", "y1", "y2", "cx", "cy", "r", "rx", "ry", "width", "height", "font-size", "stroke-width"}
        for node in root.iter():
            if node in definitions:
                continue
            for key, value in list(node.attrib.items()):
                if key in attrs and pattern.fullmatch(value):
                    node.set(key, scale(value))
                elif key in {"points", "d", "viewBox", "stroke-dasharray"}:
                    node.set(key, pattern.sub(lambda m: scale(m.group()), value))
                elif key == "transform" and value.startswith("rotate("):
                    nums = pattern.findall(value)
                    node.set(key, "rotate("+nums[0]+" "+" ".join(scale(v) for v in nums[1:])+")")
        s = copy.deepcopy(self.oracle)
        s["artifacts"]["figure.svg"] = ET.tostring(root, encoding="unicode")
        for bounds in s["answer"]["panel_bounds"].values():
            bounds[:] = [v*.01 for v in bounds]
        self.assertTrue(all(c["passed"] for c in self.checks(s).values()))


class RenderingEvidence(unittest.TestCase):
    def test_missing_renderer_never_fabricates_rendered_receipt(self):
        c = get_case("NRB09", 0)
        s = reference_submission(c)
        with tempfile.TemporaryDirectory() as dest, patch("nrb.rendering.renderer_identity", side_effect=RendererUnavailable("not installed")):
            with self.assertRaises(RendererUnavailable):
                render_svg(s["artifacts"]["figure.svg"], Path(dest)/"no.png", case_hash=c["case_hash"],
                           submission_hash=fingerprint(s), evaluator_identity={"test": "identity"})
            self.assertFalse((Path(dest)/"no.png").exists())

    def test_render_check_cli_exposes_per_control_errors_without_claiming_review(self):
        from scripts.check_rendering import main
        with tempfile.TemporaryDirectory() as dest, patch("sys.argv", ["check_rendering.py", "--out", str(Path(dest)/"controls")]), patch("scripts.check_rendering.render_svg", side_effect=RendererUnavailable("contract fixture: child renderer failed with exact diagnostic")), patch("sys.stdout", new_callable=io.StringIO) as output:
            status = main()
        summary = json.loads(output.getvalue())
        self.assertEqual(status, 2)
        self.assertEqual(summary["render_status"], "unavailable")
        self.assertEqual(summary["review_status"], "unassessed")
        self.assertEqual({row["label"] for row in summary["render_errors"]}, {"oracle", "minimalpoint", "zerostroke", "whitecover", "emptydiagram", "offcanvastext", "nestedopacity", "emptymarker"})
        self.assertTrue(all("exact diagnostic" in row["error"] for row in summary["render_errors"]))

    def test_actual_cairosvg_empty_marker_draws_same_pixels_as_no_arrowhead(self):
        try:
            importlib.metadata.version("CairoSVG")
        except importlib.metadata.PackageNotFoundError:
            self.skipTest("CairoSVG not installed: actual empty-marker runtime regression unavailable")
        case = get_case("NRB09", 0)
        empty = negative_controls(reference_submission(case))["emptymarker"]
        original_svg = empty["artifacts"]["figure.svg"]
        no_arrowhead = copy.deepcopy(empty)
        root = ET.fromstring(original_svg)
        arrow = next(node for node in root.iter() if node.attrib.get("id") == "displacement-arrow")
        del arrow.attrib["marker-end"]
        no_arrowhead["artifacts"]["figure.svg"] = ET.tostring(root, encoding="unicode")
        identity = {"evaluation_schema_version": "test-empty-marker", "evaluator_digest": "test"}
        with tempfile.TemporaryDirectory() as dest:
            receipts = []
            for label, submission in (("empty", empty), ("no-arrowhead", no_arrowhead)):
                path = Path(dest)/(label+".png")
                kwargs = dict(case_hash=case["case_hash"], submission_hash=fingerprint(submission), evaluator_identity=identity)
                receipt = render_svg(submission["artifacts"]["figure.svg"], path, **kwargs)
                self.assertEqual(receipt["renderer"]["name"], "CairoSVG")
                self.assertTrue(receipt["rendered"])
                self.assertEqual(validate_render_receipt(receipt, submission["artifacts"]["figure.svg"], png_path=path, **kwargs), [])
                receipts.append(receipt)
            self.assertEqual((Path(dest)/"empty.png").read_bytes(), (Path(dest)/"no-arrowhead.png").read_bytes())
        self.assertEqual(empty["artifacts"]["figure.svg"], original_svg)
        self.assertEqual(receipts[0]["raw_svg_sha256"], hashlib.sha256(original_svg.encode()).hexdigest())
        self.assertNotEqual(receipts[0]["raw_svg_sha256"], receipts[1]["raw_svg_sha256"])
        self.assertEqual(receipts[0]["normalization"]["empty_marker_reference_count"], 1)
        self.assertEqual(receipts[0]["normalization"]["empty_marker_ids"], ["arrow"])
        self.assertEqual(receipts[1]["normalization"]["empty_marker_reference_count"], 0)
        checks = {row["id"]: row for row in t09.grade(case, empty)}
        self.assertFalse(checks["schematic_direction"]["passed"])
        self.assertEqual(sum(row["points"] for row in checks.values() if row["passed"]), 65)

    def test_actual_optional_renderer_and_receipt_binding(self):
        try:
            renderer_identity()
        except RendererUnavailable as exc:
            self.skipTest(str(exc))
        c = get_case("NRB09", 0)
        s = reference_submission(c)
        svg = s["artifacts"]["figure.svg"]
        identity = {"evaluation_schema_version": "test-render-v1", "evaluator_digest": "test"}
        with tempfile.TemporaryDirectory() as dest:
            png = Path(dest)/"figure.png"
            kwargs = dict(case_hash=c["case_hash"], submission_hash=fingerprint(s), evaluator_identity=identity)
            receipt = render_svg(svg, png, **kwargs)
            self.assertTrue(receipt["rendered"])
            with self.assertRaises(FileExistsError):
                render_svg(svg, png, **kwargs)
            self.assertEqual(validate_render_receipt(receipt, svg, png_path=png, **kwargs), [])
            for key in ("case_hash", "submission_hash", "raw_svg_sha256", "output_png_sha256", "evaluator_identity", "display_width_mm"):
                bad = copy.deepcopy(receipt)
                bad[key] = {} if key == "evaluator_identity" else "tampered"
                self.assertTrue(validate_render_receipt(bad, svg, png_path=png, **kwargs), key)
            self.assertTrue(validate_render_receipt(receipt, svg, png_path=None, **kwargs))
            png.write_bytes(png.read_bytes() + b"changed")
            self.assertIn("actual PNG hash mismatch", validate_render_receipt(receipt, svg, png_path=png, **kwargs))


if __name__ == "__main__":
    unittest.main()

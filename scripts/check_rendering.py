#!/usr/bin/env python3
"""Render public NRB09 controls into a reviewer-owned evidence directory.

This writes *unassessed* reviewer templates. A raster or a successful XML check
never marks the essential rendered-legibility responsibility as passed.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

# Support a source checkout without requiring editable installation.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nrb.core import fingerprint, get_case, reference_submission
from nrb.rendering import RendererUnavailable, render_svg, validate_render_receipt
from nrb.tasks import t09


def negative_controls(submission):
    """Seven deliberately defective figures, each changing one visual duty."""
    variants = {}
    for name in ("minimalpoint", "zerostroke", "emptydiagram", "offcanvastext", "nestedopacity", "emptymarker"):
        changed = copy.deepcopy(submission)
        root = ET.fromstring(changed["artifacts"]["figure.svg"])
        ids = {node.attrib["id"]: node for node in root.iter() if "id" in node.attrib}
        if name == "minimalpoint":
            for group in ("observations", "residual-points"):
                for node in ids[group]:
                    node.set("r", "0.000001")
        elif name == "zerostroke":
            ids["signal-model"].set("stroke-width", "0")
        elif name == "emptydiagram":
            for ident in ("mass", "spring", "damper"):
                node = ids[ident]
                node.clear()
                node.tag = "{http://www.w3.org/2000/svg}g"
                node.set("id", ident)
        elif name == "offcanvastext":
            for node in root.iter():
                if node.tag.endswith("text"):
                    node.set("x", "100000")
        elif name == "nestedopacity":
            group = ids["observations"]
            parent = next(p for p in root.iter() if group in list(p))
            index = list(parent).index(group)
            parent.remove(group)
            wrapper = ET.SubElement(parent, "{http://www.w3.org/2000/svg}g", {"opacity": "0.5"})
            parent.remove(wrapper)
            parent.insert(index, wrapper)
            wrapper.append(group)
            group.set("opacity", "0.5")
        elif name == "emptymarker":
            ids["arrow"].clear()
            ids["arrow"].set("id", "arrow")
        changed["artifacts"]["figure.svg"] = ET.tostring(root, encoding="unicode")
        variants[name] = changed
    changed = copy.deepcopy(submission)
    changed["artifacts"]["figure.svg"] = changed["artifacts"]["figure.svg"].replace(
        "</svg>", '<rect x="0" y="0" width="1200" height="720" fill="#FFFFFF"/></svg>')
    variants["whitecover"] = changed
    return variants


def run(output_dir, seed=0, dpi=144.0):
    output_dir = Path(output_dir)
    if output_dir.is_symlink() or (output_dir.exists() and any(output_dir.iterdir())):
        raise ValueError("Use an empty trusted reviewer output directory")
    output_dir.mkdir(parents=True, exist_ok=True)
    case = get_case("NRB09", seed)
    oracle = reference_submission(case)
    try:
        from nrb.provenance import evaluator_identity
        identity = evaluator_identity()
    except ImportError:
        # Standalone development has an explicit limited identity, never a fake
        # current evaluator digest. The final integrated evaluator supplies it.
        identity = {"mode": "development-rendering-only", "source_sha256": hashlib.sha256(
            (Path(__file__).resolve().parents[1] / "nrb" / "rendering.py").read_bytes()).hexdigest()}
    cases = {"oracle": oracle, **negative_controls(oracle)}
    results = []
    unavailable = False
    for label, submission in cases.items():
        folder = output_dir / label
        folder.mkdir()
        svg = submission["artifacts"]["figure.svg"]
        (folder / "figure.svg").write_text(svg, encoding="utf-8")
        (folder / "submission.json").write_text(json.dumps(submission, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        static = t09.grade(case, submission)
        failed = [c["id"] for c in static if c["passed"] is not True]
        if label == "oracle" and failed:
            raise AssertionError("Oracle static checks failed: " + ", ".join(failed))
        if label not in {"oracle", "whitecover"} and not failed:
            raise AssertionError("Static negative control escaped: " + label)
        item = {"label": label, "case_hash": case["case_hash"], "submission_hash": fingerprint(submission),
                "static_failed_checks": failed, "static_points": sum(c["points"] for c in static if c["passed"] is True),
                "expected_review_outcome": "pass" if label == "oracle" else "fail",
                "review_required": True}
        try:
            receipt = render_svg(svg, folder / "figure.png", case_hash=case["case_hash"],
                                 submission_hash=item["submission_hash"], evaluator_identity=identity, dpi=dpi)
            errors = validate_render_receipt(receipt, svg, case_hash=case["case_hash"],
                                            submission_hash=item["submission_hash"], evaluator_identity=identity,
                                            png_path=folder / "figure.png")
            if errors:
                raise AssertionError(errors)
            (folder / "render-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
            item.update(render_status="rendered", render_receipt=f"{label}/render-receipt.json", png=f"{label}/figure.png")
        except RendererUnavailable as exc:
            item.update(render_status="unavailable", render_error=str(exc))
            unavailable = True
        item["reviewer_result"] = {"id": "rendered_legibility", "outcome": "unassessed",
                                   "inspected_whole_figure": False, "inspected_at_180mm": False,
                                   "evidence": "", "rationale": ""}
        results.append(item)
    files = {str(path.relative_to(output_dir)): hashlib.sha256(path.read_bytes()).hexdigest()
             for path in sorted(output_dir.rglob("*")) if path.is_file()}
    manifest = {"schema_version": "nrb-render-controls-v1", "task_id": "NRB09", "seed": seed,
                "evaluator_identity": identity, "display_width_mm": 180.0,
                "scope": "Public classical synthetic oscillator only. Rasterization is not visual acceptance.",
                "render_status": "unavailable" if unavailable else "rendered", "review_status": "unassessed",
                "controls": results, "material_sha256": files}
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="empty trusted reviewer evidence directory")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--dpi", type=float, default=144.0)
    args = parser.parse_args()
    result = run(args.out, args.seed, args.dpi)
    print(json.dumps({"render_status": result["render_status"], "review_status": result["review_status"],
                      "controls": len(result["controls"]), "manifest": str(args.out / "manifest.json"),
                      "render_errors": [{"label": item["label"], "error": item["render_error"]}
                                        for item in result["controls"] if "render_error" in item]}))
    return 2 if result["render_status"] == "unavailable" else 0


if __name__ == "__main__":
    raise SystemExit(main())

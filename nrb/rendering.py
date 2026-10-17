"""Optional, bounded SVG rasterization and reviewer-owned rendering receipts.

The evaluator core remains stdlib-only. A receipt says that an allowed static SVG
was rasterized; it does not say that the figure is readable or scientifically
correct. Only a reviewer who actually inspects the PNG may make those judgments.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

RECEIPT_SCHEMA = "nrb-svg-render-v1"
DISPLAY_WIDTH_MM = 180.0
MAX_SVG_BYTES = 2_000_000
MAX_NODES = 20_000
MAX_PIXELS = 16_000_000
SVG_NS = "http://www.w3.org/2000/svg"
# No use/image/foreignObject, animation, CSS, nested viewports, external font or
# resource elements. Only local marker references may request another object.
ALLOWED_TAGS = {"svg", "g", "defs", "marker", "title", "desc", "metadata", "rect",
                "circle", "ellipse", "line", "polyline", "polygon", "path", "text", "tspan"}
URL_ATTRIBUTES = {"marker-start", "marker-mid", "marker-end"}


class UnsafeSVG(ValueError):
    """Input is outside the benchmark's deliberately narrow static protocol."""


class RendererUnavailable(RuntimeError):
    """No usable optional renderer exists; no rendering claim may be made."""


def _tag(node):
    return node.tag.split("}")[-1]


def parse_static_svg(text):
    """Parse only self-contained SVG. This does not establish visual quality."""
    if not isinstance(text, str) or len(text.encode("utf-8")) > MAX_SVG_BYTES:
        raise UnsafeSVG("SVG must be a UTF-8 string of at most 2 MB")
    lowered = text.lower()
    if any(x in lowered for x in ("<!doctype", "<!entity", "@import", "<?xml-stylesheet")):
        raise UnsafeSVG("DTD, entities and stylesheets are forbidden")
    # An optional XML declaration is harmless. Other processing instructions
    # have no role in the permitted static drawing format.
    if "<?" in re.sub(r"^\s*<\?xml\s[^?]*\?>", "", text, count=1).lower():
        raise UnsafeSVG("SVG processing instructions are forbidden")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise UnsafeSVG("Invalid SVG XML") from exc
    if root.tag not in ("svg", "{" + SVG_NS + "}svg"):
        raise UnsafeSVG("Root must be an SVG element")
    by_id = {}
    count = 0
    for node in root.iter():
        count += 1
        if count > MAX_NODES:
            raise UnsafeSVG("SVG has too many elements")
        name = _tag(node)
        if name not in ALLOWED_TAGS or ("}" in node.tag and not node.tag.startswith("{" + SVG_NS + "}")):
            raise UnsafeSVG("Noneditable, active, or unsupported SVG element")
        if name == "svg" and node is not root:
            raise UnsafeSVG("Nested SVG viewports are outside the coordinate protocol")
        for key, value in node.attrib.items():
            local = key.split("}")[-1].lower()
            if "}" in key and key != "{http://www.w3.org/XML/1998/namespace}space":
                raise UnsafeSVG("Namespaced resource attributes are forbidden")
            if local.startswith("on") or local in {"href", "src", "base", "style", "filter", "mask", "clip-path"}:
                raise UnsafeSVG("Active/external resources and CSS/effects are forbidden")
            if "url" in value.lower():
                if local not in URL_ATTRIBUTES or not re.fullmatch(r"url\(#[A-Za-z0-9_-]+\)", value):
                    raise UnsafeSVG("Only local marker resource references are permitted")
            # display/visibility hiding is excluded by the candidate protocol;
            # cumulative opacity is checked separately on essential objects.
            if local == "display" and value.strip().lower() == "none":
                raise UnsafeSVG("Hidden elements cannot satisfy the figure contract")
            if local == "visibility" and value.strip().lower() in {"hidden", "collapse"}:
                raise UnsafeSVG("Hidden elements cannot satisfy the figure contract")
            if local in {"opacity", "fill-opacity", "stroke-opacity"}:
                try:
                    number = float(value)
                except (ValueError, OverflowError):
                    raise UnsafeSVG("Opacity must be a finite number") from None
                if not math.isfinite(number) or not 0 <= number <= 1:
                    raise UnsafeSVG("Opacity must be between zero and one")
        if "id" in node.attrib:
            ident = node.attrib["id"]
            if ident in by_id:
                raise UnsafeSVG("Duplicate SVG ID")
            by_id[ident] = node
    parents = {child: parent for parent in root.iter() for child in parent}
    stack = [(root, 0)]
    while stack:
        node, depth = stack.pop()
        if depth > 128:
            raise UnsafeSVG("SVG nesting exceeds the safe static-review limit")
        stack.extend((child, depth + 1) for child in node)
    return root, by_id, parents


def svg_viewbox(root):
    try:
        view = [float(v) for v in root.attrib["viewBox"].replace(",", " ").split()]
        if len(view) != 4 or not all(math.isfinite(v) for v in view) or min(view[2:]) <= 0:
            raise ValueError
    except (ValueError, KeyError, TypeError, OverflowError):
        raise UnsafeSVG("A finite positive root viewBox is required") from None
    # Physical checks use width/viewBox width. Unequal viewport stretching would
    # violate that mapping; the reviewer raster always preserves the aspect.
    if root.attrib.get("preserveAspectRatio", "xMidYMid meet") not in {"xMidYMid meet", "xMidYMid", "none"}:
        raise UnsafeSVG("Unsupported viewport alignment")
    return view


def _remove_empty_marker_references(root):
    """Omit no-op marker references only in the renderer's private SVG copy.

    CairoSVG 2.8.2 crashes when it computes a bounding box for a marker with no
    graphic descendants. Such a marker paints nothing; removing the reference
    preserves that drawing semantics. Do not remove nonempty, degenerate or
    malformed graphic contents: those require normal renderer error handling.
    The candidate SVG and its raw hash remain untouched.
    """
    graphics = {"rect", "circle", "ellipse", "line", "polyline", "polygon", "path", "text", "tspan"}
    empty_ids = {node.attrib["id"] for node in root.iter()
                 if _tag(node) == "marker" and "id" in node.attrib
                 and not any(_tag(child) in graphics for child in node.iter() if child is not node)}
    removed = []
    for node in root.iter():
        for attribute in URL_ATTRIBUTES:
            value = node.attrib.get(attribute, "")
            match = re.fullmatch(r"url\(#([A-Za-z0-9_-]+)\)", value)
            if match and match.group(1) in empty_ids:
                del node.attrib[attribute]
                removed.append(match.group(1))
    return removed


def _png_dimensions(data):
    if len(data) < 33 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("Renderer did not produce PNG bytes")
    width, height = struct.unpack(">II", data[16:24])
    if not width or not height or width * height > MAX_PIXELS:
        raise ValueError("Invalid or excessive PNG dimensions")
    return width, height


def _limits():
    """Apply bounded child resources on POSIX, without affecting the grader."""
    if os.name == "posix":
        import resource
        resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
        resource.setrlimit(resource.RLIMIT_FSIZE, (64_000_000, 64_000_000))
        # Inkscape and fontconfig need more address space than the SVG itself.
        resource.setrlimit(resource.RLIMIT_AS, (2_000_000_000, 2_000_000_000))


def renderer_identity():
    """Choose an actually installed renderer; never report a simulated render."""
    try:
        version = importlib.metadata.version("CairoSVG")
        return {"name": "CairoSVG", "version": version}
    except importlib.metadata.PackageNotFoundError:
        binary = shutil.which("inkscape")
        if not binary:
            raise RendererUnavailable("Install optional CairoSVG==2.8.2 (or Inkscape) to rasterize SVG") from None
        try:
            proc = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=10,
                                  check=True, preexec_fn=_limits if os.name == "posix" else None)
        except (OSError, subprocess.SubprocessError) as exc:
            raise RendererUnavailable("Installed Inkscape cannot be queried") from exc
        line = next((s for s in proc.stdout.splitlines() if s.startswith("Inkscape ")), "")
        if not line:
            raise RendererUnavailable("Inkscape returned no version identity")
        return {"name": "Inkscape", "version": line[len("Inkscape "):]}


def render_svg(svg_text, output_png, *, case_hash, submission_hash, evaluator_identity,
               display_width_mm=DISPLAY_WIDTH_MM, dpi=144.0):
    """Safely render into a *trusted reviewer-selected* PNG path and bind bytes.

    Candidate artifact paths must never select ``output_png``. The child has no
    permitted external SVG resources, bounded input, geometry, CPU, memory and
    wall time. The optional renderer is never imported by normal core grading.
    """
    output = Path(output_png)
    if output.exists() or output.is_symlink():
        raise FileExistsError("Refusing existing reviewer PNG output")
    root, _, _ = parse_static_svg(svg_text)
    view = svg_viewbox(root)
    if display_width_mm != DISPLAY_WIDTH_MM or not math.isfinite(dpi) or not 72 <= dpi <= 300:
        raise ValueError("Review rendering requires 180 mm width and 72–300 DPI")
    if not isinstance(evaluator_identity, dict) or not evaluator_identity:
        raise ValueError("A nonempty evaluator identity is required")
    if not all(isinstance(v, str) and re.fullmatch(r"[0-9a-f]{64}", v) for v in (case_hash, submission_hash)):
        raise ValueError("case_hash and submission_hash must be SHA256 hex strings")
    width = round(display_width_mm / 25.4 * dpi)
    height = round(width * view[3] / view[2])
    if height <= 0 or width * height > MAX_PIXELS:
        raise UnsafeSVG("Requested SVG aspect ratio exceeds the safe raster size")
    display_width_mm, dpi = float(display_width_mm), float(dpi)
    renderer = renderer_identity()
    # Ignore candidate viewport lengths in the reviewer copy. Explicit sizing
    # and this normalized aspect ratio make a viewBox-unit rescaling equivalent.
    root.set("width", str(width))
    root.set("height", str(height))
    root.set("preserveAspectRatio", "xMidYMid meet")
    empty_marker_references = _remove_empty_marker_references(root)
    normalized = ET.tostring(root, encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="nrb-svg-render-") as temporary:
        env = dict(os.environ)
        env["INKSCAPE_PROFILE_DIR"] = temporary
        env["XDG_CACHE_HOME"] = temporary
        if renderer["name"] == "CairoSVG":
            program = ("import sys,cairosvg; "
                       f"cairosvg.svg2png(bytestring=sys.stdin.buffer.read(),output_width={width},"
                       f"output_height={height},unsafe=False,write_to=sys.stdout.buffer)")
            command = [sys.executable, "-c", program]
        else:
            command = [shutil.which("inkscape"), "--pipe", "--export-type=png", "--export-filename=-",
                       f"--export-width={width}", f"--export-height={height}"]
        try:
            result = subprocess.run(command, input=normalized, capture_output=True, timeout=30, env=env,
                                    preexec_fn=_limits if os.name == "posix" else None)
        except (OSError, subprocess.SubprocessError) as exc:
            raise RendererUnavailable("Optional SVG renderer did not complete") from exc
        if result.returncode:
            raise RendererUnavailable("Optional SVG renderer failed: " + result.stderr.decode("utf-8", "replace")[-500:])
        png = result.stdout
    actual_width, actual_height = _png_dimensions(png)
    if (actual_width, actual_height) != (width, height):
        raise RendererUnavailable("Renderer output dimensions differ from the requested raster")
    output = Path(output_png)
    if output.is_symlink():
        raise ValueError("Reviewer PNG output cannot be a symlink")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output.parent, prefix=".nrb-render-", delete=False) as handle:
        temporary_output = Path(handle.name)
        handle.write(png)
    try:
        # Hard-link publication is exclusive: a concurrent writer cannot be
        # silently overwritten between the initial path check and completion.
        os.link(temporary_output, output)
    finally:
        temporary_output.unlink(missing_ok=True)
    return {"schema_version": RECEIPT_SCHEMA, "task_id": "NRB09", "rendered": True,
            "case_hash": case_hash, "submission_hash": submission_hash,
            "evaluator_identity": json.loads(json.dumps(evaluator_identity, allow_nan=False)),
            "raw_svg_sha256": hashlib.sha256(svg_text.encode("utf-8")).hexdigest(),
            "output_png_sha256": hashlib.sha256(png).hexdigest(), "renderer": renderer,
            "display_width_mm": display_width_mm, "dpi": dpi, "width_px": width, "height_px": height,
            "normalization": {"version": "nrb-static-svg-normalize-v1",
                              "empty_marker_reference_count": len(empty_marker_references),
                              "empty_marker_ids": sorted(set(empty_marker_references)),
                              "normalized_svg_sha256": hashlib.sha256(normalized).hexdigest()}}


def validate_render_receipt(receipt, svg_text, *, case_hash, submission_hash, evaluator_identity, png_path):
    """Return validation errors against actual reviewer PNG bytes, never a URL.

    This authenticates binding and provenance within the trusted review process;
    it cannot authenticate an untrusted reviewer or infer visual acceptance.
    """
    errors = []
    if not isinstance(receipt, dict):
        return ["render receipt must be an object"]
    expected = {"schema_version": RECEIPT_SCHEMA, "task_id": "NRB09", "rendered": True,
                "case_hash": case_hash, "submission_hash": submission_hash,
                "evaluator_identity": evaluator_identity,
                "raw_svg_sha256": hashlib.sha256(svg_text.encode("utf-8")).hexdigest(),
                "display_width_mm": DISPLAY_WIDTH_MM}
    for key, value in expected.items():
        if type(receipt.get(key)) is not type(value) or receipt.get(key) != value:
            errors.append("render receipt identity mismatch: " + key)
    renderer = receipt.get("renderer")
    if not isinstance(renderer, dict) or renderer.get("name") not in {"CairoSVG", "Inkscape"} or not isinstance(renderer.get("version"), str) or not renderer["version"].strip():
        errors.append("render receipt lacks an actual renderer name/version")
    try:
        root, _, _ = parse_static_svg(svg_text)
        view = svg_viewbox(root)
        dpi = receipt["dpi"]
        if isinstance(dpi, bool) or not isinstance(dpi, (float, int)) or not math.isfinite(dpi) or not 72 <= dpi <= 300:
            raise ValueError("invalid DPI")
        width = round(DISPLAY_WIDTH_MM / 25.4 * dpi)
        height = round(width * view[3] / view[2])
        if isinstance(receipt.get("width_px"), bool) or isinstance(receipt.get("height_px"), bool) or (receipt.get("width_px"), receipt.get("height_px")) != (width, height):
            errors.append("render receipt raster dimensions mismatch")
        if png_path is None:
            raise ValueError("actual reviewer PNG path is required")
        path = Path(png_path)
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 64_000_000:
            raise ValueError("invalid reviewer PNG file")
        data = path.read_bytes()
        if _png_dimensions(data) != (width, height):
            errors.append("actual PNG dimensions mismatch")
        if hashlib.sha256(data).hexdigest() != receipt.get("output_png_sha256"):
            errors.append("actual PNG hash mismatch")
    except (ValueError, KeyError, TypeError, OverflowError, OSError) as exc:
        errors.append("render evidence unavailable or invalid: " + str(exc))
    return errors

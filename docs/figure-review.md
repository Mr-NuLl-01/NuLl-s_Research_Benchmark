# NRB09 figure visibility and actual rendering

NRB09 still awards 70 automatic points and 30 independent review points. An
editable, correctly bound SVG is necessary evidence, but cannot establish that a
figure is readable. In particular, a final opaque rectangle can cover all the
scientific content while preserving every XML coordinate and data value.

## Minimum static screen

The declared figure is assessed at **180 mm displayed width**. A viewBox unit is
arbitrary: the physical conversion is `180 / viewBox_width` mm per unit. A
consistent rescaling of SVG coordinates, fonts, declared panel bounds and widths
therefore preserves the result.

The following are **provisional engineering thresholds** for excluding nearly
invisible essential objects, not universal journal standards or a visual quality
score:

- Data circle diameter: at least 0.20 mm.
- Essential model and schematic strokes: at least 0.08 mm.
- Effective paint opacity: at least 0.30, after multiplying every ancestor's
  compositing `opacity` and applying inherited `fill-opacity` or `stroke-opacity`.

The minimum screen also requires nondegenerate painted schematic primitives,
actual graphic contents within the referenced marker viewport, a rightward
positive-displacement arrow, and required labels with approximate bounds inside
the root canvas. Empty `g` nodes and empty marker definitions do not count as
visible content. These checks deliberately use a restricted coordinate protocol;
unsupported transforms cannot silently satisfy the essential geometry checks.
Text bounds are an estimate, not a font-layout engine. Conservative path hulls
include curve controls and can overestimate a curve's occupied space. Occlusion,
contrast, label collision, and mechanical connection semantics require rendering
and review.

## Safe rasterization and material binding

Normal automatic grading uses only Python's standard library. The separate
reviewer rendering path uses installed **CairoSVG** (the pinned CI renderer is
`CairoSVG==2.8.2`) or installed Inkscape. It first parses the restricted static SVG
protocol: DTD/entities, scripts, CSS, bitmaps, external links/resources, animation,
effects, and nested SVG viewports are disallowed. Only local marker resource
references are permitted. Input, element count, raster dimensions, child CPU,
memory and wall time are bounded. Rendering normalizes the reviewer viewport to
180 mm while preserving the root viewBox aspect ratio.

The output path belongs to the trusted reviewer workspace, never to a candidate
artifact. The rendering receipt binds the exact original SVG bytes, case hash,
submission hash, evaluator identity, renderer name/version, raster dimensions,
180 mm review width, and actual PNG hash. Receipt verification reads the trusted
PNG file again; a self-declared PNG hash or candidate URL is insufficient. A
receipt authenticates material binding within the review process. It is not an
independent signature from the renderer and does not authenticate an untrusted
reviewer.

A missing optional renderer is reported as unavailable. No receipt or rendered
claim is fabricated. A successful rasterizer run also leaves visual acceptance
**unassessed**. For the essential rendered-legibility responsibility, the review
must include a bound valid receipt, actual reviewer PNG bytes, an explicit
acknowledgment that the whole figure and 180 mm equivalent were inspected, and a
specific evidence location and rationale. LLM review remains provisional.

## Reproduce the public synthetic controls

```bash
python -m pip install 'CairoSVG==2.8.2'
python -m unittest discover -s tests -p test_figure_visibility.py -v
python scripts/check_rendering.py --out /tmp/nrb-render-controls
```

The script requires an empty trusted output directory. It writes an SVG,
submission, actual PNG and rendering receipt for the oracle and each of the
seven controls. `manifest.json` hashes those materials and supplies explicitly
unassessed reviewer-result structures. It exits nonzero if an optional renderer
is unavailable or a required static negative control escapes. It never invents
an actual inspection or marks a reviewer template as passed.

| Figure | Static expectation | Actual review focus |
|---|---|---|
| oracle | 70/70 | All three panels, labels, curve, observations, residuals and schematic remain visible. |
| minimalpoint | Reject observation/residual geometry | The data points effectively disappear. |
| zerostroke | Reject model geometry | The fixed model curve disappears. |
| whitecover | May remain 70/70 | Whole figure is blank; must fail actual rendered-legibility review. |
| emptydiagram | Reject schematic | Named schematic objects contain no painted primitives. |
| offcanvastext | Reject labels/layout | Required text lies outside the canvas and is absent in the raster. |
| nestedopacity | Reject observation geometry | Ancestor opacity 0.5 × child opacity 0.5 produces faint observations at 0.25. |
| emptymarker | Reject schematic | The displacement line has no visible arrowhead. |

## Scope of the implementation inspection

On 2026-10-17, the eight control figures were actually rasterized locally by
Inkscape 1.2.2 (`b0a8486541, 2022-12-01`) and all eight full PNGs were opened for
LLM inspection. The 180 mm equivalent rendering at 144 DPI was 1020 × 612 pixels;
the complete oracle was readable at this scale. The missing objects, missing
labels, faint observations, absent arrowhead, and blank white-cover figure were
visible as described above. The opacity limit excludes the intentionally faint
control; this is engineering calibration against the normal oracle and extreme
controls, not a universal perceptual threshold.

This inspection covers these public classical synthetic oscillator assets only.
It is not human review, physical monitor calibration, validation of arbitrary SVG
semantics, or acceptance of future candidate figures. Every candidate still
requires its own exact-material rendering and review. CI produces current bound
materials and unassessed templates; an earlier inspection is not transferred to
new SVG bytes or a revised evaluator.

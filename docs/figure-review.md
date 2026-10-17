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

A renderer-copy normalization handles an empty-marker incompatibility in
CairoSVG 2.8.2. Its `draw_markers` implementation attempts to index a missing
bounding box when a referenced marker contains no graphic contents. The first
CairoSVG CI run rendered seven figures successfully and failed only on this
empty-marker control. A marker with no graphic or text descendants paints
nothing, so the private renderer copy removes references to that marker. It does
not add an arrowhead, edit candidate SVG bytes, or turn the static schematic
failure into a pass. Nonempty or degenerate graphic contents are not removed by
this rule. The receipt records the number/IDs of removed references and the
normalized SVG hash, alongside the unchanged original SVG hash. An actual
CairoSVG regression verifies that the empty-marker PNG is byte-identical to the
explicit no-arrowhead reference. A successful render remains distinct from
rendered-legibility acceptance.

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

## Scope of the implementation inspections

On 2026-10-17, two distinct local material sets were rendered and inspected:

| Material | Renderer | Evaluator digest | Actual inspection |
|---|---|---|---|
| [Historical Inkscape controls](../validation/v0.2.0/render-controls/README.md) | Inkscape 1.2.2 (`b0a8486541, 2022-12-01`) | `1b872d660f0a56f05c9ec390a90a150bed78d9af918efa81c5a8fcfb0f4e7cba` | All eight complete PNGs individually opened; provisional oracle pass and seven control failures. |
| [Post-fix CairoSVG controls](../validation/v0.2.0/render-controls-cairo/README.md) | CairoSVG 2.8.2 with cairocffi 1.7.1 | `8dfb824a40469966a1fb8def3de39611608c28b2b8d84557210f40e44fb8d20b` | All eight freshly generated complete PNGs individually opened again; provisional oracle pass and seven control failures. |

Both sets use a 180 mm equivalent target at 144 DPI, producing 1020 × 612
rasters. The CairoSVG set contains a fresh independent review, not a transfer of
the earlier Inkscape judgment. Its raw SVG, PNG, case, submission and evaluator
bindings were verified; normalized SVG hashes were independently rebuilt and
checked for all eight figures. Only `emptymarker` removes one no-op reference;
the observed image contains the displacement shaft without an arrowhead, and
its static schematic check still fails. All other normalization counts are zero.

The complete CairoSVG oracle was readable at this scale. Missing points, the
missing model curve, absent schematic objects, missing labels, faint observations,
the absent arrowhead and the fully blank white-cover figure were visible as
described above. Faint observations remain partly visible: their rejection uses
the disclosed provisional effective-opacity threshold, not a universal human
perceptual claim. The white-cover figure still earns 70 automatic points and
fails actual rendered-legibility inspection.

Each directory contains its unmodified generation manifest with unassessed
reviewer templates, an independent `reviewer-results.json` recording the
subsequent image inspection, and a final file-hash manifest. Original commit
identity is recorded as null when unavailable rather than invented. The old
Inkscape material was preserved unchanged after the renderer fix.

These inspections cover the exact public classical synthetic oscillator assets
only. They are LLM provisional reviews, not human review, physical monitor
calibration, validation of arbitrary SVG semantics, or acceptance of future
candidate figures. Every candidate still requires its own exact-material
rendering and review. An identical raster under a different evaluator commit is
still a distinct provenance record and does not inherit an earlier pass.

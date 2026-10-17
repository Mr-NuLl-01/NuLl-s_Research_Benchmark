# Frozen 8dfb824 CairoSVG rendering controls

All eight public synthetic oscillator figures were freshly rendered by
CairoSVG 2.8.2 with cairocffi 1.7.1, then individually opened as complete
1020 x 612 PNGs for LLM provisional inspection. The target is 180 mm equivalent
at 144 DPI. No human review or physical display calibration is claimed.

`manifest.json` is the unmodified generator output, with script-stage unassessed
reviewer templates. `reviewer-results.json` separately records the subsequent
actual image inspection and binds it to the manifest, receipts, exact source
identity and all SVG/PNG/submission hashes. The actual evaluator commit is null
because no revision could be established in this local workspace; it is not
replaced with an assumed commit.

Each control subdirectory contains its original `figure.svg`, actual
`figure.png`, `submission.json` and `render-receipt.json`. Receipt normalization
metadata was verified by rebuilding the private renderer copy and recomputing
its hash. Only `emptymarker` removes one reference to the entirely empty marker;
all other controls remove zero. The raw SVG is unchanged. The observed result
is a displacement line without a head, not a repaired arrow or an accepted
schematic. Its static schematic check still fails at 65 automatic points.

The oracle is provisionally readable. All seven negative controls fail their
specified visible-content responsibility. `whitecover` remains completely blank
white despite 70 automatic points. `nestedopacity` remains partly visible but
fails the task's disclosed provisional effective-opacity threshold.

`material-sha256.json` records all other bundle files. The earlier sibling
`render-controls` directory is preserved as historical evidence under its old
source identity and Inkscape renderer. These findings are fresh inspection
records and must not be silently reassigned to a later commit or evaluator.
No model API calls, private research or secret credentials were involved.

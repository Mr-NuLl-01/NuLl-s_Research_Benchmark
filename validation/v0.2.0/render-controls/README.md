# Frozen-source NRB09 rendering controls

This directory contains public synthetic scientific-figure validation material.
All eight complete PNGs were rendered and then individually opened for LLM
inspection. Results are provisional LLM judgments, not human review or physical
monitor calibration. The raster target is 180 mm equivalent at 144 DPI.

`manifest.json` is the unmodified generated material manifest and contains the
script-stage unassessed reviewer templates. `reviewer-results.json` is the
separate subsequent image-inspection record, bound to that manifest, the exact
render receipts, PNGs, SVGs, submissions and evaluator identity. Each asset
subdirectory contains `figure.svg`, `figure.png`, `render-receipt.json` and the
public synthetic `submission.json` used to generate it.

The oracle is provisionally readable. All seven defective controls fail their
specified visible-content responsibility. In particular, `whitecover` is blank
white despite retaining 70 automatic points; XML/data success alone cannot pass
actual rendered-legibility review. `nestedopacity` remains partly visible but
fails the explicitly provisional effective-opacity threshold.

`material-sha256.json` records final bundle file hashes, excluding itself.
An identical raster generated under a different evaluator commit is a distinct
provenance record; these inspection decisions are not silently transferred.
The actual source identity records an unavailable commit as null rather than
inventing a revision. No model API calls or private research were involved.

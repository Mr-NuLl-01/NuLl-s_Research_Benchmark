# SIGNAL IN MOTION — editable reference implementation

10.000 seconds · 1920 × 1080 · 24 fps · 240 video frames · stereo 48 kHz audio.

This is a procedural motion-design/compositing demonstration, not an inference or quality result for a named video model. Its Python code, matte logic, scene geometry, typography, and music are editable. It contains no model-specific hidden judging rubric.

## Reproduce

Requires Python 3.12, the dependencies in requirements.txt, and FFmpeg 7.1 (including libx264). Both scripts run from any working directory. No web service, model, credentials, or generated-image tool is called.

From the extracted package root, run:

```sh
python -m pip install -r demo_project/requirements.txt
python demo_project/run_demo.py
python demo_project/source/audit.py shared_assets/source.mp4
```

Install FFmpeg separately if it is not already available. The supplied Python dependencies are pinned; the commands do not invoke a model or network API after dependencies are installed.

run_demo.py copies the two unchanged fonts and their license from shared_assets into demo_project/assets, then explicitly passes shared_assets/source.mp4 to the compositor. It creates local audio and matte caches, followed by demo_project/reference.mp4. It does not overwrite the supplied reference at tracks/B/reference.mp4. The source MP4 is not duplicated. No EXR directory is silently preferred.

For manual control, run source/prepare_assets.py with --source /absolute/path/to/source.mp4 from the demo_project directory, then source/render.py. The supplied soundtrack.wav is the deterministic output of prepare_assets.py; --audio can regenerate it without decoding the source, and --matte regenerates only actor frames. The Python scripts locate their own project directory; pass an absolute source path when invoking them from another working directory.

The delivered original QA is at ../evaluator/reference_qa/. An audit rerun checks technical conditions; it does not perform or assert a new visual review or subjective listening test.

Tested with Python 3.12.14, NumPy 2.3.5, Pillow 12.3.0, SciPy 1.17.0, FFmpeg 7.1.5. Library or encoder-version changes can affect compressed bytes. The exact supplied source MP4 is required for matched pixels; hashing that input is part of qa_report.json.

## Editable layers and timing

- 0.0–1.5 s: SIGNAL IN MOTION. Radial signal halos, short restrained readable title jitter.
- 1.5–4.0 s: STAY IN ORBIT. Individual glyphs follow a depth-sorted elliptical orbit, with projected tangents and side foreshortening. Back glyphs are composited before the actor, front glyphs after it.
- 4.0–5.5 s: CAPTURE / SPLIT / RECOMBINE. Three vertical panels, distinct source crops/scales, synchronized source time.
- 5.5–7.0 s: RIDE THE WAVE. Continuous wave paths and a scrolling typographic ribbon with explicit front/back masking.
- 7.0–8.5 s: LOCK ON. A true hexagonal aperture contracts and expands.
- 8.5–10.0 s: SIGNAL RECEIVED. Abstract stage, sparse geometric confetti, stable graphics and readable title for the final 0.5 s.

Every output frame n uses original source frame n. There is no looping, interpolation, speed change, newly invented actor motion, or time-offset panel. The native source actor occupies only part of the camera frame; close-ups reveal that source-resolution limit.

## Keying and changes

The code crops a 550 × 720 region at x=800, y=292, wide enough for the early pointing gesture. It uses a chroma matte, a connected-component garbage mask to exclude studio lights/markers, green-spill suppression, and a cuff-following floor mask. A deliberate foreground stage lip covers the lowest sole/contact pixels. Hair retains the original warm backlight. This is an editable procedural key, not an assertion of feature-film-quality manual rotoscoping.

Other changes: scene-linear footage was converted to display BT.709 by the source-preparation workflow; the demo adds reframing, scale changes, composites, typography, procedural geometry, original music, and H.264/AAC encoding. No original film music, dialogue, or sound effects are included.

## Rights and credits

Footage: Tears of Steel, shot 04_3b. (CC) Blender Foundation | https://mango.blender.org . Licensed under CC BY 3.0: https://creativecommons.org/licenses/by/3.0/ . Raw source: https://media.xiph.org/tearsofsteel/tearsofsteel-footage-exr/04_3b/linear_hd/ . See SOURCE_LICENSE.md and the source evidence files for attribution and limitations. No endorsement by the original creators or performers is implied. This package is a technical creative demonstration, not an advertisement using the performer's likeness.

Fonts: DejaVu Sans Condensed Bold and DejaVu Sans Mono, supplied unchanged. See assets/DejaVu-LICENSE.txt for the Bitstream Vera / DejaVu license and notices.

New motion-design code, original composition elements and synthesized soundtrack are licensed under the repository MIT license by approval for this integration. The incorporated footage retains CC BY 3.0 and the fonts retain their original terms. See ../PACKAGE_LICENSE_STATUS.md and ../LICENSE.txt; no blanket CC0 claim is made.

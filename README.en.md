# NuLl's Research Benchmark · V1.1

[简体中文](README.zh-CN.md) · **English** · [Detailed usage](docs/v1.1/usage.en.md) · [Offline scoring page](docs/v1.1/scorecard.html)

A practical benchmark for scientific coding, research work, and optional creative production: **10 coding tasks, 6 research tasks, 3 original optional extensions, and one new optional video test with A/B modes**. Each task asks for inspectable deliverables, with separate judgments for score, essential completion, and work that remains unassessed.

V1.1 adds an optional video-production test with two selectable modes, a bilingual manual-scoring page, and evaluator corrections. The original 19 V1.0 candidate prompts remain frozen. **V1.1 scores must not be pooled with reports from an older evaluator**, even when the prompt is unchanged. Regrade retained submissions with one pinned evaluator before comparing them.

This is a public development benchmark. Difficulty levels are design estimates, not calibration from real model runs. Reference solutions, wrong-answer controls, mock runs, and infrastructure checks are not AI performance results.

## Choose a task

| Tasks | Work assessed | Scoring |
|---|---|---|
| C01–C05 | Measurement CSVs, bootstrap, heat-equation debugging, multilayer optics, stiff integration | 70 automatic + 30 manual |
| C06–C10 | Fortran drift–diffusion, inverse heat conduction, anisotropic elliptic PDEs, coupled drift–diffusion–Poisson, inverse reaction–diffusion debugging | 70 automatic + 30 manual |
| R01–R03 | Editable scientific figures, Python plotting, conservative English revision | 100 manual |
| R04–R06 | Results/discussion from evidence, close reading and bounded reproduction, mini-review synthesis | 100 manual |
| X01–X03 | Interactive HTML, a scientific explainer video, original instrumental audio | 100 manual; optional |
| New video option · X04/A or X05/B | A: 10-second motion design from a written brief; B: visual reconstruction of a supplied reference | 100 manual per mode; separate A/B profiles |

C06 and C09 use Fortran 2008; the other coding tasks use Python. Detailed contracts are in [the original single-file tasks](tasks/v1.0/) and [the V1.1 video tasks](tasks/v1.1/). X04 and X05 require generated media bundles, not just their Markdown instructions. X02 remains the original scientific-explainer task.

The new video option is excluded from the default core scope. Choose A (`X04`), B (`X05`), or explicitly both. Coding, research, original optional media, Video A (`optional_video_a`), and Video B (`optional_video_b`) are separate profiles. There is no scientific-plus-entertainment grand total, and A/B scores are not interchangeable.

## Start with one task

### 1. Prepare the evaluator

Use Python 3.11+ and Git. Docker is needed to execute unknown coding submissions safely. Run these commands in the **evaluator's environment**:

```bash
git clone https://github.com/Mr-NuLl-01/NuLl-s_Research_Benchmark.git
cd NuLl-s_Research_Benchmark
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m nrb_v1 --version
python -m nrb_v1 identity

docker build -t nrb-v1:local -f environments/v1/Dockerfile .
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`. The Docker image supplies GNU Fortran and scientific/media tools; you do not need a separate host compiler for Docker grading. Docker is unnecessary for generating task packets, packaging files, or reviewing research/media submissions.

### 2. Give the candidate only its inputs

For a single coding task:

```bash
python -m nrb_v1 export --format files --tasks C04 --seed 17 \
  --dest candidates/C04-s17
```

Give the candidate `candidates/C04-s17/C04.md` in a fresh session and an isolated environment. Do not give it the repository URL, evaluator checkout, reference implementation, old submissions, or evaluator files. A new folder alone does not isolate a tool-using agent.

For a video task:

```bash
python -m nrb_v1 generate-pack --task X04 --dest candidates/X04
# For Video B instead:
python -m nrb_v1 generate-pack --task X05 --dest candidates/X05
```

Give the candidate the selected generated directory. It contains the task, footage, soundtrack, fonts, and license notices; only X05 receives the reference video. Keep the demonstration renderer and evaluator-only material out of both candidate environments.

### 3. Collect actual outputs and create a review

After the candidate finishes C04, place its real files in `received/C04/`:

```bash
python -m nrb_v1 pack --task C04 --from-dir received/C04 \
  --out received/C04.json
python -m nrb_v1 review-packet --task C04 --seed 17 \
  --submission received/C04.json --execution docker \
  --dest reviews/C04
```

Open the downloaded [scoring page](docs/v1.1/scorecard.html) in a browser and import `reviews/C04/review.json` with its matching `automatic.json`. Inspect the source, report, and actual test results; enter ratings, evidence, essential outcomes, and reviewer identity. Export the completed review into the same review directory, preserving the original artifacts and `automatic.json`.

```bash
python -m nrb_v1 grade --task C04 --seed 17 \
  --submission received/C04.json --review reviews/C04/review.json \
  --out results/C04-final.json
python -m nrb_v1 summarize --tasks C04 \
  --reports results/C04-final.json --out results/C04-summary.json
```

The scoring page is a review editor. The final CLI command checks the ledger against the submission, artifact bytes, rubric, and evaluator identity. New output paths must not already exist.

## What a score means

- Coding automatic points are out of **70**, not a complete score out of 100. The remaining 30 points and essential responsibilities require review.
- Research and media tasks require actual inspection. Opening metadata, extracting frames, or reading a script does not establish that a reviewer watched or listened to the deliverable.
- Unavailable execution or incomplete review stays unassessed. Unknown runtime, token usage, and cost stay `null`; they are not zero.
- `complete` means essential checks and review are complete. `quality_qualified` additionally requires a complete total of at least 80. A high score cannot cancel an essential failure.
- Human review and provisional LLM review are recorded separately. Files scored without model/harness provenance do not establish a controlled model comparison.

Use [the detailed guide](docs/v1.1/usage.en.md) for video review, task subsets, offline/resourceful conditions, harnesses, timing, result interpretation, and troubleshooting. [Scoring rules](docs/v1/scoring.md) explain the scientific judgments; [research rubrics](docs/v1/research-guide.md) cover R01–R06 and X01–X03.

## Reproducibility and validation

Pin the evaluator commit, content digest, task/bundle hashes, model version, tools/skills, budget, environment image, seeds, and reviewer. Keep separate output directories for each model, configuration, and attempt.

```bash
python -m unittest discover -s tests_v1 -v
python -m nrb_v1 selftest --tasks coding --seeds 0,17,2026 \
  --include-mutants --execution docker --image nrb-v1:local \
  --out validation-run.json
```

These commands validate the infrastructure and known controls; they do not call a candidate model. `trusted` is available only for controlled reference self-tests, with host dependencies installed. Never use it for unknown submissions.

Check [GitHub Actions](https://github.com/Mr-NuLl-01/NuLl-s_Research_Benchmark/actions/workflows/ci.yml) for the exact commit you use. [V1.0 validation records](docs/v1/validation.md) are historical evidence, not certification of later V1.1 changes. The legacy `nrb` CLI and `questions/` follow V0.2; use `nrb-v1` or `python -m nrb_v1` here.

## Licenses

Repository code, documentation, and original synthetic tasks retain the existing [MIT license](LICENSE). Third-party assets keep their own licenses:

- Weissgerber (2015) and Crameri (2020): CC BY 4.0; Rougier (2014): CC0 1.0. Exact scope and credits: [research sources](sources/v1/README.md).
- X04/X05 footage: *Tears of Steel*, shot 04_3b, Blender Foundation, CC BY 3.0. The supplied clip is a frame selection and color/encoding transformation; reference-video modifications also require preserved attribution.
- Bundled DejaVu fonts retain their Bitstream Vera/DejaVu terms. They are not relicensed as CC0 or MIT.

Keep the [video package's notices](sources/v1.1/signal-in-motion/PACKAGE_LICENSE_STATUS.md) and included `LICENSES/` with redistributed media. Cite the benchmark's exact commit and the underlying sources. No endorsement by the original creators or performers is implied.

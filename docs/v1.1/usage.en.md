# V1.1 usage guide

[简体中文](usage.zh-CN.md) · [English overview](../../README.en.md) · [Scoring page](scorecard.html)

The evaluator commands below run from the repository root. They prepare inputs and grade collected work; they do not automatically select or call a model. Use a new destination for each run. Candidate output paths such as `received/C04/` assume you have already collected the requested files.

## 1. Decide what you are comparing

Choose tasks, model/version, allowed tools, budget, attempts, and review method **before** inspecting results.

| Condition | Candidate access | How to report it |
|---|---|---|
| Response-only | Task inputs and one response; no execution tools | Keep separate from tool-using agents |
| Offline agent/research | Supplied inputs plus a fixed local runtime; no web search or external asset retrieval | Default closed-input condition |
| Resourceful | Predeclared additional tools, services, search, or skills | A separately named experimental condition, with resources, costs, and interventions recorded |

“Resourceful” is a protocol choice, not a CLI `--mode` flag. It changes the original offline contract and must be declared as an extension. Provider connectivity needed for model inference is not permission for web browsing or repository access. Build environments and download permitted inputs before starting the timed task.

Each task uses a fresh conversation and isolated candidate environment. Give it **only its candidate file/bundle**, not a GitHub URL or repository checkout. The evaluator contains reference code, tests, and demonstration projects. Do not expose those through mounted folders, shell access, history, or shared retrieval tools. See [closed evaluation](../v1/closed-evaluation.md).

C01–C10 form the coding profile; R01–R06 the research profile; X01–X03 the original optional profile. The new optional video test has two selectable modes: A/X04 and B/X05, reported under separate `optional_video_a` and `optional_video_b` profiles. Choose one mode or explicitly both; neither is included in `coding` or `required`. Predeclare which optional tasks are enabled. A selected task with no output is a missing deliverable, not a reason to shrink the denominator afterward.

## 2. Install the evaluator

### Core setup

Requirements: Git and Python 3.11+. Commands use a POSIX shell; in PowerShell use `.venv\Scripts\Activate.ps1` instead of the activation line.

```bash
git clone https://github.com/Mr-NuLl-01/NuLl-s_Research_Benchmark.git
cd NuLl-s_Research_Benchmark
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m nrb_v1 --version
python -m nrb_v1 identity
python -m nrb_v1 list --tasks all
```

Before a controlled comparison, check out the chosen commit and save `identity` output with the run. `nrb-v1` and `python -m nrb_v1` are equivalent entry points; the older `nrb` command is the V0.2 protocol.

The core evaluator has no mandatory third-party Python dependencies. Packet generation, packing, and manual review do not require Docker. The original research HTML files already contain their readings and images; normal use does not rebuild or download those sources.

### Unknown code: Docker

Install Docker and start its daemon, then:

```bash
docker version
docker build -t nrb-v1:local -f environments/v1/Dockerfile .
docker image inspect nrb-v1:local
```

The checked-in Dockerfile supplies Python 3.12, GNU Fortran, NumPy, SciPy, Matplotlib, Pillow, CairoSVG, FFmpeg, and DejaVu fonts. Record the actual image ID/digest and hardware limits. Docker grading of C06/C09 compiles Fortran in the container, so a host `gfortran` installation is unnecessary for that path.

A trusted local reference self-test needs host `gfortran` for C06/C09. Check with `gfortran --version`; install it through your operating system's package manager if needed. The complete test suite also has compiler-dependent checks. Missing infrastructure must remain unscored, not be represented as candidate failure or a passed test.

Never execute unknown submissions through the trusted backend. `grade --execution none` deliberately omits code execution; it is not an alternative way to obtain automatic scientific scores.

For video review, use a real video player with audio. FFmpeg/ffprobe can measure formats, duration, and frame counts, but do not replace watching the output. Host media tools are separate from tools inside the Docker image.

## 3. Prepare exactly the selected task

### Original single-file tasks

The fixed seed-17 inputs are under [tasks/v1.0/](../../tasks/v1.0/). C tasks are Markdown; R01–R06 and X01–X03 are self-contained HTML.

Generate one task or an explicit subset:

```bash
python -m nrb_v1 export --format files --tasks C04 --seed 17 \
  --dest candidates/C04-s17
python -m nrb_v1 export --format files --tasks C04,C06 --seed 2026 \
  --dest candidates/selected-s2026
```

Give each candidate only its own file. `catalog.json` is evaluator bookkeeping. Use `--tasks coding` for C01–C10, `research` for R01–R06, `required` for those 16 tasks, `optional` for X01–X05, or `video` for X04/X05. `list --tasks all` shows the installed version's full registry. Use explicit task IDs when you need an exact subset.

Coding seeds generate parameter variants. Research/media prompts are fixed: changing a seed label does not create a new scientific sample. Keep fixed tasks at the published seed 17, and record repeat attempts as separate runs.

Download and open a complete HTML task, including expandable readings. A GitHub preview screenshot is incomplete input. A text-only harness seeing base64 strings has not received visual evidence; provide the embedded images through its actual multimodal input path or declare that limitation.

### New optional video test: choose A or B

```bash
# Choose mode A:
python -m nrb_v1 generate-pack --task X04 --dest candidates/X04
# Or choose mode B:
python -m nrb_v1 generate-pack --task X05 --dest candidates/X05
```

These are two modes of one optional video test: X04/A is written-brief production; X05/B is reference reconstruction. Run only the mode you selected, or explicitly enable both. Both use *SIGNAL IN MOTION*: a 10-second, 1920×1080, 24 fps, 240-frame H.264 video, using the supplied footage and soundtrack with six specified scenes. X05 additionally includes `reference.mp4`; X04 must not receive or inspect it.

The generated directory includes `TASK.md`, `COPY.txt`, `source.mp4`, `soundtrack.wav`, fonts under `assets/`, `LICENSES/`, and a blank `RUN_RECORD.template.json`. `INPUT_MANIFEST.json` records sizes and SHA-256 identities for the supplied files; its `packet_hash` covers the bundle, not only the prompt. Hand over the whole directory with its structure intact. A standalone `tasks/v1.1/X04.md` or `X05.md` is not the complete media input. Do not send `demo_project/`, evaluator scene specifications, QA records, or the full source package to either candidate. X05 may observe its reference but must not copy reference frames into its output.

Required video outputs are `output.mp4`, `source.zip`, `README.md`, `LICENSES.md`, and `run-record.json`. The ZIP holds editable sources; the README gives reproduction commands/dependencies; license notes preserve credits and changes; the run record distinguishes measured usage from unknown values. Keep the first output and retries separately. An editing plan, screenshot, or renderer source alone does not count as a playable video.

## 4. Collect and package submissions

For C04, place `solution.py`, `report.md`, and `tests.py` in `received/C04/`. Fortran tasks use `main.f90` instead of `solution.py`. Individual tasks define the scientific API and any additional requirements.

```bash
python -m nrb_v1 pack --task C04 --from-dir received/C04 \
  --out received/C04.json
python -m nrb_v1 pack --task R01 --from-dir received/R01 \
  --out received/R01.json
python -m nrb_v1 pack --task X04 --from-dir received/X04 \
  --out received/X04.json
```

Run only the commands for outputs you actually collected. `pack` embeds UTF-8 text and base64-encodes binary files. It preserves relative filenames, rejects symlinks and unsafe paths, and currently caps the total decoded artifact payload at 100 MiB. Package the requested final outputs, not temporary frames, caches, or redundant copies of inputs.

A JSON envelope looks like this; the example text is not a valid solution:

```json
{
  "task_id": "C04",
  "artifacts": {
    "solution.py": "Full source text",
    "report.md": "Full scientific report",
    "tests.py": "Full independent test source"
  },
  "answer": {}
}
```

A filename, remote link, pseudocode, or promise to deliver later is not the artifact's contents.

## 5. Automatic scoring and manual review

### Coding

To obtain only the automatic report:

```bash
python -m nrb_v1 grade --task C04 --seed 17 \
  --submission received/C04.json --execution docker --image nrb-v1:local \
  --out results/C04-auto.json
```

For a reviewable package, use:

```bash
python -m nrb_v1 review-packet --task C04 --seed 17 \
  --submission received/C04.json --execution docker --image nrb-v1:local \
  --dest reviews/C04
```

`review-packet` runs automatic scoring itself, so the first command is optional. It creates the task, `artifacts/`, `submission.json`, `automatic.json`, and a blank `review.json`.

Review scientific reasoning, independent tests, and implementation/handoff quality. Actually run candidate tests in an answer-free isolated environment; inspect whether their expected results are independent of the implementation. Do not run unknown `tests.py` on the evaluator host or mount the repository/Home/Docker socket into the candidate environment.

### Research and original media tasks

```bash
python -m nrb_v1 review-packet --task R01 --seed 17 \
  --submission received/R01.json --dest reviews/R01
```

Use the same command with R02–R06 or X01–X03 as appropriate. Review the actual rendered files, not just source code. Inspect figures at their intended display size; operate HTML controls; watch the full video; listen to the full audio. Use [the detailed research rubrics](../v1/research-guide.md) and the generated ledger.

### X04/X05 video review

```bash
python -m nrb_v1 evaluate-skeleton --task X04 \
  --submission received/X04.json --dest reviews/X04
```

`evaluate-skeleton` prepares the formal review materials and an `inputs/` directory containing source media and the X05 reference; it does not automatically judge video quality or certify completion. Existing `review-packet` and `grade` also recognize the new IDs. Both review-generation commands preserve the bound `inputs/` bundle; `evaluate-skeleton` additionally provides `video-rubric.md`.

Watch `inputs/source.mp4` and the full `artifacts/output.mp4` with sound, and record timecoded findings. For X05, also watch the supplied reference and compare scene structure, scale, motion paths, timing, occlusion, and transitions. A single pixel-distance metric is not the reference-reconstruction score. Record actual technical measurements and the required media-review metadata; leave observations unperformed when you could not make them. Check delivered project sources, run instructions, and credits.

The `media_review` section requires observations in all six intervals: 0–1.5, 1.5–4, 4–5.5, 5.5–7, 7–8.5, and 8.5–10 seconds. Record actual times inside each interval, visual findings, source/reference playback, and output listening. The soundtrack check has no extra visual-score weight: if audio is missing, document it and fail the audio core requirement; unavailable observation remains unassessed. Technical probe data alone cannot complete these fields. See [the video protocol](video-protocol.md).

X04 has seven manual dimensions; X05 has eight, including reference reconstruction. Their weights and criteria come from their own generated reviews. Do not substitute X02's scientific-explainer rubric.

## 6. Use the bilingual offline scoring page

1. Download [scorecard.html](scorecard.html) and open the file in a modern browser. The GitHub source preview does not run the page. Switch between Chinese and English as needed.
2. Import the evaluator-generated `review.json` and matching `automatic.json`. The automatic report is read-only. Inspect the actual files in the review directory separately.
3. Enter the real reviewer identity. For each criterion, choose an integer 0–4 and add concrete evidence and a rationale. Check each essential responsibility as pass, fail, or unassessed. Complete observations and, for video, required media-review fields honestly.
4. Export a draft if work is incomplete. Missing ratings stay `null`. A checked export validates required fields; it does not prove the reviewer observed the media or replace final CLI validation.
5. Save the downloaded review as `reviews/C04/review.json`, or use another filename inside the same review directory and pass that exact path below. Keep `automatic.json` and `artifacts/` beside it; for X04/X05 also keep the complete generated `inputs/` directory unchanged. Retain a copy of the original blank ledger if useful.

Edits stay in the current browser page: export a draft before closing or reloading. The page edits a review ledger; it does not execute code, call a model, or write directly into your review directory. Do not change task IDs, seeds, hashes, rubric weights, criteria, or artifact manifests to force a mismatch through.

Finalize C04:

```bash
python -m nrb_v1 grade --task C04 --seed 17 \
  --submission received/C04.json --review reviews/C04/review.json \
  --out results/C04-final.json
```

Finalize X04 after completing its review:

```bash
python -m nrb_v1 grade --task X04 \
  --submission received/X04.json --review reviews/X04/review.json \
  --out results/X04-final.json
```

The CLI rechecks the current evaluator, task, submission, automatic evidence, and actual artifact bytes. For X04/X05 it also verifies the review directory’s actual input media, fonts, notices, and manifest; changed files or symlinks are rejected. Editing a submission after review requires a fresh review packet. LLM reviewers must record their model and prompt fingerprint; their conclusions remain provisional and must not be pooled with human reviews.

## 7. Summarize the scope you actually selected

For one task:

```bash
python -m nrb_v1 summarize --tasks C04 \
  --reports results/C04-final.json --out results/C04-summary.json
```

For an explicit subset, collect matching submissions/reviews first:

```bash
python -m nrb_v1 grade-suite --tasks C04,C06 --seed 17 \
  --submissions received --reviews reviews --execution docker \
  --out results/selected-final.json
python -m nrb_v1 summarize --tasks C04,C06 \
  --reports results/selected-final.json --out results/selected-summary.json
```

`grade-suite` expects `received/C04.json`, `received/C06.json`, etc., and `reviews/C04/review.json`, etc. Missing selected submissions retain failure rows. Missing reviews retain pending review. Use `--tasks coding` only when the intended scope is all ten coding tasks; a two-task mean is not a ten-task result.

If both video modes were explicitly enabled and reviewed:

```bash
python -m nrb_v1 summarize --tasks X04,X05 \
  --reports results/X04-final.json results/X05-final.json \
  --out results/video-profiles.json
```

This preserves separate Video A and Video B profiles. Multiple tracks do not receive a pooled grand total. Do not combine models, configurations, human/LLM review cohorts, or repeated attempts into one summary. Duplicate task/seed pairs are rejected; summarize each attempt separately.

### Important report fields

| Field | Interpretation |
|---|---|
| `auto_points` / `auto_scored_max` | Earned automatic points and coverage; coding maximum is 70 |
| `review_points` / `total` | Manual points and complete total; unfinished values remain `null` |
| `completion_status` | `failed`, `infrastructure_unscored`, `pending_review`, or `complete` |
| `critical_failures` / `pending_items` | Essential failures and unresolved work; inspect both |
| `quality_qualified` | True only after essential completion and a complete total ≥80 |
| `completion_authority` | Human assessment or provisional LLM assessment |
| `cohort_check` | Recorded configuration checks and missing provenance |
| `comparison_eligible` | Explicit runner eligibility when available; absence is not proof of controlled conditions |

An automatic 70/70 alone is still pending review. Infrastructure failures stay unscored. If a submission both lacks required files and has unavailable execution, it may be `failed` while `pending_items` still lists unknown checks. Do not read status without its evidence.

## 8. Model timing, tokens, and reproducibility

Record the model/provider/version, exact input hashes, harness and version, prompts/settings, tools/skills, network rules, hardware, time budget, retry/best-of-N policy, and human interventions. Preserve raw output and provider logs.

Separate end-to-end wall time, model-generation time, rendering time, and downloads where measured. File-only `grade` cannot reconstruct generation duration, tokens, or cost; those fields remain `null`. The command runner records subprocess wall time, not pure model inference time, and does not infer provider token usage. Do not relabel render time as model speed or fill unavailable values with zero.

For videos, start from the [run-record template](../../sources/v1.1/signal-in-motion/evaluator/run_record.template.json). Keep measured values and their method. Candidate timeouts are task outcomes; an inaccessible compiler/container is an infrastructure issue.

## 9. Harness integration

All task types can use the file workflow. Automatic Inspect AI, promptfoo, and Harbor adapters are **coding-only**. Video tasks use real files and the manual media-review path.

```bash
python -m nrb_v1 export --format jsonl --tasks C04 --seed 17 \
  --dest exports/jsonl-C04
python -m nrb_v1 export --format promptfoo --tasks C04 --seed 17 \
  --dest exports/promptfoo-C04
python -m nrb_v1 export --format harbor --tasks C04 --seed 17 \
  --image nrb-v1:local --dest exports/harbor-C04
```

The pinned integrations are Inspect AI 0.3.281, promptfoo 0.124.1, and Harbor 0.24.0. Harbor's pinned runtime requires Python 3.12+; promptfoo requires Node.js 22.22.0+ (the repository CI configuration uses Node 24). These are optional dependencies, not requirements for manual scoring. See [the harness instructions](../v1/usage.md) for provider configuration and invocation.

Inspect defaults to response-only. promptfoo's exported default is an empty mock with no model call. Harbor separates candidate and verifier containers; retain that separation. Framework scalar scores represent automatic points/70 only.

The native `run --command-json` runner does not transport X04/X05 media bundles. For its supported tasks, it launches a host process. Its new candidate directory is not a security boundary. Use an independently isolated wrapper for controlled closed-input runs, and record `--model-label`, `--harness-label`, and `--metadata`. Do not interpret a plumbing mock as a real model trial.

## 10. V1.1 comparability and validation

See [release notes](release-notes.md) and [scoring corrections](../v1/scoring-fixes-20261017.md). V1.1 corrects numeric output typing, import/initialization-error handling, independent residual checks, and result eligibility/cohort checks. Real-valued scientific quantities accept equivalent JSON integer/float representations; discrete counts remain exact integers. Initialization failure cannot stand in for a required per-case exception. Claimed zero residuals do not replace independent equation checks.

Because scoring changed, retain original artifacts but regenerate reviews/reports with a single pinned evaluator. Never patch historical report hashes or mix old and new reports. Even unchanged task files do not make the scoring versions interchangeable. Known configuration conflicts are rejected; missing provenance remains unknown. Public tests and reference results do not calibrate real model performance.

```bash
python -m unittest discover -s tests_v1 -v
python -m nrb_v1 selftest --tasks coding --seeds 0,17,2026 \
  --include-mutants --execution docker --image nrb-v1:local \
  --out validation-run.json
```

Check [CI for the exact commit](https://github.com/Mr-NuLl-01/NuLl-s_Research_Benchmark/actions/workflows/ci.yml). The [archived V1.0 validation](../v1/validation.md) applies to its recorded commit only. A local pass, a CI definition, and a completed remote CI run are different evidence.

## 11. Common problems

- **Output already exists:** choose a new destination; preserve previous runs rather than silently overwriting evidence.
- **Docker/image/compiler unavailable:** fix the evaluator runtime and regrade. Do not count missing infrastructure as a zero-score model answer.
- **Review binding mismatch:** use the same fixed evaluator and original submission; restore the matching `automatic.json` and artifacts or regenerate the review. Do not edit hashes.
- **Required observation missing:** actually inspect the relevant file, then record evidence; otherwise keep it unassessed.
- **Scorecard import/export succeeds but CLI rejects it:** the CLI also checks local file bytes and evaluator identity. Keep the exported ledger beside its original `automatic.json`, `artifacts/`, and, for X04/X05, unchanged `inputs/`.
- **Missing video inputs:** use `generate-pack`; downloading only the task Markdown does not supply footage, soundtrack, fonts, or the X05 reference.
- **Mixed-cohort or duplicate report error:** separate models/configurations/attempts, then summarize only the intended task IDs.
- **No final mean:** inspect missing tasks, unscored execution, pending review, and comparison eligibility. Do not manufacture a mean from the successful subset.

## 12. Source licenses

The repository's [MIT license](../../LICENSE) covers its code, documentation, and original synthetic content. Research papers and figures retain their article-specific licenses: P1/P3 CC BY 4.0 and P2 CC0 1.0; see [source scope and credits](../../sources/v1/README.md).

The X04/X05 *Tears of Steel* footage is Blender Foundation material under CC BY 3.0. Preserve attribution, license links, and transformation notices for the supplied clip and derived reference. DejaVu fonts retain their own Bitstream Vera/DejaVu terms. See [video license status](../../sources/v1.1/signal-in-motion/PACKAGE_LICENSE_STATUS.md) and the generated bundle's `LICENSES/`. These assets are not relicensed by the repository's MIT license; their inclusion does not imply creator or performer endorsement.

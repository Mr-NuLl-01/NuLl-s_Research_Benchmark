# V1.0 daily research and optional modality tasks

The six required research tasks represent daily scientific work after the ten coding tasks. Each is delivered as one self-contained downloadable HTML with its instructions, data, actual reference images or full supplied paper text, output contract and public criteria. The candidate needs no repository files or network connection. There is no candidate answer key. The research metadata generator is `nrb_v1.research.tasks()`.

| ID | Daily work | Difficulty | Suggested time | Core evidence to inspect |
| --- | --- | --- | --- | --- |
| R01 | Learn from three actual reference figures and make an original multi-panel scientific SVG | 4/5 | 60 min | Reference-specific design note; data fidelity; live editable text and scientific elements; final-size figure and caption |
| R02 | Python plotting for nearby values, broad dynamic range and signed/censored observations | 4/5 | 60 min | Actual generated plots and runnable code; axis-by-axis scale decisions; uncertainty and observation-status fidelity |
| R03 | Conservative English editing with a scientific fact ledger | 3/5 | 30 min | Edited passage; all quantitative/design/uncertainty/scope facts; disposition of unsupported claims; author queries |
| R04 | Results and discussion from an actual embedded synthetic figure and its data | 4/5 | 50 min | Both input panels; quantitative calculations; separation of observation/inference/mechanism; claim-evidence ledger |
| R05 | Three-paper close reading, explicit/implicit logic and two bounded public-method reproductions | 5/5 | 90 min | Full supplied readings and relevant supplement; source cards; methodological logic; executable synthetic demonstrations and limits |
| R06 | Critical mini-review with evidence SVG, comparative table and valid references | 5/5 | 90 min | Cross-source argument; claim-level source links; source-conditioned table/map; accurate bibliographic records and declared review scope |

Suggested time is descriptive rather than an automatic scoring threshold. Record actual time and environment limits separately. No model-performance values, pilot rankings or completed scientific answers are asserted by this task release.

## Manual score: multidimensional and anchored

Every task has five substantive dimensions whose weights sum to 100. They are not a fixed “70 scientific + 30 presentation” split. The evaluator export contains task-specific anchors for ratings 0, 2 and 4. A reviewer may use 1 or 3 when the evidence falls between adjacent anchors and must explain the intermediate judgment. Compute each dimension as:

`dimension points = dimension weight × rating / 4`

Sum dimension points only when all required dimensions are assessable. Do not convert uninspectable media or an unavailable evaluator into an assumed quality score. Report missing required artifacts as observed omissions when the task was enabled and the artifact could have been supplied; distinguish those omissions from evaluator inability to inspect a valid artifact. A full-data score must include reviewer identity or pseudonym, artifact evidence locations, dimension-level reasons, coverage and separate core-gate outcomes.

Public candidate HTMLs show criterion names and weights plus core requirements. Evaluator anchor strings are excluded from candidate HTMLs. No detector decides whether R03 is “human,” and no automatic phrase blacklist can substitute for preserving the scientific record. Editing quality is evaluated through precision, natural English, evidence boundaries and a fact ledger.

## Core gates remain visible beside the score

Each task defines three core requirements. Record each as `met`, `not_met`, or `not_assessable`, with concrete evidence. A high sum cannot compensate for invented data, invented references, missing actual required modality, a vector figure that is only a flattened screenshot, or a partial synthetic reproduction represented as a complete paper rerun. Report an overall completion status beside the numeric result; do not hide a failed core requirement behind the total. Do not add a new numerical penalty after the weighted rubric has already considered the same omission. These gates specify completion and scientific integrity, while dimension scores preserve partial performance information.

R01 and R02 require scientific scale judgment. A log axis is neither automatically correct nor automatically better. Nearby absolute values, broad positive ranges, signed estimates, zero and censoring involve distinct scientific questions. Review whether the chosen transformation, baseline/offset, uncertainty meaning and alternative diagnostic support those questions. A clearly labelled zoom or paired-difference panel may be appropriate; visual exaggeration or silent data removal is not cured by attractive formatting.

R05 and R06 use actual source papers supplied offline. Reviewers must check claims against those source locations rather than infer correctness from plausible prose or valid-looking DOI strings. Full main article texts, figures, bibliography and supplied-scope boundaries are embedded. P1's complete S1 Text methods/results are also supplied. Missing external code and absent other SI must remain outside any claimed reproduction/read scope. The two R05 synthetic calculations are bounded method demonstrations, not an empirical audit rerun, colour-map optimization or observer study.

## Blind review workflow

1. Export candidate instructions independently from evaluator-only rubrics. Assign the candidate an opaque submission ID; keep model name, vendor, price and earlier scores outside the reviewer packet.
2. Freeze submitted artifact bytes before review and record the task version/environment. File hashes support auditability, not scientific validation.
3. Inspect the actual artifacts: render SVG/HTML, open plots at the requested width, run the supplied local calculation where relevant, and compare claims with the embedded paper/figure/data. For interactive or media tasks, inspect actual behavior and media rather than a script alone.
4. Score dimensions independently with source/artifact evidence. Record core gates independently and state reviewer coverage/uncertainty. Reviewers should not consult another model's submission while scoring the current one.
5. For comparative research claims, use at least two independent human reviews per enabled research task. Resolve material disagreements through a documented adjudication that retains the original ratings. If only one reviewer is available, label the result accordingly; do not claim inter-rater reliability.
6. Publish per-task scores, dimension scores, gate status, coverage, artifact references and disagreement. Keep research results and optional modality results separate. Report the aggregation formula and enabled denominator explicitly; compare models only on a declared common task/modality set.

This release provides anchored review instruments and runnable integrity checks, not evidence that the rubric has already achieved inter-rater reliability or discriminates every pair of models. Pilot results should be added only after actual blind submissions and reviews exist.

## Optional capabilities: X01–X03

| ID | Track | Actual artifact required when enabled | Additional review concerns |
| --- | --- | --- | --- |
| X01 | Offline interactive HTML | One functional self-contained dashboard with embedded data | Correct filtering/counts, scale handling, signed/censored values, keyboard use, exports and absence of network dependencies |
| X02 | Scientific video | Playable 45–60 s encoded video plus timed captions | Source-grounded narrative, synthetic status, visual pacing, actual frames, caption synchronization and licensed credits |
| X03 | Original instrumental audio | Openable original 32 s stereo PCM WAV plus editable source | Composition and narration context, cue timing, clean audio, ingredient provenance, measured technical properties and honest limitations |

These optional tasks have their own five-dimension 100-point rubrics and explicit gates. Enable them only when production and review capability exists. An environment without audio/video capability reports `unavailable` with a concrete reason, and that task is excluded from the enabled-track denominator. A missing modality must never silently receive zero or receive a completion claim from a text-only plan. If an enabled candidate was able to produce the requested modality but omitted it, record the omission and failed completion gate. Do not make optional media capability part of the required six-task research score.

For X03, the absence of an optional encoder or an optional LUFS/true-peak measurement tool is narrower than inability to produce audio. Score the actual deliverable and transparent limitation under the rubric. Do not credit an unperformed loudness or listening check. Narrative-support judgments are bounded because no narration stem is supplied.

## Concrete artifact and observation contract

`required_artifacts` contains only exact canonical filenames, never prose alternatives. Editable design/render/music projects are packaged as `source.zip` with a local README and their natural editable formats. X02 uses `captions.srt`. X03's optional `listening-preview.mp3` is listed in `optional_artifacts` and cannot be required for completion.

Each task also declares `modal_observation_artifacts`, a subset of required outputs that a reviewer must actually view, watch or listen to before certifying visual/media completion. The evaluator observation record should identify the exact filename and SHA-256 of the submitted bytes, the appropriate viewed/watched/listened status, reviewer and substantive inspection notes. A candidate's own assertion that it rendered or listened does not establish independent reviewer observation. Record inability to inspect separately from an observed low-quality or absent artifact. R04 has no generated visual deliverable: its input figure is embedded in the candidate HTML, and a reviewer must still read that input when assessing whether the prose faithfully interprets it. R01's three embedded source images likewise need actual reading during the design/reference assessment.

## Source and integrity checks

`sources/v1/README.md` describes exact article licenses, reading scope, transformations, original assets and reproduction commands. `manifest.json` preserves per-asset URLs and SHA-256 plus article-specific license evidence. P2 is CC0; P1 and P3 are CC BY 4.0. Do not substitute generic publisher licensing assumptions for those exact records.

Run:

```bash
python -m unittest tests_v1.test_research_packets -v
```

The checks verify task coverage, required/optional separation, weighted anchors, evaluator/candidate separation, self-contained resource loading, actual embedded reference figures, substantial readable paper text, an actual live-text input SVG and source-byte provenance. They do not grade candidate scientific reasoning or certify paper conclusions. Scientific/manual visual review remains necessary.

# Optional video tracks / 可选视频赛道

NRB V1.1 adds one optional video evaluation feature with two selectable modes:
X04 (A, prompt-driven production) and X05 (B, reference reconstruction).
The default core task selection excludes both modes.
X02 is unchanged. A and B use independent fresh contexts, identical tools/budgets/retry
rules and common source/audio/font bytes. B additionally receives reference.mp4.
Report two independent manual scores out of 100 under `optional_video_a` and
`optional_video_b`. Never average A/B together or add them to scientific scores.
There are no actual model runs, hidden model rankings or automatic visual scores.

V1.1 新增 X04（文字驱动制作）与 X05（参考视觉重建），不替换 X02。
每条轨道独立新会话、新工作区，模型配置、工具、预算及重试规则保持一致。
A 不获得参考成片、作者实现、评审记录或中间遮罩。B 额外获得参考成片，仍不获得作者实现。
模型无法观看/制作视频时记录不可用，不作为该启用赛道的有效比较运行。

## Prepare a candidate / 生成候选包

Run in an evaluator environment with the complete repository assets:

```bash
python -m nrb_v1 generate-pack --task X04 --dest /tmp/candidate-X04
python -m nrb_v1 generate-pack --task X05 --dest /tmp/candidate-X05
```

Give each candidate its entire generated directory, not just TASK.md. The allowlist
contains TASK.md, COPY.txt, source.mp4, soundtrack.wav, fonts, licenses and a blank
run-record template. Only X05 includes reference.mp4. `INPUT_MANIFEST.json` binds
all file sizes and SHA-256 hashes. Its `packet_hash` hashes the canonical list of
input entries, not only the prompt. `common_assets_sha256` must match across A/B;
full packet hashes differ by design. Unknown usage/cost/time remains null.

`export --format files --tasks video --dest ...` exports the same isolated directories.
Legacy tasks remain single-file exports. Text-only `run`, Inspect, promptfoo and Harbor
adapters do not transport the new media tasks; use a media-capable harness that actually
makes videos accessible. Reading a path, codec report, transcript, or thumbnail does
not establish full video observation. Merely exporting inputs does not run a model.

## Submission and manual review / 交付及人工评阅

Required files: output.mp4, source.zip, README.md, LICENSES.md, run-record.json.
Keep the first output and all retries; do not substitute a human-repaired output.
The ZIP contains editable source, the README reproduction commands/dependencies and
actual run limitations, and LICENSES.md includes source attribution and modifications.

```bash
python -m nrb_v1 pack --task X04 --from-dir received/X04 --out received/X04.json
python -m nrb_v1 evaluate-skeleton --task X04 --submission received/X04.json --dest reviews/X04
# Open inputs/source.mp4, artifacts/output.mp4 and (X05 only) inputs/reference.mp4.
# Fill review.json after real observation, then:
python -m nrb_v1 grade --task X04 --submission received/X04.json --review reviews/X04/review.json --out results/X04.json
```

`evaluate-skeleton` creates an ordinary `nrb-review-v1` ledger and a separate inputs/
directory. It asserts no observation and awards no points. `review-packet` also works and copies the same bound input media;
`evaluate-skeleton` additionally supplies the detailed video rubric. Final grading
rechecks the actual input files beside the ledger, including source/reference/audio,
against the manifest and rejects symlinks or changed bytes. `grade` without a completed
review returns unassessed manual scores. The source/reference are evaluator inputs,
never candidate-submitted artifacts.

All criterion scores are integer levels 0–4, weighted as weight × score / 4. This
follows NRB's existing convention and replaces interpolation in the early standalone
video draft. Technical checks can support 10 manual points but are not automatic
visual-quality grades. The exact bilingual weights and anchors are in
[nrb_rubrics.json](../../sources/v1.1/signal-in-motion/evaluator/nrb_rubrics.json).

### Evidence contract / 观察证据合同

- The existing observation binds actual output.mp4 playback to the submitted SHA-256.
- `media_review` additionally binds full source playback, output listening and (B)
  full reference playback to the correct bytes. Each observation starts false with
  blank evidence. Do not prefill a successful review from the reference QA.
- Record concrete findings and observed timecodes in all six intervals: 0–1.5,
  1.5–4, 4–5.5, 5.5–7, 7–8.5 and 8.5–10 seconds. Orbit/ribbon foreground/background
  changes, hexagonal iris action, keying edges and final copy need actual playback.
- Soundtrack is checked separately without new visual-score weight. `audio_check`
  is present/missing only after evidence. Missing audio requires the audio core gate
  to fail; it does not invent a new weighted audio penalty. Unavailable listening
  or viewing leaves the review open.
- Core requirements are video, source continuity, real depth interaction, soundtrack
  and reproducible/licensed handoff. A high quality score cannot override failure.
- Human and LLM-assisted reviews remain separate cohorts. LLM review is provisional.
  These validation fields support auditability, not proof that a reviewer is truthful.

## Rights and provenance / 权利与来源

Footage: Tears of Steel, shot 04_3b. (CC) Blender Foundation |
https://mango.blender.org . CC BY 3.0: https://creativecommons.org/licenses/by/3.0/ .
Frames 00000–00239, scene-linear RGB to BT.709 conversion, 24 fps encoding; reference
adds reframing, keying, green-spill suppression, compositing, motion graphics and music.
No original film audio is included. No endorsement by creators or performers is implied.
Portrait/privacy rights and trademark exclusions remain applicable.

The new code, prompts, docs, rubrics, original visual elements and procedurally generated
soundtrack explicitly follow the repository MIT license as approved for integration.
Third-party footage remains CC BY 3.0; DejaVu fonts retain Bitstream Vera/DejaVu terms.
No blanket MIT/CC0 relicensing of the combined footage/font content is claimed.

Full notices and original evidence: [component-license statement](../../sources/v1.1/signal-in-motion/PACKAGE_LICENSE_STATUS.md)
and [source provenance](../../sources/v1.1/signal-in-motion/shared_assets/LICENSES/SOURCE_LICENSE.md).
The binary assets are regular repository files, not embedded base64 HTML. The material
manifest verifies every packaged source, prompt, license, demo and evaluator file.

## Version and evidence / 版本与验证

The author demo QA applies only to the supplied reference, not model capability or
fresh V1.1 CI. Historical V1.0 CI remains historical. Preserve exact input hashes,
evaluator commit/digest, runtime metadata, reviewer identity and evidence. Score fixes
change V1.1 evaluation outcomes: regrade earlier candidate submissions consistently;
do not mix old/new evaluator reports. Original V1.0 task files and IDs are retained.

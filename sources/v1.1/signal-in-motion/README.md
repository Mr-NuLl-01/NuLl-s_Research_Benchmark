# SIGNAL IN MOTION · NRB V1.1

Optional X04 (A: prompt-driven design) and X05 (B: reference reconstruction).
These are separate manual video-quality tracks, 100 points each. They do not replace
X02 or contribute to the scientific-coding/research score. No actual model run or
model ranking is supplied.

Prepare candidates from the repository CLI:

    python -m nrb_v1 generate-pack --task X04 --dest /path/to/fresh-X04
    python -m nrb_v1 generate-pack --task X05 --dest /path/to/fresh-X05

Give each candidate only its generated directory, in a fresh independent session
and environment. Do not share this complete source tree: it contains the B reference,
author implementation, evaluator rubrics and reference QA. A never receives those
files. B receives reference.mp4 but no author implementation or evaluator records.

source.mp4 is a 10-second 1920×1012, 24 fps, 240-frame silent CC BY 3.0 derivative.
Both tracks receive identical source, original soundtrack, font and license bytes.
reference.mp4 is the 1920×1080 author demonstration, not a candidate/model result.
Video assets are normal binary files; no base64 media is embedded in task documents.

See ../../../docs/v1.1/video-protocol.md for the CLI, score and observation contract;
evaluator/rubric.md for detailed review guidance; PACKAGE_LICENSE_STATUS.md for
component licenses. demo_project/ is editable evaluator-only reference code.
evaluator/reference_qa/ documents the supplied author demonstration only, not
fresh V1.1 CI or subjective model performance.

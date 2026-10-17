# V1.1.0 release notes / 发布说明

## Compatibility / 兼容性

V1.1 retains C01–C10, R01–R06 and X01–X03 IDs and all 19 frozen V1.0 candidate
files unchanged. Generated legacy coding prompts retain their V1.0.0 header for
byte-identical candidate inputs. The evaluator is version 1.1.0 and scoring schema
`nrb-v1.1`, with a new content identity. One new optional video feature has two selectable manual modes, X04 and X05;
neither enters the default core selection.
The Python module/CLI name remains `nrb_v1` / `nrb-v1` for the V1 family.

Score corrections change outcomes: old/new scores are not directly comparable.
Regrade saved submissions under one fixed evaluator commit/digest; do not copy an
old completed review onto a new evaluator identity. See
[scoring corrections](../v1/scoring-fixes-20261017.md).

评分修复包含数值合同、严格类型、独立残差、执行错误隔离及比较队列保护。
完整修复细节以关联报告和回归测试为准。旧候选题面稳定不等于旧评分结论仍可混比。

## Additions / 新增

- X04: prompt-driven green-screen motion design, optional manual 100-point video track.
- X05: reference reconstruction from the same source/audio, separate manual 100-point track.
- `generate-pack`: allowlisted, hash-verified multi-file candidate input directories.
- `evaluate-skeleton`: blank manual ledger with source/reference/listening and timecoded
  six-scene observation fields, plus evaluator-only input media.
- Binary media stored as ordinary files; complete material manifest and component licenses.
- Chinese/English instructions and an offline bilingual scorecard for manual review.

There is no automatic video quality scorer and no claimed model performance. The
supplied reference is an editable author demonstration. Its technical QA cannot
replace model testing or manual observation of a candidate's actual output.

## Verification status / 验证状态

The sealed scoring-fix baseline completed 87 unit tests (83 passed; 4 skipped due to
missing optional Docker/Fortran/framework environments) and 90 controlled Python
reference/wrong-candidate checks over seeds 0, 17 and 2026. Those are evaluator tests,
not AI runs. The final V1.1 integration independently passed 104 unit tests (100 passed, four
explicit environment skips), 90 controlled Python checks, 19 scorecard logic checks
and two real CLI ledger round trips. Final-source wheel build/offline installation
and installed X04/X05 input generation also passed. See the
[machine-readable integration summary](../../validation/v1.1/integration-summary.json).
Actual-browser appearance, mobile and print behavior remain unverified; see the
[scorecard QA limitations](../../validation/v1.1/scorecard-qa.md).

Historical V1.0 eight-job CI applies to its historical commit only. No V1.1 CI pass is
claimed by this document until the exact newly published commit has been verified.
User-submitted models have not been run on the new X04/X05 tracks.

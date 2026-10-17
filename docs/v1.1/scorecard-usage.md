# Offline scorecard / 离线评分表

## 中文

下载并用现代桌面浏览器打开 [`scorecard.html`](scorecard.html)。单个文件自包含，不需要服务端、联网或 CDN。右上角可切换中文和 English。请勿将 GitHub 的源码预览当成可运行页面。

1. 先由评测器生成原始评阅包。科研题示例：

   ```sh
   nrb-v1 review-packet --task R03 --submission R03-submission.json --dest review-R03 --execution none
   ```

   编程题应在受支持的隔离评测环境用 `--execution docker` 获得实际自动结果；`none` 只生成未执行状态。视频题推荐：

   ```sh
   nrb-v1 evaluate-skeleton --task X04 --submission X04-submission.json --dest review-X04
   ```

2. 点击“导入评阅 / 自动报告”，选择同一个目录内的 `review.json` 和 `automatic.json`。可一次多选，也可分次导入。每份 JSON 限 5 MiB；此页不接收 `submission.json`、汇总报告或已合并评分报告。每题只编辑一个提交及种子；不同运行请分别打开页面。
3. 实际检查 `artifacts/` 中的文件。X04/X05 还要完整观看 `inputs/source.mp4`，X05 还要观看 `inputs/reference.mp4`，并实际观看和收听提交的 `artifacts/output.mp4`。保留视频评阅包内的 `inputs/`，最终 CLI 会重新核验输入媒体字节。
4. 填真实评阅者身份与类型。按原始 0/2/4 锚点选择整数 0–4，填写证据位置及科学理由。1、3 为中间等级；空白保持 `null`。核心责任独立记为 `pass`、`fail` 或 `unassessed`。LLM 评分须记录实际模型与提示词指纹，始终为暂评。
5. 视频题还须逐项记录来源/参考片观看、输出收听、配乐状态，以及六个固定区间内的观察时间点与发现。配乐缺失必须把 `audio` 核心责任记为 `fail`；缺模态不伪造观看或收听。
6. “导出草稿 JSON”保留未评字段。“检查并导出评阅”检查完整质量等级、证据、身份及所需观察，但不会认证成果质量或核验实际文件字节。下载名分别为 `review-R03-draft.json`、`review-R03.json` 等。请确认浏览器下载完成，再把文件保存回原评阅包目录；不要仅移动 JSON 而丢下 `automatic.json`、`artifacts/` 或视频题的 `inputs/`。
7. 使用下载文件的实际路径合并，例如：

   ```sh
   nrb-v1 grade --task R03 --submission review-R03/submission.json --review review-R03/review-R03.json --out R03-reviewed.json
   ```

   X04/X05 同理替换题号与目录。最终 CLI 才会验证评测器身份、内容指纹、输入及提交文件字节并计算权威结果。

编程题显示自动 70 与人工 30；科研、X01–X03、视频 A/B 均使用各题人工 100 量表。未知自动结果不转成零；任一未评质量维度使完整数值预览保持未知。核心失败不被高分抵消。五个轨道分别浏览，无跨轨道总分。标记不可比较的运行不展示排名总分。

页面不写入本地存储，也不上传文件。刷新/关闭会丢失未导出的修改。提供打印样式与“打印 / PDF”入口；本次环境未能完成真实浏览器视觉、手机布局或打印检查，详见 [QA 记录](../../validation/v1.1/scorecard-qa.md)。

## English

Download and open [`scorecard.html`](scorecard.html) in a modern desktop browser. It is one self-contained file with no server, network or CDN dependency. Use the upper-right switch for Chinese or English. GitHub’s source preview does not execute the page.

1. Generate an evaluator review packet first. For example:

   ```sh
   nrb-v1 review-packet --task R03 --submission R03-submission.json --dest review-R03 --execution none
   ```

   Coding tasks need `--execution docker` in the supported isolated evaluator for actual automatic results. `none` leaves execution unassessed. For video tasks:

   ```sh
   nrb-v1 evaluate-skeleton --task X04 --submission X04-submission.json --dest review-X04
   ```

2. Import `review.json` and `automatic.json` from the same packet, together or separately. Each JSON is limited to 5 MiB. Submission JSON, summary reports and merged reviewed reports are not supported inputs. The page holds one submission/seed per task; open separate pages for separate runs.
3. Inspect the real files in `artifacts/`. For X04/X05, also watch `inputs/source.mp4` in full; X05 additionally requires `inputs/reference.mp4`. Watch and listen to `artifacts/output.mp4`. Retain the video packet’s `inputs/`; the final CLI rechecks input media bytes.
4. Record the actual reviewer identity and type. Use integer levels 0–4 against the canonical 0/2/4 anchors, with specific evidence and rationale. Levels 1 and 3 are intermediate; blank remains `null`. Assess core requirements separately as `pass`, `fail` or `unassessed`. LLM review requires its actual model and prompt fingerprint and remains provisional.
5. Video reviews also record source/reference watching, output listening, soundtrack status, and concrete observations with timecodes inside each of the six fixed scene intervals. A missing soundtrack requires the `audio` core gate to fail. Do not fabricate observations when a modality is unavailable.
6. “Export draft JSON” retains incomplete fields. “Check and export review” validates ratings, evidence, identity and required observation records, but does not certify quality or verify actual media bytes. Download names include `review-R03-draft.json` or `review-R03.json`. Confirm the download completed, then save it beside the original `automatic.json`, `artifacts/` and video `inputs/` directory.
7. Merge with the actual exported filename, for example:

   ```sh
   nrb-v1 grade --task R03 --submission review-R03/submission.json --review review-R03/review-R03.json --out R03-reviewed.json
   ```

   Substitute the video task ID and directory for X04/X05. The CLI verifies evaluator identity, content fingerprints, input/submission bytes and the authoritative result.

Coding shows automatic 70 plus manual 30. Research, X01–X03 and the separate video A/B tasks use their own manual-100 rubrics. Unknown automatic results never become zero. Any unrated quality dimension keeps the complete numeric preview unknown. High scores do not override core failure. Five separate track views have no combined total. Explicitly comparison-ineligible runs have no ranking total.

The page uploads nothing and writes no local storage. Refreshing or closing loses unexported edits. Print styles and a “Print / PDF” action are included; actual-browser visual, mobile and print checks could not be completed in this environment. See the [QA record](../../validation/v1.1/scorecard-qa.md).

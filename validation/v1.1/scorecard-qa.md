# Scorecard QA / 评分表检查

Date: 2026-10-17. Scope: software behavior only. Synthetic test ratings and observations are not a model evaluation or genuine scientific/media assessment.

## Verified / 已验证

- JavaScript syntax parses with Node 24.19.0.
- 21 actual task definitions render through a minimal DOM stub in both languages; rubric data come from the repository registry.
- 19 JavaScript state/schema checks pass. Exact checks are in `scorecard-test-results.json`.
- An unchanged exported draft equals the imported evaluator `review.json`, including null scores and all immutable binding fields.
- Real Python `attach_review` accepts JS-exported R03 and X05 synthetic ledgers. Both deliberately remain `failed`, with `quality_qualified=false`; a numerical score never converts their known core failure to success.
- Tested: null score clearing; coding 70+30; manual-100 tracks; incomplete automatic coverage; comparison ineligibility; human/LLM distinction; rubric/anchor tampering; boolean and fractional scores; binding mismatches; escaped input; unsafe numbers and object keys; required actual observations; video A/B schemas; six-scene time ranges; missing soundtrack/fail branch.
- Static inspection finds no network or persistent-browser-storage calls. The page has a restrictive CSP including `connect-src 'none'`. This is not a penetration test.

## Not verified in an actual browser / 未完成真实浏览器检查

Visual appearance, real DOM interactions, keyboard/accessibility behavior, mobile layout, browser download behavior and print/PDF layout remain unverified. A print stylesheet and responsive rules exist, but this is not evidence that they render correctly.

Attempted local Chromium startup failed before opening the page: `socket() failed: Operation not permitted`. The supported escalation path then failed during environment setup with a read-only filesystem mount error. The supported cloud browser rejected the `file://` URL because only HTTP(S) navigation is allowed. No alternate route was used to bypass that policy denial.

The JavaScript tests use a minimal DOM stub, not Chromium, and do not establish actual-browser compatibility. The included Playwright test script is an uncompleted browser test plan, not a passed check.

## User-side smoke check / 用户侧快速检查

Open the downloaded HTML locally in a current browser; switch languages/tracks; import a generated packet; verify blank scores; export a draft and compare the JSON; inspect print preview before using PDF output. The final NRB CLI remains authoritative for file bytes, fingerprints, evaluator identity and scoring.

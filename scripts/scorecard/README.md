# Rebuild and test the scorecard

From the repository root:

```sh
python scripts/scorecard/build_scorecard.py
python scripts/scorecard/qa/run_logic_tests.py
```

The generator reads the actual NRB registry, canonical rubric hashes and video observation protocol. It embeds these plus human-written display translations into one dependency-free `docs/v1.1/scorecard.html`. The original rubric strings and weights remain authoritative in exported JSON.

Logic tests need Python and Node.js. They use a minimal DOM stub and explicitly synthetic fixtures, then feed exported ledgers into real `attach_review`. They are not browser or model tests. Results go to `validation/v1.1/scorecard-test-results.json`.

An optional actual-browser test plan is in `qa/browser_tests.py`. It additionally requires Playwright and Chromium (`/usr/bin/chromium` in the script). It could not run in the build environment. Do not report it as passed; see the QA limitations in `validation/v1.1/scorecard-qa.md`. The deployed HTML itself has no Python, Node, Playwright, network or server dependency.

# v0.2 validation evidence index

These are implementation, oracle and negative-control checks, not model capability scores.

- **Current fixed-commit CI:** [ci-current.json](ci-current.json), code commit `f125975aa914e4c9dcf9c06402c358bed21232e3`, evaluator digest `8dfb824a40469966a1fb8def3de39611608c28b2b8d84557210f40e44fb8d20b`. All four jobs passed in [run 39036404174](https://github.com/Mr-NuLl-01/NuLl-s_Research_Benchmark/actions/runs/39036404174).
- **Current local execution:** `unit-tests-current.*`, `selftest-current.json`, `native-smoke-current.json`, `exports-current.json`. The imported workspace had no Git HEAD. Its actual `evaluator_commit` stays null; source bytes have the current digest.
- **Current actual figure viewing:** [render-controls-cairo](render-controls-cairo/) contains CairoSVG 2.8.2 PNGs, original SVGs, receipts, hashes and a separate LLM provisional visual review. CI rendering alone does not populate that review.
- **Historical first-release local checks:** files without `-current` and [render-controls](render-controls/) retain their original evaluator identity and Inkscape evidence. They were not rerun or relabeled as current.
- **Local Docker availability:** [local-isolation.json](local-isolation.json) accurately remains unavailable. The actual successful Docker probe occurred later in CI; its distinct receipt is summarized in `ci-current.json`.

Do not merge these distinct evaluator identities into one model comparison. The full Chinese interpretation, test counts and limits are in [docs/validation.md](../../docs/validation.md).

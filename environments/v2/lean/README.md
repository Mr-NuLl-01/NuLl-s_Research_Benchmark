# L01 Lean audit sources

These readable sources mirror `PRELUDE` and `DRIVER` in `nrb_v2/lean.py`; the Python constants are the packaged runtime authority. Both copies are checked by the contract tests. They contain definitions, target propositions, syntax controls and kernel audit logic, but no candidate reference proof.

Pinned toolchain: `leanprover/lean4:v4.19.0`. Only bundled Lean/Std is used.

For a native audit of an already reviewed proof packet, in this directory:

```bash
lean -o NRBPrelude.olean NRBPrelude.lean
LEAN_PATH=. lean --run Verifier.lean /absolute/path/to/proofs.json
```

Use the Docker grader for arbitrary candidate submissions. This is a fixed-target, synchronous kernel and transitive axiom check in a restricted proof language. It is not the separate `comparator`/external-checker workflow and does not claim its stronger adversarial guarantees.

The public candidate packet contains the definitions and six target propositions. It never includes `REFERENCE_PROOFS` or negative controls. Proofs are evaluated independently: every obligation starts from the same trusted imported environment, preventing earlier candidate definitions from changing later goals.

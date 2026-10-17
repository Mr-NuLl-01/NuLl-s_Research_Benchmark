# v0.2 science task contracts

All examples and generated packets in these task families are original synthetic
teaching instances based on classical statistics, linear algebra and ordinary
measurement models. They contain no private research results. The changes here
preserve the ten task families and the existing 70 automatic points per task.

## Numerical display contract: NRB01–03

Candidate-facing prompts now recommend full floating-point precision and require
at least **nine significant digits** if numbers are shortened. Scientific notation
should be used for small nonzero quantities. This is an output contract, not a
claim that additional decimal places create experimental precision.

Existing field comparisons are retained:

| Task | Relative tolerance | Absolute tolerance | Scope |
|---|---:|---:|---|
| NRB01 | `2e-6` | `1e-9` | Reported paired descriptive statistics |
| NRB02 | `3e-6` | `1e-9` | Reported identifiable combinations, recovery and predictions |
| NRB03 | `3e-7` | `1e-10` | Displayed variances, worst objective and runner-up gap |

Integer fields, identities and classifications keep their separate exact checks.
The analytic example `tau=21/1.7=12.352941176470589` makes the old mismatch concrete:
`.6g` gives `12.3529`, which fails the NRB02 comparison; `.9g` gives
`12.3529412`, which passes. Tests round the complete numeric answer recursively
with `.9g` on seeds `0, 1, 17, 37, 101, 255, 2026`. They also exercise zero,
small signed values, order-of-magnitude boundaries and malformed numbers. No
blanket tolerance relaxation was introduced.

## NRB03: exact objective membership and displayed values

The finite decimal values appearing in `design.json` define the mathematical
input. `Fraction(str(value))` reconstructs those decimal values, avoiding the
unintended alternative interpretation of exact binary floating-point payloads.
For each scenario, rational information terms are scaled to a common integer
denominator before enumeration. This preserves exact arithmetic while keeping
the small finite search inexpensive.

The scorer separates three questions:

1. Does the chosen integer vector satisfy every design constraint and have an
   invertible intercept/slope information matrix?
2. Is its exact maximum scenario variance the exact finite-set minimum?
3. Are the submitted decimal numbers reasonable rounded displays of the values
   computed for that actual chosen vector?

The global minimizer set uses exact equality. The runner-up set is the smallest
exact objective **strictly greater than the exact minimum plus `1/10**12`**.
Objectives between the exact minimum and that threshold are neither global
minimizers nor eligible runner-ups. All vectors at either accepted exact level
are legal. Numeric display tolerance never broadens either vector set.

Regression controls include a four-allocation instance where a nonoptimal
objective is just `2e-13` above the minimum, and the first eligible runner-up is
`1e-9` above the minimum. They reject a near-optimal vector as a global optimum,
reject tied optima and below-threshold vectors as runner-ups, and reject a
nonminimum eligible runner-up even when its displayed value lies within the
numeric tolerance. An exact `1e-12` decimal boundary case is explicitly excluded
by the strict inequality. A separate tied instance accepts distinct exact global and
runner-up vectors.

### Mandatory executable reproduction contract

`solve.py` must expose this standard-library Python interface:

```python
def solve(problem: dict) -> dict:
    # problem is the JSON-decoded contents of design.json.
    # Return exactly the declared answer dictionary, without wrappers.
    ...
```

The returned dictionary has exactly the same fields and types as the submitted
`answer`. Importing the module must not run a CLI or open an input file. A guarded
`if __name__ == "__main__"` CLI is allowed. The reference CLI retains a historical
`feasible_count` output alias for existing local tools, but `solve(problem)`
returns only the declared answer fields.

Independent quality acceptance must **actually call** this entry point; presence
of a script or a prose claim of execution cannot establish reproduction. The
module helper is:

```python
from nrb.tasks.t03 import reproduce_solution
receipt = reproduce_solution(case, submission, execution="docker")
```

The helper uses the existing bounded `nrb.execution.run_python` backend, validates
the returned dictionary with all ordinary task checks, and verifies that its
chosen optimum and runner-up vectors agree with the submitted vectors and
reported values. A candidate may choose any exact tied optimum and reproduce that
choice; a different valid vector returned by unrelated code is not evidence that
the submitted choice was reproduced. Legitimate numeric rounding is accepted.

The receipt has `id=solve_reproduction`, `status=pass|fail|unassessed`, a tri-state
`passed` field, task/case/submission/source/input/result hashes, the backend,
execution outcome, detail and zero-weight verification records. It does not add
or redistribute automatic points. Missing or broken code is a failure;
unavailable execution is unassessed evidence. Review integration should require
this receipt for the `search_reproduced` essential responsibility. External
submissions require the isolated Docker/container backend. `trusted` is reserved
for repository-owned reference and deliberate mutation tests and is not an
isolation boundary.

The regression suite actually executes the reference entry point on seeds
`0,17,101`, a correct alternate tied solution, and deliberate invalid, unrelated,
malformed and broken implementations using the trusted repository-test backend.
These local tests do not claim Docker or another external harness was run.

## NRB08: Boolean schema without filled decisions

The three `claims` fields now show Boolean type descriptions rather than
`true,false,false` answer values. Candidates must submit actual JSON Booleans.
Copying the type strings earns no logical-claims credit. Mathematical proof,
numeric evaluation, and counterexample evidence remain separate responsibilities.

## NRB10: synchronized evidence states

The candidate prompt provides types and full enums, with no filled evidence or
handoff verdicts. Eight deterministic semantic variants update the packet logs,
manifest, active request and expected decisions together:

| Seed modulo 8 | Variant | Main current evidence | Integrity | Handoff |
|---:|---|---|---|---|
| 0 | Integrity conflict | Arithmetic pass, render/platform not run | One mismatch | `needs_integrity_repair` |
| 1 | Arithmetic failure | Arithmetic fail, render/platform pass | All match | `checks_pending` |
| 2 | Not run | All required checks not run | All match | `checks_pending` |
| 3 | Insufficient scope | Import smoke test does not cover required arithmetic | All match | `checks_pending` |
| 4 | Revision mismatch | Apparently successful records concern another revision | All match | `checks_pending` |
| 5 | Rendering failure | Arithmetic/platform pass, render fail | All match | `checks_pending` |
| 6 | Platform failure | Arithmetic/render pass, platform fail | All match | `checks_pending` |
| 7 | Ready | All required checks pass for active revision | All match | `ready_for_author_review` |

Legacy identity independently covers `same_revision`, `stale_revision`, and
`insufficient`. The public `validation_scope.md` defines every evidence label and
the exact required scope. `full_validation=true` requires all three payload
hashes to match and the current active-revision arithmetic, rendering and
cross-platform checks all to pass. This means that the supplied evidence covers
the stated packet checks; it does not establish independent execution or
real-world deployment validity. Matching legacy identity never substitutes for
a missing required current record.

The ready variant positively supports the claim that all stated checks are
complete. A copied old template that always reports `not_run`, stale history and
an incomplete handoff fails that variant. Failed or irrelevant logs do not become
successful evidence merely because hashes match. Reference prose and future
handoff actions are generated from the actual evidence state, including the case
where author review is the correct next action.

The no-new-simulations rule remains an explicit **fixed authorization protocol**:
audit calculations on supplied synthetic values are permitted; new simulations,
publication and overwriting the original bundle are not. Its Boolean is checked
as a protocol responsibility, and it is not presented as variation in research
judgment. SHA256 binds byte identity, not scientific correctness.

## Automatic critical check identifiers

These identifiers mark core automatic scientific/evidence responsibilities and
retain their existing point weights:

| Task | Critical check IDs |
|---|---|
| NRB01 | `current_source`, `independent_units` |
| NRB02 | `structural_rank`, `scale_symmetry`, `discriminating_intervention` |
| NRB03 | `all_design_constraints`, `global_optimality`, `strict_runner_up` |
| NRB08 | `weighted_induced_norm`, `residual_certificate`, `counterexample_validity` |
| NRB10 | `integrity_model.txt`, `integrity_plot.svg`, `integrity_values.csv`; `evidence_current_arithmetic`, `evidence_legacy_summary`, `evidence_rendering`, `evidence_cross_platform`, `evidence_full_validation`; `handoff_revision`, `handoff_status` |

Core completion additionally needs independent essential review: NRB01 evidence
scope; NRB02 arbitrary-input equivalence and intervention assumptions; NRB03
complete-domain optimality/code consistency and executed reproduction; NRB08
existence/uniqueness proof, general residual-bound proof and counterexample
explanation; NRB10 meaningful faithful English, no fabricated execution, and an
actionable continuation. The presence of prose artifacts alone does not satisfy
these responsibilities.

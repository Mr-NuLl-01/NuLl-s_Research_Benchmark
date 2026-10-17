# V1.0 C01–C05 implementation and scientific validation notes

All task inputs are original public synthetic examples. No private research data, unpublished study text, personal metadata, or model API calls are used. Each candidate receives a complete self-contained Chinese prompt and submits `solution.py`, `report.md`, and `tests.py`. Reference solution source uses only Python standard-library modules. Hidden expected values remain in host task modules and are not included in candidate prompts or reference solution source.

## Intended ladder and fixed scoring

These are intended design difficulties, not empirically measured model discrimination. Every task has A/basic 20, B/scientific 30, and C/stress 20 automated points, with 30 separate manual-review points managed by the V1 evaluator.

| Task | Intended difficulty | Main distinction | Cases | Candidate time budget |
|---|---:|---|---:|---:|
| C01 | 1/5 | Instrument CSV identities, temperature/uncertainty units, stable weighted mean | 10 | 900 s |
| C02 | 2/5 | Group versus technical repeats, equal-stratum target, deterministic cluster bootstrap | 7 | 900 s |
| C03 | 3/5 | Repair a multi-bug finite-volume backward-Euler heat solver | 7 | 900 s |
| C04 | 4/5 | Complex passive thin-film optics, s/p conventions, decay-only stable recursion | 9 | 1800 s |
| C05 | 5/5 | Prescribed adaptive stiff integration, rejected-step rollback, schedule changes, local clock | 9 | 1800 s |

The candidate budgets are authoring budgets. The evaluator should separately bound subprocess execution. Current cases execute in milliseconds; the algorithms have explicitly bounded task input sizes. The reference and negative controls are complete candidate artifacts, not selector flags interpreted by the evaluator.

## Independent evidence and scope

Scientific verification followed the `rk-certify` distinction between analytic derivations, numeric observations, and external sources. Passing the finite test set is not claimed to prove all continuous parameter domains, model validity, or benchmark discrimination.

| Claim | Evidence | Scope and limit |
|---|---|---|
| C01 known inverse-variance mean, standard error, and chi-squared | Direct analytic calculation for two unequal uncertainties plus executed candidate | Independent errors with supplied known standard uncertainties; no covariance or calibration-drift model |
| C02 specified bootstrap target and quantile | Independent seven-replicate LCG replay, analytic singleton distribution, row permutation | Conditional bootstrap of observed independent groups; no exact finite-sample coverage claim |
| C03 implicit finite-volume update and conservation | Independently derived two-cell eigenmode; executed energy account and maximum-envelope checks | Given spatial and temporal discretization; no continuous-PDE convergence theorem |
| C04 Fresnel normalization and multilayer complex amplitudes | Independent characteristic-matrix computation for s and p; analytic interface, lossless conservation, total-reflection and opaque-layer limits | Isotropic nonmagnetic passive coherent finite layers, lossless half spaces; exact critical singularity excluded |
| C05 adaptive state and timing | Independent exchange exponential, exact piecewise forcing, conservation/equilibrium, time-translation invariance | Prescribed first-order step-doubling algorithm; local tolerance is not a global-error certificate |

C04 primary theoretical source: Steven J. Byrnes, *Multilayer optical calculations*, arXiv:1603.02720, especially sections 3–5, https://arxiv.org/abs/1603.02720 and the author's code repository https://github.com/sbyrnes321/tmm . Retrieved 2026-10-17. The task uses tangential-electric-field amplitudes: its p reflection sign convention is explicitly defined, rather than silently adopting a different full-E convention. The reference implementation is independently written from the task definitions.

## Actual verification

Executed on Python 3.12.14:

```text
python -m py_compile nrb_v1/tasks/c01.py nrb_v1/tasks/c02.py nrb_v1/tasks/c03.py nrb_v1/tasks/c04.py nrb_v1/tasks/c05.py
python -m unittest tests_v1.test_c01_c05 -v
Ran 10 tests in 0.136s
OK
```

The ten unittest methods execute all references and errors over seeds 0, 17, and 2026, enforce strict JSON serialization, input immutability, tier weights, reference sample-test execution, executable mutant rejection, and the independent scientific checks above. Subtests cover substantially more than ten individual cases. Root evaluator integration and subprocess isolation are separate checks.

Every negative control is run as its actual candidate `solve` function. Observed failed cases at seed 17:

| Task | Wrong implementation | Observed failing cases |
|---|---|---|
| C01 | First duplicate wins | duplicates_missing |
| C01 | Equal rather than inverse-variance weights | parse_units, duplicates_missing, quoted_bom, scaled_variance |
| C02 | Technical pseudoreplication | one_group, unequal_technical_repeats |
| C02 | Pool all strata by group count | unequal_technical_repeats, stratum_target |
| C03 | Arithmetic rather than resistance-based interface | heterogeneous_conservative, source_fixed_mix |
| C03 | Lose left fixed boundary for one cell | one_cell_two_boundaries |
| C04 | Amplitude magnitude as power transmission | interface_power, quarterwave, oblique_absorbing_s, oblique_absorbing_p, evanescent_substrate |
| C04 | Ignore p polarization | oblique_absorbing_p, brewster_and_lossless, opaque_layer, long_bragg |
| C04 | Arbitrary thickness cutoff | quarterwave, oblique_absorbing_s, oblique_absorbing_p, opaque_layer, long_bragg |
| C05 | Commit rejected state | stiff_rollback, right_continuous_schedule, floating_endpoint |
| C05 | Use left-continuous source at change point | right_continuous_schedule |
| C05 | Discard small endpoint remainders | stiff_rollback, large_absolute_clock |

C05 reference trial counts at seed 17 include stiff_rollback 1167 accepted/7 rejected, right_continuous_schedule 1544/17, and floating_endpoint 6/1. These make rollback and controller tests substantive. The large-absolute-time test succeeds with 48 accepted steps and no rejection even though its initial step is below an absolute timestamp ULP; the local clock resolves those steps.

## Boundaries requiring empirical calibration

Task authoring budgets and difficulty labels are provisional. Negative controls demonstrate that named known mistakes are rejected; they do not measure the performance of real models. Running a model sample and inspecting failure distributions is required before reporting calibrated difficulty, coverage of model populations, or statistical separation. C05 step counts deliberately lock a specified controller algorithm and therefore should not be interpreted as a general comparison of stiff ODE solvers.

## Integration audit and difficulty revisions

C04's candidate prompt now supplies physical forward/backward fields, interface continuity, optical admittances, Fresnel interfaces and phase definitions, but does **not** give the stable multilayer-composition recurrence. The candidate must derive or select a stable composition and explain it. Its visible example is a real oblique absorbing three-layer scenario. C05's visible example includes both strong exchange stiffness and multiple source changes; its exact adaptive lifecycle remains prescribed because return values include step counts. C05 therefore measures algorithm implementation, rollback and scheduling rather than discovery of an integration method.

Scientific inputs now vary reproducibly with the public seed: C01 scientific temperatures and uncertainties; C02 bootstrap draws; C03 widths, conductivity, heat capacity, temperatures and source strengths; C04 absorbing-stack angle, thicknesses and complex index; C05 stiff rates and source strengths. Variations preserve the stated physical domains and known negative controls. Public seeds reduce simple fixture memorization; they are not secret and do not prevent training contamination of a public benchmark. C04/C05 visible examples use the same seed parameter generator as their scientific cases, with no hidden-case or reference evaluation needed to construct a candidate prompt.

`tests_v1/test_integration_coding.py` runs actual trusted subprocesses and synthetic review ledgers. Synthetic ledger entries test state transitions only and are not human/model assessments of quality. The audit found and root infrastructure repaired:

1. Noncanonical artifact path aliases and file/directory prefix collisions.
2. Input-object mutation after both successful and exception-raising calls.
3. Float replacements for exact integer output fields.
4. NaN/Infinity serialization errors previously miscredited as requested candidate ValueError exceptions.
5. Extremely large valid JSON integers previously overflowing host numeric comparison.
6. Malformed case-record frames previously reaching host grading without schema validation.

The integration suite checks worker payloads contain inputs only and materialized candidate files contain no expected answers; syntax errors, missing solve, NaN/Infinity and non-JSON returns; timeouts versus unavailable execution; full reference and mutant score gradients; manual pending/fail/complete gates; required-file failures despite high totals; report/ledger/artifact/submission tampering; and human versus provisional-LLM completion authority. Hash binding detects changed bytes in the supplied evidence workflow; it is not a cryptographic signature against an evaluator owner who deliberately rewrites reports and rehashes them.

Latest combined execution:

```text
python -m unittest tests_v1.test_c01_c05 tests_v1.test_integration_coding -q
Ran 23 tests in 5.745s
OK
```

All five reference submissions score 70 automatic points and remain pending independent quality review. Actual seeded-17 mutant automatic scores are C01: 55/18; C02: 45/40; C03: 40/60; C04: 25/39/29; C05: 33/55/48. This demonstrates retention of partial credit and concrete known-failure sensitivity, without measuring real-model discrimination. A high numeric total cannot override a failed critical case or absent required artifact.

A post-audit CLI run covered every coding task, not only C01–C05:

```text
python -m nrb_v1 selftest --tasks coding --seeds 17 --execution trusted --timeout 15 --include-mutants --out /tmp/nrb-v1-coding-selftest-post-schema.json
passed: true; 38 entries (10 references and 28 wrong controls); api_provider_calls: 0
```

This audit's execution evidence is trusted subprocess validation of repository references and controlled mutants. It does not certify the Docker network/filesystem boundary or arbitrary hostile native executables. C03's current stress case checks implicit stability on a small mesh; asymptotic complexity also requires engineering review rather than being inferred from one runtime.

The final integration test also exercises modality observation gates for R01 visual viewing, X01 actual-interaction records, X02 video watching and X03 audio listening. It rejects absent performance, missing observation entries, wrong artifact hash, wrong action, empty findings and nonboolean assertions. Unassessed/all-failed core reviews can remain unfinished without pretending observation occurred. These are explicitly synthetic ledger/byte fixtures for gate mechanics, not valid research/media submissions or actual human judgments. The schema binds an observation assertion to exact submitted bytes; it cannot establish that a person truly saw or heard them. Actual reviewers remain responsible for honest inspection.

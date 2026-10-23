# V2 Docker CI evidence — 39970163399

The actual Docker job passed for implementation commit
`735174612fe0fb298a83c872a0350f6eabf2d0a5`.
The downloaded artifact was checked against GitHub's SHA-256 and its contents
were independently audited on 2026-10-23. All records use evaluator fingerprint
`7f2487673f1a214d60311193a369d48ab9215f9d7006554bf5c823e6ce5c7aa3`
and report `source_dirty=false`.

- [Workflow run](https://github.com/Mr-NuLl-01/NuLl-s_Research_Benchmark/actions/runs/39970163399)
- [Docker job](https://github.com/Mr-NuLl-01/NuLl-s_Research_Benchmark/actions/runs/39970163399/job/120470415803)
- [Implementation commit](https://github.com/Mr-NuLl-01/NuLl-s_Research_Benchmark/commit/735174612fe0fb298a83c872a0350f6eabf2d0a5)
- [Machine-readable audit](summary.json), [audit program](audit.py),
  [run](run.json), [job](job.json), [artifact metadata](artifact.json),
  [extracted-file hashes](extracted-files.json).

## Actual results

The control artifact contains **70 scoring records**: all **13 references scored
100**, and all **57 reviewed wrong controls scored below 100**. All 70 report
`execution.status=executed`; none is unavailable or unscored. The release gate
contains 72 successful checks: image inspection, the 70 controls, and coverage.

| Task | Reference score | Wrong controls detected | Execution |
| --- | ---: | ---: | --- |
| P01 | 100 | 2 | Docker |
| P02 | 100 | 2 | Docker |
| P03 | 100 | 2 | Docker |
| P04 | 100 | 3 | Docker |
| P05 | 100 | 3 | Docker |
| P06 | 100 | 4 | Docker |
| P07 | 100 | 3 | Docker |
| P08 | 100 | 4 | Docker |
| F01 | 100 | 4 | Docker |
| F02 | 100 | 5 | Docker |
| F03 | 100 | 4 | Docker |
| L01 | 100 | 14 | Docker; Lean kernel |
| H02 | 100 | 7 | Numeric answer verification |

Twelve code tasks account for **62 Docker control records** (12 references and
50 wrong controls). H02 accounts for **8 answer-verification records** (one
reference and seven wrong answers), with no container image claim.

The complete controls took **94.330 seconds**. The separate production-executor
isolation probe and its P01 reference/wrong-output controls took **1.104 seconds**.
These are authored validation controls, not measured model performance; no
model-provider API was called.

See [raw controls](v2-docker-controls.json) and [control log](v2-docker-controls.log).

## Actual runtime identities

Every code report's `image_id` matches the immutable image inspected in this job.
Both images report Linux/amd64.

| Runtime | Actual image ID |
| --- | --- |
| Python / Fortran | `sha256:09c1891d626e895e5ef1a9caea6cced3c69c35d3017d5e2a478910206742a7c3` |
| Lean | `sha256:d08cdfcaef18afdcfc2cdd5470fc899718843a377213d80a396f7e487cda523c` |

Observed Docker server: 28.0.4. The candidate Python probe observed
Python 3.12.15, GCC 14.2.0. Every Fortran control reports
`GNU Fortran (Debian 14.2.0-19) 14.2.0`.
Every Lean control reports
`Lean (version 4.19.0, x86_64-unknown-linux-gnu, commit 6caaee842e94, Release)`.

See [full image inspection](v2-images.json), [Docker version](v2-docker-version.txt),
[Python/Fortran build](v2-runtime-build.log), and [Lean build](v2-lean-build.log).
The [Python package inventory](v2-python-packages.txt) describes the host evaluator
environment recorded by the workflow.

## Lean proof audit

All six fixed obligations were kernel-checked against their exact target:
`step_balance`, `zero_input_active`, `trace_balance`, `restart`,
`prefix_admissible`, and `collected_bound`.
The recorded transitive dependencies contain only the allowed standard axioms;
the actual reference uses `propext` and `Quot.sound` where needed.

The direct and indirect `sorry` controls were rejected through the recorded
`sorryAx` dependency. Command injection, weakening, native evaluation,
metaprogramming, custom tactic options, unsafe terms, external input through
`include_str`, and kernel-skipping controls were detected. The intentionally
wrong trace induction received 78.571429; the missing final obligation received
85.714286. Each loses exactly its own obligation, demonstrating partial scoring.
Empty proofs received zero.

## Isolation observations

All **13 observations** in the actual Python/Fortran production executor passed:

1. UID/GID were 65534.
2. Evaluator packages were not importable.
3. The known evaluator, repository, and Docker socket paths were absent.
4. The candidate mount contained only `solution.py` and its execution driver.
5. The root mount was read-only.
6. The candidate mount was read-only.
7. Root writes were blocked.
8. Candidate-mount writes were blocked.
9. Temporary writes succeeded.
10. `NoNewPrivs` was enabled.
11. Effective capabilities were empty.
12. Only the loopback network interface was present.
13. An external connection attempt failed with no network route.

The probe also preserved its generated nonce and used the inspected runtime
image. Its P01 reference and deliberately empty output were independently
validated. See [raw isolation evidence](v2-isolation.json).
These observations describe this executor, image, and host; they do not establish
general resistance to host or kernel exploits. Lean used its separately recorded
pinned image; the Python isolation probe is not described as a separate Lean probe.

## Artifact integrity and independent audit

Artifact ID: `12508199381`; name: `v2-docker-evidence`; archive size: **48,542 bytes**.

GitHub and the local ZIP both report:

```text
77b68639e6e3c23a0583c85bb1d1b00f663047494dc736ab068c06af436e52d6
```

The original [ZIP](v2-docker-evidence.zip) contains nine files. Extraction checked
the exact member allowlist, duplicate/path/symlink constraints, size limits, ZIP
integrity, and per-file hashes before auditing the reports. Temporary signed
download URLs and tokens are not stored here.

The independent audit checked the exact run/commit, artifact digest, clean
evaluator identity, all expected reference/mutant labels, all source and
submission hashes, each report's schema/content hash/derived score, full test
coverage, immutable image binding, Lean compiler/goal/axiom records, and the
isolation observations. It did not rerun candidates locally or count a job's
success flag as a substitute for the underlying records.

To repeat that read-only audit against these files, choose a new output path:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 validation/v2.0/ci/39970163399/docker/audit.py --out /tmp/nrb-docker-audit-39970163399.json
```

The audit refuses to overwrite an existing output file. Initial in-progress API
snapshots remain in `run-initial.json` and `job-initial.json`; the completed
metadata is in `run.json` and `job.json`.

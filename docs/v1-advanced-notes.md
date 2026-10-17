# V1 advanced coding families C06–C10

These five families use public, classical equations and generated synthetic
inputs. They do not read private research, laboratory records, device designs,
current projects, or external services. Candidate solutions are single files:
`main.f90` for C06/C09 and `solution.py` for C07/C08/C10, plus a scientific report
and executable independent tests. Python references use only the standard
library. The Fortran references are compiled and executed, not inspected as
text and assumed correct.

| Family | Difficulty | Scientific responsibility |
| --- | --- | --- |
| C06 | 3/5 | Conservative SG flux on a nonuniform grid; drift sign, reaction/source balance, positive density, small/large Peclet limits |
| C07 | 4/5 | Shared diffusion identification with independently eliminated experiment amplitudes/baselines; heteroscedastic absolute errors; profile interval and information after nuisance projection |
| C08 | 4/5 | Heterogeneous diagonal-anisotropic 2-D elliptic solve; harmonic face coefficients; nonuniform volumes; consistent outward discrete boundary flux |
| C09 | 5/5 | Simultaneous finite nonlinear one-carrier SG/Poisson BVP; positive density, nonlinear globalization, equilibrium/current/gauge checks |
| C10 | 5/5 | Repair a coupled implicit reaction–diffusion, discrete tangent, weighted inverse, checkpoint and deterministic parametric-bootstrap pipeline |

Each task uses basic/scientific/stress tiers with maxima 20/30/20, totaling 70
automatic points. Scientific explanation, independent evidence, and handoff
remain 30 manual points. Passing a reference execution does not supply those
manual ratings or qualify an external model.

## Scientific definitions that prevent ambiguous grading

C06 prescribes the SG formula with the flux orientation explicitly stated. Its
source is a density per time, so it must be multiplied by the nonuniform volume
width in the tridiagonal integrated equation. The high-Peclet test is finite
and physically interpretable; it is not an arbitrary floating-point torture
case. The supported edge Peclet magnitude is at most 2500.

C07 defines absolute chi-square from supplied instrument standard deviations.
The amplitudes and baselines are nuisance parameters; information conditional
on fixed nuisance values is not the required Schur-complement information.
The test family has a single non-flat profile minimum, while an exact constant
signal exercises structural loss of diffusion identifiability. A full profile
interval and a nonzero local information measure are deliberately distinct
outcomes. No finite-sample coverage theorem is claimed for the specified
likelihood-ratio threshold.

C08 defines the face average and the control-volume boundary explicitly. The
reported flux surrounds the union of interior node volumes, not an unstated
continuous-surface reconstruction. Discrete manufactured truth is kept only
in the host. Candidate `boundary` interior entries are zero placeholders,
and an independent test changes them to a large arbitrary value to verify
that they are ignored. Continuous sinusoidal manufactured forcing separately
checks approximately second-order refinement; a discrete manufactured test
alone cannot establish that continuum rate.

C09 does not claim global uniqueness of general nonlinear DD–Poisson systems.
The bounded test family is generated with known positive solutions. The
grader independently recomputes both original residual equations, the SG
constitutive law, boundary contacts, and density positivity, accepting any
valid positive solution. A candidate cannot earn points merely by reporting
a small residual. Independent analytic/Boltzmann manufactured tests additionally
check recovery of prescribed roots and potential gauge shifts. This is a
finite one-carrier steady BVP, not a general semiconductor simulator and not
a theorem about existence or convergence on arbitrary sources.

C10 differentiates the specified backward-Euler update rather than substituting
continuous-time sensitivities. The current-time reaction transfer is required
for mass conservation. Its checkpoint contains both physical and tangent
states. The RNG definition consumes two uint32 updates for every normal and
continues across bootstrap replicates; each replicate is refitted. Known
absolute standard deviations imply `(J.T J)^-1`, without residual-variance
rescaling. Uniform initial data provide a concrete rank-deficient inverse
problem in which an optimizer result alone is insufficient.

## Executed verification

The focused suite can be rerun with:

```sh
python -m unittest tests_v1.test_c06_c10 -v
```

It compiles C06/C09 with `gfortran -std=f2008 -O2 -fcheck=all
-ffree-line-length-none`, executes reference submissions through the actual
candidate subprocess grader at seeds 0, 17, and 2026, and executes every
negative control. When the compiler is unavailable, compiled checks are
explicitly skipped rather than counted as passed.

Independent checks include a nonuniform exponential exact transport solution;
integrated source/loss balance; Boltzmann zero flux and gauge invariance;
original nonlinear residual recomputation; profile curvature versus projected
information; absolute-sigma scaling; 2-D continuum mesh refinement; periodic
Fourier amplification factors and analytic discrete tangents; central-difference
derivative checks; inverse recovery from independent modal formulas; and
JSON restart identity. The reference artifacts' own `tests.py` files are also
written to temporary directories and run as actual files.

At seed 17, actual automatic scores for executable controls were:

| Family | Reference | Deliberately wrong candidate | Automatic score /70 |
| --- | ---: | --- | ---: |
| C06 | 70 | centered drift; uniform control-volume width; incorrect right boundary coefficient | 32; 60; 32 |
| C07 | 70 | discarded baseline; ignored heteroscedastic weights; conditional information | 6; 13; 13 |
| C08 | 70 | arithmetic interface; swapped tensor directions; reversed west flux | 46; 26; 6 |
| C09 | 70 | incorrect Poisson mesh scale; reset potential gauge; reversed drift sign | 32; 32; 22 |
| C10 | 70 | lagged reaction transfer; reset checkpoint tangents; residual-scaled covariance; reused bootstrap noise | 14; 39; 50; 60 |

These scores describe regression controls, not model performance. They show
that scientific and uncertainty errors lose points even when simple cases
still work. This suite does not prove the absence of all numerical defects,
global inverse uniqueness outside the stated families, or scientific validity
of an unrelated real experiment.

## Primary method sources

- Scharfetter, D. L. and Gummel, H. K. (1969), “Large-signal analysis of a
  silicon Read diode oscillator,” *IEEE Transactions on Electron Devices* 16,
  64–77. DOI: <https://doi.org/10.1109/T-ED.1969.16566>.
- NIST Sesame project, “Numerical treatment of the drift diffusion Poisson
  equations,” primary implementation documentation:
  <https://github.com/usnistgov/sesame/blob/master/doc/physics/discretization.rst>.
- Golub, G. H. and Pereyra, V. (1973), “The Differentiation of Pseudo-Inverses
  and Nonlinear Least Squares Problems Whose Variables Separate,” *SIAM
  Journal on Numerical Analysis* 10, 413–432.
  <https://doi.org/10.1137/0710036>.
- NIST FiPy, finite-volume theoretical and numerical background:
  <https://pages.nist.gov/fipy/en/stable/numerical/index.html>.

Sources establish the method provenance. The task's explicit equations,
signs, units, matrix shapes, and uncertainty definitions remain the grading
contract; formulas using a different carrier/current convention are not
interchangeable without derivation.

## Actual Docker CI gates

After building `environments/v1/Dockerfile` as `nrb-v1:local`, CI runs:

```sh
python scripts/v1/check_docker.py --image nrb-v1:local --out docker-v1.json
python scripts/v1/check_isolation.py --image nrb-v1:local --out isolation-v1.json
```

The first gate executes all ten references and selected scientific wrong
candidates through the Docker backend, including compiled Fortran controls.
It records the inspected image ID, engine/runtime/compiler versions, evaluator
identity, real grading reports, and automatic-only expected outcomes. Grading
uses the inspected image ID rather than a mutable tag. The second gate builds
the actual Harbor C01 candidate image from the exported packet, checks the
build context, and probes the real filesystem and disconnected network under
an inspected unprivileged container boundary. It records image IDs, material
hashes, runtime checks, and build/probe logs. Separate-verifier grading and
permissions are covered by `adapters/v1/harbor_smoke.py`.

Both commands require new output paths and return nonzero for missing Docker,
missing images, runtime failures, or unexpected scientific/isolation outcomes.
Neither substitutes a mocked result or a trusted host execution for Docker.
They make zero provider calls and their reports are not model performance.
Local development without Docker verifies the static rejection checks and
the explicit unavailable/nonzero path only; actual Docker success must come
from the CI invocation and its recorded evidence.

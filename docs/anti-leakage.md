# Candidate isolation and evaluator separation

NRB-10 uses public classical, synthetic task material. The closed-input track
measures work from the supplied packet and general knowledge. A candidate must
not receive this repository, reference answers, graders, review findings,
previous model submissions, or oracle solutions. The public rubric and core
completion conditions are part of the packet; grader implementation and hidden
behavior cases are not. See the actual packet builder in `nrb/core.py` and the
separate export paths in `nrb/adapters.py`.

## Three different boundaries

| Mode | Candidate input | Actual boundary | What the record must establish |
|---|---|---|---|
| Response-only API | The generated packet in a fresh model context | No local shell or repository is exposed by the NRB Inspect solver. Provider-side tools remain a separate configuration responsibility. | Exact model version, generation settings, no browsing/search/retrieval or persistent memory, complete request/tool policy. |
| Harbor agent | Packet under `/app`; task instruction; installed agent runtime | A candidate image separate from the root-owned, network-disabled verifier. Candidate run is offline by default; explicit model API hosts may be allowlisted. | Image digest, task configuration, mounts, actual supported network enforcement, fresh per-task state, and provider-side tools disabled. |
| Raw local CLI diagnostic | A fresh packet directory and stdin prompt | `nrb.harness.run_command` is a host subprocess, not a security sandbox. A fresh directory does not prevent reading its parent, global files, credentials, skills, or the network. | An external isolation wrapper is needed before calling it controlled. An unwrapped run remains diagnostic. |

The evaluator identity is recorded on the evaluator side in exports, framework
sample metadata and canonical reports. It is not appended to candidate prompt
text. A changed grader with an unchanged prompt is still a different evaluator.
The adapters reject source-identity drift before new scoring. Historical
canonical reports retain their recorded identity; missing identities remain
legacy/unverified. Conversion does not restamp them with the current evaluator.

## Harbor export policy

The default export contains **no `solution/`** and permits **no agent network**:

```bash
python -m nrb export --format harbor --tasks all --seed 0 \
  --python-image python:3.12-slim --dest /tmp/nrb-harbor-offline
```

An actual model agent may need an explicitly configured provider hostname:

```bash
python -m nrb export --format harbor --tasks all --seed 0 \
  --python-image python:3.12-slim --agent-hosts api.openai.com \
  --dest /tmp/nrb-harbor-model
```

Use only the exact hostnames needed by the selected provider and authentication
flow. The exporter rejects wildcards, URLs and paths. Do not automatically
allow all providers. Resolve and record the Python image digest for a controlled
comparison; the moving tag above is a convenient setup example.

Agent setup may use the network to provision its runtime. Candidate execution
is separately offline or allowlisted. The verifier remains a separate,
network-disabled container and runs submitted Python under an unprivileged UID.
Never mount the evaluator checkout, full export directory, `tests/`, `solution/`,
Docker socket, host home, model transcript archive or review evidence into the
candidate. A Docker build context of `environment/` contains only its Dockerfile,
restricted `.dockerignore`, and packet. The Dockerfile copies only `packet/`.

Oracle solutions require the explicit **evaluator-only** option:

```bash
python -m nrb export --format harbor --tasks all --seed 0 --include-oracle \
  --dest /tmp/nrb-harbor-oracle-validation
python adapters/harbor/smoke.py --dest /tmp/nrb-harbor-runtime-check --tasks all
```

The smoke script opts in to the oracle deliberately and is never model
performance. Its solution is supplied by Harbor's oracle workflow; it is excluded
from the agent Docker build context. An oracle export must not be reused as an
ordinary model candidate environment.

The evaluator copied into the verifier includes `evaluation_policy.json` and an
origin record. The verifier checks actual scoring-source/policy bytes against
the exported evaluator digest and retains the exporter commit identity even when
there is no `.git` inside the image. The case identity and scored report carry
the same evaluator identity. A stale or modified verifier is an infrastructure
or provenance failure, not a model answer failure.

## Reproducible offline image probe

```bash
python scripts/check_candidate_isolation.py \
  --python-image python:3.12-slim --out /tmp/nrb-candidate-isolation.json
```

The script exports one synthetic packet without an oracle, rejects extra build
context files/COPY instructions, and builds the actual candidate image. It then
creates a separate read-only Docker container with `--network none`, no host
bind mounts, dropped capabilities and no new privileges. Before execution it
inspects those settings. Inside the actual image it checks the packet hashes,
blank submission sentinel, absence of `/grader`, `/solution`, `/tests`, candidate
repository directories and host sockets, inability to import `nrb`, loopback-only
interfaces, and failure of an outbound socket connection. The generated report
records actual image identity, checks, logs and material hashes.

This is an **offline candidate-image isolation test**. It makes no live provider
API calls and does not establish that a Harbor backend correctly enforces its
live API allowlist. Missing Docker/daemon is `runtime_status=unavailable` with
`passed=false` and a nonzero exit status. The implementation environment used
for this change had no Docker executable; its static screen ran, while the
container probe remained unavailable. Real Docker checks belong in the Docker
CI job or an equivalently configured local installation.

## Remaining provider and state responsibilities

A hostname allowlist controls destinations, not the complete behavior of a
provider API. The provider may expose browsing, remote execution, retrieval,
connector access or other tools behind an allowed hostname. Disable these
server-side tools for the closed-input track and preserve the actual request
configuration and tool events. An outbound proxy, relay or shared authentication
host may also broaden access beyond the nominal hostname; inspect the actual
backend rather than assuming that a list of DNS names closes every route.

Start each task with fresh conversation, working files and agent state. Do not
carry earlier benchmark responses, source excerpts, review corrections, global
agent memories or shared caches into later tasks. Record any mandatory skills or
agent instructions as harness configuration. A fresh task directory alone does
not enforce these conditions for host CLI agents. Inability to verify a boundary
must remain an explicit limitation or infrastructure result, with no silent
fallback to unrestricted networking and no promotion to a controlled comparison.

The pinned Harbor interface is task schema 1.4 in release 0.24.0, checked by the
optional runtime schema test. Its primary configuration source is
[Harbor v0.24.0 task config](https://github.com/harbor-framework/harbor/blob/v0.24.0/src/harbor/models/task/config.py).
Live backend networking must be validated separately using that release's
implementation and the actual deployment environment.

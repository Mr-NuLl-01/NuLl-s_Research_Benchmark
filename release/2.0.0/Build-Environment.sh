#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
if command -v python3 >/dev/null 2>&1; then
  NRB_PYTHON=python3
else
  NRB_PYTHON=python
fi
"$NRB_PYTHON" -m venv .nrb-env
.nrb-env/bin/python -m pip install -r requirements-evaluator.txt
docker build --platform=linux/amd64 -t nrb-v2:local -f environments/v2/Dockerfile .
docker build --platform=linux/amd64 -t nrb-v2-lean:local -f environments/v2/LeanDockerfile .
printf '\nEnvironment ready. Place each task file in its submissions directory, then run Grade-Results.\n'

#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
if [ -x .nrb-env/bin/python ]; then
  exec .nrb-env/bin/python run-grader.py "$@"
fi
exec python3 run-grader.py "$@"

#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
docker build -t nrb-v2-python:local -f environments/v2/Dockerfile .
printf '\nEnvironment ready. Place solution.py in submissions/P01 ... P08, then run Grade-Results.\n'

#!/bin/sh
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)" || exit 1
python3 run-grader.py "$@"
result=$?
printf '\nPress Enter to close.\n'
read -r answer
exit "$result"

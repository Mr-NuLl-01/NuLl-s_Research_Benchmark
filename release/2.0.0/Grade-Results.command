#!/bin/sh
set -u
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
sh Grade-Results.sh "$@"
NRB_RESULT=$?
printf '\nPress Enter to close. '
read -r NRB_CLOSE || :
exit "$NRB_RESULT"

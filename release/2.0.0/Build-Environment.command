#!/bin/sh
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)" || exit 1
sh Build-Environment.sh
NRB_RESULT=$?
printf '\nPress Enter to close.\n'
read -r NRB_CLOSE || :
exit "$NRB_RESULT"

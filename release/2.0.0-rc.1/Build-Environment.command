#!/bin/sh
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)" || exit 1
sh Build-Environment.sh
result=$?
printf '\nPress Enter to close.\n'
read -r answer
exit "$result"

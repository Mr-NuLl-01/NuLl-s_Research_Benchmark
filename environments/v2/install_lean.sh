#!/bin/sh
# CI/native reference validation only. Arbitrary candidates use LeanDockerfile.
# Usage: sh environments/v2/install_lean.sh /absolute/new/destination
set -eu
if [ "$#" -ne 1 ]; then
  echo 'usage: install_lean.sh /absolute/new/destination' >&2
  exit 2
fi
case "$1" in /*) ;; *) echo 'destination must be absolute' >&2; exit 2 ;; esac
if [ "$(uname -s)" != Linux ] || [ "$(uname -m)" != x86_64 ]; then
  echo 'This fixed helper installs Linux amd64 only. Use the Docker image on other hosts.' >&2
  exit 2
fi
nrb_destination=$1
if [ -e "$nrb_destination" ]; then
  echo 'destination already exists; choose a new directory' >&2
  exit 2
fi
nrb_download_dir=$(mktemp -d)
trap 'rm -rf "$nrb_download_dir"' EXIT HUP INT TERM
curl --fail --location --retry 3 \
  https://github.com/leanprover/lean4/releases/download/v4.19.0/lean-4.19.0-linux.tar.zst \
  --output "$nrb_download_dir/lean.tar.zst"
printf '%s  %s\n' 6fe3ce97a58f44e2b3567d455b994eacec5bfe9ae7774f2a573444480ba813fe "$nrb_download_dir/lean.tar.zst" | sha256sum --check -
mkdir -p "$nrb_destination"
tar --no-same-owner --use-compress-program=unzstd --strip-components=1 -xf "$nrb_download_dir/lean.tar.zst" -C "$nrb_destination"
"$nrb_destination/bin/lean" --version
printf 'NRB_LEAN=%s/bin/lean\n' "$nrb_destination"

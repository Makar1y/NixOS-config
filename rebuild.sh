#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

./noc-save.sh

sudo nixos-rebuild switch --flake .#main

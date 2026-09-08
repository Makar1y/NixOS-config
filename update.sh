#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

./noc-save.sh

nix flake update

sudo nixos-rebuild switch --flake .#main
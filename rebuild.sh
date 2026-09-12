#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

sudo nixos-rebuild switch --flake .#main

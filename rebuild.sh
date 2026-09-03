#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

nix run nixpkgs#noctalia-shell -- ipc call state all > ./modules/features/noctalia.json

sudo nixos-rebuild switch --flake .#main

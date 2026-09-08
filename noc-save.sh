#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

tmp="$(mktemp)"

if nix run nixpkgs#noctalia-shell -- ipc call state all > "$tmp" 2>/dev/null; then
	mv "$tmp" ./modules/features/noctalia.json
else
	echo "noctalia-shell not running; keeping existing noctalia.json" >&2
	rm -f "$tmp"
fi
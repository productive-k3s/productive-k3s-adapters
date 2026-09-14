#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
THEME="$ROOT/.shared/productive-k3s-docs-theme"
if [[ ! -d "$THEME" || -z "$(ls -A "$THEME" 2>/dev/null)" ]]; then
  echo "Shared docs theme submodule is not initialized." >&2
  echo "Run: git submodule update --init --recursive" >&2
  exit 1
fi
rm -rf "$HERE/src/overrides"
mkdir -p "$HERE/src/overrides" "$HERE/src/assets/stylesheets"
if [[ -d "$THEME/overrides" ]]; then cp -R "$THEME/overrides/." "$HERE/src/overrides/"; fi
if [[ -f "$THEME/assets/stylesheets/extra.css" ]]; then cp "$THEME/assets/stylesheets/extra.css" "$HERE/src/assets/stylesheets/extra.css"; fi

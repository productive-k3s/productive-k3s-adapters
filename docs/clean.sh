#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
rm -rf "$HERE/site" "$HERE/src/overrides"
rm -f "$HERE/src/assets/stylesheets/extra.css"

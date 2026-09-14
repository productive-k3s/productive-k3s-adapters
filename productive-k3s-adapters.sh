#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}" exec python -m productive_k3s_adapters.cli "$@"

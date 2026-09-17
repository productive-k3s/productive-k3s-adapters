#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
rm -rf "${ROOT_DIR}/site" "${ROOT_DIR}/src/overrides"
rm -f "${ROOT_DIR}/src/assets/stylesheets/extra.css"
rm -f "${ROOT_DIR}/src/assets/images/argentina.png"
rm -f "${ROOT_DIR}/src/assets/images/productive-k3s-icon-square-0.3x.png"
rm -f "${ROOT_DIR}/src/assets/images/favicon.ico"

#!/usr/bin/env bash
set -euo pipefail
VERSION="${1:-}"
if [[ -z "$VERSION" ]]; then
  echo "usage: $0 <version>" >&2
  exit 2
fi
TAG="v${VERSION#v}"
git diff --quiet && git diff --cached --quiet || { echo "working tree must be clean" >&2; exit 1; }
git tag -a "$TAG" -m "Productive K3s Adapters $TAG"
echo "Created $TAG. Push with: git push origin $TAG"

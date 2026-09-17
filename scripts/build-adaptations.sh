#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON:-python3}"
OUTPUT_DIR="${OUTPUT_DIR:-${REPO_DIR}/.generated/adaptations}"
case "${OUTPUT_DIR}" in
  /*) ;;
  *) OUTPUT_DIR="${REPO_DIR}/${OUTPUT_DIR}" ;;
esac

usage() {
  cat >&2 <<'EOF'
Usage: scripts/build-adaptations.sh [adaptation-path ...]

Build Productive K3S adaptation candidates from adaptations/<producer>/<name>.

Outputs:
  .generated/adaptations/<producer>/<name>/source/
  .generated/adaptations/<producer>/<name>/<stack-name>-<version>.tgz
EOF
}

yaml_metadata_value() {
  local file="$1"
  local key="$2"
  awk -v key="${key}" '
    /^metadata:/ { section="metadata"; next }
    /^spec:/ { section="spec"; next }
    section == "metadata" && key == "metadata.name" && /^  name:/ { sub(/^  name:[[:space:]]*/, "", $0); print; exit }
    section == "spec" && key == "spec.stackName" && /^  stackName:/ { sub(/^  stackName:[[:space:]]*/, "", $0); print; exit }
    section == "spec" && key == "spec.input" && /^  input:/ { sub(/^  input:[[:space:]]*/, "", $0); print; exit }
  ' "${file}"
}

yaml_stack_version() {
  local file="$1"
  awk '
    /^metadata:/ { section="metadata"; next }
    section == "metadata" && /^  version:/ { sub(/^  version:[[:space:]]*/, "", $0); print; exit }
  ' "${file}"
}

yaml_metadata_field() {
  local file="$1"
  local field="$2"
  awk -v field="${field}" '
    /^metadata:/ { section="metadata"; next }
    section == "metadata" && field == "name" && /^  name:/ { sub(/^  name:[[:space:]]*/, "", $0); print; exit }
    section == "metadata" && field == "version" && /^  version:/ { sub(/^  version:[[:space:]]*/, "", $0); print; exit }
  ' "${file}"
}

stack_addon_paths() {
  local file="$1"
  awk '
    /^  addons:/ { in_addons=1; next }
    in_addons && /^  [a-zA-Z0-9_-]+:/ { in_addons=0 }
    in_addons && /^    path:/ { sub(/^    path:[[:space:]]*/, "", $0); print }
  ' "${file}"
}

adaptation_dirs() {
  if (($# > 0)); then
    for path in "$@"; do
      printf '%s\n' "${path}"
    done
    return
  fi

  find "${REPO_DIR}/adaptations" -mindepth 2 -maxdepth 2 -type d | sort
}

build_one() {
  local adaptation_dir="$1"
  local metadata compose_input compose_source name stack_name version rel producer output_root source_dir package_dir artifact

  adaptation_dir="$(cd "${adaptation_dir}" && pwd)"
  metadata="${adaptation_dir}/adaptation.yaml"
  [[ -f "${metadata}" ]] || {
    echo "Missing adaptation metadata: ${metadata}" >&2
    exit 1
  }

  rel="${adaptation_dir#${REPO_DIR}/adaptations/}"
  producer="${rel%%/*}"
  name="$(yaml_metadata_value "${metadata}" "metadata.name")"
  compose_input="$(yaml_metadata_value "${metadata}" "spec.input")"
  stack_name="$(yaml_metadata_value "${metadata}" "spec.stackName")"
  [[ -n "${name}" ]] || name="${rel#*/}"
  [[ -n "${compose_input}" ]] || compose_input="compose.yaml"
  [[ -n "${stack_name}" ]] || stack_name="${producer}-${name}"
  [[ -f "${adaptation_dir}/${compose_input}" ]] || {
    echo "Missing adaptation input: ${adaptation_dir}/${compose_input}" >&2
    exit 1
  }
  compose_source="${adaptation_dir#${REPO_DIR}/}/${compose_input}"

  output_root="${OUTPUT_DIR}/${producer}/${name}"
  source_dir="${output_root}/source"
  rm -rf "${output_root}"
  mkdir -p "${output_root}"

  cd "${REPO_DIR}"
  PYTHONPATH="${REPO_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}" \
    "${PYTHON_BIN}" -m productive_k3s_adapters.cli convert compose "${compose_source}" \
      --name "${stack_name}" \
      --output "${source_dir}"

  cp "${metadata}" "${source_dir}/adaptation.yaml"
  version="$(yaml_stack_version "${source_dir}/stack.yaml")"
  [[ -n "${version}" ]] || version="0.1.0"
  package_dir="${output_root}/package"
  mkdir -p "${package_dir}/addons"

  {
    printf 'apiVersion: addons.productive-k3s.io/v1\n'
    printf 'kind: Stack\n'
    printf 'metadata:\n'
    printf '  name: %s\n' "${stack_name}"
    printf '  version: %s\n' "${version}"
    printf 'spec:\n'
    printf '  resolution:\n'
    printf '    mode: bundled\n'
    printf '  runtime:\n'
    printf '    compatibility:\n'
    printf '      kubernetes:\n'
    printf '        distros:\n'
    printf '          - k3s\n'
    printf '  addons:\n'
    stack_addon_paths "${source_dir}/stack.yaml" | while read -r addon_rel_path; do
      local addon_dir
      addon_dir="${source_dir}/${addon_rel_path}"
      local addon_manifest addon_name addon_version addon_artifact
      addon_manifest="${addon_dir}/addon.yaml"
      [[ -f "${addon_manifest}" ]] || continue
      addon_name="$(yaml_metadata_field "${addon_manifest}" name)"
      addon_version="$(yaml_metadata_field "${addon_manifest}" version)"
      [[ -n "${addon_name}" ]] || addon_name="$(basename "${addon_dir}")"
      [[ -n "${addon_version}" ]] || addon_version="0.1.0"
      addon_artifact="${addon_name}-${addon_version}.tgz"
      tar -czf "${package_dir}/addons/${addon_artifact}" -C "${addon_dir}" .
      printf '    - name: %s\n' "${addon_name}"
      printf '      source: addons/%s\n' "${addon_artifact}"
    done
  } > "${package_dir}/stack.yaml"

  cp "${source_dir}/README.md" "${package_dir}/README.md"
  cp "${source_dir}/conversion-report.json" "${package_dir}/conversion-report.json"
  cp "${source_dir}/adaptation.yaml" "${package_dir}/adaptation.yaml"

  artifact="${output_root}/${stack_name}-${version}.tgz"
  tar -czf "${artifact}" -C "${package_dir}" .
  echo "Created ${artifact}"
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

while IFS= read -r adaptation_dir; do
  build_one "${adaptation_dir}"
done < <(adaptation_dirs "$@")

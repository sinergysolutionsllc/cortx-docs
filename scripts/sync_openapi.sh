#!/usr/bin/env bash
set -euo pipefail

# sync_openapi.sh
# Clone per-service repositories and stage their OpenAPI specs inside
# docs/services/<service>/openapi.yaml. JSON specs are converted to YAML so the
# documentation build has a single canonical format. If a spec cannot be found,
# a minimal health-check stub is written so downstream jobs remain deterministic.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="${ROOT}/tmp/openapi-sync"
OUT_DIR="${ROOT}/docs/services"
OWNER="${GH_OWNER:-sinergysolutionsllc}"
TOKEN="${ORG_READ_TOKEN:-}"
IFS=',' read -r -a SERVICES <<< "${SERVICES:-gateway,identity,validation,ai-broker,workflow,compliance,ledger,ocr,rag}"

# Known spec locations (relative to repo root). Adjust as needed per service.
declare -A PATHS=(
  [gateway]="openapi.yaml"
  [identity]="openapi.json"
  [validation]="services/validation/openapi.yaml"
  ["ai-broker"]="openapi/openapi.yml"
  [workflow]="specs/openapi.yaml"
  [compliance]="specs/openapi.yaml"
  [ledger]="openapi.yaml"
  [ocr]="api/openapi.yaml"
  [rag]="openapi.yaml"
)

# Optional explicit repo overrides. Defaults to https://github.com/${OWNER}/<svc>.git
declare -A REPOS=(
  [gateway]="https://github.com/${OWNER}/gateway.git"
  [identity]="https://github.com/${OWNER}/identity.git"
  [validation]="https://github.com/${OWNER}/validation.git"
  ["ai-broker"]="https://github.com/${OWNER}/ai-broker.git"
  [workflow]="https://github.com/${OWNER}/workflow.git"
  [compliance]="https://github.com/${OWNER}/compliance.git"
  [ledger]="https://github.com/${OWNER}/ledger.git"
  [ocr]="https://github.com/${OWNER}/ocr.git"
  [rag]="https://github.com/${OWNER}/rag.git"
)

repo_url() {
  local svc="$1"
  local base="${REPOS[$svc]:-https://github.com/${OWNER}/${svc}.git}"
  if [[ -n "${TOKEN}" ]]; then
    echo "${base/https:\/\/github.com\//https://x-access-token:${TOKEN}@github.com/}"
  else
    echo "${base}"
  fi
}

copy_spec_or_stub() {
  local svc="$1" src="$2" dest_dir="$3"
  mkdir -p "${dest_dir}"
  if [[ -n "${src}" && -f "${src}" ]]; then
    if [[ "${src}" == *.json ]]; then
      SRC="${src}" DST="${dest_dir}/openapi.yaml" python3 - <<'PY'
import json, yaml, os
from pathlib import Path
src = Path(os.environ['SRC'])
dst = Path(os.environ['DST'])
with src.open() as f:
    data = json.load(f)
dst.write_text(yaml.safe_dump(data, sort_keys=False))
PY
      echo "   ✔ ${svc}: converted ${src} -> openapi.yaml"
    else
      cp "${src}" "${dest_dir}/openapi.yaml"
      echo "   ✔ ${svc}: copied ${src}"
    fi
  else
    cat > "${dest_dir}/openapi.yaml" <<'YML'
openapi: 3.0.3
info:
  title: TBD Service API
  version: 0.0.0
paths:
  /health:
    get:
      summary: Health check
      responses:
        '200':
          description: OK
YML
    echo "   ⚠ ${svc}: spec not found, wrote stub"
  fi
}

rm -rf "${TMP_DIR}"
mkdir -p "${TMP_DIR}" "${OUT_DIR}"

if [[ -n "${TOKEN}" ]]; then
  echo "::add-mask::${TOKEN}"
fi

echo "==> Syncing OpenAPI specs"
for svc in "${SERVICES[@]}"; do
  [[ -z "${svc}" ]] && continue
  echo "==> ${svc}"
  tmp_repo="${TMP_DIR}/${svc}"
  dest_dir="${OUT_DIR}/${svc}"

  git clone --depth 1 "$(repo_url "${svc}")" "${tmp_repo}" >/dev/null 2>&1 || {
    echo "   ⚠ ${svc}: clone failed, writing stub"
    copy_spec_or_stub "${svc}" "" "${dest_dir}"
    continue
  }

  candidate=""
  if [[ -n "${PATHS[$svc]:-}" ]]; then
    local_path="${tmp_repo}/${PATHS[$svc]}"
    [[ -f "${local_path}" ]] && candidate="${local_path}"
  fi

  if [[ -z "${candidate}" ]]; then
    candidate="$(find "${tmp_repo}" -maxdepth 4 -type f \
      \( -name 'openapi.yaml' -o -name 'openapi.yml' -o -name 'openapi.json' \) | head -n 1)"
  fi

  copy_spec_or_stub "${svc}" "${candidate}" "${dest_dir}"

done

rm -rf "${TMP_DIR}"
echo "All specs written to ${OUT_DIR}"

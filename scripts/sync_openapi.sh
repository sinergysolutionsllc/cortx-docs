#!/usr/bin/env bash
set -euo pipefail

# --- Repo URLs ---------------------------------------------------------------
declare -A REPOS=(
  [gateway]="https://github.com/sinergysolutionsllc/gateway.git"
  [identity]="https://github.com/sinergysolutionsllc/identity.git"
  [validation]="https://github.com/sinergysolutionsllc/validation.git"
  [ai-broker]="https://github.com/sinergysolutionsllc/ai-broker.git"
  [workflow]="https://github.com/sinergysolutionsllc/workflow.git"
  [compliance]="https://github.com/sinergysolutionsllc/compliance.git"
  [ledger]="https://github.com/sinergysolutionsllc/ledger.git"
  [ocr]="https://github.com/sinergysolutionsllc/ocr.git"
  [rag]="https://github.com/sinergysolutionsllc/rag.git"
)

# --- Known spec paths (override per service if you know them) ----------------
# Example:
# PATHS[gateway]="openapi.yaml"
# PATHS[identity]="api/openapi.yaml"
declare -A PATHS=(
  [gateway]="openapi.yaml"
  [identity]="api/openapi.yaml"
  [validation]="services/validation/openapi.yaml"
  [ai-broker]="openapi/openapi.yml"
  [workflow]="specs/openapi.yaml"
  [compliance]="specs/openapi.yaml"
  [ledger]="openapi.yaml"
  [ocr]="api/openapi.yaml"
  [rag]="openapi.yaml"
)

# --- Begin -------------------------------------------------------------------
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "${ROOT}/docs/services"
rm -rf "${ROOT}/tmp"
mkdir -p "${ROOT}/tmp"

for svc in "${!REPOS[@]}"; do
  echo "==> Syncing ${svc}"
  repo="${REPOS[$svc]}"
  tmpdir="${ROOT}/tmp/${svc}"
  dest="${ROOT}/docs/services/${svc}"
  mkdir -p "${dest}"

  git clone --depth 1 "${repo}" "${tmpdir}"

  resolved=""

  # 1) Try explicit PATHS override
  if [[ -n "${PATHS[$svc]:-}" ]]; then
    cand="${tmpdir}/${PATHS[$svc]}"
    if [[ -f "${cand}" ]]; then
      resolved="${cand}"
    fi
  fi

  # 2) Fallback quick search to maxdepth 4
  if [[ -z "${resolved}" ]]; then
    while IFS= read -r cand; do
      resolved="${cand}"
      break
    done < <(find "${tmpdir}" -maxdepth 4 -type f \( -name "openapi.yaml" -o -name "openapi.yml" \) | head -n 1)
  fi

  # 3) Copy or write stub
  if [[ -n "${resolved}" && -f "${resolved}" ]]; then
    cp "${resolved}" "${dest}/openapi.yaml"
    echo "   ✔ Found spec at: ${resolved#${tmpdir}/}"
  else
    echo "   ⚠ No spec found — writing stub for ${svc}"
    cat > "${dest}/openapi.yaml" <<'YML'
openapi: 3.0.3
info:
  title: TBD Service API
  version: 0.0.0
paths:
  /health:
    get:
      summary: Health check
      responses:
        '200': { description: OK }
YML
  fi
done

rm -rf "${ROOT}/tmp"
echo "All service specs synced to docs/services/*/openapi.yaml"

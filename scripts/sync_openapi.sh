#!/usr/bin/env bash
set -euo pipefail

ORG="sinergysolutionsllc"
SERVICES=(gateway identity validation ai-broker workflow compliance ledger ocr rag)

# Use GITHUB_TOKEN if available (CI), else clone anonymously
BASE_URL="https://github.com/${ORG}"
if [[ -n "${GITHUB_TOKEN:-}" ]]; then
  BASE_URL="https://${GITHUB_TOKEN}@github.com/${ORG}"
fi

stub_spec() {
  local svc="$1"
  cat <<YAML
openapi: 3.0.3
info:
  title: ${svc^} API (stub)
  version: 0.0.0
servers:
  - url: http://localhost
paths:
  /health:
    get:
      summary: Health check
      responses:
        '200': { description: OK }
YAML
}

for s in "${SERVICES[@]}"; do
  echo "Syncing OpenAPI for: $s"
  mkdir -p "docs/services/$s"
  tmpdir=$(mktemp -d)
  repo_url="${BASE_URL}/${s}.git"
  if git clone --depth 1 "$repo_url" "$tmpdir/repo" >/dev/null 2>&1; then
    spec=$(find "$tmpdir/repo" -maxdepth 4 -type f -name openapi.yaml | head -n1 || true)
    if [[ -n "${spec:-}" && -f "$spec" ]]; then
      cp "$spec" "docs/services/$s/openapi.yaml"
      echo "  -> copied from $(realpath --relative-to="$tmpdir/repo" "$spec" 2>/dev/null || echo "$spec")"
    else
      echo "  !! openapi.yaml not found, writing stub"
      stub_spec "$s" > "docs/services/$s/openapi.yaml"
    fi
  else
    echo "  !! clone failed for $repo_url, writing stub"
    stub_spec "$s" > "docs/services/$s/openapi.yaml"
  fi
  rm -rf "$tmpdir"
done

echo "Sync complete."


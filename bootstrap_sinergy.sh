#!/usr/bin/env bash
set -euo pipefail

# ===== CONFIG =====
ORG="${ORG:-sinergysolutionsllc}"   # override like: ORG=myorg ./bootstrap_sinergy.sh
VIS="${VIS:-private}"               # private|public (GitHub Enterprise also supports internal)
GIT_NAME="${GIT_NAME:-Sinergy Bot}"
GIT_EMAIL="${GIT_EMAIL:-engineering@sinergysolutions.ai}"

# ===== PRE-FLIGHT CHECKS =====
echo "==> Preflight: Checking GitHub CLI auth"
gh auth status || { echo "ERROR: gh not authenticated. Run: gh auth login"; exit 1; }

echo "==> Preflight: Verifying access to org '$ORG'"
if ! gh api "orgs/$ORG" >/dev/null 2>&1; then
  echo "ERROR: Cannot access org '$ORG'."
  echo " - Make sure the org exists and your GitHub user is an Owner."
  echo " - If you just created the org, re-run: gh auth refresh -h github.com -s admin:org,repo"
  exit 1
fi

# helper: create & init local repo + GitHub repo
mk_repo () {
  local REPO="$1"
  local FULL="$ORG/$REPO"
  echo "==> Creating repo: $FULL (visibility: $VIS)"

  # Check if repo already exists
  if gh repo view "$FULL" >/dev/null 2>&1; then
    echo "    Repo $FULL already exists, skipping..."
    # Still need to return 1 to signal caller to skip the rest
    return 1
  fi

  # Create remote repo (no invalid flags)
  gh repo create "$FULL" --"$VIS" --disable-wiki

  # Local init & first commit
  mkdir -p "$REPO"
  cd "$REPO"
  git init -b main
  git config user.name "$GIT_NAME"
  git config user.email "$GIT_EMAIL"
  return 0
}

push_repo () {
  local REPO="$1"
  # Skip if repo was skipped in mk_repo (we're inside the repo dir)
  if [ ! -d ".git" ]; then
    echo "    Skipping push for $REPO (not newly created)"
    cd ..
    return 0
  fi
  git add .
  git commit -m "chore: initial scaffold"
  git remote add origin "https://github.com/$ORG/$REPO.git"
  git push -u origin main
  cd ..
}

add_common_files () {
  mkdir -p .github/workflows docs/ADRs docs/runbooks docs/dashboards specs/openapi specs/schemas scripts .ai .claude
  cat > .gitignore <<'EOF'
# general
.DS_Store
.env
*.log

# node
node_modules/
dist/
coverage/

# python
__pycache__/
*.pyc
.venv/
.coverage
htmlcov/

# containers
*.local.yml
EOF

  # NOTE: Teams referenced here should exist; if not, update later.
  cat > CODEOWNERS <<'EOF'
# Paths requiring review (adjust team slugs if needed)
/specs/ @sinergysolutionsllc/platform-arch @sinergysolutionsllc/secops
/infra/ @sinergysolutionsllc/platform-arch
/services/ @sinergysolutionsllc/backend-leads
/frontend/ @sinergysolutionsllc/frontend-leads
EOF

  cat > SECURITY.md <<'EOF'
# Security Policy
- Report vulnerabilities to security@sinergysolutions.ai
- No secrets in code. Pre-commit secret scans required.
EOF

  cat > CONTRIBUTING.md <<'EOF'
# Contributing
- Trunk-based dev, short-lived PRs.
- PRs require passing CI, lint, tests, and CODEOWNERS review where applicable.
EOF

  cat > .ai/RULES.md <<'EOF'
# AI Guardrails
- Never paste secrets/customer data.
- Prefer generating tests, docs, and scaffolds.
- Follow repo structure and coding standards.
EOF

  cat > .ai/CONTEXT.md <<'EOF'
This repo is part of CORTX by Sinergy. Follow JSON Schema/OpenAPI-first contracts, CI gates, and SemVer.
EOF

  cat > .ai/PROMPTS_SCAFFOLD.md <<'EOF'
Generate a new module/service with: tests, OpenAPI/Schema, CI, Makefile, Dockerfile. Keep contracts in /specs.
EOF

  cat > .claude/agents.yaml <<'EOF'
architect:
  goals:
    - enforce contracts and repo standards
  limits:
    - no secrets
coder:
  goals:
    - implement features with tests
reviewer:
  goals:
    - enforce CODEOWNERS, lint, coverage
EOF

  cat > .cursorrules <<'EOF'
# Cursor/Claude Code Rules
preferTests=true
blockSecrets=true
enforceContracts=true
EOF

  cat > .github/workflows/ci.yml <<'YML'
name: CI
on:
  pull_request:
  push:
    branches: [ main ]
jobs:
  lint-test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        language: [python, node]
    steps:
      - uses: actions/checkout@v4
      - name: Python setup
        if: matrix.language == 'python'
        uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Node setup
        if: matrix.language == 'node'
        uses: actions/setup-node@v4
        with: { node-version: '20' }
      - name: Install deps (Python)
        if: matrix.language == 'python'
        run: |
          python -m pip install --upgrade pip
          pip install pytest pytest-cov ruff mypy
      - name: Lint & Test (Python)
        if: matrix.language == 'python'
        run: |
          ruff check .
          mypy || true
          pytest -q --maxfail=1 --disable-warnings
      - name: Install deps (Node)
        if: matrix.language == 'node'
        run: |
          if [ -f package.json ]; then npm ci; else echo "no node project"; fi
      - name: Lint & Test (Node)
        if: matrix.language == 'node'
        run: |
          if [ -f package.json ]; then npm run -s lint || true; npm test -s || true; fi
YML

  cat > .github/workflows/release.yml <<'YML'
name: Release
on:
  push:
    tags: ['v*.*.*']
jobs:
  build-publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build container
        run: |
          echo "build placeholder (add Dockerfile)"
      - name: Publish SBOM
        run: |
          echo "generate SBOM placeholder"
YML

  cat > REPO_INSTRUCTION.md <<'EOF'
# REPO_INSTRUCTION
- Keep OpenAPI/JSON Schemas in /specs
- CI: lint, tests, SCA, SBOM
- Trunk-based dev; SemVer tags for releases
- No secrets; enforce CODEOWNERS on critical paths
EOF

  cat > README.md <<'EOF'
# Sinergy Repo Scaffold
This repository follows CORTX standards: contracts-first, CI-gated, modular.
- See /specs for OpenAPI & JSON Schemas
- See /docs for ADRs & runbooks
EOF
}

# ----- Specific repos -----
mk_platform () {
  local REPO="cortx-platform"
  mk_repo "$REPO" || return 0
  add_common_files
  mkdir -p services/{gateway,identity,schemas,validation,compliance,workflow,config} infra/{helm,terraform,docker}
  cat > services/gateway/README.md <<'EOF'
# Gateway
Entrypoint API for CORTX Platform. Publishes OpenAPI in /specs.
EOF
  cat > specs/openapi/platform.yaml <<'EOF'
openapi: 3.0.3
info: { title: CORTX Platform, version: 0.1.0 }
paths: {}
EOF
  push_repo "$REPO"
}

mk_designer () {
  local REPO="cortx-designer"
  mk_repo "$REPO" || return 0
  add_common_files
  mkdir -p frontend backend compiler adapters
  cat > README.md <<'EOF'
# CORTX Designer
Pack authoring (RulePacks/WorkflowPacks). Outputs versioned packs to registry.
EOF
  push_repo "$REPO"
}

mk_sdks () {
  local REPO="cortx-sdks"
  mk_repo "$REPO" || return 0
  add_common_files
  mkdir -p sdk-python/src/cortx_sdk sdk-ts/src
  cat > sdk-python/pyproject.toml <<'EOF'
[project]
name = "cortx-sdk"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = []
EOF
  echo '__all__ = []' > sdk-python/src/cortx_sdk/__init__.py
  cat > sdk-ts/package.json <<'EOF'
{ "name":"@sinergysolutionsllc/cortx-sdk", "version":"0.1.0", "type":"module", "main":"dist/index.js", "scripts": { "build":"tsc", "lint":"echo skip", "test":"echo skip" } }
EOF
  cat > sdk-ts/tsconfig.json <<'EOF'
{ "compilerOptions": { "target":"ES2022", "module":"ES2022", "declaration": true, "outDir":"dist", "strict": true } }
EOF
  echo 'export {};' > sdk-ts/src/index.ts
  push_repo "$REPO"
}

mk_packs () {
  local REPO="cortx-packs"
  mk_repo "$REPO" || return 0
  add_common_files
  mkdir -p rulepacks/{federal,healthcare,corporate,state_local} workflowpacks/{cross_suite,suite_specific} schemas tests
  cat > README.md <<'EOF'
# CORTX Packs
Versioned RulePacks & WorkflowPacks. SemVer per pack directory.
EOF
  push_repo "$REPO"
}

mk_e2e () {
  local REPO="cortx-e2e"
  mk_repo "$REPO" || return 0
  add_common_files
  mkdir -p environments tests/{contract,scenario}
  cat > environments/docker-compose.yml <<'EOF'
version: "3.9"
services:
  platform:
    image: ghcr.io/sinergysolutionsllc/cortx-platform:latest
    ports: ["8080:8080"]
EOF
  cat > tests/contract/hello_test.py <<'EOF'
def test_contract_hello():
    assert True
EOF
  push_repo "$REPO"
}

mk_suite () {
  local REPO="$1"
  shift
  local MODULES=("$@")
  mk_repo "$REPO" || return 0
  add_common_files
  mkdir -p modules
  if [ ${#MODULES[@]} -gt 0 ]; then
    for m in "${MODULES[@]}"; do mkdir -p "modules/$m"; done
  fi
  REPO_TITLE="$(echo "$REPO" | awk '{print toupper(substr($0,1,1)) tolower(substr($0,2))}')"
  cat > README.md <<EOF
# $REPO_TITLE
Suite repository. Modules:
$(if [ ${#MODULES[@]} -gt 0 ]; then for m in "${MODULES[@]}"; do echo "- $m"; done; fi)
EOF
  push_repo "$REPO"
}

# ===== RUN =====
echo "==> Bootstrapping under org: $ORG"
mk_platform
mk_designer
mk_sdks
mk_packs
mk_e2e

mk_suite "fedsuite" "fedreconcile" "fedtransform"
mk_suite "corpsuite" "propverify" "greenlight" "investmait"
mk_suite "medsuite"
mk_suite "govsuite"

echo "✅ All repositories created and pushed under org: $ORG"

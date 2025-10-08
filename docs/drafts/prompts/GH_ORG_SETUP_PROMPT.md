

# Claude Code — Org Setup & Rails (Steps 3–10)

You are **Claude Code**. Execute the following to finish setting up the Sinergy Solutions GitHub org rails for **`sinergysolutionsllc`**.  
Assume repos exist:  
`cortx-platform`, `cortx-designer`, `cortx-sdks`, `cortx-packs`, `cortx-e2e`, `fedsuite`, `corpsuite`, `medsuite`, `govsuite`.

**Global**
- Local working dir: `~/Development/sinergysolutionsllc`
- Org: `sinergysolutionsllc`
- Be **idempotent**: create only if missing; modify in place if present.
- After file changes: `git add`, `git commit -m "<clear message>"`, `git push`.
- Stop on error and report it.

---

## Step 3 — Apply branch protection (JSON payload; safe/minimal → tighten later)

**A) Ensure each repo has at least 1 commit on `main`** (skip if already has commits)
```bash
ORG=sinergysolutionsllc
cd ~/Development/sinergysolutionsllc
for r in cortx-platform cortx-designer cortx-sdks cortx-packs cortx-e2e fedsuite corpsuite medsuite govsuite; do
  if ! git -C "$r" rev-parse HEAD >/dev/null 2>&1; then
    echo "Seeding $r"
    mkdir -p "$r"
    ( cd "$r" && git init -b main \
      && echo "# $r" > README.md \
      && git add README.md \
      && git commit -m "chore: seed repo" \
      && git remote add origin "https://github.com/$ORG/$r.git" \
      && git push -u origin main )
  fi
  # trigger a CI run once
  ( cd "$r" && date +"%Y-%m-%d %H:%M:%S" >> .seed-ci && git add .seed-ci && git commit -m "chore: trigger CI" && git push )
done
```

**B) Minimal protection (no required contexts yet)**
```bash
ORG=sinergysolutionsllc
for r in cortx-platform cortx-designer cortx-sdks cortx-packs cortx-e2e fedsuite corpsuite medsuite govsuite; do
  gh api -X PUT "repos/$ORG/$r/branches/main/protection" \
    -H "Accept: application/vnd.github+json" \
    --input - <<'JSON'
{
  "required_status_checks": null,
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "required_approving_review_count": 1
  },
  "restrictions": null
}
JSON
done
```

**C) Full protection (require the “CI” check)** — run after at least one CI run exists:
```bash
ORG=sinergysolutionsllc
for r in cortx-platform cortx-designer cortx-sdks cortx-packs cortx-e2e fedsuite corpsuite medsuite govsuite; do
  gh api -X PUT "repos/$ORG/$r/branches/main/protection" \
    -H "Accept: application/vnd.github+json" \
    --input - <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["CI"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "required_approving_review_count": 1
  },
  "restrictions": null
}
JSON
done
```

**Verify**
```bash
gh api repos/sinergysolutionsllc/cortx-platform/branches/main/protection | jq .
```

---

## Step 4 — Create common labels in all repos
```bash
cd ~/Development/sinergysolutionsllc
for r in cortx-platform cortx-designer cortx-sdks cortx-packs cortx-e2e fedsuite corpsuite medsuite govsuite; do
  for L in "type:feature:#0E8A16" "type:bug:#D73A4A" "type:chore:#5319E7" "priority:high:#B60205" "security:#B60205" "infra:#1D76DB"; do
    NAME="${L%%:*}"; COLOR="${L##*:}"
    gh label create --repo sinergysolutionsllc/$r "$NAME" -c "$COLOR" 2>/dev/null || gh label edit --repo sinergysolutionsllc/$r "$NAME" -c "$COLOR"
  done
done
```

---

## Step 5 — `cortx-platform`: FastAPI gateway + GHCR release workflow

**Files**
- `services/gateway/app.py`
```python
from fastapi import FastAPI

app = FastAPI(title="CORTX Platform Gateway", version="0.1.0")

@app.get("/health")
def health():
    return {"ok": True}
```

- `services/gateway/requirements.txt`
```
fastapi==0.115.0
uvicorn[standard]==0.30.6
```

- `services/gateway/Dockerfile`
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY services/gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/gateway .
EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
```

- Replace `/.github/workflows/release.yml`
```yaml
name: Release
on:
  push:
    tags: ['v*.*.*']
jobs:
  docker:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      - name: Login GHCR
        run: echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin
      - name: Build
        run: |
          IMAGE=ghcr.io/${{ github.repository }}/gateway:${{ github.ref_name }}
          docker build -t "$IMAGE" -f services/gateway/Dockerfile .
          echo "IMAGE=$IMAGE" >> $GITHUB_ENV
      - name: Push
        run: docker push "$IMAGE"
```

**Shell**
```bash
cd ~/Development/sinergysolutionsllc/cortx-platform
mkdir -p services/gateway
cat > services/gateway/app.py <<'PY'
from fastapi import FastAPI

app = FastAPI(title="CORTX Platform Gateway", version="0.1.0")

@app.get("/health")
def health():
    return {"ok": True}
PY
cat > services/gateway/requirements.txt <<'REQ'
fastapi==0.115.0
uvicorn[standard]==0.30.6
REQ
cat > services/gateway/Dockerfile <<'DOCKER'
FROM python:3.11-slim
WORKDIR /app
COPY services/gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/gateway .
EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
DOCKER
cat > .github/workflows/release.yml <<'YML'
name: Release
on:
  push:
    tags: ['v*.*.*']
jobs:
  docker:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      - name: Login GHCR
        run: echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u ${{ github.actor }} --password-stdin
      - name: Build
        run: |
          IMAGE=ghcr.io/${{ github.repository }}/gateway:${{ github.ref_name }}
          docker build -t "$IMAGE" -f services/gateway/Dockerfile .
          echo "IMAGE=$IMAGE" >> $GITHUB_ENV
      - name: Push
        run: docker push "$IMAGE"
YML
git add .
git commit -m "feat(gateway): minimal FastAPI + GHCR release workflow"
git push
git tag v0.1.0 && git push origin v0.1.0
```

---

## Step 6 — `cortx-e2e`: Compose the image + smoke test

**Files**
- `environments/docker-compose.yml`
```yaml
version: "3.9"
services:
  platform:
    image: ghcr.io/sinergysolutionsllc/cortx-platform/gateway:v0.1.0
    ports: ["8080:8080"]
```

- `requirements.txt`
```
requests==2.32.3
pytest==8.3.3
```

- `tests/scenario/smoke_test.py`
```python
import time, requests

def test_gateway_health():
    time.sleep(2)
    r = requests.get("http://localhost:8080/health", timeout=5)
    assert r.status_code == 200 and r.json().get("ok") is True
```

- `Makefile`
```make
compose_up:
\tdocker compose -f environments/docker-compose.yml up -d --remove-orphans
compose_down:
\tdocker compose -f environments/docker-compose.yml down -v
test:
\tpython3 -m pip install -r requirements.txt
\tpytest -q
```

**Shell**
```bash
cd ~/Development/sinergysolutionsllc/cortx-e2e
mkdir -p environments tests/scenario
cat > environments/docker-compose.yml <<'YML'
version: "3.9"
services:
  platform:
    image: ghcr.io/sinergysolutionsllc/cortx-platform/gateway:v0.1.0
    ports: ["8080:8080"]
YML
cat > requirements.txt <<'REQ'
requests==2.32.3
pytest==8.3.3
REQ
cat > tests/scenario/smoke_test.py <<'PY'
import time, requests

def test_gateway_health():
    time.sleep(2)
    r = requests.get("http://localhost:8080/health", timeout=5)
    assert r.status_code == 200 and r.json().get("ok") is True
PY
cat > Makefile <<'MAKE'
compose_up:
\tdocker compose -f environments/docker-compose.yml up -d --remove-orphans
compose_down:
\tdocker compose -f environments/docker-compose.yml down -v
test:
\tpython3 -m pip install -r requirements.txt
\tpytest -q
MAKE
git add .
git commit -m "test(e2e): compose platform gateway + smoke test"
git push
```

---

## Step 7 — `cortx-sdks`: TS publish to GitHub Packages; Py build artifact

**Files**
- `sdk-ts/.github/workflows/publish.yml`
```yaml
name: Publish TS SDK
on:
  push:
    tags: ['sdk-ts-v*.*.*']
jobs:
  publish:
    runs-on: ubuntu-latest
    permissions: { contents: read, packages: write }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', registry-url: 'https://npm.pkg.github.com' }
      - name: Set scope
        run: |
          cd sdk-ts
          jq '.name="@sinergysolutionsllc/cortx-sdk"' package.json > p.tmp && mv p.tmp package.json
      - name: Build
        run: |
          cd sdk-ts
          npm ci
          npm run build || echo "no build script; OK for bootstrap"
      - name: Publish
        run: |
          cd sdk-ts
          npm publish --access restricted
        env:
          NODE_AUTH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

- `sdk-python/.github/workflows/publish.yml`
```yaml
name: Publish Py SDK
on:
  push:
    tags: ['sdk-py-v*.*.*']
jobs:
  publish:
    runs-on: ubuntu-latest
    permissions: { contents: read, packages: write }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install build
        working-directory: sdk-python
      - run: python -m build
        working-directory: sdk-python
      - name: Upload dist as artifact
        uses: actions/upload-artifact@v4
        with:
          name: cortx-sdk-py-dist
          path: sdk-python/dist/**
```

**Shell**
```bash
cd ~/Development/sinergysolutionsllc/cortx-sdks
mkdir -p sdk-ts/.github/workflows sdk-python/.github/workflows
cat > sdk-ts/.github/workflows/publish.yml <<'YML'
name: Publish TS SDK
on:
  push:
    tags: ['sdk-ts-v*.*.*']
jobs:
  publish:
    runs-on: ubuntu-latest
    permissions: { contents: read, packages: write }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', registry-url: 'https://npm.pkg.github.com' }
      - name: Set scope
        run: |
          cd sdk-ts
          jq '.name="@sinergysolutionsllc/cortx-sdk"' package.json > p.tmp && mv p.tmp package.json
      - name: Build
        run: |
          cd sdk-ts
          npm ci
          npm run build || echo "no build script; OK for bootstrap"
      - name: Publish
        run: |
          cd sdk-ts
          npm publish --access restricted
        env:
          NODE_AUTH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
YML
cat > sdk-python/.github/workflows/publish.yml <<'YML'
name: Publish Py SDK
on:
  push:
    tags: ['sdk-py-v*.*.*']
jobs:
  publish:
    runs-on: ubuntu-latest
    permissions: { contents: read, packages: write }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install build
        working-directory: sdk-python
      - run: python -m build
        working-directory: sdk-python
      - name: Upload dist as artifact
        uses: actions/upload-artifact@v4
        with:
          name: cortx-sdk-py-dist
          path: sdk-python/dist/**
YML
git add .
git commit -m "chore(sdks): add TS & Py publish workflows"
git push
git tag sdk-ts-v0.1.0 && git push origin sdk-ts-v0.1.0
git tag sdk-py-v0.1.0 && git push origin sdk-py-v0.1.0
```

---

## Step 8 — `cortx-packs`: rulepack schema + first federal pack + lint CI

**Files**
- `schemas/rulepack.schema.json`
```json
{
  "$schema":"https://json-schema.org/draft/2020-12/schema",
  "title":"RulePack",
  "type":"object",
  "required":["name","version","rules"],
  "properties":{
    "name":{"type":"string"},
    "version":{"type":"string"},
    "rules":{"type":"array","items":{"type":"object"}}
  }
}
```

- `rulepacks/federal/gtas-gate/v1/pack.json`
```json
{
  "name": "federal.gtas-gate",
  "version": "1.0.0",
  "rules": []
}
```

- `.github/workflows/pack-lint.yml`
```yaml
name: Pack Lint
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Install validator
        run: pip install check-jsonschema
      - name: Validate packs
        run: |
          check-jsonschema --schemafile schemas/rulepack.schema.json rulepacks/**/v*/pack.json
```

**Shell**
```bash
cd ~/Development/sinergysolutionsllc/cortx-packs
mkdir -p schemas rulepacks/federal/gtas-gate/v1 .github/workflows
cat > schemas/rulepack.schema.json <<'JSON'
{
  "$schema":"https://json-schema.org/draft/2020-12/schema",
  "title":"RulePack",
  "type":"object",
  "required":["name","version","rules"],
  "properties":{
    "name":{"type":"string"},
    "version":{"type":"string"},
    "rules":{"type":"array","items":{"type":"object"}}
  }
}
JSON
cat > rulepacks/federal/gtas-gate/v1/pack.json <<'JSON'
{
  "name": "federal.gtas-gate",
  "version": "1.0.0",
  "rules": []
}
JSON
cat > .github/workflows/pack-lint.yml <<'YML'
name: Pack Lint
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Install validator
        run: pip install check-jsonschema
      - name: Validate packs
        run: |
          check-jsonschema --schemafile schemas/rulepack.schema.json rulepacks/**/v*/pack.json
YML
git add .
git commit -m "feat(packs): rulepack schema + federal gtas-gate v1 + lint CI"
git push
```

---

## Step 9 — Suites: module landing READMEs

**Shell**
```bash
# fedsuite
cd ~/Development/sinergysolutionsllc/fedsuite
mkdir -p modules/fedreconcile modules/dataflow
cat > modules/fedreconcile/README.md <<'MD'
# FedReconcile
- Input: Trial Balance + GTAS ATB
- Output: Discrepancies + suggested journal corrections (AI-optional)
- Depends on: cortx-sdks, rulepacks/federal/*
MD
cat > modules/dataflow/README.md <<'MD'
# DataFlow
- Input: legacy source extracts
- Output: normalized FBDI-ready datasets
- Reusable: adapters & mapping framework (formerly FedTransform)
MD
git add .
git commit -m "docs(fedsuite): seed module READMEs"
git push

# corpsuite
cd ~/Development/sinergysolutionsllc/corpsuite
mkdir -p modules/propverify modules/greenlight modules/investmait
cat > modules/propverify/README.md <<'MD'
# PropVerify
- Inputs: parcel & records datasets
- Output: title abstraction artifacts, alerts
- Notes: state data usage constraints respected
MD
cat > modules/greenlight/README.md <<'MD'
# Greenlight
- Purpose: vendor/go-to-market opportunity triage (SAM, eVA, etc.)
- Output: scored pipeline entries, document snapshots
MD
cat > modules/investmait/README.md <<'MD'
# InvestMait
- Purpose: real estate investment analysis (P/L, sensitivity)
- Output: scenario reports and alerts
MD
git add .
git commit -m "docs(corpsuite): seed module READMEs"
git push
```

---

## Step 10 — Renovate (optional, recommended)

1) Install the **Renovate** app for the org (GitHub UI).
2) Add config to each repo:

```bash
for r in cortx-platform cortx-designer cortx-sdks cortx-packs cortx-e2e fedsuite corpsuite medsuite govsuite; do
  cd ~/Development/sinergysolutionsllc/$r
  mkdir -p .github
  cat > .github/renovate.json <<'JSON'
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended"],
  "packageRules": [
    { "matchManagers": ["docker"], "enabled": true },
    { "matchManagers": ["pip_requirements"], "enabled": true },
    { "matchManagers": ["npm"], "enabled": true }
  ]
}
JSON
  git add .github/renovate.json
  git commit -m "chore: add Renovate config"
  git push
done
```

---

## Final verification checklist

- Labels exist in all repos.  
- `cortx-platform` Actions built & pushed `ghcr.io/sinergysolutionsllc/cortx-platform/gateway:v0.1.0`.  
- `cortx-e2e` can compose and pass the smoke test locally.  
- `cortx-sdks` TS package published to GitHub Packages (`@sinergysolutionsllc/cortx-sdk`); Python build artifact uploaded.  
- `cortx-packs` “Pack Lint” passes.  
- Suite READMEs present.  
- Renovate configs committed (if enabled).

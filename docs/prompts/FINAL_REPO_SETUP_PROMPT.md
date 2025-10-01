Role: You are a repo refactoring agent running in /Users/michael/Development/sinergysolutionsllc. You operate on the local filesystem and can run shell commands.

Goal: Implement the 6 follow-ups:
	1.	Commit & push current changes
	2.	Add Redoc pages to render each service’s OpenAPI inline (no extra MkDocs plugin)
	3.	Add nav entries to expose OpenAPI (YAML) and OpenAPI (Redoc) for each service
	4.	Add a Makefile for common tasks
	5.	Add spec linting to contracts CI (Redocly CLI)
	6.	Add a guard against accidental edits to published OpenAPI copies in docs/

Pre-flight
	•	Fail if mkdocs.yml, docs/, services/ are not present.

⸻

1) Commit & (optionally) push
set -euo pipefail

# Ensure we are in repo root
cd /Users/michael/Development/sinergysolutionsllc
test -f mkdocs.yml && test -d docs && test -d services || (echo "Missing mkdocs.yml/docs/services" && exit 1)

# Stage current changes if any
git add -A
if ! git diff --cached --quiet; then
  git commit -m "chore(docs): publish OpenAPI copies, sync guard, docs+contracts CI"
fi

# Optional push (safe to skip if not configured)
if git rev-parse --abbrev-ref --symbolic-full-name @{u} >/dev/null 2>&1; then
  git push
else
  echo "No upstream configured; skipping push."
fi

2) Generate Redoc pages per service

Create openapi.html per service that renders ./openapi.yaml with Redoc (CDN script). Services list: gateway identity validation ai-broker workflow compliance ledger ocr rag.

set -e

SERVICES=(gateway identity validation ai-broker workflow compliance ledger ocr rag)

for s in "${SERVICES[@]}"; do
  mkdir -p "docs/services/$s"
  cat > "docs/services/$s/openapi.html" <<'HTML'
<!doctype html>
<html>
  <head>
    <meta charset="utf-8"/>
    <title>OpenAPI</title>
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    <!-- Redoc via CDN -->
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
    <style>
      body { margin: 0; padding: 0; }
      .container { height: 100vh; }
    </style>
  </head>
  <body>
    <redoc spec-url="./openapi.yaml" hide-download-button="false" expand-responses="200,201,400,401,403,404"></redoc>
  </body>
</html>
HTML
  echo "Wrote docs/services/$s/openapi.html"
done

3) Update mkdocs.yml nav to include YAML + Redoc entries
	•	Under nav: - Services:, ensure each service section has:
	•	<Service>/README.md
	•	OpenAPI (YAML): services/<service>/openapi.yaml
	•	OpenAPI (Redoc): services/<service>/openapi.html

This patch keeps existing structure and replaces any flat paths.

python3 - <<'PY'
import io, re, sys, pathlib, yaml

repo = pathlib.Path(".")
mk = repo/"mkdocs.yml"
data = yaml.safe_load(mk.read_text())

def ensure_services_nav(d):
    nav = d.get("nav", [])
    # find Services block
    for item in nav:
        if isinstance(item, dict) and "Services" in item:
            svc = item["Services"]
            # Normalize services index
            try:
                idx = next(i for i, v in enumerate(svc) if (v == "services/index.md" or (isinstance(v, dict) and "services/index.md" in v.values())))
            except StopIteration:
                svc.insert(0, "services/index.md")
            # Map of expected entries
            services = [
                ("Gateway","gateway"),
                ("Identity","identity"),
                ("Validation","validation"),
                ("AI Broker","ai-broker"),
                ("Workflow","workflow"),
                ("Compliance","compliance"),
                ("Ledger","ledger"),
                ("OCR","ocr"),
                ("RAG","rag"),
            ]
            new = ["services/index.md"]
            # Keep any items before services if present
            seen = set()
            for name, folder in services:
                block = {
                    name: [
                        f"services/{folder}/README.md",
                        { "OpenAPI (YAML)": f"services/{folder}/openapi.yaml" },
                        { "OpenAPI (Redoc)": f"services/{folder}/openapi.html" },
                    ]
                }
                new.append(block)
                seen.add(folder)
            # Replace the full Services with our normalized list but preserve extra custom entries if any
            item["Services"] = new
            return True
    # If Services block not found, append it
    data.setdefault("nav", []).append({
        "Services": [
            "services/index.md",
            {"Gateway": [
                "services/gateway/README.md",
                {"OpenAPI (YAML)": "services/gateway/openapi.yaml"},
                {"OpenAPI (Redoc)": "services/gateway/openapi.html"},
            ]},
            {"Identity": [
                "services/identity/README.md",
                {"OpenAPI (YAML)": "services/identity/openapi.yaml"},
                {"OpenAPI (Redoc)": "services/identity/openapi.html"},
            ]},
            {"Validation": [
                "services/validation/README.md",
                {"OpenAPI (YAML)": "services/validation/openapi.yaml"},
                {"OpenAPI (Redoc)": "services/validation/openapi.html"},
            ]},
            {"AI Broker": [
                "services/ai-broker/README.md",
                {"OpenAPI (YAML)": "services/ai-broker/openapi.yaml"},
                {"OpenAPI (Redoc)": "services/ai-broker/openapi.html"},
            ]},
            {"Workflow": [
                "services/workflow/README.md",
                {"OpenAPI (YAML)": "services/workflow/openapi.yaml"},
                {"OpenAPI (Redoc)": "services/workflow/openapi.html"},
            ]},
            {"Compliance": [
                "services/compliance/README.md",
                {"OpenAPI (YAML)": "services/compliance/openapi.yaml"},
                {"OpenAPI (Redoc)": "services/compliance/openapi.html"},
            ]},
            {"Ledger": [
                "services/ledger/README.md",
                {"OpenAPI (YAML)": "services/ledger/openapi.yaml"},
                {"OpenAPI (Redoc)": "services/ledger/openapi.html"},
            ]},
            {"OCR": [
                "services/ocr/README.md",
                {"OpenAPI (YAML)": "services/ocr/openapi.yaml"},
                {"OpenAPI (Redoc)": "services/ocr/openapi.html"},
            ]},
            {"RAG": [
                "services/rag/README.md",
                {"OpenAPI (YAML)": "services/rag/openapi.yaml"},
                {"OpenAPI (Redoc)": "services/rag/openapi.html"},
            ]},
        ]
    })
    return True

ensure_services_nav(data)
mk.write_text(yaml.safe_dump(data, sort_keys=False))
print("Updated mkdocs.yml nav with YAML + Redoc entries.")
PY

# Validate build
mkdocs build --strict

4) Add a Makefile

cat > Makefile <<'MK'
.PHONY: docs verify contracts ci publish-openapi

docs:
\tmkdocs build --strict

verify:
\tpython3 scripts/verify_openapi_sync.py

contracts:
\t@echo "OpenAPI specs:"
\t@find services -name openapi.yaml -print

publish-openapi:
\t@echo "Publishing authoritative OpenAPI to docs..."
\t@SERVICES="gateway identity validation ai-broker workflow compliance ledger ocr rag"; \
\tfor s in $$SERVICES; do \
\t  mkdir -p docs/services/$$s; \
\t  cp services/$$s/openapi.yaml docs/services/$$s/openapi.yaml; \
\techo "Published $$s"; \
\tdone

ci: verify docs
MK

5) Add spec linting (Redocly) to contracts-ci
	•	Inject Redocly CLI install + lint step.

    python3 - <<'PY'
from pathlib import Path
wf = Path(".github/workflows/contracts-ci.yml")
y = wf.read_text()
if "redocly" not in y:
    y = y.rstrip() + """

  lint-openapi:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install Redocly CLI
        run: npm i -g @redocly/cli
      - name: Lint OpenAPI
        run: redocly lint "services/**/openapi.yaml"
"""
    wf.write_text(y)
    print("Enhanced contracts-ci.yml with Redocly lint.")
else:
    print("contracts-ci.yml already has Redocly lint.")
PY

6) Guard against accidental edits to published copies

Keep the SHA sync guard, and add a PR-time check that fails if docs copies were changed without matching authoritative changes.

python3 - <<'PY'
from pathlib import Path
wf = Path(".github/workflows/docs-ci.yml")
content = wf.read_text()
if "Docs copies changed" not in content:
    content = content.rstrip() + """

  check-docs-copies-changes:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4
      - name: Detect changes to docs OpenAPI copies without service changes
        run: |
          set -e
          # List changed files
          CHANGED=$(jq -r '.pull_request.base.sha + " " + .pull_request.head.sha' <(echo "${{ toJson(github.event) }}") | xargs -n2 sh -c 'git fetch origin "$0" && git diff --name-only "$0".."$1"' | sort -u)
          echo "$CHANGED" > changed.txt || true
          echo "Changed files:"
          cat changed.txt || true
          # Flags
          DOCS_CHANGED=$(grep -E '^docs/services/.+/openapi\.yaml$' changed.txt || true)
          SRV_CHANGED=$(grep -E '^services/.+/openapi\.yaml$' changed.txt || true)
          if [ -n "$DOCS_CHANGED" ] && [ -z "$SRV_CHANGED" ]; then
            echo "Docs copies changed but authoritative service specs did not. Please edit only services/<svc>/openapi.yaml and run 'make publish-openapi'."; exit 1
          fi
          echo "Change policy OK."
"""
    wf.write_text(content)
    print("Augmented docs-ci.yml with PR change guard.")
else:
    print("Change guard already present.")
PY

Final validation

# Re-publish to ensure copies are aligned (idempotent)
make publish-openapi
python3 scripts/verify_openapi_sync.py

# Strict docs build
mkdocs build --strict

Commit & (optional) push

git add -A
git commit -m "docs(openapi): add Redoc pages, nav entries, Makefile, Redocly lint, PR change guard"
if git rev-parse --abbrev-ref --symbolic-full-name @{u} >/dev/null 2>&1; then
  git push
else
  echo "No upstream configured; skipping push."
fi
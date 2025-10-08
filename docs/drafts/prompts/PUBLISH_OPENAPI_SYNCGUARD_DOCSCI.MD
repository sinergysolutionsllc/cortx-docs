Role: You are a repository refactoring agent for the CORTX monorepo. You operate on the local filesystem.

Goal:
	1.	Publish OpenAPI specs into docs/services/<svc>/openapi.yaml (copied from services/<svc>/openapi.yaml).
	2.	Update doc links in docs/services/<svc>/README.md to point to the published copy (./openapi.yaml) so links are clickable in the docs site.
	3.	Add a sync guard script that fails CI if the published copies drift from the authoritative specs.
	4.	Add docs-ci and contracts-ci GitHub Actions to enforce builds and sync.

Target services:
	•	gateway, identity, validation, ai-broker, workflow, compliance, ledger, ocr, rag

Actions

0) Pre-flight
	•	Confirm repo root contains: mkdocs.yml, docs/, services/, .github/.
	•	If missing, fail with a clear message.

1) Publish OpenAPI copies into docs

For each service <S> in the list:
	•	Ensure services/<S>/openapi.yaml exists. If not, create the minimal stub (as in previous scaffolder).
	•	Ensure docs/services/<S>/ exists.
	•	Copy services/<S>/openapi.yaml → docs/services/<S>/openapi.yaml (overwrite allowed).
	•	If docs/services/<S>/README.md contains a reference like:
	•	**OpenAPI:** \services//openapi.yaml`` or similar
then replace it with:
	•	**OpenAPI:** [openapi.yaml](./openapi.yaml)

2) Create sync guard script

Create scripts/verify_openapi_sync.py:

#!/usr/bin/env python3
import sys, hashlib, pathlib

SERVICES = ["gateway","identity","validation","ai-broker","workflow","compliance","ledger","ocr","rag"]

def sha256(p: pathlib.Path):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    repo = pathlib.Path(__file__).resolve().parents[1]
    failures = []
    for s in SERVICES:
        src = repo / "services" / s / "openapi.yaml"
        dst = repo / "docs" / "services" / s / "openapi.yaml"
        if not src.exists():
            failures.append(f"[MISSING] {src}")
            continue
        if not dst.exists():
            failures.append(f"[MISSING] {dst}")
            continue
        if sha256(src) != sha256(dst):
            failures.append(f"[DRIFT] {src} != {dst}")
    if failures:
        print("OpenAPI sync check FAILED:")
        print("\n".join(failures))
        sys.exit(1)
    print("OpenAPI sync check OK.")
if __name__ == "__main__":
    main()
Make it executable:
    chmod +x scripts/verify_openapi_sync.py
3) Add docs-ci workflow
Create .github/workflows/docs-ci.yml:
name: docs-ci
on:
  pull_request:
    paths:
      - 'docs/**'
      - 'mkdocs.yml'
      - '.github/workflows/docs-ci.yml'
  push:
    branches: [ main ]
    paths:
      - 'docs/**'
      - 'mkdocs.yml'

jobs:
  build-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install mkdocs deps
        run: |
          pip install mkdocs-material mkdocs-macros-plugin
      - name: Verify OpenAPI sync
        run: |
          python scripts/verify_openapi_sync.py
      - name: Build docs (strict)
        run: |
          mkdocs build --strict
4) Add contracts-ci workflow

Create .github/workflows/contracts-ci.yml:

name: contracts-ci
on:
  pull_request:
    paths:
      - 'services/**/openapi.yaml'
      - 'schemas/**'
      - '.github/workflows/contracts-ci.yml'
  push:
    branches: [ main ]
    paths:
      - 'services/**/openapi.yaml'
      - 'schemas/**'

jobs:
  validate-specs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate OpenAPI files exist
        run: |
          echo "Validating OpenAPI presence..."
          find services -name openapi.yaml | grep -q . || (echo "No OpenAPI files found" && exit 1)
      # Optional: add openapi-cli or spectral later for linting
      - name: Report files
        run: |
          find services -name openapi.yaml -print
5) Build & verify locally
	•	Run:
    python scripts/verify_openapi_sync.py
mkdocs build --strict

	•	Expect both to succeed.

6) Output summary
	•	List all docs/services/<S>/openapi.yaml created/updated.
	•	Confirm README links updated to [openapi.yaml](./openapi.yaml).
	•	Confirm CI workflows added.

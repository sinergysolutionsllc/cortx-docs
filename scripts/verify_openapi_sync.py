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


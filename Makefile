.PHONY: docs verify contracts ci publish-openapi

docs:
	mkdocs build --strict

verify:
	python3 scripts/verify_openapi_sync.py

contracts:
	@echo "OpenAPI specs:"
	@find services -name openapi.yaml -print

publish-openapi:
	@echo "Publishing authoritative OpenAPI to docs..."
	@SERVICES="gateway identity validation ai-broker workflow compliance ledger ocr rag"; \
	for s in $$SERVICES; do \
	  mkdir -p docs/services/$$s; \
	  cp services/$$s/openapi.yaml docs/services/$$s/openapi.yaml; \
	echo "Published $$s"; \
	done

ci: verify docs


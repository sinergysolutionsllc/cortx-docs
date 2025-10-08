# ==============================================================================
# Sinergy Solutions LLC - Organization-wide Makefile
#
# This Makefile orchestrates common tasks across all repositories in the
# sinergysolutionsllc multi-repo environment.
#
# Targets with the '-all' suffix (e.g., 'test-all') will iterate through
# the repositories defined in the REPOS variable and execute the
# corresponding target in each repository's local Makefile.
# ==============================================================================

# Defines the list of repositories to operate on.
REPOS := \
    cortx-platform \
    cortx-designer \
    cortx-sdks \
    cortx-packs \
    cortx-e2e \
    fedsuite \
    corpsuite \
    medsuite \
    govsuite

# Set the default goal to 'help'
.DEFAULT_GOAL := help

# ==============================================================================
# Org-wide Development Targets
# ==============================================================================

.PHONY: install-all test-all lint-all clean-all

install-all: ## Install dependencies for all repositories
	@for repo in $(REPOS); do \
		if [ -d "$$repo" ]; then \
			echo "--- Installing dependencies in $$repo ---"; \
			$(MAKE) -C $$repo install; \
		else \
			echo "--- Skipping $$repo (directory not found) ---"; \
		fi \
	done

test-all: ## Run tests in all repositories
	@for repo in $(REPOS); do \
		if [ -d "$$repo" ]; then \
			echo "--- Running tests in $$repo ---"; \
			$(MAKE) -C $$repo test; \
		else \
			echo "--- Skipping $$repo (directory not found) ---"; \
		fi \
	done

lint-all: ## Lint all repositories
	@for repo in $(REPOS); do \
		if [ -d "$$repo" ]; then \
			echo "--- Linting $$repo ---"; \
			$(MAKE) -C $$repo lint; \
		else \
			echo "--- Skipping $$repo (directory not found) ---"; \
		fi \
	done

clean-all: ## Clean all repositories
	@for repo in $(REPOS); do \
		if [ -d "$$repo" ]; then \
			echo "--- Cleaning $$repo ---"; \
			$(MAKE) -C $$repo clean; \
		else \
			echo "--- Skipping $$repo (directory not found) ---"; \
		fi \
	done

# ==============================================================================
# Org-wide Git Operations
# ==============================================================================

.PHONY: status-all update-all

status-all: ## Show git status for all repositories
	@for repo in $(REPOS); do \
		if [ -d "$$repo" ]; then \
			echo "--- Git status for $$repo ---"; \
			(cd $$repo && git status -s); \
		else \
			echo "--- Skipping $$repo (directory not found) ---"; \
		fi \
	done

update-all: ## Pull latest changes for all repositories
	@for repo in $(REPOS); do \
		if [ -d "$$repo" ]; then \
			echo "--- Updating $$repo ---"; \
			(cd $$repo && git pull); \
		else \
			echo "--- Skipping $$repo (directory not found) ---"; \
		fi \
	done

# ==============================================================================
# Documentation & CI Targets (Preserved from original Makefile)
# ==============================================================================

.PHONY: docs verify contracts ci publish-openapi

docs: ## Build MkDocs documentation
	mkdocs build --strict

verify: ## Verify OpenAPI spec synchronization
	python3 scripts/verify_openapi_sync.py

contracts: ## Find all OpenAPI contracts
	@echo "OpenAPI specs:"
	@find services -name openapi.yaml -print

publish-openapi: ## Publish all OpenAPI specs to the central docs
	@echo "Publishing authoritative OpenAPI to docs..."
	@SERVICES="gateway identity validation ai-broker workflow compliance ledger ocr rag"; \
	for s in $$SERVICES; do \
	  mkdir -p docs/services/$$s; \
	  cp services/$$s/openapi.yaml docs/services/$$s/openapi.yaml;
	echo "Published $$s"; \
	done

ci: verify docs ## Run CI checks (verify specs and build docs)

# ==============================================================================
# Help Target
# ==============================================================================

.PHONY: help

help: ## Display this help screen
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%%-20s\033[0m %%s\n", $$1, $$2}'

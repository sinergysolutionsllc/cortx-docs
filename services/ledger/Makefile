# Makefile for CORTX Ledger Service

.PHONY: help install install-dev test test-unit test-integration test-cov test-verbose clean lint format type-check

help:
	@echo "CORTX Ledger Service - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install production dependencies"
	@echo "  make install-dev      Install development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests"
	@echo "  make test-unit        Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make test-cov         Run tests with HTML coverage report"
	@echo "  make test-verbose     Run tests with verbose output"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run ruff linter"
	@echo "  make format           Format code with black"
	@echo "  make type-check       Run mypy type checker"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Remove test artifacts and cache"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:
	pytest

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-cov:
	pytest --cov=app --cov-report=html --cov-report=term
	@echo "Coverage report generated at htmlcov/index.html"

test-verbose:
	pytest -vv -s

lint:
	ruff check app/ tests/

format:
	black app/ tests/

type-check:
	mypy app/

clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf *.egg-info
	rm -rf __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

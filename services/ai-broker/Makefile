# Makefile for AI Broker Service
# Convenient commands for development and testing

.PHONY: help install test test-unit test-integration test-coverage test-fast lint format clean

help:
	@echo "AI Broker Service - Available Commands"
	@echo "======================================="
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install all dependencies (prod + dev)"
	@echo "  make install-prod     Install production dependencies only"
	@echo "  make install-dev      Install development dependencies only"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all tests with coverage"
	@echo "  make test-unit        Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make test-coverage    Run tests and generate HTML coverage report"
	@echo "  make test-fast        Run tests without coverage (fast)"
	@echo "  make test-ci          Run tests in CI mode (XML coverage)"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run linting (ruff)"
	@echo "  make format           Format code (black)"
	@echo "  make typecheck        Run type checking (mypy)"
	@echo "  make quality          Run all quality checks"
	@echo ""
	@echo "Development:"
	@echo "  make run              Run the service locally"
	@echo "  make dev              Run service in development mode (auto-reload)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Remove generated files and caches"
	@echo "  make clean-test       Remove test artifacts"
	@echo ""

install:
	pip install -r requirements.txt -r requirements-dev.txt

install-prod:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

test:
	pytest --cov=app --cov-report=term-missing -v

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-coverage:
	pytest --cov=app --cov-report=term-missing --cov-report=html -v
	@echo ""
	@echo "Coverage report generated: htmlcov/index.html"

test-fast:
	pytest -v --tb=short

test-ci:
	pytest --cov=app --cov-report=xml --cov-report=term -v

lint:
	ruff check app/ tests/

format:
	black app/ tests/

typecheck:
	mypy app/

quality: lint typecheck
	@echo "All quality checks passed!"

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

dev:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache .mypy_cache
	rm -rf htmlcov .coverage coverage.xml
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

clean-test:
	rm -rf .pytest_cache htmlcov .coverage coverage.xml

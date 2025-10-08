# Makefile for Identity Service
# Simplifies common development tasks

.PHONY: help install test test-unit test-integration test-cov test-watch clean lint format

# Default target
help:
	@echo "Available targets:"
	@echo "  make install          - Install all dependencies"
	@echo "  make test            - Run all tests"
	@echo "  make test-unit       - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make test-cov        - Run tests with coverage report"
	@echo "  make test-watch      - Run tests in watch mode"
	@echo "  make lint            - Run linting checks"
	@echo "  make format          - Format code"
	@echo "  make clean           - Clean up generated files"
	@echo "  make run             - Run the service locally"

# Install dependencies
install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

# Run all tests
test:
	pytest -v

# Run unit tests only
test-unit:
	pytest tests/unit/ -v

# Run integration tests only
test-integration:
	pytest tests/integration/ -v

# Run tests with coverage
test-cov:
	pytest --cov=app --cov-report=term-missing --cov-report=html
	@echo "\nCoverage report generated in htmlcov/index.html"

# Run tests in watch mode (requires pytest-watch)
test-watch:
	ptw -- -v

# Run linting
lint:
	ruff check app/ tests/
	mypy app/

# Format code
format:
	black app/ tests/
	ruff check --fix app/ tests/

# Clean up generated files
clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf **/__pycache__
	rm -rf **/*.pyc
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +

# Run the service
run:
	python app/main.py

# Run service with hot reload
dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

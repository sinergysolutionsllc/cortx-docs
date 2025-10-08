#!/bin/bash
# Run tests for Compliance Service

set -e

echo "================================"
echo "Compliance Service Test Suite"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
TEST_TYPE="${1:-all}"
COVERAGE="${2:-true}"

echo -e "${YELLOW}Running tests...${NC}"
echo ""

# Run tests based on type
case "$TEST_TYPE" in
    "unit")
        echo "Running unit tests only..."
        if [ "$COVERAGE" = "true" ]; then
            pytest tests/unit/ -v --cov=app --cov-report=term-missing --cov-report=html
        else
            pytest tests/unit/ -v
        fi
        ;;
    "integration")
        echo "Running integration tests only..."
        if [ "$COVERAGE" = "true" ]; then
            pytest tests/integration/ -v --cov=app --cov-report=term-missing --cov-report=html
        else
            pytest tests/integration/ -v
        fi
        ;;
    "all")
        echo "Running all tests..."
        if [ "$COVERAGE" = "true" ]; then
            pytest -v --cov=app --cov-report=term-missing --cov-report=html
        else
            pytest -v
        fi
        ;;
    *)
        echo "Unknown test type: $TEST_TYPE"
        echo "Usage: ./run_tests.sh [unit|integration|all] [true|false]"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Tests completed!${NC}"

if [ "$COVERAGE" = "true" ]; then
    echo ""
    echo "Coverage report generated at: htmlcov/index.html"
    echo "To view: open htmlcov/index.html"
fi

echo ""
echo "================================"

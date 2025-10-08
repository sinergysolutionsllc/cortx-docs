#!/bin/bash
# Test runner script for Gateway service
# Usage: ./run_tests.sh [options]

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}CORTX Gateway Test Runner${NC}"
echo "================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
pip install -q -r requirements.txt
pip install -q -r requirements-dev.txt

# Run tests based on argument
case "${1:-all}" in
    "unit")
        echo -e "${GREEN}Running unit tests...${NC}"
        pytest tests/unit/ -v
        ;;
    "integration")
        echo -e "${GREEN}Running integration tests...${NC}"
        pytest tests/integration/ -v
        ;;
    "auth")
        echo -e "${GREEN}Running authentication tests...${NC}"
        pytest -m auth -v
        ;;
    "proxy")
        echo -e "${GREEN}Running proxy tests...${NC}"
        pytest -m proxy -v
        ;;
    "coverage")
        echo -e "${GREEN}Running tests with coverage report...${NC}"
        pytest --cov=app --cov-report=html --cov-report=term-missing
        echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
        ;;
    "quick")
        echo -e "${GREEN}Running quick test (no coverage)...${NC}"
        pytest tests/ -v --no-cov
        ;;
    "parallel")
        echo -e "${GREEN}Running tests in parallel...${NC}"
        pytest tests/ -n auto
        ;;
    "all"|*)
        echo -e "${GREEN}Running all tests with coverage...${NC}"
        pytest
        ;;
esac

# Show summary
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
else
    echo -e "${RED}❌ Some tests failed!${NC}"
    exit 1
fi

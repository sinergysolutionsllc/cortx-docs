#!/bin/bash
# Quick Reference: RAG Service Test Commands

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}RAG Service Test Commands${NC}"
echo "================================"
echo ""

# Basic commands
echo -e "${GREEN}Basic Commands:${NC}"
echo "pytest                                    # Run all tests"
echo "pytest -v                                 # Verbose output"
echo "pytest -x                                 # Stop on first failure"
echo "pytest -s                                 # Show print statements"
echo ""

# By marker
echo -e "${GREEN}Run by Test Type:${NC}"
echo "pytest -m unit                            # Unit tests only (fast)"
echo "pytest -m integration                     # Integration tests only"
echo "pytest -m 'not slow'                      # Skip slow tests"
echo ""

# By file
echo -e "${GREEN}Run Specific Files:${NC}"
echo "pytest tests/unit/test_chunking.py       # Chunking tests"
echo "pytest tests/unit/test_embeddings.py     # Embedding tests"
echo "pytest tests/unit/test_retrieval.py      # Retrieval tests"
echo "pytest tests/unit/test_models.py         # Model tests"
echo "pytest tests/unit/test_database.py       # Database tests"
echo "pytest tests/integration/                # All integration tests"
echo ""

# Coverage
echo -e "${GREEN}Coverage Commands:${NC}"
echo "pytest --cov=app                          # Show coverage report"
echo "pytest --cov=app --cov-report=html       # Generate HTML report"
echo "pytest --cov=app --cov-report=term-missing # Show missing lines"
echo "open htmlcov/index.html                   # View HTML coverage"
echo ""

# Performance
echo -e "${GREEN}Performance:${NC}"
echo "pytest -n auto                            # Parallel execution (all CPUs)"
echo "pytest -n 4                               # Parallel with 4 workers"
echo "pytest --durations=10                     # Show 10 slowest tests"
echo ""

# Debugging
echo -e "${GREEN}Debugging:${NC}"
echo "pytest --pdb                              # Drop to debugger on failure"
echo "pytest --lf                               # Run last failed tests"
echo "pytest --ff                               # Run failed first, then rest"
echo "pytest --cache-clear                      # Clear pytest cache"
echo ""

# Specific tests
echo -e "${GREEN}Run Specific Test:${NC}"
echo "pytest tests/unit/test_chunking.py::TestChunkText::test_chunk_text_basic"
echo ""

# Watch mode (requires pytest-watch)
echo -e "${YELLOW}Watch Mode (if pytest-watch installed):${NC}"
echo "ptw                                       # Auto-run on file changes"
echo ""

# Database setup
echo -e "${GREEN}Database Setup:${NC}"
echo "docker run -d --name cortx-test-db -e POSTGRES_USER=cortx -e POSTGRES_PASSWORD=cortx_dev_password -e POSTGRES_DB=cortx_test -p 5432:5432 ankane/pgvector"
echo "export TEST_DATABASE_URL='postgresql://cortx:cortx_dev_password@localhost:5432/cortx_test'"
echo ""

# Useful combinations
echo -e "${GREEN}Useful Combinations:${NC}"
echo "pytest -m unit --cov=app --cov-report=term-missing -v"
echo "pytest -m integration -v -s"
echo "pytest --cov=app --cov-report=html -n auto"

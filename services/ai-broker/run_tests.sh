#!/bin/bash
# Test runner script for AI Broker service

set -e

echo "🧪 AI Broker Service - Test Suite Runner"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -f "app/main.py" ]; then
    echo "❌ Error: Please run this script from the ai-broker service directory"
    exit 1
fi

# Install dependencies if needed
echo "📦 Checking dependencies..."
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "⚠️  No virtual environment found. It's recommended to create one:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate"
    echo ""
fi

# Run tests based on argument
case "${1:-all}" in
    unit)
        echo "🔬 Running unit tests only..."
        pytest tests/unit/ -v
        ;;
    integration)
        echo "🔗 Running integration tests only..."
        pytest tests/integration/ -v
        ;;
    coverage)
        echo "📊 Running tests with coverage report..."
        pytest --cov=app --cov-report=term-missing --cov-report=html
        echo ""
        echo "✅ Coverage report generated in htmlcov/index.html"
        ;;
    fast)
        echo "⚡ Running tests (fast mode, no coverage)..."
        pytest -v --tb=short
        ;;
    ci)
        echo "🤖 Running tests in CI mode..."
        pytest --cov=app --cov-report=xml --cov-report=term -v
        ;;
    all|*)
        echo "🧪 Running all tests with coverage..."
        pytest --cov=app --cov-report=term-missing -v
        ;;
esac

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "✅ All tests passed!"
else
    echo ""
    echo "❌ Some tests failed (exit code: $exit_code)"
fi

exit $exit_code

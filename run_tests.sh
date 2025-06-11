#!/bin/bash
# BoarderframeOS Test Runner

echo "🧪 Running BoarderframeOS Tests..."

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated. Activating..."
    source .venv/bin/activate || {
        echo "❌ Failed to activate virtual environment. Run ./scripts/setup-dev.sh first."
        exit 1
    }
fi

# Run tests with coverage
echo "📊 Running tests with coverage..."
pytest tests/ -v --cov=core --cov=agents --cov=mcp --cov=ui --cov-report=html --cov-report=term

# Check if tests passed
if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
    echo "📊 Coverage report generated in htmlcov/index.html"
else
    echo "❌ Some tests failed. Check the output above."
    exit 1
fi
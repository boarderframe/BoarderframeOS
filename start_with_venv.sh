#!/bin/bash
# Start BoarderframeOS with proper virtual environment

# Get script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    echo "🐍 Activating virtual environment..."
    source .venv/bin/activate
else
    echo "⚠️  Virtual environment not found, using system Python"
fi

# Verify litellm is available
echo "🔍 Checking dependencies..."
python -c "import litellm" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ litellm is available"
else
    echo "📦 Installing litellm..."
    pip install litellm
fi

# Start the system
echo "🚀 Starting BoarderframeOS..."
exec python startup.py "$@"

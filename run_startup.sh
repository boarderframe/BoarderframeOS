#!/bin/bash
# Wrapper script to ensure startup.py runs with the virtual environment

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if venv exists
if [ ! -d "$DIR/.venv" ]; then
    echo "❌ Virtual environment not found at $DIR/.venv"
    echo "Please create it with: python3 -m venv .venv"
    exit 1
fi

# Activate the virtual environment
source "$DIR/.venv/bin/activate"

# Verify we're using the right Python
echo "🐍 Using Python: $(which python)"
echo "📦 Python version: $(python --version)"

# Run startup.py with the virtual environment Python
exec python "$DIR/startup.py" "$@"
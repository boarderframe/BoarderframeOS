#!/bin/bash
# Agent Cortex Startup Wrapper - Ensures proper startup with full logging

# Set up paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/tmp/agent_cortex_startup_wrapper.log"

# Create log file with timestamp
echo "========================================" > "$LOG_FILE"
echo "Agent Cortex Startup Wrapper" >> "$LOG_FILE"
echo "Started at: $(date)" >> "$LOG_FILE"
echo "Project root: $PROJECT_ROOT" >> "$LOG_FILE"
echo "Script dir: $SCRIPT_DIR" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Export Python path
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
echo "PYTHONPATH set to: $PYTHONPATH" >> "$LOG_FILE"

# Change to project root
cd "$PROJECT_ROOT" || exit 1
echo "Changed directory to: $(pwd)" >> "$LOG_FILE"

# Find Python executable (prefer virtual environment)
if [ -f "venv/bin/python" ]; then
    PYTHON_EXE="venv/bin/python"
elif [ -f ".venv/bin/python" ]; then
    PYTHON_EXE=".venv/bin/python"
else
    PYTHON_EXE="python3"
fi
echo "Using Python: $PYTHON_EXE" >> "$LOG_FILE"

# Test Python path
echo "Testing Python imports..." >> "$LOG_FILE"
$PYTHON_EXE -c "import sys; print('Python path:', sys.path)" >> "$LOG_FILE" 2>&1
$PYTHON_EXE -c "import core; print('core module found')" >> "$LOG_FILE" 2>&1
$PYTHON_EXE -c "import ui; print('ui module found')" >> "$LOG_FILE" 2>&1

# Start the robust launcher
echo "Starting Agent Cortex robust launcher..." >> "$LOG_FILE"
exec $PYTHON_EXE ui/agent_cortex_robust_launcher.py >> "$LOG_FILE" 2>&1

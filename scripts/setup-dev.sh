#!/bin/bash
# BoarderframeOS Development Environment Setup Script

echo "🚀 Setting up BoarderframeOS development environment..."

# Check if Python 3.11+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $PYTHON_VERSION detected. BoarderframeOS requires Python 3.11 or higher."
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing production dependencies..."
pip install -r requirements.txt

# Install development dependencies
echo "📦 Installing development dependencies..."
pip install pre-commit pytest pytest-asyncio pytest-cov black isort mypy flake8 bandit

# Install pre-commit hooks
echo "🪝 Installing pre-commit hooks..."
pre-commit install
pre-commit install --hook-type commit-msg

# Run initial code formatting
echo "🎨 Running initial code formatting..."
black . || true
isort . || true

# Create .env file from example if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from example..."
    cp .env.example .env
    echo "⚠️  Please update .env with your API keys and configuration"
fi

# Check Docker
if command -v docker &> /dev/null; then
    echo "🐳 Docker detected"
    if docker info &> /dev/null; then
        echo "✅ Docker daemon is running"
    else
        echo "⚠️  Docker daemon is not running. Please start Docker Desktop."
    fi
else
    echo "⚠️  Docker is not installed. Please install Docker for full functionality."
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs data/configs data/memories data/evolution

# Run initial tests
echo "🧪 Running initial tests..."
pytest tests/ -v || echo "⚠️  Some tests failed. This is expected for initial setup."

echo "
✅ Development environment setup complete!

Next steps:
1. Update .env with your API keys
2. Start Docker Desktop if not running
3. Run 'make docker-up' to start PostgreSQL and Redis
4. Run 'make start-system' to start BoarderframeOS

Available commands:
- make help         # Show all available commands
- make lint         # Run linting checks
- make format       # Auto-format code
- make test         # Run tests
- make start-system # Start complete system

Happy coding! 🚀
"
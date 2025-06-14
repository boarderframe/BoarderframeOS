#!/bin/bash
# Install voice dependencies for BoarderframeOS

echo "========================================"
echo "Installing Voice Dependencies"
echo "========================================"

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS"
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "Homebrew not found. Please install Homebrew first:"
        echo "/bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi

    # Install portaudio for macOS
    echo "Installing portaudio..."
    brew install portaudio

elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected Linux"
    # Install dependencies for Linux
    echo "Installing system dependencies..."
    sudo apt-get update
    sudo apt-get install -y portaudio19-dev python3-pyaudio

elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    echo "Detected Windows"
    echo "PyAudio should install directly with pip on Windows"
fi

echo ""
echo "Installing Python packages..."

# Install voice packages
pip install pyttsx3==2.90
pip install SpeechRecognition==3.10.1
pip install pyaudio==0.2.14

# Optional: Install Whisper for better speech recognition
echo ""
echo "Would you like to install Whisper for better speech recognition? (y/n)"
read -r response
if [[ "$response" == "y" ]]; then
    pip install openai-whisper
fi

echo ""
echo "========================================"
echo "Voice dependencies installation complete!"
echo "========================================"
echo ""
echo "You can now test voice features with:"
echo "  python test_enhanced_solomon.py"

#!/usr/bin/env python3
"""
Install voice dependencies for BoarderframeOS
Platform-independent installer
"""

import platform
import subprocess
import sys


def install_package(package):
    """Install a package using pip"""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


def main():
    print("=" * 60)
    print("BoarderframeOS Voice Dependencies Installer")
    print("=" * 60)

    system = platform.system()
    print(f"Detected OS: {system}")

    # Platform-specific instructions
    if system == "Darwin":  # macOS
        print("\n⚠️  macOS detected. You may need to install portaudio first:")
        print("  brew install portaudio")
        print("\nIf you don't have Homebrew, install it from https://brew.sh")
        input("\nPress Enter after installing portaudio (or to skip)...")

    elif system == "Linux":
        print("\n⚠️  Linux detected. You may need to install system dependencies:")
        print("  sudo apt-get install portaudio19-dev python3-pyaudio")
        input("\nPress Enter after installing dependencies (or to skip)...")

    # Install packages
    packages = [
        ("pyttsx3==2.90", "Text-to-Speech engine"),
        ("SpeechRecognition==3.10.1", "Speech recognition"),
        ("pyaudio==0.2.14", "Audio I/O"),
    ]

    print("\nInstalling Python packages...")

    for package, description in packages:
        print(f"\nInstalling {package} ({description})...")
        try:
            install_package(package)
            print(f"✓ {package} installed successfully")
        except Exception as e:
            print(f"❌ Failed to install {package}: {e}")
            print("  You may need to install system dependencies first")

    # Optional packages
    print("\n" + "-" * 60)
    print("Optional packages for enhanced features:")
    print("-" * 60)

    optional = [
        (
            "openai-whisper",
            "Better speech recognition (may take time to download models)",
        ),
        ("azure-cognitiveservices-speech", "Azure TTS/STT (requires Azure account)"),
        ("elevenlabs", "Premium voice synthesis (requires ElevenLabs account)"),
    ]

    for package, description in optional:
        response = input(f"\nInstall {package}? ({description}) [y/N]: ")
        if response.lower() == "y":
            try:
                install_package(package)
                print(f"✓ {package} installed")
            except Exception as e:
                print(f"❌ Failed to install {package}: {e}")

    print("\n" + "=" * 60)
    print("Installation complete!")
    print("=" * 60)

    print("\nTesting voice capabilities...")

    # Test imports
    try:
        import pyttsx3

        print("✓ pyttsx3 imported successfully")

        # Quick TTS test
        engine = pyttsx3.init()
        print("✓ TTS engine initialized")

        import speech_recognition as sr

        print("✓ Speech recognition imported successfully")

        import pyaudio

        print("✓ PyAudio imported successfully")

        print("\n✅ All voice dependencies are working!")

    except Exception as e:
        print(f"\n❌ Error testing voice dependencies: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure system audio libraries are installed")
        print("2. On macOS: brew install portaudio")
        print("3. On Linux: sudo apt-get install portaudio19-dev")

    print("\nNext steps:")
    print("1. Test enhanced Solomon: python test_enhanced_solomon.py")
    print("2. Interactive chat: python test_enhanced_solomon.py --interactive")
    print("3. Launch system: python enhanced_startup.py")


if __name__ == "__main__":
    main()

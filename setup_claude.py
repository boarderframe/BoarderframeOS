#!/usr/bin/env python3
"""
Setup script for Claude API integration
Helps configure the ANTHROPIC_API_KEY for BoarderframeOS agents
"""

import os
import sys
from pathlib import Path


def setup_claude_api():
    """Set up Claude API key for BoarderframeOS"""

    print("=" * 80)
    print("BoarderframeOS - Claude API Setup")
    print("=" * 80)

    # Check if .env file exists
    env_path = Path(__file__).parent / ".env"

    # Read existing .env if it exists
    existing_vars = {}
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    key, value = line.strip().split("=", 1)
                    existing_vars[key] = value

    # Check if API key already exists
    if "ANTHROPIC_API_KEY" in existing_vars:
        print("\n✓ ANTHROPIC_API_KEY is already configured in .env file")
        print(
            "  Current key starts with:",
            existing_vars["ANTHROPIC_API_KEY"][:10] + "...",
        )

        response = input("\nDo you want to update the API key? (y/n): ")
        if response.lower() != "y":
            print("Setup complete - existing key retained.")
            return

    # Get API key from user
    print("\nTo use Claude API for agent intelligence, you need an Anthropic API key.")
    print("Get your API key from: https://console.anthropic.com/")
    print("\nNote: The API key should start with 'sk-ant-'")

    api_key = input("\nEnter your ANTHROPIC_API_KEY: ").strip()

    # Validate key format
    if not api_key.startswith("sk-ant-"):
        print("\n⚠️  Warning: API key should start with 'sk-ant-'")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != "y":
            print("Setup cancelled.")
            return

    # Update existing vars
    existing_vars["ANTHROPIC_API_KEY"] = api_key

    # Write .env file
    with open(env_path, "w") as f:
        f.write("# BoarderframeOS Environment Variables\n\n")

        # Write all variables
        for key, value in existing_vars.items():
            f.write(f"{key}={value}\n")

        # Add other optional API keys with comments
        if "OPENAI_API_KEY" not in existing_vars:
            f.write("\n# Optional: OpenAI API Key (for fallback)\n")
            f.write("# OPENAI_API_KEY=sk-...\n")

        if "ELEVENLABS_API_KEY" not in existing_vars:
            f.write("\n# Optional: ElevenLabs API Key (for premium voices)\n")
            f.write("# ELEVENLABS_API_KEY=...\n")

        if "AZURE_SPEECH_KEY" not in existing_vars:
            f.write("\n# Optional: Azure Speech Services (for TTS/STT)\n")
            f.write("# AZURE_SPEECH_KEY=...\n")
            f.write("# AZURE_SPEECH_REGION=eastus\n")

    print("\n✓ Claude API key saved to .env file")
    print("✓ Enhanced agents will now use Claude for intelligence")

    # Test the setup
    print("\nTesting Claude integration...")
    try:
        from core.claude_integration import get_claude_integration

        claude = get_claude_integration()
        print("✓ Claude integration initialized successfully")

        # Simple test
        response = claude.get_sync_response(
            "solomon", "Say hello and confirm you're working", context={"test": True}
        )
        print(f"\nTest response from Solomon: {response[:100]}...")
        print("\n✓ Claude API is working correctly!")

    except Exception as e:
        print(f"\n❌ Error testing Claude API: {e}")
        print("\nPlease check:")
        print("1. Your API key is correct")
        print("2. You have an active Anthropic account")
        print("3. Your API key has sufficient credits")

    print("\n" + "=" * 80)
    print("Setup complete! You can now run enhanced agents with Claude intelligence.")
    print("=" * 80)

    print("\nNext steps:")
    print(
        "1. Install voice dependencies: pip install pyttsx3 SpeechRecognition pyaudio"
    )
    print("2. Test Solomon: python test_enhanced_solomon.py")
    print("3. Run interactive mode: python test_enhanced_solomon.py --interactive")


if __name__ == "__main__":
    setup_claude_api()

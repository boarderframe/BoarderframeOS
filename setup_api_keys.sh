#!/bin/bash

# API Keys Setup Script for Open WebUI Development Environment
# This script helps you configure API keys for cloud models

echo "🔑 API Keys Setup for Open WebUI Development Environment"
echo ""

# Function to securely read API key
read_api_key() {
    local service_name=$1
    local env_var=$2
    echo -n "Enter your $service_name API key (or press Enter to skip): "
    read -s api_key
    echo ""
    
    if [ ! -z "$api_key" ]; then
        echo "export $env_var=\"$api_key\"" >> ~/.bashrc
        echo "export $env_var=\"$api_key\"" >> ~/.zshrc
        export $env_var="$api_key"
        echo "✅ $service_name API key configured"
    else
        echo "⏭️  Skipping $service_name API key"
    fi
}

echo "This script will help you configure API keys for cloud models."
echo "You can skip any service you don't want to use."
echo ""

# OpenAI
echo "🤖 OpenAI Configuration"
echo "Required for: GPT-5, GPT-4o, O1, O3, embedding models"
read_api_key "OpenAI" "OPENAI_API_KEY"
echo ""

# Anthropic
echo "🧠 Anthropic Configuration"
echo "Required for: Claude models"
read_api_key "Anthropic" "ANTHROPIC_API_KEY"
echo ""

# Google
echo "🔍 Google Configuration"
echo "Required for: Gemini models"
read_api_key "Google" "GOOGLE_API_KEY"
echo ""

echo "📝 API Keys have been added to your shell configuration files."
echo "⚠️  For immediate effect, restart LiteLLM or run: source ~/.bashrc (or ~/.zshrc)"
echo ""
echo "🔄 To apply changes:"
echo "1. Restart LiteLLM: Kill the current process and run ./start_dev_environment.sh"
echo "2. Or source your shell config: source ~/.bashrc"
echo ""
echo "💡 Tip: Only configure the API keys for services you actually want to use."
echo "The local gpt-oss-20b model works without any API keys!"
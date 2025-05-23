#!/bin/bash
# Script to open the Solomon chat interface

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🌐 Opening Solomon Chat interface..."

# Open in browser (macOS)
open "file://${SCRIPT_DIR}/solomon_chat.html"

echo "✅ Solomon Chat interface opened in your browser"
echo "📌 Make sure the Solomon agent and chat server are running"

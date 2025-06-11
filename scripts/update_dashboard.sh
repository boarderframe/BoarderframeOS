#!/bin/bash
# Update dashboard to enhanced version

echo "🔄 Updating BoarderframeOS Dashboard..."

# Kill existing dashboard
pkill -f "persistent_ui.py" 2>/dev/null
pkill -f "python.*8888" 2>/dev/null

# Wait a moment
sleep 2

# Copy enhanced dashboard to persistent_ui.py
cp /Users/cosburn/BoarderframeOS/enhanced_dashboard.py /Users/cosburn/BoarderframeOS/persistent_ui.py

echo "✅ Dashboard updated to enhanced version"
echo ""
echo "🚀 To start the updated dashboard:"
echo "   ./start"
echo ""
echo "📊 New features:"
echo "   - Real-time service status"
echo "   - Live agent monitoring"
echo "   - System health indicators"
echo "   - Auto-refresh every 10 seconds"
echo "   - API endpoint at /api/status"

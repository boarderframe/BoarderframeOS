#!/bin/bash
# Capture BoarderframeOS browser window using AppleScript

# Generate timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_FILE="boarderframe_browser_${TIMESTAMP}.png"

echo "🖼️  BoarderframeOS Browser Window Capture"
echo "========================================"
echo ""

# Method 1: Try to capture the frontmost browser window
echo "📸 Attempting to capture browser window..."

# Use AppleScript to bring browser to front and get window ID
osascript <<EOF
tell application "System Events"
    set frontApp to name of first application process whose frontmost is true

    -- Try common browsers
    if frontApp contains "Chrome" or frontApp contains "Safari" or frontApp contains "Firefox" then
        tell application frontApp
            activate
        end tell
        delay 0.5
    else
        -- Try to find and activate a browser
        try
            tell application "Google Chrome"
                activate
            end tell
        on error
            try
                tell application "Safari"
                    activate
                end tell
            on error
                tell application "Firefox"
                    activate
                end tell
            end try
        end try
    end if
end tell
EOF

# Give browser time to come to front
sleep 1

# Now capture the active window
echo "Click on the BoarderframeOS window when the cursor changes..."
screencapture -W -x "$OUTPUT_FILE"

# Check if capture was successful
if [ -f "$OUTPUT_FILE" ]; then
    FILE_SIZE=$(stat -f%z "$OUTPUT_FILE" 2>/dev/null || stat -c%s "$OUTPUT_FILE" 2>/dev/null)
    echo ""
    echo "✅ Screenshot captured successfully!"
    echo "   File: $OUTPUT_FILE"
    echo "   Size: $FILE_SIZE bytes"

    # Try to open the screenshot
    if command -v open &> /dev/null; then
        echo "   Opening screenshot..."
        open "$OUTPUT_FILE"
    fi
else
    echo ""
    echo "❌ Screenshot capture failed"
    echo "   Please ensure you clicked on the browser window"
fi

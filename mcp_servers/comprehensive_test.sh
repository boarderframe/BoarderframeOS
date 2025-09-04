#!/bin/bash

echo "🚀 COMPREHENSIVE NETWORK MONITORING TEST"
echo "========================================"
echo "Testing JSON→SSE conversion detection across all monitoring layers"
echo ""

# Start monitoring logs in background
echo "📋 Starting log monitoring..."
tail -f /tmp/network_monitor.log > /tmp/live_monitor.log &
TAIL_PID=$!

echo "🔍 Running comprehensive tests..."

# Test 1: Direct MCP server calls (should be clean JSON)
echo "📍 Test 1: Direct MCP Server (Clean JSON)"
curl -v -H "Accept: application/json" \
     -H "Content-Type: application/json" \
     http://localhost:9004/test/json 2>&1 | tee /tmp/direct_mcp.log

echo -e "\n📍 Test 2: MCP Server with SSE Accept header"
curl -v -H "Accept: text/event-stream" \
     -H "Content-Type: application/json" \
     http://localhost:9004/test/json 2>&1 | tee /tmp/mcp_sse_request.log

echo -e "\n📍 Test 3: Open WebUI Frontend (HTML Response)"
curl -v -H "Accept: application/json" \
     http://localhost:8080/ 2>&1 | tee /tmp/openwebui_frontend.log

echo -e "\n📍 Test 4: Open WebUI API with SSE Accept"
curl -v -H "Accept: text/event-stream" \
     -H "Content-Type: application/json" \
     http://localhost:8080/api/models 2>&1 | tee /tmp/openwebui_sse.log

echo -e "\n📍 Test 5: Through Monitoring Proxy (Port 8081)"
curl -v -H "Accept: application/json" \
     http://localhost:8081/api/health 2>&1 | tee /tmp/proxy_test.log

echo -e "\n📍 Test 6: MCP through Proxy (Port 9005)"
curl -v -H "Accept: application/json" \
     http://localhost:9005/health 2>&1 | tee /tmp/mcp_proxy.log

# Test with streaming simulation
echo -e "\n📍 Test 7: Simulated Streaming Request"
(
echo "data: {\"message\": \"Hello\"}"
echo ""
echo "data: {\"message\": \"World\"}"
echo ""
echo "data: [DONE]"
echo ""
) | curl -v -X POST \
     -H "Content-Type: text/plain" \
     -H "Accept: text/event-stream" \
     --data-binary @- \
     http://httpbin.org/post 2>&1 | tee /tmp/simulated_sse.log

echo -e "\n🔍 ANALYSIS PHASE"
echo "=================="

echo "📊 Content-Type Analysis:"
echo "Direct MCP JSON responses:"
grep -i "content-type.*application/json" /tmp/direct_mcp.log /tmp/mcp_sse_request.log

echo -e "\nOpen WebUI responses:"
grep -i "content-type" /tmp/openwebui_frontend.log /tmp/openwebui_sse.log

echo -e "\n🚨 SSE Detection:"
echo "Requests with SSE Accept headers:"
grep -i "Accept: text/event-stream" /tmp/*.log

echo -e "\nResponses with SSE content-type:"
grep -i "content-type.*text/event-stream" /tmp/*.log

echo -e "\n📡 Data Format Analysis:"
echo "Looking for 'data:' prefixes in responses:"
grep -i "data:" /tmp/*.log

echo -e "\n🔄 Transfer Encoding:"
grep -i "transfer-encoding\|connection" /tmp/*.log

echo -e "\n📈 Proxy Traffic Analysis:"
if [ -f /tmp/network_analysis.json ]; then
    echo "Proxy captured $(jq '.total_requests // 0' /tmp/network_analysis.json) requests"
    echo "SSE conversions detected: $(jq '.conversions_detected // 0' /tmp/network_analysis.json)"
else
    echo "No proxy analysis file found yet"
fi

# Stop log monitoring
kill $TAIL_PID 2>/dev/null

echo -e "\n✅ COMPREHENSIVE MONITORING TEST COMPLETE"
echo "========================================="
echo "🎯 Key findings will be in:"
echo "   - Browser monitor: open /Users/cosburn/MCP Servers/browser_monitor.html"
echo "   - Log files: /tmp/*.log" 
echo "   - Network analysis: /tmp/network_analysis.json"
echo ""
echo "🔍 To check for JSON→SSE conversions:"
echo "   1. Look for Content-Type mismatches (JSON request → SSE response)"
echo "   2. Look for 'data:' prefixes in JSON endpoint responses"
echo "   3. Check proxy logs for transformation points"
echo ""

# Generate summary
echo "📋 SUMMARY REPORT" > /tmp/monitoring_summary.txt
echo "=================" >> /tmp/monitoring_summary.txt
echo "Test timestamp: $(date)" >> /tmp/monitoring_summary.txt
echo "" >> /tmp/monitoring_summary.txt
echo "Services tested:" >> /tmp/monitoring_summary.txt
echo "✓ MCP Server (localhost:9004) - Kroger API server" >> /tmp/monitoring_summary.txt
echo "✓ Open WebUI (localhost:8080) - Main web interface" >> /tmp/monitoring_summary.txt
echo "✓ Monitoring Proxy (localhost:8081) - Traffic interceptor" >> /tmp/monitoring_summary.txt
echo "✓ MCP Proxy (localhost:9005) - MCP traffic interceptor" >> /tmp/monitoring_summary.txt
echo "" >> /tmp/monitoring_summary.txt
echo "Total test files created: $(ls /tmp/*.log 2>/dev/null | wc -l)" >> /tmp/monitoring_summary.txt
echo "" >> /tmp/monitoring_summary.txt

cat /tmp/monitoring_summary.txt
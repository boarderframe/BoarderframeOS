#!/bin/bash

# Comprehensive curl testing script to identify SSE conversion points
# Tests various endpoints with different Accept headers

echo "🔍 Starting comprehensive Open WebUI API testing..."
echo "Target: http://localhost:8080"
echo "MCP Server: http://localhost:9004"
echo "======================================="

# Test 1: Standard JSON API call
echo "🧪 Test 1: Standard JSON API call"
curl -v -H "Accept: application/json" \
     -H "Content-Type: application/json" \
     http://localhost:8080/api/health 2>&1 | tee /tmp/test1_json.log

echo -e "\n======================================="

# Test 2: Request with SSE Accept header
echo "🧪 Test 2: SSE Accept header"
curl -v -H "Accept: text/event-stream" \
     -H "Content-Type: application/json" \
     http://localhost:8080/api/health 2>&1 | tee /tmp/test2_sse.log

echo -e "\n======================================="

# Test 3: Chat completion endpoint (likely to use SSE)
echo "🧪 Test 3: Chat completion endpoint"
curl -v -X POST \
     -H "Accept: application/json" \
     -H "Content-Type: application/json" \
     -d '{"model":"test","messages":[{"role":"user","content":"hello"}],"stream":false}' \
     http://localhost:8080/api/chat/completions 2>&1 | tee /tmp/test3_chat.log

echo -e "\n======================================="

# Test 4: Chat completion with streaming
echo "🧪 Test 4: Chat completion with streaming"
curl -v -X POST \
     -H "Accept: text/event-stream" \
     -H "Content-Type: application/json" \
     -d '{"model":"test","messages":[{"role":"user","content":"hello"}],"stream":true}' \
     http://localhost:8080/api/chat/completions 2>&1 | tee /tmp/test4_chat_stream.log

echo -e "\n======================================="

# Test 5: Direct MCP server call
echo "🧪 Test 5: Direct MCP server call"
curl -v -H "Accept: application/json" \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
     http://localhost:9004/ 2>&1 | tee /tmp/test5_mcp_direct.log

echo -e "\n======================================="

# Test 6: WebSocket connection test
echo "🧪 Test 6: WebSocket connection test"
curl -v \
     -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
     -H "Sec-WebSocket-Version: 13" \
     http://localhost:8080/ws 2>&1 | tee /tmp/test6_websocket.log

echo -e "\n======================================="

# Test 7: Open WebUI specific endpoints
echo "🧪 Test 7: Open WebUI models endpoint"
curl -v -H "Accept: application/json" \
     http://localhost:8080/api/models 2>&1 | tee /tmp/test7_models.log

echo -e "\n======================================="

# Test 8: Test with proxy monitoring
echo "🧪 Test 8: Via monitoring proxy"
curl -v -H "Accept: application/json" \
     -H "Content-Type: application/json" \
     http://localhost:8081/api/health 2>&1 | tee /tmp/test8_proxy.log

echo -e "\n======================================="

# Test 9: MCP tools endpoint through proxy
echo "🧪 Test 9: MCP tools via proxy"
curl -v -H "Accept: application/json" \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
     http://localhost:9005/ 2>&1 | tee /tmp/test9_mcp_proxy.log

echo -e "\n======================================="

# Analyze results
echo "📊 ANALYSIS OF CURL TESTS"
echo "========================="

echo "🔍 Checking for Content-Type changes..."
grep -i "content-type" /tmp/test*.log | grep -v "request" || echo "No content-type headers found"

echo -e "\n🔍 Checking for SSE indicators..."
grep -i "text/event-stream\|data:\|event:" /tmp/test*.log || echo "No SSE indicators found"

echo -e "\n🔍 Checking for streaming responses..."
grep -i "transfer-encoding: chunked\|connection: keep-alive" /tmp/test*.log || echo "No streaming indicators found"

echo -e "\n🔍 Checking response status codes..."
grep -E "HTTP/[0-9]\.[0-9] [0-9]{3}" /tmp/test*.log

echo -e "\n📄 All test logs saved to /tmp/test*.log"
echo "🎯 Key files to examine:"
echo "  - /tmp/test4_chat_stream.log (most likely to show SSE conversion)"
echo "  - /tmp/test8_proxy.log (proxy interception)"
echo "  - /tmp/test9_mcp_proxy.log (MCP proxy interception)"
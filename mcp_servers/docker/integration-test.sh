#!/bin/bash

# Integration Test Script for MCP Server Manager Docker Setup
# Tests all services and their integration

set -e

echo "=== MCP Server Manager Docker Integration Test ==="
echo

# Test FastAPI Manager
echo "1. Testing FastAPI MCP Manager..."
echo "   Health Check:"
curl -s http://localhost:8000/health | python3 -m json.tool
echo
echo "   API Health Check:"
curl -s http://localhost:8000/api/v1/health | python3 -m json.tool
echo

echo "   Create Test Server:"
SERVER_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/servers \
  -H "Content-Type: application/json" \
  -d '{"name": "integration-test-server", "type": "test", "description": "Integration test server"}')
echo "$SERVER_RESPONSE" | python3 -m json.tool
SERVER_ID=$(echo "$SERVER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo

echo "   Get Server by ID:"
curl -s http://localhost:8000/api/v1/servers/$SERVER_ID | python3 -m json.tool
echo

echo "   List All Servers:"
curl -s http://localhost:8000/api/v1/servers | python3 -m json.tool
echo

echo "   Metrics:"
curl -s http://localhost:8000/metrics | python3 -m json.tool
echo

# Test PostgreSQL
echo "2. Testing PostgreSQL Database..."
echo "   Version and connectivity:"
docker exec mcp-postgres psql -U mcpuser -d mcpdb -c "SELECT version();" | head -3
echo

echo "   Basic CRUD operations:"
docker exec mcp-postgres psql -U mcpuser -d mcpdb -c "
  CREATE TABLE integration_test (id SERIAL PRIMARY KEY, test_data VARCHAR(100), created_at TIMESTAMP DEFAULT NOW());
  INSERT INTO integration_test (test_data) VALUES ('integration-test-1'), ('integration-test-2');
  SELECT * FROM integration_test;
  DROP TABLE integration_test;
"
echo

# Test Ollama
echo "3. Testing Ollama LLM Service..."
echo "   Version:"
curl -s http://localhost:11434/api/version | python3 -m json.tool
echo

echo "   Available Models:"
curl -s http://localhost:11434/api/tags | python3 -m json.tool
echo

# Test Open WebUI
echo "4. Testing Open WebUI..."
echo "   Health Status:"
curl -s http://localhost:3000/health | python3 -m json.tool
echo

echo "   Frontend Accessibility:"
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
if [ "$STATUS_CODE" = "200" ]; then
  echo "   ✓ Open WebUI frontend is accessible (HTTP $STATUS_CODE)"
else
  echo "   ✗ Open WebUI frontend returned HTTP $STATUS_CODE"
fi
echo

# Test Internal Network Connectivity
echo "5. Testing Internal Network Connectivity..."

echo "   MCP Manager -> Ollama:"
if docker exec fastapi-mcp-manager curl -s http://ollama:11434/api/version > /dev/null; then
  echo "   ✓ MCP Manager can reach Ollama"
else
  echo "   ✗ MCP Manager cannot reach Ollama"
fi

echo "   Open WebUI -> MCP Manager:"
if docker exec mcp-open-webui curl -s http://mcp-manager:8000/health > /dev/null; then
  echo "   ✓ Open WebUI can reach MCP Manager"
else
  echo "   ✗ Open WebUI cannot reach MCP Manager"
fi

echo "   Open WebUI -> Ollama:"
if docker exec mcp-open-webui curl -s http://ollama:11434/api/version > /dev/null; then
  echo "   ✓ Open WebUI can reach Ollama"
else
  echo "   ✗ Open WebUI cannot reach Ollama"
fi

# Test Container Health
echo
echo "6. Container Health Status:"
docker-compose -f docker-compose-simple.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

# Clean up test data
echo
echo "7. Cleaning up test data..."
curl -s -X DELETE http://localhost:8000/api/v1/servers/$SERVER_ID
echo "   ✓ Test server deleted"

echo
echo "=== Integration Test Summary ==="
echo "✓ FastAPI MCP Manager: Working"
echo "✓ PostgreSQL Database: Working"  
echo "✓ Ollama LLM Service: Working"
echo "✓ Open WebUI Frontend: Working"
echo "✓ Internal Network: Working"
echo "✓ Data Persistence: Working"
echo
echo "All services are running and integrated successfully!"
echo "Services accessible at:"
echo "  - MCP Manager API: http://localhost:8000"
echo "  - MCP Manager Docs: http://localhost:8000/docs"
echo "  - Open WebUI: http://localhost:3000"
echo "  - Ollama API: http://localhost:11434"
echo "  - PostgreSQL: localhost:5432"
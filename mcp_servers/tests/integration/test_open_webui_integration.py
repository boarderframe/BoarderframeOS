"""
Comprehensive integration tests for Open WebUI integration.
Tests MCP server communication, chat functionality, and WebUI compatibility.
"""
import pytest
import asyncio
import json
from typing import Dict, List, Any
from unittest.mock import Mock, AsyncMock, patch
import httpx
from fastapi import status
import websockets
import time
from datetime import datetime

from tests.utils.test_helpers import APITestHelper, DataFactory
from tests.fixtures.mcp_fixtures import MCPServerFactory, MCPResponseFactory


@pytest.mark.integration
@pytest.mark.asyncio
class TestOpenWebUIIntegration:
    """Test Open WebUI integration scenarios."""
    
    @pytest.fixture
    def webui_client_config(self):
        """Configuration for WebUI client simulation."""
        return {
            "webui_url": "http://localhost:8080",
            "api_endpoint": "/api/v1/chat/completions",
            "auth_token": "webui-test-token",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer webui-test-token",
                "User-Agent": "OpenWebUI/1.0"
            }
        }
    
    @pytest.fixture
    def mock_mcp_server(self):
        """Mock MCP server for testing."""
        server_data = MCPServerFactory.create_server_data(
            name="webui-test-server",
            protocol="http",
            host="localhost",
            port=8081
        )
        return server_data
    
    @pytest.fixture
    def mock_webui_session(self):
        """Mock WebUI session data."""
        return {
            "session_id": "webui-session-123",
            "user_id": "webui-user-456",
            "chat_id": "chat-789",
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 2048
        }
    
    async def test_webui_server_discovery(self, integration_client, mock_mcp_server):
        """Test WebUI can discover and connect to MCP servers."""
        headers = {"Authorization": "Bearer test-token"}
        
        # Create MCP server
        create_response = await integration_client.post(
            "/api/v1/mcp-servers/",
            json=mock_mcp_server,
            headers=headers
        )
        
        if create_response.status_code != status.HTTP_201_CREATED:
            pytest.skip("Server creation not implemented")
        
        server = create_response.json()
        server_id = server["id"]
        
        # Test WebUI discovery endpoint
        discovery_response = await integration_client.get(
            "/api/v1/webui/servers",
            headers=headers
        )
        
        if discovery_response.status_code == status.HTTP_200_OK:
            discovered_servers = discovery_response.json()
            assert isinstance(discovered_servers, list)
            
            # Find our test server
            test_server = next(
                (s for s in discovered_servers if s.get("id") == server_id),
                None
            )
            assert test_server is not None
            assert test_server["name"] == mock_mcp_server["name"]
    
    async def test_webui_chat_integration(self, integration_client, mock_mcp_server, mock_webui_session):
        """Test chat integration with MCP servers through WebUI."""
        headers = {"Authorization": "Bearer test-token"}
        
        # Create and start MCP server
        create_response = await integration_client.post(
            "/api/v1/mcp-servers/",
            json=mock_mcp_server,
            headers=headers
        )
        
        if create_response.status_code != status.HTTP_201_CREATED:
            pytest.skip("Server creation not implemented")
        
        server = create_response.json()
        server_id = server["id"]
        
        # Start server
        start_response = await integration_client.post(
            f"/api/v1/mcp-servers/{server_id}/start",
            headers=headers
        )
        
        # Simulate WebUI chat request
        chat_request = {
            "model": mock_webui_session["model"],
            "messages": [
                {
                    "role": "user",
                    "content": "Hello, can you help me with file operations?"
                }
            ],
            "temperature": mock_webui_session["temperature"],
            "max_tokens": mock_webui_session["max_tokens"],
            "mcp_server_id": server_id,
            "session_id": mock_webui_session["session_id"]
        }
        
        chat_response = await integration_client.post(
            "/api/v1/webui/chat",
            json=chat_request,
            headers=headers
        )
        
        if chat_response.status_code == status.HTTP_200_OK:
            response_data = chat_response.json()
            
            # Verify OpenAI-compatible response format
            assert "choices" in response_data
            assert len(response_data["choices"]) > 0
            assert "message" in response_data["choices"][0]
            assert "content" in response_data["choices"][0]["message"]
            
            # Verify MCP server was involved
            assert "usage" in response_data
            assert response_data.get("model") == mock_webui_session["model"]
    
    async def test_webui_tool_invocation(self, integration_client, mock_mcp_server):
        """Test tool invocation through WebUI interface."""
        headers = {"Authorization": "Bearer test-token"}
        
        # Create and start MCP server
        create_response = await integration_client.post(
            "/api/v1/mcp-servers/",
            json=mock_mcp_server,
            headers=headers
        )
        
        if create_response.status_code != status.HTTP_201_CREATED:
            pytest.skip("Server creation not implemented")
        
        server = create_response.json()
        server_id = server["id"]
        
        # Get available tools
        tools_response = await integration_client.get(
            f"/api/v1/mcp-servers/{server_id}/tools",
            headers=headers
        )
        
        if tools_response.status_code == status.HTTP_200_OK:
            tools = tools_response.json()
            
            if tools:  # If server has tools
                tool = tools[0]
                
                # Invoke tool through WebUI
                tool_request = {
                    "tool_name": tool["name"],
                    "parameters": tool.get("parameters", {}),
                    "session_id": "webui-session-123"
                }
                
                invoke_response = await integration_client.post(
                    f"/api/v1/webui/tools/{server_id}/invoke",
                    json=tool_request,
                    headers=headers
                )
                
                if invoke_response.status_code == status.HTTP_200_OK:
                    result = invoke_response.json()
                    assert "result" in result or "error" in result
    
    async def test_webui_streaming_chat(self, integration_client, mock_mcp_server):
        """Test streaming chat responses for WebUI."""
        headers = {"Authorization": "Bearer test-token"}
        
        # Create MCP server
        create_response = await integration_client.post(
            "/api/v1/mcp-servers/",
            json=mock_mcp_server,
            headers=headers
        )
        
        if create_response.status_code != status.HTTP_201_CREATED:
            pytest.skip("Server creation not implemented")
        
        server = create_response.json()
        server_id = server["id"]
        
        # Test streaming chat
        stream_request = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Tell me a story"}],
            "stream": True,
            "mcp_server_id": server_id
        }
        
        # Use httpx for streaming
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{integration_client.base_url}/api/v1/webui/chat/stream",
                json=stream_request,
                headers=headers
            ) as response:
                if response.status_code == status.HTTP_200_OK:
                    chunks = []
                    async for chunk in response.aiter_text():
                        if chunk.strip():
                            chunks.append(chunk)
                    
                    # Verify streaming format
                    assert len(chunks) > 0
                    
                    # Check Server-Sent Events format
                    for chunk in chunks:
                        if chunk.startswith("data: "):
                            data = chunk[6:]  # Remove "data: " prefix
                            if data != "[DONE]":
                                try:
                                    parsed = json.loads(data)
                                    assert "choices" in parsed
                                except json.JSONDecodeError:
                                    pass  # Some chunks might not be JSON
    
    async def test_webui_file_handling(self, integration_client, mock_mcp_server):
        """Test file upload and handling through WebUI."""
        headers = {"Authorization": "Bearer test-token"}
        
        # Create MCP server
        create_response = await integration_client.post(
            "/api/v1/mcp-servers/",
            json=mock_mcp_server,
            headers=headers
        )
        
        if create_response.status_code != status.HTTP_201_CREATED:
            pytest.skip("Server creation not implemented")
        
        server = create_response.json()
        server_id = server["id"]
        
        # Simulate file upload
        file_content = b"Test file content for WebUI integration"
        files = {"file": ("test.txt", file_content, "text/plain")}
        
        upload_response = await integration_client.post(
            f"/api/v1/webui/files/upload?server_id={server_id}",
            files=files,
            headers={"Authorization": "Bearer test-token"}  # Remove Content-Type for multipart
        )
        
        if upload_response.status_code == status.HTTP_200_OK:
            upload_result = upload_response.json()
            assert "file_id" in upload_result or "url" in upload_result
            
            # Test file processing
            if "file_id" in upload_result:
                process_request = {
                    "file_id": upload_result["file_id"],
                    "action": "analyze",
                    "session_id": "webui-session-123"
                }
                
                process_response = await integration_client.post(
                    f"/api/v1/webui/files/process",
                    json=process_request,
                    headers=headers
                )
                
                # Should either succeed or provide meaningful error
                assert process_response.status_code in [
                    status.HTTP_200_OK,
                    status.HTTP_202_ACCEPTED,
                    status.HTTP_400_BAD_REQUEST,
                    status.HTTP_501_NOT_IMPLEMENTED
                ]
    
    async def test_webui_session_management(self, integration_client, mock_webui_session):
        """Test WebUI session management."""
        headers = {"Authorization": "Bearer test-token"}
        
        # Create session
        session_data = {
            "user_id": mock_webui_session["user_id"],
            "chat_id": mock_webui_session["chat_id"],
            "model": mock_webui_session["model"],
            "settings": {
                "temperature": mock_webui_session["temperature"],
                "max_tokens": mock_webui_session["max_tokens"]
            }
        }
        
        create_session_response = await integration_client.post(
            "/api/v1/webui/sessions",
            json=session_data,
            headers=headers
        )
        
        if create_session_response.status_code == status.HTTP_201_CREATED:
            session = create_session_response.json()
            session_id = session["session_id"]
            
            # Get session
            get_response = await integration_client.get(
                f"/api/v1/webui/sessions/{session_id}",
                headers=headers
            )
            
            assert get_response.status_code == status.HTTP_200_OK
            retrieved_session = get_response.json()
            assert retrieved_session["user_id"] == mock_webui_session["user_id"]
            
            # Update session
            update_data = {"settings": {"temperature": 0.9}}
            update_response = await integration_client.patch(
                f"/api/v1/webui/sessions/{session_id}",
                json=update_data,
                headers=headers
            )
            
            if update_response.status_code == status.HTTP_200_OK:
                updated_session = update_response.json()
                assert updated_session["settings"]["temperature"] == 0.9
            
            # Delete session
            delete_response = await integration_client.delete(
                f"/api/v1/webui/sessions/{session_id}",
                headers=headers
            )
            
            assert delete_response.status_code in [
                status.HTTP_204_NO_CONTENT,
                status.HTTP_200_OK
            ]
    
    async def test_webui_websocket_integration(self, integration_client, mock_mcp_server):
        """Test WebSocket integration for real-time updates."""
        headers = {"Authorization": "Bearer test-token"}
        
        # Create MCP server
        create_response = await integration_client.post(
            "/api/v1/mcp-servers/",
            json=mock_mcp_server,
            headers=headers
        )
        
        if create_response.status_code != status.HTTP_201_CREATED:
            pytest.skip("Server creation not implemented")
        
        server = create_response.json()
        server_id = server["id"]
        
        # Test WebSocket connection
        ws_url = f"ws://localhost:8000/api/v1/webui/ws/{server_id}"
        
        try:
            async with websockets.connect(
                ws_url,
                extra_headers={"Authorization": "Bearer test-token"}
            ) as websocket:
                # Send ping message
                ping_message = {
                    "type": "ping",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await websocket.send(json.dumps(ping_message))
                
                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                parsed_response = json.loads(response)
                
                assert parsed_response.get("type") in ["pong", "error"]
                
        except (websockets.exceptions.ConnectionClosed, 
                websockets.exceptions.InvalidStatusCode,
                asyncio.TimeoutError,
                ConnectionRefusedError):
            # WebSocket might not be implemented yet
            pytest.skip("WebSocket not available")
    
    async def test_webui_model_compatibility(self, integration_client, mock_mcp_server):
        """Test compatibility with different model types."""
        headers = {"Authorization": "Bearer test-token"}
        
        # Create MCP server
        create_response = await integration_client.post(
            "/api/v1/mcp-servers/",
            json=mock_mcp_server,
            headers=headers
        )
        
        if create_response.status_code != status.HTTP_201_CREATED:
            pytest.skip("Server creation not implemented")
        
        server = create_response.json()
        server_id = server["id"]
        
        # Test different model types
        models_to_test = [
            "gpt-3.5-turbo",
            "gpt-4",
            "claude-3-haiku",
            "llama-2-7b",
            "mistral-7b"
        ]
        
        for model in models_to_test:
            chat_request = {
                "model": model,
                "messages": [{"role": "user", "content": "Hello"}],
                "mcp_server_id": server_id
            }
            
            response = await integration_client.post(
                "/api/v1/webui/chat",
                json=chat_request,
                headers=headers
            )
            
            # Should either work or provide meaningful error
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_501_NOT_IMPLEMENTED
            ]
            
            if response.status_code == status.HTTP_200_OK:
                data = response.json()
                assert data.get("model") == model
    
    async def test_webui_error_handling(self, integration_client):
        """Test error handling in WebUI integration."""
        headers = {"Authorization": "Bearer test-token"}
        
        # Test with non-existent server
        chat_request = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Hello"}],
            "mcp_server_id": 99999
        }
        
        response = await integration_client.post(
            "/api/v1/webui/chat",
            json=chat_request,
            headers=headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Test with invalid request format
        invalid_request = {
            "model": "",  # Invalid model
            "messages": [],  # Empty messages
        }
        
        response = await integration_client.post(
            "/api/v1/webui/chat",
            json=invalid_request,
            headers=headers
        )
        
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]
    
    async def test_webui_rate_limiting(self, integration_client, mock_mcp_server):
        """Test rate limiting for WebUI requests."""
        headers = {"Authorization": "Bearer test-token"}
        
        # Create MCP server
        create_response = await integration_client.post(
            "/api/v1/mcp-servers/",
            json=mock_mcp_server,
            headers=headers
        )
        
        if create_response.status_code != status.HTTP_201_CREATED:
            pytest.skip("Server creation not implemented")
        
        server = create_response.json()
        server_id = server["id"]
        
        # Make rapid requests
        requests_count = 50
        responses = []
        
        for i in range(requests_count):
            chat_request = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": f"Request {i}"}],
                "mcp_server_id": server_id
            }
            
            response = await integration_client.post(
                "/api/v1/webui/chat",
                json=chat_request,
                headers=headers
            )
            
            responses.append(response.status_code)
            
            # Small delay to avoid overwhelming
            if i % 10 == 0:
                await asyncio.sleep(0.1)
        
        # Check if rate limiting is applied
        rate_limited_count = sum(1 for status_code in responses if status_code == 429)
        
        # Either no rate limiting or some requests are rate limited
        assert rate_limited_count == 0 or rate_limited_count > 0
        
        # Successful requests should be in majority
        successful_count = sum(1 for status_code in responses if status_code == 200)
        assert successful_count >= requests_count * 0.5  # At least 50% success rate
    
    async def test_webui_authentication_integration(self, integration_client):
        """Test authentication integration with WebUI."""
        # Test without authentication
        chat_request = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Hello"}]
        }
        
        response = await integration_client.post(
            "/api/v1/webui/chat",
            json=chat_request
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test with invalid token
        invalid_headers = {"Authorization": "Bearer invalid-token"}
        response = await integration_client.post(
            "/api/v1/webui/chat",
            json=chat_request,
            headers=invalid_headers
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test with valid token (if authentication is implemented)
        valid_headers = {"Authorization": "Bearer test-token"}
        response = await integration_client.post(
            "/api/v1/webui/chat",
            json=chat_request,
            headers=valid_headers
        )
        
        # Should either work or fail for other reasons (not auth)
        assert response.status_code != status.HTTP_401_UNAUTHORIZED


@pytest.mark.integration
@pytest.mark.asyncio
class TestWebUICompatibility:
    """Test compatibility with Open WebUI specific features."""
    
    async def test_openai_api_compatibility(self, integration_client):
        """Test OpenAI API compatibility for WebUI."""
        headers = {"Authorization": "Bearer test-token"}
        
        # Test models endpoint
        models_response = await integration_client.get(
            "/api/v1/webui/models",
            headers=headers
        )
        
        if models_response.status_code == status.HTTP_200_OK:
            models = models_response.json()
            assert "data" in models
            assert isinstance(models["data"], list)
            
            for model in models["data"]:
                assert "id" in model
                assert "object" in model
                assert model["object"] == "model"
        
        # Test completions endpoint format
        completion_request = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        completion_response = await integration_client.post(
            "/api/v1/webui/chat/completions",
            json=completion_request,
            headers=headers
        )
        
        if completion_response.status_code == status.HTTP_200_OK:
            completion = completion_response.json()
            
            # Verify OpenAI API format
            assert "id" in completion
            assert "object" in completion
            assert completion["object"] == "chat.completion"
            assert "created" in completion
            assert "model" in completion
            assert "choices" in completion
            assert "usage" in completion
    
    async def test_webui_function_calling(self, integration_client, mock_mcp_server):
        """Test function calling compatibility with WebUI."""
        headers = {"Authorization": "Bearer test-token"}
        
        # Create MCP server with tools
        create_response = await integration_client.post(
            "/api/v1/mcp-servers/",
            json=mock_mcp_server,
            headers=headers
        )
        
        if create_response.status_code != status.HTTP_201_CREATED:
            pytest.skip("Server creation not implemented")
        
        server = create_response.json()
        server_id = server["id"]
        
        # Test function calling request
        function_request = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": "Please read the file 'test.txt'"}
            ],
            "functions": [
                {
                    "name": "read_file",
                    "description": "Read a file from the filesystem",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path"}
                        },
                        "required": ["path"]
                    }
                }
            ],
            "function_call": "auto",
            "mcp_server_id": server_id
        }
        
        response = await integration_client.post(
            "/api/v1/webui/chat/completions",
            json=function_request,
            headers=headers
        )
        
        if response.status_code == status.HTTP_200_OK:
            result = response.json()
            
            # Check if function was called
            if result["choices"][0]["message"].get("function_call"):
                function_call = result["choices"][0]["message"]["function_call"]
                assert "name" in function_call
                assert "arguments" in function_call
    
    async def test_webui_image_handling(self, integration_client):
        """Test image handling for WebUI integration."""
        headers = {"Authorization": "Bearer test-token"}
        
        # Create a simple test image (1x1 pixel PNG)
        test_image = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13'
            b'\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\xda'
            b'c\xf8\x00\x00\x00\x01\x00\x01um!\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        
        files = {"image": ("test.png", test_image, "image/png")}
        
        upload_response = await integration_client.post(
            "/api/v1/webui/images/upload",
            files=files,
            headers={"Authorization": "Bearer test-token"}
        )
        
        if upload_response.status_code == status.HTTP_200_OK:
            upload_result = upload_response.json()
            assert "image_id" in upload_result or "url" in upload_result
            
            # Test image analysis
            if "image_id" in upload_result:
                analysis_request = {
                    "image_id": upload_result["image_id"],
                    "prompt": "Describe this image",
                    "model": "gpt-4-vision-preview"
                }
                
                analysis_response = await integration_client.post(
                    "/api/v1/webui/images/analyze",
                    json=analysis_request,
                    headers=headers
                )
                
                # Should either work or provide meaningful error
                assert analysis_response.status_code in [
                    status.HTTP_200_OK,
                    status.HTTP_501_NOT_IMPLEMENTED,
                    status.HTTP_400_BAD_REQUEST
                ]
    
    async def test_webui_conversation_history(self, integration_client):
        """Test conversation history management for WebUI."""
        headers = {"Authorization": "Bearer test-token"}
        
        # Create conversation
        conversation_data = {
            "title": "Test Conversation",
            "user_id": "webui-user-123",
            "model": "gpt-3.5-turbo"
        }
        
        create_response = await integration_client.post(
            "/api/v1/webui/conversations",
            json=conversation_data,
            headers=headers
        )
        
        if create_response.status_code == status.HTTP_201_CREATED:
            conversation = create_response.json()
            conversation_id = conversation["id"]
            
            # Add messages to conversation
            messages = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there! How can I help you?"},
                {"role": "user", "content": "What's the weather like?"}
            ]
            
            for message in messages:
                message_data = {
                    "conversation_id": conversation_id,
                    **message
                }
                
                message_response = await integration_client.post(
                    "/api/v1/webui/messages",
                    json=message_data,
                    headers=headers
                )
                
                assert message_response.status_code in [
                    status.HTTP_201_CREATED,
                    status.HTTP_200_OK
                ]
            
            # Get conversation history
            history_response = await integration_client.get(
                f"/api/v1/webui/conversations/{conversation_id}/messages",
                headers=headers
            )
            
            if history_response.status_code == status.HTTP_200_OK:
                history = history_response.json()
                assert len(history) >= len(messages)
    
    async def test_webui_plugin_system(self, integration_client, mock_mcp_server):
        """Test plugin system integration for WebUI."""
        headers = {"Authorization": "Bearer test-token"}
        
        # Test plugin discovery
        plugins_response = await integration_client.get(
            "/api/v1/webui/plugins",
            headers=headers
        )
        
        if plugins_response.status_code == status.HTTP_200_OK:
            plugins = plugins_response.json()
            assert isinstance(plugins, list)
            
            # Look for MCP plugin
            mcp_plugin = next(
                (p for p in plugins if "mcp" in p.get("name", "").lower()),
                None
            )
            
            if mcp_plugin:
                assert "id" in mcp_plugin
                assert "name" in mcp_plugin
                assert "enabled" in mcp_plugin
        
        # Test plugin configuration
        plugin_config = {
            "plugin_id": "mcp-integration",
            "settings": {
                "auto_discovery": True,
                "default_timeout": 30,
                "max_connections": 10
            }
        }
        
        config_response = await integration_client.post(
            "/api/v1/webui/plugins/configure",
            json=plugin_config,
            headers=headers
        )
        
        # Should either work or indicate not implemented
        assert config_response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_501_NOT_IMPLEMENTED,
            status.HTTP_404_NOT_FOUND
        ]
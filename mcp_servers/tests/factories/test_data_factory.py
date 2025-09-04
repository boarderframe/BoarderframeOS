"""
Comprehensive test data factories and fixtures for consistent test data generation.
Provides factories for all data types used in testing across the application.
"""
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import json
from faker import Faker

# Initialize Faker for realistic data generation
fake = Faker()


class ServerStatus(Enum):
    """Server status options."""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"


class Protocol(Enum):
    """Protocol options."""
    STDIO = "stdio"
    HTTP = "http"
    HTTPS = "https"
    WEBSOCKET = "websocket"


@dataclass
class ServerConfig:
    """Server configuration data."""
    host: str
    port: int
    timeout: int = 30
    retries: int = 3
    auto_start: bool = True
    max_connections: int = 10
    environment: Dict[str, str] = None
    ssl_enabled: bool = False
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None
    
    def __post_init__(self):
        if self.environment is None:
            self.environment = {}


@dataclass
class ServerMetrics:
    """Server metrics data."""
    cpu_usage: float
    memory_usage: float
    connections: int
    requests_per_second: float
    error_rate: float
    uptime_seconds: int
    response_time_avg: float
    response_time_p95: float
    response_time_p99: float
    bytes_sent: int = 0
    bytes_received: int = 0
    
    @classmethod
    def realistic(cls) -> 'ServerMetrics':
        """Generate realistic metrics."""
        return cls(
            cpu_usage=random.uniform(5.0, 80.0),
            memory_usage=random.uniform(10.0, 90.0),
            connections=random.randint(0, 50),
            requests_per_second=random.uniform(0.1, 100.0),
            error_rate=random.uniform(0.0, 0.05),
            uptime_seconds=random.randint(300, 86400 * 30),  # 5 min to 30 days
            response_time_avg=random.uniform(50.0, 500.0),
            response_time_p95=random.uniform(100.0, 1000.0),
            response_time_p99=random.uniform(200.0, 2000.0),
            bytes_sent=random.randint(1000, 10000000),
            bytes_received=random.randint(500, 5000000)
        )


@dataclass
class UserData:
    """User data for authentication testing."""
    email: str
    username: str
    password: str
    first_name: str = ""
    last_name: str = ""
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = True
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        if not self.first_name:
            self.first_name = fake.first_name()
        if not self.last_name:
            self.last_name = fake.last_name()
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.utcnow().isoformat()


class TestDataFactory:
    """Main factory for generating test data."""
    
    @staticmethod
    def random_string(length: int = 10, chars: str = string.ascii_lowercase) -> str:
        """Generate random string."""
        return ''.join(random.choices(chars, k=length))
    
    @staticmethod
    def random_email(domain: str = "example.com") -> str:
        """Generate random email address."""
        username = TestDataFactory.random_string(8)
        return f"{username}@{domain}"
    
    @staticmethod
    def random_port(min_port: int = 8000, max_port: int = 9000) -> int:
        """Generate random port number."""
        return random.randint(min_port, max_port)
    
    @staticmethod
    def random_password(length: int = 12) -> str:
        """Generate random secure password."""
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(random.choices(chars, k=length))
        # Ensure password meets requirements
        if not any(c.isupper() for c in password):
            password = password[:-1] + random.choice(string.ascii_uppercase)
        if not any(c.islower() for c in password):
            password = password[:-2] + random.choice(string.ascii_lowercase) + password[-1]
        if not any(c.isdigit() for c in password):
            password = password[:-3] + random.choice(string.digits) + password[-2:]
        return password
    
    @staticmethod
    def create_server_data(**overrides) -> Dict[str, Any]:
        """Create MCP server data with optional overrides."""
        base_data = {
            "name": f"test-server-{TestDataFactory.random_string(6)}",
            "description": fake.text(max_nb_chars=100),
            "host": "localhost",
            "port": TestDataFactory.random_port(),
            "protocol": random.choice(list(Protocol)).value,
            "command": random.choice([
                "/usr/bin/python",
                "/usr/bin/node",
                "/usr/bin/java",
                "/bin/bash"
            ]),
            "args": [
                "-m", 
                f"server_{TestDataFactory.random_string(4)}"
            ],
            "env": {
                "NODE_ENV": "test",
                "DEBUG": "true",
                "LOG_LEVEL": random.choice(["debug", "info", "warn", "error"])
            },
            "config": {
                "timeout": random.randint(30, 120),
                "retries": random.randint(1, 5),
                "auto_start": random.choice([True, False]),
                "max_connections": random.randint(5, 50)
            },
            "status": random.choice(list(ServerStatus)).value,
            "created_at": fake.date_time_between(start_date="-30d").isoformat(),
            "updated_at": fake.date_time_between(start_date="-1d").isoformat(),
            "last_health_check": fake.date_time_between(start_date="-1h").isoformat()
        }
        
        base_data.update(overrides)
        return base_data
    
    @staticmethod
    def create_user_data(**overrides) -> Dict[str, Any]:
        """Create user data with optional overrides."""
        user_data = UserData(
            email=TestDataFactory.random_email(),
            username=TestDataFactory.random_string(8),
            password=TestDataFactory.random_password()
        )
        
        user_dict = asdict(user_data)
        user_dict.update(overrides)
        return user_dict
    
    @staticmethod
    def create_admin_user_data(**overrides) -> Dict[str, Any]:
        """Create admin user data."""
        admin_overrides = {
            "is_superuser": True,
            "username": f"admin_{TestDataFactory.random_string(6)}",
            "email": f"admin_{TestDataFactory.random_string(6)}@example.com"
        }
        admin_overrides.update(overrides)
        return TestDataFactory.create_user_data(**admin_overrides)
    
    @staticmethod
    def create_multiple_servers(count: int, **common_overrides) -> List[Dict[str, Any]]:
        """Create multiple server configurations."""
        servers = []
        for i in range(count):
            server_overrides = {
                "name": f"multi-server-{i+1}",
                "port": 8000 + i,
                **common_overrides
            }
            servers.append(TestDataFactory.create_server_data(**server_overrides))
        return servers
    
    @staticmethod
    def create_server_with_metrics(**overrides) -> Dict[str, Any]:
        """Create server data with realistic metrics."""
        server_data = TestDataFactory.create_server_data(**overrides)
        server_data["metrics"] = asdict(ServerMetrics.realistic())
        return server_data
    
    @staticmethod
    def create_conversation_data(**overrides) -> Dict[str, Any]:
        """Create conversation data for WebUI testing."""
        base_data = {
            "id": str(uuid.uuid4()),
            "title": fake.sentence(nb_words=4),
            "user_id": str(uuid.uuid4()),
            "model": random.choice([
                "gpt-3.5-turbo",
                "gpt-4",
                "claude-3-haiku",
                "llama-2-7b"
            ]),
            "created_at": fake.date_time_between(start_date="-7d").isoformat(),
            "updated_at": fake.date_time_between(start_date="-1d").isoformat(),
            "message_count": random.randint(1, 50),
            "is_archived": random.choice([True, False]),
            "tags": fake.words(nb=random.randint(0, 5))
        }
        
        base_data.update(overrides)
        return base_data
    
    @staticmethod
    def create_chat_message(**overrides) -> Dict[str, Any]:
        """Create chat message data."""
        base_data = {
            "id": str(uuid.uuid4()),
            "conversation_id": str(uuid.uuid4()),
            "role": random.choice(["user", "assistant", "system"]),
            "content": fake.text(max_nb_chars=500),
            "timestamp": fake.date_time_between(start_date="-1d").isoformat(),
            "token_count": random.randint(10, 500),
            "model_used": random.choice(["gpt-3.5-turbo", "gpt-4"]),
            "metadata": {
                "source": "webui",
                "session_id": str(uuid.uuid4()),
                "response_time_ms": random.randint(100, 2000)
            }
        }
        
        base_data.update(overrides)
        return base_data
    
    @staticmethod
    def create_tool_definition(**overrides) -> Dict[str, Any]:
        """Create MCP tool definition."""
        tool_names = [
            "file_reader", "web_scraper", "calculator", "database_query",
            "image_generator", "text_analyzer", "code_executor", "api_caller"
        ]
        
        base_data = {
            "name": random.choice(tool_names),
            "description": fake.text(max_nb_chars=200),
            "version": f"{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "Input parameter"
                    },
                    "options": {
                        "type": "object",
                        "description": "Optional configuration"
                    }
                },
                "required": ["input"]
            },
            "examples": [
                {
                    "input": {"input": "example value"},
                    "output": {"result": "example output"}
                }
            ],
            "tags": fake.words(nb=random.randint(1, 4)),
            "author": fake.name(),
            "license": random.choice(["MIT", "Apache-2.0", "GPL-3.0", "BSD-3-Clause"])
        }
        
        base_data.update(overrides)
        return base_data
    
    @staticmethod
    def create_resource_definition(**overrides) -> Dict[str, Any]:
        """Create MCP resource definition."""
        resource_types = [
            "file", "database", "api", "document", "image", "config"
        ]
        
        base_data = {
            "name": f"{random.choice(resource_types)}_{TestDataFactory.random_string(6)}",
            "type": random.choice([
                "text/plain", "application/json", "text/csv",
                "image/png", "application/pdf", "text/html"
            ]),
            "description": fake.text(max_nb_chars=150),
            "uri": f"file:///path/to/{TestDataFactory.random_string(8)}.{random.choice(['txt', 'json', 'csv'])}",
            "size": random.randint(1024, 10485760),  # 1KB to 10MB
            "created_at": fake.date_time_between(start_date="-30d").isoformat(),
            "modified_at": fake.date_time_between(start_date="-1d").isoformat(),
            "permissions": {
                "read": True,
                "write": random.choice([True, False]),
                "execute": random.choice([True, False])
            },
            "metadata": {
                "encoding": "utf-8",
                "checksum": TestDataFactory.random_string(32, string.hexdigits.lower()),
                "tags": fake.words(nb=random.randint(0, 3))
            }
        }
        
        base_data.update(overrides)
        return base_data
    
    @staticmethod
    def create_api_request_data(**overrides) -> Dict[str, Any]:
        """Create API request data for testing."""
        methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        
        base_data = {
            "method": random.choice(methods),
            "url": f"/api/v1/{TestDataFactory.random_string(8)}",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {TestDataFactory.random_string(32)}",
                "User-Agent": f"TestClient/{random.randint(1, 3)}.{random.randint(0, 9)}"
            },
            "query_params": {
                "page": random.randint(1, 10),
                "limit": random.choice([10, 20, 50, 100]),
                "sort": random.choice(["name", "created_at", "updated_at"])
            },
            "body": {
                "data": TestDataFactory.random_string(100),
                "timestamp": datetime.utcnow().isoformat()
            },
            "response_time_ms": random.randint(50, 2000),
            "status_code": random.choice([200, 201, 400, 401, 403, 404, 500])
        }
        
        base_data.update(overrides)
        return base_data
    
    @staticmethod
    def create_error_data(error_type: str = "generic", **overrides) -> Dict[str, Any]:
        """Create error data for testing error handling."""
        error_templates = {
            "validation": {
                "code": "VALIDATION_ERROR",
                "message": "Validation failed",
                "details": {
                    "field": fake.word(),
                    "value": TestDataFactory.random_string(8),
                    "constraint": "required"
                }
            },
            "authentication": {
                "code": "AUTH_ERROR",
                "message": "Authentication failed",
                "details": {
                    "reason": "invalid_token",
                    "token": TestDataFactory.random_string(16)
                }
            },
            "authorization": {
                "code": "AUTHORIZATION_ERROR",
                "message": "Access denied",
                "details": {
                    "required_permission": "admin",
                    "user_role": "user"
                }
            },
            "not_found": {
                "code": "NOT_FOUND",
                "message": "Resource not found",
                "details": {
                    "resource_type": "server",
                    "resource_id": random.randint(1, 1000)
                }
            },
            "server_error": {
                "code": "INTERNAL_ERROR",
                "message": "Internal server error",
                "details": {
                    "error_id": str(uuid.uuid4()),
                    "timestamp": datetime.utcnow().isoformat()
                }
            },
            "generic": {
                "code": "ERROR",
                "message": fake.sentence(),
                "details": {}
            }
        }
        
        base_data = error_templates.get(error_type, error_templates["generic"]).copy()
        base_data.update(overrides)
        return base_data
    
    @staticmethod
    def create_performance_data(**overrides) -> Dict[str, Any]:
        """Create performance test data."""
        base_data = {
            "test_name": f"perf_test_{TestDataFactory.random_string(8)}",
            "start_time": fake.date_time_between(start_date="-1h").isoformat(),
            "end_time": fake.date_time_between(start_date="-30m").isoformat(),
            "duration_ms": random.randint(1000, 60000),
            "requests_total": random.randint(100, 10000),
            "requests_successful": None,  # Will be calculated
            "requests_failed": None,      # Will be calculated
            "avg_response_time": random.uniform(50.0, 500.0),
            "min_response_time": random.uniform(10.0, 50.0),
            "max_response_time": random.uniform(500.0, 2000.0),
            "percentiles": {
                "p50": random.uniform(50.0, 200.0),
                "p90": random.uniform(200.0, 500.0),
                "p95": random.uniform(300.0, 800.0),
                "p99": random.uniform(500.0, 1500.0)
            },
            "throughput_rps": random.uniform(10.0, 100.0),
            "error_rate": random.uniform(0.0, 0.05),
            "memory_usage_mb": random.uniform(100.0, 1000.0),
            "cpu_usage_percent": random.uniform(20.0, 80.0)
        }
        
        # Calculate success/failure counts
        if base_data["requests_successful"] is None:
            failed = int(base_data["requests_total"] * base_data["error_rate"])
            base_data["requests_failed"] = failed
            base_data["requests_successful"] = base_data["requests_total"] - failed
        
        base_data.update(overrides)
        return base_data


class ScenarioFactory:
    """Factory for creating test scenarios and data sets."""
    
    @staticmethod
    def create_load_test_scenario(user_count: int = 10) -> Dict[str, Any]:
        """Create a load test scenario with multiple users and servers."""
        users = [TestDataFactory.create_user_data() for _ in range(user_count)]
        servers = TestDataFactory.create_multiple_servers(user_count * 2)
        
        return {
            "name": f"load_test_{user_count}_users",
            "description": f"Load test scenario with {user_count} users",
            "users": users,
            "servers": servers,
            "duration_minutes": 10,
            "ramp_up_seconds": 30,
            "expected_rps": user_count * 2,
            "max_response_time_ms": 1000
        }
    
    @staticmethod
    def create_security_test_data() -> Dict[str, Any]:
        """Create data for security testing."""
        return {
            "sql_injection_payloads": [
                "'; DROP TABLE users; --",
                "' OR '1'='1",
                "1; DELETE FROM servers; --",
                "' UNION SELECT * FROM users --"
            ],
            "xss_payloads": [
                "<script>alert('xss')</script>",
                "javascript:alert('xss')",
                "<img src=x onerror=alert('xss')>",
                "';alert('xss');//"
            ],
            "invalid_tokens": [
                "",
                "invalid-token",
                "Bearer ",
                "Bearer invalid",
                TestDataFactory.random_string(100)
            ],
            "malicious_file_names": [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32\\config\\sam",
                "/etc/passwd",
                "malware.exe",
                "script.php"
            ]
        }
    
    @staticmethod
    def create_integration_test_data() -> Dict[str, Any]:
        """Create comprehensive data for integration tests."""
        return {
            "servers": TestDataFactory.create_multiple_servers(5),
            "users": [
                TestDataFactory.create_user_data(),
                TestDataFactory.create_admin_user_data()
            ],
            "conversations": [
                TestDataFactory.create_conversation_data() for _ in range(3)
            ],
            "tools": [
                TestDataFactory.create_tool_definition() for _ in range(10)
            ],
            "resources": [
                TestDataFactory.create_resource_definition() for _ in range(8)
            ]
        }


# Convenience functions for common test data
def server_data(**overrides) -> Dict[str, Any]:
    """Shorthand for creating server data."""
    return TestDataFactory.create_server_data(**overrides)


def user_data(**overrides) -> Dict[str, Any]:
    """Shorthand for creating user data."""
    return TestDataFactory.create_user_data(**overrides)


def admin_user(**overrides) -> Dict[str, Any]:
    """Shorthand for creating admin user data."""
    return TestDataFactory.create_admin_user_data(**overrides)


def multiple_servers(count: int, **overrides) -> List[Dict[str, Any]]:
    """Shorthand for creating multiple servers."""
    return TestDataFactory.create_multiple_servers(count, **overrides)


def error_data(error_type: str = "generic", **overrides) -> Dict[str, Any]:
    """Shorthand for creating error data."""
    return TestDataFactory.create_error_data(error_type, **overrides)


def api_request(**overrides) -> Dict[str, Any]:
    """Shorthand for creating API request data."""
    return TestDataFactory.create_api_request_data(**overrides)


# Export all factory functions for easy import
__all__ = [
    'TestDataFactory', 'ScenarioFactory', 'ServerStatus', 'Protocol',
    'ServerConfig', 'ServerMetrics', 'UserData',
    'server_data', 'user_data', 'admin_user', 'multiple_servers',
    'error_data', 'api_request'
]
"""
Locust load testing script for MCP Server Manager.
Simulates realistic user behavior and API usage patterns.
"""
import json
import random
import time
from locust import HttpUser, task, between, events
from locust.exception import RescheduleTask


class MCPServerManagerUser(HttpUser):
    """Simulates a user of the MCP Server Manager system."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Called when a user starts - performs login/setup."""
        self.auth_token = None
        self.user_servers = []
        self.login()
    
    def login(self):
        """Authenticate user and get token."""
        login_data = {
            "username": f"loadtest_user_{random.randint(1000, 9999)}@example.com",
            "password": "LoadTestPassword123!"
        }
        
        # Try to register first (might fail if user exists)
        self.client.post("/api/v1/auth/register", json={
            **login_data,
            "email": login_data["username"]
        })
        
        # Login
        response = self.client.post("/api/v1/auth/login", json=login_data)
        
        if response.status_code == 200:
            self.auth_token = response.json().get("access_token")
        else:
            # Use a default test token if auth is not fully implemented
            self.auth_token = "loadtest-token"
    
    @property
    def auth_headers(self):
        """Get authentication headers."""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    @task(3)
    def health_check(self):
        """Check system health - most frequent operation."""
        self.client.get("/api/v1/health")
    
    @task(5)
    def list_servers(self):
        """List MCP servers - common operation."""
        response = self.client.get("/api/v1/mcp-servers/", headers=self.auth_headers)
        
        if response.status_code == 200:
            servers = response.json()
            # Update local server list for other operations
            self.user_servers = [s for s in servers if isinstance(s, dict) and 'id' in s]
    
    @task(2)
    def create_server(self):
        """Create a new MCP server - less frequent but important."""
        server_data = {
            "name": f"loadtest_server_{random.randint(1000, 9999)}",
            "description": "Server created by load test",
            "host": "localhost",
            "port": random.randint(8000, 9000),
            "protocol": random.choice(["stdio", "http"]),
            "command": "/usr/bin/python",
            "args": ["-m", "test_server"],
            "env": {"LOAD_TEST": "true"},
            "config": {
                "timeout": random.randint(30, 120),
                "retries": random.randint(1, 5)
            }
        }
        
        response = self.client.post(
            "/api/v1/mcp-servers/",
            json=server_data,
            headers=self.auth_headers
        )
        
        if response.status_code == 201:
            server = response.json()
            self.user_servers.append(server)
    
    @task(1)
    def update_server(self):
        """Update an existing server - occasional operation."""
        if not self.user_servers:
            raise RescheduleTask()
        
        server = random.choice(self.user_servers)
        server_id = server.get("id")
        
        if not server_id:
            raise RescheduleTask()
        
        update_data = {
            "description": f"Updated at {time.time()}",
            "config": {
                "timeout": random.randint(30, 120),
                "retries": random.randint(1, 5)
            }
        }
        
        self.client.put(
            f"/api/v1/mcp-servers/{server_id}",
            json=update_data,
            headers=self.auth_headers
        )
    
    @task(1)
    def get_server_details(self):
        """Get details of a specific server."""
        if not self.user_servers:
            raise RescheduleTask()
        
        server = random.choice(self.user_servers)
        server_id = server.get("id")
        
        if not server_id:
            raise RescheduleTask()
        
        self.client.get(
            f"/api/v1/mcp-servers/{server_id}",
            headers=self.auth_headers
        )
    
    @task(1)
    def server_actions(self):
        """Perform server actions (start/stop/restart)."""
        if not self.user_servers:
            raise RescheduleTask()
        
        server = random.choice(self.user_servers)
        server_id = server.get("id")
        
        if not server_id:
            raise RescheduleTask()
        
        action = random.choice(["start", "stop", "restart"])
        
        self.client.post(
            f"/api/v1/mcp-servers/{server_id}/{action}",
            headers=self.auth_headers
        )
    
    @task(1)
    def search_servers(self):
        """Search servers with various filters."""
        search_params = {
            "search": random.choice([
                "loadtest",
                "server",
                "test",
                "",  # Empty search
            ]),
            "status": random.choice([
                "running",
                "stopped",
                "active",
                "",  # No filter
            ]),
            "limit": random.choice([10, 20, 50])
        }
        
        # Remove empty parameters
        params = {k: v for k, v in search_params.items() if v}
        
        self.client.get(
            "/api/v1/mcp-servers/",
            params=params,
            headers=self.auth_headers
        )
    
    @task(1)
    def get_server_metrics(self):
        """Get server metrics - monitoring operation."""
        if not self.user_servers:
            raise RescheduleTask()
        
        server = random.choice(self.user_servers)
        server_id = server.get("id")
        
        if not server_id:
            raise RescheduleTask()
        
        self.client.get(
            f"/api/v1/mcp-servers/{server_id}/metrics",
            headers=self.auth_headers
        )
    
    @task(1)
    def delete_server(self):
        """Delete a server - cleanup operation."""
        if not self.user_servers:
            raise RescheduleTask()
        
        # Only delete occasionally and if we have multiple servers
        if len(self.user_servers) < 2 or random.random() > 0.3:
            raise RescheduleTask()
        
        server = random.choice(self.user_servers)
        server_id = server.get("id")
        
        if not server_id:
            raise RescheduleTask()
        
        response = self.client.delete(
            f"/api/v1/mcp-servers/{server_id}",
            headers=self.auth_headers
        )
        
        if response.status_code in [200, 204]:
            # Remove from local list
            self.user_servers = [s for s in self.user_servers if s.get("id") != server_id]


class AdminUser(HttpUser):
    """Simulates an admin user with additional privileges."""
    
    wait_time = between(2, 5)  # Admins are less frequent but more thorough
    weight = 1  # Lower weight means fewer admin users
    
    def on_start(self):
        """Admin setup."""
        self.auth_token = "admin-loadtest-token"
    
    @property
    def auth_headers(self):
        """Get admin authentication headers."""
        return {"Authorization": f"Bearer {self.auth_token}"}
    
    @task(3)
    def admin_dashboard(self):
        """Access admin dashboard."""
        self.client.get("/api/v1/admin/dashboard", headers=self.auth_headers)
    
    @task(2)
    def list_all_users(self):
        """List all users - admin operation."""
        self.client.get("/api/v1/admin/users", headers=self.auth_headers)
    
    @task(2)
    def system_metrics(self):
        """Get system-wide metrics."""
        self.client.get("/api/v1/admin/metrics", headers=self.auth_headers)
    
    @task(1)
    def system_settings(self):
        """Get system settings."""
        self.client.get("/api/v1/admin/settings", headers=self.auth_headers)
    
    @task(1)
    def audit_logs(self):
        """Access audit logs."""
        self.client.get("/api/v1/admin/audit-logs", headers=self.auth_headers)


class WebUIIntegrationUser(HttpUser):
    """Simulates Open WebUI integration usage."""
    
    wait_time = between(1, 4)
    weight = 2  # Some users use WebUI integration
    
    def on_start(self):
        """WebUI user setup."""
        self.auth_token = "webui-loadtest-token"
        self.session_id = f"webui_session_{random.randint(1000, 9999)}"
    
    @property
    def auth_headers(self):
        """Get WebUI authentication headers."""
        return {
            "Authorization": f"Bearer {self.auth_token}",
            "User-Agent": "OpenWebUI/1.0"
        }
    
    @task(5)
    def chat_completion(self):
        """WebUI chat completion request."""
        chat_request = {
            "model": random.choice([
                "gpt-3.5-turbo",
                "gpt-4",
                "claude-3-haiku"
            ]),
            "messages": [
                {
                    "role": "user",
                    "content": random.choice([
                        "Hello, how are you?",
                        "What's the weather like?",
                        "Can you help me with a task?",
                        "Tell me about MCP servers",
                        "How do I configure a server?"
                    ])
                }
            ],
            "temperature": random.uniform(0.1, 1.0),
            "max_tokens": random.randint(100, 1000),
            "session_id": self.session_id
        }
        
        self.client.post(
            "/api/v1/webui/chat",
            json=chat_request,
            headers=self.auth_headers
        )
    
    @task(2)
    def list_models(self):
        """List available models for WebUI."""
        self.client.get("/api/v1/webui/models", headers=self.auth_headers)
    
    @task(1)
    def streaming_chat(self):
        """WebUI streaming chat request."""
        stream_request = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": "Tell me a story"}
            ],
            "stream": True,
            "session_id": self.session_id
        }
        
        with self.client.post(
            "/api/v1/webui/chat/stream",
            json=stream_request,
            headers=self.auth_headers,
            stream=True,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                # Consume stream
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        pass
                response.success()
            else:
                response.failure(f"Streaming failed: {response.status_code}")
    
    @task(1)
    def tool_invocation(self):
        """WebUI tool invocation."""
        tool_request = {
            "tool_name": "file_reader",
            "parameters": {"path": "/test/file.txt"},
            "session_id": self.session_id
        }
        
        self.client.post(
            "/api/v1/webui/tools/1/invoke",
            json=tool_request,
            headers=self.auth_headers
        )


# Event handlers for custom metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    print("Load test starting...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops."""
    print("Load test completed.")
    
    # Print summary statistics
    stats = environment.stats
    print(f"\nLoad Test Summary:")
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"Max response time: {stats.total.max_response_time:.2f}ms")
    print(f"Requests per second: {stats.total.current_rps:.2f}")
    print(f"Failure rate: {stats.total.fail_ratio:.2%}")


# Custom scenarios for specific load patterns
class BurstTrafficUser(HttpUser):
    """Simulates burst traffic patterns."""
    
    wait_time = between(0.1, 0.5)  # Very short wait times
    weight = 1
    
    def on_start(self):
        self.auth_token = "burst-loadtest-token"
    
    @task(10)
    def rapid_health_checks(self):
        """Rapid fire health checks."""
        self.client.get("/api/v1/health")
    
    @task(5)
    def rapid_server_list(self):
        """Rapid server listing."""
        self.client.get(
            "/api/v1/mcp-servers/",
            headers={"Authorization": f"Bearer {self.auth_token}"}
        )


class BackgroundTaskUser(HttpUser):
    """Simulates background/monitoring tasks."""
    
    wait_time = between(10, 30)  # Longer intervals
    weight = 1
    
    def on_start(self):
        self.auth_token = "monitor-loadtest-token"
    
    @task(1)
    def system_monitoring(self):
        """System monitoring calls."""
        endpoints = [
            "/api/v1/health",
            "/api/v1/metrics",
            "/api/v1/status"
        ]
        
        for endpoint in endpoints:
            self.client.get(
                endpoint,
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            time.sleep(1)  # Brief pause between monitoring calls


# Load test configuration examples:
#
# Basic load test:
# locust -f locustfile.py --host=http://localhost:8000 --users=10 --spawn-rate=2 --run-time=2m
#
# Stress test:
# locust -f locustfile.py --host=http://localhost:8000 --users=100 --spawn-rate=10 --run-time=5m
#
# Spike test:
# locust -f locustfile.py --host=http://localhost:8000 --users=200 --spawn-rate=50 --run-time=1m
#
# Endurance test:
# locust -f locustfile.py --host=http://localhost:8000 --users=20 --spawn-rate=2 --run-time=30m
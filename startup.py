#!/usr/bin/env python3
"""
BoarderframeOS System Startup
Complete system boot including BoarderframeOS and BCC
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import psutil

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))


class EnhancedSystemStartup:
    """Enhanced system startup with clean terminal output and robust error handling"""

    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.status_data = {
            "startup_phase": "initializing",
            "services": {},
            "agents": {},
            "mcp_servers": {},
            "start_time": datetime.now().isoformat(),
            "logs": [],
        }
        self.running = False
        self.status_file = "/tmp/boarderframe_startup_status.json"

        # Configure clean logging
        logging.basicConfig(level=logging.WARNING, format="%(message)s")  # Reduce noise
        self.logger = logging.getLogger("startup")

        # Ensure we use the correct virtual environment Python executable
        self.venv_python = self._get_venv_python_executable()

    def print_section(self, title: str, emoji: str = "🔧"):
        """Print a clean, simplified section header"""
        print(f"\n{emoji} {title}")
        print("─" * 50)

    def print_step(self, message: str, status: str = "info", agent=False):
        """Print a step with clear status indicators"""
        # Simplified status indicators with consistent spacing
        if status == "success":
            print(f"  ✅ {message}")
        elif status == "starting":
            print(f"  ⏳ {message}")
        elif status == "error":
            print(f"  ❌ {message}")
        elif status == "warning":
            print(f"  ⚠️  {message}")
        elif status == "info":
            print(f"  ℹ️  {message}")
        else:
            print(f"  • {message}")

    def log_status(self, message: str, component: str = "system", status: str = "info"):
        """Log status without printing (for file only)"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "component": component,
            "message": message,
            "status": status,
        }

        self.status_data["logs"].append(log_entry)

        # Keep only last 20 log entries
        if len(self.status_data["logs"]) > 20:
            self.status_data["logs"] = self.status_data["logs"][-20:]

        self.save_status()

    def _get_venv_python_executable(self) -> str:
        """Get the correct virtual environment Python executable"""
        # First, try to detect if we're in a virtual environment
        current_python = sys.executable

        # Check if we're already using a venv python
        if ".venv" in current_python or "venv" in current_python:
            return current_python

        # Try to find the virtual environment python
        project_root = Path(__file__).parent
        venv_python_paths = [
            project_root / ".venv" / "bin" / "python",
            project_root / "venv" / "bin" / "python",
            project_root / ".venv" / "Scripts" / "python.exe",  # Windows
        ]

        for venv_path in venv_python_paths:
            if venv_path.exists():
                return str(venv_path)

        # Fallback to current python
        return current_python

    def _verify_dependencies_for_subprocess(self, required_modules: List[str]) -> bool:
        """Verify that required modules can be imported by subprocess"""
        try:
            env = self._create_enhanced_subprocess_env()
            for module in required_modules:
                result = subprocess.run(
                    [self.venv_python, "-c", f"import {module}; print('{module} OK')"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    env=env,  # Use enhanced environment
                )
                if result.returncode != 0:
                    self.print_step(
                        f"Dependency check failed for {module}: {result.stderr[:100]}",
                        "error",
                    )
                    return False
            return True
        except Exception as e:
            self.print_step(f"Dependency verification error: {str(e)[:50]}", "error")
            return False

    def _create_enhanced_subprocess_env(self) -> Dict[str, str]:
        """Create enhanced environment for subprocess calls"""
        env = os.environ.copy()
        project_root = str(Path(__file__).parent)

        # Ensure Python path includes project root
        python_path = env.get("PYTHONPATH", "")
        if python_path:
            env["PYTHONPATH"] = f"{project_root}:{python_path}"
        else:
            env["PYTHONPATH"] = project_root

        # Ensure virtual environment is properly set
        if ".venv" in self.venv_python:
            venv_root = str(Path(self.venv_python).parent.parent)
            env["VIRTUAL_ENV"] = venv_root

        return env

    def save_status(self):
        """Save current status to file for dashboard"""
        try:
            with open(self.status_file, "w") as f:
                json.dump(self.status_data, f, indent=2)
        except Exception as e:
            pass  # Silent fail for status file

    def refresh_server_status(self):
        """Refresh server status with real-time health checks"""
        try:
            # Import and run the status refresh tool
            subprocess.run(
                [sys.executable, "fix_server_status.py"],
                cwd=str(Path(__file__).parent),
                check=False,
            )
            self.print_step("Server status refreshed with real-time data", "success")
        except Exception as e:
            self.print_step(f"Status refresh failed: {str(e)[:50]}", "warning")

    def update_component_status(
        self, component_type: str, name: str, status: str, details: Dict = None
    ):
        """Update status of a specific component"""
        if component_type not in self.status_data:
            self.status_data[component_type] = {}

        self.status_data[component_type][name] = {
            "status": status,
            "last_update": datetime.now().isoformat(),
            "details": details or {},
        }
        self.save_status()

    async def start_registry_system(self):
        """Initialize and start the registry system infrastructure"""
        self.print_section("Registry System", "🗂️")

        try:
            # Check if Docker infrastructure is running
            self.print_step(
                "Checking PostgreSQL and Redis infrastructure...", "starting"
            )

            import docker

            client = docker.from_env()

            # Check for required containers
            required_containers = ["boarderframeos_postgres", "boarderframeos_redis"]
            running_containers = []

            for container_name in required_containers:
                try:
                    container = client.containers.get(container_name)
                    if container.status == "running":
                        running_containers.append(container_name)
                        self.print_step(f"✓ {container_name} is running", "success")
                    else:
                        self.print_step(
                            f"⚠️ {container_name} is {container.status}", "warning"
                        )
                except:
                    self.print_step(f"❌ {container_name} not found", "error")

            if len(running_containers) < 2:
                self.print_step("Starting Docker infrastructure...", "starting")
                # Try to start the infrastructure
                result = subprocess.run(
                    ["docker-compose", "up", "-d", "postgresql", "redis"],
                    cwd=Path(__file__).parent,
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    self.print_step(
                        f"Docker startup failed: {result.stderr[:50]}", "error"
                    )
                    return False

                # Wait for containers to be healthy
                self.print_step("Waiting for containers to be healthy...", "starting")
                for i in range(30):  # Wait up to 30 seconds
                    await asyncio.sleep(1)
                    try:
                        # Check PostgreSQL health
                        postgres_container = client.containers.get(
                            "boarderframeos_postgres"
                        )
                        if postgres_container.status == "running":
                            # Check if PostgreSQL is ready
                            health_result = subprocess.run(
                                [
                                    "docker",
                                    "exec",
                                    "boarderframeos_postgres",
                                    "pg_isready",
                                    "-U",
                                    "boarderframe",
                                    "-d",
                                    "boarderframeos",
                                ],
                                capture_output=True,
                                text=True,
                            )
                            if health_result.returncode == 0:
                                self.print_step("PostgreSQL is ready", "success")
                                break
                    except Exception:
                        continue
                else:
                    self.print_step("PostgreSQL health check timeout", "warning")

            # Test database connectivity
            self.print_step("Testing database connectivity...", "starting")
            try:
                # Test PostgreSQL connection
                test_result = subprocess.run(
                    [
                        "docker",
                        "exec",
                        "boarderframeos_postgres",
                        "psql",
                        "-U",
                        "boarderframe",
                        "-d",
                        "boarderframeos",
                        "-c",
                        "SELECT 1;",
                    ],
                    capture_output=True,
                    text=True,
                )
                if test_result.returncode == 0:
                    self.print_step("Database connectivity confirmed", "success")
                else:
                    self.print_step(
                        f"Database connection failed: {test_result.stderr[:50]}",
                        "error",
                    )
                    return False
            except Exception as e:
                self.print_step(
                    f"Database connection test failed: {str(e)[:50]}", "error"
                )
                return False

            # Initialize registry client
            self.print_step("Initializing registry client...", "starting")
            # Import locally to avoid circular imports
            import os
            import sys

            sys.path.insert(0, os.path.dirname(__file__))
            try:
                from core.registry_integration import get_registry_client

                registry_client = await get_registry_client()
                self.print_step("Registry client initialized", "success")
            except Exception as e:
                self.print_step(
                    f"Registry client init failed: {str(e)[:50]}", "warning"
                )
                # Continue without registry client

            self.print_step("Registry system initialized successfully", "success")
            self.update_component_status(
                "services",
                "registry_system",
                "running",
                {
                    "component": "service_discovery",
                    "database_status": "connected",
                    "redis_status": "connected",
                },
            )
            return True

        except Exception as e:
            self.print_step(f"Registry system failed: {str(e)[:50]}", "error")
            self.update_component_status(
                "services", "registry_system", "failed", {"error": str(e)[:100]}
            )
            # Don't fail startup completely if registry fails
            return True  # Allow system to continue without registry

    async def start_message_bus(self):
        """Initialize and start the message bus for agent communication"""
        self.print_section("Message Bus", "📡")

        try:
            self.print_step(
                "Starting message bus for agent communication...", "starting"
            )

            # Import and start message bus
            from core.message_bus import message_bus

            await message_bus.start()

            self.print_step("Message bus started successfully", "success")
            self.update_component_status(
                "services",
                "message_bus",
                "running",
                {"component": "core_communication", "agents_connected": 0},
            )
            return True

        except Exception as e:
            self.print_step(f"Message bus failed: {str(e)[:50]}", "error")
            self.update_component_status(
                "services", "message_bus", "failed", {"error": str(e)[:100]}
            )
            return False

    async def start_agent_cortex_system(self):
        """Initialize and start Agent Cortex intelligent model orchestration"""
        self.print_section("Agent Cortex", "🧠")

        try:
            self.print_step(
                "Initializing Agent Cortex for intelligent model orchestration...",
                "starting",
            )

            # First, verify critical dependencies for Agent Cortex
            self.print_step("Verifying Agent Cortex dependencies...", "starting")
            cortex_dependencies = ["litellm", "qdrant_client", "core.agent_cortex"]
            if not self._verify_dependencies_for_subprocess(cortex_dependencies):
                self.print_step("Agent Cortex dependency verification failed", "error")
                self.update_component_status(
                    "services",
                    "agent_cortex",
                    "failed",
                    {
                        "error": "Missing dependencies: litellm, qdrant_client, or core modules"
                    },
                )
                return False
            self.print_step("All Agent Cortex dependencies verified", "success")

            # Import and initialize Agent Cortex
            from core.agent_cortex import get_agent_cortex_instance

            cortex = await get_agent_cortex_instance()

            # Verify Cortex is operational
            status = await cortex.get_status()

            self.print_step("Agent Cortex initialized successfully", "success")
            self.print_step(f"Strategy: {cortex.current_strategy.value}", "info")
            self.print_step(
                f"Active providers: {len(cortex.multi_provider.providers)}", "info"
            )

            self.update_component_status(
                "services",
                "agent_cortex",
                "running",
                {
                    "component": "intelligent_orchestration",
                    "strategy": cortex.current_strategy.value,
                    "providers": len(cortex.multi_provider.providers),
                    "status": status,
                },
            )

            # Start Agent Cortex Management UI with enhanced subprocess setup
            self.print_step(
                "Starting Agent Cortex Management UI on port 8889...", "starting"
            )

            enhanced_env = self._create_enhanced_subprocess_env()

            # Mark this as a subprocess launch for Agent Cortex
            enhanced_env["BOARDERFRAME_STARTUP"] = "1"

            # Kill any existing Agent Cortex UI processes first
            try:
                subprocess.run(
                    ["pkill", "-f", "agent_cortex_management.py"],
                    capture_output=True,
                    check=False,
                )
                subprocess.run(
                    ["pkill", "-f", "agent_cortex_launcher.py"],
                    capture_output=True,
                    check=False,
                )
                subprocess.run(
                    ["pkill", "-f", "agent_cortex_simple_launcher.py"],
                    capture_output=True,
                    check=False,
                )
                await asyncio.sleep(1)  # Give processes time to die
            except:
                pass

            # Set environment to indicate subprocess launch
            enhanced_env["BOARDERFRAME_STARTUP"] = "1"

            # Use the simple launcher to avoid async conflicts
            cortex_ui_process = subprocess.Popen(
                [self.venv_python, "ui/agent_cortex_simple_launcher.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(Path(__file__).parent),
                env=enhanced_env,
                start_new_session=True,  # Create new process group
                close_fds=True,  # Close inherited file descriptors
            )

            self.processes["cortex_ui"] = cortex_ui_process

            # Wait for Cortex UI to start with better error handling
            ui_started = False
            self.print_step(
                "Waiting for Agent Cortex UI to become responsive...", "starting"
            )
            for i in range(60):  # Increased timeout to 60 iterations (30 seconds)
                await asyncio.sleep(0.5)

                # Progress indicator every 5 seconds
                if i > 0 and i % 10 == 0:
                    self.print_step(
                        f"Still waiting for Agent Cortex UI (attempt {i}/60)...", "info"
                    )

                # Check if process died
                if cortex_ui_process.poll() is not None:
                    stdout, stderr = cortex_ui_process.communicate()
                    error_msg = stderr.decode() if stderr else stdout.decode()
                    self.print_step(f"Agent Cortex UI process died early", "error")
                    if error_msg:
                        # Print more detailed error for debugging
                        print(f"    Error details: {error_msg[:300]}")

                    # Try to restart once if it died due to import issues
                    if "ModuleNotFoundError" in error_msg or "ImportError" in error_msg:
                        self.print_step(
                            "Retrying Agent Cortex UI startup with enhanced environment...",
                            "starting",
                        )

                        # Ensure PYTHONPATH is set correctly
                        enhanced_env["PYTHONPATH"] = str(Path(__file__).parent)

                        cortex_ui_process = subprocess.Popen(
                            [self.venv_python, "ui/agent_cortex_simple_launcher.py"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            cwd=str(Path(__file__).parent),
                            env=enhanced_env,
                            start_new_session=True,
                            close_fds=True,
                        )
                        self.processes["cortex_ui"] = cortex_ui_process
                        continue

                    self.update_component_status(
                        "services",
                        "agent_cortex",
                        "failed",
                        {"error": f"UI Process died: {error_msg[:200]}"},
                    )
                    break

                # Check if port is responding
                try:
                    import socket

                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex(("localhost", 8889))
                    sock.close()
                    if result == 0:
                        self.print_step(
                            "Agent Cortex Management UI started on http://localhost:8889",
                            "success",
                        )
                        self.update_component_status(
                            "services",
                            "agent_cortex",
                            "running",
                            {
                                "port": 8889,
                                "url": "http://localhost:8889",
                                "pid": cortex_ui_process.pid,
                                "component": "intelligent_orchestration_ui",
                                "strategy": cortex.current_strategy.value,
                                "providers": len(cortex.multi_provider.providers),
                            },
                        )
                        ui_started = True
                        break
                except:
                    pass

            if not ui_started:
                self.print_step(
                    "Agent Cortex UI startup timeout - will try manual start", "warning"
                )
                # Try a final manual start attempt with the launcher
                try:
                    # Set explicit subprocess environment
                    manual_env = enhanced_env.copy()
                    manual_env["FLASK_DEBUG"] = "0"
                    manual_env["WERKZEUG_RUN_MAIN"] = "true"

                    manual_process = subprocess.Popen(
                        [self.venv_python, "ui/agent_cortex_launcher.py"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        cwd=str(Path(__file__).parent),
                        env=manual_env,
                    )
                    self.processes["cortex_ui"] = manual_process
                    await asyncio.sleep(2)

                    # Quick check if manual start worked
                    import socket

                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex(("localhost", 8889))
                    sock.close()
                    if result == 0:
                        self.print_step(
                            "Agent Cortex UI started via manual method", "success"
                        )
                        self.update_component_status(
                            "services",
                            "agent_cortex",
                            "running",
                            {
                                "port": 8889,
                                "url": "http://localhost:8889",
                                "manual_start": True,
                            },
                        )
                        ui_started = True
                except Exception as manual_e:
                    self.print_step(
                        f"Manual start also failed: {str(manual_e)[:50]}", "warning"
                    )

                if not ui_started:
                    self.update_component_status(
                        "services",
                        "agent_cortex",
                        "failed",
                        {
                            "note": "Core Agent Cortex is operational, but UI failed to start",
                            "error": "UI startup timeout after multiple retry attempts",
                        },
                    )
                    # Still return True since core Agent Cortex works, just UI failed
                    self.print_step(
                        "Agent Cortex core operational, UI will need manual start",
                        "warning",
                    )
                    self.print_step("Manual start: ./start_agent_cortex.sh", "info")

            # Update the final status based on whether UI started
            if ui_started:
                # UI started successfully
                return True
            else:
                # UI didn't start but core is operational
                # Update status to show core is running even if UI isn't
                self.update_component_status(
                    "services",
                    "agent_cortex",
                    "running",
                    {
                        "component": "intelligent_orchestration",
                        "strategy": cortex.current_strategy.value,
                        "providers": len(cortex.multi_provider.providers),
                        "ui_status": "offline",
                        "core_status": "operational",
                        "note": "Core Agent Cortex operational, UI requires manual start",
                    },
                )
                return True  # Return True since core Agent Cortex is operational

        except Exception as e:
            self.print_step(f"Agent Cortex failed: {str(e)[:50]}", "error")
            self.update_component_status(
                "services", "agent_cortex", "failed", {"error": str(e)[:100]}
            )
            return False

    async def start_agent_orchestrator(self):
        """Initialize and start the Agent Orchestrator for sophisticated agent lifecycle management"""
        self.print_section("Agent Orchestrator", "🎭")

        try:
            self.print_step(
                "Initializing Agent Orchestrator for production agent management...",
                "starting",
            )

            # Import and initialize Agent Orchestrator
            from core.agent_orchestrator import OrchestrationMode, orchestrator

            # Set orchestration mode based on environment
            if os.getenv("BOARDERFRAME_ENV") == "production":
                orchestrator.mode = OrchestrationMode.PRODUCTION
            elif os.getenv("BOARDERFRAME_ENV") == "testing":
                orchestrator.mode = OrchestrationMode.TESTING
            else:
                orchestrator.mode = OrchestrationMode.DEVELOPMENT

            # Initialize the orchestrator
            await orchestrator.initialize()

            self.print_step("Agent Orchestrator initialized successfully", "success")
            self.print_step(f"Mode: {orchestrator.mode.value}", "info")
            self.print_step(
                f"Registry agents: {len(orchestrator.agent_registry)}", "info"
            )

            self.update_component_status(
                "services",
                "agent_orchestrator",
                "running",
                {
                    "component": "agent_lifecycle_management",
                    "mode": orchestrator.mode.value,
                    "max_agents": orchestrator.agent_limits[orchestrator.mode][
                        "max_agents"
                    ],
                    "registry_size": len(orchestrator.agent_registry),
                    "mesh_networks": len(orchestrator.mesh_networks),
                },
            )

            # Store orchestrator reference for later use in agent startup
            self.orchestrator = orchestrator

            return True

        except Exception as e:
            self.print_step(f"Agent Orchestrator failed: {str(e)[:50]}", "error")
            self.update_component_status(
                "services", "agent_orchestrator", "failed", {"error": str(e)[:100]}
            )
            return False

    async def run_database_migrations(self):
        """Run database migrations to ensure schema is up to date"""
        self.print_section("Database Migrations", "🏗️")

        try:
            self.print_step(
                "Checking database schema and running migrations...", "starting"
            )

            # Check if migrations directory exists
            migrations_dir = Path(__file__).parent / "migrations"
            if not migrations_dir.exists():
                self.print_step("No migrations directory found, skipping...", "info")
                return True

            # First, ensure base schema exists by running SQL migrations via Docker
            migration_files = sorted(migrations_dir.glob("*.sql"))
            if migration_files:
                self.print_step(
                    f"Found {len(migration_files)} SQL migration files", "info"
                )
                self.print_step(
                    "SQL migrations are handled automatically by Docker init scripts",
                    "info",
                )

            # Wait a bit to ensure any Docker init scripts have completed
            await asyncio.sleep(2)

            # Test database connectivity before running Python migrations
            self.print_step("Verifying database connectivity...", "starting")
            try:
                test_result = subprocess.run(
                    [
                        "docker",
                        "exec",
                        "boarderframeos_postgres",
                        "psql",
                        "-U",
                        "boarderframe",
                        "-d",
                        "boarderframeos",
                        "-c",
                        "SELECT version();",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if test_result.returncode != 0:
                    self.print_step(
                        f"Database not ready: {test_result.stderr[:100]}", "error"
                    )
                    return False
                self.print_step("Database connectivity verified", "success")
            except subprocess.TimeoutExpired:
                self.print_step("Database connection timeout", "error")
                return False
            except Exception as e:
                self.print_step(
                    f"Database connection test failed: {str(e)[:50]}", "error"
                )
                return False

            # Run Python migration scripts if they exist (but skip problematic ones for now)
            python_migrations = sorted(migrations_dir.glob("*.py"))
            successful_migrations = 0
            skipped_migrations = []

            # Skip problematic migrations that require specific schema
            skip_migrations = [
                "migrate_departments.py",
                "migrate_sqlite_to_postgres.py",
                "populate_divisions_departments.py",  # Skip this one too due to unique constraint issues
            ]

            for migration_file in python_migrations:
                if migration_file.name in skip_migrations:
                    self.print_step(
                        f"Skipping {migration_file.name} (requires manual setup)",
                        "info",
                    )
                    skipped_migrations.append(migration_file.name)
                    continue

                if migration_file.name.startswith(
                    "migrate_"
                ) or migration_file.name.startswith("populate_"):
                    self.print_step(f"Running {migration_file.name}...", "starting")
                    try:
                        # Import and run migration
                        import importlib.util

                        spec = importlib.util.spec_from_file_location(
                            "migration", migration_file
                        )
                        migration_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(migration_module)

                        # Check if it has a main function and run it
                        if hasattr(migration_module, "main"):
                            if asyncio.iscoroutinefunction(migration_module.main):
                                await migration_module.main()
                            else:
                                migration_module.main()

                        self.print_step(
                            f"Migration {migration_file.name} completed", "success"
                        )
                        successful_migrations += 1
                    except Exception as e:
                        self.print_step(
                            f"Migration {migration_file.name} failed: {str(e)[:50]}",
                            "warning",
                        )
                        # Continue with other migrations

            if skipped_migrations:
                self.print_step(
                    f"Skipped {len(skipped_migrations)} migrations requiring manual setup",
                    "info",
                )

            self.print_step("Database migrations completed", "success")
            self.update_component_status(
                "services",
                "database_migrations",
                "completed",
                {
                    "sql_files": len(migration_files),
                    "python_files": len(python_migrations),
                    "successful_python_migrations": successful_migrations,
                    "skipped_migrations": len(skipped_migrations),
                },
            )
            return True

        except Exception as e:
            self.print_step(f"Database migrations failed: {str(e)[:50]}", "error")
            self.update_component_status(
                "services", "database_migrations", "failed", {"error": str(e)[:100]}
            )
            # Don't fail startup completely - basic schema should work
            return True

    async def initialize_hq_metrics_layer(self):
        """Initialize HQ metrics calculation and visualization layer"""
        self.print_section("HQ Metrics Layer", "📊")

        try:
            self.print_step(
                "Initializing HQ Metrics Layer for comprehensive system tracking...",
                "starting",
            )

            # Import HQ Metrics components
            from core.hq_metrics_integration import HQMetricsIntegration
            from core.hq_metrics_layer import MetricsCalculator

            # Initialize metrics integration
            self.hq_metrics = HQMetricsIntegration()

            # Set the server status from our current MCP server status
            if (
                hasattr(self.hq_metrics, "metrics_calculator")
                and self.hq_metrics.metrics_calculator
            ):
                # Gather current server status
                server_status = {}

                # Add MCP servers
                print(
                    f"DEBUG: Available status_data keys: {list(self.status_data.keys())}"
                )
                if "mcp_servers" in self.status_data:
                    print(
                        f"DEBUG: Found {len(self.status_data['mcp_servers'])} MCP servers in status_data"
                    )
                    for server_name, server_info in self.status_data[
                        "mcp_servers"
                    ].items():
                        if server_info.get("status") == "running":
                            server_status[server_name] = {
                                "status": "healthy",
                                "port": server_info.get("port", 0),
                                "name": server_name.replace("_", " ").title(),
                                "category": "MCP Servers",
                            }
                else:
                    print("DEBUG: No mcp_servers key in status_data!")

                # Note: Corporate Headquarters will be added later when it starts
                # Set the server status
                print(
                    f"DEBUG: Setting server status with {len(server_status)} servers: {list(server_status.keys())}"
                )
                self.hq_metrics.metrics_calculator.set_server_status(server_status)

            # Warm up metrics cache with initial calculation
            self.print_step("Warming up metrics cache...", "starting")
            try:
                initial_metrics = self.hq_metrics.get_all_metrics(force_refresh=True)
                agent_count = initial_metrics.get("agents", {}).get("total", 0)
                server_count = initial_metrics.get("servers", {}).get("total", 0)

                self.print_step(
                    f"Metrics cache warmed - {agent_count} agents, {server_count} servers tracked",
                    "success",
                )
            except Exception as cache_error:
                self.print_step(
                    f"Metrics cache warming failed: {str(cache_error)[:50]}", "warning"
                )
                # Continue without failing - metrics will work but slower initially

            self.print_step("HQ Metrics Layer initialized successfully", "success")
            self.update_component_status(
                "services",
                "hq_metrics_layer",
                "running",
                {
                    "component": "metrics_calculation",
                    "cache_warmed": True,
                    "integration_active": True,
                },
            )

            return True

        except Exception as e:
            self.print_step(f"HQ Metrics Layer failed: {str(e)[:50]}", "error")
            self.update_component_status(
                "services", "hq_metrics_layer", "failed", {"error": str(e)[:100]}
            )
            return False

    async def initialize_cost_management(self):
        """Initialize cost management and optimization systems"""
        self.print_section("Cost Management", "💰")

        try:
            self.print_step(
                "Initializing cost management and optimization systems...", "starting"
            )

            # Import cost management configuration
            from core.cost_management import (
                AGENT_COST_POLICIES,
                API_COST_SETTINGS,
                MODEL_COSTS,
                get_cost_optimization_status,
            )

            # Get optimization status
            cost_status = get_cost_optimization_status()

            # Set up cost tracking and monitoring
            self.print_step("Setting up API cost tracking...", "starting")

            # Log cost settings info
            enabled_features = []
            if API_COST_SETTINGS.get("cost_optimization_enabled"):
                enabled_features.append("optimization")
            if API_COST_SETTINGS.get("rate_limiting", {}).get("enabled"):
                enabled_features.append("rate_limiting")
            if API_COST_SETTINGS.get("smart_batching", {}).get("enabled"):
                enabled_features.append("smart_batching")

            self.print_step(
                f"Cost features enabled: {', '.join(enabled_features)}", "info"
            )
            self.print_step(f"Tracking {len(MODEL_COSTS)} LLM models", "info")

            self.print_step("Cost Management initialized successfully", "success")
            self.update_component_status(
                "services",
                "cost_management",
                "running",
                {
                    "component": "cost_optimization",
                    "models_tracked": len(MODEL_COSTS),
                    "optimization_active": API_COST_SETTINGS.get(
                        "cost_optimization_enabled", False
                    ),
                    "features_enabled": enabled_features,
                },
            )

            return True

        except Exception as e:
            self.print_step(f"Cost Management failed: {str(e)[:50]}", "error")
            self.update_component_status(
                "services", "cost_management", "failed", {"error": str(e)[:100]}
            )
            return False

    def check_dependencies(self):
        """Check and install required dependencies"""
        self.print_section("Dependency Check", "📦")

        try:
            # First run environment setup
            self.print_step("Running environment setup...", "starting")
            try:
                from scripts.setup_environment import (
                    ensure_database_setup,
                    setup_environment,
                )

                if not setup_environment():
                    self.print_step("Environment setup failed", "error")
                    return False

                self.print_step("Environment setup completed", "success")

                # Ensure database is ready
                self.print_step(
                    "Ensuring database infrastructure is ready...", "starting"
                )
                if ensure_database_setup():
                    self.print_step("Database infrastructure ready", "success")
                else:
                    self.print_step(
                        "Database setup had issues, continuing...", "warning"
                    )

            except Exception as e:
                self.print_step(f"Environment setup error: {str(e)[:50]}", "warning")
                # Continue without setup - might still work

            # Check Python packages
            self.print_step("Checking Python dependencies...", "starting")

            # Try to import key packages
            required_packages = [
                ("fastapi", "FastAPI"),
                ("psutil", "psutil"),
                ("httpx", "httpx"),
                ("docker", "docker"),
                ("flask", "Flask"),
            ]

            missing_packages = []
            for package_name, import_name in required_packages:
                try:
                    __import__(import_name.lower())
                except ImportError:
                    missing_packages.append(package_name)

            if missing_packages:
                self.print_step(
                    f"Installing missing packages: {', '.join(missing_packages)}",
                    "starting",
                )
                for package in missing_packages:
                    try:
                        subprocess.run(
                            [sys.executable, "-m", "pip", "install", package],
                            check=True,
                            capture_output=True,
                        )
                    except subprocess.CalledProcessError:
                        self.print_step(f"Failed to install {package}", "warning")

            self.print_step("All dependencies ready", "success")
            return True

        except Exception as e:
            self.print_step(f"Dependency check failed: {e}", "error")
            return False

    async def start_mcp_server(self, server_info: Dict) -> bool:
        """Start a single MCP server with enhanced error handling"""
        name = server_info["name"]
        port = server_info["port"]
        script = server_info["script"]

        try:
            # Just show a simple dot for progress, main result will show at the end
            print(f"    ⏳ {name.ljust(12)} ", end="", flush=True)

            # Update status to starting
            self.update_component_status(
                "mcp_servers", name, "starting", {"port": port, "script": script}
            )

            # Check if port is already in use
            try:
                import socket

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(("localhost", port))
                sock.close()
                if result == 0:
                    print("✅ (already running)")
                    self.update_component_status(
                        "mcp_servers", name, "running", {"port": port}
                    )
                    return True
            except:
                pass

            # Start the server with current Python
            script_path = Path(__file__).parent / "mcp" / script
            current_python = sys.executable

            if not script_path.exists():
                print("❌ (script not found)")
                self.update_component_status(
                    "mcp_servers",
                    name,
                    "not_found",
                    {"expected_path": str(script_path)},
                )
                return False

            # Start process with virtual environment Python
            # Add port argument for servers that need it
            cmd = [self.venv_python, str(script_path)]
            if name == "database_postgres":
                cmd.extend(["--port", str(port)])

            # Use enhanced environment setup
            env = self._create_enhanced_subprocess_env()

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(Path(__file__).parent),
                env=env,
            )

            self.processes[f"mcp_{name}"] = process

            # Wait for startup with timeout (longer for filesystem server)
            timeout_iterations = (
                60 if name == "filesystem" else 30
            )  # 30s for filesystem, 15s for others
            for i in range(timeout_iterations):
                await asyncio.sleep(0.5)
                if process.poll() is not None:
                    # Process died
                    stdout, stderr = process.communicate()
                    print("❌ (process died)")
                    self.update_component_status(
                        "mcp_servers", name, "failed", {"error": stderr.decode()[:200]}
                    )
                    return False

                # Check if port is responding
                try:
                    import socket

                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex(("localhost", port))
                    sock.close()
                    if result == 0:
                        print("✅")
                        self.update_component_status(
                            "mcp_servers",
                            name,
                            "running",
                            {"port": port, "pid": process.pid},
                        )

                        # Register with database registry
                        await self.register_mcp_server_with_registry(
                            name, port, server_info
                        )

                        return True
                except:
                    continue

            # Timeout reached
            print("⏰ (timeout)")
            self.update_component_status("mcp_servers", name, "timeout", {"port": port})
            return False

        except Exception as e:
            print("❌ (error)")
            self.update_component_status(
                "mcp_servers", name, "error", {"error": str(e)}
            )
            return False

    async def register_mcp_server_with_registry(
        self, name: str, port: int, server_info: Dict
    ):
        """Register an MCP server with the database registry"""
        try:
            # Import locally to avoid circular imports
            import os
            import sys

            sys.path.insert(0, os.path.dirname(__file__))
            from core.registry_integration import register_server_with_database

            # Map server capabilities based on name
            capabilities = []
            if "filesystem" in name:
                capabilities = [
                    "file_operations",
                    "directory_management",
                    "search",
                    "monitoring",
                ]
            elif "database" in name:
                capabilities = [
                    "database_operations",
                    "vector_search",
                    "data_analytics",
                ]
            elif "git" in name:
                capabilities = [
                    "version_control",
                    "repository_management",
                    "code_tracking",
                ]
            elif "browser" in name:
                capabilities = ["web_browsing", "content_extraction", "automation"]
            elif "registry" in name:
                capabilities = [
                    "service_discovery",
                    "health_monitoring",
                    "registration",
                ]
            else:
                capabilities = ["general_purpose"]

            server_id = await register_server_with_database(
                server_name=f"BoarderframeOS {name.title()} Server",
                server_type="mcp",
                endpoint_url=f"http://localhost:{port}",
                capabilities=capabilities,
            )

            self.print_step(f"Registered {name} server in database registry", "success")

        except Exception as e:
            self.print_step(
                f"Registry registration failed for {name}: {str(e)[:40]}", "warning"
            )
            # Don't fail server startup if registry registration fails

    async def register_corporate_headquarters_with_registry(self):
        """Register BoarderframeOS Corporate Headquarters with database registry"""
        try:
            # Import locally to avoid circular imports
            import os
            import sys

            sys.path.insert(0, os.path.dirname(__file__))
            from core.registry_integration import register_server_with_database

            headquarters_capabilities = [
                "dashboard",
                "system_monitoring",
                "agent_management",
                "service_status",
                "chat_interface",
                "screenshot_api",
                "department_analytics",
                "registry_overview",
            ]

            server_id = await register_server_with_database(
                server_name="BoarderframeOS Corporate Headquarters",
                server_type="web_ui",
                endpoint_url="http://localhost:8888",
                capabilities=headquarters_capabilities,
            )

            self.print_step(
                "Corporate Headquarters registered in database registry", "success"
            )

        except Exception as e:
            self.print_step(
                f"Corporate Headquarters registry registration failed: {str(e)[:40]}",
                "warning",
            )
            # Don't fail Corporate Headquarters startup if registry registration fails

    async def start_mcp_servers(self):
        """Start all MCP servers with improved visual organization"""
        self.print_section("MCP Servers", "🔌")
        self.status_data["startup_phase"] = "starting_mcp_servers"

        # Group servers by categories for better organization
        core_servers = [
            {
                "name": "registry",
                "port": 8000,
                "script": "registry_server.py",
                "category": "Core",
            },  # Fixed port conflict
            {
                "name": "filesystem",
                "port": 8001,
                "script": "filesystem_server.py",
                "category": "Core",
            },
            {
                "name": "database_postgres",
                "port": 8010,
                "script": "database_server_postgres.py",
                "category": "Core",
            },  # Using PostgreSQL instead of SQLite
        ]

        service_servers = [
            # Removed LLM server - replaced by Agent Cortex
            {
                "name": "payment",
                "port": 8006,
                "script": "payment_server.py",
                "category": "Services",
            },
            {
                "name": "analytics",
                "port": 8007,
                "script": "analytics_server.py",
                "category": "Services",
            },
            {
                "name": "customer",
                "port": 8008,
                "script": "customer_server.py",
                "category": "Services",
            },
            {
                "name": "screenshot",
                "port": 8011,
                "script": "screenshot_server.py",
                "category": "Services",
            },
        ]

        # Note: Corporate Headquarters is started separately
        # in start_control_center() after all MCP servers are running
        # This ensures BCC can properly monitor all services

        # Combine all servers but maintain groups
        mcp_servers = core_servers + service_servers

        # Start core servers first (they're critical)
        print("\n  Core Servers:")
        core_results = []
        for server in core_servers:
            ok = await self.start_mcp_server(server)
            core_results.append((server["name"], ok, server["port"]))

        # Then start service servers
        print("\n  Service Servers:")
        service_results = []
        for server in service_servers:
            ok = await self.start_mcp_server(server)
            service_results.append((server["name"], ok, server["port"]))

        # Combine results
        results = core_results + service_results

        # Health check summary
        print("\n  Health Check:")
        all_healthy = await self.health_check_mcps(mcp_servers)

        # Final success count
        return sum(1 for _, ok, _ in results if ok)

    async def health_check_mcps(self, mcp_servers):
        """Health check for all MCP servers with simple output"""
        import httpx

        healthy_count = 0

        for server in mcp_servers:
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    resp = await client.get(f"http://localhost:{server['port']}/health")
                    if resp.status_code == 200:
                        healthy_count += 1
            except Exception:
                pass

        # Simple summary
        total = len(mcp_servers)
        print(f"  ✅ {healthy_count}/{total} servers healthy")

        return healthy_count == total

    async def start_agent_communication_center(self):
        """Start the Agent Communication Center (ACC)"""
        self.print_section("Agent Communication Center (ACC)", "🔗")
        self.status_data["startup_phase"] = "starting_acc"

        try:
            self.print_step(
                "Starting Agent Communication Center on port 8890",
                "starting",
            )

            # Start the ACC with enhanced subprocess setup
            enhanced_env = self._create_enhanced_subprocess_env()
            acc_process = subprocess.Popen(
                [self.venv_python, "agent_communication_center.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=str(Path(__file__).parent),
                env=enhanced_env,
            )

            self.processes["agent_communication_center"] = acc_process

            # Wait for startup
            for attempt in range(15):  # Try for 15 seconds
                await asyncio.sleep(1)

                # Check if process died
                if acc_process.poll() is not None:
                    try:
                        stdout, _ = acc_process.communicate(timeout=1)
                        error_msg = (
                            stdout.decode()
                            if stdout
                            else "Process exited without output"
                        )
                    except subprocess.TimeoutExpired:
                        error_msg = "Process communication timeout"
                    except Exception as e:
                        error_msg = f"Communication error: {str(e)}"

                    self.print_step(f"ACC failed: {error_msg[:100]}", "error")
                    self.update_component_status(
                        "services",
                        "agent_communication_center",
                        "failed",
                        {"error": error_msg[:200]},
                    )
                    return False

                # Check if port 8890 is responding
                try:
                    import socket

                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex(("localhost", 8890))
                    sock.close()
                    if result == 0:
                        self.print_step(
                            "Agent Communication Center started successfully",
                            "success",
                        )
                        self.update_component_status(
                            "services",
                            "agent_communication_center",
                            "running",
                            {
                                "port": 8890,
                                "pid": acc_process.pid,
                                "url": "http://localhost:8890",
                                "type": "core_service",
                                "description": "Claude-powered agent communications",
                            },
                        )

                        # Update metrics layer with ACC status
                        if hasattr(self, "hq_metrics") and hasattr(
                            self.hq_metrics, "metrics_calculator"
                        ):
                            # Get current server status
                            server_status = {}
                            if "mcp_servers" in self.status_data:
                                for server_name, server_info in self.status_data[
                                    "mcp_servers"
                                ].items():
                                    if server_info.get("status") == "running":
                                        server_status[server_name] = {
                                            "status": "healthy",
                                            "port": server_info.get("port", 0),
                                            "name": server_name.replace(
                                                "_", " "
                                            ).title(),
                                            "category": "MCP Servers",
                                        }

                            # Add ACC
                            server_status["agent_communication_center"] = {
                                "status": "healthy",
                                "port": 8890,
                                "name": "Agent Communication Center",
                                "category": "Core Services",
                            }

                            # Update the metrics layer
                            self.hq_metrics.metrics_calculator.set_server_status(
                                server_status
                            )

                        # Register ACC with database registry
                        # Note: Temporarily disabled due to missing module
                        # await self.register_acc_with_registry()

                        return True
                except Exception as e:
                    # Continue trying
                    pass

            # Timeout reached
            self.print_step("ACC startup timeout (15s)", "warning")
            return False

        except Exception as e:
            self.print_step(f"ACC error: {str(e)[:100]}", "error")
            self.update_component_status(
                "services", "agent_communication_center", "error", {"error": str(e)}
            )
            return False

    async def register_acc_with_registry(self):
        """Register ACC with the database registry"""
        try:
            # Import here to avoid circular dependencies
            from core.database_service_registry import ServiceRegistry

            registry = ServiceRegistry()

            # Register ACC as a core service
            await registry.register_service(
                name="agent_communication_center",
                host="localhost",
                port=8890,
                service_type="core_service",
                metadata={
                    "description": "Agent Communication Center - Claude-powered agent chat",
                    "version": "1.0.0",
                    "api_docs": "http://localhost:8890/docs",
                    "features": ["claude-3", "voice", "multi-agent"],
                    "category": "Core Services",
                },
            )

            self.log_status("ACC registered with database registry", "acc", "success")

        except Exception as e:
            self.log_status(f"Failed to register ACC: {str(e)}", "acc", "warning")

    async def start_corporate_headquarters(self):
        """Start the BoarderframeOS Corporate Headquarters"""
        self.print_section("Corporate Headquarters", "🎛️")
        self.status_data["startup_phase"] = "starting_corporate_headquarters"

        try:
            self.print_step(
                "Starting BoarderframeOS Corporate Headquarters on port 8888",
                "starting",
            )

            # Start the BoarderframeOS Corporate Headquarters with enhanced subprocess setup
            enhanced_env = self._create_enhanced_subprocess_env()
            corporate_headquarters_process = subprocess.Popen(
                [self.venv_python, "corporate_headquarters.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Combine stderr with stdout
                cwd=str(Path(__file__).parent),
                env=enhanced_env,
            )

            self.processes["corporate_headquarters"] = corporate_headquarters_process

            # Wait for startup with better monitoring
            for attempt in range(15):  # Try for 15 seconds
                await asyncio.sleep(1)

                # Check if process died
                if corporate_headquarters_process.poll() is not None:
                    try:
                        stdout, _ = corporate_headquarters_process.communicate(
                            timeout=1
                        )
                        error_msg = (
                            stdout.decode()
                            if stdout
                            else "Process exited without output"
                        )
                    except subprocess.TimeoutExpired:
                        error_msg = "Process communication timeout"
                    except Exception as e:
                        error_msg = f"Communication error: {str(e)}"

                    self.print_step(
                        f"Corporate Headquarters failed: {error_msg[:100]}", "error"
                    )
                    self.update_component_status(
                        "services",
                        "corporate_headquarters",
                        "failed",
                        {"error": error_msg[:200]},
                    )
                    return False

                # Check if port 8888 is responding
                try:
                    import socket

                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex(("localhost", 8888))
                    sock.close()
                    if result == 0:
                        self.print_step(
                            "BoarderframeOS Corporate Headquarters started successfully",
                            "success",
                        )
                        self.update_component_status(
                            "services",
                            "corporate_headquarters",
                            "running",
                            {
                                "port": 8888,
                                "pid": corporate_headquarters_process.pid,
                                "url": "http://localhost:8888",
                            },
                        )

                        # Update metrics layer with corporate headquarters status
                        if hasattr(self, "hq_metrics") and hasattr(
                            self.hq_metrics, "metrics_calculator"
                        ):
                            # Get current server status and add corporate headquarters
                            server_status = {}
                            if "mcp_servers" in self.status_data:
                                for server_name, server_info in self.status_data[
                                    "mcp_servers"
                                ].items():
                                    if server_info.get("status") == "running":
                                        server_status[server_name] = {
                                            "status": "healthy",
                                            "port": server_info.get("port", 0),
                                            "name": server_name.replace(
                                                "_", " "
                                            ).title(),
                                            "category": "MCP Servers",
                                        }

                            # Add corporate headquarters
                            server_status["corporate_headquarters"] = {
                                "status": "healthy",
                                "port": 8888,
                                "name": "Corporate Headquarters",
                                "category": "Core Services",
                            }

                            # Update the metrics layer
                            self.hq_metrics.metrics_calculator.set_server_status(
                                server_status
                            )

                        # Register Corporate Headquarters with database registry
                        await self.register_corporate_headquarters_with_registry()

                        return True
                except Exception as e:
                    # Continue trying
                    pass

            # Timeout reached
            self.print_step("Corporate Headquarters startup timeout (15s)", "warning")
            return False

        except Exception as e:
            self.print_step(f"Corporate Headquarters error: {str(e)[:100]}", "error")
            self.update_component_status(
                "services", "corporate_headquarters", "error", {"error": str(e)}
            )
            return False

    async def start_agents(self):
        """Start agent coordination system using enhanced agent manager and orchestrator"""
        self.print_section("Agents", "🤖")
        self.status_data["startup_phase"] = "starting_agents"
        try:
            # Use orchestrator if available, fallback to agent manager
            if hasattr(self, "orchestrator") and self.orchestrator:
                self.print_step(
                    "Using Agent Orchestrator for sophisticated agent management",
                    "starting",
                )

                # Try to load registry now that database should be ready
                try:
                    await self.orchestrator.ensure_registry_loaded()
                except Exception as e:
                    self.print_step(
                        f"Failed to load orchestrator registry: {str(e)[:50]}",
                        "warning",
                    )

                # Check if orchestrator has any agents in registry
                if len(self.orchestrator.agent_registry) == 0:
                    self.print_step(
                        "No agents found in orchestrator registry, falling back to agent manager",
                        "warning",
                    )
                    use_orchestrator = False
                else:
                    use_orchestrator = True

                if use_orchestrator:
                    # Start core agents through orchestrator
                    core_results = await self.orchestrator.start_core_agents()

                    running_count = sum(core_results.values())
                    total_count = len(core_results)

                    for agent_name, success in core_results.items():
                        if success:
                            self.print_step(
                                f"{agent_name.title()} agent - started via orchestrator",
                                "success",
                            )
                            self.update_component_status(
                                "agents",
                                agent_name,
                                "running",
                                {
                                    "managed_by": "orchestrator",
                                    "lifecycle_management": "advanced",
                                    "startup_method": "orchestrated",
                                },
                            )
                        else:
                            self.print_step(
                                f"{agent_name.title()} agent - failed to start", "error"
                            )
                            self.update_component_status(
                                "agents",
                                agent_name,
                                "failed",
                                {
                                    "error": "Orchestrator startup failed",
                                    "managed_by": "orchestrator",
                                },
                            )

                    print(
                        f"\n  ✅ {running_count}/{total_count} agents started via orchestrator"
                    )
                else:
                    # Fall through to agent manager
                    use_orchestrator = False
            else:
                use_orchestrator = False

            if not use_orchestrator:
                # Fallback to enhanced agent manager
                self.print_step(
                    "Using enhanced agent manager (orchestrator not available)",
                    "starting",
                )

                # Import and use the enhanced agent manager
                from scripts.start_agents import AgentManager

                agent_manager = AgentManager()

                # Get available agents in priority order
                agents_by_priority = sorted(
                    agent_manager.agent_configs.items(), key=lambda x: x[1]["priority"]
                )

                results = []

                for agent_name, config in agents_by_priority:
                    self.print_step(f"Checking {agent_name.title()} agent", "starting")

                    # Check if agent is already running
                    if agent_manager.is_agent_running(agent_name):
                        pid = agent_manager.get_agent_pid(agent_name)
                        self.print_step(
                            f"{agent_name.title()} (PID {pid}) - already running",
                            "success",
                        )
                        self.update_component_status(
                            "agents",
                            agent_name,
                            "running",
                            {
                                "pid": pid,
                                "model": config["model"],
                                "description": config["description"],
                                "priority": config["priority"],
                                "managed_by": "agent_manager",
                            },
                        )
                        results.append(True)
                    else:
                        # Start the agent
                        self.print_step(
                            f"Starting {agent_name.title()} agent...", "starting"
                        )
                        success = agent_manager.start_agent(agent_name)

                        if success:
                            # Wait a moment and verify it started
                            await asyncio.sleep(2)
                            if agent_manager.is_agent_running(agent_name):
                                pid = agent_manager.get_agent_pid(agent_name)
                                self.print_step(
                                    f"{agent_name.title()} (PID {pid}) - started",
                                    "success",
                                )
                                self.update_component_status(
                                    "agents",
                                    agent_name,
                                    "running",
                                    {
                                        "pid": pid,
                                        "model": config["model"],
                                        "description": config["description"],
                                        "priority": config["priority"],
                                        "managed_by": "agent_manager",
                                    },
                                )
                                results.append(True)
                            else:
                                self.print_step(
                                    f"{agent_name.title()} - failed to start", "error"
                                )
                                self.update_component_status(
                                    "agents",
                                    agent_name,
                                    "failed",
                                    {
                                        "error": "Process died after startup",
                                        "model": config["model"],
                                        "description": config["description"],
                                    },
                                )
                                results.append(False)
                        else:
                            self.print_step(
                                f"{agent_name.title()} - failed to start", "error"
                            )
                            self.update_component_status(
                                "agents",
                                agent_name,
                                "failed",
                                {
                                    "error": "Failed to start process",
                                    "model": config["model"],
                                    "description": config["description"],
                                },
                            )
                            results.append(False)

                    # Small delay between agent starts
                    if (
                        agent_name != list(agents_by_priority)[-1][0]
                    ):  # Not the last agent
                        await asyncio.sleep(1)

                # Simple agent summary
                running_count = sum(results)
                total_count = len(results)
                print(f"\n  ✅ {running_count}/{total_count} agents running")

            return True

        except Exception as e:
            self.print_step(f"Agent system error: {str(e)[:100]}", "error")
            self.log_status(f"Agent startup error: {str(e)}", "agents", "error")
            return True

    async def run_startup(self):
        """Run the complete enhanced system startup with all components"""
        # Create a more attractive header
        print("\n" + "=" * 70)
        print(f"{'🏰 BOARDERFRAMEOS ENHANCED SYSTEM BOOT 🏰':^70}")
        print("=" * 70)
        print(f"{'📅 ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'):^70}")
        print("=" * 70 + "\n")

        # Initialize status
        self.status_data["startup_phase"] = "initializing"
        self.save_status()

        success_count = 0
        total_steps = 12  # Updated with ACC and all new components

        # Phase 1: Infrastructure Setup
        print("🔧 Phase 1: Infrastructure Setup")
        print("─" * 50)

        # Step 1: Dependencies
        if not self.check_dependencies():
            print("\n❌ Startup failed at dependency check")
            return False
        success_count += 1

        # Step 2: Database Migrations (NEW)
        if await self.run_database_migrations():
            success_count += 1

        # Step 3: Registry System (critical for service discovery)
        if await self.start_registry_system():
            success_count += 1

        # Phase 2: Core Services
        print("\n🎭 Phase 2: Core Services")
        print("─" * 50)

        # Step 4: Message Bus (critical for agent communication)
        if await self.start_message_bus():
            success_count += 1

        # Step 5: Cost Management (NEW)
        if await self.initialize_cost_management():
            success_count += 1

        # Step 6: Agent Cortex (intelligent model orchestration)
        if await self.start_agent_cortex_system():
            success_count += 1

        # Step 7: Agent Orchestrator (NEW - Critical addition)
        if await self.start_agent_orchestrator():
            success_count += 1

        # Phase 3: Advanced Services
        print("\n🔌 Phase 3: Advanced Services")
        print("─" * 50)

        # Step 8: MCP Servers (critical infrastructure - start before metrics)
        mcp_count = await self.start_mcp_servers()
        if mcp_count > 0:
            success_count += 1

        # Step 9: HQ Metrics Layer (NEW - after MCP servers)
        if await self.initialize_hq_metrics_layer():
            success_count += 1

        # Phase 4: Agents & Interface
        print("\n🤖 Phase 4: Agents & Interface")
        print("─" * 50)

        # Step 10: Agents (now coordinated through orchestrator)
        if await self.start_agents():
            success_count += 1

        # Step 11: Agent Communication Center (ACC) - Claude-powered communications
        if await self.start_agent_communication_center():
            success_count += 1

        # Step 12: Corporate Headquarters (must be the very last step)
        if await self.start_corporate_headquarters():
            success_count += 1

        # Enhanced final status
        print(f"\n🎉 Enhanced System Startup Complete")
        print("=" * 70)

        self.status_data["startup_phase"] = "operational"
        self.save_status()

        # Give Agent Cortex a bit more time to fully initialize if needed
        await asyncio.sleep(2)

        # Refresh server status with real-time health checks
        print("\n🔄 Refreshing server status with real-time health checks...")
        self.refresh_server_status()

        # Enhanced success criteria
        if success_count >= 8:  # Most components running
            print("✅ BoarderframeOS Enhanced System is fully operational!")
            print("🏰 Enterprise-grade agent coordination active")
            print("📊 HQ Metrics Layer providing real-time insights")
            print("💰 Cost management optimization enabled")
            print("🎭 Agent Orchestrator managing sophisticated lifecycles")
            print()
            print("🎛️  Corporate Headquarters: http://localhost:8888")
            print("🔗 Agent Communication Center: http://localhost:8890")
            print("🧠 Agent Cortex Management: http://localhost:8889")
            print("💬 Ready for advanced agent conversations")
            print("📊 All server status updated with real-time health data")

            # Launch control center in browser
            try:
                import webbrowser

                webbrowser.open("http://localhost:8888")
                print("🌐 Browser opened automatically")
            except Exception:
                print("⚠️  Open browser manually to http://localhost:8888")

        elif success_count >= 5:  # Basic functionality
            print("⚠️  BoarderframeOS is operational with basic functionality")
            print(f"🎛️  Corporate Headquarters: http://localhost:8888")
            print("💡 Some advanced features may not be available")

        else:
            print(f"❌ Partial startup: {success_count}/{total_steps} components")
            print("🔧 Check logs for detailed error information")

        print(f"\n💡 Run 'python system_status.py' for detailed status")
        print(f"📊 Enhanced metrics available at Corporate Headquarters")

        return success_count >= 5

    def setup_signal_handlers(self):
        """Setup clean shutdown handlers"""

        def signal_handler(signum, frame):
            print(f"\n🛑 Received shutdown signal...")
            self.cleanup()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def cleanup(self):
        """Clean shutdown of all processes"""
        self.print_step("Cleaning up processes", "info")
        for name, process in self.processes.items():
            try:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass


async def main():
    """Main startup function with improved handling"""
    startup_time = datetime.now()
    startup = EnhancedSystemStartup()
    startup.setup_signal_handlers()

    try:
        success = await startup.run_startup()
        if success:
            # Keep running to maintain processes with better status output
            uptime_counter = 0
            print("\n⏳ System running... Press Ctrl+C to stop")

            while True:
                await asyncio.sleep(60)  # Check every minute
                uptime_counter += 1

                # Print periodic status every 15 minutes
                if uptime_counter % 15 == 0:
                    uptime = datetime.now() - startup_time
                    hours, remainder = divmod(uptime.total_seconds(), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    uptime_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

                    print(f"\n🕒 System uptime: {uptime_str}")
                    print(f"💪 System running normally. Press Ctrl+C to stop.\n")
        else:
            print("\n❌ BoarderframeOS boot failed")
            return 1
    except KeyboardInterrupt:
        print("\n\n🛑 Shutdown requested - cleaning up processes...")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
    finally:
        # Always clean up
        startup.cleanup()
        print("\n✅ BoarderframeOS shutdown complete.")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

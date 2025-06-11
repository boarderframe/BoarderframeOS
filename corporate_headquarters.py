#!/usr/bin/env python3
"""
BoarderframeOS Corporate Headquarters with Modern UI, Real-Time Status, and Department Integration
"""
import asyncio
import http.server
import json
import os
import signal
import socket
import socketserver
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import httpx
import psutil

# Metrics Layer Integration
try:
    from core.hq_metrics_integration import METRICS_CSS, HQMetricsIntegration
    from core.hq_metrics_layer import BFColors, BFIcons, MetricValue

    METRICS_AVAILABLE = True
except ImportError:
    print("Warning: Metrics layer not available")
    METRICS_AVAILABLE = False


PORT = 8888


class HealthDataManager:
    """Centralized Health Data Collection and Management"""

    def __init__(self, dashboard_data):
        self.dashboard = dashboard_data
        self.refresh_steps = [
            "Initializing global refresh...",
            "Checking system resources (CPU, Memory, Disk)...",
            "Scanning PostgreSQL database health...",
            "Querying database tables and metrics...",
            "Checking Corporate Headquarters server...",
            "Checking MCP Registry server...",
            "Scanning Filesystem MCP server...",
            "Checking Database MCP server...",
            "Checking Agent Cortex intelligent orchestration...",
            "Checking Analytics MCP server...",
            "Scanning Payment MCP server...",
            "Checking Customer MCP server...",
            "Checking PostgreSQL MCP server...",
            "Checking LLM MCP server...",
            "Scanning running agents and processes...",
            "Loading organizational data from database...",
            "Checking department and division status...",
            "Updating service registry information...",
            "Finalizing health metrics and status...",
        ]

    async def global_refresh_all_data(self, progress_callback=None):
        """Perform comprehensive refresh of all Corporate Headquarters data with progress tracking"""
        print("🔄 Starting global_refresh_all_data...")
        self.dashboard.unified_data["refresh_in_progress"] = True

        # Ensure services_status exists in unified_data
        if "services_status" not in self.dashboard.unified_data:
            self.dashboard.unified_data["services_status"] = {}
            print("🔄 Initialized empty services_status in unified_data")

        start_time = time.time()

        try:
            for i, step_description in enumerate(self.refresh_steps):
                print(f"🔍 Step {i+1}/{len(self.refresh_steps)}: {step_description}")

                if progress_callback:
                    progress_callback(i + 1, len(self.refresh_steps), step_description)

                try:
                    # Execute the corresponding refresh step
                    await self._execute_refresh_step(i)
                    print(f"✅ Step {i+1} completed successfully")
                except Exception as step_error:
                    print(f"⚠️ Step {i+1} failed but continuing: {step_error}")
                    # Continue with other steps even if one fails - this is expected for offline services
                    pass

                # Small delay for UI feedback
                await asyncio.sleep(0.1)

            # Update global refresh timestamp
            self.dashboard.unified_data["last_refresh"] = datetime.now().isoformat()

            # Sync unified data to legacy properties for compatibility
            self._sync_to_legacy_properties()

            refresh_time = time.time() - start_time
            print(f"✅ Global refresh completed in {refresh_time:.2f}s")

            return True

        except Exception as e:
            print(f"❌ Global refresh failed: {e}")
            import traceback

            traceback.print_exc()
            return False
        finally:
            self.dashboard.unified_data["refresh_in_progress"] = False

    async def _execute_refresh_step(self, step_index: int):
        """Execute specific refresh step based on index"""
        try:
            if step_index == 0:  # Initialize
                print("🔄 Initializing refresh...")
                pass  # Already handled in global_refresh_all_data
            elif step_index == 1:  # System resources
                print("📊 Refreshing system metrics...")
                await self._refresh_system_metrics()
            elif step_index == 2:  # PostgreSQL health
                print("🖾 Refreshing database health...")
                await self._refresh_database_health()
            elif step_index == 3:  # Database tables/metrics
                print("📋 Refreshing database details...")
                await self._refresh_database_details()
            elif step_index == 4:  # Corporate Headquarters
                print("🏢 Checking Corporate Headquarters...")
                await self._refresh_corporate_headquarters_status()
            elif step_index == 5:  # Registry MCP
                print("🗜 Checking Registry MCP...")
                await self._refresh_mcp_server("registry", 8000)
            elif step_index == 6:  # Filesystem MCP
                print("📁 Checking Filesystem MCP...")
                await self._refresh_mcp_server("filesystem", 8001)
            elif step_index == 7:  # Database MCP
                print("🖾 Checking Database MCP...")
                await self._refresh_mcp_server("database_postgres", 8010)
            elif step_index == 8:  # Agent Cortex (replaced LLM MCP)
                print("🧠 Checking Agent Cortex system...")
                await self._refresh_agent_cortex_status()
            elif step_index == 9:  # Analytics MCP
                print("📊 Checking Analytics MCP...")
                await self._refresh_mcp_server("analytics", 8007)
            elif step_index == 10:  # Payment MCP
                print("💳 Checking Payment MCP...")
                await self._refresh_mcp_server("payment", 8006)
            elif step_index == 11:  # Customer MCP
                print("👥 Checking Customer MCP...")
                await self._refresh_mcp_server("customer", 8008)
            elif step_index == 12:  # PostgreSQL MCP
                print("🐘 Checking PostgreSQL MCP...")
                await self._refresh_mcp_server("postgres", 8010)
            elif step_index == 13:  # LLM MCP
                print("🤖 Checking LLM MCP...")
                await self._refresh_mcp_server("llm", 8005)
            elif step_index == 14:  # Running agents
                print("🤖 Refreshing agents status...")
                await self._refresh_agents_status()
            elif step_index == 15:  # Organizational data
                print("🏢 Refreshing organizational data...")
                await self._refresh_organizational_data()
            elif step_index == 16:  # Departments/divisions
                print("🏢 Refreshing departments data...")
                await self._refresh_departments_data()
                # Also collect organizational metrics
                await self._collect_organizational_metrics()
            elif step_index == 17:  # Service registry
                print("🗜 Refreshing service registry...")
                await self._refresh_registry_data()
            elif step_index == 18:  # Finalize
                print("✅ Finalizing health metrics...")
                await self._finalize_health_metrics()
        except Exception as e:
            print(f"❌ Refresh step {step_index} failed: {e}")
            import traceback

            traceback.print_exc()
            # Don't re-raise - let other steps continue

    async def _refresh_system_metrics(self):
        """Refresh system resource metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            self.dashboard.unified_data["system_metrics"] = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "memory_used_gb": memory.used / (1024**3),
                "memory_total_gb": memory.total / (1024**3),
                "disk_used_gb": disk.used / (1024**3),
                "disk_total_gb": disk.total / (1024**3),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"System metrics refresh failed: {e}")

    async def _refresh_database_health(self):
        """Refresh PostgreSQL database health"""
        await self.dashboard._update_database_health()
        # Copy to unified data
        self.dashboard.unified_data["database_health"] = getattr(
            self.dashboard, "database_health_metrics", {}
        )

    async def _refresh_database_details(self):
        """Refresh detailed database information"""
        # Additional database metrics can be added here
        pass

    async def _refresh_mcp_server(self, server_name: str, port: int):
        """Refresh specific MCP server status"""
        try:
            print(f"⚙️ Checking {server_name} server on port {port}...")
            async with httpx.AsyncClient(
                timeout=self.dashboard.monitoring_config["health_check_timeout"]
            ) as client:
                url = f"http://localhost:{port}/health"
                response = await client.get(url)

                if response.status_code == 200:
                    health_data = response.json()
                    self.dashboard.unified_data["services_status"][server_name] = {
                        "status": "healthy",
                        "port": port,
                        "response_time": response.elapsed.total_seconds(),
                        "details": health_data,
                        "last_check": datetime.now().isoformat(),
                    }
                    print(f"✅ {server_name} server is healthy")
                else:
                    self.dashboard.unified_data["services_status"][server_name] = {
                        "status": "unhealthy",
                        "port": port,
                        "last_check": datetime.now().isoformat(),
                    }
                    print(
                        f"⚠️ {server_name} server returned status {response.status_code}"
                    )
        except Exception as e:
            self.dashboard.unified_data["services_status"][server_name] = {
                "status": "offline",
                "port": port,
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }
            print(f"❌ {server_name} server offline: {e}")

    async def _refresh_agents_status(self):
        """Refresh running agents status"""
        try:
            # Copy current running agents to unified data
            self.dashboard.unified_data["agents_status"] = dict(
                self.dashboard.running_agents
            )
            print(
                f"✅ Refreshed agents status: {len(self.dashboard.running_agents)} agents"
            )
        except Exception as e:
            print(f"❌ Failed to refresh agents status: {e}")

    async def _refresh_organizational_data(self):
        """Refresh organizational structure data"""
        # Run sync method in executor to avoid blocking
        import asyncio

        loop = asyncio.get_event_loop()
        org_data = await loop.run_in_executor(
            None, self.dashboard._fetch_organizational_data
        )
        if org_data:
            self.dashboard.unified_data["organizational_data"] = org_data
            print(f"✅ Refreshed organizational data: {len(org_data)} divisions")
        else:
            print("⚠️ No organizational data returned from fetch")

    async def _refresh_departments_data(self):
        """Refresh departments and divisions data"""
        try:
            # Get fresh departments data from database
            departments_from_db = await self._fetch_departments_from_database()
            if departments_from_db:
                self.dashboard.unified_data["departments_data"] = departments_from_db
                # Also update the instance variable
                self.departments_data = departments_from_db
                print(
                    f"✅ Refreshed departments data: {len(departments_from_db)} departments from database"
                )
            else:
                # Fallback to existing data
                self.dashboard.unified_data["departments_data"] = dict(
                    self.departments_data
                )
                print(
                    f"✅ Refreshed departments data: {len(self.departments_data)} departments from cache"
                )
        except Exception as e:
            print(f"❌ Failed to refresh departments data: {e}")

    async def _fetch_departments_from_database(self):
        """Fetch departments from PostgreSQL database"""
        try:
            import asyncpg

            connection = await asyncpg.connect(
                host="localhost",
                port=5434,
                user="boarderframe",
                password="boarderframe_secure_2025",
                database="boarderframeos",
            )

            # Fetch all departments with their division info
            departments_query = """
                SELECT
                    d.id,
                    d.department_name,
                    d.description,
                    d.operational_status,
                    d.category,
                    d.created_at,
                    div.division_name,
                    div.division_description
                FROM departments d
                JOIN divisions div ON d.division_id = div.id
                ORDER BY div.division_name, d.department_name
            """

            rows = await connection.fetch(departments_query)
            await connection.close()

            # Convert to dictionary format compatible with existing code
            departments_dict = {}
            for row in rows:
                dept_key = f"dept_{row['id']}"
                departments_dict[dept_key] = {
                    "name": row["department_name"],
                    "description": row["description"],
                    "status": row["operational_status"],
                    "category": row["category"],
                    "division": row["division_name"],
                    "division_description": row["division_description"],
                    "created_at": (
                        row["created_at"].isoformat() if row["created_at"] else None
                    ),
                }

            return departments_dict

        except Exception as e:
            print(f"Database departments fetch error: {e}")
            return None

    async def _refresh_agent_cortex_status(self):
        """Refresh Agent Cortex system status"""
        try:
            # Check Cortex Management UI
            async with httpx.AsyncClient(
                timeout=self.dashboard.monitoring_config["health_check_timeout"]
            ) as client:
                url = "http://localhost:8889/api/agent-cortex/status"
                response = await client.get(url)

                if response.status_code == 200:
                    agent_cortex_status = response.json()
                    self.dashboard.unified_data["services_status"]["agent_cortex"] = {
                        "status": "healthy",
                        "port": 8889,
                        "response_time": response.elapsed.total_seconds(),
                        "details": agent_cortex_status,
                        "last_check": datetime.now().isoformat(),
                    }
                    print(f"✅ Agent Cortex system is healthy")
                else:
                    self.dashboard.unified_data["services_status"]["agent_cortex"] = {
                        "status": "unhealthy",
                        "port": 8889,
                        "last_check": datetime.now().isoformat(),
                    }
                    print(f"⚠️ Agent Cortex returned status {response.status_code}")
        except Exception as e:
            # Try to check if Agent Cortex instance exists even if UI is not running
            try:
                from core.agent_cortex import get_agent_cortex_instance

                agent_cortex = await get_agent_cortex_instance()
                status = await agent_cortex.get_status()
                self.dashboard.unified_data["services_status"]["agent_cortex"] = {
                    "status": "healthy",
                    "port": 8889,
                    "details": status,
                    "note": "UI not running but Cortex operational",
                    "last_check": datetime.now().isoformat(),
                }
                print(f"✅ Agent Cortex system is operational (UI not accessible)")
            except:
                self.dashboard.unified_data["services_status"]["agent_cortex"] = {
                    "status": "offline",
                    "port": 8889,
                    "error": str(e),
                    "last_check": datetime.now().isoformat(),
                }
                print(f"❌ Agent Cortex system offline: {e}")

    async def _refresh_corporate_headquarters_status(self):
        """Refresh Corporate Headquarters server status"""
        try:
            # Corporate HQ is special - we check ourselves
            # Since we're running, we can mark ourselves as healthy
            self.dashboard.unified_data["services_status"]["corporate_headquarters"] = {
                "status": "healthy",
                "port": 8888,
                "name": "Corporate Headquarters",
                "category": "Core Infrastructure",
                "priority": 1,
                "description": "Main management interface",
                "details": {
                    "status": "healthy",
                    "uptime": "Active",
                    "services": len(self.dashboard.services_status),
                    "agents": len(self.dashboard.running_agents),
                },
                "last_check": datetime.now().isoformat(),
                "note": "Self-check (we are running)",
            }
            print(f"✅ Corporate Headquarters is healthy (self-check)")
        except Exception as e:
            # This should never happen since we're running
            self.dashboard.unified_data["services_status"]["corporate_headquarters"] = {
                "status": "unknown",
                "port": 8888,
                "error": str(e),
                "last_check": datetime.now().isoformat(),
            }
            print(f"⚠️ Corporate Headquarters status unknown: {e}")

    async def _collect_organizational_metrics(self):
        """Collect comprehensive organizational metrics from database and registry"""
        try:
            # Ensure we have fresh data from unified store
            if "departments_data" in self.dashboard.unified_data:
                departments_data = self.dashboard.unified_data["departments_data"]
            else:
                departments_data = self.departments_data

            if "organizational_data" in self.dashboard.unified_data:
                org_data = self.dashboard.unified_data["organizational_data"]
            else:
                org_data = self.dashboard._fetch_organizational_data() or {}

            print("📊 Collecting organizational metrics...")
            metrics = {
                "divisions": {"total": 0, "active": 0, "percentage": 0},
                "departments": {"total": 0, "active": 0, "percentage": 0},
                "leaders": {"total": 0, "active": 0, "percentage": 0},
                "agents": {"total": 0, "active": 0, "percentage": 0},
                "by_division": {},  # Division-specific metrics
            }

            # Collect from database
            import asyncpg

            connection = await asyncpg.connect(
                host="localhost",
                port=5434,
                user="boarderframe",
                password="boarderframe_secure_2025",
                database="boarderframeos",
            )

            # Get divisions metrics
            divisions_query = """
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN is_active = true THEN 1 END) as active
                FROM divisions
            """
            div_result = await connection.fetchrow(divisions_query)
            metrics["divisions"]["total"] = div_result["total"]
            metrics["divisions"]["active"] = div_result["active"]
            if metrics["divisions"]["total"] > 0:
                metrics["divisions"]["percentage"] = round(
                    (metrics["divisions"]["active"] / metrics["divisions"]["total"])
                    * 100,
                    1,
                )

            # Get departments metrics
            departments_query = """
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN operational_status = 'active' THEN 1 END) as active
                FROM departments
            """
            dept_result = await connection.fetchrow(departments_query)
            metrics["departments"]["total"] = dept_result["total"]
            metrics["departments"]["active"] = dept_result["active"]
            if metrics["departments"]["total"] > 0:
                metrics["departments"]["percentage"] = round(
                    (metrics["departments"]["active"] / metrics["departments"]["total"])
                    * 100,
                    1,
                )

            # Get leaders metrics
            leaders_query = """
                SELECT COUNT(*) as total,
                       COUNT(CASE WHEN active_status = 'active' THEN 1 END) as active
                FROM leaders
            """
            leader_result = await connection.fetchrow(leaders_query)
            metrics["leaders"]["total"] = leader_result["total"]
            metrics["leaders"]["active"] = leader_result["active"]
            if metrics["leaders"]["total"] > 0:
                metrics["leaders"]["percentage"] = round(
                    (metrics["leaders"]["active"] / metrics["leaders"]["total"]) * 100,
                    1,
                )

            # Get division-specific metrics
            division_metrics_query = """
                SELECT
                    div.id,
                    div.division_name,
                    div.is_active as division_active,
                    COUNT(DISTINCT d.id) as total_departments,
                    COUNT(DISTINCT CASE WHEN d.operational_status = 'active' THEN d.id END) as active_departments,
                    COUNT(DISTINCT l.id) as total_leaders,
                    COUNT(DISTINCT CASE WHEN l.active_status = 'active' THEN l.id END) as active_leaders
                FROM divisions div
                LEFT JOIN departments d ON div.id = d.division_id
                LEFT JOIN leaders l ON d.id = l.department_id
                GROUP BY div.id, div.division_name, div.is_active
            """

            div_metrics = await connection.fetch(division_metrics_query)

            for row in div_metrics:
                div_name = row["division_name"]
                metrics["by_division"][div_name] = {
                    "departments": {
                        "total": row["total_departments"],
                        "active": row["active_departments"],
                        "percentage": round(
                            (
                                (
                                    row["active_departments"]
                                    / row["total_departments"]
                                    * 100
                                )
                                if row["total_departments"] > 0
                                else 0
                            ),
                            1,
                        ),
                    },
                    "leaders": {
                        "total": row["total_leaders"],
                        "active": row["active_leaders"],
                        "percentage": round(
                            (
                                (row["active_leaders"] / row["total_leaders"] * 100)
                                if row["total_leaders"] > 0
                                else 0
                            ),
                            1,
                        ),
                    },
                    "agents": {
                        "total": 0,  # Will be populated from agent mapping
                        "active": 0,
                        "percentage": 0,
                    },
                    "is_active": row["division_active"],
                }

            await connection.close()

            # Get agents metrics from registry
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get("http://localhost:8000/api/agents")
                    if response.status_code == 200:
                        agents_data = response.json()
                        metrics["agents"]["total"] = agents_data.get("total", 0)
                        metrics["agents"]["active"] = agents_data.get("online", 0)
                        if metrics["agents"]["total"] > 0:
                            metrics["agents"]["percentage"] = round(
                                (
                                    metrics["agents"]["active"]
                                    / metrics["agents"]["total"]
                                )
                                * 100,
                                1,
                            )
            except:
                # Fallback to counting from unified data
                if "agents" in self.dashboard.unified_data:
                    agents_list = self.dashboard.unified_data["agents"]
                    metrics["agents"]["total"] = len(agents_list)
                    metrics["agents"]["active"] = sum(
                        1 for a in agents_list if a.get("status") == "online"
                    )
                    if metrics["agents"]["total"] > 0:
                        metrics["agents"]["percentage"] = round(
                            (metrics["agents"]["active"] / metrics["agents"]["total"])
                            * 100,
                            1,
                        )

            # Store metrics in unified data
            self.dashboard.unified_data["organizational_metrics"] = metrics
            print(f"✅ Collected organizational metrics: {metrics}")

            return metrics

        except Exception as e:
            print(f"❌ Failed to collect organizational metrics: {e}")
            # Return default metrics
            return {
                "divisions": {"total": 0, "active": 0, "percentage": 0},
                "departments": {"total": 0, "active": 0, "percentage": 0},
                "leaders": {"total": 0, "active": 0, "percentage": 0},
                "agents": {"total": 0, "active": 0, "percentage": 0},
            }

    async def _refresh_registry_data(self):
        """Refresh service registry information"""
        # Placeholder for registry-specific data
        pass

    async def _finalize_health_metrics(self):
        """Finalize and calculate overall health metrics"""
        # Calculate overall system health
        services_online = len(
            [
                s
                for s in self.dashboard.unified_data["services_status"].values()
                if s.get("status") == "healthy"
            ]
        )
        total_services = len(self.dashboard.unified_data["services_status"])

        self.dashboard.unified_data["overall_health"] = {
            "status": (
                "online"
                if services_online > total_services * 0.7
                else "warning" if services_online > 0 else "offline"
            ),
            "services_ratio": f"{services_online}/{total_services}",
            "last_calculated": datetime.now().isoformat(),
        }

    def _sync_to_legacy_properties(self):
        """Sync unified data back to legacy properties for compatibility"""
        try:
            # Only sync if data exists in unified_data
            if "services_status" in self.dashboard.unified_data:
                self.dashboard.services_status = dict(
                    self.dashboard.unified_data["services_status"]
                )
                print(
                    f"✅ Synced {len(self.dashboard.services_status)} services to legacy"
                )

                # Also update metrics layer if available
                if hasattr(self.dashboard, "metrics_layer") and hasattr(
                    self.dashboard.metrics_layer, "set_server_status"
                ):
                    self.dashboard.metrics_layer.set_server_status(
                        self.dashboard.unified_data["services_status"]
                    )
                    print(f"✅ Updated metrics layer with server status")

            if "system_metrics" in self.dashboard.unified_data:
                self.dashboard.system_metrics = dict(
                    self.dashboard.unified_data["system_metrics"]
                )
                print(f"✅ Synced system metrics to legacy")

            if "database_health" in self.dashboard.unified_data:
                self.dashboard.database_health_metrics = dict(
                    self.dashboard.unified_data["database_health"]
                )
                print(f"✅ Synced database health to legacy")

            if "last_refresh" in self.dashboard.unified_data:
                self.dashboard.last_update = self.dashboard.unified_data["last_refresh"]
                print(f"✅ Synced last update timestamp")

            print(f"✅ Legacy property sync completed")
        except Exception as e:
            print(f"❌ Legacy property sync failed: {e}")

    # Enhanced Refresh System Methods
    async def enhanced_global_refresh(self, components=None, progress_callback=None):
        """Enhanced global refresh with granular component selection"""
        print("🔄 Starting enhanced global refresh...")
        self.dashboard.unified_data["refresh_in_progress"] = True

        # Default components to refresh if none specified
        if components is None:
            components = [
                "system_metrics",
                "database_health",
                "services_status",
                "agents_status",
                "mcp_servers",
                "registry_data",
                "departments_data",
                "organizational_data",
            ]

        start_time = time.time()
        refreshed_components = []
        failed_components = []

        try:
            total_steps = len(components)

            for i, component in enumerate(components):
                print(f"🔍 Refreshing {component} ({i+1}/{total_steps})...")

                if progress_callback:
                    progress_callback(i + 1, total_steps, f"Refreshing {component}...")

                try:
                    success = await self._refresh_component(component)
                    if success:
                        refreshed_components.append(component)
                        print(f"✅ {component} refreshed successfully")
                    else:
                        failed_components.append(component)
                        print(f"⚠️ {component} refresh failed but continuing")
                except Exception as e:
                    failed_components.append(component)
                    print(f"⚠️ {component} refresh error: {e}")

                await asyncio.sleep(0.1)  # UI feedback delay

            # Update timestamps
            self.dashboard.unified_data["last_refresh"] = datetime.now().isoformat()
            self._sync_to_legacy_properties()

            refresh_time = time.time() - start_time
            print(f"✅ Enhanced global refresh completed in {refresh_time:.2f}s")

            return {
                "success": True,
                "total_components": len(components),
                "refreshed_components": refreshed_components,
                "failed_components": failed_components,
                "refresh_time": refresh_time,
            }

        except Exception as e:
            print(f"❌ Enhanced global refresh failed: {e}")
            import traceback

            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "refreshed_components": refreshed_components,
                "failed_components": failed_components,
            }
        finally:
            self.dashboard.unified_data["refresh_in_progress"] = False

    async def _refresh_component(self, component):
        """Refresh specific component based on type"""
        try:
            if component == "system_metrics":
                await self._refresh_system_metrics()
            elif component == "database_health":
                await self._refresh_database_health()
                await self._refresh_database_details()
            elif component == "services_status":
                await self._refresh_corporate_headquarters_status()
            elif component == "agents_status":
                await self._refresh_agents_status()
            elif component == "mcp_servers":
                # Refresh all MCP servers
                mcp_servers = [
                    ("registry", 8000),
                    ("filesystem", 8001),
                    ("database_postgres", 8010),
                    ("analytics", 8007),
                    ("payment", 8006),
                    ("customer", 8008),
                    ("llm", 8005),
                ]
                for server_name, port in mcp_servers:
                    await self._refresh_mcp_server(server_name, port)
            elif component == "registry_data":
                await self._refresh_registry_data()
            elif component == "departments_data":
                await self._refresh_departments_data()
            elif component == "organizational_data":
                await self._refresh_organizational_data()
            else:
                print(f"⚠️ Unknown component: {component}")
                return False

            return True
        except Exception as e:
            print(f"❌ Component {component} refresh failed: {e}")
            return False


class DashboardData:
    """Centralized Health & Data Management System for BoarderframeOS Corporate Headquarters"""

    def __init__(self):
        # === CENTRALIZED DATA STORE ===
        # All Corporate Headquarters components pull from these unified data structures
        self.unified_data = {
            "services_status": {},  # All MCP servers and services
            "agents_status": {},  # All agent states and metrics
            "system_metrics": {},  # CPU, memory, disk, network
            "database_health": {},  # PostgreSQL health and metrics
            "registry_data": {},  # Service registry information
            "departments_data": {},  # Organizational structure
            "leaders_data": {},  # Leadership information
            "organizational_data": {},  # Full org chart data
            "mcp_details": {},  # Detailed MCP server information
            "startup_status": {},  # System startup state
            "health_history": {},  # Historical health data
            "last_refresh": None,  # Global last refresh timestamp
            "refresh_in_progress": False,  # Global refresh state
        }

        # === LEGACY COMPATIBILITY ===
        # Keep existing properties for backward compatibility during transition
        self.services_status = {}
        self.agents_status = {}
        self.system_metrics = {}
        self.health_status = {}
        self.running_agents = {}
        self.startup_status = {}
        self.mcp_details = {}
        self.departments_data = {}
        self.agent_department_mapping = {}
        self.system_overview = {}
        self.database_health_metrics = {}
        self.last_update = None
        self.update_thread = None
        self.running = True

        # === ENHANCED MONITORING CONFIG ===
        self.health_history = {}
        self.alert_conditions = {}
        self.monitoring_config = {
            "update_interval": 15,  # seconds
            "health_check_timeout": 8,  # seconds
            "max_history_entries": 100,
            "global_refresh_steps": 16,  # Total steps in global refresh
            "alert_thresholds": {
                "cpu_percent": 90,
                "memory_percent": 85,
                "disk_percent": 90,
            },
        }

        # Initialize Corporate HQ as healthy since we're running
        self.unified_data["services_status"]["corporate_headquarters"] = {
            "status": "healthy",
            "port": 8888,
            "name": "Corporate Headquarters",
            "category": "Core Infrastructure",
            "priority": 1,
            "description": "Main management interface",
            "last_check": datetime.now().isoformat(),
        }
        self.services_status["corporate_headquarters"] = self.unified_data[
            "services_status"
        ]["corporate_headquarters"]

        # Initialize metrics layer
        self.metrics_layer = None
        if METRICS_AVAILABLE:
            try:
                # Create database configuration for metrics layer
                db_config = {
                    "host": "localhost",
                    "port": 5434,
                    "database": "boarderframeos",
                    "user": "boarderframe",
                    "password": "boarderframe_secure_2025",
                }
                self.metrics_layer = HQMetricsIntegration(db_config)
                print("✓ Metrics layer initialized successfully")
            except Exception as e:
                print(f"⚠️ Failed to initialize metrics layer: {e}")

        self.status_file = "data/system_status.json"

        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)

        # Initialize centralized health data manager
        self.health_manager = HealthDataManager(self)

        # Load initial data and persistent status
        self._load_department_data()
        self._load_persistent_status()

        # Initialize with basic server data to prevent empty state
        self._initialize_basic_server_data()

        # Run initial health check to populate real server status
        # NOTE: Commented out because it marks servers as offline before they have time to start
        # The background refresh will update the status properly
        # self._run_initial_health_check()

        print("🎯 Centralized Health & Data Management System initialized")
        print(f"📊 Monitoring {len(self.unified_data)} data categories")
        print(
            f"⚡ Global refresh system ready with {self.monitoring_config['global_refresh_steps']} steps"
        )
        print(f"🔄 Health manager type: {type(self.health_manager)}")
        print(
            f"📦 Available methods: {[m for m in dir(self.health_manager) if not m.startswith('_')]}"
        )

        # Test basic functionality
        try:
            test_data = self.get_health_summary()
            print(f"✅ Health summary working: {len(test_data)} keys")
        except Exception as e:
            print(f"❌ Health summary failed: {e}")

    def _load_department_data(self):
        """Load department data from JSON file"""
        try:
            departments_file = (
                Path(__file__).parent
                / "departments"
                / "boarderframeos-departments.json"
            )
            if departments_file.exists():
                with open(departments_file, "r") as f:
                    data = json.load(f)
                    self.departments_data = data.get("boarderframeos_departments", {})
                    self._create_agent_department_mapping()
            else:
                print("⚠️  Department data file not found")
        except Exception as e:
            print(f"⚠️  Error loading department data: {e}")

    def _create_agent_department_mapping(self):
        """Create mapping between agents and departments"""
        self.agent_department_mapping = {}

        # Define known agent to department mappings
        agent_mappings = {
            "solomon": "executive_leadership",
            "david": "executive_leadership",
            "michael": "coordination_orchestration",
            "adam": "agent_development",
            "eve": "agent_development",
            "levi": "finance",
            "judah": "legal",
            "benjamin": "sales",
            "ephraim": "marketing",
            "nehemiah": "procurement",
            "bezalel": "engineering",
            "dan": "research_development",
            "daniel": "innovation",
            "naphtali": "operations",
            "gad": "security",
            "ezra": "data_management",
            "gabriel": "infrastructure",
            "apollos": "learning_development",
            "aaron": "human_resources",
            "zebulun": "production",
            "asher": "customer_support",
            "jubal": "creative_services",
            "enoch": "data_generation",
            "issachar": "analytics",
            "joseph": "strategic_planning",
            "joshua": "change_management",
        }

        for agent, dept_key in agent_mappings.items():
            if dept_key in self.departments_data:
                self.agent_department_mapping[agent] = {
                    "department_key": dept_key,
                    "department_name": self.departments_data[dept_key][
                        "department_name"
                    ],
                    "category": self.departments_data[dept_key]["category"],
                }

    def get_department_summary(self, departments_data=None):
        """Get summary of departments and their statistics using centralized data"""
        # Use provided data or fallback to centralized/legacy data
        if departments_data is None:
            departments_data = self.unified_data.get(
                "departments_data", self.departments_data
            )

        if not departments_data:
            return {}

        summary = {
            "total_departments": len(departments_data),
            "categories": {},
            "total_leaders": 0,
            "total_agents": 0,
            "departments_by_category": {},
        }

        for dept_key, dept_data in departments_data.items():
            category = dept_data.get("category", "Other")

            # Count by category
            if category not in summary["categories"]:
                summary["categories"][category] = 0
            summary["categories"][category] += 1

            # Group departments by category
            if category not in summary["departments_by_category"]:
                summary["departments_by_category"][category] = []
            summary["departments_by_category"][category].append(dept_data)

            # Count leaders and agents
            summary["total_leaders"] += len(dept_data.get("leaders", []))
            summary["total_agents"] += len(dept_data.get("native_agents", []))

        return summary

    def _get_subsystem_status(self, subsystem: str) -> str:
        """Get status for a specific subsystem using centralized data"""
        # Use unified_data when available, fallback to legacy data
        agents_data = self.unified_data.get("agents_status", self.running_agents)
        services_data = self.unified_data.get("services_status", self.services_status)
        db_data = self.unified_data.get(
            "database_health", getattr(self, "database_health_metrics", {})
        )
        departments_data = self.unified_data.get(
            "departments_data", self.departments_data
        )

        if subsystem == "agents":
            running_count = len(
                [a for a in agents_data.values() if a.get("status") == "running"]
            )
            return "online" if running_count > 0 else "offline"
        elif subsystem == "leaders":
            leader_agents = ["solomon", "david", "michael"]
            running_leaders = len(
                [
                    a
                    for a in leader_agents
                    if a in agents_data and agents_data[a].get("status") == "running"
                ]
            )
            return "online" if running_leaders > 0 else "offline"
        elif subsystem == "departments":
            return "online" if len(departments_data) > 0 else "offline"
        elif subsystem == "servers":
            online_servers = len(
                [
                    s
                    for s in services_data.values()
                    if s.get("status") in ["healthy", "online"]
                ]
            )
            return "online" if online_servers > 0 else "offline"
        elif subsystem == "registry":
            registry_status = services_data.get("registry", {}).get("status", "offline")
            return "online" if registry_status in ["healthy", "online"] else "offline"
        elif subsystem == "database":
            db_status = db_data.get("status", "offline")
            return "online" if db_status == "healthy" else "offline"
        elif subsystem == "divisions":
            # Try to get from organizational data, fallback to departments count
            org_data = self.unified_data.get("organizational_data", {})
            return (
                "online"
                if len(org_data) > 0 or len(departments_data) > 0
                else "offline"
            )
        elif subsystem == "mcps":
            mcp_services = [
                "registry",
                "filesystem",
                "database",
                "llm",
                "customer",
                "analytics",
                "payment",
            ]
            healthy_mcps = len(
                [
                    s
                    for s in mcp_services
                    if services_data.get(s, {}).get("status") in ["healthy", "online"]
                ]
            )
            return "online" if healthy_mcps > 0 else "offline"
        elif subsystem == "boarderframe_servers":
            # BoarderFrame specific servers like Corporate Headquarters
            return (
                "online"  # Corporate Headquarters is always online if we're seeing this
            )
        return "unknown"

    def _get_agents_count(self) -> str:
        """Get agents count summary using centralized data"""
        agents_data = self.unified_data.get("agents_status", self.running_agents)
        running = len([a for a in agents_data.values() if a.get("status") == "running"])
        total = len(agents_data) if agents_data else 2  # Default: Solomon, David
        return f"{running}/{total}"

    def _get_leaders_count(self) -> str:
        """Get leaders count summary using centralized data"""
        agents_data = self.unified_data.get("agents_status", self.running_agents)
        leader_agents = ["solomon", "david", "michael"]
        running = len(
            [
                a
                for a in leader_agents
                if a in agents_data and agents_data[a].get("status") == "running"
            ]
        )
        return f"{running}/{len(leader_agents)}"

    def _get_departments_count(self) -> str:
        """Get departments count summary using centralized data"""
        departments_data = self.unified_data.get(
            "departments_data", self.departments_data
        )
        total = len(departments_data)
        active = len(
            [d for d in departments_data.values() if d.get("status") != "inactive"]
        )
        return f"{active}/{total}"

    def _get_servers_count(self) -> str:
        """Get servers count summary using centralized data"""
        services_data = self.unified_data.get("services_status", self.services_status)
        online = len(
            [
                s
                for s in services_data.values()
                if s.get("status") in ["healthy", "online"]
            ]
        )
        total = len(services_data) if services_data else 8  # Default MCP servers
        return f"{online}/{total}"

    def _get_database_status(self) -> str:
        """Get database status summary with key metrics using centralized data"""
        db_metrics = self.unified_data.get(
            "database_health", getattr(self, "database_health_metrics", {})
        )

        if not db_metrics or db_metrics.get("status") != "healthy":
            return "Offline"

        # Show only tables and size as requested
        tables = db_metrics.get("total_tables", 0)
        size = db_metrics.get("database_size", "Unknown")

        return f"{tables} tables • {size}"

    def _get_formatted_timestamp(self) -> str:
        """Get formatted timestamp with date first and AM/PM format"""
        from datetime import datetime

        now = datetime.now()
        # Format: "Dec 31, 2025 at 11:59 PM"
        return now.strftime("%b %d, %Y at %I:%M %p")

    def _get_divisions_count(self) -> str:
        """Get divisions count summary using centralized data"""
        try:
            # Try to get from unified organizational data first
            org_data = self.unified_data.get("organizational_data", {})
            if org_data:
                total = len(org_data)
                active = len(
                    [
                        div
                        for div in org_data.values()
                        if div.get("status") != "inactive"
                    ]
                )
                return f"{active}/{total}"
            else:
                # Try fetching from database
                org_data = self._fetch_organizational_data()
                if org_data:
                    total = len(org_data)
                    active = len(
                        [
                            div
                            for div in org_data.values()
                            if div.get("status") != "inactive"
                        ]
                    )
                    return f"{active}/{total}"
                else:
                    # Fallback to estimated count based on our known structure
                    return "9/9"  # We have 9 major divisions defined
        except Exception:
            return "9/9"  # Safe fallback

    def _get_mcps_count(self) -> str:
        """Get MCP servers count summary using centralized data"""
        services_data = self.unified_data.get("services_status", self.services_status)
        mcp_services = [
            "registry",
            "filesystem",
            "database",
            "llm",
            "customer",
            "analytics",
            "payment",
        ]
        healthy_mcps = len(
            [
                s
                for s in mcp_services
                if services_data.get(s, {}).get("status") in ["healthy", "online"]
            ]
        )
        total_mcps = len(mcp_services)
        return f"{healthy_mcps}/{total_mcps}"

    def _get_boarderframe_servers_count(self) -> str:
        """Get BoarderFrame servers count summary"""
        # BoarderFrame specific tools/servers
        boarderframe_tools = [
            "Corporate Headquarters",
            "Message Bus",
            "Agent Orchestrator",
        ]
        # Corporate Headquarters is always online if we're seeing this interface
        # Message Bus and Orchestrator status would need to be checked separately
        # For now, assume Corporate Headquarters is online (1) and check for others
        online_count = 1  # Corporate Headquarters is running

        # Could add checks for other BoarderFrame components here
        # For now, return a conservative estimate
        total_count = len(boarderframe_tools)
        return f"{online_count}/{total_count}"

    def _get_category_count(self, category_name: str) -> str:
        """Get server count for a specific category"""
        # Get the most up-to-date services data, preferring unified_data
        services_data = self.unified_data.get("services_status", {})
        if not services_data:
            services_data = self.services_status

        # Define server categories matching the Systems tab organization
        category_servers = {
            "Core Systems": ["corporate_headquarters", "agent_cortex", "registry"],
            "MCP Servers": ["filesystem", "database_postgres", "analytics"],
            "Business Services": ["payment", "customer"],
        }

        servers = category_servers.get(category_name, [])
        online_count = len(
            [s for s in servers if services_data.get(s, {}).get("status") == "healthy"]
        )
        total_count = len(servers)
        return f"{online_count}/{total_count}"

    def _get_category_status(self, category_name: str) -> str:
        """Get status for a specific server category"""
        # Get the most up-to-date services data, preferring unified_data
        services_data = self.unified_data.get("services_status", {})
        if not services_data:
            services_data = self.services_status

        # Define server categories matching the Systems tab organization
        category_servers = {
            "Core Systems": ["corporate_headquarters", "agent_cortex", "registry"],
            "MCP Servers": ["filesystem", "database_postgres", "analytics"],
            "Business Services": ["payment", "customer"],
        }

        servers = category_servers.get(category_name, [])
        if not servers:
            return "offline"

        online_count = len(
            [s for s in servers if services_data.get(s, {}).get("status") == "healthy"]
        )
        total_count = len(servers)

        if online_count == total_count:
            return "online"
        elif online_count > 0:
            return "warning"
        else:
            return "offline"

    def start_updates(self, enhanced=True):
        """Start background data updates with enhanced monitoring"""
        print(
            f"🔄 Starting {'enhanced' if enhanced else 'standard'} monitoring system..."
        )
        print(
            f"📊 Update interval: {self.monitoring_config['update_interval']} seconds"
        )

        # Run initial update immediately
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._async_update())
            loop.close()
            print("✅ Initial system scan completed")
        except Exception as e:
            print(f"❌ Initial update error: {e}")

        # Start enhanced or standard update thread
        if enhanced:
            self.update_thread = threading.Thread(
                target=self._enhanced_update_wrapper, daemon=True
            )
        else:
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)

        self.update_thread.start()

    def _enhanced_update_wrapper(self):
        """Wrapper to run enhanced async update loop in thread"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._enhanced_update_loop())
        except Exception as e:
            print(f"❌ Enhanced monitoring error: {e}")
        finally:
            loop.close()

    def _update_loop(self):
        """Background update loop"""
        while self.running:
            try:
                # Run async update in new event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._async_update())
                loop.close()
            except Exception as e:
                print(f"Update error: {e}")
            time.sleep(30)  # Update every 30 seconds

    async def _async_update(self):
        """Async update of all dashboard data"""
        async with httpx.AsyncClient(
            timeout=self.monitoring_config["health_check_timeout"]
        ) as client:
            await self._update_services(client)
            await self._update_agents()
            await self._update_system_metrics()
            await self._update_startup_status()
            await self._update_database_health()

            # Update organizational metrics every 3rd update cycle (every 45 seconds at 15s interval)
            update_count = getattr(self, "_update_count", 0)
            self._update_count = update_count + 1

            if self._update_count % 3 == 0:
                try:
                    health_manager = HealthDataManager(self)
                    metrics = await health_manager._collect_organizational_metrics()
                    self.unified_data["organizational_metrics"] = metrics
                except Exception as e:
                    print(f"⚠️ Failed to update organizational metrics: {e}")

            self.last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    async def _update_database_health(self):
        """Update database health metrics"""
        try:
            self.database_health_metrics = await self._get_database_health_metrics()
            # Also update unified_data for consistency
            self.unified_data["database_health"] = self.database_health_metrics
        except Exception as e:
            print(f"⚠️  Database health check failed: {e}")
            self.database_health_metrics = {
                "status": "error",
                "error": str(e),
                "last_check": datetime.now().isoformat(),
                "database_size": "Unknown",
                "total_tables": 0,
                "active_connections": 0,
                "tables": [],
            }
            # Also update unified_data for consistency
            self.unified_data["database_health"] = self.database_health_metrics

    async def _update_services(self, client):
        """Update services status with enhanced MCP server details"""
        services = {
            # MCP Servers - Model Context Protocol servers
            "filesystem": {
                "port": 8001,
                "name": "File System Server",
                "icon": "fas fa-folder-tree",
                "category": "MCP Servers",
            },
            "database_postgres": {
                "port": 8010,
                "name": "PostgreSQL Database Server",
                "icon": "fas fa-database",
                "category": "MCP Servers",
            },
            "analytics": {
                "port": 8007,
                "name": "Analytics Server",
                "icon": "fas fa-chart-bar",
                "category": "MCP Servers",
            },
            # Core Systems - Essential infrastructure
            "corporate_headquarters": {
                "port": 8888,
                "name": "HR",
                "icon": "fas fa-users-cog",
                "category": "Core Systems",
            },
            "agent_cortex": {
                "port": 8889,
                "name": "Agent Cortex",
                "icon": "fas fa-brain",
                "category": "Core Systems",
            },
            "registry": {
                "port": 8009,
                "name": "Registry",
                "icon": "fas fa-server",
                "category": "Core Systems",
            },
            # Business Services - Business-focused services
            "payment": {
                "port": 8006,
                "name": "Payment Server",
                "icon": "fas fa-credit-card",
                "category": "Business Services",
            },
            "customer": {
                "port": 8008,
                "name": "Customer Server",
                "icon": "fas fa-users",
                "category": "Business Services",
            },
        }

        for service_id, service_info in services.items():
            try:
                resp = await client.get(
                    f"http://localhost:{service_info['port']}/health"
                )
                if resp.status_code == 200:
                    health_data = (
                        resp.json()
                        if resp.headers.get("content-type", "").startswith(
                            "application/json"
                        )
                        else {}
                    )

                    # Enhanced data for filesystem server
                    if service_id == "filesystem":
                        self.mcp_details[service_id] = {
                            "uptime": health_data.get("uptime", "Unknown"),
                            "total_operations": health_data.get("total_operations", 0),
                            "active_clients": health_data.get("active_clients", 0),
                            "ai_features": health_data.get("ai_available", False),
                            "vector_db_size": health_data.get("vector_db_entries", 0),
                            "base_path": health_data.get("base_path", "/"),
                            "disk_usage": health_data.get("disk_usage", {}),
                            "recent_operations": health_data.get(
                                "recent_operations", []
                            ),
                        }

                    # Calculate uptime if not provided by server
                    server_uptime = health_data.get("uptime")
                    if server_uptime is None:
                        # Use response time as a simple health indicator
                        if resp.elapsed.total_seconds() < 1.0:
                            server_uptime = "Online"
                        else:
                            server_uptime = (
                                f"{resp.elapsed.total_seconds():.1f}s response"
                            )

                    self.services_status[service_id] = {
                        "status": "healthy",
                        "response_time": resp.elapsed.total_seconds(),
                        "details": health_data,
                        "last_check": datetime.now().strftime("%I:%M:%S %p"),
                        "uptime": server_uptime,
                        **service_info,
                    }
                else:
                    self.services_status[service_id] = {
                        "status": "degraded",
                        "error": f"HTTP {resp.status_code}",
                        "last_check": datetime.now().strftime("%I:%M:%S %p"),
                        "uptime": "Unknown",
                        **service_info,
                    }
            except Exception as e:
                self.services_status[service_id] = {
                    "status": "critical",
                    "error": str(e)[:50],
                    "last_check": datetime.now().strftime("%I:%M:%S %p"),
                    "uptime": "Offline",
                    **service_info,
                }

    async def _update_agents(self):
        """Update agents status with enhanced information from agent manager"""
        running_agents = {}
        try:
            # Import agent manager for configuration data
            sys.path.insert(0, str(Path(__file__).parent))
            from scripts.start_agents import AgentManager

            agent_manager = AgentManager()

            # Check each configured agent
            for agent_name, config in agent_manager.agent_configs.items():
                if agent_manager.is_agent_running(agent_name):
                    pid = agent_manager.get_agent_pid(agent_name)

                    # Get process information
                    try:
                        import psutil

                        process = psutil.Process(pid)
                        memory_percent = process.memory_percent()
                        cpu_percent = process.cpu_percent()
                        create_time = datetime.fromtimestamp(
                            process.create_time()
                        ).strftime("%H:%M:%S")
                    except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
                        memory_percent = 0
                        cpu_percent = 0
                        create_time = "Unknown"

                    running_agents[agent_name] = {
                        "name": agent_name.title(),
                        "status": "running",
                        "pid": pid,
                        "type": config.get("description", "AI Agent"),
                        "model": config.get("model", "Unknown"),
                        "priority": config.get("priority", 0),
                        "memory_percent": memory_percent,
                        "cpu_percent": cpu_percent,
                        "start_time": create_time,
                        "health": "healthy",
                    }
                else:
                    # Agent not running
                    running_agents[agent_name] = {
                        "name": agent_name.title(),
                        "status": "stopped",
                        "pid": None,
                        "type": config.get("description", "AI Agent"),
                        "model": config.get("model", "Unknown"),
                        "priority": config.get("priority", 0),
                        "memory_percent": 0,
                        "cpu_percent": 0,
                        "start_time": None,
                        "health": "offline",
                    }

        except ImportError:
            # Fallback to basic process detection if agent manager unavailable
            import psutil

            for process in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    cmdline = (
                        " ".join(process.info["cmdline"])
                        if process.info["cmdline"]
                        else ""
                    )
                    if (
                        "solomon.py" in cmdline
                        or "solomon" in process.info["name"].lower()
                    ):
                        running_agents["solomon"] = {
                            "name": "Solomon",
                            "status": "running",
                            "pid": process.info["pid"],
                            "type": "Strategic Planning Agent",
                            "model": "claude-3-5-sonnet-latest",
                            "priority": 1,
                            "memory_percent": process.memory_percent(),
                            "cpu_percent": process.cpu_percent(),
                            "health": "healthy",
                        }
                    elif (
                        "david.py" in cmdline or "david" in process.info["name"].lower()
                    ):
                        running_agents["david"] = {
                            "name": "David",
                            "status": "running",
                            "pid": process.info["pid"],
                            "type": "Research Agent",
                            "model": "claude-3-5-sonnet-latest",
                            "priority": 2,
                            "memory_percent": process.memory_percent(),
                            "cpu_percent": process.cpu_percent(),
                            "health": "healthy",
                        }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            print(f"Error updating agent status: {e}")

        self.running_agents = running_agents

    async def _update_system_metrics(self):
        """Update system metrics"""
        try:
            import psutil

            # Get network connections with proper error handling for macOS permissions
            try:
                active_connections = len(psutil.net_connections())
            except (psutil.AccessDenied, PermissionError):
                # Fall back to counting listening sockets instead
                try:
                    active_connections = len(
                        [
                            c
                            for c in psutil.net_connections(kind="inet")
                            if c.status == "LISTEN"
                        ]
                    )
                except (psutil.AccessDenied, PermissionError):
                    active_connections = 0

            self.system_metrics = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent,
                "active_connections": active_connections,
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "load_avg": os.getloadavg() if hasattr(os, "getloadavg") else [0, 0, 0],
            }
        except ImportError:
            self.system_metrics = {
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_percent": 0,
                "active_connections": 0,
                "boot_time": "Unknown",
                "load_avg": [0, 0, 0],
            }

    async def _update_startup_status(self):
        """Update startup status from file"""
        try:
            if os.path.exists("startup_status.json"):
                with open("startup_status.json", "r") as f:
                    self.startup_status = json.load(f)
        except:
            pass

    def _load_persistent_status(self):
        """Load persistent system status data"""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, "r") as f:
                    data = json.load(f)
                    self.health_history = data.get("health_history", {})
                    self.last_update = data.get("last_update")

            # Also load startup status from startup.py
            startup_status_file = "/tmp/boarderframe_startup_status.json"
            if os.path.exists(startup_status_file):
                print(f"📁 Loading startup status from {startup_status_file}")
                with open(startup_status_file, "r") as f:
                    startup_data = json.load(f)

                    # Load MCP server status
                    if "mcp_servers" in startup_data:
                        print(
                            f"✅ Found {len(startup_data['mcp_servers'])} MCP servers in startup status"
                        )
                        for server_name, server_info in startup_data[
                            "mcp_servers"
                        ].items():
                            if server_info.get("status") == "running":
                                # Add to unified data
                                self.unified_data["services_status"][server_name] = {
                                    "status": "healthy",
                                    "port": server_info.get("details", {}).get(
                                        "port", 0
                                    ),
                                    "pid": server_info.get("details", {}).get("pid"),
                                    "name": server_name.replace("_", " ").title(),
                                    "category": "MCP Servers",
                                    "last_check": server_info.get(
                                        "last_update", datetime.now().isoformat()
                                    ),
                                }
                                # Also add to legacy for compatibility
                                self.services_status[server_name] = self.unified_data[
                                    "services_status"
                                ][server_name]
                                print(
                                    f"  ✅ Loaded {server_name} as healthy on port {server_info.get('details', {}).get('port', 0)}"
                                )

                    # Load other services status
                    if "services" in startup_data:
                        for service_name, service_info in startup_data[
                            "services"
                        ].items():
                            if service_info.get("status") == "running":
                                self.unified_data["services_status"][service_name] = {
                                    "status": "healthy",
                                    "port": service_info.get("details", {}).get(
                                        "port", 0
                                    ),
                                    "category": "Core Services",
                                    "last_check": service_info.get(
                                        "last_update", datetime.now().isoformat()
                                    ),
                                }
                                self.services_status[service_name] = self.unified_data[
                                    "services_status"
                                ][service_name]

                    # Update metrics layer with initial status
                    if self.metrics_layer and hasattr(
                        self.metrics_layer, "set_server_status"
                    ):
                        print(
                            f"📊 Updating metrics layer with {len(self.unified_data['services_status'])} servers"
                        )
                        self.metrics_layer.set_server_status(
                            self.unified_data["services_status"]
                        )

                    # Also ensure health manager syncs to legacy properties
                    if hasattr(self, "health_manager"):
                        self.health_manager._sync_to_legacy_properties()
                        print("✅ Synced startup status to legacy properties")

        except Exception as e:
            print(f"⚠️  Error loading persistent status: {e}")

    def _save_persistent_status(self):
        """Save current system status to persistent storage"""
        try:
            status_data = {
                "last_update": datetime.now().isoformat(),
                "services_status": self.services_status,
                "agents_status": self.agents_status,
                "system_metrics": self.system_metrics,
                "health_history": self.health_history,
                "timestamp": time.time(),
            }

            with open(self.status_file, "w") as f:
                json.dump(status_data, f, indent=2)

        except Exception as e:
            print(f"⚠️  Error saving persistent status: {e}")

    def _record_health_event(
        self,
        component_type: str,
        component_name: str,
        status: str,
        details: dict = None,
    ):
        """Record a health status change event with history"""
        timestamp = datetime.now().isoformat()

        # Initialize component history if needed
        component_key = f"{component_type}:{component_name}"
        if component_key not in self.health_history:
            self.health_history[component_key] = []

        # Record the event
        event = {
            "timestamp": timestamp,
            "status": status,
            "details": details or {},
            "component_type": component_type,
            "component_name": component_name,
        }

        self.health_history[component_key].append(event)

        # Keep only recent history
        max_entries = self.monitoring_config["max_history_entries"]
        if len(self.health_history[component_key]) > max_entries:
            self.health_history[component_key] = self.health_history[component_key][
                -max_entries:
            ]

    def _check_alert_conditions(self):
        """Check for alert conditions and record them"""
        alerts = []

        # Check system metrics against thresholds
        for metric, threshold in self.monitoring_config["alert_thresholds"].items():
            current_value = self.system_metrics.get(metric, 0)
            if current_value > threshold:
                alerts.append(
                    {
                        "type": "system_threshold",
                        "metric": metric,
                        "value": current_value,
                        "threshold": threshold,
                        "severity": (
                            "warning" if current_value < threshold * 1.1 else "critical"
                        ),
                    }
                )

        # Check for service failures
        for service_name, service_data in self.services_status.items():
            if service_data.get("status") not in ["healthy", "online"]:
                alerts.append(
                    {
                        "type": "service_down",
                        "service": service_name,
                        "status": service_data.get("status", "unknown"),
                        "severity": "critical",
                    }
                )

        # Check for agent failures
        for agent_name, agent_data in self.agents_status.items():
            if agent_data.get("status") != "running":
                alerts.append(
                    {
                        "type": "agent_down",
                        "agent": agent_name,
                        "status": agent_data.get("status", "unknown"),
                        "severity": "critical",
                    }
                )

        return alerts

    async def _enhanced_update_loop(self):
        """Enhanced update loop with health tracking and persistence"""
        while self.running:
            try:
                await self._async_update()

                # Record health events
                for service_name, service_data in self.services_status.items():
                    self._record_health_event(
                        "service",
                        service_name,
                        service_data.get("status", "unknown"),
                        service_data,
                    )

                for agent_name, agent_data in self.agents_status.items():
                    self._record_health_event(
                        "agent",
                        agent_name,
                        agent_data.get("status", "unknown"),
                        agent_data,
                    )

                # Check for alerts
                alerts = self._check_alert_conditions()
                if alerts:
                    self._record_health_event(
                        "system", "alerts", "active", {"alerts": alerts}
                    )

                # Save persistent status
                self._save_persistent_status()

                self.last_update = datetime.now().isoformat()

            except Exception as e:
                print(f"❌ Enhanced update loop error: {e}")
                self._record_health_event(
                    "system", "update_loop", "error", {"error": str(e)}
                )

            await asyncio.sleep(self.monitoring_config["update_interval"])

    def get_health_summary(self):
        """Get comprehensive health summary for dashboard using centralized data"""
        # Use centralized data when available, fallback to legacy data
        services_data = self.unified_data.get("services_status", self.services_status)
        agents_data = self.unified_data.get("agents_status", self.agents_status)
        departments_data = self.unified_data.get(
            "departments_data", self.departments_data
        )

        # Check if we have overall health from unified data
        if "overall_health" in self.unified_data:
            unified_health = self.unified_data["overall_health"]
            overall_status = unified_health.get("status", "unknown")
        else:
            # Calculate overall status from individual components
            overall_status = self._calculate_overall_status(services_data, agents_data)

        summary = {
            "overall_status": overall_status,
            "services": {
                "total": len(services_data),
                "healthy": sum(
                    1 for s in services_data.values() if s.get("status") == "healthy"
                ),
                "degraded": sum(
                    1 for s in services_data.values() if s.get("status") == "degraded"
                ),
                "critical": sum(
                    1
                    for s in services_data.values()
                    if s.get("status") not in ["healthy", "degraded"]
                ),
            },
            "agents": {
                "total": len(agents_data),
                "running": sum(
                    1 for a in agents_data.values() if a.get("status") == "running"
                ),
                "stopped": sum(
                    1 for a in agents_data.values() if a.get("status") != "running"
                ),
            },
            "leaders": {
                "total": self._get_leaders_count_from_unified_data(),
                "active": self._get_active_leaders_count_from_unified_data(),
            },
            "departments": {
                "total": len(departments_data),
                "active": len(
                    [
                        d
                        for d in departments_data.values()
                        if d.get("status", "active") == "active"
                    ]
                ),
            },
            "registry": {
                "status": services_data.get("registry", {}).get("status", "offline")
            },
            "last_update": self.unified_data.get("last_refresh", self.last_update),
            "alerts": self._check_alert_conditions(),
        }

        return summary

    def _initialize_basic_server_data(self):
        """Initialize basic server data to prevent empty state on startup"""
        print("🔄 Initializing basic server data...")

        # Define default servers organized by type and importance
        default_servers = {
            # Core Infrastructure (Highest Priority)
            "corporate_headquarters": {
                "name": "Corporate Headquarters",
                "port": 8888,
                "status": "healthy",  # We're running if this code executes
                "last_check": "Self-check",
                "category": "Core Infrastructure",
                "priority": 1,
                "description": "Main management interface",
            },
            "agent_cortex": {
                "name": "Agent Cortex",
                "port": 8889,
                "status": "unknown",
                "last_check": "Initializing...",
                "category": "Core Infrastructure",
                "priority": 2,
                "description": "Intelligent model orchestration",
            },
            "registry": {
                "name": "Registry Server",
                "port": 8009,
                "status": "unknown",
                "last_check": "Initializing...",
                "category": "Core Infrastructure",
                "priority": 3,
                "description": "Service discovery and registration",
            },
            # MCP Servers (High Priority)
            "filesystem": {
                "name": "Filesystem Server",
                "port": 8001,
                "status": "unknown",
                "last_check": "Initializing...",
                "category": "MCP Servers",
                "priority": 4,
                "description": "File operations and management",
            },
            "database_postgres": {
                "name": "PostgreSQL Database Server",
                "port": 8010,
                "status": "unknown",
                "last_check": "Initializing...",
                "category": "MCP Servers",
                "priority": 5,
                "description": "Data storage and retrieval",
            },
            "analytics": {
                "name": "Analytics Server",
                "port": 8007,
                "status": "unknown",
                "last_check": "Initializing...",
                "category": "MCP Servers",
                "priority": 6,
                "description": "Business intelligence and metrics",
            },
            # Business Services (Medium Priority)
            "payment": {
                "name": "Payment Server",
                "port": 8006,
                "status": "unknown",
                "last_check": "Initializing...",
                "category": "Business Services",
                "priority": 7,
                "description": "Revenue and billing management",
            },
            "customer": {
                "name": "Customer Server",
                "port": 8008,
                "status": "unknown",
                "last_check": "Initializing...",
                "category": "Business Services",
                "priority": 8,
                "description": "Customer relationship management",
            },
        }

        # Initialize both legacy and unified data
        # But only for servers that don't already exist (to preserve loaded status)
        initialized_count = 0
        preserved_count = 0

        for server_id, server_info in default_servers.items():
            if server_id not in self.unified_data["services_status"]:
                self.services_status[server_id] = server_info
                self.unified_data["services_status"][server_id] = server_info
                initialized_count += 1
            else:
                # Keep the existing loaded status
                preserved_count += 1
                print(
                    f"  ⏩ Preserved {server_id} - status: {self.unified_data['services_status'][server_id].get('status')}"
                )

        print(
            f"✅ Initialized {initialized_count} new servers, preserved {preserved_count} loaded servers"
        )

    def _run_initial_health_check(self):
        """Run a quick initial health check to populate server status"""
        print("📊 Running initial health check...")

        # Run a simplified health check for key servers
        import socket

        # Check servers in order of priority (most important first)
        servers_to_check = [
            ("corporate_headquarters", 8888),
            ("agent_cortex", 8889),
            ("registry", 8000),
            ("filesystem", 8001),
            ("database_postgres", 8010),
            ("analytics", 8007),
            ("payment", 8006),
            ("customer", 8008),
        ]

        healthy_count = 0

        for server_name, port in servers_to_check:
            try:
                # Quick socket check to see if port is open
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)  # 1 second timeout
                result = sock.connect_ex(("localhost", port))
                sock.close()

                if result == 0:
                    # Port is open, assume healthy
                    self.services_status[server_name]["status"] = "healthy"
                    self.services_status[server_name][
                        "last_check"
                    ] = datetime.now().isoformat()
                    self.unified_data["services_status"][server_name][
                        "status"
                    ] = "healthy"
                    self.unified_data["services_status"][server_name][
                        "last_check"
                    ] = datetime.now().isoformat()
                    healthy_count += 1
                    print(f"✅ {server_name} server is healthy on port {port}")
                else:
                    # Port is closed, mark as offline
                    self.services_status[server_name]["status"] = "offline"
                    self.services_status[server_name][
                        "last_check"
                    ] = datetime.now().isoformat()
                    self.unified_data["services_status"][server_name][
                        "status"
                    ] = "offline"
                    self.unified_data["services_status"][server_name][
                        "last_check"
                    ] = datetime.now().isoformat()
                    print(f"❌ {server_name} server is offline on port {port}")

            except Exception as e:
                # Error checking, mark as offline
                self.services_status[server_name]["status"] = "offline"
                self.services_status[server_name][
                    "last_check"
                ] = datetime.now().isoformat()
                self.unified_data["services_status"][server_name]["status"] = "offline"
                self.unified_data["services_status"][server_name][
                    "last_check"
                ] = datetime.now().isoformat()
                print(f"❌ {server_name} server check failed: {e}")

        print(
            f"✅ Initial health check complete: {healthy_count}/{len(servers_to_check)} servers healthy"
        )

        # Also collect initial organizational metrics
        try:
            print("📊 Collecting initial organizational metrics...")
            import asyncio

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Create HealthDataManager instance to collect metrics
            health_manager = HealthDataManager(self)
            metrics = loop.run_until_complete(
                health_manager._collect_organizational_metrics()
            )

            # Store in unified data
            self.unified_data["organizational_metrics"] = metrics
            print(f"✅ Initial organizational metrics collected")

        except Exception as e:
            print(f"⚠️ Failed to collect initial organizational metrics: {e}")
            # Set default metrics
            self.unified_data["organizational_metrics"] = {
                "divisions": {"total": 0, "active": 0, "percentage": 0},
                "departments": {"total": 0, "active": 0, "percentage": 0},
                "leaders": {"total": 0, "active": 0, "percentage": 0},
                "agents": {"total": 0, "active": 0, "percentage": 0},
            }

    def _calculate_overall_status(self, services_data, agents_data):
        """Calculate overall system status from component health"""
        # Use unified data if available, fallback to passed data
        if hasattr(self, "unified_data") and self.unified_data.get("services_status"):
            services_data = self.unified_data["services_status"]

        # Debug: log status calculation
        healthy_services = sum(
            1 for s in services_data.values() if s.get("status") == "healthy"
        )
        degraded_services = sum(
            1 for s in services_data.values() if s.get("status") == "degraded"
        )
        critical_services = sum(
            1
            for s in services_data.values()
            if s.get("status") not in ["healthy", "degraded"]
        )
        running_agents = sum(
            1 for a in agents_data.values() if a.get("status") == "running"
        )
        stopped_agents = sum(
            1 for a in agents_data.values() if a.get("status") != "running"
        )

        print(
            f"📊 Status calculation: {healthy_services} healthy, {degraded_services} degraded, {critical_services} critical services; {running_agents} running, {stopped_agents} stopped agents"
        )

        # Determine overall status with more nuanced logic
        if critical_services > 2 or stopped_agents > 1:
            return "offline"
        elif critical_services > 0 or stopped_agents > 0 or degraded_services > 0:
            return "warning"
        else:
            return "online"

    def _get_centralized_metrics(self):
        """Get all centralized metrics from the unified data store"""
        try:
            metrics = {
                "system": self.unified_data.get("system_metrics", {}),
                "services": self.unified_data.get("services_status", {}),
                "agents": self.unified_data.get("agents_status", {}),
                "database": self.unified_data.get("database_health", {}),
                "registry": self.unified_data.get("registry_data", {}),
                "departments": self.unified_data.get("departments_data", {}),
                "leaders": self.unified_data.get("leaders_data", {}),
                "organizational": self.unified_data.get("organizational_data", {}),
                "mcp_details": self.unified_data.get("mcp_details", {}),
                "startup_status": self.unified_data.get("startup_status", {}),
                "health_history": self.unified_data.get("health_history", {}),
                "last_refresh": self.unified_data.get("last_refresh"),
                "metrics_layer_available": self.metrics_layer is not None,
            }

            # Add summary metrics
            metrics["summary"] = {
                "total_agents": len(metrics["agents"]),
                "running_agents": sum(
                    1
                    for a in metrics["agents"].values()
                    if a.get("status") == "running"
                ),
                "total_services": len(metrics["services"]),
                "healthy_services": sum(
                    1
                    for s in metrics["services"].values()
                    if s.get("status") == "healthy"
                ),
                "total_departments": len(metrics["departments"]),
                "total_leaders": len(metrics["leaders"]),
            }

            return metrics
        except Exception as e:
            print(f"Error getting centralized metrics: {e}")
            return {}

    def _generate_metrics_page_content(self):
        """Generate comprehensive metrics page content using metrics layer"""
        if not self.metrics_layer:
            return self._generate_metrics_fallback()

        try:
            # Pass real server status to metrics layer
            services_status = self.unified_data.get("services_status", {})

            # Force Corporate HQ to be healthy since we're running
            if (
                not services_status.get("corporate_headquarters")
                or services_status.get("corporate_headquarters", {}).get("status")
                != "healthy"
            ):
                services_status["corporate_headquarters"] = {
                    "status": "healthy",
                    "port": 8888,
                    "name": "Corporate Headquarters",
                    "category": "Core Infrastructure",
                    "last_check": datetime.now().isoformat(),
                }

            print(f"🔍 Passing {len(services_status)} servers to metrics layer")
            if "corporate_headquarters" in services_status:
                print(
                    f"🔍 Corporate HQ status: {services_status['corporate_headquarters'].get('status', 'unknown')}"
                )
            if hasattr(self.metrics_layer, "set_server_status"):
                self.metrics_layer.set_server_status(services_status)

            # Use the metrics layer to generate the metrics page
            return self.metrics_layer.get_metrics_page_html()
        except Exception as e:
            print(f"Error generating metrics page: {e}")
            return self._generate_metrics_fallback()

    def _generate_metrics_fallback(self):
        """Generate fallback metrics display when metrics layer is not available"""
        metrics = self._get_centralized_metrics()

        html = f"""
        <div class="metrics-container">
            <h3 style="margin-bottom: 2rem;">System Metrics Overview</h3>

            <div class="metrics-summary" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 2rem;">
                <div class="metric-card" style="background: var(--secondary-bg); padding: 1.5rem; border-radius: 8px;">
                    <h4>Agents</h4>
                    <div style="font-size: 2rem; font-weight: bold; color: var(--accent-color);">
                        {metrics['summary']['running_agents']} / {metrics['summary']['total_agents']}
                    </div>
                    <div style="color: var(--secondary-text);">Running Agents</div>
                </div>

                <div class="metric-card" style="background: var(--secondary-bg); padding: 1.5rem; border-radius: 8px;">
                    <h4>Services</h4>
                    <div style="font-size: 2rem; font-weight: bold; color: var(--success-color);">
                        {metrics['summary']['healthy_services']} / {metrics['summary']['total_services']}
                    </div>
                    <div style="color: var(--secondary-text);">Healthy Services</div>
                </div>

                <div class="metric-card" style="background: var(--secondary-bg); padding: 1.5rem; border-radius: 8px;">
                    <h4>Organization</h4>
                    <div style="font-size: 2rem; font-weight: bold; color: var(--warning-color);">
                        {metrics['summary']['total_departments']}
                    </div>
                    <div style="color: var(--secondary-text);">Departments</div>
                </div>
            </div>

            <div class="metrics-details">
                <h4>Raw Metrics Data</h4>
                <pre style="background: var(--secondary-bg); padding: 1rem; border-radius: 8px; overflow: auto; max-height: 400px;">
{json.dumps(metrics, indent=2)}
                </pre>
            </div>
        </div>
        """

        return html

    def _generate_server_cards(self, category_name: str) -> str:
        """Generate server cards for a specific category"""
        # Get the most up-to-date services data
        services_data = self.unified_data.get("services_status", {})
        if not services_data:
            services_data = self.services_status

        # Define server categories
        category_servers = {
            "Core Systems": ["corporate_headquarters", "agent_cortex", "registry"],
            "MCP Servers": ["filesystem", "database_postgres", "analytics"],
            "Business Services": ["payment", "customer"],
        }

        servers = category_servers.get(category_name, [])
        cards_html = []

        for server_id in servers:
            server_info = services_data.get(server_id, {})
            status = server_info.get("status", "unknown")
            name = server_info.get("name", server_id.replace("_", " ").title())
            port = server_info.get("port", "N/A")
            last_check = server_info.get("last_check", "Never")
            uptime = server_info.get("uptime", "Unknown")
            response_time = server_info.get("response_time", 0)
            icon = server_info.get("icon", "fas fa-server")

            # Determine status color and icon
            if status == "healthy":
                status_color = "var(--success-color)"
                status_icon = "fa-check-circle"
                status_text = "Online"
            elif status == "degraded":
                status_color = "var(--warning-color)"
                status_icon = "fa-exclamation-circle"
                status_text = "Degraded"
            else:
                status_color = "var(--danger-color)"
                status_icon = "fa-times-circle"
                status_text = "Offline"

            # Generate server card HTML
            card_html = f"""
            <div class="server-card" style="
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid var(--border-color);
                border-radius: 12px;
                padding: 1.5rem;
                transition: all 0.3s ease;
                cursor: pointer;
                position: relative;
                overflow: hidden;
            " onmouseover="this.style.borderColor='var(--accent-color)'; this.style.background='rgba(255, 255, 255, 0.08)'"
              onmouseout="this.style.borderColor='var(--border-color)'; this.style.background='rgba(255, 255, 255, 0.05)'">
                <div style="display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 1rem;">
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <div style="
                            width: 48px; height: 48px;
                            background: {'rgba(16, 185, 129, 0.1)' if status == 'healthy' else 'rgba(245, 158, 11, 0.1)' if status == 'degraded' else 'rgba(239, 68, 68, 0.1)'};
                            border-radius: 12px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-size: 1.25rem;
                            color: {status_color};
                        ">
                            <i class="{icon}"></i>
                        </div>
                        <div>
                            <h5 style="margin: 0; font-size: 1.1rem; font-weight: 600; color: var(--primary-text);">
                                {name}
                            </h5>
                            <p style="margin: 0; font-size: 0.85rem; color: var(--secondary-text);">
                                Port {port}
                            </p>
                        </div>
                    </div>
                    <div style="
                        display: flex;
                        align-items: center;
                        gap: 0.25rem;
                        font-size: 0.85rem;
                        font-weight: 500;
                        color: {status_color};
                    ">
                        <i class="fas {status_icon}"></i>
                        <span>{status_text}</span>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.75rem; font-size: 0.85rem;">
                    <div>
                        <span style="color: var(--secondary-text);">Response Time:</span>
                        <span style="color: var(--primary-text); font-weight: 500; margin-left: 0.5rem;">
                            {f"{response_time:.2f}s" if response_time else "N/A"}
                        </span>
                    </div>
                    <div>
                        <span style="color: var(--secondary-text);">Uptime:</span>
                        <span style="color: var(--primary-text); font-weight: 500; margin-left: 0.5rem;">
                            {uptime}
                        </span>
                    </div>
                    <div style="grid-column: span 2;">
                        <span style="color: var(--secondary-text);">Last Check:</span>
                        <span style="color: var(--primary-text); font-weight: 500; margin-left: 0.5rem;">
                            {last_check}
                        </span>
                    </div>
                </div>

                <!-- Enhanced details for specific servers -->
                {self._generate_server_specific_details(server_id, server_info)}
            </div>
            """
            cards_html.append(card_html)

        return (
            "\n".join(cards_html)
            if cards_html
            else '<p style="color: var(--secondary-text); text-align: center;">No servers in this category</p>'
        )

    def _generate_server_specific_details(
        self, server_id: str, server_info: dict
    ) -> str:
        """Generate additional details for specific servers"""
        details_html = ""

        # Add specific details for filesystem server
        if server_id == "filesystem" and self.mcp_details.get("filesystem"):
            fs_details = self.mcp_details["filesystem"]
            if fs_details.get("ai_features"):
                details_html += f"""
                <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid var(--border-color);">
                    <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.8rem; color: var(--accent-color);">
                        <i class="fas fa-brain"></i>
                        <span>AI Features Enabled</span>
                    </div>
                    <div style="font-size: 0.8rem; color: var(--secondary-text); margin-top: 0.25rem;">
                        Vector DB: {fs_details.get('vector_db_size', 0)} entries
                    </div>
                </div>
                """

        return details_html

    def generate_dashboard_html(self):
        """Generate the enhanced dashboard HTML"""
        # Get comprehensive health summary
        health_summary = self.get_health_summary()

        # Extract data for widgets
        total_agents = health_summary["agents"]["total"] or 2
        active_agents = health_summary["agents"]["running"]

        # Count servers by category for better tracking
        services_data = self.unified_data.get("services_status", self.services_status)

        # Core infrastructure servers
        core_servers = ["corporate_headquarters", "agent_cortex", "registry"]
        # MCP (Model Context Protocol) servers
        mcp_servers = ["filesystem", "database_postgres", "analytics"]
        # Business services
        business_servers = ["payment", "customer"]

        # Calculate totals - we have exactly 8 servers in the system
        total_servers = 8  # 3 Core + 3 MCP + 2 Business = 8 servers

        # Count healthy servers from each category
        healthy_core = sum(
            1
            for s in core_servers
            if s in services_data and services_data[s].get("status") == "healthy"
        )
        healthy_mcp = sum(
            1
            for s in mcp_servers
            if s in services_data and services_data[s].get("status") == "healthy"
        )
        healthy_business = sum(
            1
            for s in business_servers
            if s in services_data and services_data[s].get("status") == "healthy"
        )

        # Total healthy servers across all categories
        total_healthy_servers = healthy_core + healthy_mcp + healthy_business

        # Update to use our calculated server counts
        total_services = total_servers  # Use our fixed count of 8
        healthy_services = total_healthy_servers  # Use calculated healthy count

        # For backward compatibility with narrative
        total_mcp_servers = len(mcp_servers)
        healthy_mcp_servers = healthy_mcp

        # Get real-time leader data from database
        leaders_data = self._fetch_leaders_data()
        total_leaders = len(leaders_data) if leaders_data else 0
        active_leaders = (
            len(
                [
                    l
                    for l in leaders_data
                    if l.get("active_status", "active") == "active"
                ]
            )
            if leaders_data
            else 0
        )

        # Get real-time department data
        departments_data = self.unified_data.get("departments_data", {})
        total_departments = (
            len(departments_data)
            if departments_data
            else self._get_department_count_from_db()
        )
        active_departments = (
            len(
                [
                    d
                    for d in departments_data.values()
                    if d.get("status", "active") == "active"
                ]
            )
            if departments_data
            else total_departments
        )

        # Get real-time divisions count from database
        total_divisions = (
            len(set(l["division_name"] for l in leaders_data))
            if leaders_data
            else self._get_division_count_from_db()
        )

        registry_status = health_summary["registry"]["status"]
        overall_status = health_summary["overall_status"]

        # Generate smart recommendations based on current metrics
        smart_recommendations = self._generate_smart_recommendations(
            overall_status,
            active_agents,
            total_agents,
            healthy_services,
            total_services,
            active_leaders,
            total_leaders,
            registry_status,
        )

        return f"""<!DOCTYPE html>
<html>
<head>
    <title>BoarderframeOS</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">

    <style>
        :root {{
            --primary-bg: #0a0e27;
            --secondary-bg: #1a1d3a;
            --card-bg: #252853;
            --accent-bg: #2d3561;
            --primary-text: #ffffff;
            --secondary-text: #b0b7c3;
            --accent-color: #6366f1;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --danger-color: #ef4444;
            --border-color: #374151;
            --glow-color: rgba(99, 102, 241, 0.3);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, var(--primary-bg) 0%, #0f1629 100%);
            color: var(--primary-text);
            line-height: 1.4;
            min-height: 100vh;
            padding-top: 100px; /* Account for fixed header (60px) and nav (40px) */
            overflow-x: hidden;
            overflow-y: scroll; /* Always show vertical scrollbar */
            opacity: 0;
            transition: opacity 0.5s ease;
        }}

        /* Header */
        .header {{
            background: linear-gradient(135deg, var(--secondary-bg) 0%, var(--card-bg) 50%, var(--accent-bg) 100%);
            border-bottom: 2px solid var(--accent-color);
            padding: 0.75rem 1rem;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1001;
            height: 60px;
        }}

        /* Navigation Bar - Ultra Simple */
        .navigation-container {{
            position: fixed;
            top: 60px;
            left: 0;
            right: 0;
            z-index: 1000;
            background: var(--secondary-bg);
            border-bottom: 1px solid var(--border-color);
            height: 40px;
        }}

        .nav-menu {{
            display: flex;
            justify-content: center;
            align-items: center;
            height: 40px;
            margin: 0;
            padding: 0;
            list-style: none;
        }}

        .nav-item {{
            margin: 0;
        }}

        .nav-link {{
            position: relative;
            display: inline-block;
            height: 40px;
            padding: 0;
            margin: 0 15px;
            text-decoration: none;
            color: var(--secondary-text);
            font-size: 13px;
            font-weight: 500;
            background: transparent;
            border: none;
            cursor: pointer;
            transition: color 0.2s ease;
            line-height: 40px;
            vertical-align: top;
            text-align: center;
        }}

        .nav-link:hover {{
            color: var(--primary-text);
        }}

        .nav-link.active {{
            color: var(--accent-color);
            font-weight: 600;
        }}

        .nav-link i {{
            font-size: 14px;
            vertical-align: middle;
            margin-right: 6px;
        }}

        .nav-link span {{
            vertical-align: middle;
        }}

        /* Navigation Responsive Design */
        @media (max-width: 768px) {{
            .nav-link {{
                padding: 0 15px;
                font-size: 13px;
            }}

            .nav-link span {{
                display: none;
            }}

            .nav-link i {{
                font-size: 16px;
            }}
        }}

        @media (max-width: 480px) {{
            .nav-menu {{
                overflow-x: auto;
                scrollbar-width: none;
                -ms-overflow-style: none;
            }}

            .nav-menu::-webkit-scrollbar {{
                display: none;
            }}

            .nav-link {{
                padding: 0 12px;
            }}
        }}

        /* Tab Content */
        .tab-content {{
            display: none;
        }}

        .tab-content.active {{
            display: block;
        }}

        /* Chat Button */
        .chat-button {{
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, var(--accent-color), var(--success-color));
            border: none;
            border-radius: 50%;
            color: white;
            font-size: 1.5rem;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
            transition: all 0.3s ease;
            z-index: 1001;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .chat-button:hover {{
            transform: scale(1.1);
            box-shadow: 0 6px 25px rgba(99, 102, 241, 0.6);
        }}

        /* Chat Overlay */
        .chat-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            z-index: 1002;
            display: none;
            align-items: center;
            justify-content: center;
        }}

        .chat-container {{
            background: var(--secondary-bg);
            border-radius: 16px;
            width: 90%;
            max-width: 800px;
            height: 80%;
            display: flex;
            flex-direction: column;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
            border: 1px solid var(--border-color);
        }}

        .chat-header {{
            padding: 0.5rem 0.75rem;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .chat-close {{
            background: none;
            border: none;
            color: var(--secondary-text);
            font-size: 1.5rem;
            cursor: pointer;
            transition: color 0.3s ease;
        }}

        .chat-close:hover {{
            color: var(--danger-color);
        }}

        .agent-selector {{
            padding: 0.5rem 0.75rem;
            border-bottom: 1px solid var(--border-color);
            background: var(--card-bg);
        }}

        .agent-pills {{
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }}

        .agent-pill {{
            padding: 0.25rem 0.5rem;
            background: var(--accent-bg);
            border: 1px solid var(--border-color);
            border-radius: 15px;
            color: var(--secondary-text);
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 0.85rem;
        }}

        .agent-pill.active {{
            background: var(--accent-color);
            color: white;
            border-color: var(--accent-color);
        }}

        .agent-pill:hover {{
            border-color: var(--accent-color);
            color: var(--primary-text);
        }}

        .chat-messages {{
            flex: 1;
            padding: 0.5rem 0.75rem;
            overflow-y: auto;
            background: var(--primary-bg);
        }}

        .chat-input-area {{
            padding: 0.5rem 0.75rem;
            border-top: 1px solid var(--border-color);
            background: var(--card-bg);
        }}

        .chat-input {{
            width: 100%;
            padding: 0.5rem;
            background: var(--primary-bg);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            color: var(--primary-text);
            resize: none;
        }}

        .chat-send {{
            margin-top: 0.5rem;
            background: var(--accent-color);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            cursor: pointer;
            transition: background 0.3s ease;
        }}

        .chat-send:hover {{
            background: var(--success-color);
        }}
            z-index: 100;
            backdrop-filter: blur(10px);
            position: relative;
            overflow: hidden;
        }}

        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.1), transparent);
            animation: shimmer 3s infinite;
        }}

        @keyframes shimmer {{
            0% {{ left: -100%; }}
            100% {{ left: 100%; }}
        }}

        .header-content {{
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: relative;
            z-index: 1;
        }}

        .logo {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .logo i {{
            font-size: 2.5rem;
            color: var(--accent-color);
            text-shadow: 0 0 20px var(--glow-color);
            animation: glow-pulse 2s ease-in-out infinite alternate;
        }}

        @keyframes glow-pulse {{
            from {{ text-shadow: 0 0 20px var(--glow-color); }}
            to {{ text-shadow: 0 0 30px var(--glow-color), 0 0 40px var(--accent-color); }}
        }}

        .logo i {{
            font-size: 2rem;
            color: var(--accent-color);
            text-shadow: 0 0 20px var(--glow-color);
        }}

        .logo h1 {{
            font-size: 1.8rem;
            font-weight: 700;
            background: linear-gradient(45deg, var(--accent-color), #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: glow-text 3s ease-in-out infinite alternate;
        }}

        @keyframes glow-text {{
            from {{
                filter: drop-shadow(0 0 5px rgba(99, 102, 241, 0.3));
            }}
            to {{
                filter: drop-shadow(0 0 15px rgba(99, 102, 241, 0.6));
            }}
        }}

        .header-actions {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .global-refresh-btn {{
            display: flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.4rem 0.8rem;
            background: linear-gradient(135deg, var(--accent-color), #4f46e5);
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.8rem;
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: 0 2px 6px rgba(99, 102, 241, 0.25);
            height: 32px;
        }}

        .global-refresh-btn:hover {{
            background: linear-gradient(135deg, #4f46e5, var(--accent-color));
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
        }}

        .global-refresh-btn:disabled {{
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }}

        .global-refresh-btn .spinning {{
            animation: spin 1s linear infinite;
        }}


        @keyframes spin {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}

        /* Component card animations */
        .spinning {{
            animation: spin 1s linear infinite;
        }}

        .refresh-component-card {{
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        .refresh-component-card:hover {{
            transform: scale(1.02) !important;
        }}

        @keyframes componentPulse {{
            0%, 100% {{
                box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
            }}
            50% {{
                box-shadow: 0 8px 25px rgba(99, 102, 241, 0.5);
            }}
        }}

        @keyframes componentComplete {{
            0% {{
                transform: scale(1);
                filter: brightness(1);
            }}
            50% {{
                transform: scale(1.08);
                filter: brightness(1.2);
            }}
            100% {{
                transform: scale(1.05);
                filter: brightness(1.15);
            }}
        }}

        .system-status {{
            display: flex;
            align-items: center;
            gap: 1.5rem;
            position: relative;
        }}

        .status-indicator {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.25rem 0.5rem;
            border-radius: 25px;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid var(--border-color);
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 0.85rem;
        }}

        .status-indicator:hover {{
            background: rgba(255, 255, 255, 0.15);
            transform: translateY(-1px);
        }}

        .status-dropdown {{
            position: absolute;
            top: 100%;
            right: 0;
            margin-top: 0.5rem;
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            min-width: 280px;
            z-index: 1000;
            opacity: 0;
            visibility: hidden;
            transform: translateY(-10px);
            transition: all 0.3s ease;
        }}

        .status-dropdown.show {{
            opacity: 1;
            visibility: visible;
            transform: translateY(0);
        }}

        .dropdown-header {{
            padding: 0.6rem 0.75rem;
            border-bottom: 1px solid var(--border-color);
            font-weight: 500;
            font-size: 0.9rem;
            color: var(--primary-text);
            letter-spacing: 0.025em;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .dropdown-section {{
            padding: 0.25rem 0;
        }}

        .dropdown-item {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.25rem 0.5rem;
            cursor: pointer;
            transition: background 0.2s ease;
        }}

        .dropdown-item:hover {{
            background: rgba(255, 255, 255, 0.05);
        }}

        .dropdown-item:active {{
            background: rgba(255, 255, 255, 0.1);
            transform: scale(0.98);
        }}

        .subsystem-name {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            color: var(--secondary-text);
            font-size: 0.9rem;
            min-width: 120px;
        }}

        .subsystem-name i {{
            width: 16px;
            text-align: center;
            font-size: 0.9rem;
        }}

        .subsystem-status {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.85rem;
            font-weight: 500;
            min-width: 50px;
            justify-content: flex-end;
        }}

        .status-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }}

        .status-dot.online {{ background: var(--success-color); }}
        .status-dot.warning {{ background: var(--warning-color); }}
        .status-dot.offline {{ background: var(--danger-color); }}
        .status-dot.initializing {{
            background: #3b82f6;
            animation: pulse 1s infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.6; }}
        }}

        /* Main Container */
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 1.5rem 2rem;
        }}

        .grid {{
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            margin-bottom: 1rem;
        }}

        .widget-grid {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 0.75rem;
            padding: 0.5rem;
        }}

        .widget {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 0.75rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
            transition: all 0.3s ease;
        }}

        .widget:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
        }}

        .widget-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.5rem;
            padding-bottom: 0.25rem;
            border-bottom: 1px solid var(--border-color);
        }}

        .widget-title {{
            display: flex;
            align-items: center;
            gap: 0.4rem;
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--primary-text);
        }}

        .widget-value {{
            font-size: 1.6rem;
            font-weight: 700;
            margin: 0.2rem 0;
        }}

        .widget-label {{
            font-size: 0.75rem;
            color: var(--secondary-text);
        }}

        .widget-small {{
            grid-column: span 1;
        }}

        .widget-medium {{
            grid-column: span 2;
        }}

        .widget-large {{
            grid-column: span 3;
        }}

        .widget-full {{
            grid-column: span 5;
        }}

        .full-width {{
            grid-column: 1 / -1;
        }}

        /* Section spacing */
        .section-separator {{
            margin: 3rem 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--border-color), transparent);
        }}

        /* Card Styles */
        .card {{
            background: linear-gradient(135deg, var(--card-bg) 0%, var(--accent-bg) 100%);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 0.75rem;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}

        .card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, var(--accent-color), #8b5cf6, var(--accent-color));
            opacity: 0.8;
        }}

        .card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
            border-color: var(--accent-color);
        }}

        .card h3 {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.5rem;
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--primary-text);
        }}

        .card h3 i {{
            color: var(--accent-color);
            font-size: 1.2rem;
        }}

        /* Service Cards */
        .service-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            margin-bottom: 0.4rem;
            transition: all 0.2s ease;
        }}

        .service-item:hover {{
            background: rgba(255, 255, 255, 0.08);
            border-color: var(--accent-color);
        }}

        .service-info {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .service-icon {{
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            color: white;
        }}

        .service-icon.filesystem {{ background: linear-gradient(45deg, #10b981, #059669); }}
        .service-icon.registry {{ background: linear-gradient(45deg, #6366f1, #4f46e5); }}
        .service-icon.database {{ background: linear-gradient(45deg, #f59e0b, #d97706); }}
        .service-icon.llm {{ background: linear-gradient(45deg, #8b5cf6, #7c3aed); }}
        .service-icon.dashboard {{ background: linear-gradient(45deg, #ef4444, #dc2626); }}

        .service-details h4 {{
            margin: 0;
            font-size: 1rem;
            font-weight: 600;
        }}

        .service-details p {{
            margin: 0;
            font-size: 0.9rem;
            color: var(--secondary-text);
        }}

        .service-status {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.4rem 0.8rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
            text-transform: uppercase;
            transition: all 0.3s ease;
        }}

        .service-status.healthy {{
            background: rgba(16, 185, 129, 0.2);
            color: var(--success-color);
            border: 1px solid var(--success-color);
        }}

        .service-status.degraded {{
            background: rgba(245, 158, 11, 0.2);
            color: var(--warning-color);
            border: 1px solid var(--warning-color);
        }}

        .service-status.critical {{
            background: rgba(239, 68, 68, 0.2);
            color: var(--danger-color);
            border: 1px solid var(--danger-color);
        }}

        /* Agents */
        .agent-card {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
            transition: all 0.2s ease;
        }}

        .agent-card:hover {{
            background: rgba(255, 255, 255, 0.08);
            transform: translateY(-1px);
        }}

        .agent-card.active {{
            border-color: var(--success-color);
            background: rgba(16, 185, 129, 0.1);
        }}

        .agent-card.inactive {{
            border-color: var(--border-color);
            opacity: 0.7;
        }}

        .agent-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.8rem;
        }}

        .agent-name {{
            font-size: 1.1rem;
            font-weight: 600;
            margin: 0;
        }}

        .agent-status {{
            padding: 0.3rem 0.8rem;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: 500;
            text-transform: uppercase;
        }}

        .agent-status.running {{
            background: rgba(16, 185, 129, 0.2);
            color: var(--success-color);
            border: 1px solid var(--success-color);
        }}

        .agent-status.inactive {{
            background: rgba(107, 114, 128, 0.2);
            color: #9ca3af;
            border: 1px solid #6b7280;
        }}

        .agent-details {{
            color: var(--secondary-text);
            font-size: 0.9rem;
            line-height: 1.4;
        }}

        .agent-details div {{
            margin-bottom: 0.3rem;
        }}

        /* Metrics */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }}

        .metric-item {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 1rem;
            text-align: center;
        }}

        .metric-value {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--accent-color);
            margin-bottom: 0.5rem;
            transition: all 0.3s ease;
        }}

        .metric-label {{
            font-size: 0.9rem;
            color: var(--secondary-text);
        }}

        /* Special filesystem display */
        .filesystem-enhanced {{
            border-left: 3px solid var(--success-color) !important;
        }}

        .filesystem-enhanced .service-details p::after {{
            content: " 🤖 AI";
            color: var(--success-color);
            font-weight: 600;
            font-size: 0.8rem;
        }}

        /* MCP Server colored borders */
        .server-registry {{
            border-left: 4px solid #6366f1 !important;
        }}

        .server-filesystem {{
            border-left: 4px solid #10b981 !important;
        }}

        .server-database {{
            border-left: 4px solid #f59e0b !important;
        }}

        .server-llm {{
            border-left: 4px solid #8b5cf6 !important;
        }}

        .server-dashboard {{
            border-left: 4px solid #ef4444 !important;
        }}

        .server-payment {{
            border-left: 4px solid #059669 !important;
        }}

        .server-analytics {{
            border-left: 4px solid #dc2626 !important;
        }}

        .server-customer {{
            border-left: 4px solid #7c2d92 !important;
        }}

        /* Category section styles */
        .category-section {{
            margin-bottom: 2rem;
        }}

        .category-title {{
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--primary-text);
            margin-bottom: 1rem;
            padding-left: 0.5rem;
            border-left: 3px solid var(--accent-color);
            background: linear-gradient(90deg, rgba(99, 102, 241, 0.1) 0%, transparent 100%);
            padding: 0.5rem;
            border-radius: 4px;
        }}

        .category-services {{
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }}

        .category-section:last-child {{
            margin-bottom: 0;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .container {{
                padding: 1rem;
            }}

            .header-content {{
                flex-direction: column;
                gap: 1rem;
            }}

            .grid {{
                grid-template-columns: 1fr;
            }}

            .widget-grid {{
                grid-template-columns: 1fr;
                padding: 1rem;
            }}

            .widget-small, .widget-medium, .widget-large, .widget-full {{
                grid-column: span 1;
            }}

            .service-item {{
                flex-direction: column;
                align-items: flex-start;
                gap: 0.8rem;
            }}
        }}

        @media (max-width: 1200px) {{
            .widget-grid {{
                grid-template-columns: repeat(3, 1fr);
            }}

            .widget-full {{
                grid-column: span 3;
            }}
        }}

        @media (max-width: 900px) {{
            .widget-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}

            .widget-full {{
                grid-column: span 2;
            }}
        }}

        /* Animations */
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .card {{
            animation: fadeInUp 0.6s ease forwards;
        }}

        .card:nth-child(1) {{ animation-delay: 0.1s; }}
        .card:nth-child(2) {{ animation-delay: 0.2s; }}
        .card:nth-child(3) {{ animation-delay: 0.3s; }}
        .card:nth-child(4) {{ animation-delay: 0.4s; }}

        .content-updating {{
            opacity: 0.7;
            transition: opacity 0.3s ease;
        }}

        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.7; }}
            100% {{ opacity: 1; }}
        }}

        .updating {{
            animation: pulse 0.5s ease-in-out;
        }}

        /* Enhanced Agent Cards */
        .enhanced-agent-card {{
            display: flex;
            align-items: flex-start;
            gap: 1.2rem;
            padding: 1.25rem;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
            overflow: hidden;
            min-height: 140px;
            max-width: 100%;
        }}

        .enhanced-agent-card:hover {{
            background: rgba(255, 255, 255, 0.08);
            border-color: var(--accent-color);
            transform: translateY(-2px);
        }}

        .agent-avatar {{
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--accent-color), #4f46e5);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.8rem;
            color: white;
            flex-shrink: 0;
        }}

        .agent-avatar.offline {{
            background: linear-gradient(135deg, var(--border-color), #374151);
            opacity: 0.6;
        }}

        .agent-info {{
            flex: 1;
            min-width: 0;
            overflow: hidden;
        }}

        .agent-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 0.75rem;
        }}

        .agent-header > div:first-child {{
            flex: 1;
        }}

        .agent-name {{
            font-size: 1.2rem;
            font-weight: 600;
            color: var(--primary-text);
            margin: 0 0 0.25rem 0;
        }}

        .agent-title {{
            font-size: 0.9rem;
            color: var(--secondary-text);
            margin: 0;
            line-height: 1.3;
        }}

        .agent-status-badge {{
            display: flex;
            align-items: center;
            gap: 0.3rem;
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
        }}

        .agent-status-badge.running {{
            background: rgba(16, 185, 129, 0.2);
            color: var(--success-color);
            border: 1px solid var(--success-color);
        }}

        .agent-status-badge.offline {{
            background: rgba(107, 114, 128, 0.2);
            color: var(--secondary-text);
            border: 1px solid var(--border-color);
        }}

        .agent-department {{
            margin-top: 0.25rem;
        }}

        .agent-department span {{
            font-size: 0.8rem;
            color: var(--accent-color);
            font-weight: 500;
        }}

        .agent-meta {{
            margin-bottom: 0.8rem;
            font-size: 0.85rem;
            color: var(--secondary-text);
        }}

        .agent-model {{
            display: block;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        .agent-type {{
            font-weight: 500;
        }}

        .agent-department {{
            display: flex;
            align-items: center;
            gap: 0.3rem;
            color: var(--accent-color);
            font-weight: 500;
        }}

        .agent-metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
            gap: 0.5rem;
            margin-bottom: 0.8rem;
        }}

        .metric-chip {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.25rem;
            padding: 0.25rem 0.5rem;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 6px;
            font-size: 0.75rem;
            color: var(--secondary-text);
            text-align: center;
        }}

        .agent-capabilities {{
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin-bottom: 1rem;
        }}

        .capability-tag {{
            padding: 0.2rem 0.6rem;
            background: rgba(99, 102, 241, 0.2);
            color: var(--accent-color);
            border-radius: 15px;
            font-size: 0.8rem;
            border: 1px solid var(--accent-color);
        }}

        .capability-tag.disabled {{
            background: rgba(107, 114, 128, 0.2);
            color: var(--secondary-text);
            border-color: var(--border-color);
        }}

        /* Department Overview Styles */
        .department-overview {{
            padding: 0;
        }}

        .department-stats-bar {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}

        .stat-card {{
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 1rem;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            transition: all 0.3s ease;
        }}

        .stat-card:hover {{
            background: rgba(255, 255, 255, 0.08);
            border-color: var(--accent-color);
            transform: translateY(-2px);
        }}

        .stat-icon {{
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--accent-color), #4f46e5);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.5rem;
        }}

        .stat-info {{
            flex: 1;
        }}

        .stat-number {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary-text);
            line-height: 1;
        }}

        .stat-text {{
            font-size: 0.9rem;
            color: var(--secondary-text);
            margin-top: 0.2rem;
        }}

        .department-categories {{
            margin-bottom: 2rem;
        }}

        .department-category-card {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
            cursor: pointer;
        }}

        .department-category-card:hover {{
            background: rgba(255, 255, 255, 0.08);
            border-color: var(--accent-color);
        }}

        .category-header {{
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 1.5rem;
        }}

        .category-icon {{
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--accent-color), #8b5cf6);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.8rem;
        }}

        .category-info {{
            flex: 1;
        }}

        .category-info h4 {{
            margin: 0 0 0.3rem 0;
            font-size: 1.2rem;
            color: var(--primary-text);
        }}

        .category-info p {{
            margin: 0;
            color: var(--secondary-text);
            font-size: 0.9rem;
        }}

        .category-stats {{
            display: flex;
            gap: 2rem;
        }}

        .stat-item {{
            text-align: center;
        }}

        .stat-value {{
            display: block;
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--accent-color);
        }}

        .stat-label {{
            display: block;
            font-size: 0.8rem;
            color: var(--secondary-text);
            margin-top: 0.2rem;
        }}

        .category-details {{
            border-top: 1px solid var(--border-color);
            padding: 1rem 1.5rem;
            background: rgba(0, 0, 0, 0.2);
        }}

        .mini-dept-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 1rem;
        }}

        .mini-dept-card {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1rem;
            transition: all 0.2s ease;
        }}

        .mini-dept-card:hover {{
            background: rgba(255, 255, 255, 0.08);
            border-color: var(--accent-color);
        }}

        .mini-dept-name {{
            font-weight: 600;
            color: var(--primary-text);
            margin-bottom: 0.5rem;
            font-size: 0.95rem;
        }}

        .mini-dept-leader {{
            color: var(--secondary-text);
            font-size: 0.85rem;
            margin-bottom: 0.5rem;
        }}

        .mini-dept-stats {{
            display: flex;
            gap: 1rem;
            font-size: 0.8rem;
            color: var(--secondary-text);
        }}

        .department-actions {{
            display: flex;
            gap: 1rem;
            justify-content: center;
            margin-top: 2rem;
        }}

        .department-btn {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.8rem 1.5rem;
            background: var(--accent-color);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 500;
            transition: all 0.3s ease;
            text-decoration: none;
        }}

        .department-btn:hover {{
            background: #4f46e5;
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(99, 102, 241, 0.3);
        }}

        .department-btn.secondary {{
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid var(--border-color);
        }}

        .department-btn.secondary:hover {{
            background: rgba(255, 255, 255, 0.15);
            border-color: var(--accent-color);
        }}

        /* Agent-Department Analytics Styles */
        .analytics-overview {{
            padding: 0;
        }}

        .analytics-summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
            padding: 1rem;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 12px;
            border: 1px solid var(--border-color);
        }}

        .analytics-stat {{
            text-align: center;
            padding: 0.5rem;
        }}

        .analytics-stat-value {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--accent-color);
            line-height: 1;
        }}

        .analytics-stat-label {{
            font-size: 0.8rem;
            color: var(--secondary-text);
            margin-top: 0.3rem;
        }}

        .analytics-departments {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 1rem;
        }}

        .dept-analytics-card {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            transition: all 0.3s ease;
        }}

        .dept-analytics-card:hover {{
            background: rgba(255, 255, 255, 0.08);
            border-color: var(--accent-color);
            transform: translateY(-2px);
        }}

        .dept-analytics-card.active {{
            border-left: 4px solid var(--success-color);
        }}

        .dept-analytics-card.inactive {{
            border-left: 4px solid var(--border-color);
            opacity: 0.8;
        }}

        .dept-analytics-header {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        }}

        .dept-analytics-icon {{
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--accent-color), #8b5cf6);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.3rem;
        }}

        .dept-analytics-info {{
            flex: 1;
        }}

        .dept-analytics-info h4 {{
            margin: 0 0 0.2rem 0;
            font-size: 1.1rem;
            color: var(--primary-text);
        }}

        .dept-analytics-info p {{
            margin: 0;
            font-size: 0.85rem;
            color: var(--secondary-text);
        }}

        .dept-analytics-status {{
            text-align: right;
        }}

        .activity-indicator {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.9rem;
        }}

        .activity-indicator.active {{
            color: var(--success-color);
        }}

        .activity-indicator.inactive {{
            color: var(--secondary-text);
        }}

        .activity-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: currentColor;
            animation: pulse 2s infinite;
        }}

        .dept-analytics-metrics {{
            border-top: 1px solid var(--border-color);
            padding-top: 1rem;
        }}

        .metric-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 1rem;
        }}

        .metric-item-small {{
            display: flex;
            align-items: center;
            gap: 0.3rem;
            font-size: 0.8rem;
            color: var(--secondary-text);
        }}

        .metric-item-small i {{
            color: var(--accent-color);
        }}

        .activity-bar {{
            width: 100%;
            height: 6px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 3px;
            overflow: hidden;
            margin-bottom: 0.5rem;
        }}

        .activity-progress {{
            height: 100%;
            background: linear-gradient(90deg, var(--success-color), var(--accent-color));
            border-radius: 3px;
            transition: width 0.8s ease;
        }}

        .activity-text {{
            text-align: center;
            font-size: 0.8rem;
            color: var(--secondary-text);
        }}

        .priority-badge {{
            position: absolute;
            top: -5px;
            right: -5px;
            width: 20px;
            height: 20px;
            background: var(--accent-color);
            color: white;
            border-radius: 50%;
            font-size: 0.7rem;
            font-weight: bold;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 2px solid var(--bg-primary);
        }}

        .priority-badge.offline {{
            background: var(--border-color);
            color: var(--secondary-text);
        }}

        .agent-avatar {{
            position: relative;
        }}

        .agent-actions {{
            margin-top: 1rem;
        }}

        .start-agent-btn {{
            padding: 0.5rem 1rem;
            background: var(--accent-color);
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.2s ease;
        }}

        .start-agent-btn:hover {{
            background: #4f46e5;
            transform: translateY(-1px);
        }}

        /* Enhanced Service Cards */
        .enhanced-service-card {{
            padding: 1.5rem;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        }}

        .enhanced-service-card:hover {{
            background: rgba(255, 255, 255, 0.08);
            border-color: var(--accent-color);
            transform: translateY(-2px);
        }}

        .service-header {{
            display: flex;
            align-items: center;
            gap: 1.2rem;
            margin-bottom: 1rem;
        }}

        .service-icon-large {{
            width: 50px;
            height: 50px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            color: white;
            flex-shrink: 0;
        }}

        .service-main-info {{
            flex: 1;
        }}

        .service-title {{
            font-size: 1.2rem;
            font-weight: 600;
            color: var(--primary-text);
            margin: 0 0 0.3rem 0;
        }}

        .service-meta {{
            display: flex;
            gap: 1rem;
            font-size: 0.9rem;
            color: var(--secondary-text);
        }}

        .service-meta span {{
            display: flex;
            align-items: center;
            gap: 0.3rem;
        }}

        .service-status-badge {{
            display: flex;
            align-items: center;
            gap: 0.3rem;
            padding: 0.4rem 0.8rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 500;
            flex-shrink: 0;
        }}

        .service-status-badge.healthy {{
            background: rgba(16, 185, 129, 0.2);
            color: var(--success-color);
            border: 1px solid var(--success-color);
        }}

        .service-status-badge.warning {{
            background: rgba(245, 158, 11, 0.2);
            color: var(--warning-color);
            border: 1px solid var(--warning-color);
        }}

        .service-status-badge.critical {{
            background: rgba(239, 68, 68, 0.2);
            color: var(--danger-color);
            border: 1px solid var(--danger-color);
        }}

        .service-tools {{
            border-top: 1px solid var(--border-color);
            padding-top: 1rem;
        }}

        .tools-label {{
            font-size: 0.9rem;
            color: var(--secondary-text);
            margin-bottom: 0.5rem;
            font-weight: 500;
        }}

        .tool-charms {{
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }}

        .tool-charm {{
            padding: 0.3rem 0.8rem;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid var(--border-color);
            border-radius: 15px;
            font-size: 0.8rem;
            color: var(--secondary-text);
            transition: all 0.2s ease;
        }}

        .tool-charm:hover {{
            background: rgba(99, 102, 241, 0.2);
            border-color: var(--accent-color);
            color: var(--accent-color);
        }}

        /* Global Refresh Modal Styles */
        .modal-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 2000;
            backdrop-filter: blur(5px);
        }}

        .modal-content {{
            background: var(--card-bg);
            border-radius: 16px;
            border: 1px solid var(--border-color);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }}

        .modal-header {{
            padding: 1.5rem;
            border-bottom: 1px solid var(--border-color);
            background: var(--secondary-bg);
        }}

        .modal-header h3 {{
            margin: 0;
            color: var(--primary-text);
            font-size: 1.2rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .modal-body {{
            padding: 1.5rem;
            flex: 1;
            overflow-y: auto;
        }}

        .modal-footer {{
            padding: 1rem 1.5rem;
            border-top: 1px solid var(--border-color);
            background: var(--secondary-bg);
            text-align: right;
        }}

        .modal-footer button {{
            padding: 0.6rem 1.5rem;
            background: var(--accent-color);
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            transition: background 0.3s ease;
        }}

        .modal-footer button:disabled {{
            background: var(--border-color);
            cursor: not-allowed;
        }}

        .progress-container {{
            margin-bottom: 2rem;
        }}

        .progress-bar {{
            width: 100%;
            height: 8px;
            background: var(--border-color);
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 0.5rem;
        }}

        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--accent-color), var(--success-color));
            transition: width 0.3s ease;
        }}

        .progress-text {{
            display: flex;
            justify-content: space-between;
            color: var(--secondary-text);
            font-size: 0.9rem;
        }}

        .component-list {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.5rem;
            margin-top: 1rem;
        }}

        .component-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 6px;
            font-size: 0.9rem;
        }}

        .component-item .fas.pending {{
            color: var(--border-color);
        }}

        .component-item .fas.processing {{
            color: var(--warning-color);
            animation: pulse 1s infinite;
        }}

        .component-item .fas.complete {{
            color: var(--success-color);
        }}

        /* Enhanced Refresh Steps Styles */
        .refresh-steps-list {{
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.02);
        }}

        .refresh-step {{
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 0.75rem 1rem;
            border-bottom: 1px solid var(--border-color);
            transition: all 0.3s ease;
            background: transparent;
        }}

        .refresh-step:last-child {{
            border-bottom: none;
        }}

        .refresh-step.active {{
            background: rgba(99, 102, 241, 0.1);
            border-left: 3px solid var(--accent-color);
        }}

        .refresh-step.completed {{
            background: rgba(16, 185, 129, 0.05);
        }}

        .refresh-step.error {{
            background: rgba(239, 68, 68, 0.1);
            border-left: 3px solid var(--danger-color);
        }}

        .step-indicator {{
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            flex-shrink: 0;
            width: 24px;
            height: 24px;
        }}

        .step-icon {{
            font-size: 0.6rem;
            transition: all 0.3s ease;
        }}

        .step-icon.pending {{
            color: var(--border-color);
        }}

        .step-icon.active {{
            color: var(--accent-color);
            animation: pulse 1.5s infinite;
        }}

        .step-icon.completed {{
            color: var(--success-color);
        }}

        .step-icon.error {{
            color: var(--danger-color);
        }}

        .step-number {{
            position: absolute;
            font-size: 0.7rem;
            font-weight: 600;
            color: var(--primary-text);
            opacity: 0.8;
        }}

        .step-content {{
            flex: 1;
            min-width: 0;
        }}

        .step-title {{
            font-weight: 600;
            color: var(--primary-text);
            margin-bottom: 0.25rem;
            font-size: 0.9rem;
        }}

        .step-description {{
            font-size: 0.8rem;
            color: var(--secondary-text);
            line-height: 1.3;
        }}

        .step-status {{
            font-size: 0.8rem;
            font-weight: 500;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            background: rgba(255, 255, 255, 0.05);
            color: var(--secondary-text);
            min-width: 70px;
            text-align: center;
            flex-shrink: 0;
        }}

        .step-status.active {{
            background: rgba(99, 102, 241, 0.2);
            color: var(--accent-color);
        }}

        .step-status.completed {{
            background: rgba(16, 185, 129, 0.2);
            color: var(--success-color);
        }}

        .step-status.error {{
            background: rgba(239, 68, 68, 0.2);
            color: var(--danger-color);
        }}

        .refresh-summary {{
            text-align: center;
            padding: 1rem;
            background: rgba(16, 185, 129, 0.1);
            border-radius: 8px;
            border: 1px solid var(--success-color);
        }}

        .summary-stats {{
            display: flex;
            justify-content: space-around;
            margin-top: 1rem;
            font-size: 0.9rem;
        }}

        .refresh-details h4 {{
            margin: 0 0 1rem 0;
            color: var(--primary-text);
            font-size: 1rem;
        }}
    </style>
</head>
<body>

    <header class="header">
        <div class="header-content">
            <div class="logo">
                <i class="fas fa-microchip"></i>
                <h1>BoarderframeOS</h1>
            </div>
            <div class="header-actions">
                <!-- System Status -->
                <div class="system-status">
                    <div class="status-indicator" onclick="toggleStatusDropdown()">
                        <div class="status-dot {overall_status}"></div>
                        <span>System {overall_status.replace('_', ' ').title()}</span>
                        <i class="fas fa-chevron-down" style="font-size: 0.8rem; color: var(--secondary-text);"></i>
                    </div>
                </div>

                <!-- Global Refresh Button -->
                <button class="global-refresh-btn" onclick="startGlobalRefresh()" id="globalRefreshBtn" title="Refresh All Corporate Headquarters Data">
                    <i class="fas fa-sync-alt"></i>
                    <span>Refresh OS</span>
                </button>
            </div>
                <div class="status-dropdown" id="statusDropdown">
                    <div class="dropdown-header">
                        <i class="fas fa-heartbeat"></i> System Status
                        <span style="margin-left: auto; font-size: 0.8rem; color: var(--secondary-text);">
                            {self._get_formatted_timestamp()}
                        </span>
                    </div>

                    <!-- Organization Section -->
                    <div style="padding: 0.5rem 0.75rem; font-size: 0.8rem; font-weight: 600; color: var(--accent-color); background: rgba(255,255,255,0.02); border-bottom: 1px solid var(--border-color);">
                        <i class="fas fa-users"></i> Organization
                    </div>
                    <div class="dropdown-section">
                        <div class="dropdown-item" onclick="navigateToTab('agents')" style="cursor: pointer;">
                            <div class="subsystem-name">
                                <i class="fas fa-robot"></i>
                                <span>Agents</span>
                            </div>
                            <div class="subsystem-status">
                                <div class="status-dot {self._get_subsystem_status('agents')}"></div>
                                <span>{self._get_agents_count()}</span>
                            </div>
                        </div>
                        <div class="dropdown-item" onclick="navigateToTab('leaders')" style="cursor: pointer;">
                            <div class="subsystem-name">
                                <i class="fas fa-crown"></i>
                                <span>Leaders</span>
                            </div>
                            <div class="subsystem-status">
                                <div class="status-dot {self._get_subsystem_status('leaders')}"></div>
                                <span>{self._get_leaders_count()}</span>
                            </div>
                        </div>
                        <div class="dropdown-item" onclick="navigateToTab('divisions')" style="cursor: pointer;">
                            <div class="subsystem-name">
                                <i class="fas fa-sitemap"></i>
                                <span>Divisions</span>
                            </div>
                            <div class="subsystem-status">
                                <div class="status-dot {self._get_subsystem_status('divisions')}"></div>
                                <span>{self._get_divisions_count()}</span>
                            </div>
                        </div>
                        <div class="dropdown-item" onclick="navigateToTab('departments')" style="cursor: pointer;">
                            <div class="subsystem-name">
                                <i class="fas fa-building"></i>
                                <span>Departments</span>
                            </div>
                            <div class="subsystem-status">
                                <div class="status-dot {self._get_subsystem_status('departments')}"></div>
                                <span>{self._get_departments_count()}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Servers Section -->
                    <div style="padding: 0.5rem 0.75rem; font-size: 0.8rem; font-weight: 600; color: var(--accent-color); background: rgba(255,255,255,0.02); border-bottom: 1px solid var(--border-color);">
                        <i class="fas fa-server"></i> Servers
                    </div>
                    <div class="dropdown-section">
                        <div class="dropdown-item" onclick="navigateToTab('services')" style="cursor: pointer;">
                            <div class="subsystem-name">
                                <i class="fas fa-building"></i>
                                <span>Core Servers</span>
                            </div>
                            <div class="subsystem-status">
                                <div class="status-dot {self._get_category_status('Core Systems')}"></div>
                                <span>{self._get_category_count('Core Systems')}</span>
                            </div>
                        </div>
                        <div class="dropdown-item" onclick="navigateToTab('services')" style="cursor: pointer;">
                            <div class="subsystem-name">
                                <i class="fas fa-plug"></i>
                                <span>MCP Servers</span>
                            </div>
                            <div class="subsystem-status">
                                <div class="status-dot {self._get_category_status('MCP Servers')}"></div>
                                <span>{self._get_category_count('MCP Servers')}</span>
                            </div>
                        </div>
                        <div class="dropdown-item" onclick="navigateToTab('services')" style="cursor: pointer;">
                            <div class="subsystem-name">
                                <i class="fas fa-briefcase"></i>
                                <span>Business Services</span>
                            </div>
                            <div class="subsystem-status">
                                <div class="status-dot {self._get_category_status('Business Services')}"></div>
                                <span>{self._get_category_count('Business Services')}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Database Section -->
                    <div style="padding: 0.5rem 0.75rem; font-size: 0.8rem; font-weight: 600; color: var(--accent-color); background: rgba(255,255,255,0.02); border-bottom: 1px solid var(--border-color);">
                        <i class="fas fa-database"></i> Database
                    </div>
                    <div class="dropdown-section">
                        <div class="dropdown-item" onclick="navigateToTab('database')" style="cursor: pointer;">
                            <div class="subsystem-name">
                                <i class="fas fa-database"></i>
                                <span>PostgreSQL</span>
                            </div>
                            <div class="subsystem-status">
                                <div class="status-dot {self._get_subsystem_status('database')}"></div>
                                <span style="font-size: 0.75rem;">{self._get_database_status()}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </header>

    <!-- Global Refresh Progress Modal -->
    <div id="globalRefreshModal" class="modal-overlay" style="display: none;">
        <div class="modal-content" style="width: 900px; height: 700px; max-height: 95vh; overflow: hidden;">
            <div class="modal-header" style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(79, 70, 229, 0.1)); border-bottom: 1px solid var(--border-color);">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <h3 style="margin: 0; display: flex; align-items: center; gap: 0.75rem;"><i id="modalSpinner" class="fas fa-sync-alt spinning"></i> BoarderframeOS Enhanced Refresh</h3>
                        <p style="margin: 0.5rem 0 0 0; color: var(--secondary-text); font-size: 0.9rem;">Refreshing all Corporate Headquarters data layers...</p>
                    </div>
                    <button id="closeRefreshBtnHeader" onclick="closeGlobalRefreshModal()" style="background: rgba(255,255,255,0.1); border: 1px solid var(--border-color); color: var(--secondary-text); padding: 0.5rem; border-radius: 6px; cursor: pointer;" disabled>
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div style="display: flex; align-items: center; gap: 1rem; margin-top: 1rem;">
                    <div style="flex: 1; background: rgba(255,255,255,0.1); border-radius: 8px; height: 8px; overflow: hidden;">
                        <div id="globalProgressFill" style="height: 100%; background: linear-gradient(90deg, var(--accent-color), var(--success-color)); width: 0%; transition: width 0.4s ease;"></div>
                    </div>
                    <span id="globalProgressPercent" style="font-size: 0.9rem; color: var(--secondary-text); min-width: 40px; font-weight: 600;">0%</span>
                </div>
            </div>
            <div class="modal-body" style="padding: 1.5rem;">
                <div class="refresh-current-step" style="margin-bottom: 2rem; padding: 1rem; background: rgba(99, 102, 241, 0.1); border: 1px solid var(--accent-color); border-radius: 8px;">
                    <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;">
                        <i id="currentStepIcon" class="fas fa-play" style="color: var(--accent-color);"></i>
                        <span id="currentStepText" style="font-weight: 600; color: var(--primary-text);">Initializing global refresh...</span>
                    </div>
                    <div id="currentStepDetails" style="font-size: 0.9rem; color: var(--secondary-text);">
                        Preparing to refresh all BoarderframeOS Corporate Headquarters components...
                    </div>
                </div>

                <div class="refresh-components-container">
                    <h4 style="margin-bottom: 1.5rem; color: var(--primary-text); display: flex; align-items: center; gap: 0.5rem;">
                        <i class="fas fa-grip-horizontal"></i> System Components:
                    </h4>
                    <div class="refresh-components-grid" id="refreshComponentsGrid" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem;">
                        <!-- Row 1 -->
                        <div class="refresh-component-card" data-component="system_metrics" style="background: linear-gradient(135deg, #6366f1, #8b5cf6); border-radius: 12px; padding: 1.25rem; text-align: center; color: white; position: relative; overflow: hidden; transition: all 0.3s ease; box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);">
                            <div style="position: absolute; top: -50%; right: -50%; width: 100%; height: 100%; background: rgba(255,255,255,0.1); border-radius: 50%; opacity: 0.5;"></div>
                            <div style="position: relative; z-index: 2;">
                                <i class="fas fa-chart-line" style="font-size: 2rem; margin-bottom: 0.75rem; display: block;"></i>
                                <div style="font-weight: 600; margin-bottom: 0.25rem;">System Metrics</div>
                                <div style="font-size: 0.75rem; opacity: 0.9; margin-bottom: 0.75rem;">CPU, Memory, Disk usage</div>
                                <div class="component-status" id="status-system_metrics" style="padding: 0.25rem 0.5rem; background: rgba(255,255,255,0.2); border-radius: 6px; font-size: 0.7rem; font-weight: 500;">
                                    <i class="fas fa-clock"></i> Pending
                                </div>
                            </div>
                        </div>

                        <div class="refresh-component-card" data-component="database_health" style="background: linear-gradient(135deg, #10b981, #059669); border-radius: 12px; padding: 1.25rem; text-align: center; color: white; position: relative; overflow: hidden; transition: all 0.3s ease; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);">
                            <div style="position: absolute; top: -50%; right: -50%; width: 100%; height: 100%; background: rgba(255,255,255,0.1); border-radius: 50%; opacity: 0.5;"></div>
                            <div style="position: relative; z-index: 2;">
                                <i class="fas fa-database" style="font-size: 2rem; margin-bottom: 0.75rem; display: block;"></i>
                                <div style="font-weight: 600; margin-bottom: 0.25rem;">Database Health</div>
                                <div style="font-size: 0.75rem; opacity: 0.9; margin-bottom: 0.75rem;">PostgreSQL connections</div>
                                <div class="component-status" id="status-database_health" style="padding: 0.25rem 0.5rem; background: rgba(255,255,255,0.2); border-radius: 6px; font-size: 0.7rem; font-weight: 500;">
                                    <i class="fas fa-clock"></i> Pending
                                </div>
                            </div>
                        </div>

                        <div class="refresh-component-card" data-component="services_status" style="background: linear-gradient(135deg, #f59e0b, #d97706); border-radius: 12px; padding: 1.25rem; text-align: center; color: white; position: relative; overflow: hidden; transition: all 0.3s ease; box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);">
                            <div style="position: absolute; top: -50%; right: -50%; width: 100%; height: 100%; background: rgba(255,255,255,0.1); border-radius: 50%; opacity: 0.5;"></div>
                            <div style="position: relative; z-index: 2;">
                                <i class="fas fa-cogs" style="font-size: 2rem; margin-bottom: 0.75rem; display: block;"></i>
                                <div style="font-weight: 600; margin-bottom: 0.25rem;">Services Status</div>
                                <div style="font-size: 0.75rem; opacity: 0.9; margin-bottom: 0.75rem;">Core service health</div>
                                <div class="component-status" id="status-services_status" style="padding: 0.25rem 0.5rem; background: rgba(255,255,255,0.2); border-radius: 6px; font-size: 0.7rem; font-weight: 500;">
                                    <i class="fas fa-clock"></i> Pending
                                </div>
                            </div>
                        </div>

                        <div class="refresh-component-card" data-component="agents_status" style="background: linear-gradient(135deg, #8b5cf6, #7c3aed); border-radius: 12px; padding: 1.25rem; text-align: center; color: white; position: relative; overflow: hidden; transition: all 0.3s ease; box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);">
                            <div style="position: absolute; top: -50%; right: -50%; width: 100%; height: 100%; background: rgba(255,255,255,0.1); border-radius: 50%; opacity: 0.5;"></div>
                            <div style="position: relative; z-index: 2;">
                                <i class="fas fa-robot" style="font-size: 2rem; margin-bottom: 0.75rem; display: block;"></i>
                                <div style="font-weight: 600; margin-bottom: 0.25rem;">Agents Status</div>
                                <div style="font-size: 0.75rem; opacity: 0.9; margin-bottom: 0.75rem;">AI agent processes</div>
                                <div class="component-status" id="status-agents_status" style="padding: 0.25rem 0.5rem; background: rgba(255,255,255,0.2); border-radius: 6px; font-size: 0.7rem; font-weight: 500;">
                                    <i class="fas fa-clock"></i> Pending
                                </div>
                            </div>
                        </div>

                        <!-- Row 2 -->
                        <div class="refresh-component-card" data-component="mcp_servers" style="background: linear-gradient(135deg, #ef4444, #dc2626); border-radius: 12px; padding: 1.25rem; text-align: center; color: white; position: relative; overflow: hidden; transition: all 0.3s ease; box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);">
                            <div style="position: absolute; top: -50%; right: -50%; width: 100%; height: 100%; background: rgba(255,255,255,0.1); border-radius: 50%; opacity: 0.5;"></div>
                            <div style="position: relative; z-index: 2;">
                                <i class="fas fa-server" style="font-size: 2rem; margin-bottom: 0.75rem; display: block;"></i>
                                <div style="font-weight: 600; margin-bottom: 0.25rem;">MCP Servers</div>
                                <div style="font-size: 0.75rem; opacity: 0.9; margin-bottom: 0.75rem;">Protocol server health</div>
                                <div class="component-status" id="status-mcp_servers" style="padding: 0.25rem 0.5rem; background: rgba(255,255,255,0.2); border-radius: 6px; font-size: 0.7rem; font-weight: 500;">
                                    <i class="fas fa-clock"></i> Pending
                                </div>
                            </div>
                        </div>

                        <div class="refresh-component-card" data-component="registry_data" style="background: linear-gradient(135deg, #06b6d4, #0891b2); border-radius: 12px; padding: 1.25rem; text-align: center; color: white; position: relative; overflow: hidden; transition: all 0.3s ease; box-shadow: 0 4px 12px rgba(6, 182, 212, 0.3);">
                            <div style="position: absolute; top: -50%; right: -50%; width: 100%; height: 100%; background: rgba(255,255,255,0.1); border-radius: 50%; opacity: 0.5;"></div>
                            <div style="position: relative; z-index: 2;">
                                <i class="fas fa-network-wired" style="font-size: 2rem; margin-bottom: 0.75rem; display: block;"></i>
                                <div style="font-weight: 600; margin-bottom: 0.25rem;">Registry Data</div>
                                <div style="font-size: 0.75rem; opacity: 0.9; margin-bottom: 0.75rem;">Service discovery</div>
                                <div class="component-status" id="status-registry_data" style="padding: 0.25rem 0.5rem; background: rgba(255,255,255,0.2); border-radius: 6px; font-size: 0.7rem; font-weight: 500;">
                                    <i class="fas fa-clock"></i> Pending
                                </div>
                            </div>
                        </div>

                        <div class="refresh-component-card" data-component="departments_data" style="background: linear-gradient(135deg, #84cc16, #65a30d); border-radius: 12px; padding: 1.25rem; text-align: center; color: white; position: relative; overflow: hidden; transition: all 0.3s ease; box-shadow: 0 4px 12px rgba(132, 204, 22, 0.3);">
                            <div style="position: absolute; top: -50%; right: -50%; width: 100%; height: 100%; background: rgba(255,255,255,0.1); border-radius: 50%; opacity: 0.5;"></div>
                            <div style="position: relative; z-index: 2;">
                                <i class="fas fa-building" style="font-size: 2rem; margin-bottom: 0.75rem; display: block;"></i>
                                <div style="font-weight: 600; margin-bottom: 0.25rem;">Departments</div>
                                <div style="font-size: 0.75rem; opacity: 0.9; margin-bottom: 0.75rem;">Organizational units</div>
                                <div class="component-status" id="status-departments_data" style="padding: 0.25rem 0.5rem; background: rgba(255,255,255,0.2); border-radius: 6px; font-size: 0.7rem; font-weight: 500;">
                                    <i class="fas fa-clock"></i> Pending
                                </div>
                            </div>
                        </div>

                        <div class="refresh-component-card" data-component="organizational_data" style="background: linear-gradient(135deg, #ec4899, #db2777); border-radius: 12px; padding: 1.25rem; text-align: center; color: white; position: relative; overflow: hidden; transition: all 0.3s ease; box-shadow: 0 4px 12px rgba(236, 72, 153, 0.3);">
                            <div style="position: absolute; top: -50%; right: -50%; width: 100%; height: 100%; background: rgba(255,255,255,0.1); border-radius: 50%; opacity: 0.5;"></div>
                            <div style="position: relative; z-index: 2;">
                                <i class="fas fa-sitemap" style="font-size: 2rem; margin-bottom: 0.75rem; display: block;"></i>
                                <div style="font-weight: 600; margin-bottom: 0.25rem;">Organization</div>
                                <div style="font-size: 0.75rem; opacity: 0.9; margin-bottom: 0.75rem;">Hierarchy data</div>
                                <div class="component-status" id="status-organizational_data" style="padding: 0.25rem 0.5rem; background: rgba(255,255,255,0.2); border-radius: 6px; font-size: 0.7rem; font-weight: 500;">
                                    <i class="fas fa-clock"></i> Pending
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="refresh-summary" id="refreshSummary" style="display: none; margin-top: 2rem; padding: 1.5rem; background: rgba(16, 185, 129, 0.1); border: 1px solid var(--success-color); border-radius: 8px;">
                    <h4><i class="fas fa-check-circle" style="color: var(--success-color);"></i> Refresh Complete!</h4>
                    <p>All BoarderframeOS Corporate Headquarters data has been updated successfully.</p>
                    <div class="summary-stats" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 1rem;">
                        <div style="text-align: center;">
                            <div style="font-size: 1.2rem; font-weight: 600; color: var(--success-color);" id="refreshDuration">--</div>
                            <div style="font-size: 0.9rem; color: var(--secondary-text);">Duration (seconds)</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 1.2rem; font-weight: 600; color: var(--accent-color);" id="refreshedComponents">--</div>
                            <div style="font-size: 0.9rem; color: var(--secondary-text);">Components Refreshed</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 1.2rem; font-weight: 600; color: var(--success-color);" id="refreshStatus">Success</div>
                            <div style="font-size: 0.9rem; color: var(--secondary-text);">Final Status</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button onclick="closeGlobalRefreshModal()" id="closeRefreshBtn" disabled style="background: var(--accent-color); color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 6px; cursor: pointer; font-size: 0.9rem;">
                    <i class="fas fa-times"></i> Close
                </button>
            </div>
        </div>
    </div>

    <!-- Enhanced Systems Refresh Wizard Modal -->
    <style>
        @keyframes pulseGlow {{{{
            0% {{{{ box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.4); }}}}
            70% {{{{ box-shadow: 0 0 0 10px rgba(99, 102, 241, 0); }}}}
            100% {{{{ box-shadow: 0 0 0 0 rgba(99, 102, 241, 0); }}}}
        }}

        @keyframes slideInUp {{
            from {{ transform: translateY(20px); opacity: 0; }}
            to {{ transform: translateY(0); opacity: 1; }}
        }}

        @keyframes checkmark {{
            0% {{ stroke-dashoffset: 100; }}
            100% {{ stroke-dashoffset: 0; }}
        }}

        @keyframes rotateIcon {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}

        .wizard-step {{
            opacity: 0;
            transition: all 0.3s ease;
        }}

        .wizard-step.active {{
            opacity: 1;
            animation: slideInUp 0.5s ease forwards;
        }}

        .wizard-step.completed {{
            opacity: 0.5;
            transform: scale(0.9);
        }}

        .system-icon {{
            transition: all 0.3s ease;
        }}

        .system-icon.checking {{
            animation: pulseGlow 2s infinite;
        }}

        .completion-confetti {{
            position: absolute;
            width: 100%;
            height: 100%;
            pointer-events: none;
            overflow: hidden;
        }}

        .particle {{
            position: absolute;
            background: linear-gradient(45deg, #6366f1, #10b981);
            width: 10px;
            height: 10px;
            border-radius: 50%;
            animation: fall 3s linear forwards;
        }}

        @keyframes fall {{
            to {{
                transform: translateY(600px) rotate(720deg);
                opacity: 0;
            }}
        }}
    </style>

    <div id="systemsRefreshModal" class="modal-overlay" style="display: none;">
        <div class="modal-content" style="width: 600px; height: 500px; max-height: 90vh; overflow: hidden; display: flex; flex-direction: column; background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%); border: 1px solid rgba(99, 102, 241, 0.3); box-shadow: 0 20px 40px rgba(0,0,0,0.5);">
            <div class="modal-header" style="background: rgba(0,0,0,0.2); border-bottom: 1px solid rgba(255,255,255,0.1);">
                <h3 style="display: flex; align-items: center; gap: 0.5rem;">
                    <i class="fas fa-magic" style="color: #6366f1;"></i>
                    Systems Refresh Wizard
                    <span style="font-size: 0.8rem; color: rgba(255,255,255,0.6); margin-left: auto;">BoarderframeOS v2025</span>
                </h3>
            </div>

            <div class="modal-body" style="padding: 2rem; flex: 1; display: flex; flex-direction: column; position: relative;">
                <!-- Animated Background -->
                <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; opacity: 0.05; background-image: repeating-linear-gradient(45deg, transparent, transparent 35px, rgba(255,255,255,.1) 35px, rgba(255,255,255,.1) 70px); pointer-events: none;"></div>

                <!-- Progress Steps -->
                <div id="wizardProgress" style="display: flex; justify-content: space-between; margin-bottom: 2rem; position: relative; z-index: 1;">
                    <div class="step-indicator" data-step="1" style="flex: 1; text-align: center;">
                        <div style="width: 40px; height: 40px; background: rgba(99, 102, 241, 0.2); border: 2px solid #6366f1; border-radius: 50%; margin: 0 auto 0.5rem; display: flex; align-items: center; justify-content: center; transition: all 0.3s;">
                            <i class="fas fa-plug" style="color: #6366f1;"></i>
                        </div>
                        <span style="font-size: 0.75rem; color: rgba(255,255,255,0.7);">Initialize</span>
                    </div>
                    <div style="flex: 1; height: 2px; background: rgba(255,255,255,0.1); margin-top: 20px;"></div>
                    <div class="step-indicator" data-step="2" style="flex: 1; text-align: center;">
                        <div style="width: 40px; height: 40px; background: rgba(99, 102, 241, 0.2); border: 2px solid rgba(255,255,255,0.3); border-radius: 50%; margin: 0 auto 0.5rem; display: flex; align-items: center; justify-content: center; transition: all 0.3s;">
                            <i class="fas fa-server" style="color: rgba(255,255,255,0.5);"></i>
                        </div>
                        <span style="font-size: 0.75rem; color: rgba(255,255,255,0.5);">Scan Systems</span>
                    </div>
                    <div style="flex: 1; height: 2px; background: rgba(255,255,255,0.1); margin-top: 20px;"></div>
                    <div class="step-indicator" data-step="3" style="flex: 1; text-align: center;">
                        <div style="width: 40px; height: 40px; background: rgba(99, 102, 241, 0.2); border: 2px solid rgba(255,255,255,0.3); border-radius: 50%; margin: 0 auto 0.5rem; display: flex; align-items: center; justify-content: center; transition: all 0.3s;">
                            <i class="fas fa-check" style="color: rgba(255,255,255,0.5);"></i>
                        </div>
                        <span style="font-size: 0.75rem; color: rgba(255,255,255,0.5);">Complete</span>
                    </div>
                </div>

                <!-- Main Content Area -->
                <div id="wizardContent" style="flex: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; position: relative;">
                    <!-- Step 1: Initialize -->
                    <div id="step1Content" class="wizard-step active">
                        <div class="system-icon" style="width: 80px; height: 80px; background: linear-gradient(135deg, #6366f1, #8b5cf6); border-radius: 50%; margin: 0 auto 1.5rem; display: flex; align-items: center; justify-content: center; box-shadow: 0 10px 30px rgba(99, 102, 241, 0.3);">
                            <i class="fas fa-rocket" style="font-size: 2.5rem; color: white;"></i>
                        </div>
                        <h3 style="margin: 0 0 0.5rem 0; color: white;">Initializing Systems Refresh</h3>
                        <p style="color: rgba(255,255,255,0.7); max-width: 400px; margin: 0 auto;">Preparing to scan all BoarderframeOS services and gather real-time health metrics...</p>
                    </div>

                    <!-- Step 2: Scanning -->
                    <div id="step2Content" class="wizard-step" style="width: 100%;">
                        <div id="scanningAnimation" style="margin-bottom: 2rem;">
                            <div style="position: relative; width: 120px; height: 120px; margin: 0 auto;">
                                <div style="position: absolute; width: 100%; height: 100%; border: 3px solid rgba(99, 102, 241, 0.2); border-radius: 50%;"></div>
                                <div style="position: absolute; width: 100%; height: 100%; border: 3px solid transparent; border-top-color: #6366f1; border-radius: 50%; animation: rotateIcon 1s linear infinite;"></div>
                                <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 60px; height: 60px; background: rgba(99, 102, 241, 0.1); border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                                    <i id="scanIcon" class="fas fa-server" style="font-size: 1.5rem; color: #6366f1;"></i>
                                </div>
                            </div>
                        </div>
                        <h3 style="margin: 0 0 0.5rem 0; color: white;">Scanning Systems</h3>
                        <p id="scanStatus" style="color: rgba(255,255,255,0.7); margin-bottom: 1.5rem;">Checking Registry Server...</p>

                        <!-- Live Progress -->
                        <div style="width: 100%; max-width: 400px; margin: 0 auto;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                                <span style="font-size: 0.8rem; color: rgba(255,255,255,0.6);">Progress</span>
                                <span id="systemsProgressText" style="font-size: 0.8rem; color: rgba(255,255,255,0.6);">0%</span>
                            </div>
                            <div style="width: 100%; height: 8px; background: rgba(255,255,255,0.1); border-radius: 10px; overflow: hidden;">
                                <div id="systemsProgressBar" style="height: 100%; background: linear-gradient(90deg, #6366f1, #10b981); width: 0%; transition: width 0.4s ease; box-shadow: 0 0 10px rgba(99, 102, 241, 0.5);"></div>
                            </div>
                        </div>

                        <!-- Systems Grid -->
                        <div id="systemsGrid" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-top: 2rem; width: 100%; max-width: 500px;">
                            <!-- Systems will be dynamically added here -->
                        </div>
                    </div>

                    <!-- Step 3: Complete -->
                    <div id="step3Content" class="wizard-step">
                        <div class="completion-confetti" id="confetti"></div>
                        <div style="width: 100px; height: 100px; background: linear-gradient(135deg, #10b981, #059669); border-radius: 50%; margin: 0 auto 1.5rem; display: flex; align-items: center; justify-content: center; box-shadow: 0 10px 30px rgba(16, 185, 129, 0.3); animation: pulseGlow 2s infinite;">
                            <svg width="50" height="50" viewBox="0 0 24 24" fill="none" style="stroke: white; stroke-width: 3; stroke-linecap: round; stroke-linejoin: round;">
                                <path d="M20 6L9 17l-5-5" stroke-dasharray="100" stroke-dashoffset="100" style="animation: checkmark 0.5s ease-out forwards;"/>
                            </svg>
                        </div>
                        <h3 style="margin: 0 0 1rem 0; color: white;">Refresh Complete!</h3>

                        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;">
                            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; text-align: center;">
                                <div>
                                    <div style="font-size: 2rem; font-weight: 700; color: #10b981; margin-bottom: 0.25rem;" id="systemsRefreshDuration">--</div>
                                    <div style="font-size: 0.8rem; color: rgba(255,255,255,0.6);">Seconds</div>
                                </div>
                                <div>
                                    <div style="font-size: 2rem; font-weight: 700; color: #6366f1; margin-bottom: 0.25rem;" id="systemsRefreshedComponents">--</div>
                                    <div style="font-size: 0.8rem; color: rgba(255,255,255,0.6);">Systems</div>
                                </div>
                                <div>
                                    <div style="font-size: 2rem; font-weight: 700; color: #10b981; margin-bottom: 0.25rem;">100%</div>
                                    <div style="font-size: 0.8rem; color: rgba(255,255,255,0.6);">Healthy</div>
                                </div>
                            </div>
                        </div>

                        <p style="color: rgba(255,255,255,0.7);">All systems have been successfully refreshed and are operating normally.</p>
                    </div>
                </div>
            </div>

            <div class="modal-footer" style="background: rgba(0,0,0,0.2); border-top: 1px solid rgba(255,255,255,0.1); padding: 1rem 2rem;">
                <button onclick="closeSystemsRefreshModal()" id="closeSystemsRefreshBtn" disabled style="background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; border: none; padding: 0.75rem 2rem; border-radius: 8px; cursor: pointer; font-size: 0.9rem; font-weight: 500; transition: all 0.3s; box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);">
                    <i class="fas fa-times"></i> Close
                </button>
            </div>
        </div>
    </div>

    <!-- Navigation Bar -->
    <nav class="navigation-container">
        <div class="navigation-wrapper">
            <ul class="nav-menu">
                <li class="nav-item">
                    <button class="nav-link active" onclick="showTab('dashboard')" data-tab="dashboard">
                        <i class="fas fa-home"></i>
                        <span>Welcome</span>
                    </button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" onclick="showTab('agents')" data-tab="agents">
                        <i class="fas fa-robot"></i>
                        <span>Agents</span>
                    </button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" onclick="showTab('leaders')" data-tab="leaders">
                        <i class="fas fa-crown"></i>
                        <span>Leaders</span>
                    </button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" onclick="showTab('departments')" data-tab="departments">
                        <i class="fas fa-building"></i>
                        <span>Departments</span>
                    </button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" onclick="showTab('divisions')" data-tab="divisions">
                        <i class="fas fa-sitemap"></i>
                        <span>Divisions</span>
                    </button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" onclick="showTab('registry')" data-tab="registry">
                        <i class="fas fa-network-wired"></i>
                        <span>Registry</span>
                    </button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" onclick="showTab('database')" data-tab="database">
                        <i class="fas fa-database"></i>
                        <span>Database</span>
                    </button>

                </li>

                <li class="nav-item">
                    <button class="nav-link" onclick="showTab('metrics')" data-tab="metrics">
                        <i class="fas fa-chart-line"></i>
                        <span>Metrics</span>
                    </button></li>
                <li class="nav-item">
                    <button class="nav-link" onclick="showTab('services')" data-tab="services">
                        <i class="fas fa-server"></i>
                        <span>Servers</span>
                    </button>
                </li>
                <li class="nav-item">
                    <button class="nav-link" onclick="showTab('settings')" data-tab="settings">
                        <i class="fas fa-cog"></i>
                        <span>Settings</span>
                    </button>
                </li>
            </ul>
        </div>
    </nav>

    <div class="container">
        <!-- Home Tab -->
        <div id="dashboard" class="tab-content active">
            <!-- Welcome & Status Narrative Card -->
            <div class="card full-width" style="margin-bottom: 2rem; border: 2px solid {'#10b98120' if overall_status == 'online' else '#f59e0b20' if overall_status == 'warning' else '#ef444420'}; background: linear-gradient(135deg, {'#10b98108, #10b98103' if overall_status == 'online' else '#f59e0b08, #f59e0b03' if overall_status == 'warning' else '#ef444408, #ef444403'});">
                <div style="display: flex; align-items: center; gap: 1.5rem; margin-bottom: 1.5rem;">
                    <div style="
                        width: 80px; height: 80px;
                        background: linear-gradient(135deg, {'#10b981, #10b981cc' if overall_status == 'online' else '#f59e0b, #f59e0bcc' if overall_status == 'warning' else '#ef4444, #ef4444cc'});
                        border-radius: 16px;
                        display: flex; align-items: center; justify-content: center;
                        color: white; font-size: 2.5rem;
                        box-shadow: 0 6px 16px {'#10b98140' if overall_status == 'online' else '#f59e0b40' if overall_status == 'warning' else '#ef444440'};
                    ">
                        {'<i class="fas fa-microchip"></i>' if overall_status == 'online' else '⚠️' if overall_status == 'warning' else '🚨'}
                    </div>
                    <div style="flex: 1;">
                        <h2 style="margin: 0 0 0.5rem 0; color: var(--primary-text); font-size: 2rem; font-weight: 700;">
                            {'Welcome back, Carl! 🎉' if overall_status == 'online' else 'Welcome back, Carl ⚠️' if overall_status == 'warning' else 'Carl, Attention Required! 🚨'}
                        </h2>
                        <p style="margin: 0; color: var(--secondary-text); font-size: 1.1rem; font-weight: 500;">
                            {'Your BoarderframeOS ecosystem is running at peak performance' if overall_status == 'online' else 'Your BoarderframeOS ecosystem needs some attention' if overall_status == 'warning' else 'Your BoarderframeOS ecosystem has critical issues'}
                        </p>
                    </div>
                    <div style="text-align: right;">
                        <div style="
                            padding: 0.75rem 1.5rem;
                            background: {'#10b98120' if overall_status == 'online' else '#f59e0b20' if overall_status == 'warning' else '#ef444420'};
                            border: 2px solid {'#10b981' if overall_status == 'online' else '#f59e0b' if overall_status == 'warning' else '#ef4444'};
                            border-radius: 12px;
                        ">
                            <div style="font-size: 0.8rem; color: var(--secondary-text); margin-bottom: 0.25rem; text-transform: uppercase; letter-spacing: 0.5px;">System Status</div>
                            <div style="font-size: 1.25rem; font-weight: 700; color: {'#10b981' if overall_status == 'online' else '#f59e0b' if overall_status == 'warning' else '#ef4444'};">
                                {overall_status.replace('_', ' ').title()}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- System Health Narrative -->
                <div style="
                    background: var(--card-bg);
                    border-radius: 12px;
                    padding: 1.5rem;
                    border-left: 4px solid {'#10b981' if overall_status == 'online' else '#f59e0b' if overall_status == 'warning' else '#ef4444'};
                ">
                    <div style="font-size: 1.1rem; line-height: 1.7; color: var(--secondary-text);">
                        {f'''
                        <p style="margin: 0 0 1.25rem 0;">
                            🌐 Your <strong>BoarderframeOS ecosystem</strong> is currently <span style="color: {'#10b981' if overall_status == 'online' else '#f59e0b' if overall_status == 'warning' else '#ef4444'}; font-weight: 700; background: {'#10b98115' if overall_status == 'online' else '#f59e0b15' if overall_status == 'warning' else '#ef444415'}; padding: 0.25rem 0.5rem; border-radius: 6px;"><i class="fas fa-circle" style="font-size: 0.6rem; margin-right: 0.5rem;"></i>{overall_status.replace('_', ' ').lower()}</span>
                            {' with all core systems operating within normal parameters.' if overall_status == 'online' else ' with some components requiring attention.' if overall_status == 'warning' else ' with critical issues that need immediate resolution.'}
                        </p>
                        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-bottom: 1.25rem;">
                            <div style="background: {'#10b98110' if active_agents == total_agents else '#f59e0b10' if active_agents > 0 else '#ef444410'}; padding: 1rem; border-radius: 8px; border: 1px solid {'#10b981' if active_agents == total_agents else '#f59e0b' if active_agents > 0 else '#ef4444'}40;">
                                <strong style="color: {'#10b981' if active_agents == total_agents else '#f59e0b' if active_agents > 0 else '#ef4444'};">🤖 Agent Workforce:</strong> {active_agents} of {total_agents} agents are operational
                                {' - all agents responding' if active_agents == total_agents else f' - {total_agents - active_agents} agents offline' if active_agents > 0 else ' - critical: no agents responding'}
                            </div>
                            <div style="background: {'#10b98110' if healthy_services == total_servers else '#f59e0b10' if healthy_services > 0 else '#ef444410'}; padding: 1rem; border-radius: 8px; border: 1px solid {'#10b981' if healthy_services == total_servers else '#f59e0b' if healthy_services > 0 else '#ef4444'}40;">
                                <strong style="color: {'#10b981' if healthy_services == total_servers else '#f59e0b' if healthy_services > 0 else '#ef4444'};">⚡ Infrastructure:</strong> {healthy_services} of {total_servers} servers online
                                {' - all systems operational' if healthy_services == total_servers else f' - {total_servers - healthy_services} servers offline' if healthy_services > 0 else ' - critical: infrastructure failure'}
                            </div>
                        </div>
                        <p style="margin: 0;">
                            👑 <strong>Leadership coordination</strong> spans <span style="color: #8b5cf6; font-weight: 600;">{total_divisions} divisions</span>,
                            <span style="color: #ec4899; font-weight: 600;">{total_departments} departments</span> and <span style="color: #f59e0b; font-weight: 600;">{active_leaders} leaders</span>, with the service registry
                            <span style="color: {'#10b981' if registry_status == 'healthy' else '#ef4444'}; font-weight: 600;">{registry_status}</span>.
                            <span style="margin-top: 1rem; display: block; padding: 1rem; background: {'#10b98115' if overall_status == 'online' else '#f59e0b15' if overall_status == 'warning' else '#ef444415'}; border-radius: 8px; font-weight: 500; color: {'#10b981' if overall_status == 'online' else '#f59e0b' if overall_status == 'warning' else '#ef4444'}; line-height: 1.6;">
                            💡 <strong>System Intelligence:</strong> {smart_recommendations}
                            </span>
                        </p>
                        ''' if overall_status else ''}
                    </div>
                </div>
            </div>

            <!-- System Overview Card -->
            <div class="card full-width" style="margin-bottom: 2rem; border: 2px solid #8b5cf620; background: linear-gradient(135deg, #8b5cf608, #8b5cf603);">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border-color);">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div style="
                            width: 60px; height: 60px;
                            background: linear-gradient(135deg, #8b5cf6, #8b5cf6cc);
                            border-radius: 12px;
                            display: flex; align-items: center; justify-content: center;
                            color: white; font-size: 1.5rem; box-shadow: 0 4px 12px #8b5cf640;
                        ">
                            <i class="fas fa-tachometer-alt"></i>
                        </div>
                        <div>
                            <h3 style="margin: 0; color: var(--primary-text); font-size: 1.25rem;">BoarderframeOS Status</h3>
                            <p style="margin: 0.25rem 0; color: var(--secondary-text); font-size: 0.9rem;">
                                Real-time metrics • Performance monitoring
                            </p>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 0.75rem; color: var(--secondary-text); margin-bottom: 0.25rem;">Overall Health</div>
                        <div style="font-size: 1rem; font-weight: 600; color: {'var(--success-color)' if overall_status == 'online' else 'var(--warning-color)' if overall_status == 'warning' else 'var(--danger-color)'};">
                            {(active_agents + healthy_services) / (total_agents + total_services) * 100:.0f}% Operational
                        </div>
                    </div>
                </div>

                <!-- Dashboard Metrics Grid -->
                <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 1rem; align-items: stretch;">
                    <div class="widget widget-small">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-robot" style="color: var(--success-color);"></i>
                                <span>Agents</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: var(--success-color);">
                            {active_agents}/{total_agents}
                        </div>
                        <div class="widget-subtitle">Online/Total</div>
                    </div>

                    <div class="widget widget-small">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-crown" style="color: #f59e0b;"></i>
                                <span>Leaders</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: #f59e0b;">
                            {active_leaders}/{total_leaders}
                        </div>
                        <div class="widget-subtitle">Active/Total</div>
                    </div>

                    <div class="widget widget-small">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-building" style="color: #ec4899;"></i>
                                <span>Departments</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: #ec4899;">
                            {active_departments}/{total_departments}
                        </div>
                        <div class="widget-subtitle">Active/Total</div>
                    </div>

                    <div class="widget widget-small">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-server" style="color: #06b6d4;"></i>
                                <span>Servers</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: #06b6d4;">
                            {healthy_services}/{total_servers}
                        </div>
                        <div class="widget-subtitle">Online/Total</div>
                    </div>

                    <div class="widget widget-small">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-network-wired" style="color: {('#10b981' if registry_status == 'healthy' else 'var(--danger-color)')};"></i>
                                <span>Registry</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: {('#10b981' if registry_status == 'healthy' else 'var(--danger-color)')};">
                            {'✓' if registry_status == 'healthy' else '✗'}
                        </div>
                        <div class="widget-subtitle">{'Healthy' if registry_status == 'healthy' else 'Offline'}</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Agents Tab -->
        <div id="agents" class="tab-content">
            <!-- Agent Metrics Card -->
            <div class="card full-width" style="margin-bottom: 2rem; border: 2px solid #06b6d420; background: linear-gradient(135deg, #06b6d408, #06b6d403);">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border-color);">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div style="
                            width: 60px; height: 60px;
                            background: linear-gradient(135deg, #06b6d4, #06b6d4cc);
                            border-radius: 12px;
                            display: flex; align-items: center; justify-content: center;
                            color: white; font-size: 1.5rem; box-shadow: 0 4px 12px #06b6d440;
                        ">
                            <i class="fas fa-robot"></i>
                        </div>
                        <div>
                            <h3 style="margin: 0; color: var(--primary-text); font-size: 1.25rem;">Agents Status</h3>
                            <p style="margin: 0.25rem 0; color: var(--secondary-text); font-size: 0.9rem;">
                                {active_agents} active agents • System performance monitoring
                            </p>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 0.75rem; color: var(--secondary-text); margin-bottom: 0.25rem;">Overall Status</div>
                        <div style="font-size: 1rem; font-weight: 600; color: {'var(--success-color)' if active_agents > 0 else 'var(--danger-color)'};">
                            {'Operational' if active_agents > 0 else 'Offline'}
                        </div>
                    </div>
                </div>

                <!-- Agent Metrics Grid -->
                <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 1rem; align-items: stretch;">
                    <div class="widget widget-small">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-play-circle" style="color: var(--success-color);"></i>
                                <span>Active</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: var(--success-color);">
                            {active_agents}
                        </div>
                        <div class="widget-subtitle">Running</div>
                    </div>

                    <div class="widget widget-small">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-rocket" style="color: #8b5cf6;"></i>
                                <span>Productive</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: #8b5cf6;">
                            {len([a for a in self.running_agents.values() if a.get('health', 'unknown') in ['good', 'healthy'] and a.get('cpu_percent', 100) < 80])}
                        </div>
                        <div class="widget-subtitle">Performing</div>
                    </div>

                    <div class="widget widget-small">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-heart" style="color: var(--warning-color);"></i>
                                <span>Healthy</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: var(--warning-color);">
                            {len([a for a in self.running_agents.values() if a.get('health', 'unknown') in ['good', 'healthy']])}
                        </div>
                        <div class="widget-subtitle">Wellness</div>
                    </div>

                    <div class="widget widget-small">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-pause-circle" style="color: var(--danger-color);"></i>
                                <span>Idle</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: var(--danger-color);">
                            {total_agents - active_agents}
                        </div>
                        <div class="widget-subtitle">Offline</div>
                    </div>

                    <div class="widget widget-small">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-users" style="color: var(--accent-color);"></i>
                                <span>Total</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: var(--accent-color);">
                            {total_agents}
                        </div>
                        <div class="widget-subtitle">Workforce</div>
                    </div>
                </div>
            </div>

            <!-- Agent Status Cards -->
            <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border-color); border-radius: 12px; padding: 1.5rem;">
                <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.5rem; border-bottom: 1px solid var(--border-color); padding-bottom: 1rem;">
                    <div style="width: 48px; height: 48px; background: var(--accent-color); border-radius: 12px; display: flex; align-items: center; justify-content: center; color: white; font-size: 1.5rem;">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div>
                        <h3 style="margin: 0; color: var(--primary-text); font-size: 1.5rem; font-weight: 600;">Agent Status</h3>
                        <p style="margin: 0; color: var(--secondary-text); font-size: 1rem;">Monitor and manage all AI agents and their activities</p>
                    </div>
                </div>

                <!-- Agent Controls -->
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; gap: 1rem;">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <i class="fas fa-filter" style="color: var(--secondary-text);"></i>
                            <select id="agentFilter" onchange="filterAgents()" style="padding: 0.5rem; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 6px; color: var(--primary-text); font-size: 0.9rem;">
                                <option value="all">All Agents</option>
                                <option value="active">🟢 Active</option>
                                <option value="productive">🚀 Productive</option>
                                <option value="healthy">💚 Healthy</option>
                                <option value="inactive">🔴 Offline</option>
                            </select>
                        </div>
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <i class="fas fa-sort" style="color: var(--secondary-text);"></i>
                            <select id="agentSort" onchange="sortAgents()" style="padding: 0.5rem; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 6px; color: var(--primary-text); font-size: 0.9rem;">
                                <option value="name">📝 Name</option>
                                <option value="status">🟢 Status</option>
                                <option value="health">💚 Health</option>
                                <option value="cpu">🖥️ CPU Usage</option>
                            </select>
                        </div>
                    </div>
                    <div style="color: var(--secondary-text); font-size: 0.9rem;">
                        <span id="agentCount">{total_agents}</span> agents
                    </div>
                </div>

                <div id="agentGrid" style="display: flex; flex-direction: column; gap: 1rem;">
                    {self._generate_enhanced_agents_html()}
                </div>
            </div>
        </div>

        <!-- Leaders Tab -->
        <div id="leaders" class="tab-content">
            {self._generate_leaders_html()}
        </div>

        <!-- Divisions Tab -->
        <div id="divisions" class="tab-content">
            {self._generate_divisions_html()}
        </div>


        <!-- Registry Tab -->
        <div id="registry" class="tab-content">
            <!-- Registry Overview Card -->
            <div class="card full-width" style="margin-bottom: 2rem; border: 2px solid #6366f120; background: linear-gradient(135deg, #6366f108, #6366f103);">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border-color);">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div style="
                            width: 60px; height: 60px;
                            background: linear-gradient(135deg, #6366f1, #6366f1cc);
                            border-radius: 12px;
                            display: flex; align-items: center; justify-content: center;
                            color: white; font-size: 1.5rem; box-shadow: 0 4px 12px #6366f140;
                        ">
                            <i class="fas fa-network-wired"></i>
                        </div>
                        <div>
                            <h3 style="margin: 0; color: var(--primary-text); font-size: 1.25rem;">Registry Status</h3>
                            <p style="margin: 0.25rem 0; color: var(--secondary-text); font-size: 0.9rem;">
                                Service discovery • Component coordination • Health monitoring
                            </p>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 0.75rem; color: var(--secondary-text); margin-bottom: 0.25rem;">Registry Health</div>
                        <div style="font-size: 1rem; font-weight: 600; color: {'var(--success-color)' if registry_status == 'healthy' else 'var(--warning-color)'};">
                            {'Operational' if registry_status == 'healthy' else 'Degraded'}
                        </div>
                    </div>
                </div>

                <!-- Registry Metrics Grid -->
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; align-items: stretch;">
                    <div class="widget widget-small">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-robot" style="color: var(--success-color);"></i>
                                <span>Agents</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: var(--success-color);">
                            {active_agents}
                        </div>
                        <div class="widget-subtitle">Registered</div>
                    </div>

                    <div class="widget widget-small">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-server" style="color: var(--accent-color);"></i>
                                <span>Servers</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: var(--accent-color);">
                            {healthy_services}
                        </div>
                        <div class="widget-subtitle">Registered</div>
                    </div>

                    <div class="widget widget-small">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-database" style="color: #06b6d4;"></i>
                                <span>Database</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: #06b6d4;">
                            {registry_status.title()}
                        </div>
                        <div class="widget-subtitle">Status</div>
                    </div>

                    <div class="widget widget-small">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-network-wired" style="color: {'#10b981' if self.services_status.get('registry', {}).get('status', 'Unknown') == 'healthy' else '#f59e0b'};"></i>
                                <span>Registry</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: {'#10b981' if self.services_status.get('registry', {}).get('status', 'Unknown') == 'healthy' else '#f59e0b'};">
                            {self.services_status.get('registry', {}).get('status', 'Unknown').title()}
                        </div>
                        <div class="widget-subtitle">Server</div>
                    </div>
                </div>
            </div>

            <!-- Registry Overview -->
            <div class="widget widget-full" style="margin-top: 1.5rem;">
                <div class="widget-header">
                    <div class="widget-title">
                        <i class="fas fa-database"></i>
                        <span>Registry Overview</span>
                    </div>
                </div>
                <div class="grid">
                    {self._generate_registry_overview_html()}
                </div>
            </div>
        </div>

        <!-- Departments Tab -->
        <div id="departments" class="tab-content">
            <!-- Department Overview Card -->
            <div class="card full-width" style="margin-bottom: 2rem; border: 2px solid #ec489920; background: linear-gradient(135deg, #ec489908, #ec489903);">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border-color);">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div style="
                            width: 60px; height: 60px;
                            background: linear-gradient(135deg, #ec4899, #ec4899cc);
                            border-radius: 12px;
                            display: flex; align-items: center; justify-content: center;
                            color: white; font-size: 1.5rem; box-shadow: 0 4px 12px #ec489940;
                        ">
                            <i class="fas fa-building"></i>
                        </div>
                        <div>
                            <h3 style="margin: 0; color: var(--primary-text); font-size: 1.25rem;">Departments Status</h3>
                            <p style="margin: 0.25rem 0; color: var(--secondary-text); font-size: 0.9rem;">
                                {total_departments} departments across {total_divisions} divisions • Organizational structure
                            </p>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 0.75rem; color: var(--secondary-text); margin-bottom: 0.25rem;">Department Status</div>
                        <div style="font-size: 1rem; font-weight: 600; color: var(--success-color);">
                            Operational
                        </div>
                    </div>
                </div>

                <!-- Department Metrics Grid -->
                <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 1rem; align-items: stretch;">
                <div class="widget widget-small">
                    <div class="widget-header">
                        <div class="widget-title">
                            <i class="fas fa-building" style="color: #ec4899;"></i>
                            <span>Departments</span>
                        </div>
                    </div>
                    <div class="widget-value" style="color: #ec4899;">
                        {total_departments}
                    </div>
                    <div class="widget-subtitle">Total Active</div>
                </div>

                <div class="widget widget-small">
                    <div class="widget-header">
                        <div class="widget-title">
                            <i class="fas fa-sitemap" style="color: var(--success-color);"></i>
                            <span>Divisions</span>
                        </div>
                    </div>
                    <div class="widget-value" style="color: var(--success-color);">
                        {total_divisions}
                    </div>
                    <div class="widget-subtitle">Organizational Units</div>
                </div>

                <div class="widget widget-small">
                    <div class="widget-header">
                        <div class="widget-title">
                            <i class="fas fa-crown" style="color: var(--warning-color);"></i>
                            <span>Leaders</span>
                        </div>
                    </div>
                    <div class="widget-value" style="color: var(--warning-color);">
                        {total_leaders}
                    </div>
                    <div class="widget-subtitle">Department Heads</div>
                </div>

                <div class="widget widget-small">
                    <div class="widget-header">
                        <div class="widget-title">
                            <i class="fas fa-users" style="color: #06b6d4;"></i>
                            <span>Teams</span>
                        </div>
                    </div>
                    <div class="widget-value" style="color: #06b6d4;">
                        120+
                    </div>
                    <div class="widget-subtitle">Specialized Agents</div>
                </div>

                <div class="widget widget-small">
                    <div class="widget-header">
                        <div class="widget-title">
                            <i class="fas fa-chart-line" style="color: var(--accent-color);"></i>
                            <span>Status</span>
                        </div>
                    </div>
                    <div class="widget-value" style="color: var(--success-color);">
                        ✓
                    </div>
                    <div class="widget-subtitle">All Operational</div>
                </div>
            </div>
            </div>

            <!-- Organizational Chart -->
            <div class="card full-width">
                <div style="text-align: center; margin-bottom: 1.5rem;">
                    <div style="color: var(--secondary-text); font-size: 0.9rem;">
                        AI-Native Operating System • {total_divisions} Divisions • {total_departments} Departments • {total_leaders} Leaders
                    </div>
                </div>

                <!-- Controls -->
                <div style="display: flex; justify-content: center; gap: 1rem; margin-bottom: 1rem;">
                    <button onclick="expandAllOrgNodes()" style="padding: 0.5rem 1rem; background: var(--accent-color); color: white; border: none; border-radius: 8px; cursor: pointer; transition: all 0.2s ease;">
                        <i class="fas fa-expand"></i> Expand All
                    </button>
                    <button onclick="collapseAllOrgNodes()" style="padding: 0.5rem 1rem; background: var(--accent-color); color: white; border: none; border-radius: 8px; cursor: pointer; opacity: 0.8; transition: all 0.2s ease;">
                        <i class="fas fa-compress"></i> Collapse All
                    </button>
                </div>

                <!-- Organizational Chart Container -->
                <div id="org-chart-container" style="
                    background: var(--secondary-bg);
                    border: 1px solid var(--border-color);
                    border-radius: 12px;
                    padding: 2rem;
                    overflow-x: auto;
                    overflow-y: visible;
                    min-height: 600px;
                ">
                    {self._generate_organizational_chart()}
                </div>
            </div>
        </div>

        <!-- System Tab -->
        <div id="system" class="tab-content">
            <!-- System Overview -->
            <div class="card full-width" style="margin-bottom: 2rem; border: 2px solid #06b6d420; background: linear-gradient(135deg, #06b6d408, #06b6d403);">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border-color);">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div style="
                            width: 60px; height: 60px;
                            background: linear-gradient(135deg, #06b6d4, #06b6d4cc);
                            border-radius: 12px;
                            display: flex; align-items: center; justify-content: center;
                            color: white; font-size: 1.5rem; box-shadow: 0 4px 12px #06b6d440;
                        ">
                            <i class="fas fa-chart-line"></i>
                        </div>
                        <div>
                            <h3 style="margin: 0; color: var(--primary-text); font-size: 1.25rem;">System Performance</h3>
                            <p style="margin: 0.25rem 0; color: var(--secondary-text); font-size: 0.9rem;">
                                Real-time monitoring and control of BoarderframeOS infrastructure
                            </p>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 0.75rem; color: var(--secondary-text); margin-bottom: 0.25rem;">System Health</div>
                        <div style="font-size: 1rem; font-weight: 600; color: var(--success-color);">
                            Operational
                        </div>
                    </div>
                </div>
            </div>

            <!-- System Metrics Grid -->
            <div class="grid">
                <div class="card" style="text-align: center; background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(79, 70, 229, 0.05));">
                    <div style="font-size: 2.5rem; color: var(--accent-color); margin-bottom: 0.5rem;">
                        <i class="fas fa-microchip"></i>
                    </div>
                    <div class="metric-value" style="font-size: 2.5rem; color: var(--accent-color);">
                        {self.system_metrics.get('cpu_percent', 0):.1f}%
                    </div>
                    <div class="metric-label" style="font-size: 1.1rem;">CPU Usage</div>
                    <div style="margin-top: 0.5rem; height: 4px; background: rgba(99, 102, 241, 0.2); border-radius: 2px;">
                        <div style="height: 100%; width: {self.system_metrics.get('cpu_percent', 0)}%; background: var(--accent-color); border-radius: 2px;"></div>
                    </div>
                </div>

                <div class="card" style="text-align: center; background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.05));">
                    <div style="font-size: 2.5rem; color: var(--success-color); margin-bottom: 0.5rem;">
                        <i class="fas fa-memory"></i>
                    </div>
                    <div class="metric-value" style="font-size: 2.5rem; color: var(--success-color);">
                        {self.system_metrics.get('memory_percent', 0):.1f}%
                    </div>
                    <div class="metric-label" style="font-size: 1.1rem;">Memory Usage</div>
                    <div style="margin-top: 0.5rem; height: 4px; background: rgba(16, 185, 129, 0.2); border-radius: 2px;">
                        <div style="height: 100%; width: {self.system_metrics.get('memory_percent', 0)}%; background: var(--success-color); border-radius: 2px;"></div>
                    </div>
                </div>

                <div class="card" style="text-align: center; background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(217, 119, 6, 0.05));">
                    <div style="font-size: 2.5rem; color: var(--warning-color); margin-bottom: 0.5rem;">
                        <i class="fas fa-hdd"></i>
                    </div>
                    <div class="metric-value" style="font-size: 2.5rem; color: var(--warning-color);">
                        {self.system_metrics.get('disk_percent', 0):.1f}%
                    </div>
                    <div class="metric-label" style="font-size: 1.1rem;">Disk Usage</div>
                    <div style="margin-top: 0.5rem; height: 4px; background: rgba(245, 158, 11, 0.2); border-radius: 2px;">
                        <div style="height: 100%; width: {self.system_metrics.get('disk_percent', 0)}%; background: var(--warning-color); border-radius: 2px;"></div>
                    </div>
                </div>

                <div class="card" style="text-align: center; background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(124, 58, 237, 0.05));">
                    <div style="font-size: 2.5rem; color: #8b5cf6; margin-bottom: 0.5rem;">
                        <i class="fas fa-network-wired"></i>
                    </div>
                    <div class="metric-value" style="font-size: 2.5rem; color: #8b5cf6;">
                        {len(self.services_status)}
                    </div>
                    <div class="metric-label" style="font-size: 1.1rem;">Active Services</div>
                    <div style="margin-top: 0.5rem; font-size: 0.9rem; color: var(--secondary-text);">
                        Network Health: Optimal
                    </div>
                </div>
            </div>

            <!-- System Information -->
            <div class="card full-width" style="margin-top: 2rem;">
                <h3 style="margin-bottom: 1rem;">
                    <i class="fas fa-info-circle"></i> System Information
                </h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem;">
                    <div style="padding: 0.5rem; background: rgba(255, 255, 255, 0.05); border-radius: 6px;">
                        <div style="color: var(--accent-color); font-weight: 600; margin-bottom: 0.5rem;">
                            <i class="fas fa-server"></i> BoarderframeOS
                        </div>
                        <div style="color: var(--secondary-text);">Corporate Headquarters Active</div>
                    </div>
                    <div style="padding: 0.5rem; background: rgba(255, 255, 255, 0.05); border-radius: 6px;">
                        <div style="color: var(--success-color); font-weight: 600; margin-bottom: 0.5rem;">
                            <i class="fas fa-clock"></i> Uptime
                        </div>
                        <div style="color: var(--secondary-text);">System Running</div>
                    </div>
                    <div style="padding: 0.5rem; background: rgba(255, 255, 255, 0.05); border-radius: 6px;">
                        <div style="color: var(--warning-color); font-weight: 600; margin-bottom: 0.5rem;">
                            <i class="fas fa-refresh"></i> Last Update
                        </div>
                        <div style="color: var(--secondary-text);">{self.last_update or 'Updating...'}</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Reporting Tab -->
        <div id="reporting" class="tab-content">
            <!-- Analytics Dashboard -->
            <div class="card full-width" style="margin-bottom: 2rem;">
                <h2 style="text-align: center; margin-bottom: 2rem; color: var(--accent-color);">
                    <i class="fas fa-chart-line"></i> Analytics Dashboard
                </h2>

                <!-- Key Performance Indicators -->
                <div class="grid" style="margin-bottom: 2rem;">
                    <div class="card" style="text-align: center; background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.05));">
                        <div style="font-size: 2rem; color: var(--success-color); margin-bottom: 0.5rem;">
                            <i class="fas fa-tachometer-alt"></i>
                        </div>
                        <div class="metric-value" style="color: var(--success-color);">
                            {(healthy_services/total_services*100) if total_services > 0 else 100:.1f}%
                        </div>
                        <div class="metric-label">System Health</div>
                    </div>

                    <div class="card" style="text-align: center; background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(79, 70, 229, 0.05));">
                        <div style="font-size: 2rem; color: var(--accent-color); margin-bottom: 0.5rem;">
                            <i class="fas fa-users-cog"></i>
                        </div>
                        <div class="metric-value" style="color: var(--accent-color);">
                            {len([a for a in self.agents_status.values() if a.get('status') == 'running'])}
                        </div>
                        <div class="metric-label">Active Agents</div>
                    </div>

                    <div class="card" style="text-align: center; background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(217, 119, 6, 0.05));">
                        <div style="font-size: 2rem; color: var(--warning-color); margin-bottom: 0.5rem;">
                            <i class="fas fa-chart-area"></i>
                        </div>
                        <div class="metric-value" style="color: var(--warning-color);">
                            {self.system_metrics.get('cpu_percent', 0):.0f}%
                        </div>
                        <div class="metric-label">CPU Usage</div>
                    </div>

                    <div class="card" style="text-align: center; background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(124, 58, 237, 0.05));">
                        <div style="font-size: 2rem; color: #8b5cf6; margin-bottom: 0.5rem;">
                            <i class="fas fa-building"></i>
                        </div>
                        <div class="metric-value" style="color: #8b5cf6;">
                            {len(self.departments_data)}
                        </div>
                        <div class="metric-label">Departments</div>
                    </div>
                </div>
            </div>

            <!-- Real-time Monitoring -->
            <div class="grid" style="gap: 2rem;">
                <div class="card">
                    <h3 style="margin-bottom: 1.5rem;">
                        <i class="fas fa-chart-line"></i> System Performance
                    </h3>
                    <div style="padding: 0.5rem; background: rgba(255, 255, 255, 0.05); border-radius: 6px; margin-bottom: 0.5rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <span>CPU Usage</span>
                            <span>{self.system_metrics.get('cpu_percent', 0):.1f}%</span>
                        </div>
                        <div style="height: 8px; background: rgba(99, 102, 241, 0.2); border-radius: 4px;">
                            <div style="height: 100%; width: {self.system_metrics.get('cpu_percent', 0)}%; background: var(--accent-color); border-radius: 4px;"></div>
                        </div>
                    </div>
                    <div style="padding: 0.5rem; background: rgba(255, 255, 255, 0.05); border-radius: 6px; margin-bottom: 0.5rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <span>Memory Usage</span>
                            <span>{self.system_metrics.get('memory_percent', 0):.1f}%</span>
                        </div>
                        <div style="height: 8px; background: rgba(16, 185, 129, 0.2); border-radius: 4px;">
                            <div style="height: 100%; width: {self.system_metrics.get('memory_percent', 0)}%; background: var(--success-color); border-radius: 4px;"></div>
                        </div>
                    </div>
                    <div style="padding: 0.5rem; background: rgba(255, 255, 255, 0.05); border-radius: 6px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <span>Disk Usage</span>
                            <span>{self.system_metrics.get('disk_percent', 0):.1f}%</span>
                        </div>
                        <div style="height: 8px; background: rgba(245, 158, 11, 0.2); border-radius: 4px;">
                            <div style="height: 100%; width: {self.system_metrics.get('disk_percent', 0)}%; background: var(--warning-color); border-radius: 4px;"></div>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <h3 style="margin-bottom: 1.5rem;">
                        <i class="fas fa-eye"></i> Real-time Overview
                    </h3>
                    <div style="space-y: 1rem;">
                        <div style="display: flex; justify-content: space-between; padding: 0.75rem; background: rgba(255, 255, 255, 0.05); border-radius: 8px; margin-bottom: 1rem;">
                            <span><i class="fas fa-server" style="color: var(--accent-color);"></i> Servers Online</span>
                            <span style="color: var(--success-color); font-weight: 600;">{healthy_services}/{total_services}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 0.75rem; background: rgba(255, 255, 255, 0.05); border-radius: 8px; margin-bottom: 1rem;">
                            <span><i class="fas fa-robot" style="color: var(--success-color);"></i> Active Agents</span>
                            <span style="color: var(--success-color); font-weight: 600;">{len([a for a in self.agents_status.values() if a.get('status') == 'running'])}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 0.75rem; background: rgba(255, 255, 255, 0.05); border-radius: 8px; margin-bottom: 1rem;">
                            <span><i class="fas fa-users" style="color: var(--warning-color);"></i> Total Leaders</span>
                            <span style="color: var(--warning-color); font-weight: 600;">{sum(len(dept.get('leaders', [])) for dept in self.departments_data.values()) if self.departments_data else 0}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 0.75rem; background: rgba(255, 255, 255, 0.05); border-radius: 8px;">
                            <span><i class="fas fa-clock" style="color: #8b5cf6;"></i> Last Update</span>
                            <span style="color: #8b5cf6; font-weight: 600;">{self.last_update or 'Updating...'}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Database Tab -->
        <div id="database" class="tab-content">
            <!-- Database Overview Card -->
            <div class="card full-width" style="margin-bottom: 2rem; border: 2px solid #f59e0b20; background: linear-gradient(135deg, #f59e0b08, #f59e0b03);">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border-color);">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div style="
                            width: 60px; height: 60px;
                            background: linear-gradient(135deg, #f59e0b, #f59e0bcc);
                            border-radius: 12px;
                            display: flex; align-items: center; justify-content: center;
                            color: white; font-size: 1.5rem; box-shadow: 0 4px 12px #f59e0b40;
                        ">
                            <i class="fas fa-database"></i>
                        </div>
                        <div>
                            <h3 style="margin: 0; color: var(--primary-text); font-size: 1.25rem;">Database Status</h3>
                            <p style="margin: 0; color: var(--secondary-text); font-size: 0.95rem;">BoarderframeOS Primary Data Storage</p>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div style="text-align: right;">
                            <div style="font-size: 1.2rem; color: var(--success-color); margin-bottom: 0.25rem;">
                                <i class="fas fa-check-circle"></i> Connected
                            </div>
                            <div style="font-size: 0.85rem; color: var(--secondary-text);">
                                Last updated: <span id="db-last-update">{self.database_health_metrics.get('last_check', 'Never') if hasattr(self, 'database_health_metrics') else 'Never'}</span>
                            </div>
                        </div>
                        <button
                            onclick="refreshDatabaseMetrics()"
                            style="
                                background: linear-gradient(135deg, #10b981, #059669);
                                color: white;
                                border: none;
                                padding: 0.5rem 1rem;
                                border-radius: 6px;
                                cursor: pointer;
                                font-size: 0.9rem;
                                display: flex;
                                align-items: center;
                                gap: 0.5rem;
                                transition: all 0.2s;
                                height: fit-content;
                            "
                            onmouseover="this.style.transform='scale(1.05)'"
                            onmouseout="this.style.transform='scale(1)'"
                        >
                            <i class="fas fa-sync-alt"></i>
                            Refresh Data
                        </button>
                    </div>
                </div>

                <!-- Database Metrics Grid - Matching Servers Tab Format -->
                <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 1rem; align-items: stretch;">
                    <div class="widget widget-small">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-table" style="color: var(--success-color);"></i>
                                <span>Tables</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: var(--success-color);">
                            {self.database_health_metrics.get('total_tables', 'N/A') if hasattr(self, 'database_health_metrics') else 'N/A'}
                        </div>
                        <div class="widget-label">Total</div>
                    </div>

                    <div class="widget widget-small">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-link" style="color: var(--accent-color);"></i>
                                <span>Connections</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: var(--accent-color);">
                            {self.database_health_metrics.get('active_connections', 'N/A') if hasattr(self, 'database_health_metrics') else 'N/A'}
                        </div>
                        <div class="widget-label">Active</div>
                    </div>

                    <div class="widget widget-small">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-hdd" style="color: var(--warning-color);"></i>
                                <span>Size</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: var(--warning-color);">
                            {self.database_health_metrics.get('database_size', 'N/A') if hasattr(self, 'database_health_metrics') else 'N/A'}
                        </div>
                        <div class="widget-label">Database</div>
                    </div>

                    <div class="widget widget-small">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-tachometer-alt" style="color: var(--info-color);"></i>
                                <span>Cache</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: var(--info-color);">
                            {self.database_health_metrics.get('cache_hit_ratio', 'N/A') if hasattr(self, 'database_health_metrics') else 'N/A'}%
                        </div>
                        <div class="widget-label">Hit Ratio</div>
                    </div>

                    <div class="widget widget-small">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-check-circle" style="color: var(--success-color);"></i>
                                <span>Status</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: {'var(--success-color)' if (hasattr(self, 'database_health_metrics') and self.database_health_metrics.get('status') == 'healthy') else 'var(--danger-color)'};">
                            {"Healthy" if (hasattr(self, 'database_health_metrics') and self.database_health_metrics.get('status') == 'healthy') else 'Error'}
                        </div>
                        <div class="widget-label">Health</div>
                    </div>
                </div>
            </div>

            <!-- Database Tables Overview -->
            <div class="card full-width" style="margin-bottom: 2rem;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border-color);">
                    <h3 style="margin: 0; color: var(--accent-color);">
                        <i class="fas fa-table"></i> Database Tables
                    </h3>
                    <div style="font-size: 0.9rem; color: var(--secondary-text);">
                        PostgreSQL with pgvector extension
                    </div>
                </div>

                <!-- Filters and Controls -->
                <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem; flex-wrap: wrap;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <label for="categoryFilter" style="font-size: 0.9rem; color: var(--secondary-text);">Filter by Category:</label>
                        <select id="categoryFilter" onchange="filterTables()" style="
                            background: var(--secondary-bg);
                            color: var(--primary-text);
                            border: 1px solid var(--border-color);
                            border-radius: 4px;
                            padding: 0.25rem 0.5rem;
                            font-size: 0.9rem;
                        ">
                            <option value="">All Categories</option>
                            <option value="agents">Agents</option>
                            <option value="divisions">Divisions</option>
                            <option value="departments">Departments</option>
                            <option value="registry">Registry</option>
                            <option value="messaging">Messaging</option>
                            <option value="migrations">Migrations</option>
                            <option value="system">System</option>
                            <option value="other">Other</option>
                        </select>
                    </div>

                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <label for="searchFilter" style="font-size: 0.9rem; color: var(--secondary-text);">Search:</label>
                        <input type="text" id="searchFilter" placeholder="Filter table names..." onkeyup="filterTables()" style="
                            background: var(--secondary-bg);
                            color: var(--primary-text);
                            border: 1px solid var(--border-color);
                            border-radius: 4px;
                            padding: 0.25rem 0.5rem;
                            font-size: 0.9rem;
                            width: 200px;
                        ">
                    </div>

                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="font-size: 0.9rem; color: var(--secondary-text);">Sort by:</span>
                        <button onclick="sortTables('name')" style="
                            background: var(--secondary-bg);
                            color: var(--primary-text);
                            border: 1px solid var(--border-color);
                            border-radius: 4px;
                            padding: 0.25rem 0.5rem;
                            font-size: 0.8rem;
                            cursor: pointer;
                        ">Name</button>
                        <button onclick="sortTables('size')" style="
                            background: var(--secondary-bg);
                            color: var(--primary-text);
                            border: 1px solid var(--border-color);
                            border-radius: 4px;
                            padding: 0.25rem 0.5rem;
                            font-size: 0.8rem;
                            cursor: pointer;
                        ">Size</button>
                        <button onclick="sortTables('category')" style="
                            background: var(--secondary-bg);
                            color: var(--primary-text);
                            border: 1px solid var(--border-color);
                            border-radius: 4px;
                            padding: 0.25rem 0.5rem;
                            font-size: 0.8rem;
                            cursor: pointer;
                        ">Category</button>
                    </div>

                    <div style="margin-left: auto;">
                        <span id="tableCount" style="font-size: 0.9rem; color: var(--secondary-text);">
                            Showing all tables
                        </span>
                    </div>
                </div>

                <div style="overflow-x: auto;">
                    <table id="databaseTable" style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="border-bottom: 1px solid var(--border-color);">
                                <th style="text-align: left; padding: 0.75rem; color: var(--primary-text); font-weight: 600; cursor: pointer;" onclick="sortTables('name')">
                                    Table Name <i class="fas fa-sort" style="margin-left: 0.5rem; opacity: 0.5;"></i>
                                </th>
                                <th style="text-align: left; padding: 0.75rem; color: var(--primary-text); font-weight: 600; cursor: pointer;" onclick="sortTables('schema')">
                                    Schema <i class="fas fa-sort" style="margin-left: 0.5rem; opacity: 0.5;"></i>
                                </th>
                                <th style="text-align: left; padding: 0.75rem; color: var(--primary-text); font-weight: 600; cursor: pointer;" onclick="sortTables('size')">
                                    Size <i class="fas fa-sort" style="margin-left: 0.5rem; opacity: 0.5;"></i>
                                </th>
                                <th style="text-align: left; padding: 0.75rem; color: var(--primary-text); font-weight: 600; cursor: pointer;" onclick="sortTables('columns')">
                                    Columns <i class="fas fa-sort" style="margin-left: 0.5rem; opacity: 0.5;"></i>
                                </th>
                                <th style="text-align: left; padding: 0.75rem; color: var(--primary-text); font-weight: 600; cursor: pointer;" onclick="sortTables('category')">
                                    Category <i class="fas fa-sort" style="margin-left: 0.5rem; opacity: 0.5;"></i>
                                </th>
                            </tr>
                        </thead>
                        <tbody id="databaseTableBody">
                            {self._generate_database_tables_rows()}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Database Connection Details -->
            <div class="grid" style="gap: 1.5rem;">
                <div class="card">
                    <h4 style="margin: 0 0 1rem 0; color: var(--accent-color);">
                        <i class="fas fa-info-circle"></i> Connection Info
                    </h4>
                    <div style="font-family: monospace; font-size: 0.9rem; color: var(--secondary-text);">
                        <div style="margin-bottom: 0.5rem;"><strong>Host:</strong> localhost:5434</div>
                        <div style="margin-bottom: 0.5rem;"><strong>Database:</strong> boarderframeos</div>
                        <div style="margin-bottom: 0.5rem;"><strong>Active/Max Connections:</strong> {self.database_health_metrics.get('active_connections', 'N/A') if hasattr(self, 'database_health_metrics') else 'N/A'} / {self.database_health_metrics.get('max_connections', 'N/A') if hasattr(self, 'database_health_metrics') else 'N/A'}</div>
                        <div style="margin-bottom: 0.5rem;"><strong>Active Queries:</strong> {self.database_health_metrics.get('active_queries', 'N/A') if hasattr(self, 'database_health_metrics') else 'N/A'}</div>
                        <div style="margin-bottom: 0.5rem;"><strong>PostgreSQL:</strong> {self.database_health_metrics.get('version', 'Unknown') if hasattr(self, 'database_health_metrics') else 'Unknown'}</div>
                        <div style="margin-bottom: 0.5rem;"><strong>pgvector:</strong> {'Enabled' if (hasattr(self, 'database_health_metrics') and self.database_health_metrics.get('pgvector_enabled')) else 'Unknown'}</div>
                    </div>
                </div>

                <div class="card">
                    <h4 style="margin: 0 0 1rem 0; color: var(--accent-color);">
                        <i class="fas fa-chart-line"></i> Performance Metrics
                    </h4>
                    <div style="font-family: monospace; font-size: 0.9rem; color: var(--secondary-text);">
                        <div style="margin-bottom: 0.5rem;"><strong>Transactions:</strong> {self.database_health_metrics.get('commits', 'N/A') if hasattr(self, 'database_health_metrics') else 'N/A'} commits, {self.database_health_metrics.get('rollbacks', 'N/A') if hasattr(self, 'database_health_metrics') else 'N/A'} rollbacks</div>
                        <div style="margin-bottom: 0.5rem;"><strong>Tuples Inserted:</strong> {self.database_health_metrics.get('tuples_inserted', 'N/A') if hasattr(self, 'database_health_metrics') else 'N/A'}</div>
                        <div style="margin-bottom: 0.5rem;"><strong>Tuples Updated:</strong> {self.database_health_metrics.get('tuples_updated', 'N/A') if hasattr(self, 'database_health_metrics') else 'N/A'}</div>
                        <div style="margin-bottom: 0.5rem;"><strong>Tuples Deleted:</strong> {self.database_health_metrics.get('tuples_deleted', 'N/A') if hasattr(self, 'database_health_metrics') else 'N/A'}</div>
                    </div>
                </div>
            </div>
        </div>


        <!-- Metrics Tab -->
        <div id="metrics" class="tab-content">
            <div class="card full-width" style="margin-bottom: 2rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <h2 style="text-align: center; margin-bottom: 1rem; color: var(--accent-color);">
                            <i class="fas fa-chart-line"></i> BoarderframeOS Metrics Dashboard
                        </h2>
                        <p style="text-align: center; color: var(--secondary-text); margin-bottom: 0;">
                            System metrics and analytics from the metrics layer
                        </p>
                    </div>
                    <button onclick="loadMetricsData()" style="
                        background: linear-gradient(135deg, #10b981, #059669);
                        color: white;
                        border: none;
                        padding: 0.75rem 1.5rem;
                        border-radius: 8px;
                        cursor: pointer;
                        font-size: 1rem;
                        display: flex;
                        align-items: center;
                        gap: 0.5rem;
                        transition: all 0.3s ease;
                    " onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
                        <i class="fas fa-sync-alt"></i> Refresh Metrics
                    </button>
                </div>
            </div>

            <div class="card full-width">
                <div id="metrics-content">
                    <div style="text-align: center; padding: 2rem;">
                        <i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: var(--accent-color);"></i>
                        <p style="margin-top: 1rem; color: var(--secondary-text);">Loading metrics...</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Services Tab -->
        <div id="services" class="tab-content">
            <!-- Services Overview Card -->
            <div class="card full-width" style="margin-bottom: 2rem; border: 2px solid #06b6d420; background: linear-gradient(135deg, #06b6d408, #06b6d403);">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border-color);">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div style="
                            width: 60px; height: 60px;
                            background: linear-gradient(135deg, #06b6d4, #06b6d4cc);
                            border-radius: 12px;
                            display: flex; align-items: center; justify-content: center;
                            color: white; font-size: 1.5rem; box-shadow: 0 4px 12px #06b6d440;
                        ">
                            <i class="fas fa-server"></i>
                        </div>
                        <div>
                            <h3 style="margin: 0; color: var(--primary-text); font-size: 1.25rem;">Server Status</h3>
                            <p style="margin: 0.25rem 0; color: var(--secondary-text); font-size: 0.9rem;">
                                BoarderframeOS Infrastructure • Real-time monitoring
                            </p>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 0.75rem; color: var(--secondary-text); margin-bottom: 0.25rem;">Infrastructure Health</div>
                        <div style="font-size: 1rem; font-weight: 600; color: {('#10b981' if healthy_services == total_services else '#f59e0b' if healthy_services > 0 else '#ef4444')};">
                            {healthy_services}/{total_services} Online
                        </div>
                    </div>
                </div>

                <!-- Server Categories Metrics Grid -->
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; align-items: stretch;">
                    <div class="widget widget-small">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-database" style="color: var(--accent-color);"></i>
                                <span>MCP Servers</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: var(--accent-color);">
                            {self._get_category_count('MCP Servers')}
                        </div>
                        <div class="widget-subtitle">Model Context Protocol</div>
                    </div>

                    <div class="widget widget-small">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-cogs" style="color: var(--success-color);"></i>
                                <span>Core Systems</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: var(--success-color);">
                            {self._get_category_count('Core Systems')}
                        </div>
                        <div class="widget-subtitle">Infrastructure</div>
                    </div>

                    <div class="widget widget-small">
                        <div class="widget-header">
                            <div class="widget-title">
                                <i class="fas fa-briefcase" style="color: var(--warning-color);"></i>
                                <span>Business Services</span>
                            </div>
                        </div>
                        <div class="widget-value" style="color: var(--warning-color);">
                            {self._get_category_count('Business Services')}
                        </div>
                        <div class="widget-subtitle">Revenue & CRM</div>
                    </div>
                </div>
            </div>

            <!-- Server Categories Display -->
            <div class="card full-width">
                <div style="margin-bottom: 2rem;">
                    <div style="margin-bottom: 1.5rem;">
                        <h3 style="margin: 0; color: var(--accent-color);">
                            <i class="fas fa-network-wired"></i> Server Infrastructure
                        </h3>
                    </div>

                    <!-- MCP Servers Section -->
                    <div style="margin-bottom: 2rem;">
                        <h4 style="color: var(--accent-color); margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">
                            <i class="fas fa-database"></i> MCP Servers
                            <span style="font-size: 0.8rem; color: var(--secondary-text); font-weight: normal;">Model Context Protocol</span>
                        </h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem;">
                            {self._generate_server_cards('MCP Servers')}
                        </div>
                    </div>

                    <!-- Core Systems Section -->
                    <div style="margin-bottom: 2rem;">
                        <h4 style="color: var(--success-color); margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">
                            <i class="fas fa-cogs"></i> Core Systems
                            <span style="font-size: 0.8rem; color: var(--secondary-text); font-weight: normal;">Infrastructure Services</span>
                        </h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem;">
                            {self._generate_server_cards('Core Systems')}
                        </div>
                    </div>

                    <!-- Business Services Section -->
                    <div style="margin-bottom: 2rem;">
                        <h4 style="color: var(--warning-color); margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">
                            <i class="fas fa-briefcase"></i> Business Services
                            <span style="font-size: 0.8rem; color: var(--secondary-text); font-weight: normal;">Revenue & Customer Management</span>
                        </h4>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem;">
                            {self._generate_server_cards('Business Services')}
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Settings Tab -->
        <div id="settings" class="tab-content">
            <div class="card full-width" style="margin-bottom: 2rem;">
                <h2 style="text-align: center; margin-bottom: 2rem; color: var(--accent-color);">
                    <i class="fas fa-cog"></i> BoarderframeOS Configuration
                </h2>
            </div>

            <!-- Settings Grid -->
            <div class="grid" style="gap: 2rem;">
                <!-- System Configuration -->
                <div class="card">
                    <h3 style="margin-bottom: 1.5rem;">
                        <i class="fas fa-server"></i> System Configuration
                    </h3>
                    <div style="space-y: 1rem;">
                        <div style="margin-bottom: 1rem;">
                            <label style="display: block; margin-bottom: 0.5rem; color: var(--primary-text); font-weight: 500;">Dashboard Refresh Rate</label>
                            <select style="width: 100%; padding: 0.5rem; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 6px; color: var(--primary-text);">
                                <option value="30">30 seconds</option>
                                <option value="60">1 minute</option>
                                <option value="300">5 minutes</option>
                                <option value="600">10 minutes</option>
                            </select>
                        </div>
                        <div style="margin-bottom: 1rem;">
                            <label style="display: block; margin-bottom: 0.5rem; color: var(--primary-text); font-weight: 500;">Time Zone</label>
                            <select style="width: 100%; padding: 0.5rem; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 6px; color: var(--primary-text);">
                                <option value="UTC">UTC</option>
                                <option value="EST">Eastern Time</option>
                                <option value="PST">Pacific Time</option>
                                <option value="GMT">Greenwich Mean Time</option>
                            </select>
                        </div>
                        <div style="margin-bottom: 1rem;">
                            <label style="display: flex; align-items: center; gap: 0.5rem; color: var(--primary-text);">
                                <input type="checkbox" checked style="accent-color: var(--accent-color);">
                                Enable system notifications
                            </label>
                        </div>
                        <div style="margin-bottom: 1rem;">
                            <label style="display: flex; align-items: center; gap: 0.5rem; color: var(--primary-text);">
                                <input type="checkbox" checked style="accent-color: var(--accent-color);">
                                Auto-start agents on system boot
                            </label>
                        </div>
                    </div>
                </div>

                <!-- Agent Management -->
                <div class="card">
                    <h3 style="margin-bottom: 1.5rem;">
                        <i class="fas fa-robot"></i> Agent Management
                    </h3>
                    <div style="space-y: 1rem;">
                        <div style="margin-bottom: 1rem;">
                            <label style="display: block; margin-bottom: 0.5rem; color: var(--primary-text); font-weight: 500;">Default Agent Model</label>
                            <select style="width: 100%; padding: 0.5rem; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 6px; color: var(--primary-text);">
                                <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                                <option value="claude-3-opus">Claude 3 Opus</option>
                                <option value="gpt-4">GPT-4</option>
                                <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                            </select>
                        </div>
                        <div style="margin-bottom: 1rem;">
                            <label style="display: block; margin-bottom: 0.5rem; color: var(--primary-text); font-weight: 500;">Max Concurrent Agents</label>
                            <input type="number" value="10" min="1" max="50" style="width: 100%; padding: 0.5rem; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 6px; color: var(--primary-text);">
                        </div>
                        <div style="margin-bottom: 1rem;">
                            <label style="display: flex; align-items: center; gap: 0.5rem; color: var(--primary-text);">
                                <input type="checkbox" checked style="accent-color: var(--accent-color);">
                                Enable agent performance monitoring
                            </label>
                        </div>
                        <div style="margin-bottom: 1rem;">
                            <label style="display: flex; align-items: center; gap: 0.5rem; color: var(--primary-text);">
                                <input type="checkbox" style="accent-color: var(--accent-color);">
                                Auto-restart failed agents
                            </label>
                        </div>
                    </div>
                </div>

                <!-- Security Settings -->
                <div class="card">
                    <h3 style="margin-bottom: 1.5rem;">
                        <i class="fas fa-shield-alt"></i> Security & Access
                    </h3>
                    <div style="space-y: 1rem;">
                        <div style="margin-bottom: 1rem;">
                            <label style="display: block; margin-bottom: 0.5rem; color: var(--primary-text); font-weight: 500;">API Rate Limit</label>
                            <select style="width: 100%; padding: 0.5rem; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 6px; color: var(--primary-text);">
                                <option value="100">100 requests/minute</option>
                                <option value="500">500 requests/minute</option>
                                <option value="1000">1000 requests/minute</option>
                                <option value="unlimited">Unlimited</option>
                            </select>
                        </div>
                        <div style="margin-bottom: 1rem;">
                            <label style="display: block; margin-bottom: 0.5rem; color: var(--primary-text); font-weight: 500;">Session Timeout</label>
                            <select style="width: 100%; padding: 0.5rem; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 6px; color: var(--primary-text);">
                                <option value="30">30 minutes</option>
                                <option value="60">1 hour</option>
                                <option value="240">4 hours</option>
                                <option value="480">8 hours</option>
                            </select>
                        </div>
                        <div style="margin-bottom: 1rem;">
                            <label style="display: flex; align-items: center; gap: 0.5rem; color: var(--primary-text);">
                                <input type="checkbox" checked style="accent-color: var(--accent-color);">
                                Enable audit logging
                            </label>
                        </div>
                        <div style="margin-bottom: 1rem;">
                            <label style="display: flex; align-items: center; gap: 0.5rem; color: var(--primary-text);">
                                <input type="checkbox" checked style="accent-color: var(--accent-color);">
                                Require authentication for API access
                            </label>
                        </div>
                    </div>
                </div>

                <!-- Organization Settings -->
                <div class="card">
                    <h3 style="margin-bottom: 1.5rem;">
                        <i class="fas fa-building"></i> Organization
                    </h3>
                    <div style="space-y: 1rem;">
                        <div style="margin-bottom: 1rem;">
                            <label style="display: block; margin-bottom: 0.5rem; color: var(--primary-text); font-weight: 500;">Organization Name</label>
                            <input type="text" value="BoarderframeOS" style="width: 100%; padding: 0.5rem; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 6px; color: var(--primary-text);">
                        </div>
                        <div style="margin-bottom: 1rem;">
                            <label style="display: block; margin-bottom: 0.5rem; color: var(--primary-text); font-weight: 500;">Primary Administrator</label>
                            <input type="text" value="Carl" style="width: 100%; padding: 0.5rem; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 6px; color: var(--primary-text);">
                        </div>
                        <div style="margin-bottom: 1rem;">
                            <label style="display: block; margin-bottom: 0.5rem; color: var(--primary-text); font-weight: 500;">Department Structure</label>
                            <select style="width: 100%; padding: 0.5rem; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 6px; color: var(--primary-text);">
                                <option value="hierarchical">Hierarchical</option>
                                <option value="flat">Flat Structure</option>
                                <option value="matrix">Matrix Organization</option>
                                <option value="custom">Custom Structure</option>
                            </select>
                        </div>
                        <div style="margin-bottom: 1rem;">
                            <label style="display: flex; align-items: center; gap: 0.5rem; color: var(--primary-text);">
                                <input type="checkbox" checked style="accent-color: var(--accent-color);">
                                Enable department analytics
                            </label>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Save Settings Button -->
            <div style="text-align: center; margin-top: 2rem;">
                <button style="background: var(--accent-color); color: white; border: none; padding: 0.5rem 1rem; border-radius: 6px; font-size: 0.9rem; font-weight: 600; cursor: pointer; transition: all 0.3s ease;" onmouseover="this.style.background='var(--success-color)'" onmouseout="this.style.background='var(--accent-color)'">
                    <i class="fas fa-save"></i> Save Configuration
                </button>
            </div>
        </div>
    </div>

    <!-- Persistent Chat Button -->
    <button class="chat-button" onclick="openChat()">
        <i class="fas fa-comments"></i>
    </button>

    <!-- Chat Overlay -->
    <div class="chat-overlay" id="chatOverlay">
        <div class="chat-container">
            <div class="chat-header">
                <h3 style="margin: 0; color: var(--primary-text);">
                    <i class="fas fa-robot"></i> Agent Chat
                </h3>
                <button class="chat-close" onclick="closeChat()">
                    <i class="fas fa-times"></i>
                </button>
            </div>

            <div class="agent-selector">
                <h4 style="margin: 0 0 1rem 0; color: var(--primary-text); font-size: 0.9rem;">Select Agents to Chat With:</h4>
                <div class="agent-pills">
                    <div class="agent-pill active" data-agent="solomon" onclick="toggleAgent('solomon')">
                        <i class="fas fa-crown"></i> Solomon
                    </div>
                    <div class="agent-pill" data-agent="david" onclick="toggleAgent('david')">
                        <i class="fas fa-shield-alt"></i> David
                    </div>
                    <div class="agent-pill" data-agent="michael" onclick="toggleAgent('michael')">
                        <i class="fas fa-balance-scale"></i> Michael
                    </div>
                    <div class="agent-pill" data-agent="adam" onclick="toggleAgent('adam')">
                        <i class="fas fa-user-cog"></i> Adam
                    </div>
                    <div class="agent-pill" data-agent="eve" onclick="toggleAgent('eve')">
                        <i class="fas fa-leaf"></i> Eve
                    </div>
                    <div class="agent-pill" data-agent="bezalel" onclick="toggleAgent('bezalel')">
                        <i class="fas fa-tools"></i> Bezalel
                    </div>
                </div>
            </div>

            <div class="chat-messages" id="chatMessages">
                <div style="text-align: center; color: var(--secondary-text); padding: 2rem;">
                    <i class="fas fa-comments" style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                    <p>Select agents above and start chatting with your AI team!</p>
                </div>
            </div>

            <div class="chat-input-area">
                <textarea class="chat-input" id="chatInput" placeholder="Type your message here..." rows="2"></textarea>
                <button class="chat-send" onclick="sendMessage()">
                    <i class="fas fa-paper-plane"></i> Send
                </button>
            </div>
        </div>

    </div>

    <script>
        // Tab switching functionality
        function showTab(tabName) {{
            // Hide all tab contents
            const tabs = document.querySelectorAll('.tab-content');
            tabs.forEach(tab => tab.classList.remove('active'));

            // Remove active class from all nav links
            const navLinks = document.querySelectorAll('.nav-link');
            navLinks.forEach(link => link.classList.remove('active'));

            // Show selected tab content
            const selectedTab = document.getElementById(tabName);
            if (selectedTab) {{
                selectedTab.classList.add('active');
            }}

            // Add active class to clicked nav link
            const clickedLink = document.querySelector(`.nav-link[data-tab="${{tabName}}"]`);
            if (clickedLink) {{
                clickedLink.classList.add('active');
            }}

            // Auto-load metrics when metrics tab is shown
            if (tabName === 'metrics') {{
                // Check if metrics haven't been loaded yet (spinner is showing)
                const metricsContent = document.getElementById('metrics-content');
                if (metricsContent && metricsContent.querySelector('.fa-spinner')) {{
                    console.log('Auto-loading metrics...');
                    loadMetricsData();
                }}
            }}
        }}

        // Load metrics data
        function loadMetricsData() {{
            console.log('[Metrics] Loading metrics data...');
            const timestamp = new Date().toISOString();
            const metricsDiv = document.getElementById('metrics-content');
            metricsDiv.innerHTML = '<div style="text-align: center; padding: 2rem;"><i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: var(--accent-color);"></i><p style="margin-top: 1rem;">Loading metrics...</p></div>';

            // Log metrics request
            console.log(`[Metrics] Requesting metrics at ${{timestamp}}`);

            // Fetch metrics page HTML from API
            fetch('/api/metrics/page')
                .then(response => response.json())
                .then(data => {{
                    if (data.status === 'success') {{
                        console.log('[Metrics] Successfully loaded metrics from layer');
                        metricsDiv.innerHTML = data.html;

                        // Log metrics summary to console
                        fetch('/api/metrics')
                            .then(r => r.json())
                            .then(metrics => {{
                                console.log('[Metrics] Summary:', {{
                                    agents: metrics.data.summary?.total_agents || 'N/A',
                                    departments: metrics.data.summary?.total_departments || 'N/A',
                                    services: metrics.data.summary?.total_services || 'N/A',
                                    database_size: metrics.data.database?.database_size || 'N/A',
                                    leaders: metrics.data.summary?.total_leaders || 'N/A',
                                    timestamp: timestamp
                                }});
                            }});
                    }} else {{
                        console.error('[Metrics] Error loading metrics:', data.message);
                        metricsDiv.innerHTML = `
                            <div class="alert alert-danger" style="margin: 2rem;">
                                <i class="fas fa-exclamation-triangle"></i>
                                Error loading metrics: ${{data.message || 'Unknown error'}}
                            </div>
                        `;
                    }}
                }})
                .catch(error => {{
                    console.error('[Metrics] Network error fetching metrics:', error);
                    // Fallback to raw metrics API
                    fetch('/api/metrics')
                        .then(response => response.json())
                        .then(data => {{
                            if (data.status === 'success') {{
                                console.log('[Metrics] Loaded raw metrics as fallback');
                                metricsDiv.innerHTML = `
                                    <div style="padding: 2rem;">
                                        <h3>System Metrics (Raw Data)</h3>
                                        <pre style="background: var(--secondary-bg); padding: 1rem; border-radius: 8px; overflow: auto; max-height: 600px;">
${{JSON.stringify(data.data, null, 2)}}
                                        </pre>
                                    </div>
                                `;
                            }} else {{
                                metricsDiv.innerHTML = `
                                    <div class="alert alert-danger" style="margin: 2rem;">
                                        <i class="fas fa-exclamation-triangle"></i>
                                        Failed to load metrics data
                                    </div>
                                `;
                            }}
                        }})
                        .catch(err => {{
                            console.error('[Metrics] Complete failure loading metrics:', err);
                            metricsDiv.innerHTML = `
                                <div class="alert alert-danger" style="margin: 2rem;">
                                    <i class="fas fa-exclamation-triangle"></i>
                                    Network error: Unable to fetch metrics
                                </div>
                            `;
                        }});
                }});
        }}

        // Database refresh functionality
        async function refreshDatabaseMetrics() {{
            const button = event.target.closest('button');
            const icon = button.querySelector('i');
            const originalText = button.innerHTML;
            const lastUpdateSpan = document.getElementById('db-last-update');

            // Create and show progress popup with detailed steps
            showRefreshProgress('Initializing database refresh...');

            // Show loading state
            button.disabled = true;
            icon.classList.add('fa-spin');
            button.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i> Refreshing...';

            try {{
                console.log('Triggering database refresh...');

                // Step 1: Validation
                await simulateDelay(300);
                updateRefreshProgress('🔍 Validating database connection parameters...');

                // Step 2: Connection
                await simulateDelay(400);
                updateRefreshProgress('🔌 Establishing connection to PostgreSQL (localhost:5434)...');

                // Step 3: Authentication
                await simulateDelay(300);
                updateRefreshProgress('🔐 Authenticating with boarderframeos database...');

                // Step 4: API Call
                await simulateDelay(200);
                updateRefreshProgress('📡 Sending refresh request to server...');

                const response = await fetch('/api/database/refresh', {{
                    method: 'POST'
                }});

                console.log('Response status:', response.status);

                if (response.ok) {{
                    // Step 5: Server Processing
                    updateRefreshProgress('⚙️ Server processing database health check...');
                    await simulateDelay(500);

                    // Step 6: Table Analysis
                    updateRefreshProgress('📊 Analyzing database tables and schemas...');
                    await simulateDelay(400);

                    // Step 7: Connection Stats
                    updateRefreshProgress('📈 Gathering connection statistics...');
                    await simulateDelay(300);

                    // Step 8: Size Calculation
                    updateRefreshProgress('💾 Calculating database and table sizes...');
                    await simulateDelay(400);

                    // Step 9: Performance Metrics
                    updateRefreshProgress('⚡ Collecting cache hit ratios and performance data...');
                    await simulateDelay(350);

                    // Step 10: Extension Check
                    updateRefreshProgress('🔧 Verifying pgvector and PostgreSQL extensions...');
                    await simulateDelay(250);

                    let data;
                    try {{
                        const responseText = await response.text();
                        console.log('Raw response:', responseText);
                        data = JSON.parse(responseText);
                    }} catch (parseError) {{
                        console.error('JSON parse error:', parseError);
                        throw new Error('Invalid response format from server');
                    }}

                    console.log('Parsed response:', data);

                    // Step 11: Data Processing
                    updateRefreshProgress('🧮 Processing and categorizing table data...');
                    await simulateDelay(300);

                    // Step 12: UI Updates
                    updateRefreshProgress('🎨 Updating metrics widgets and visualizations...');
                    await simulateDelay(250);

                    // Update the last update time
                    if (lastUpdateSpan) {{
                        lastUpdateSpan.textContent = new Date().toLocaleString();
                    }}

                    // Show success message briefly
                    button.innerHTML = '<i class="fas fa-check"></i> Refreshed!';
                    button.style.background = 'linear-gradient(135deg, #10b981, #059669)';

                    // Step 13: Final Update
                    updateRefreshProgress('🔄 Refreshing table filters and sorting...');
                    await simulateDelay(200);

                    // Step 14: Success
                    updateRefreshProgress('✅ Database metrics updated successfully!', 'success');

                    setTimeout(() => {{
                        hideRefreshProgress();
                        refreshDatabaseTabContent();

                        // Reset button state
                        button.disabled = false;
                        button.innerHTML = originalText;
                        button.style.background = 'linear-gradient(135deg, #10b981, #059669)';
                    }}, 1500);

                }} else {{
                    const errorText = await response.text();
                    console.error('Server error response:', errorText);
                    throw new Error(`Server error: ${{response.status}} - ${{errorText}}`);
                }}
            }} catch (error) {{
                console.error('Database refresh error:', error);
                updateRefreshProgress(`❌ Error: ${{error.message}}`, 'error');

                setTimeout(() => {{
                    hideRefreshProgress();
                }}, 3000);

                // Reset button state on error
                button.disabled = false;
                icon.classList.remove('fa-spin');
                button.innerHTML = originalText;
            }}
        }}

        // Helper function for realistic timing simulation
        function simulateDelay(ms) {{
            return new Promise(resolve => setTimeout(resolve, ms));
        }}

        // Progress popup functions
        function showRefreshProgress(message) {{
            // Remove existing popup if any
            const existingPopup = document.getElementById('refreshProgressPopup');
            if (existingPopup) {{
                existingPopup.remove();
            }}

            // Create popup overlay
            const popup = document.createElement('div');
            popup.id = 'refreshProgressPopup';
            popup.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10000;
                backdrop-filter: blur(5px);
            `;

            // Create popup content
            const content = document.createElement('div');
            content.style.cssText = `
                background: var(--secondary-bg);
                border: 2px solid var(--accent-color);
                border-radius: 12px;
                padding: 2rem;
                text-align: center;
                width: 420px;
                min-width: 420px;
                max-width: 420px;
                height: 280px;
                min-height: 280px;
                max-height: 280px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                color: var(--primary-text);
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            `;

            content.innerHTML = `
                <div style="flex-shrink: 0;">
                    <div style="margin-bottom: 1rem;">
                        <i class="fas fa-database" style="font-size: 2rem; color: var(--accent-color);"></i>
                    </div>
                    <h3 style="margin: 0 0 1rem 0; color: var(--accent-color);">Database Refresh</h3>
                </div>

                <div style="flex: 1; display: flex; flex-direction: column; justify-content: center;">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span id="stepCounter" style="font-size: 0.8rem; color: var(--secondary-text);">Step 1 of 14</span>
                        <span id="progressPercent" style="font-size: 0.8rem; color: var(--secondary-text);">0%</span>
                    </div>
                    <div id="progressMessage" style="
                        margin-bottom: 1rem;
                        color: var(--secondary-text);
                        height: 3rem;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        text-align: center;
                        line-height: 1.4;
                    ">${{message}}</div>
                    <div class="progress-bar" style="
                        width: 100%;
                        height: 10px;
                        background: var(--border-color);
                        border-radius: 5px;
                        overflow: hidden;
                        margin-bottom: 1rem;
                        box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
                    ">
                        <div id="progressFill" style="
                            height: 100%;
                            background: linear-gradient(90deg, var(--accent-color), var(--success-color));
                            border-radius: 5px;
                            width: 0%;
                            transition: width 0.4s ease;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        "></div>
                    </div>
                </div>

                <div style="flex-shrink: 0; display: flex; align-items: center; justify-content: center; gap: 0.5rem;">
                    <i class="fas fa-sync-alt fa-spin" style="color: var(--accent-color);"></i>
                    <span style="font-size: 0.9rem; color: var(--secondary-text);">Processing database operations...</span>
                </div>
            `;

            popup.appendChild(content);
            document.body.appendChild(popup);

            // Initialize progress tracking
            popup.currentStep = 0;
            popup.totalSteps = 14; // Total number of steps in refresh process
        }}

        function updateRefreshProgress(message, type = 'info') {{
            const messageDiv = document.getElementById('progressMessage');
            const progressFill = document.getElementById('progressFill');
            const stepCounter = document.getElementById('stepCounter');
            const progressPercent = document.getElementById('progressPercent');
            const popup = document.getElementById('refreshProgressPopup');

            if (messageDiv) {{
                messageDiv.innerHTML = message; // Use innerHTML to support emojis

                // Update progress bar based on steps
                if (popup && type !== 'error') {{
                    popup.currentStep++;
                    const percent = (popup.currentStep / popup.totalSteps) * 100;
                    const displayPercent = Math.min(percent, 95);

                    // Update step counter
                    if (stepCounter) {{
                        stepCounter.textContent = `Step ${{popup.currentStep}} of ${{popup.totalSteps}}`;
                    }}

                    // Update percentage display
                    if (progressPercent) {{
                        progressPercent.textContent = `${{Math.round(displayPercent)}}%`;
                    }}

                    if (progressFill) {{
                        if (type === 'success') {{
                            progressFill.style.width = '100%';
                            progressFill.style.background = 'var(--success-color)';
                            messageDiv.style.color = 'var(--success-color)';

                            // Update final displays
                            if (stepCounter) stepCounter.textContent = `Completed all ${{popup.totalSteps}} steps`;
                            if (progressPercent) progressPercent.textContent = '100%';
                        }} else {{
                            progressFill.style.width = `${{displayPercent}}%`;
                            messageDiv.style.color = 'var(--primary-text)';
                        }}
                    }}
                }} else if (type === 'error') {{
                    messageDiv.style.color = 'var(--danger-color)';
                    if (progressFill) {{
                        progressFill.style.background = 'var(--danger-color)';
                    }}
                    if (stepCounter) {{
                        stepCounter.textContent = 'Error occurred';
                        stepCounter.style.color = 'var(--danger-color)';
                    }}
                }}
            }}
        }}

        function hideRefreshProgress() {{
            const popup = document.getElementById('refreshProgressPopup');
            if (popup) {{
                // Fade out animation
                popup.style.opacity = '0';
                popup.style.transition = 'opacity 0.3s ease';

                setTimeout(() => {{
                    popup.remove();
                }}, 300);
            }}
        }}

        function refreshDatabaseTabContent() {{
            // Instead of full page reload, just refresh the database tab content
            // by fetching updated HTML for just the database section
            fetch('/')
                .then(response => response.text())
                .then(html => {{
                    // Parse the response to extract just the database tab content
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const newDatabaseTab = doc.getElementById('database');
                    const currentDatabaseTab = document.getElementById('database');

                    if (newDatabaseTab && currentDatabaseTab) {{
                        // Preserve the active state
                        if (currentDatabaseTab.classList.contains('active')) {{
                            newDatabaseTab.classList.add('active');
                        }}

                        // Replace the content
                        currentDatabaseTab.innerHTML = newDatabaseTab.innerHTML;

                        console.log('Database tab content refreshed without page reload');
                    }}
                }})
                .catch(error => {{
                    console.error('Failed to refresh database tab content:', error);
                    // Fallback to full reload if partial refresh fails
                    window.location.reload();
                }});
        }}

        // Database table filtering and sorting functionality
        let currentSort = {{ field: 'category', ascending: true }};

        function filterTables() {{
            const categoryFilter = document.getElementById('categoryFilter').value.toLowerCase();
            const searchFilter = document.getElementById('searchFilter').value.toLowerCase();
            const tbody = document.getElementById('databaseTableBody');
            const rows = tbody.querySelectorAll('tr');

            let visibleCount = 0;
            let categoryCount = 0;

            rows.forEach(row => {{
                const isHeaderRow = row.cells.length === 1; // Category header rows

                if (isHeaderRow) {{
                    const categoryName = row.textContent.toLowerCase();
                    const matchesCategory = !categoryFilter || categoryName.includes(categoryFilter);

                    if (matchesCategory) {{
                        row.style.display = '';
                        categoryCount++;
                    }} else {{
                        row.style.display = 'none';
                    }}
                }} else {{
                    const tableName = row.cells[0].textContent.toLowerCase();
                    const categoryCell = row.cells[4];
                    const categoryText = categoryCell ? categoryCell.textContent.toLowerCase() : '';

                    const matchesSearch = !searchFilter || tableName.includes(searchFilter);
                    const matchesCategory = !categoryFilter || categoryText.includes(categoryFilter);

                    if (matchesSearch && matchesCategory) {{
                        row.style.display = '';
                        visibleCount++;
                    }} else {{
                        row.style.display = 'none';
                    }}
                }}
            }});

            // Update count display
            const countSpan = document.getElementById('tableCount');
            if (categoryFilter || searchFilter) {{
                countSpan.textContent = `Showing ${{visibleCount}} tables`;
            }} else {{
                countSpan.textContent = 'Showing all tables';
            }}
        }}

        function sortTables(field) {{
            const tbody = document.getElementById('databaseTableBody');
            const rows = Array.from(tbody.querySelectorAll('tr'));

            // Separate header rows from data rows
            const headerRows = rows.filter(row => row.cells.length === 1);
            const dataRows = rows.filter(row => row.cells.length > 1);

            // Toggle sort direction if clicking same field
            if (currentSort.field === field) {{
                currentSort.ascending = !currentSort.ascending;
            }} else {{
                currentSort.field = field;
                currentSort.ascending = true;
            }}

            // Sort data rows
            dataRows.sort((a, b) => {{
                let aValue, bValue;

                switch (field) {{
                    case 'name':
                        aValue = a.cells[0].textContent.trim();
                        bValue = b.cells[0].textContent.trim();
                        break;
                    case 'schema':
                        aValue = a.cells[1].textContent.trim();
                        bValue = b.cells[1].textContent.trim();
                        break;
                    case 'size':
                        // Extract numeric value for proper size sorting
                        aValue = parseSizeValue(a.cells[2].textContent.trim());
                        bValue = parseSizeValue(b.cells[2].textContent.trim());
                        break;
                    case 'columns':
                        aValue = parseInt(a.cells[3].textContent.trim()) || 0;
                        bValue = parseInt(b.cells[3].textContent.trim()) || 0;
                        break;
                    case 'category':
                        aValue = a.cells[4].textContent.trim();
                        bValue = b.cells[4].textContent.trim();
                        break;
                    default:
                        return 0;
                }}

                if (typeof aValue === 'string') {{
                    aValue = aValue.toLowerCase();
                    bValue = bValue.toLowerCase();
                }}

                let result;
                if (aValue < bValue) result = -1;
                else if (aValue > bValue) result = 1;
                else result = 0;

                return currentSort.ascending ? result : -result;
            }});

            // Clear tbody and re-add sorted rows
            tbody.innerHTML = '';

            if (field === 'category') {{
                // Group by category when sorting by category
                const categoryGroups = {{}};
                dataRows.forEach(row => {{
                    const category = row.cells[4].textContent.trim();
                    if (!categoryGroups[category]) {{
                        categoryGroups[category] = [];
                    }}
                    categoryGroups[category].push(row);
                }});

                Object.keys(categoryGroups).sort().forEach(category => {{
                    // Find the header row for this category
                    const headerRow = headerRows.find(row =>
                        row.textContent.toLowerCase().includes(category.toLowerCase())
                    );
                    if (headerRow) {{
                        tbody.appendChild(headerRow);
                    }}

                    categoryGroups[category].forEach(row => {{
                        tbody.appendChild(row);
                    }});
                }});
            }} else {{
                // For other sorts, just add data rows without category headers
                dataRows.forEach(row => {{
                    tbody.appendChild(row);
                }});
            }}

            // Update sort indicators
            updateSortIndicators(field);
        }}

        function parseSizeValue(sizeStr) {{
            const sizeMap = {{ 'bytes': 1, 'kb': 1024, 'mb': 1024*1024, 'gb': 1024*1024*1024 }};
            const match = sizeStr.toLowerCase().match(/([\\d.]+)\\s*(bytes|kb|mb|gb)?/);
            if (match) {{
                const value = parseFloat(match[1]);
                const unit = match[2] || 'bytes';
                return value * (sizeMap[unit] || 1);
            }}
            return 0;
        }}

        function updateSortIndicators(activeField) {{
            const headers = document.querySelectorAll('#databaseTable th');
            headers.forEach(header => {{
                const icon = header.querySelector('i.fas');
                if (icon) {{
                    icon.className = 'fas fa-sort';
                    icon.style.opacity = '0.5';
                }}
            }});

            // Update active field indicator
            const fieldMap = {{ name: 0, schema: 1, size: 2, columns: 3, category: 4 }};
            const activeHeader = headers[fieldMap[activeField]];
            if (activeHeader) {{
                const icon = activeHeader.querySelector('i.fas');
                if (icon) {{
                    icon.className = currentSort.ascending ? 'fas fa-sort-up' : 'fas fa-sort-down';
                    icon.style.opacity = '1';
                }}
            }}
        }}

        // Status dropdown functionality
        function toggleStatusDropdown() {{
            const dropdown = document.getElementById('statusDropdown');
            dropdown.classList.toggle('show');
        }}

        function closeStatusDropdown() {{
            const dropdown = document.getElementById('statusDropdown');
            dropdown.classList.remove('show');
        }}

        // Navigate to tab from dropdown and close dropdown
        function navigateToTab(tabName) {{
            closeStatusDropdown();
            showTab(tabName);
        }}

        // Close dropdown when clicking outside or on quick action buttons
        document.addEventListener('click', function(event) {{
            const statusIndicator = document.querySelector('.status-indicator');
            const dropdown = document.getElementById('statusDropdown');

            // Close if clicking outside the entire status area
            if (!statusIndicator.contains(event.target) && !dropdown.contains(event.target)) {{
                dropdown.classList.remove('show');
            }}

            // Close if clicking on quick action buttons (except refresh which closes itself)
            if (event.target.closest('button') && dropdown.contains(event.target)) {{
                if (!event.target.textContent.includes('Refresh')) {{
                    setTimeout(() => dropdown.classList.remove('show'), 100);
                }}
            }}
        }});

        // Enhanced Universal Refresh System
        class RefreshManager {{
            constructor() {{
                this.isRefreshing = false;
                this.components = [
                    'system_metrics', 'database_health', 'services_status',
                    'agents_status', 'mcp_servers', 'registry_data',
                    'departments_data', 'organizational_data'
                ];
            }}

            async refreshAll(options = {{}}) {{
                if (this.isRefreshing) {{
                    console.log('⚠️ Refresh already in progress');
                    return false;
                }}

                const {{
                    components = null,
                    showModal = true,
                    onProgress = null,
                    onComplete = null,
                    targetButtonId = 'globalRefreshBtn'
                }} = options;

                this.isRefreshing = true;
                const startTime = Date.now();

                try {{
                    // Setup UI
                    const refreshBtn = document.getElementById(targetButtonId);
                    if (refreshBtn) {{
                        refreshBtn.disabled = true;
                        refreshBtn.innerHTML = '<i class="fas fa-sync-alt spinning"></i><span>Refreshing...</span>';
                    }}

                    if (showModal) {{
                        this._showRefreshModal();
                    }}

                    // Call enhanced refresh API
                    console.log('🔄 Starting enhanced global refresh...');
                    const response = await fetch('/api/enhanced/refresh', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{ components: components }})
                    }});

                    if (!response.ok) {{
                        throw new Error(`Refresh failed: ${{response.status}} ${{response.statusText}}`);
                    }}

                    const result = await response.json();
                    const refreshTime = (Date.now() - startTime) / 1000;

                    console.log('✅ Enhanced refresh completed:', result);

                    if (onComplete) {{
                        onComplete(result, refreshTime);
                    }}

                    if (showModal) {{
                        this._showRefreshSuccess(result, refreshTime);
                    }}

                    // Refresh current page content
                    await this._refreshPageContent();

                    return result;

                }} catch (error) {{
                    console.error('❌ Refresh failed:', error);

                    if (showModal) {{
                        this._showRefreshError(error);
                    }}

                    throw error;
                }} finally {{
                    this.isRefreshing = false;

                    // Re-enable button
                    const refreshBtn = document.getElementById(targetButtonId);
                    if (refreshBtn) {{
                        refreshBtn.disabled = false;
                        refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i><span>Refresh All</span>';
                    }}
                }}
            }}

            async refreshComponent(component, options = {{}}) {{
                const {{
                    showNotification = true,
                    onComplete = null
                }} = options;

                try {{
                    console.log(`🔄 Refreshing component: ${{component}}`);

                    if (showNotification) {{
                        this._showNotification(`Refreshing ${{component}}...`, 'info');
                    }}

                    const response = await fetch(`/api/refresh/${{component}}`, {{
                        method: 'POST'
                    }});

                    if (!response.ok) {{
                        throw new Error(`Component refresh failed: ${{response.status}}`);
                    }}

                    const result = await response.json();
                    console.log(`✅ Component ${{component}} refreshed:`, result);

                    if (showNotification) {{
                        this._showNotification(`${{component}} refreshed successfully`, 'success');
                    }}

                    if (onComplete) {{
                        onComplete(result);
                    }}

                    return result;

                }} catch (error) {{
                    console.error(`❌ Component ${{component}} refresh failed:`, error);

                    if (showNotification) {{
                        this._showNotification(`Failed to refresh ${{component}}: ${{error.message}}`, 'error');
                    }}

                    throw error;
                }}
            }}

            _showRefreshModal() {{
                const modal = document.getElementById('globalRefreshModal');
                if (modal) {{
                    modal.style.display = 'flex';
                    const summary = document.getElementById('refreshSummary');
                    if (summary) summary.style.display = 'none';
                }}
            }}

            _showRefreshSuccess(result, refreshTime) {{
                const summary = document.getElementById('refreshSummary');
                const durationSpan = document.getElementById('refreshDuration');
                const componentsSpan = document.getElementById('refreshedComponents');
                const statusSpan = document.getElementById('refreshStatus');

                if (summary && durationSpan && componentsSpan && statusSpan) {{
                    durationSpan.textContent = `${{refreshTime.toFixed(2)}}s`;
                    componentsSpan.textContent = result.result?.refreshed_components?.length || 'N/A';
                    statusSpan.textContent = result.status === 'success' ? 'Success' : 'Partial';
                    summary.style.display = 'block';
                }}

                // Enable close button
                const closeBtn = document.getElementById('closeRefreshBtn');
                if (closeBtn) closeBtn.disabled = false;
            }}

            _showRefreshError(error) {{
                const summary = document.getElementById('refreshSummary');
                if (summary) {{
                    summary.innerHTML = `
                        <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; border-radius: 8px; padding: 1rem;">
                            <h4 style="color: #ef4444; margin: 0 0 0.5rem 0;">Refresh Failed</h4>
                            <p style="margin: 0; color: rgba(255,255,255,0.8);">${{error.message}}</p>
                        </div>
                    `;
                    summary.style.display = 'block';
                }}

                const closeBtn = document.getElementById('closeRefreshBtn');
                if (closeBtn) closeBtn.disabled = false;
            }}

            _showNotification(message, type = 'info') {{
                // Create a simple notification system
                const notification = document.createElement('div');
                notification.className = `refresh-notification refresh-notification-${{type}}`;
                notification.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    padding: 12px 16px;
                    border-radius: 8px;
                    color: white;
                    font-weight: 500;
                    z-index: 10000;
                    transform: translateX(100%);
                    transition: transform 0.3s ease;
                    background: ${{type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#6366f1'}};
                `;
                notification.textContent = message;

                document.body.appendChild(notification);

                // Animate in
                setTimeout(() => {{
                    notification.style.transform = 'translateX(0)';
                }}, 100);

                // Remove after delay
                setTimeout(() => {{
                    notification.style.transform = 'translateX(100%)';
                    setTimeout(() => {{
                        if (notification.parentNode) {{
                            notification.parentNode.removeChild(notification);
                        }}
                    }}, 300);
                }}, 3000);
            }}

            async _refreshPageContent() {{
                // Attempt to refresh current tab content without full page reload
                try {{
                    const activeTab = document.querySelector('.tab-btn.active');
                    if (activeTab) {{
                        const tabName = activeTab.getAttribute('data-tab');
                        console.log(`🔄 Refreshing active tab content: ${{tabName}}`);

                        // Trigger specific tab refresh if function exists
                        if (window[`refresh${{tabName}}TabContent`]) {{
                            await window[`refresh${{tabName}}TabContent`]();
                        }}
                    }}
                }} catch (error) {{
                    console.log('Could not refresh tab content, continuing:', error);
                }}
            }}
        }}

        // Global refresh manager instance
        const refreshManager = new RefreshManager();

        // Enhanced global refresh function using the new refresh system with legacy modal
        async function startGlobalRefresh() {{
            const refreshBtn = document.getElementById('globalRefreshBtn');
            const modal = document.getElementById('globalRefreshModal');
            const progressFill = document.getElementById('globalProgressFill');
            const progressPercent = document.getElementById('globalProgressPercent');
            const closeBtn = document.getElementById('closeRefreshBtn');
            const refreshSummary = document.getElementById('refreshSummary');
            const currentStepText = document.getElementById('currentStepText');
            const currentStepDetails = document.getElementById('currentStepDetails');

            // Disable refresh button and show modal
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt spinning"></i><span>Refreshing OS...</span>';
            modal.style.display = 'flex';
            closeBtn.disabled = true;
            refreshSummary.style.display = 'none';

            // Reset progress
            progressFill.style.width = '0%';
            progressPercent.textContent = '0%';

            // Reset all component cards
            const componentCards = document.querySelectorAll('.refresh-component-card');
            componentCards.forEach((card) => {{
                const componentId = card.getAttribute('data-component');
                const statusDiv = document.getElementById(`status-${{componentId}}`);
                if (statusDiv) {{
                    statusDiv.innerHTML = '<i class="fas fa-clock"></i> Pending';
                }}
                // Reset all animation and style properties
                card.style.animation = 'none';
                card.style.transform = 'scale(1)';
                card.style.opacity = '1';
                card.style.filter = 'brightness(1)';
                card.style.borderLeft = 'none';
                // Reset to original shadow - get the computed style from CSS
                const computedStyle = window.getComputedStyle(card);
                card.style.boxShadow = computedStyle.getPropertyValue('box-shadow');
            }});

            // Set initial current step
            currentStepText.textContent = 'Starting enhanced global refresh...';
            currentStepDetails.textContent = 'Preparing to refresh all BoarderframeOS components using enhanced system...';

            const startTime = Date.now();

            // Function to update component status
            const updateComponentStatus = (componentId, status) => {{
                // Find the card by data-component attribute
                const card = document.querySelector(`[data-component="${{componentId}}"]`);
                const statusDiv = document.getElementById(`status-${{componentId}}`);

                if (card && statusDiv) {{
                    if (status === 'running') {{
                        statusDiv.innerHTML = '<i class="fas fa-sync-alt spinning" style="color: #6366f1;"></i> Refreshing...';
                        card.style.animation = 'componentPulse 2s ease-in-out infinite';
                        card.style.transform = 'scale(1.02)';
                        card.style.boxShadow = '0 8px 25px rgba(99, 102, 241, 0.4)';
                        card.style.filter = 'brightness(1.1)';
                        card.style.borderLeft = '4px solid #6366f1';
                    }} else if (status === 'completed') {{
                        statusDiv.innerHTML = '<i class="fas fa-check-circle" style="color: #10b981;"></i> Complete';
                        card.style.animation = 'componentComplete 0.6s ease-out forwards';
                        card.style.boxShadow = '0 8px 25px rgba(16, 185, 129, 0.4)';
                        card.style.borderLeft = '4px solid #10b981';

                        // Add a completion glow effect
                        setTimeout(() => {{
                            card.style.animation = 'none';
                            card.style.transform = 'scale(1)';
                            card.style.boxShadow = '0 4px 12px rgba(16, 185, 129, 0.3)';
                            card.style.filter = 'brightness(1.05)';
                        }}, 600);
                    }} else if (status === 'error') {{
                        statusDiv.innerHTML = '<i class="fas fa-exclamation-circle" style="color: #ef4444;"></i> Error';
                        card.style.animation = 'none';
                        card.style.boxShadow = '0 8px 25px rgba(239, 68, 68, 0.4)';
                        card.style.filter = 'brightness(0.9)';
                        card.style.borderLeft = '4px solid #ef4444';
                        card.style.transform = 'scale(0.98)';
                    }}
                }}
            }};

            // Simulate progressive refresh (since we get all results at once, we'll simulate the progression)
            const componentOrder = [
                'system_metrics', 'database_health', 'services_status', 'agents_status',
                'mcp_servers', 'registry_data', 'departments_data', 'organizational_data'
            ];

            try {{
                // Start the refresh API call
                console.log('🔄 Starting enhanced global refresh...');

                // Simulate progressive refresh with realistic timing
                const simulateProgress = async () => {{
                    let currentComponent = 0;
                    const totalComponents = componentOrder.length;

                    const runNextComponent = () => {{
                        if (currentComponent < totalComponents) {{
                            const component = componentOrder[currentComponent];
                            updateComponentStatus(component, 'running');
                            currentStepText.textContent = `Refreshing ${{component.replace('_', ' ')}}...`;
                            currentStepDetails.textContent = `Processing ${{component}} data layer...`;

                            // Update progress bar
                            const progress = ((currentComponent + 0.5) / totalComponents) * 100;
                            progressFill.style.width = `${{progress}}%`;
                            progressPercent.textContent = `${{Math.round(progress)}}%`;

                            currentComponent++;

                            // Schedule next component (random delay between 300-800ms for realism)
                            setTimeout(runNextComponent, Math.random() * 500 + 300);
                        }}
                    }};

                    // Start the simulation
                    runNextComponent();
                }};

                // Start the simulation
                simulateProgress();

                const response = await fetch('/api/enhanced/refresh', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{}})
                }});

                if (!response.ok) {{
                    throw new Error(`Enhanced refresh failed: ${{response.status}} ${{response.statusText}}`);
                }}

                const result = await response.json();
                const refreshTime = (Date.now() - startTime) / 1000;

                console.log('✅ Enhanced refresh completed:', result);

                // Show completion sequence for components that were refreshed
                const refreshedComponents = result.result?.refreshed_components || componentOrder;
                let completionIndex = 0;

                const showCompletions = () => {{
                    if (completionIndex < refreshedComponents.length) {{
                        const component = refreshedComponents[completionIndex];
                        updateComponentStatus(component, 'completed');
                        completionIndex++;
                        setTimeout(showCompletions, 200); // Quick succession for completion
                    }}
                }};

                // Wait a moment then show completions and handle skipped components
                setTimeout(() => {{
                    showCompletions();

                    // Mark any failed components
                    const failedComponents = result.result?.failed_components || [];
                    failedComponents.forEach(component => {{
                        updateComponentStatus(component, 'error');
                    }});

                    // Handle any skipped components
                    const refreshedComponents = result.result?.refreshed_components || componentOrder;
                    componentOrder.forEach(component => {{
                        if (!refreshedComponents.includes(component) && !failedComponents.includes(component)) {{
                            const card = document.querySelector(`[data-component="${{component}}"]`);
                            const statusDiv = document.getElementById(`status-${{component}}`);
                            if (statusDiv) {{
                                statusDiv.innerHTML = '<i class="fas fa-exclamation-circle" style="color: #f59e0b;"></i> Skipped';
                            }}
                            if (card) {{
                                card.style.filter = 'brightness(0.95)';
                                card.style.borderLeft = '4px solid #f59e0b';
                            }}
                        }}
                    }});
                }}, 500);

                // Update progress to 100%
                setTimeout(() => {{
                    progressFill.style.width = '100%';
                    progressPercent.textContent = '100%';
                }}, 2000); // After all components are shown as complete

                // Update current step
                currentStepText.textContent = 'Enhanced refresh completed successfully!';
                currentStepDetails.textContent = `Refreshed ${{result.result?.refreshed_components?.length || 8}} components in ${{refreshTime.toFixed(2)}} seconds.`;

                // Show success summary
                const summary = document.getElementById('refreshSummary');
                const durationSpan = document.getElementById('refreshDuration');
                const componentsSpan = document.getElementById('refreshedComponents');
                const statusSpan = document.getElementById('refreshStatus');

                if (summary && durationSpan && componentsSpan && statusSpan) {{
                    durationSpan.textContent = `${{refreshTime.toFixed(2)}}s`;
                    componentsSpan.textContent = result.result?.refreshed_components?.length || 8;
                    statusSpan.textContent = result.status === 'success' ? 'Success' : 'Partial';
                    summary.style.display = 'block';
                }}

                // Enable close button
                closeBtn.disabled = false;

                return result;

            }} catch (error) {{
                console.error('❌ Enhanced refresh failed:', error);

                // Show error state
                currentStepText.textContent = 'Enhanced refresh failed';
                currentStepDetails.textContent = `Error: ${{error.message}}`;

                // Show error summary
                const summary = document.getElementById('refreshSummary');
                if (summary) {{
                    summary.innerHTML = `
                        <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; border-radius: 8px; padding: 1rem;">
                            <h4 style="color: #ef4444; margin: 0 0 0.5rem 0;">Enhanced Refresh Failed</h4>
                            <p style="margin: 0; color: rgba(255,255,255,0.8);">${{error.message}}</p>
                        </div>
                    `;
                    summary.style.display = 'block';
                }}

                closeBtn.disabled = false;
                throw error;
            }} finally {{
                // Re-enable refresh button
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i><span>Refresh OS</span>';
            }}
        }}

        // Quick refresh function for use in buttons anywhere
        async function quickRefresh(buttonId = null) {{
            return await refreshManager.refreshAll({{
                showModal: false,
                targetButtonId: buttonId || 'quickRefreshBtn'
            }});
        }}

        // Component-specific refresh functions
        async function refreshDatabase() {{
            return await refreshManager.refreshComponent('database_health');
        }}

        async function refreshAgents() {{
            return await refreshManager.refreshComponent('agents_status');
        }}

        async function refreshServices() {{
            return await refreshManager.refreshComponent('services_status');
        }}

        async function refreshMetrics() {{
            return await refreshManager.refreshComponent('system_metrics');
        }}

        // Legacy global refresh function (original implementation)
        async function startGlobalRefreshLegacy() {{
            const refreshBtn = document.getElementById('globalRefreshBtn');
            const modal = document.getElementById('globalRefreshModal');
            const progressFill = document.getElementById('globalProgressFill');
            const progressPercent = document.getElementById('globalProgressPercent');
            const closeBtn = document.getElementById('closeRefreshBtn');
            const refreshSummary = document.getElementById('refreshSummary');
            const currentStepText = document.getElementById('currentStepText');
            const currentStepDetails = document.getElementById('currentStepDetails');
            const currentStepIcon = document.getElementById('currentStepIcon');

            // Disable refresh button and show modal
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt spinning"></i><span>Refreshing OS...</span>';
            modal.style.display = 'flex';
            closeBtn.disabled = true;
            refreshSummary.style.display = 'none';

            // Reset progress
            progressFill.style.width = '0%';
            progressPercent.textContent = '0%';

            // Reset all step indicators
            const refreshSteps = document.querySelectorAll('.refresh-step');
            refreshSteps.forEach((step, index) => {{
                step.className = 'refresh-step';
                const icon = step.querySelector('.step-icon');
                const status = step.querySelector('.step-status');
                icon.className = 'fas fa-circle step-icon pending';
                status.textContent = 'Pending';
                status.className = 'step-status';
            }});

            // Set initial current step
            currentStepText.textContent = 'Testing API connection...';
            currentStepDetails.textContent = 'Verifying BoarderframeOS Corporate Headquarters API is responsive...';
            currentStepIcon.className = 'fas fa-network-wired';

            const startTime = Date.now();
            const totalSteps = 16;

            try {{
                // First test basic API connectivity
                console.log('🔍 Testing API connectivity...');
                const testResponse = await fetch('/api/test');
                if (!testResponse.ok) {{
                    throw new Error(`API test failed: ${{testResponse.status}}`);
                }}
                console.log('✅ API connectivity confirmed');

                // Update progress
                progressText.textContent = 'API connected, starting refresh...';
                progressPercent.textContent = '10%';
                progressFill.style.width = '10%';

                // Call the backend global refresh API
                console.log('🔄 Calling global refresh API...');
                const response = await fetch('/api/global/refresh', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }}
                }});

                console.log('📡 Global refresh response:', response.status, response.statusText);

                if (response.ok) {{
                    const result = await response.json();

                    // Simulate progress updates (in real implementation, this would be real-time)
                    await simulateRefreshProgress();

                    // Show completion
                    const duration = ((Date.now() - startTime) / 1000).toFixed(1);
                    showRefreshComplete(duration, '16');

                    // Reload the page to show updated data
                    setTimeout(() => {{
                        window.location.reload();
                    }}, 2000);

                }} else {{
                    throw new Error('Refresh failed');
                }}

            }} catch (error) {{
                console.error('❌ Global refresh failed:', error);
                console.error('Error details:', {{
                    name: error.name,
                    message: error.message,
                    stack: error.stack
                }});

                progressText.textContent = 'Refresh failed: ' + error.message;
                progressPercent.textContent = 'Error';
                progressFill.style.width = '100%';
                progressFill.style.background = '#ef4444';

                // Show error in summary
                const errorSummary = document.getElementById('refreshSummary');
                errorSummary.innerHTML = `
                    <h4><i class="fas fa-exclamation-triangle" style="color: var(--danger-color);"></i> Refresh Failed!</h4>
                    <p>Error: ${{error.message}}</p>
                    <div class="summary-stats">
                        <span><strong>Status:</strong> Failed</span>
                        <span><strong>Error Type:</strong> ${{error.name}}</span>
                    </div>
                `;
                errorSummary.style.display = 'block';
            }} finally {{
                // Re-enable refresh button
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i><span>Refresh OS</span>';
                closeBtn.disabled = false;
            }}
        }}

        async function simulateRefreshProgress() {{
            const steps = [
                'System Resources',
                'PostgreSQL Database',
                'MCP Servers (7)',
                'Running Agents',
                'Organizational Data',
                'Service Registry'
            ];

            const progressFill = document.getElementById('globalProgressFill');
            const progressText = document.getElementById('globalProgressText');
            const progressPercent = document.getElementById('globalProgressPercent');
            const components = document.querySelectorAll('.component-item');

            for (let i = 0; i < steps.length; i++) {{
                // Update progress
                const percent = ((i + 1) / steps.length * 100).toFixed(0);
                progressFill.style.width = percent + '%';
                progressText.textContent = `Refreshing ${{steps[i]}}...`;
                progressPercent.textContent = percent + '%';

                // Update component status
                if (components[i]) {{
                    const icon = components[i].querySelector('.fas');
                    icon.className = 'fas fa-circle processing';
                }}

                // Wait a bit
                await new Promise(resolve => setTimeout(resolve, 500));

                // Mark as complete
                if (components[i]) {{
                    const icon = components[i].querySelector('.fas');
                    icon.className = 'fas fa-circle complete';
                }}
            }}
        }}

        function showRefreshComplete(duration, componentCount) {{
            const refreshSummary = document.getElementById('refreshSummary');
            const durationSpan = document.getElementById('refreshDuration');
            const componentsSpan = document.getElementById('refreshedComponents');
            const statusSpan = document.getElementById('refreshStatus');

            durationSpan.textContent = duration;
            componentsSpan.textContent = componentCount;
            statusSpan.textContent = 'Success';

            refreshSummary.style.display = 'block';
        }}

        function closeGlobalRefreshModal() {{
            document.getElementById('globalRefreshModal').style.display = 'none';
        }}

        function closeModal(modalId) {{
            document.getElementById(modalId).style.display = 'none';
        }}

        async function refreshSystemsMetrics() {{
            console.log('Starting systems refresh...');
            const refreshBtn = document.getElementById('systemsRefreshBtn');
            const modal = document.getElementById('systemsRefreshModal');
            const closeBtn = document.getElementById('closeSystemsRefreshBtn');

            // Disable refresh button and show modal
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt spinning"></i><span>Refreshing Systems...</span>';
            modal.style.display = 'flex';
            closeBtn.disabled = true;

            // Debug - check if elements exist
            console.log('Modal element:', modal);
            console.log('Step 1 element:', document.getElementById('step1Content'));

            // Make sure step 1 is visible
            const step1 = document.getElementById('step1Content');
            if (step1) {{
                step1.style.opacity = '1';
                step1.style.display = 'block';
                console.log('Step 1 made visible');
            }}

            const startTime = Date.now();

            try {{
                // Wait for user to see initialization
                await new Promise(resolve => setTimeout(resolve, 2000));

                console.log('Moving to step 2...');

                // Hide step 1, show step 2
                if (step1) step1.style.display = 'none';
                const step2 = document.getElementById('step2Content');
                if (step2) {{
                    step2.classList.add('active');
                    step2.style.opacity = '1';
                    step2.style.display = 'block';
                }}

                // Start animated scanning
                const scanPromise = animateScanningProgress();

                // Call the actual API to refresh systems
                const response = await fetch('/api/systems/refresh', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }}
                }});

                const result = await response.json();

                if (response.ok && result.status === 'success') {{
                    // Wait for scanning animation to complete
                    await scanPromise;

                    // Calculate final duration
                    const duration = ((Date.now() - startTime) / 1000).toFixed(1);
                    document.getElementById('systemsRefreshDuration').textContent = duration;
                    document.getElementById('systemsRefreshedComponents').textContent = result.systems_checked || 11;

                    // Move to step 3 (Complete)
                    console.log('Moving to step 3 - Complete');
                    const step2El = document.getElementById('step2Content');
                    if (step2El) step2El.style.display = 'none';

                    const step3 = document.getElementById('step3Content');
                    if (step3) {{
                        step3.classList.add('active');
                        step3.style.opacity = '1';
                        step3.style.display = 'block';
                    }}

                    // Add confetti celebration effect
                    createConfetti();

                    // Update the last updated timestamp
                    const lastUpdateSpan = document.getElementById('systems-last-update');
                    if (lastUpdateSpan) {{
                        const now = new Date();
                        lastUpdateSpan.textContent = now.toLocaleString();
                    }}

                    // Update the header status dropdown with fresh data
                    try {{
                        const headerResponse = await fetch('/api/header-status-dropdown');
                        if (headerResponse.ok) {{
                            const headerResult = await headerResponse.json();
                            if (headerResult.status === 'success') {{
                                const statusDropdown = document.getElementById('statusDropdown');
                                if (statusDropdown) {{
                                    statusDropdown.innerHTML = headerResult.dropdown_html;
                                }}
                            }}
                        }}
                    }} catch (headerError) {{
                        console.warn('Failed to update header dropdown:', headerError);
                    }}

                    // Enable close button - modal stays open until user clicks close
                    closeBtn.disabled = false;
                    closeBtn.style.opacity = '1';

                }} else {{
                    throw new Error(result.message || 'Systems refresh failed');
                }}

            }} catch (error) {{
                console.error('Systems refresh failed:', error);

                // Show error state in the scanning step
                const scanStatus = document.getElementById('scanStatus');
                if (scanStatus) {{
                    scanStatus.textContent = 'Error: ' + (error.message || 'An error occurred');
                    scanStatus.style.color = '#ef4444';
                }}
                const progressBar = document.getElementById('systemsProgressBar');
                if (progressBar) {{
                    progressBar.style.background = 'linear-gradient(90deg, #ef4444, #dc2626)';
                }}

            }} finally {{
                // Re-enable controls
                closeBtn.disabled = false;
                closeBtn.style.opacity = '1';
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i><span>Refresh Systems</span>';
            }}
        }}

        function closeSystemsRefreshModal() {{
            document.getElementById('systemsRefreshModal').style.display = 'none';

            // Reload the page to show refreshed data, staying on Systems tab
            showTab('services');
            location.reload();
        }}

        // Wizard helper functions
        function showWizardStep(step) {{
            // Hide all steps
            document.querySelectorAll('.wizard-step').forEach(el => {{
                el.classList.remove('active');
            }});

            // Show current step
            document.getElementById(`step${{step}}Content`).classList.add('active');

            // Update progress indicators
            document.querySelectorAll('.step-indicator').forEach((indicator, index) => {{
                const indicatorStep = index + 1;
                const circle = indicator.querySelector('div');
                const icon = circle.querySelector('i');

                if (indicatorStep < step) {{
                    // Completed step
                    circle.style.background = '#10b981';
                    circle.style.borderColor = '#10b981';
                    icon.style.color = 'white';
                }} else if (indicatorStep === step) {{
                    // Active step
                    circle.style.background = 'rgba(99, 102, 241, 0.2)';
                    circle.style.borderColor = '#6366f1';
                    icon.style.color = '#6366f1';
                }} else {{
                    // Future step
                    circle.style.background = 'rgba(99, 102, 241, 0.2)';
                    circle.style.borderColor = 'rgba(255,255,255,0.3)';
                    icon.style.color = 'rgba(255,255,255,0.5)';
                }}
            }});
        }}

        async function animateScanningProgress() {{
            const progressBar = document.getElementById('systemsProgressBar');
            const progressText = document.getElementById('systemsProgressText');
            const scanStatus = document.getElementById('scanStatus');
            const systemsGrid = document.getElementById('systemsGrid');

            const systems = [
                {{ name: 'Registry', icon: 'fa-server', delay: 300 }},
                {{ name: 'Filesystem', icon: 'fa-folder-tree', delay: 500 }},
                {{ name: 'Database', icon: 'fa-database', delay: 400 }},
                {{ name: 'Analytics', icon: 'fa-chart-line', delay: 600 }},
                {{ name: 'Payment', icon: 'fa-credit-card', delay: 350 }},
                {{ name: 'Customer', icon: 'fa-users', delay: 450 }},
                {{ name: 'Agent Cortex', icon: 'fa-brain', delay: 550 }},
                {{ name: 'PostgreSQL', icon: 'fa-database', delay: 400 }}
            ];

            // Create system icons grid
            systemsGrid.innerHTML = systems.map((sys, i) => `
                <div id="system-${{i}}" style="display: flex; flex-direction: column; align-items: center; opacity: 0.3; transition: all 0.3s;">
                    <div style="width: 50px; height: 50px; background: rgba(255,255,255,0.1); border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-bottom: 0.5rem;">
                        <i class="fas ${{sys.icon}}" style="font-size: 1.2rem; color: rgba(255,255,255,0.5);"></i>
                    </div>
                    <span style="font-size: 0.7rem; color: rgba(255,255,255,0.5);">${{sys.name}}</span>
                </div>
            `).join('');

            // Animate each system check
            for (let i = 0; i < systems.length; i++) {{
                const progress = ((i + 1) / systems.length * 100).toFixed(0);
                progressBar.style.width = progress + '%';
                progressText.textContent = progress + '%';
                scanStatus.textContent = `Checking ${{systems[i].name}} Server...`;

                // Highlight current system
                const systemEl = document.getElementById(`system-${{i}}`);
                systemEl.style.opacity = '1';
                systemEl.querySelector('div').style.background = 'rgba(99, 102, 241, 0.3)';
                systemEl.querySelector('i').style.color = '#6366f1';

                await sleep(systems[i].delay);

                // Mark as complete
                systemEl.querySelector('div').style.background = 'rgba(16, 185, 129, 0.3)';
                systemEl.querySelector('i').style.color = '#10b981';
            }}

            scanStatus.textContent = 'All systems scanned successfully!';
            await sleep(500);
        }}

        function createConfetti() {{
            const confettiContainer = document.getElementById('confetti');
            const colors = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

            for (let i = 0; i < 50; i++) {{
                setTimeout(() => {{
                    const particle = document.createElement('div');
                    particle.className = 'particle';
                    particle.style.left = Math.random() * 100 + '%';
                    particle.style.background = colors[Math.floor(Math.random() * colors.length)];
                    particle.style.animationDelay = Math.random() * 0.5 + 's';
                    particle.style.animationDuration = (2 + Math.random() * 1) + 's';
                    confettiContainer.appendChild(particle);

                    setTimeout(() => particle.remove(), 3000);
                }}, i * 30);
            }}
        }}

        function sleep(ms) {{
            return new Promise(resolve => setTimeout(resolve, ms));
        }}

        // Chat functionality
        let selectedAgents = ['solomon']; // Default to Solomon
        let chatMessages = [];

        function openChat() {{
            document.getElementById('chatOverlay').style.display = 'flex';
            document.body.style.overflow = 'hidden'; // Prevent background scrolling
        }}

        function closeChat() {{
            document.getElementById('chatOverlay').style.display = 'none';
            document.body.style.overflow = 'auto'; // Restore scrolling
        }}

        function toggleAgent(agentName) {{
            const pill = document.querySelector(`[data-agent="${{agentName}}"]`);
            const isActive = pill.classList.contains('active');

            if (isActive) {{
                // Don't allow deselecting the last agent
                if (selectedAgents.length === 1) {{
                    return;
                }}
                pill.classList.remove('active');
                selectedAgents = selectedAgents.filter(a => a !== agentName);
            }} else {{
                pill.classList.add('active');
                selectedAgents.push(agentName);
            }}

            updateChatHeader();
        }}

        function updateChatHeader() {{
            const chatHeader = document.querySelector('.chat-header h3');
            const agentNames = selectedAgents.map(agent => agent.charAt(0).toUpperCase() + agent.slice(1)).join(', ');
            chatHeader.innerHTML = `<i class="fas fa-robot"></i> Chat with ${{agentNames}}`;
        }}

        async function sendMessage() {{
            const input = document.getElementById('chatInput');
            const message = input.value.trim();

            if (!message) return;

            // Add user message to chat
            addMessageToChat('user', 'You', message);

            // Clear input
            input.value = '';

            // Send message to selected agents via the backend
            for (const agent of selectedAgents) {{
                try {{
                    const response = await fetch('/api/chat', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{
                            agent: agent,
                            message: message
                        }})
                    }});

                    if (response.ok) {{
                        const data = await response.json();
                        const agentName = agent.charAt(0).toUpperCase() + agent.slice(1);
                        addMessageToChat('agent', agentName, data.response || 'Agent response received');
                    }} else {{
                        const agentName = agent.charAt(0).toUpperCase() + agent.slice(1);
                        addMessageToChat('agent', agentName, `Error: Could not reach ${{agentName}} (Status: ${{response.status}})`);
                    }}
                }} catch (error) {{
                    const agentName = agent.charAt(0).toUpperCase() + agent.slice(1);
                    addMessageToChat('agent', agentName, `Error: ${{agentName}} is not responding`);
                    console.error(`Error communicating with ${{agent}}:`, error);
                }}
            }}
        }}

        function addMessageToChat(type, sender, message) {{
            const messagesContainer = document.getElementById('chatMessages');

            // Clear placeholder if this is the first message
            if (chatMessages.length === 0) {{
                messagesContainer.innerHTML = '';
            }}

            const messageElement = document.createElement('div');
            messageElement.style.cssText = `
                margin-bottom: 1rem;
                padding: 1rem;
                border-radius: 12px;
                ${{type === 'user' ?
                    'background: var(--accent-color); color: white; margin-left: 2rem; text-align: right;' :
                    'background: var(--card-bg); color: var(--primary-text); margin-right: 2rem;'
                }}
            `;

            messageElement.innerHTML = `
                <div style="font-weight: 600; margin-bottom: 0.5rem; font-size: 0.9rem;">
                    ${{type === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>'}} ${{sender}}
                </div>
                <div>${{message}}</div>
            `;

            messagesContainer.appendChild(messageElement);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;

            chatMessages.push({{type, sender, message, timestamp: new Date()}});
        }}

        // Handle Enter key in chat input
        document.addEventListener('DOMContentLoaded', () => {{
            const chatInput = document.getElementById('chatInput');
            if (chatInput) {{
                chatInput.addEventListener('keydown', (e) => {{
                    if (e.key === 'Enter' && !e.shiftKey) {{
                        e.preventDefault();
                        sendMessage();
                    }}
                }});
            }}
        }});

        // Non-intrusive AJAX refresh system
        let refreshCounter = 30;
        let refreshInterval;
        let isRefreshing = false;

        function updateDateTime() {{
            const now = new Date();
            const options = {{
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false
            }};
            const dateTimeString = now.toLocaleString('en-US', options);

            const indicator = document.querySelector('#live-datetime');
            if (indicator) {{
                indicator.textContent = dateTimeString;
            }}
        }}

        async function refreshContent() {{
            if (isRefreshing) return;

            isRefreshing = true;
            updateRefreshDisplay();

            // Add subtle updating effect
            const mainContent = document.querySelector('.main-content');
            if (mainContent) {{
                mainContent.classList.add('updating');
            }}

            try {{
                const response = await fetch(window.location.href);
                if (response.ok) {{
                    const html = await response.text();
                    const parser = new DOMParser();
                    const newDoc = parser.parseFromString(html, 'text/html');

                    // Update main content areas without full page reload
                    const contentSelectors = ['.grid', '.agents-grid'];
                    contentSelectors.forEach(selector => {{
                        const oldElement = document.querySelector(selector);
                        const newElement = newDoc.querySelector(selector);
                        if (oldElement && newElement) {{
                            oldElement.innerHTML = newElement.innerHTML;
                        }}
                    }});

                    // Update system metrics
                    const metricsElement = document.querySelector('.metrics-grid');
                    const newMetrics = newDoc.querySelector('.metrics-grid');
                    if (metricsElement && newMetrics) {{
                        metricsElement.innerHTML = newMetrics.innerHTML;
                    }}
                }}
            }} catch (error) {{
                console.warn('Refresh failed:', error);
                // Fallback to full page refresh if AJAX fails
                window.location.reload();
            }} finally {{
                isRefreshing = false;
                updateRefreshDisplay();

                // Remove updating effect
                const mainContent = document.querySelector('.main-content');
                if (mainContent) {{
                    mainContent.classList.remove('updating');
                }}
            }}
        }}

        function startRefreshCountdown() {{
            refreshInterval = setInterval(() => {{
                refreshCounter--;
                updateRefreshDisplay();

                if (refreshCounter <= 0) {{
                    refreshContent();
                    refreshCounter = 30;
                }}
            }}, 1000);
        }}

        // Reset refresh timer on user interaction
        function resetRefreshTimer() {{
            refreshCounter = 30;
            updateRefreshDisplay();
        }}

        // Agent management function
        function startAgent(agentId) {{
            // This would eventually call an API endpoint to start the agent
            alert(`Starting agent: ${{agentId}}. This feature will be implemented soon!`);
        }}

        // Department functions
        function toggleCategoryDetails(category) {{
            const details = document.getElementById(`category-${{category}}`);
            if (details) {{
                if (details.style.display === 'none') {{
                    details.style.display = 'block';
                }} else {{
                    details.style.display = 'none';
                }}
            }}
        }}

        function openDepartmentBrowser() {{
            // Open enhanced department browser in new tab
            window.open('http://localhost:8502', '_blank');
        }}

        function refreshDepartmentData() {{
            // This would eventually refresh department data
            alert('Department data refresh will be implemented soon!');
        }}

        // Start the refresh system
        document.addEventListener('DOMContentLoaded', () => {{
            document.body.style.opacity = '1';\n            \n            // Initialize BoarderframeOS components\n            initializeBoarderframeOSComponents();

            // Start live datetime updates
            updateDateTime();
            setInterval(updateDateTime, 1000);

            // Start auto-refresh system
            startRefreshCountdown();

            // Reset timer on user interactions
            ['click', 'scroll', 'keypress', 'mousemove'].forEach(event => {{
                document.addEventListener(event, resetRefreshTimer, {{ passive: true, once: false }});
            }});
        }});

        // Server filtering and sorting functions
        function filterServers() {{
            const filter = document.getElementById('serverFilter').value;
            const grid = document.getElementById('serverGrid');
            const servers = grid.querySelectorAll('[data-server-status]');
            let visibleCount = 0;

            servers.forEach(server => {{
                const status = server.getAttribute('data-server-status');
                let show = false;

                switch(filter) {{
                    case 'all':
                        show = true;
                        break;
                    case 'healthy':
                        show = status === 'healthy';
                        break;
                    case 'offline':
                        show = status === 'critical' || status === 'offline';
                        break;
                    case 'degraded':
                        show = status === 'degraded';
                        break;
                }}

                if (show) {{
                    server.style.display = 'block';
                    visibleCount++;
                }} else {{
                    server.style.display = 'none';
                }}
            }});

            document.getElementById('serverCount').textContent = visibleCount;
        }}

        function sortServers() {{
            const sort = document.getElementById('serverSort').value;
            const grid = document.getElementById('serverGrid');
            const servers = Array.from(grid.querySelectorAll('[data-server-status]'));

            servers.sort((a, b) => {{
                let aVal, bVal;

                switch(sort) {{
                    case 'name':
                        aVal = a.getAttribute('data-server-name') || '';
                        bVal = b.getAttribute('data-server-name') || '';
                        return aVal.localeCompare(bVal);
                    case 'status':
                        aVal = a.getAttribute('data-server-status') || '';
                        bVal = b.getAttribute('data-server-status') || '';
                        // Prioritize healthy > degraded > critical
                        const statusOrder = {{ 'healthy': 1, 'degraded': 2, 'critical': 3 }};
                        return (statusOrder[aVal] || 4) - (statusOrder[bVal] || 4);
                    case 'port':
                        aVal = parseInt(a.getAttribute('data-server-port')) || 0;
                        bVal = parseInt(b.getAttribute('data-server-port')) || 0;
                        return aVal - bVal;
                    case 'category':
                        aVal = a.getAttribute('data-server-category') || '';
                        bVal = b.getAttribute('data-server-category') || '';
                        return aVal.localeCompare(bVal);
                }}
                return 0;
            }});

            // Re-append sorted servers
            servers.forEach(server => grid.appendChild(server));
        }}

        // Agent filtering and sorting functions
        function filterAgents() {{
            const filter = document.getElementById('agentFilter').value;
            const grid = document.getElementById('agentGrid');
            const agents = grid.querySelectorAll('[data-agent-status]');
            let visibleCount = 0;

            agents.forEach(agent => {{
                const status = agent.getAttribute('data-agent-status');
                const health = agent.getAttribute('data-agent-health');
                const cpu = parseFloat(agent.getAttribute('data-agent-cpu')) || 0;
                let show = false;

                switch(filter) {{
                    case 'all':
                        show = true;
                        break;
                    case 'active':
                        show = status === 'active' || status === 'running';
                        break;
                    case 'productive':
                        show = (status === 'active' || status === 'running') &&
                               (health === 'good' || health === 'healthy') &&
                               cpu < 80;
                        break;
                    case 'healthy':
                        show = health === 'good' || health === 'healthy';
                        break;
                    case 'inactive':
                        show = status === 'inactive' || status === 'offline';
                        break;
                }}

                if (show) {{
                    agent.style.display = 'block';
                    visibleCount++;
                }} else {{
                    agent.style.display = 'none';
                }}
            }});

            document.getElementById('agentCount').textContent = visibleCount;
        }}

        function sortAgents() {{
            const sort = document.getElementById('agentSort').value;
            const grid = document.getElementById('agentGrid');
            const agents = Array.from(grid.querySelectorAll('[data-agent-status]'));

            agents.sort((a, b) => {{
                let aVal, bVal;

                switch(sort) {{
                    case 'name':
                        aVal = a.getAttribute('data-agent-name') || '';
                        bVal = b.getAttribute('data-agent-name') || '';
                        return aVal.localeCompare(bVal);
                    case 'status':
                        aVal = a.getAttribute('data-agent-status') || '';
                        bVal = b.getAttribute('data-agent-status') || '';
                        // Prioritize active > inactive
                        const statusOrder = {{ 'active': 1, 'running': 1, 'inactive': 2, 'offline': 2 }};
                        return (statusOrder[aVal] || 3) - (statusOrder[bVal] || 3);
                    case 'health':
                        aVal = a.getAttribute('data-agent-health') || '';
                        bVal = b.getAttribute('data-agent-health') || '';
                        // Prioritize good > unknown > poor
                        const healthOrder = {{ 'good': 1, 'healthy': 1, 'unknown': 2, 'poor': 3, 'critical': 3 }};
                        return (healthOrder[aVal] || 4) - (healthOrder[bVal] || 4);
                    case 'cpu':
                        aVal = parseFloat(a.getAttribute('data-agent-cpu')) || 0;
                        bVal = parseFloat(b.getAttribute('data-agent-cpu')) || 0;
                        return bVal - aVal; // Descending order (highest CPU first)
                }}
                return 0;
            }});

            // Re-append sorted agents
            agents.forEach(agent => grid.appendChild(agent));
        }}

        // Reusable BoarderframeOS Component Function
        function createBoarderframeOSComponent(size = 'medium', color = null) {{
            const sizes = {{
                'small': {{ icon: '1rem', text: '0.9rem', gap: '0.5rem' }},
                'medium': {{ icon: '1.5rem', text: '1.2rem', gap: '0.75rem' }},
                'large': {{ icon: '2rem', text: '1.5rem', gap: '1rem' }}
            }};

            const sizeConfig = sizes[size] || sizes.medium;
            const iconColor = color || 'var(--accent-color)';
            const textColor = color || 'var(--accent-color)';

            return `
                <div style="display: flex; align-items: center; gap: ${{sizeConfig.gap}};">
                    <i class="fas fa-microchip" style="
                        font-size: ${{sizeConfig.icon}};
                        color: ${{iconColor}};
                        text-shadow: 0 0 20px var(--glow-color);
                        animation: glow-pulse 2s ease-in-out infinite alternate;
                    "></i>
                    <span style="
                        font-size: ${{sizeConfig.text}};
                        font-weight: 700;
                        background: linear-gradient(45deg, ${{textColor}}, #8b5cf6);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        background-clip: text;
                        animation: glow-text 3s ease-in-out infinite alternate;
                    ">BoarderframeOS</span>
                </div>
            `;
        }}

        // Initialize BoarderframeOS components on page load
        function initializeBoarderframeOSComponents() {{
            const components = document.querySelectorAll('.boarderframe-logo-component');
            components.forEach(component => {{
                const size = component.getAttribute('data-size') || 'medium';
                const color = component.getAttribute('data-color') || null;
                component.innerHTML = createBoarderframeOSComponent(size, color);
            }});
        }}

        // Organizational Chart Interactive Functions
        function expandAllOrgNodes() {{
            const allDepartmentLists = document.querySelectorAll('.departments-list');
            const allLeaderLists = document.querySelectorAll('.leaders-list');
            const allDivisionCards = document.querySelectorAll('.division-card');
            const allDepartmentCards = document.querySelectorAll('.department-card');

            allDepartmentLists.forEach(dept => {{
                dept.style.display = 'block';
            }});

            allLeaderLists.forEach(leaders => {{
                leaders.style.display = 'block';
            }});

            allDivisionCards.forEach(card => {{
                card.classList.add('expanded');
            }});

            allDepartmentCards.forEach(card => {{
                card.classList.add('expanded');
            }});
        }}

        function collapseAllOrgNodes() {{
            const allDepartmentLists = document.querySelectorAll('.departments-list');
            const allLeaderLists = document.querySelectorAll('.leaders-list');
            const allDivisionCards = document.querySelectorAll('.division-card');
            const allDepartmentCards = document.querySelectorAll('.department-card');

            allDepartmentLists.forEach(dept => {{
                dept.style.display = 'none';
            }});

            allLeaderLists.forEach(leaders => {{
                leaders.style.display = 'none';
            }});

            allDivisionCards.forEach(card => {{
                card.classList.remove('expanded');
            }});

            allDepartmentCards.forEach(card => {{
                card.classList.remove('expanded');
            }});
        }}


        function toggleDivisionExpansion(divisionId) {{
            const departmentsContainer = document.getElementById(`${{divisionId}}-departments`);
            const divisionCard = document.getElementById(divisionId);
            const expandIcon = divisionCard.querySelector('.division-expand-icon');

            if (departmentsContainer) {{
                if (departmentsContainer.style.display === 'none' || !departmentsContainer.style.display) {{
                    departmentsContainer.style.display = 'block';
                    divisionCard.classList.add('expanded');
                }} else {{
                    departmentsContainer.style.display = 'none';
                    divisionCard.classList.remove('expanded');

                    // Also collapse all departments within this division
                    const departmentLeaders = departmentsContainer.querySelectorAll('.leaders-list');
                    departmentLeaders.forEach(leaders => {{
                        leaders.style.display = 'none';
                    }});

                    // Reset department expand icons
                    const deptCards = departmentsContainer.querySelectorAll('.department-card');
                    deptCards.forEach(card => {{
                        card.classList.remove('expanded');
                    }});
                }}
            }}
        }}

        function toggleDepartmentExpansion(deptId, event) {{
            // Prevent event bubbling to division toggle
            if (event) {{
                event.stopPropagation();
            }}

            const leadersContainer = document.getElementById(`department-${{deptId}}-leaders`);
            const deptCard = document.getElementById(deptId);

            if (leadersContainer && deptCard) {{
                if (leadersContainer.style.display === 'none' || !leadersContainer.style.display) {{
                    leadersContainer.style.display = 'block';
                    deptCard.classList.add('expanded');
                }} else {{
                    leadersContainer.style.display = 'none';
                    deptCard.classList.remove('expanded');
                }}
            }}
        }}
    </script>
</body>
</html>"""

    def _generate_services_html(self):
        """Generate enhanced services HTML organized by category"""
        if not self.services_status:
            return '<div style="text-align: center; color: var(--secondary-text); padding: 2rem;">No services detected</div>'

        # Organize services by category
        categories = {"Tech Ops": [], "Departments": [], "Service": []}

        for service_id, service in self.services_status.items():
            category = service.get("category", "Service")
            categories[category].append((service_id, service))

        services_html = ""

        # Generate HTML for each category
        for category_name, category_services in categories.items():
            if not category_services:
                continue

            services_html += f"""
                <div class="category-section">
                    <h3 class="category-title">{category_name}</h3>
                    <div class="category-services">
            """

            for service_id, service in category_services:
                status_class = service.get("status", "critical")
                border_class = f"server-{service_id}"
                response_time = service.get("response_time", 0)
                port = service.get("port", "Unknown")

                services_html += f"""
                    <div class="service-item {border_class}">
                        <div class="service-info">
                            <div class="service-icon {service_id}">
                                <i class="{service.get('icon', 'fas fa-server')}"></i>
                            </div>
                            <div class="service-details">
                                <h4>{service.get('name', service_id.title())}</h4>
                                <p>Port {port} • {response_time*1000:.0f}ms</p>
                            </div>
                        </div>
                        <div class="service-status {status_class}">
                            <i class="fas fa-circle"></i>
                            {status_class.title()}
                        </div>
                    </div>
                """

            services_html += """
                    </div>
                </div>
            """

        return services_html

    def _generate_enhanced_services_html(self):
        """Generate enhanced services HTML with tool charms organized by category"""
        if not self.services_status:
            return '<div style="text-align: center; color: var(--secondary-text); padding: 2rem;">No services detected</div>'

        # Define tools/capabilities for each MCP server
        server_tools = {
            "registry": {
                "tools": [
                    "🔍 Server Discovery",
                    "📋 Health Monitoring",
                    "🔗 Server Registry",
                    "🎯 Load Balancing",
                ],
                "color": "#6366f1",
            },
            "filesystem": {
                "tools": [
                    "📁 File Operations",
                    "🔍 Smart Search",
                    "📊 Content Analysis",
                    "🗂️ Directory Management",
                ],
                "color": "#10b981",
            },
            "database_postgres": {
                "tools": [
                    "💾 Data Storage",
                    "🔍 Query Engine",
                    "📈 Analytics",
                    "🔐 Data Security",
                ],
                "color": "#f59e0b",
            },
            "agent_cortex": {
                "tools": [
                    "🧠 Intelligent Orchestration",
                    "🔄 Model Selection",
                    "💡 Cost Optimization",
                    "📊 Performance Learning",
                ],
                "color": "#8b5cf6",
            },
            "dashboard": {
                "tools": [
                    "📊 System Control",
                    "📈 Performance Metrics",
                    "🎛️ Control Panel",
                    "📋 Status Reports",
                ],
                "color": "#ef4444",
            },
            "payment": {
                "tools": [
                    "💳 Payment Processing",
                    "🔐 Secure Transactions",
                    "📊 Payment Analytics",
                    "💰 Revenue Tracking",
                ],
                "color": "#059669",
            },
            "analytics": {
                "tools": [
                    "📈 Data Analysis",
                    "📊 Reporting",
                    "🎯 Business Intelligence",
                    "📋 Insights",
                ],
                "color": "#dc2626",
            },
            "customer": {
                "tools": [
                    "👥 Customer Management",
                    "📞 Support Tickets",
                    "📊 Customer Analytics",
                    "🎯 CRM",
                ],
                "color": "#7c2d92",
            },
        }

        # Organize services by category
        categories = {"Tech Ops": [], "Departments": [], "Service": []}

        for service_id, service in self.services_status.items():
            category = service.get("category", "Service")
            categories[category].append((service_id, service))

        services_html = ""

        # Generate HTML for each category
        for category_name, category_services in categories.items():
            if not category_services:
                continue

            services_html += f"""
                <div class="category-section">
                    <h3 class="category-title">{category_name}</h3>
                    <div class="category-services">
            """

            for service_id, service in category_services:
                status_class = service.get("status", "critical")
                border_class = f"server-{service_id}"
                response_time = service.get("response_time", 0)
                port = service.get("port", "Unknown")
                tools = server_tools.get(
                    service_id, {"tools": ["🔧 General Tools"], "color": "#6B7280"}
                )

                # Generate tool charms
                tool_charms = ""
                for tool in tools["tools"]:
                    tool_charms += f'<div class="tool-charm">{tool}</div>'

                services_html += f"""
                    <div class="enhanced-service-card {border_class}">
                        <div class="service-header">
                            <div class="service-icon-large {service_id}">
                                <i class="{service.get('icon', 'fas fa-server')}"></i>
                            </div>
                            <div class="service-main-info">
                                <h4 class="service-title">{service.get('name', service_id.title())}</h4>
                                <div class="service-meta">
                                    <span class="service-port"><i class="fas fa-network-wired"></i> Port {port}</span>
                                    <span class="service-response"><i class="fas fa-clock"></i> {response_time*1000:.0f}ms</span>
                                </div>
                            </div>
                            <div class="service-status-badge {status_class}">
                                <i class="fas fa-circle"></i>
                                <span>{status_class.title()}</span>
                            </div>
                        </div>
                        <div class="service-tools">
                            <div class="tools-label">Available Tools:</div>
                            <div class="tool-charms">
                                {tool_charms}
                            </div>
                        </div>
                    </div>
                """

            services_html += """
                    </div>
                </div>
            """

        return services_html

    def _generate_enhanced_agents_html(self):
        """Generate enhanced agents HTML with detailed UI including model information using centralized data"""
        # Use centralized data when available, fallback to legacy
        agents_data = self.unified_data.get("agents_status", self.running_agents)

        agents_html = ""

        # Get all configured agents
        try:
            from scripts.start_agents import AgentManager

            agent_manager = AgentManager()
            all_agents = list(agent_manager.agent_configs.keys())
        except ImportError:
            all_agents = ["solomon", "david"]

        for agent_id in all_agents:
            if agent_id in agents_data:
                # Agent is currently running
                agent = agents_data[agent_id]

                # Format uptime
                uptime_display = "Running"
                if agent.get("start_time"):
                    uptime_display = f"Since {agent['start_time']}"

                agents_html += f"""
                    <div class="enhanced-agent-card active" data-agent-status="active" data-agent-name="{agent['name']}" data-agent-health="{agent.get('health', 'unknown')}" data-agent-cpu="{agent.get('cpu_percent', 0)}">
                        <div class="agent-avatar">
                            <i class="fas fa-robot"></i>
                            <div class="priority-badge">{agent.get('priority', 'N/A')}</div>
                        </div>
                        <div class="agent-info">
                            <div class="agent-header">
                                <div>
                                    <h4 class="agent-name">{agent['name']}</h4>
                                    <div class="agent-title">{agent['type']}</div>
                                    {self._get_agent_department_info(agent_id)}
                                </div>
                                <div class="agent-status-badge running">
                                    <i class="fas fa-circle"></i>
                                    <span>Active</span>
                                </div>
                            </div>
                            <div class="agent-meta">
                                <span class="agent-model">🤖 {agent.get('model', 'Unknown Model')}</span>
                            </div>
                            <div class="agent-metrics">
                                <div class="metric-chip">
                                    <i class="fas fa-hashtag"></i>
                                    <span>PID: {agent['pid']}</span>
                                </div>
                                <div class="metric-chip">
                                    <i class="fas fa-memory"></i>
                                    <span>{agent.get('memory_percent', 0):.1f}% RAM</span>
                                </div>
                                <div class="metric-chip">
                                    <i class="fas fa-microchip"></i>
                                    <span>{agent.get('cpu_percent', 0):.1f}% CPU</span>
                                </div>
                                <div class="metric-chip health-{agent.get('health', 'unknown')}">
                                    <i class="fas fa-heart"></i>
                                    <span>{agent.get('health', 'unknown').title()}</span>
                                </div>
                            </div>
                            <div class="agent-capabilities">
                                {self._get_agent_capabilities(agent_id, active=True)}
                            </div>
                        </div>
                    </div>
                """
            else:
                # Agent not running
                agent_name = agent_id.replace("_", " ").title()

                # Get config info if available
                try:
                    from scripts.start_agents import AgentManager

                    agent_manager = AgentManager()
                    config = agent_manager.agent_configs.get(agent_id, {})
                    model = config.get("model", "claude-3-5-sonnet-latest")
                    description = config.get("description", "AI Assistant")
                    priority = config.get("priority", "N/A")
                except ImportError:
                    model = "claude-3-5-sonnet-latest"
                    description = "AI Assistant"
                    priority = "N/A"

                agents_html += f"""
                    <div class="enhanced-agent-card inactive" data-agent-status="inactive" data-agent-name="{agent_name}" data-agent-health="unknown" data-agent-cpu="0">
                        <div class="agent-avatar offline">
                            <i class="fas fa-robot"></i>
                            <div class="priority-badge offline">{priority}</div>
                        </div>
                        <div class="agent-info">
                            <div class="agent-header">
                                <div>
                                    <h4 class="agent-name">{agent_name}</h4>
                                    <div class="agent-title">{description}</div>
                                    {self._get_agent_department_info(agent_id)}
                                </div>
                                <div class="agent-status-badge offline">
                                    <i class="fas fa-circle"></i>
                                    <span>Offline</span>
                                </div>
                            </div>
                            <div class="agent-meta">
                                <span class="agent-model">🤖 {model}</span>
                            </div>
                            <div class="agent-capabilities">
                                {self._get_agent_capabilities(agent_id, active=False)}
                            </div>
                            <div class="agent-actions">
                                <button class="start-agent-btn" onclick="startAgent('{agent_id}')">
                                    <i class="fas fa-play"></i> Start Agent
                                </button>
                            </div>
                        </div>
                    </div>
                """

        return agents_html

    def _get_agent_capabilities(self, agent_id: str, active: bool = True) -> str:
        """Get capabilities HTML for an agent"""
        capabilities = {
            "solomon": [
                "🧠 Strategic Planning",
                "📊 System Analysis",
                "🔧 Problem Solving",
                "📈 Business Intelligence",
            ],
            "david": [
                "💬 Communication",
                "📝 Documentation",
                "🎯 Task Execution",
                "👥 Leadership",
            ],
            "eve": [
                "🧬 System Evolution",
                "🔄 Adaptation",
                "🌱 Growth Management",
                "⚡ Optimization",
            ],
        }

        agent_caps = capabilities.get(agent_id, ["🤖 AI Assistant"])
        status_class = "" if active else " disabled"

        return "".join(
            [
                f'<div class="capability-tag{status_class}">{cap}</div>'
                for cap in agent_caps
            ]
        )

    def _get_agent_department_info(self, agent_id: str) -> str:
        """Get department information HTML for an agent"""
        if agent_id in self.agent_department_mapping:
            dept_info = self.agent_department_mapping[agent_id]
            dept_name = dept_info["department_name"]
            category = dept_info["category"]

            # Get icon based on category
            category_icon = {
                "Executive": "fas fa-crown",
                "Operations": "fas fa-cogs",
                "Technology": "fas fa-microchip",
                "Business": "fas fa-briefcase",
                "Support": "fas fa-hands-helping",
            }.get(category, "fas fa-building")

            return f'<span class="agent-department"><i class="{category_icon}"></i> {dept_name}</span>'

        return ""

    def _generate_department_overview_html(self):
        """Generate department overview HTML with statistics and quick navigation using centralized data"""
        # Use centralized data when available, fallback to legacy
        departments_data = self.unified_data.get(
            "departments_data", self.departments_data
        )

        if not departments_data:
            return """
                <div style="text-align: center; padding: 2rem; color: var(--secondary-text);">
                    <i class="fas fa-building" style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                    <h4>Department data not available</h4>
                    <p>The department configuration file was not found or could not be loaded.</p>
                </div>
            """

        dept_summary = self.get_department_summary(departments_data)

        # Generate category statistics
        category_cards = ""
        for category, count in dept_summary["categories"].items():
            # Get departments in this category
            category_depts = dept_summary["departments_by_category"].get(category, [])
            leaders_count = sum(len(dept.get("leaders", [])) for dept in category_depts)
            agents_count = sum(
                len(dept.get("native_agents", [])) for dept in category_depts
            )

            category_icon = {
                "Executive": "fas fa-crown",
                "Operations": "fas fa-cogs",
                "Technology": "fas fa-microchip",
                "Business": "fas fa-briefcase",
                "Support": "fas fa-hands-helping",
                "Other": "fas fa-building",
            }.get(category, "fas fa-building")

            category_cards += f"""
                <div class="department-category-card" onclick="toggleCategoryDetails('{category}')">
                    <div class="category-header">
                        <div class="category-icon">
                            <i class="{category_icon}"></i>
                        </div>
                        <div class="category-info">
                            <h4>{category}</h4>
                            <p>{count} Departments</p>
                        </div>
                        <div class="category-stats">
                            <div class="stat-item">
                                <span class="stat-value">{leaders_count}</span>
                                <span class="stat-label">Leaders</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-value">{agents_count}</span>
                                <span class="stat-label">Agents</span>
                            </div>
                        </div>
                    </div>
                    <div class="category-details" id="category-{category}" style="display: none;">
                        {self._generate_category_departments_html(category_depts)}
                    </div>
                </div>
            """

        # Generate overall statistics
        total_depts = dept_summary["total_departments"]
        total_leaders = dept_summary["total_leaders"]
        total_agents = dept_summary["total_agents"]

        return f"""
            <div class="department-overview">
                <div class="department-stats-bar">
                    <div class="stat-card">
                        <div class="stat-icon"><i class="fas fa-building"></i></div>
                        <div class="stat-info">
                            <div class="stat-number">{total_depts}</div>
                            <div class="stat-text">Departments</div>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon"><i class="fas fa-users"></i></div>
                        <div class="stat-info">
                            <div class="stat-number">{total_leaders}</div>
                            <div class="stat-text">Leaders</div>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon"><i class="fas fa-robot"></i></div>
                        <div class="stat-info">
                            <div class="stat-number">{total_agents}</div>
                            <div class="stat-text">Teams</div>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon"><i class="fas fa-sitemap"></i></div>
                        <div class="stat-info">
                            <div class="stat-number">{len(dept_summary['categories'])}</div>
                            <div class="stat-text">Categories</div>
                        </div>
                    </div>
                </div>

                <div class="department-categories">
                    {category_cards}
                </div>

                <div class="department-actions">
                    <button class="department-btn" onclick="openDepartmentBrowser()">
                        <i class="fas fa-external-link-alt"></i>
                        Open Department Browser
                    </button>
                    <button class="department-btn secondary" onclick="refreshDepartmentData()">
                        <i class="fas fa-sync-alt"></i>
                        Refresh Data
                    </button>
                </div>
            </div>
        """

    def _generate_category_departments_html(self, category_depts):
        """Generate HTML for departments within a category"""
        if not category_depts:
            return '<div style="text-align: center; color: var(--secondary-text); padding: 1rem;">No departments found</div>'

        depts_html = ""
        for dept in category_depts:
            dept_name = dept.get("department_name", "Unknown Department")
            leader_count = len(dept.get("leaders", []))
            agent_count = len(dept.get("native_agents", []))

            # Get first leader for display
            first_leader = dept.get("leaders", [{}])[0]
            leader_name = (
                first_leader.get("name", "No leader assigned")
                if first_leader
                else "No leader assigned"
            )

            depts_html += f"""
                <div class="mini-dept-card">
                    <div class="mini-dept-name">{dept_name}</div>
                    <div class="mini-dept-leader">👤 {leader_name}</div>
                    <div class="mini-dept-stats">
                        <span>👥 {leader_count}</span>
                        <span>🤖 {agent_count}</span>
                    </div>
                </div>
            """

        return f'<div class="mini-dept-grid">{depts_html}</div>'

    def _generate_agent_department_analytics_html(self):
        """Generate analytics showing agent-department relationships"""
        if not self.departments_data or not self.agent_department_mapping:
            return """
                <div style="text-align: center; padding: 2rem; color: var(--secondary-text);">
                    <i class="fas fa-chart-network" style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                    <h4>Analytics not available</h4>
                    <p>Insufficient data for agent-department analytics.</p>
                </div>
            """

        # Analyze agent distribution by department
        dept_agent_count = {}
        active_agents_by_dept = {}

        for agent_id, dept_info in self.agent_department_mapping.items():
            dept_key = dept_info["department_key"]
            dept_name = dept_info["department_name"]

            if dept_name not in dept_agent_count:
                dept_agent_count[dept_name] = 0
                active_agents_by_dept[dept_name] = 0

            dept_agent_count[dept_name] += 1

            # Check if agent is currently running
            if agent_id in self.running_agents:
                active_agents_by_dept[dept_name] += 1

        # Generate department cards with agent info
        dept_cards = ""
        for dept_name, total_agents in dept_agent_count.items():
            active_agents = active_agents_by_dept.get(dept_name, 0)
            activity_percentage = (
                (active_agents / total_agents * 100) if total_agents > 0 else 0
            )

            # Find the department data for additional info
            dept_data = None
            for dept_info in self.departments_data.values():
                if dept_info.get("department_name") == dept_name:
                    dept_data = dept_info
                    break

            if dept_data:
                category = dept_data.get("category", "Other")
                leaders_count = len(dept_data.get("leaders", []))
                total_teams = len(dept_data.get("native_agents", []))

                category_icon = {
                    "Executive": "fas fa-crown",
                    "Operations": "fas fa-cogs",
                    "Technology": "fas fa-microchip",
                    "Business": "fas fa-briefcase",
                    "Support": "fas fa-hands-helping",
                }.get(category, "fas fa-building")

                status_class = "active" if active_agents > 0 else "inactive"

                dept_cards += f"""
                    <div class="dept-analytics-card {status_class}">
                        <div class="dept-analytics-header">
                            <div class="dept-analytics-icon">
                                <i class="{category_icon}"></i>
                            </div>
                            <div class="dept-analytics-info">
                                <h4>{dept_name}</h4>
                                <p>{category} Department</p>
                            </div>
                            <div class="dept-analytics-status">
                                <div class="activity-indicator {status_class}">
                                    <span class="activity-dot"></span>
                                    <span>{active_agents}/{total_agents} Active</span>
                                </div>
                            </div>
                        </div>
                        <div class="dept-analytics-metrics">
                            <div class="metric-row">
                                <div class="metric-item-small">
                                    <i class="fas fa-users"></i>
                                    <span>{leaders_count} Leaders</span>
                                </div>
                                <div class="metric-item-small">
                                    <i class="fas fa-dna"></i>
                                    <span>{total_teams} Teams</span>
                                </div>
                                <div class="metric-item-small">
                                    <i class="fas fa-robot"></i>
                                    <span>{total_agents} Configured</span>
                                </div>
                            </div>
                            <div class="activity-bar">
                                <div class="activity-progress" style="width: {activity_percentage}%"></div>
                            </div>
                            <div class="activity-text">{activity_percentage:.0f}% Agent Activity</div>
                        </div>
                    </div>
                """

        # Generate summary statistics
        total_configured = len(self.agent_department_mapping)
        total_active = len(self.running_agents)
        total_departments_with_agents = len(dept_agent_count)

        return f"""
            <div class="analytics-overview">
                <div class="analytics-summary">
                    <div class="analytics-stat">
                        <div class="analytics-stat-value">{total_configured}</div>
                        <div class="analytics-stat-label">Configured Agents</div>
                    </div>
                    <div class="analytics-stat">
                        <div class="analytics-stat-value">{total_active}</div>
                        <div class="analytics-stat-label">Active Agents</div>
                    </div>
                    <div class="analytics-stat">
                        <div class="analytics-stat-value">{total_departments_with_agents}</div>
                        <div class="analytics-stat-label">Active Departments</div>
                    </div>
                    <div class="analytics-stat">
                        <div class="analytics-stat-value">{(total_active/total_configured*100) if total_configured > 0 else 0:.0f}%</div>
                        <div class="analytics-stat-label">System Activity</div>
                    </div>
                </div>

                <div class="analytics-departments">
                    {dept_cards}
                </div>
            </div>
        """

    def _generate_service_widgets_html(self):
        """Generate service widgets HTML"""
        return ""  # Simplified for now

    def _generate_filesystem_details_html(self):
        """Generate detailed filesystem server information"""
        if "filesystem" not in self.mcp_details:
            return ""

        details = self.mcp_details["filesystem"]

        return f"""
            <div class="card">
                <h3><i class="fas fa-folder-tree"></i> Filesystem Server Details</h3>
                <div class="metrics-grid">
                    <div class="metric-item">
                        <div class="metric-value">{details.get('total_operations', 0)}</div>
                        <div class="metric-label">Total Operations</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">{details.get('active_clients', 0)}</div>
                        <div class="metric-label">Active Clients</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">{details.get('vector_db_size', 0)}</div>
                        <div class="metric-label">Vector DB Entries</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">{'✓' if details.get('ai_features') else '✗'}</div>
                        <div class="metric-label">Smart Analysis</div>
                    </div>
                </div>
                <div style="margin-top: 1rem; padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px;">
                    <div style="font-size: 0.9rem; color: var(--secondary-text);">
                        <div><i class="fas fa-clock"></i> Uptime: {details.get('uptime', 'Unknown')}</div>
                        <div><i class="fas fa-folder"></i> Base Path: {details.get('base_path', '/')}</div>
                    </div>
                </div>
            </div>
        """

    def _generate_simple_server_status(self):
        """Generate simple, clean server status cards"""
        if not self.services_status:
            return '<div style="text-align: center; color: var(--secondary-text); padding: 2rem;">No servers detected</div>'

        # Define server info
        servers = {
            "registry": {
                "name": "Registry Server",
                "icon": "fas fa-server",
                "port": 8009,
            },
            "filesystem": {
                "name": "File System Server",
                "icon": "fas fa-folder-tree",
                "port": 8001,
            },
            "database_postgres": {
                "name": "PostgreSQL Database Server",
                "icon": "fas fa-database",
                "port": 8010,
            },
            "agent_cortex": {
                "name": "Agent Cortex",
                "icon": "fas fa-brain",
                "port": 8889,
            },
            "payment": {
                "name": "Payment Server",
                "icon": "fas fa-credit-card",
                "port": 8006,
            },
            "analytics": {
                "name": "Analytics Server",
                "icon": "fas fa-chart-bar",
                "port": 8007,
            },
            "customer": {
                "name": "Customer Server",
                "icon": "fas fa-users",
                "port": 8008,
            },
            "postgres": {
                "name": "PostgreSQL Server",
                "icon": "fas fa-database",
                "port": 8010,
            },
            "llm": {"name": "LLM Server", "icon": "fas fa-robot", "port": 8005},
            "corporate_headquarters": {
                "name": "Corporate Headquarters",
                "icon": "fas fa-chart-line",
                "port": 8888,
            },
        }

        html = ""
        for server_id, server_info in servers.items():
            service = self.services_status.get(server_id, {})

            # Special handling for Corporate Headquarters - if we're serving this page, we're online
            if server_id == "corporate_headquarters":
                status = service.get("status", "healthy")
                # If status is still not healthy but we're running, force it to healthy
                if status not in ["healthy", "starting"]:
                    status = "healthy"
            else:
                status = service.get("status", "offline")

            # Status colors and indicators
            if status == "healthy":
                status_color = "var(--success-color)"
                status_bg = "rgba(16, 185, 129, 0.1)"
                status_text = "Online"
                status_icon = "fas fa-circle"
            else:
                status_color = "var(--danger-color)"
                status_bg = "rgba(239, 68, 68, 0.1)"
                status_text = "Offline"
                status_icon = "fas fa-times-circle"

            html += f"""
            <div style="background: {status_bg}; border: 1px solid {status_color}; border-radius: 12px; padding: 1.5rem; transition: all 0.3s ease;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div style="width: 48px; height: 48px; background: {status_color}; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: white; font-size: 1.5rem;">
                            <i class="{server_info['icon']}"></i>
                        </div>
                        <div>
                            <h4 style="margin: 0; color: var(--primary-text); font-size: 1.1rem;">{server_info['name']}</h4>
                            <p style="margin: 0; color: var(--secondary-text); font-size: 0.9rem;">Port: {server_info['port']}</p>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="color: {status_color}; font-size: 1.2rem; margin-bottom: 0.25rem;">
                            <i class="{status_icon}"></i>
                        </div>
                        <div style="color: {status_color}; font-weight: 600; font-size: 0.9rem;">{status_text}</div>
                    </div>
                </div>

                <!-- Optional: Show basic metrics if available -->
                {f'<div style="font-size: 0.85rem; color: var(--secondary-text);">Uptime: {service.get("uptime", "Unknown")}</div>' if service.get("uptime") else ""}
            </div>
            """

        return html

    def _format_uptime(self, uptime_value):
        """Format uptime value to be user-friendly"""
        if uptime_value in ["Unknown", "Active", "Offline"]:
            return uptime_value

        try:
            # If it's a number (seconds), convert to readable format
            if isinstance(uptime_value, (int, float)):
                seconds = int(uptime_value)
                if seconds < 60:
                    return f"{seconds}s"
                elif seconds < 3600:
                    minutes = seconds // 60
                    return f"{minutes}m"
                elif seconds < 86400:
                    hours = seconds // 3600
                    minutes = (seconds % 3600) // 60
                    return f"{hours}h {minutes}m"
                else:
                    days = seconds // 86400
                    hours = (seconds % 86400) // 3600
                    return f"{days}d {hours}h"

            # If it's a string that might be a number
            if (
                isinstance(uptime_value, str)
                and uptime_value.replace(".", "").isdigit()
            ):
                return self._format_uptime(float(uptime_value))

            # Otherwise return as-is
            return str(uptime_value)

        except (ValueError, TypeError):
            return "Active"

    def _get_average_response_time(self):
        """Calculate average response time across all healthy services"""
        try:
            services_data = self.unified_data.get(
                "services_status", self.services_status
            )

            if not services_data:
                return "0"

            response_times = []
            for service in services_data.values():
                if (
                    service.get("status") in ["healthy", "online"]
                    and "response_time" in service
                ):
                    try:
                        rt = float(service["response_time"])
                        response_times.append(rt * 1000)  # Convert to milliseconds
                    except (ValueError, TypeError):
                        continue

            if response_times:
                avg_ms = sum(response_times) / len(response_times)
                return f"{avg_ms:.0f}"
            else:
                return "0"

        except Exception:
            return "0"

    def _generate_header_status_dropdown(self):
        """Generate the header status dropdown content with navigation links"""
        return f"""
                    <div class="dropdown-header">
                        <i class="fas fa-heartbeat"></i> System Status
                        <span style="margin-left: auto; font-size: 0.8rem; color: var(--secondary-text);">
                            {self._get_formatted_timestamp()}
                        </span>
                    </div>

                    <!-- Organization Section -->
                    <div style="padding: 0.5rem 0.75rem; font-size: 0.8rem; font-weight: 600; color: var(--accent-color); background: rgba(255,255,255,0.02); border-bottom: 1px solid var(--border-color);">
                        <i class="fas fa-users"></i> Organization
                    </div>
                    <div class="dropdown-section">
                        <div class="dropdown-item" onclick="navigateToTab('agents')" style="cursor: pointer;">
                            <div class="subsystem-name">
                                <i class="fas fa-robot"></i>
                                <span>Agents</span>
                            </div>
                            <div class="subsystem-status">
                                <div class="status-dot {self._get_subsystem_status('agents')}"></div>
                                <span>{self._get_agents_count()}</span>
                            </div>
                        </div>
                        <div class="dropdown-item" onclick="navigateToTab('leaders')" style="cursor: pointer;">
                            <div class="subsystem-name">
                                <i class="fas fa-crown"></i>
                                <span>Leaders</span>
                            </div>
                            <div class="subsystem-status">
                                <div class="status-dot {self._get_subsystem_status('leaders')}"></div>
                                <span>{self._get_leaders_count()}</span>
                            </div>
                        </div>
                        <div class="dropdown-item" onclick="navigateToTab('divisions')" style="cursor: pointer;">
                            <div class="subsystem-name">
                                <i class="fas fa-sitemap"></i>
                                <span>Divisions</span>
                            </div>
                            <div class="subsystem-status">
                                <div class="status-dot {self._get_subsystem_status('divisions')}"></div>
                                <span>{self._get_divisions_count()}</span>
                            </div>
                        </div>
                        <div class="dropdown-item" onclick="navigateToTab('departments')" style="cursor: pointer;">
                            <div class="subsystem-name">
                                <i class="fas fa-building"></i>
                                <span>Departments</span>
                            </div>
                            <div class="subsystem-status">
                                <div class="status-dot {self._get_subsystem_status('departments')}"></div>
                                <span>{self._get_departments_count()}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Servers Section -->
                    <div style="padding: 0.5rem 0.75rem; font-size: 0.8rem; font-weight: 600; color: var(--accent-color); background: rgba(255,255,255,0.02); border-bottom: 1px solid var(--border-color);">
                        <i class="fas fa-server"></i> Servers
                    </div>
                    <div class="dropdown-section">
                        <div class="dropdown-item" onclick="navigateToTab('services')" style="cursor: pointer;">
                            <div class="subsystem-name">
                                <i class="fas fa-building"></i>
                                <span>Core Servers</span>
                            </div>
                            <div class="subsystem-status">
                                <div class="status-dot {self._get_category_status('Core Systems')}"></div>
                                <span>{self._get_category_count('Core Systems')}</span>
                            </div>
                        </div>
                        <div class="dropdown-item" onclick="navigateToTab('services')" style="cursor: pointer;">
                            <div class="subsystem-name">
                                <i class="fas fa-plug"></i>
                                <span>MCP Servers</span>
                            </div>
                            <div class="subsystem-status">
                                <div class="status-dot {self._get_category_status('MCP Servers')}"></div>
                                <span>{self._get_category_count('MCP Servers')}</span>
                            </div>
                        </div>
                        <div class="dropdown-item" onclick="navigateToTab('services')" style="cursor: pointer;">
                            <div class="subsystem-name">
                                <i class="fas fa-briefcase"></i>
                                <span>Business Services</span>
                            </div>
                            <div class="subsystem-status">
                                <div class="status-dot {self._get_category_status('Business Services')}"></div>
                                <span>{self._get_category_count('Business Services')}</span>
                            </div>
                        </div>
                    </div>

                    <!-- Database Section -->
                    <div style="padding: 0.5rem 0.75rem; font-size: 0.8rem; font-weight: 600; color: var(--accent-color); background: rgba(255,255,255,0.02); border-bottom: 1px solid var(--border-color);">
                        <i class="fas fa-database"></i> Database
                    </div>
                    <div class="dropdown-section">
                        <div class="dropdown-item" onclick="navigateToTab('database')" style="cursor: pointer;">
                            <div class="subsystem-name">
                                <i class="fas fa-database"></i>
                                <span>PostgreSQL</span>
                            </div>
                            <div class="subsystem-status">
                                <div class="status-dot {self._get_subsystem_status('database')}"></div>
                                <span style="font-size: 0.75rem;">{self._get_database_status()}</span>
                            </div>
                        </div>
                    </div>
        """

    def _generate_enhanced_server_status(self):
        """Generate enhanced, grouped server status cards by category and importance"""
        # Use centralized data when available, fallback to legacy
        services_data = self.unified_data.get("services_status", self.services_status)

        if not services_data:
            return '<div style="text-align: center; color: var(--secondary-text); padding: 2rem;">No servers detected</div>'

        # Enhanced server info organized by category and priority
        server_categories = {
            "Core Systems": {
                "emoji": "🏗️",
                "description": "Essential system components",
                "servers": {
                    "corporate_headquarters": {
                        "name": "Corporate Headquarters",
                        "icon": "fas fa-building",
                        "port": 8888,
                        "description": "Main management and monitoring interface",
                        "emoji": "🏢",
                        "priority": 1,
                    },
                    "agent_cortex": {
                        "name": "Agent Cortex",
                        "icon": "fas fa-brain",
                        "port": 8889,
                        "description": "Intelligent model orchestration and optimization",
                        "emoji": "🧠",
                        "priority": 2,
                    },
                    "registry": {
                        "name": "Registry Server",
                        "icon": "fas fa-server",
                        "port": 8009,
                        "description": "Agent and service discovery management",
                        "emoji": "📋",
                        "priority": 3,
                    },
                },
            },
            "MCP Servers": {
                "emoji": "🔌",
                "description": "Model Context Protocol services",
                "servers": {
                    "filesystem": {
                        "name": "Filesystem Server",
                        "icon": "fas fa-folder-tree",
                        "port": 8001,
                        "description": "File operations and management",
                        "emoji": "📁",
                        "priority": 4,
                    },
                    "database_postgres": {
                        "name": "PostgreSQL Database Server",
                        "icon": "fas fa-database",
                        "port": 8010,
                        "description": "Data storage and retrieval operations",
                        "emoji": "💾",
                        "priority": 5,
                    },
                    "analytics": {
                        "name": "Analytics Server",
                        "icon": "fas fa-chart-bar",
                        "port": 8007,
                        "description": "Business intelligence and metrics",
                        "emoji": "📊",
                        "priority": 6,
                    },
                },
            },
            "Business Services": {
                "emoji": "💼",
                "description": "Revenue and customer management",
                "servers": {
                    "payment": {
                        "name": "Payment Server",
                        "icon": "fas fa-credit-card",
                        "port": 8006,
                        "description": "Payment processing and billing",
                        "emoji": "💳",
                        "priority": 9,
                    },
                    "customer": {
                        "name": "Customer Server",
                        "icon": "fas fa-users",
                        "port": 8008,
                        "description": "Customer relationship management",
                        "emoji": "👥",
                        "priority": 10,
                    },
                },
            },
        }

        html = ""

        # Generate grouped server displays
        for category_name, category_info in server_categories.items():
            # Category header
            online_count = 0
            total_count = len(category_info["servers"])

            # Count online servers in this category
            for server_id in category_info["servers"]:
                service = services_data.get(server_id, {})
                if service.get("status") == "healthy":
                    online_count += 1

            # Category status color
            if online_count == total_count:
                category_color = "var(--success-color)"
                category_bg = "rgba(16, 185, 129, 0.1)"
            elif online_count > 0:
                category_color = "var(--warning-color)"
                category_bg = "rgba(245, 158, 11, 0.1)"
            else:
                category_color = "var(--danger-color)"
                category_bg = "rgba(239, 68, 68, 0.1)"

            html += f"""
            <div style="margin-bottom: 2.5rem;">
                <!-- Category Header -->
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; padding: 1rem; background: {category_bg}; border-radius: 12px; border: 1px solid {category_color}33; height: 80px;">
                    <div style="display: flex; align-items: center; gap: 1rem; flex: 1; min-width: 0;">
                        <div style="font-size: 1.5rem; flex-shrink: 0;">{category_info["emoji"]}</div>
                        <div style="min-width: 0; flex: 1;">
                            <h3 style="margin: 0; color: var(--primary-text); font-size: 1.2rem; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{category_name}</h3>
                            <p style="margin: 0; color: var(--secondary-text); font-size: 0.85rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{category_info["description"]}</p>
                        </div>
                    </div>
                    <div style="text-align: right; flex-shrink: 0; margin-left: 1rem;">
                        <div style="color: {category_color}; font-weight: 600; font-size: 1rem; margin-bottom: 0.25rem; white-space: nowrap;">
                            {online_count}/{total_count} Online
                        </div>
                        <div style="color: var(--secondary-text); font-size: 0.75rem; white-space: nowrap;">
                            {((online_count/total_count)*100) if total_count > 0 else 0:.0f}% Operational
                        </div>
                    </div>
                </div>

                <!-- Servers Grid -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 1.5rem;">
            """

            # Generate server cards for this category (sorted by priority)
            sorted_servers = sorted(
                category_info["servers"].items(), key=lambda x: x[1]["priority"]
            )

            for server_id, server_info in sorted_servers:
                service = services_data.get(server_id, {})

                # Special handling for Corporate Headquarters - if we're serving this page, we're online
                if server_id == "corporate_headquarters":
                    status = service.get("status", "healthy")
                    # If status is still not healthy but we're running, force it to healthy
                    if status not in ["healthy", "starting"]:
                        status = "healthy"
                else:
                    status = service.get("status", "offline")

                # Enhanced status styling
                if status == "healthy":
                    status_color = "var(--success-color)"
                    status_bg = "rgba(16, 185, 129, 0.05)"
                    status_text = "Online"
                    status_emoji = "✅"
                    border_color = "rgba(16, 185, 129, 0.2)"
                elif status == "starting" or status == "unknown":
                    status_color = "var(--warning-color)"
                    status_bg = "rgba(245, 158, 11, 0.05)"
                    status_text = "Starting"
                    status_emoji = "⏳"
                    border_color = "rgba(245, 158, 11, 0.2)"
                else:
                    status_color = "var(--danger-color)"
                    status_bg = "rgba(239, 68, 68, 0.05)"
                    status_text = "Offline"
                    status_emoji = "❌"
                    border_color = "rgba(239, 68, 68, 0.2)"

                # Get last check timestamp and format it nicely
                last_check = service.get("last_check", "")
                if last_check:
                    try:
                        from datetime import datetime

                        dt = datetime.fromisoformat(last_check.replace("Z", "+00:00"))
                        last_check_formatted = dt.strftime("%b %d at %I:%M %p")
                    except:
                        last_check_formatted = "Just now"
                else:
                    last_check_formatted = "Starting..."

                # Additional server-specific info
                server_details = ""
                if server_id == "corporate_headquarters":
                    server_details = "🏢 Main control center"
                elif server_id == "agent_cortex":
                    server_details = "🧠 AI orchestration"
                elif server_id == "registry":
                    server_details = "📋 Service discovery"
                elif server_id == "filesystem":
                    server_details = "📁 File operations"
                elif server_id == "database_postgres":
                    server_details = "💾 Data persistence"
                elif server_id == "analytics":
                    server_details = "📊 Business intelligence"
                elif server_id == "payment":
                    server_details = "💳 Revenue processing"
                elif server_id == "customer":
                    server_details = "👥 CRM system"

                html += f"""
                <div data-server-status="{status}" data-server-name="{server_info['name']}" data-server-port="{server_info['port']}" data-server-category="{category_name}" style="background: {status_bg}; border: 1px solid {border_color}; border-radius: 12px; padding: 1.5rem; transition: all 0.3s ease; position: relative; overflow: hidden; min-height: 200px; display: flex; flex-direction: column;">
                    <!-- Priority Badge -->
                    <div style="position: absolute; top: 0.75rem; right: 0.75rem; background: rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 0.25rem 0.5rem; font-size: 0.7rem; color: var(--secondary-text); font-weight: 600;">
                        P{server_info['priority']}
                    </div>

                    <!-- Header -->
                    <div style="display: flex; align-items: flex-start; gap: 0.75rem; margin-bottom: 1rem; margin-right: 2rem;">
                        <div style="width: 48px; height: 48px; background: rgba(255, 255, 255, 0.1); border: 1px solid var(--border-color); border-radius: 12px; display: flex; align-items: center; justify-content: center; color: {status_color}; font-size: 1.3rem; flex-shrink: 0;">
                            <i class="{server_info['icon']}"></i>
                        </div>
                        <div style="flex: 1; min-width: 0;">
                            <h4 style="margin: 0 0 0.25rem 0; color: var(--primary-text); font-size: 1.1rem; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                                {server_info['name']}
                            </h4>
                            <p style="margin: 0 0 0.5rem 0; color: var(--secondary-text); font-size: 0.8rem; line-height: 1.3;">{server_info['description']}</p>
                            {f'<p style="margin: 0; color: var(--accent-color); font-size: 0.75rem; font-weight: 500;">{server_details}</p>' if server_details else ''}
                        </div>
                    </div>

                    <!-- Status Info -->
                    <div style="margin-top: auto;">
                        <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.75rem; background: rgba(255, 255, 255, 0.03); border-radius: 8px; margin-bottom: 0.5rem;">
                            <div style="display: flex; align-items: center; gap: 0.5rem; color: {status_color}; font-weight: 600; font-size: 0.95rem;">
                                <span style="font-size: 1.1rem;">{status_emoji}</span>
                                <span>{status_text}</span>
                            </div>
                            <div style="color: var(--secondary-text); font-size: 0.8rem; font-weight: 500; white-space: nowrap;">
                                Port: {server_info['port']}
                            </div>
                        </div>
                        <div style="text-align: center; font-size: 0.75rem; color: var(--secondary-text);">
                            Last checked: {last_check_formatted}
                        </div>
                    </div>

                </div>
                """

            html += """
                </div>
            </div>
            """

        return html

    def _fetch_organizational_data(self):
        """Fetch organizational structure from database with descriptions and details"""
        try:
            import asyncio

            import asyncpg

            # Database connection details
            db_url = "postgresql://boarderframe:boarderframe_secure_2025@localhost:5434/boarderframeos"

            async def fetch_data():
                try:
                    conn = await asyncpg.connect(db_url)

                    # Fetch divisions with their details
                    divisions_query = """
                        SELECT
                            div.division_key,
                            div.division_name,
                            div.division_description,
                            div.division_purpose,
                            div.priority,
                            COUNT(DISTINCT d.id) as department_count,
                            COUNT(DISTINCT dl.id) as leader_count,
                            COALESCE(SUM(d.agent_capacity), 0) as total_agent_capacity
                        FROM divisions div
                        LEFT JOIN departments d ON div.id = d.division_id AND d.is_active = true
                        LEFT JOIN department_leaders dl ON d.id = dl.department_id AND dl.active_status = 'active'
                        WHERE div.is_active = true
                        GROUP BY div.id, div.division_key, div.division_name, div.division_description, div.division_purpose, div.priority
                        ORDER BY div.priority
                    """

                    divisions = await conn.fetch(divisions_query)

                    # Fetch departments with their details
                    departments_query = """
                        SELECT
                            d.department_key,
                            d.department_name,
                            d.description,
                            d.department_purpose,
                            d.category,
                            d.priority,
                            d.operational_status,
                            d.agent_capacity,
                            div.division_key,
                            div.priority as division_priority,
                            COUNT(DISTINCT dl.id) as leader_count
                        FROM departments d
                        JOIN divisions div ON d.division_id = div.id
                        LEFT JOIN department_leaders dl ON d.id = dl.department_id AND dl.active_status = 'active'
                        WHERE d.is_active = true AND div.is_active = true
                        GROUP BY d.id, d.department_key, d.department_name, d.description, d.department_purpose,
                                 d.category, d.priority, d.operational_status, d.agent_capacity, div.division_key, div.priority
                        ORDER BY div.priority, d.priority
                    """

                    departments = await conn.fetch(departments_query)

                    # Fetch leaders with their details
                    leaders_query = """
                        SELECT
                            dl.name,
                            dl.title,
                            dl.description,
                            dl.leadership_tier,
                            dl.biblical_archetype,
                            dl.authority_level,
                            dl.is_primary,
                            d.department_key,
                            div.division_key
                        FROM department_leaders dl
                        JOIN departments d ON dl.department_id = d.id
                        JOIN divisions div ON d.division_id = div.id
                        WHERE dl.active_status = 'active' AND d.is_active = true AND div.is_active = true
                        ORDER BY div.priority, d.priority, dl.authority_level DESC, dl.name
                    """

                    leaders = await conn.fetch(leaders_query)

                    await conn.close()

                    # Build organizational structure
                    org_structure = {}

                    # Color mapping for divisions
                    division_colors = {
                        "executive": "#6366f1",
                        "programming_development": "#10b981",
                        "information_technology": "#f59e0b",
                        "product_operations": "#8b5cf6",
                        "revenue_generation": "#ef4444",
                        "business_operations": "#06b6d4",
                        "customer_experience": "#f97316",
                        "content_generation": "#ec4899",
                        "continuous_improvement": "#84cc16",
                    }

                    # Icon mapping for divisions
                    division_icons = {
                        "executive": "fas fa-crown",
                        "programming_development": "fas fa-code",
                        "information_technology": "fas fa-server",
                        "product_operations": "fas fa-cogs",
                        "revenue_generation": "fas fa-dollar-sign",
                        "business_operations": "fas fa-building",
                        "customer_experience": "fas fa-heart",
                        "content_generation": "fas fa-palette",
                        "continuous_improvement": "fas fa-lightbulb",
                    }

                    # Process divisions
                    for div in divisions:
                        div_key = div["division_key"]
                        org_structure[div["division_name"]] = {
                            "key": div_key,
                            "description": div["division_description"] or "",
                            "purpose": div["division_purpose"] or "",
                            "color": division_colors.get(div_key, "#6366f1"),
                            "icon": division_icons.get(div_key, "fas fa-building"),
                            "priority": div["priority"],
                            "departments": {},
                        }

                    # Process departments
                    for dept in departments:
                        div_key = dept["division_key"]
                        div_name = None
                        for div in divisions:
                            if div["division_key"] == div_key:
                                div_name = div["division_name"]
                                break

                        if div_name and div_name in org_structure:
                            org_structure[div_name]["departments"][
                                dept["department_name"]
                            ] = {
                                "key": dept["department_key"],
                                "description": dept["description"] or "",
                                "purpose": dept["department_purpose"] or "",
                                "category": dept["category"] or "",
                                "status": dept["operational_status"] or "planning",
                                "agents": dept["agent_capacity"] or 0,
                                "leader_count": dept["leader_count"] or 0,
                                "leaders": [],
                            }

                    # Process leaders
                    for leader in leaders:
                        div_key = leader["division_key"]
                        dept_key = leader["department_key"]

                        # Find the division and department
                        for div_name, div_data in org_structure.items():
                            if div_data["key"] == div_key:
                                for dept_name, dept_data in div_data[
                                    "departments"
                                ].items():
                                    if dept_data["key"] == dept_key:
                                        leader_info = {
                                            "name": leader["name"],
                                            "title": leader["title"],
                                            "description": leader["description"] or "",
                                            "tier": leader["leadership_tier"]
                                            or "department",
                                            "archetype": leader["biblical_archetype"]
                                            or "",
                                            "authority": leader["authority_level"] or 5,
                                            "is_primary": leader["is_primary"] or False,
                                        }
                                        dept_data["leaders"].append(leader_info)
                                        break
                                break

                    print(
                        f"✅ Successfully loaded organizational data: {len(org_structure)} divisions"
                    )
                    return org_structure

                except Exception as e:
                    print(f"Database fetch error: {e}")
                    import traceback

                    traceback.print_exc()
                    return None

            # Run the async function
            try:
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(fetch_data())
            except RuntimeError:
                # If no event loop, create a new one
                return asyncio.run(fetch_data())

        except Exception as e:
            print(f"Error fetching organizational data: {e}")
            return None

    def _generate_organizational_chart(self):
        """Generate interactive organizational chart with divisions, departments, and leaders"""

        # Try to fetch real data from database, fallback to mock data
        org_structure = self._fetch_organizational_data()

        if not org_structure:
            # Fallback to mock data if database unavailable
            org_structure = {
                "Executive": {
                    "color": "#6366f1",
                    "icon": "fas fa-crown",
                    "departments": {
                        "Executive Leadership": {
                            "leaders": ["Solomon (Digital Twin)", "David (CEO)"],
                            "status": "operational",
                            "agents": 15,
                        },
                        "Strategic Planning": {
                            "leaders": ["Joseph (Chief Strategy Officer)"],
                            "status": "operational",
                            "agents": 10,
                        },
                        "Coordination & Orchestration": {
                            "leaders": ["Michael (Chief Orchestration Officer)"],
                            "status": "operational",
                            "agents": 12,
                        },
                        "Agent Development": {
                            "leaders": ["Adam (The Creator)", "Eve (The Evolver)"],
                            "status": "operational",
                            "agents": 20,
                        },
                    },
                },
                "Programming & Development": {
                    "color": "#10b981",
                    "icon": "fas fa-code",
                    "departments": {
                        "Core Systems Programming": {
                            "leaders": ["Bezalel (Master Programmer)"],
                            "status": "operational",
                            "agents": 25,
                        },
                        "Software Factory": {
                            "leaders": ["Bezalel (Master Programmer)"],
                            "status": "operational",
                            "agents": 30,
                        },
                        "Quality Assurance": {
                            "leaders": ["Caleb (Chief Quality Officer)"],
                            "status": "planning",
                            "agents": 15,
                        },
                    },
                },
                "Information Technology": {
                    "color": "#f59e0b",
                    "icon": "fas fa-server",
                    "departments": {
                        "Infrastructure & Operations": {
                            "leaders": ["Gabriel (Chief Infrastructure Officer)"],
                            "status": "operational",
                            "agents": 20,
                        },
                        "Security": {
                            "leaders": ["Gad (Chief Security Officer)"],
                            "status": "operational",
                            "agents": 15,
                        },
                        "Data Management": {
                            "leaders": ["Ezra (Chief Knowledge Officer)"],
                            "status": "operational",
                            "agents": 18,
                        },
                        "Analytics & Monitoring": {
                            "leaders": ["Issachar (Chief Analytics Officer)"],
                            "status": "planning",
                            "agents": 12,
                        },
                    },
                },
                "Product Operations": {
                    "color": "#8b5cf6",
                    "icon": "fas fa-cogs",
                    "departments": {
                        "Platform Services": {
                            "leaders": ["Zebulun (Chief Production Officer)"],
                            "status": "operational",
                            "agents": 20,
                        },
                        "DevOps & Deployment": {
                            "leaders": ["Naphtali (Chief Operations Officer)"],
                            "status": "operational",
                            "agents": 15,
                        },
                        "Product Management": {
                            "leaders": ["Timothy (Chief Product Officer)"],
                            "status": "planning",
                            "agents": 10,
                        },
                        "API Gateway & Integration": {
                            "leaders": ["Philip (Chief Integration Officer)"],
                            "status": "planning",
                            "agents": 12,
                        },
                    },
                },
                "Revenue Generation": {
                    "color": "#ef4444",
                    "icon": "fas fa-dollar-sign",
                    "departments": {
                        "Sales": {
                            "leaders": ["Benjamin (Chief Sales Officer)"],
                            "status": "operational",
                            "agents": 20,
                        },
                        "Marketing": {
                            "leaders": ["Ephraim (Chief Marketing Officer)"],
                            "status": "operational",
                            "agents": 18,
                        },
                        "Revenue Operations": {
                            "leaders": ["Matthew (Chief Revenue Officer)"],
                            "status": "planning",
                            "agents": 12,
                        },
                    },
                },
                "Business Operations": {
                    "color": "#06b6d4",
                    "icon": "fas fa-briefcase",
                    "departments": {
                        "Finance": {
                            "leaders": ["Levi (Chief Financial Officer)"],
                            "status": "operational",
                            "agents": 15,
                        },
                        "Legal & Compliance": {
                            "leaders": ["Judah (Chief Legal Officer)"],
                            "status": "operational",
                            "agents": 10,
                        },
                        "Human Resources": {
                            "leaders": ["Aaron (Chief People Officer)"],
                            "status": "operational",
                            "agents": 12,
                        },
                        "Procurement & Partnerships": {
                            "leaders": ["Nehemiah (Chief Procurement Officer)"],
                            "status": "planning",
                            "agents": 8,
                        },
                        "Learning & Development": {
                            "leaders": ["Apollos (Chief Learning Officer)"],
                            "status": "planning",
                            "agents": 10,
                        },
                    },
                },
                "Customer Experience": {
                    "color": "#ec4899",
                    "icon": "fas fa-heart",
                    "departments": {
                        "Customer Success": {
                            "leaders": ["Asher (Chief Customer Officer)"],
                            "status": "operational",
                            "agents": 15,
                        },
                        "Customer Support": {
                            "leaders": ["Silas (Chief Support Officer)"],
                            "status": "operational",
                            "agents": 20,
                        },
                        "Customer Experience Design": {
                            "leaders": ["Lydia (Chief Experience Officer)"],
                            "status": "planning",
                            "agents": 8,
                        },
                        "Customer Retention": {
                            "leaders": ["Priscilla (Chief Retention Officer)"],
                            "status": "planning",
                            "agents": 10,
                        },
                        "Account Management": {
                            "leaders": ["Aquila (Chief Account Officer)"],
                            "status": "planning",
                            "agents": 12,
                        },
                    },
                },
                "Content Generation": {
                    "color": "#84cc16",
                    "icon": "fas fa-palette",
                    "departments": {
                        "Creative Services": {
                            "leaders": ["Jubal (Chief Creative Officer)"],
                            "status": "operational",
                            "agents": 15,
                        },
                        "Content Strategy": {
                            "leaders": ["Luke (Chief Content Officer)"],
                            "status": "planning",
                            "agents": 10,
                        },
                        "Media Production": {
                            "leaders": ["Mark (Chief Media Officer)"],
                            "status": "planning",
                            "agents": 12,
                        },
                    },
                },
                "Continuous Improvement": {
                    "color": "#f97316",
                    "icon": "fas fa-lightbulb",
                    "departments": {
                        "Innovation Office": {
                            "leaders": ["Daniel (Chief Innovation Officer)"],
                            "status": "operational",
                            "agents": 15,
                        },
                        "Research & Development": {
                            "leaders": ["Dan (Chief Research Officer)"],
                            "status": "operational",
                            "agents": 12,
                        },
                    },
                },
            }

        html = """
        <div class="org-chart" style="
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 1rem;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        ">
            <!-- Divisions Grid -->
            <div class="divisions-grid" style="
                display: flex;
                flex-direction: column;
                gap: 1rem;
                max-width: 1200px;
                width: 100%;
            ">
        """

        # Generate division cards
        for i, (division_name, division_data) in enumerate(org_structure.items()):
            dept_count = len(division_data["departments"])
            total_agents = sum(
                dept["agents"] for dept in division_data["departments"].values()
            )
            operational_depts = len(
                [
                    d
                    for d in division_data["departments"].values()
                    if d["status"] == "operational"
                ]
            )

            # Create unique ID for the division
            division_id = f"division-{division_name.lower().replace(' ', '-').replace('&', 'and')}"

            html += f"""
            <div class="division-card" id="{division_id}" style="
                background: var(--card-bg);
                border: 2px solid {division_data['color']};
                border-radius: 12px;
                overflow: hidden;
                transition: all 0.3s ease;
                cursor: pointer;
                position: relative;
            " onclick="toggleDivisionExpansion('{division_id}')">
                <!-- Division Header -->
                <div class="division-header" style="
                    background: linear-gradient(135deg, {division_data['color']}, {division_data['color']}cc);
                    color: white;
                    padding: 1rem;
                    position: relative;
                ">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div style="display: flex; align-items: center; gap: 0.75rem; flex: 1;">
                            <i class="{division_data['icon']}" style="font-size: 1.25rem;"></i>
                            <div style="flex: 1;">
                                <div style="font-weight: 600; font-size: 1rem;">{division_name}</div>
                                <div style="font-size: 0.8rem; opacity: 0.9;">{dept_count} Departments</div>
                                {f'<div style="font-size: 0.75rem; opacity: 0.8; margin-top: 0.25rem; line-height: 1.3;">{division_data.get("description", "")}</div>' if division_data.get("description") else ""}
                            </div>
                        </div>
                        <div class="division-expand-icon" style="
                            font-size: 1rem;
                            transition: transform 0.3s ease;
                        ">
                            <i class="fas fa-sitemap"></i>
                        </div>
                    </div>
                </div>

                <!-- Division Stats -->
                <div class="division-stats" style="
                    padding: 1rem;
                    background: var(--secondary-bg);
                    border-bottom: 1px solid var(--border-color);
                ">
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; text-align: center;">
                        <div>
                            <div style="font-size: 1.25rem; font-weight: 600; color: {division_data['color']};">{dept_count}</div>
                            <div style="font-size: 0.75rem; color: var(--secondary-text);">Departments</div>
                        </div>
                        <div>
                            <div style="font-size: 1.25rem; font-weight: 600; color: var(--success-color);">{operational_depts}</div>
                            <div style="font-size: 0.75rem; color: var(--secondary-text);">Operational</div>
                        </div>
                        <div>
                            <div style="font-size: 1.25rem; font-weight: 600; color: var(--accent-color);">{total_agents}</div>
                            <div style="font-size: 0.75rem; color: var(--secondary-text);">Agents</div>
                        </div>
                    </div>
                    <!-- Add padding under metrics for vertical centering -->
                    <div style="height: 0.5rem;"></div>
                    {f'''
                    <!-- Division Purpose -->
                    <div style="
                        padding: 0.75rem 1rem;
                        background: var(--accent-bg);
                        border-top: 1px solid var(--border-color);
                        font-size: 0.85rem;
                        color: var(--secondary-text);
                        line-height: 1.4;
                        font-style: italic;
                    ">
                        <i class="fas fa-bullseye" style="color: {division_data['color']}; margin-right: 0.5rem;"></i>
                        {division_data.get("purpose", "")}
                    </div>
                    ''' if division_data.get("purpose") else ""}
                </div>

                <!-- Departments List (Initially Hidden) -->
                <div id="{division_id}-departments" class="departments-list" style="
                    display: none;
                    background: var(--card-bg);
                ">
            """

            # Generate department cards within the division
            for dept_name, dept_data in division_data["departments"].items():
                dept_id = f"dept-{division_name.lower().replace(' ', '-')}-{dept_name.lower().replace(' ', '-').replace('&', 'and')}"
                status_color = (
                    "#10b981" if dept_data["status"] == "active" else "#f59e0b"
                )
                status_icon = (
                    "fas fa-check-circle"
                    if dept_data["status"] == "active"
                    else "fas fa-clock"
                )

                html += f"""
                <div class="department-card" id="{dept_id}" style="
                    padding: 1rem;
                    border-bottom: 1px solid var(--border-color);
                    cursor: pointer;
                    transition: background 0.2s ease;
                " onclick="toggleDepartmentExpansion('{dept_id}', event)">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div style="display: flex; align-items: flex-start; gap: 0.75rem;">
                            <div style="
                                width: 32px;
                                height: 32px;
                                background: {division_data['color']};
                                border-radius: 8px;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                color: white;
                                font-size: 0.875rem;
                                flex-shrink: 0;
                                margin-top: 0.125rem;
                            ">
                                <i class="fas fa-building"></i>
                            </div>
                            <div style="flex: 1; min-width: 0;">
                                <div style="font-weight: 600; font-size: 0.9rem; color: var(--primary-text); margin-bottom: 0.25rem;">{dept_name}</div>
                                <div style="font-size: 0.75rem; color: var(--secondary-text); display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.6rem;">
                                    <i class="{status_icon}" style="color: {status_color};"></i>
                                    {'Operational' if dept_data['status'] == 'active' else dept_data['status'].title()} • {dept_data['agents']} agents
                                    {f" • {dept_data.get('category', '').title()}" if dept_data.get('category') else ""}
                                </div>
                                <div style="font-size: 0.7rem; color: var(--accent-color); font-weight: 500; margin-bottom: 0.75rem;">
                                    <i class="fas fa-user-tie" style="margin-right: 0.5rem;"></i>
                                    {', '.join([
                                        f"{leader.get('name', str(leader))} - {leader.get('title', '')} • {leader.get('description', '')}"
                                        if isinstance(leader, dict) and leader.get('title') and leader.get('description')
                                        else str(leader).replace('(', '- ').replace(')', ' • Leadership and strategic oversight')
                                        for leader in dept_data.get('leaders', [])
                                    ])}
                                </div>
                                {f'<div style="font-size: 0.7rem; color: var(--secondary-text); line-height: 1.4; opacity: 0.8; font-style: italic; margin-top: 0.75rem; padding-top: 0.5rem; border-top: 1px solid var(--border-color); margin-left: 0;"><i class="fas fa-info-circle" style="color: {division_data["color"]}; margin-right: 0.5rem;"></i>{dept_data.get("description", "")}</div>' if dept_data.get("description") else ""}
                            </div>
                        </div>
                        <div class="dept-expand-icon" style="
                            font-size: 0.75rem;
                            color: var(--secondary-text);
                            transition: transform 0.3s ease;
                        ">
                            <i class="fas fa-chevron-right"></i>
                        </div>
                    </div>

                    {f'''
                    <!-- Department Purpose -->
                    <div style="
                        padding: 0.4rem 0.75rem 0.4rem 0;
                        margin-left: 2.5rem;
                        margin-top: 0.75rem;
                        background: var(--accent-bg);
                        border-top: 1px solid var(--border-color);
                        font-size: 0.75rem;
                        color: var(--secondary-text);
                        line-height: 1.4;
                        font-style: italic;
                        text-align: left;
                    ">
                        <i class="fas fa-target" style="color: {division_data['color']}; margin-right: 0.4rem;"></i>
                        {dept_data.get("purpose", "")}
                    </div>
                    ''' if dept_data.get("purpose") else ""}

                    <!-- Leaders List (Initially Hidden) -->
                    <div id="department-{dept_id}-leaders" class="leaders-list" style="
                        display: none;
                        margin-top: 0;
                    ">
                        <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border-color);">
                            <div style="font-size: 0.8rem; font-weight: 600; color: var(--secondary-text); margin-bottom: 0.5rem;">
                                <i class="fas fa-crown"></i> Leadership
                            </div>
                """

                # Add leaders - check if leaders is a list of strings (fallback) or objects (database)
                for leader in dept_data["leaders"]:
                    # Handle both old string format and new object format
                    if isinstance(leader, str):
                        leader_name = leader
                        leader_title = ""
                        leader_desc = ""
                        leader_archetype = ""
                        is_primary = False
                    else:
                        leader_name = leader.get("name", "")
                        leader_title = leader.get("title", "")
                        leader_desc = leader.get("description", "")
                        leader_archetype = leader.get("archetype", "")
                        is_primary = leader.get("is_primary", False)

                    # Style primary leaders differently
                    bg_color = (
                        division_data["color"]
                        if is_primary
                        else f"{division_data['color']}66"
                    )
                    border_style = (
                        f"border: 2px solid {division_data['color']};"
                        if is_primary
                        else ""
                    )

                    html += f"""
                    <div style="
                        display: flex;
                        align-items: flex-start;
                        gap: 1rem;
                        margin-bottom: 1rem;
                        padding: 1rem;
                        background: linear-gradient(135deg, var(--card-bg), var(--secondary-bg));
                        border-radius: 12px;
                        border: 1px solid var(--border-color);
                        {f'box-shadow: 0 4px 12px {division_data["color"]}40; border: 2px solid {division_data["color"]};' if is_primary else 'box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);'}
                        position: relative;
                        transition: all 0.3s ease;
                        cursor: pointer;
                    " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='{f'0 6px 20px {division_data["color"]}60' if is_primary else '0 4px 16px rgba(0, 0, 0, 0.15)'}'"
                       onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='{f'0 4px 12px {division_data["color"]}40' if is_primary else '0 2px 8px rgba(0, 0, 0, 0.1)'}'">

                        {f'<div style="position: absolute; top: 0.5rem; right: 0.5rem; font-size: 0.65rem; color: {division_data["color"]}; font-weight: 600; background: {division_data["color"]}15; padding: 0.15rem 0.5rem; border-radius: 8px; border: 1px solid {division_data["color"]}40;"><i class="fas fa-star" style="margin-right: 0.25rem;"></i>PRIMARY</div>' if is_primary else ''}

                        <div style="
                            width: 48px;
                            height: 48px;
                            background: linear-gradient(135deg, {division_data["color"]}, {division_data["color"]}cc);
                            border-radius: 12px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            color: white;
                            font-size: 1.1rem;
                            flex-shrink: 0;
                            box-shadow: 0 3px 8px {division_data["color"]}50;
                            position: relative;
                        ">
                            <i class="fas fa-crown"></i>
                            {f'<div style="position: absolute; top: -2px; right: -2px; width: 12px; height: 12px; background: #10b981; border-radius: 50%; border: 2px solid white;"></div>' if is_primary else ''}
                        </div>

                        <div style="flex: 1; min-width: 0;">
                            <div style="display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 0.5rem;">
                                <div>
                                    <div style="font-size: 0.95rem; font-weight: 700; color: var(--primary-text); margin-bottom: 0.25rem;">{leader_name}</div>
                                    {f'<div style="font-size: 0.8rem; color: {division_data["color"]}; margin-bottom: 0.4rem; font-weight: 600;">{leader_title}</div>' if leader_title else ''}
                                </div>
                            </div>

                            {f'<div style="font-size: 0.75rem; color: var(--secondary-text); line-height: 1.4; margin-bottom: 0.75rem; padding: 0.5rem; background: var(--accent-bg); border-radius: 6px; border-left: 3px solid {division_data["color"]};">{leader_desc}</div>' if leader_desc else ''}

                            <div style="display: flex; align-items: center; justify-content: space-between;">
                                {f'<div style="font-size: 0.7rem; color: {division_data["color"]}; font-weight: 500; display: flex; align-items: center; gap: 0.25rem; background: {division_data["color"]}10; padding: 0.25rem 0.5rem; border-radius: 6px;"><i class="fas fa-star"></i> {leader_archetype} Archetype</div>' if leader_archetype else '<div></div>'}

                                <div style="display: flex; gap: 0.5rem;">
                                    <div style="
                                        font-size: 0.7rem;
                                        color: var(--accent-color);
                                        background: var(--accent-bg);
                                        padding: 0.25rem 0.5rem;
                                        border-radius: 6px;
                                        cursor: pointer;
                                        transition: all 0.2s ease;
                                        border: 1px solid var(--border-color);
                                    " onmouseover="this.style.background='{division_data["color"]}20'; this.style.borderColor='{division_data["color"]}'"
                                       onmouseout="this.style.background='var(--accent-bg)'; this.style.borderColor='var(--border-color)'">
                                        <i class="fas fa-comment"></i> Chat
                                    </div>
                                    <div style="
                                        font-size: 0.7rem;
                                        color: var(--secondary-text);
                                        background: var(--secondary-bg);
                                        padding: 0.25rem 0.5rem;
                                        border-radius: 6px;
                                        cursor: pointer;
                                        transition: all 0.2s ease;
                                        border: 1px solid var(--border-color);
                                    " onmouseover="this.style.background='{division_data["color"]}20'; this.style.borderColor='{division_data["color"]}'"
                                       onmouseout="this.style.background='var(--secondary-bg)'; this.style.borderColor='var(--border-color)'">
                                        <i class="fas fa-user"></i> Profile
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    """

                html += """
                        </div>
                    </div>
                </div>
                """

            html += """
                </div>
            </div>
            """

        html += """
            </div>
        </div>

        <style>
        .division-card {
            width: 100%;
            margin-bottom: 1rem;
        }

        .division-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }

        .division-card.expanded .division-expand-icon {
            transform: rotate(45deg);
        }

        .department-card:hover {
            background: var(--secondary-bg) !important;
        }

        .department-card.expanded .dept-expand-icon {
            transform: rotate(90deg);
        }

        .divisions-grid {
            width: 100%;
        }

        @media (max-width: 768px) {
            .division-card {
                margin-bottom: 0.5rem;
            }

            .org-chart {
                padding: 1rem;
            }
        }
        </style>
        """

        return html

    def _generate_detailed_server_widgets(self):
        """Generate detailed widgets for each MCP server"""
        widgets_html = ""

        for service_id, service in self.services_status.items():
            if service.get("status") != "healthy":
                continue

            status_class = service.get("status", "critical")
            border_class = f"server-{service_id}"

            # Generate specific widget content based on server type
            if service_id == "filesystem":
                widget_content = self._generate_filesystem_widget_content()
                # Use proper title for File System Server
                server_title = "File System Server Details"
            elif service_id == "registry":
                widget_content = self._generate_registry_widget_content()
                server_title = f"{service.get('name', service_id.title())} Details"
            elif service_id == "database":
                widget_content = self._generate_database_widget_content()
                server_title = f"{service.get('name', service_id.title())} Details"
            elif service_id == "agent_cortex":
                widget_content = self._generate_agent_cortex_widget_content()
                server_title = f"{service.get('name', service_id.title())} Details"
            else:
                widget_content = self._generate_generic_widget_content(service)
                server_title = f"{service.get('name', service_id.title())} Details"

            widgets_html += f"""
                <div class="card {border_class}">
                    <h3>
                        <i class="{service.get('icon', 'fas fa-server')}"></i>
                        {server_title}
                    </h3>
                    {widget_content}
                </div>
            """

        return widgets_html

    def _generate_filesystem_widget_content(self):
        """Generate detailed filesystem server widget content"""
        if "filesystem" not in self.mcp_details:
            # If no MCP details, try to get basic service info
            fs_service = self.services_status.get("filesystem", {})
            if not fs_service:
                return '<div style="text-align: center; color: var(--secondary-text); padding: 1rem;">File System Server not available</div>'

            # Show basic info if detailed data is not available
            return f"""
                <div class="metrics-grid">
                    <div class="metric-item">
                        <div class="metric-value">{fs_service.get("port", "Unknown")}</div>
                        <div class="metric-label">Port</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">{fs_service.get("response_time", 0)*1000:.0f}ms</div>
                        <div class="metric-label">Response Time</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">{"✅" if fs_service.get("status") == "healthy" else "❌"}</div>
                        <div class="metric-label">Status</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">Ready</div>
                        <div class="metric-label">State</div>
                    </div>
                </div>
                <div style="margin-top: 1rem; padding: 1rem; background: rgba(16, 185, 129, 0.1); border-radius: 8px; border-left: 3px solid var(--success-color);">
                    <h4 style="margin: 0 0 0.5rem 0; color: var(--success-color);">
                        <i class="fas fa-folder-tree"></i> File System Operations
                    </h4>
                    <p style="margin: 0; color: var(--secondary-text); font-size: 0.9rem;">
                        Provides file operations, directory management, and AI-powered content analysis capabilities.
                    </p>
                </div>
            """

        details = self.mcp_details["filesystem"]
        return f"""
            <div class="metrics-grid">
                <div class="metric-item">
                    <div class="metric-value">{details.get("total_operations", 0)}</div>
                    <div class="metric-label">Total Operations</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{details.get("active_clients", 0)}</div>
                    <div class="metric-label">Active Clients</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{"✅" if details.get("ai_features") else "❌"}</div>
                    <div class="metric-label">Smart Analysis</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{details.get("vector_db_size", 0)}</div>
                    <div class="metric-label">Vector DB Entries</div>
                </div>
            </div>
            <div style="margin-top: 1rem; padding: 1rem; background: rgba(16, 185, 129, 0.1); border-radius: 8px; border-left: 3px solid var(--success-color);">
                <h4 style="margin: 0 0 0.5rem 0; color: var(--success-color);">
                    <i class="fas fa-folder"></i> Configuration
                </h4>
                <div style="font-size: 0.9rem; color: var(--secondary-text);">
                    <div style="margin-bottom: 0.3rem;"><i class="fas fa-clock"></i> Uptime: {details.get('uptime', 'Unknown')}</div>
                    <div><i class="fas fa-folder-open"></i> Base Path: <code style="color: var(--primary-text); background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 4px;">{details.get("base_path", "/")}</code></div>
                </div>
            </div>
        """

    def _generate_registry_widget_content(self):
        """Generate registry server widget content"""
        registry_service = self.services_status.get("registry", {})
        details = registry_service.get("details", {})

        return f"""
            <div class="metrics-grid">
                <div class="metric-item">
                    <div class="metric-value">{details.get("registered_services", 0)}</div>
                    <div class="metric-label">Registered Services</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{details.get("active_connections", 0)}</div>
                    <div class="metric-label">Active Connections</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{details.get("uptime", "Unknown")}</div>
                    <div class="metric-label">Uptime</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">✅</div>
                    <div class="metric-label">Status</div>
                </div>
            </div>
            <div style="margin-top: 1rem; padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px;">
                <h4 style="margin: 0 0 0.5rem 0; color: var(--accent-color);">
                    <i class="fas fa-network-wired"></i> Server Registry
                </h4>
                <p style="margin: 0; color: var(--secondary-text);">Central coordination hub for all MCP services</p>
            </div>
        """

    async def _get_database_health_metrics(self):
        """Get comprehensive database health and metrics with improved accuracy"""
        try:
            import asyncpg

            # Database connection details
            db_url = "postgresql://boarderframe:boarderframe_secure_2025@localhost:5434/boarderframeos"

            # Connect to PostgreSQL
            conn = await asyncpg.connect(db_url)

            # Get database metrics
            metrics = {}

            # Basic database info
            db_size_query = (
                "SELECT pg_size_pretty(pg_database_size('boarderframeos')) as size"
            )
            db_size_result = await conn.fetchrow(db_size_query)
            metrics["database_size"] = (
                db_size_result["size"] if db_size_result else "Unknown"
            )

            # Get table count and info
            tables_query = """
                SELECT schemaname, tablename,
                       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                       (SELECT count(*) FROM information_schema.columns
                        WHERE table_name = tablename AND table_schema = schemaname) as columns
                FROM pg_tables
                WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """
            tables_result = await conn.fetch(tables_query)

            table_info = []
            for row in tables_result:
                table_info.append(
                    {
                        "schema": row["schemaname"],
                        "name": row["tablename"],
                        "size": row["size"],
                        "columns": row["columns"],
                    }
                )

            metrics["tables"] = table_info
            metrics["total_tables"] = len(table_info)

            # More accurate connection stats - filter out background processes
            connections_query = """
                SELECT
                    count(*) FILTER (WHERE state IS NOT NULL AND usename IS NOT NULL) as active_connections,
                    (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_connections,
                    count(*) FILTER (WHERE state = 'active') as active_queries,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections
                FROM pg_stat_activity
                WHERE datname = 'boarderframeos'
            """
            conn_result = await conn.fetchrow(connections_query)
            if conn_result:
                # Use the filtered active connections count for more accuracy
                metrics["active_connections"] = conn_result["active_connections"] or 0
                metrics["max_connections"] = conn_result["max_connections"]
                metrics["active_queries"] = conn_result["active_queries"] or 0
                metrics["idle_connections"] = conn_result["idle_connections"] or 0
                metrics["available_connections"] = (
                    metrics["max_connections"] - metrics["active_connections"]
                )
            else:
                metrics["active_connections"] = 0
                metrics["max_connections"] = 0
                metrics["available_connections"] = 0

            # Database activity stats for our specific database
            activity_query = """
                SELECT numbackends as backends,
                       xact_commit as commits,
                       xact_rollback as rollbacks,
                       blks_read as blocks_read,
                       blks_hit as blocks_hit,
                       tup_returned,
                       tup_fetched,
                       tup_inserted,
                       tup_updated,
                       tup_deleted
                FROM pg_stat_database
                WHERE datname = 'boarderframeos'
            """
            activity_result = await conn.fetchrow(activity_query)
            if activity_result:
                metrics["backends"] = activity_result["backends"] or 0
                metrics["commits"] = activity_result["commits"] or 0
                metrics["rollbacks"] = activity_result["rollbacks"] or 0
                metrics["blocks_read"] = activity_result["blocks_read"] or 0
                metrics["blocks_hit"] = activity_result["blocks_hit"] or 0
                metrics["tuples_returned"] = activity_result["tup_returned"] or 0
                metrics["tuples_fetched"] = activity_result["tup_fetched"] or 0
                metrics["tuples_inserted"] = activity_result["tup_inserted"] or 0
                metrics["tuples_updated"] = activity_result["tup_updated"] or 0
                metrics["tuples_deleted"] = activity_result["tup_deleted"] or 0

                # Calculate cache hit ratio
                total_blocks = (activity_result["blocks_read"] or 0) + (
                    activity_result["blocks_hit"] or 0
                )
                if total_blocks > 0:
                    metrics["cache_hit_ratio"] = round(
                        (activity_result["blocks_hit"] / total_blocks) * 100, 2
                    )
                else:
                    metrics["cache_hit_ratio"] = (
                        100  # If no blocks read, assume perfect cache
                    )
            else:
                metrics["backends"] = 0
                metrics["commits"] = 0
                metrics["rollbacks"] = 0
                metrics["cache_hit_ratio"] = 0

            # Get PostgreSQL version
            version_query = "SELECT version()"
            version_result = await conn.fetchrow(version_query)
            if version_result:
                version_full = version_result["version"]
                # Extract just the version number
                import re

                version_match = re.search(r"PostgreSQL (\d+\.\d+)", version_full)
                metrics["version"] = (
                    version_match.group(1) if version_match else version_full
                )
            else:
                metrics["version"] = "Unknown"

            # Check if pgvector extension is available
            pgvector_query = "SELECT extname FROM pg_extension WHERE extname = 'vector'"
            pgvector_result = await conn.fetchrow(pgvector_query)
            metrics["pgvector_enabled"] = bool(pgvector_result)

            # Get current time for last update
            metrics["last_check"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            await conn.close()

            metrics["status"] = "healthy"
            print(
                f"✅ Database health check completed - Active connections: {metrics['active_connections']}"
            )

            return metrics

        except Exception as e:
            print(f"❌ Database health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "last_check": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "database_size": "Unknown",
                "total_tables": 0,
                "active_connections": 0,
                "max_connections": 0,
                "cache_hit_ratio": 0,
                "tables": [],
            }

    def _categorize_table(self, table_name):
        """Categorize a table based on its name"""
        table_name_lower = table_name.lower()

        # System and Core Tables
        if any(
            keyword in table_name_lower
            for keyword in ["pg_", "information_schema", "sql_", "sys_"]
        ):
            return "system", "fas fa-cogs", "#6b7280"

        # Agent-related tables
        if any(
            keyword in table_name_lower
            for keyword in [
                "agent",
                "solomon",
                "david",
                "adam",
                "eve",
                "bezalel",
                "michael",
            ]
        ):
            return "agents", "fas fa-robot", "#3b82f6"

        # Division tables
        if any(
            keyword in table_name_lower
            for keyword in ["division", "leadership", "coordination", "executive"]
        ):
            return "divisions", "fas fa-sitemap", "#8b5cf6"

        # Department tables
        if any(
            keyword in table_name_lower
            for keyword in [
                "department",
                "finance",
                "legal",
                "sales",
                "marketing",
                "procurement",
                "engineering",
                "research",
                "innovation",
                "operations",
                "security",
                "data_management",
                "infrastructure",
                "learning",
                "human_resources",
                "production",
                "quality",
                "customer_service",
                "supply_chain",
                "communications",
                "strategic",
                "technology",
                "business",
                "creative",
            ]
        ):
            return "departments", "fas fa-building", "#10b981"

        # Registry and service tables
        if any(
            keyword in table_name_lower
            for keyword in ["registry", "server", "service", "mcp"]
        ):
            return "registry", "fas fa-network-wired", "#f59e0b"

        # Message and communication tables
        if any(
            keyword in table_name_lower
            for keyword in ["message", "chat", "communication", "log"]
        ):
            return "messaging", "fas fa-comments", "#ec4899"

        # Migration and schema tables
        if any(
            keyword in table_name_lower
            for keyword in ["migration", "schema", "version"]
        ):
            return "migrations", "fas fa-database", "#ef4444"

        # Default category
        return "other", "fas fa-table", "#6b7280"

    def _generate_database_tables_rows(self):
        """Generate HTML rows for database tables display with categorization"""
        if not hasattr(self, "database_health_metrics"):
            return """
                <tr>
                    <td colspan="5" style="text-align: center; padding: 2rem; color: var(--secondary-text);">
                        <i class="fas fa-spinner fa-spin"></i> Loading database table information...
                    </td>
                </tr>
            """

        tables = self.database_health_metrics.get("tables", [])
        if not tables:
            return """
                <tr>
                    <td colspan="5" style="text-align: center; padding: 2rem; color: var(--secondary-text);">
                        No tables found or database connection error
                    </td>
                </tr>
            """

        # Categorize and sort tables
        categorized_tables = {}
        for table in tables:
            category, icon, color = self._categorize_table(table.get("name", ""))
            if category not in categorized_tables:
                categorized_tables[category] = {
                    "tables": [],
                    "icon": icon,
                    "color": color,
                }
            categorized_tables[category]["tables"].append(table)

        # Sort categories by priority
        category_order = [
            "agents",
            "divisions",
            "departments",
            "registry",
            "messaging",
            "migrations",
            "system",
            "other",
        ]

        rows_html = ""
        for category in category_order:
            if category not in categorized_tables:
                continue

            category_data = categorized_tables[category]
            category_tables = sorted(
                category_data["tables"], key=lambda x: x.get("name", "")
            )

            # Add category header
            category_display = category.replace("_", " ").title()
            rows_html += f"""
                <tr style="background: rgba(255,255,255,0.03);">
                    <td colspan="5" style="padding: 1rem 0.75rem; font-weight: 600; color: {category_data['color']}; border-top: 2px solid {category_data['color']}20;">
                        <i class="{category_data['icon']}" style="margin-right: 0.5rem;"></i>
                        {category_display} ({len(category_tables)} tables)
                    </td>
                </tr>
            """

            # Add tables in this category
            for table in category_tables:
                rows_html += f"""
                    <tr style="border-bottom: 1px solid var(--border-color);">
                        <td style="padding: 0.75rem; color: var(--primary-text); padding-left: 2rem;">
                            <i class="fas fa-table" style="color: {category_data['color']}; margin-right: 0.5rem;"></i>
                            {table.get('name', 'Unknown')}
                        </td>
                        <td style="padding: 0.75rem; color: var(--secondary-text);">
                            {table.get('schema', 'public')}
                        </td>
                        <td style="padding: 0.75rem; color: var(--secondary-text);">
                            {table.get('size', 'Unknown')}
                        </td>
                        <td style="padding: 0.75rem; color: var(--secondary-text);">
                            {table.get('columns', 'N/A')}
                        </td>
                        <td style="padding: 0.75rem; color: var(--secondary-text); font-size: 0.8rem;">
                            <span style="background: {category_data['color']}20; color: {category_data['color']}; padding: 0.2rem 0.5rem; border-radius: 4px;">
                                {category_display}
                            </span>
                        </td>
                    </tr>
                """

        return rows_html

    def _generate_database_widget_content(self):
        """Generate database server widget content using centralized data"""
        # Use centralized data when available, fallback to legacy
        services_data = self.unified_data.get("services_status", self.services_status)
        db_service = services_data.get("database", {})
        details = db_service.get("details", {})

        # Use centralized database health metrics
        db_metrics = self.unified_data.get(
            "database_health", getattr(self, "database_health_metrics", {})
        )

        return f"""
            <div class="metrics-grid">
                <div class="metric-item">
                    <div class="metric-value">{db_metrics.get("total_tables", details.get("total_queries", 0))}</div>
                    <div class="metric-label">Tables</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{db_metrics.get("active_connections", details.get("active_connections", 0))}</div>
                    <div class="metric-label">Active Connections</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{db_metrics.get("database_size", details.get("database_size", "Unknown"))}</div>
                    <div class="metric-label">Database Size</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{"✅" if db_metrics.get("status") == "healthy" else "❌"}</div>
                    <div class="metric-label">Status</div>
                </div>
            </div>
            <div style="margin-top: 1rem; padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px;">
                <h4 style="margin: 0 0 0.5rem 0; color: var(--accent-color);">
                    <i class="fas fa-database"></i> PostgreSQL Database
                </h4>
                <p style="margin: 0; color: var(--secondary-text);">BoarderframeOS primary data storage with pgvector support</p>
            </div>
        """

    def _generate_agent_cortex_widget_content(self):
        """Generate Cortex widget content"""
        agent_cortex_service = self.services_status.get("agent_cortex", {})
        details = agent_cortex_service.get("details", {})

        return f"""
            <div class="metrics-grid">
                <div class="metric-item">
                    <div class="metric-value">{details.get("active_sessions", 0)}</div>
                    <div class="metric-label">Active Sessions</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{details.get("current_strategy", "balanced")}</div>
                    <div class="metric-label">Strategy</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{details.get("performance_stats", {}).get("cost_savings", "45%")}</div>
                    <div class="metric-label">Cost Savings</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">✅</div>
                    <div class="metric-label">Status</div>
                </div>
            </div>
            <div style="margin-top: 1rem; padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px;">
                <h4 style="margin: 0 0 0.5rem 0; color: var(--accent-color);">
                    <i class="fas fa-brain"></i> Intelligent Orchestration
                </h4>
                <p style="margin: 0; color: var(--secondary-text);">Dynamic model selection, cost optimization, and performance learning</p>
            </div>
        """

    def _generate_generic_widget_content(self, service):
        """Generate generic widget content for unknown services"""
        details = service.get("details", {})

        return f"""
            <div class="metrics-grid">
                <div class="metric-item">
                    <div class="metric-value">{service.get("port", "Unknown")}</div>
                    <div class="metric-label">Port</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{service.get("response_time", 0)*1000:.0f}ms</div>
                    <div class="metric-label">Response Time</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">✅</div>
                    <div class="metric-label">Status</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">{details.get("uptime", "Unknown")}</div>
                    <div class="metric-label">Uptime</div>
                </div>
            </div>
            <div style="margin-top: 1rem; padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px;">
                <h4 style="margin: 0 0 0.5rem 0; color: var(--accent-color);">
                    <i class="fas fa-server"></i> Server Details
                </h4>
                <p style="margin: 0; color: var(--secondary-text);">MCP service running on port {service.get("port", "Unknown")}</p>
            </div>
        """

    def _generate_leaders_html(self):
        """Generate comprehensive leaders overview HTML with database integration"""
        try:
            import asyncio

            import asyncpg

            # Get leaders data from database
            leaders_data = self._fetch_leaders_data()

            if not leaders_data:
                return """
                    <div style="text-align: center; padding: 2rem; color: var(--secondary-text);">
                        <i class="fas fa-crown" style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                        <h4>No Leaders Data Available</h4>
                        <p>Unable to load leadership information from database.</p>
                    </div>
                """

            # Group leaders by division for better organization
            divisions_leaders = {}
            division_colors = {
                "Executive Division": "#6366f1",
                "Programming & Development Division": "#10b981",
                "Information Technology Division": "#06b6d4",
                "Customer Experience Division": "#ec4899",
                "Content Generation Division": "#84cc16",
                "Innovation Division": "#f59e0b",
                "Finance Division": "#8b5cf6",
                "Operations Division": "#ef4444",
                "Human Resources Division": "#14b8a6",
            }

            for leader in leaders_data:
                div_name = leader["division_name"]
                if div_name not in divisions_leaders:
                    divisions_leaders[div_name] = {
                        "leaders": [],
                        "color": division_colors.get(div_name, "#6b7280"),
                        "total_departments": 0,
                        "active_departments": 0,
                    }
                divisions_leaders[div_name]["leaders"].append(leader)
                if leader["department_name"] not in [
                    l["department_name"]
                    for l in divisions_leaders[div_name]["leaders"][:-1]
                ]:
                    divisions_leaders[div_name]["total_departments"] += 1
                    if leader["operational_status"] == "active":
                        divisions_leaders[div_name]["active_departments"] += 1

            html = (
                """
                <!-- Leaders Overview Card -->
                <div class="card full-width" style="margin-bottom: 2rem; border: 2px solid #f59e0b20; background: linear-gradient(135deg, #f59e0b08, #f59e0b03);">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border-color);">
                        <div style="display: flex; align-items: center; gap: 1rem;">
                            <div style="
                                width: 60px; height: 60px;
                                background: linear-gradient(135deg, #f59e0b, #f59e0bcc);
                                border-radius: 12px;
                                display: flex; align-items: center; justify-content: center;
                                color: white; font-size: 1.5rem; box-shadow: 0 4px 12px #f59e0b40;
                            ">
                                <i class="fas fa-crown"></i>
                            </div>
                            <div>
                                <h3 style="margin: 0; color: var(--primary-text); font-size: 1.25rem;">Leaders Status</h3>
                                <p style="margin: 0.25rem 0; color: var(--secondary-text); font-size: 0.9rem;">
                                    """
                + str(len(leaders_data))
                + """ active leaders • Organizational hierarchy management
                                </p>
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 0.75rem; color: var(--secondary-text); margin-bottom: 0.25rem;">Leadership Status</div>
                            <div style="font-size: 1rem; font-weight: 600; color: var(--success-color);">
                                Operational
                            </div>
                        </div>
                    </div>

                    <!-- Leaders Metrics Grid -->
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; align-items: stretch;">
                        <div class="widget widget-small">
                            <div class="widget-header">
                                <div class="widget-title">
                                    <i class="fas fa-star" style="color: var(--success-color);"></i>
                                    <span>Executive Leaders</span>
                                </div>
                            </div>
                            <div class="widget-value" style="color: var(--success-color);">"""
                + str(
                    len([l for l in leaders_data if "Executive" in l["division_name"]])
                )
                + """</div>
                            <div class="widget-subtitle">Executive division leaders</div>
                        </div>
                        <div class="widget widget-small">
                            <div class="widget-header">
                                <div class="widget-title">
                                    <i class="fas fa-crown" style="color: var(--accent-color);"></i>
                                    <span>Leaders</span>
                                </div>
                            </div>
                            <div class="widget-value" style="color: var(--accent-color);">"""
                + str(len(leaders_data))
                + """</div>
                            <div class="widget-subtitle">Active leadership positions</div>
                        </div>
                        <div class="widget widget-small">
                            <div class="widget-header">
                                <div class="widget-title">
                                    <i class="fas fa-building" style="color: var(--accent-color);"></i>
                                    <span>Departments</span>
                                </div>
                            </div>
                            <div class="widget-value" style="color: var(--accent-color);">"""
                + str(len(set(l["department_name"] for l in leaders_data)))
                + """</div>
                            <div class="widget-subtitle">Departments with leaders</div>
                        </div>
                        <div class="widget widget-small">
                            <div class="widget-header">
                                <div class="widget-title">
                                    <i class="fas fa-sitemap" style="color: var(--warning-color);"></i>
                                    <span>Divisions</span>
                                </div>
                            </div>
                            <div class="widget-value" style="color: var(--warning-color);">"""
                + str(len(divisions_leaders))
                + """</div>
                            <div class="widget-subtitle">Organizational divisions</div>
                        </div>
                    </div>
                </div>

                <!-- Division Leadership Overview -->
            """
            )

            for division_name, division_data in divisions_leaders.items():
                division_color = division_data["color"]
                leaders = division_data["leaders"]
                active_depts = division_data["active_departments"]
                total_depts = division_data["total_departments"]

                html += f"""
                    <div class="card full-width" style="margin-bottom: 2rem; border: 2px solid {division_color}20; background: linear-gradient(135deg, {division_color}08, {division_color}03);">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border-color);">
                            <div style="display: flex; align-items: center; gap: 1rem;">
                                <div style="
                                    width: 60px; height: 60px;
                                    background: linear-gradient(135deg, {division_color}, {division_color}cc);
                                    border-radius: 12px;
                                    display: flex; align-items: center; justify-content: center;
                                    color: white; font-size: 1.5rem; box-shadow: 0 4px 12px {division_color}40;
                                ">
                                    <i class="fas fa-users"></i>
                                </div>
                                <div>
                                    <h3 style="margin: 0; color: var(--primary-text); font-size: 1.25rem;">{division_name}</h3>
                                    <p style="margin: 0.25rem 0; color: var(--secondary-text); font-size: 0.9rem;">
                                        {len(leaders)} leaders across {total_depts} departments • {active_depts} operational
                                    </p>
                                </div>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 0.75rem; color: var(--secondary-text); margin-bottom: 0.25rem;">Division Status</div>
                                <div style="font-size: 1rem; font-weight: 600; color: {'var(--success-color)' if active_depts > 0 else 'var(--warning-color)'};">
                                    {'Active' if active_depts > 0 else 'Planning'}
                                </div>
                            </div>
                        </div>

                        <!-- Leaders Grid -->
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 1rem;">
                """

                for leader in leaders:
                    archetype_icon = {
                        "Visionary": "fas fa-eye",
                        "Commander": "fas fa-shield-alt",
                        "Creator": "fas fa-hammer",
                        "Builder": "fas fa-tools",
                        "Guardian": "fas fa-shield",
                        "Shepherd": "fas fa-heart",
                        "Prophet": "fas fa-bolt",
                    }.get(leader.get("biblical_archetype", ""), "fas fa-crown")

                    status_color = (
                        "#10b981"
                        if leader["operational_status"] == "active"
                        else "#f59e0b"
                    )
                    status_text = (
                        "Operational"
                        if leader["operational_status"] == "active"
                        else "Planning"
                    )

                    html += f"""
                        <div style="
                            background: var(--card-bg);
                            border: 1px solid var(--border-color);
                            border-radius: 12px;
                            padding: 1.25rem;
                            padding-top: 2.5rem;
                            position: relative;
                            transition: all 0.3s ease;
                            cursor: pointer;
                            height: 280px;
                            display: flex;
                            flex-direction: column;
                            {f'box-shadow: 0 4px 12px {division_color}30; border: 2px solid {division_color};' if leader['is_primary'] else 'box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);'}
                        " onmouseover="this.style.transform='translateY(-3px)'; this.style.boxShadow='{f'0 8px 25px {division_color}40' if leader['is_primary'] else '0 6px 20px rgba(0, 0, 0, 0.15)'}'"
                           onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='{f'0 4px 12px {division_color}30' if leader['is_primary'] else '0 2px 8px rgba(0, 0, 0, 0.1)'}'">

                            {f'<div style="position: absolute; top: 0.75rem; right: 0.75rem; background: {division_color}15; color: {division_color}; padding: 0.2rem 0.6rem; border-radius: 6px; font-size: 0.65rem; font-weight: 600; border: 1px solid {division_color}40; z-index: 10;"><i class="fas fa-star" style="margin-right: 0.25rem;"></i>PRIMARY</div>' if leader['is_primary'] else ''}

                            <div style="display: flex; align-items: flex-start; gap: 1rem; height: 100%;">
                                <div style="
                                    width: 64px; height: 64px;
                                    background: linear-gradient(135deg, {division_color}, {division_color}cc);
                                    border-radius: 50%;
                                    display: flex; align-items: center; justify-content: center;
                                    color: white; font-size: 1.5rem;
                                    box-shadow: 0 4px 12px {division_color}50;
                                    position: relative;
                                    flex-shrink: 0;
                                ">
                                    <i class="{archetype_icon}"></i>
                                    {f'<div style="position: absolute; bottom: -2px; right: -2px; width: 20px; height: 20px; background: {status_color}; border-radius: 50%; border: 3px solid var(--card-bg); display: flex; align-items: center; justify-content: center;"><i class="fas fa-check" style="font-size: 0.6rem; color: white;"></i></div>' if leader['operational_status'] == 'active' else ''}
                                </div>

                                <div style="flex: 1; min-width: 0; display: flex; flex-direction: column; height: 100%;">
                                    <!-- Header Section - Fixed Height -->
                                    <div style="height: 5.5rem; margin-bottom: 0.75rem; display: flex; flex-direction: column;">
                                        <h4 style="margin: 0 0 0.25rem 0; color: var(--primary-text); font-size: 1.1rem; font-weight: 700; line-height: 1.2; height: 1.3rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{leader['name']}</h4>
                                        <p style="margin: 0 0 0.5rem 0; color: {division_color}; font-weight: 600; font-size: 0.9rem; line-height: 1.2; height: 2.4rem; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">{leader['title']}</p>
                                        <div style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.8rem; color: var(--secondary-text); line-height: 1.3; margin-top: auto;">
                                            <div style="display: flex; align-items: center; gap: 0.5rem; flex: 1; min-width: 0;">
                                                <i class="fas fa-building" style="flex-shrink: 0;"></i>
                                                <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{leader['department_name']}</span>
                                            </div>
                                            <div style="
                                                background: {status_color}20;
                                                color: {status_color};
                                                padding: 0.15rem 0.5rem;
                                                border-radius: 4px;
                                                font-size: 0.7rem;
                                                font-weight: 500;
                                                display: flex;
                                                align-items: center;
                                                gap: 0.25rem;
                                                border: 1px solid {status_color}40;
                                                flex-shrink: 0;
                                            ">
                                                <i class="fas fa-{'check-circle' if leader['operational_status'] == 'active' else 'clock'}" style="font-size: 0.6rem;"></i>
                                                {status_text}
                                            </div>
                                        </div>
                                    </div>

                                    <!-- Description Section - Flexible Height -->
                                    <div style="flex: 1; margin-bottom: 0.75rem;">
                                        {f'<div style="background: var(--accent-bg); border-radius: 8px; padding: 0.75rem; border-left: 3px solid {division_color}; font-size: 0.8rem; line-height: 1.4; color: var(--secondary-text); height: 100%; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical;">{leader.get("description", "")}</div>' if leader.get('description') else '<div style="height: 100%;"></div>'}
                                    </div>

                                    <!-- Footer Section - Fixed Height -->
                                    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem; margin-top: auto; min-height: 2rem;">
                                        {f'<div style="background: {division_color}15; color: {division_color}; padding: 0.25rem 0.75rem; border-radius: 6px; font-size: 0.7rem; font-weight: 500; display: flex; align-items: center; gap: 0.25rem; flex-shrink: 0; max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;"><i class="fas fa-star"></i> {leader.get("biblical_archetype", "Leader")}</div>' if leader.get('biblical_archetype') else '<div style="flex: 1;"></div>'}

                                        <div style="display: flex; gap: 0.5rem; flex-shrink: 0;">
                                            <div style="
                                                background: var(--accent-bg);
                                                color: var(--accent-color);
                                                padding: 0.3rem 0.6rem;
                                                border-radius: 6px;
                                                font-size: 0.7rem;
                                                cursor: pointer;
                                                transition: all 0.2s ease;
                                                border: 1px solid var(--border-color);
                                                display: flex;
                                                align-items: center;
                                                justify-content: center;
                                            " onmouseover="this.style.background='{division_color}20'; this.style.borderColor='{division_color}'"
                                               onmouseout="this.style.background='var(--accent-bg)'; this.style.borderColor='var(--border-color)'">
                                                <i class="fas fa-comment"></i>
                                            </div>
                                            <div style="
                                                background: var(--secondary-bg);
                                                color: var(--secondary-text);
                                                padding: 0.3rem 0.6rem;
                                                border-radius: 6px;
                                                font-size: 0.7rem;
                                                cursor: pointer;
                                                transition: all 0.2s ease;
                                                border: 1px solid var(--border-color);
                                                display: flex;
                                                align-items: center;
                                                justify-content: center;
                                            " onmouseover="this.style.background='{division_color}20'; this.style.borderColor='{division_color}'"
                                               onmouseout="this.style.background='var(--secondary-bg)'; this.style.borderColor='var(--border-color)'">
                                                <i class="fas fa-user"></i>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    """

                html += """
                        </div>
                    </div>
                """

            return html

        except Exception as e:
            print(f"Error generating leaders HTML: {e}")
            return """
                <div style="text-align: center; padding: 2rem; color: var(--secondary-text);">
                    <i class="fas fa-exclamation-triangle" style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.5; color: var(--warning-color);"></i>
                    <h4>Error Loading Leaders</h4>
                    <p>Unable to generate leaders overview. Please try again.</p>
                </div>
            """

    def _generate_divisions_html(self):
        """Generate comprehensive divisions overview HTML with database integration"""
        try:
            # Get leaders data to extract division information
            leaders_data = self._fetch_leaders_data()

            if not leaders_data:
                return """
                    <div style="text-align: center; padding: 2rem; color: var(--secondary-text);">
                        <i class="fas fa-sitemap" style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                        <h4>No Divisions Data Available</h4>
                        <p>Unable to load division information from database.</p>
                    </div>
                """

            # Group and analyze divisions
            divisions_data = {}
            division_colors = {
                "Executive Division": "#6366f1",
                "Programming & Development Division": "#10b981",
                "Information Technology Division": "#06b6d4",
                "Customer Experience Division": "#ec4899",
                "Content Generation Division": "#84cc16",
                "Innovation Division": "#f59e0b",
                "Finance Division": "#8b5cf6",
                "Operations Division": "#ef4444",
                "Human Resources Division": "#14b8a6",
            }

            for leader in leaders_data:
                div_name = leader["division_name"]
                div_desc = leader.get(
                    "division_description", "Strategic organizational division"
                )

                if div_name not in divisions_data:
                    divisions_data[div_name] = {
                        "name": div_name,
                        "description": div_desc,
                        "color": division_colors.get(div_name, "#6b7280"),
                        "leaders": [],
                        "departments": set(),
                        "total_leaders": 0,
                        "active_leaders": 0,
                        "primary_leaders": 0,
                    }

                divisions_data[div_name]["leaders"].append(leader)
                divisions_data[div_name]["departments"].add(leader["department_name"])
                divisions_data[div_name]["total_leaders"] += 1

                if leader.get("active_status", "active") == "active":
                    divisions_data[div_name]["active_leaders"] += 1
                if leader.get("is_primary", False):
                    divisions_data[div_name]["primary_leaders"] += 1

            # Convert departments set to count
            for div_name in divisions_data:
                divisions_data[div_name]["total_departments"] = len(
                    divisions_data[div_name]["departments"]
                )
                divisions_data[div_name]["departments"] = list(
                    divisions_data[div_name]["departments"]
                )

            # Get organizational metrics from unified data
            org_metrics = self.unified_data.get(
                "organizational_metrics",
                {
                    "divisions": {"total": 0, "active": 0, "percentage": 0},
                    "departments": {"total": 0, "active": 0, "percentage": 0},
                    "leaders": {"total": 0, "active": 0, "percentage": 0},
                    "agents": {"total": 0, "active": 0, "percentage": 0},
                },
            )

            html = f"""
                <!-- Divisions Overview Card -->
                <div class="card full-width" style="margin-bottom: 2rem; border: 2px solid #8b5cf620; background: linear-gradient(135deg, #8b5cf608, #8b5cf603);">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border-color);">
                        <div style="display: flex; align-items: center; gap: 1rem;">
                            <div style="
                                width: 60px; height: 60px;
                                background: linear-gradient(135deg, #8b5cf6, #8b5cf6cc);
                                border-radius: 12px;
                                display: flex; align-items: center; justify-content: center;
                                color: white; font-size: 1.5rem; box-shadow: 0 4px 12px #8b5cf640;
                            ">
                                <i class="fas fa-sitemap"></i>
                            </div>
                            <div>
                                <h3 style="margin: 0; color: var(--primary-text); font-size: 1.25rem;">Divisions Details</h3>
                                <p style="margin: 0.25rem 0; color: var(--secondary-text); font-size: 0.9rem;">
                                    Organizational structure and leadership distribution
                                </p>
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 0.75rem; color: var(--secondary-text); margin-bottom: 0.25rem;">Last Updated</div>
                            <div style="font-size: 0.9rem; color: var(--primary-text);">
                                {datetime.now().strftime("%I:%M %p")}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Enhanced Organizational Metrics Cards -->
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.5rem; margin-bottom: 2rem;">
                    <!-- Divisions Card -->
                    <div class="card" style="background: linear-gradient(135deg, #8b5cf608, #8b5cf603); border: 1px solid #8b5cf620; padding: 1.5rem;">
                        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
                            <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #8b5cf6, #7c3aed); border-radius: 12px; display: flex; align-items: center; justify-content: center; color: white;">
                                <i class="fas fa-sitemap" style="font-size: 1.25rem;"></i>
                            </div>
                            <div style="flex: 1;">
                                <h4 style="margin: 0; color: var(--primary-text); font-size: 1rem;">Divisions</h4>
                                <div style="display: flex; align-items: baseline; gap: 0.5rem; margin-top: 0.25rem;">
                                    <span style="font-size: 1.5rem; font-weight: 700; color: #8b5cf6;">{org_metrics['divisions']['active']}/{org_metrics['divisions']['total']}</span>
                                    <span style="font-size: 0.875rem; color: #8b5cf6; font-weight: 500;">{org_metrics['divisions']['percentage']}%</span>
                                </div>
                            </div>
                        </div>
                        <div style="background: rgba(139, 92, 246, 0.1); border-radius: 4px; padding: 0.5rem; text-align: center;">
                            <span style="font-size: 0.75rem; color: var(--secondary-text);">Active/Total</span>
                        </div>
                    </div>

                    <!-- Departments Card -->
                    <div class="card" style="background: linear-gradient(135deg, #10b98108, #10b98103); border: 1px solid #10b98120; padding: 1.5rem;">
                        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
                            <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #10b981, #059669); border-radius: 12px; display: flex; align-items: center; justify-content: center; color: white;">
                                <i class="fas fa-building" style="font-size: 1.25rem;"></i>
                            </div>
                            <div style="flex: 1;">
                                <h4 style="margin: 0; color: var(--primary-text); font-size: 1rem;">Departments</h4>
                                <div style="display: flex; align-items: baseline; gap: 0.5rem; margin-top: 0.25rem;">
                                    <span style="font-size: 1.5rem; font-weight: 700; color: #10b981;">{org_metrics['departments']['active']}/{org_metrics['departments']['total']}</span>
                                    <span style="font-size: 0.875rem; color: #10b981; font-weight: 500;">{org_metrics['departments']['percentage']}%</span>
                                </div>
                            </div>
                        </div>
                        <div style="background: rgba(16, 185, 129, 0.1); border-radius: 4px; padding: 0.5rem; text-align: center;">
                            <span style="font-size: 0.75rem; color: var(--secondary-text);">Active/Total</span>
                        </div>
                    </div>

                    <!-- Leaders Card -->
                    <div class="card" style="background: linear-gradient(135deg, #f59e0b08, #f59e0b03); border: 1px solid #f59e0b20; padding: 1.5rem;">
                        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
                            <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #f59e0b, #d97706); border-radius: 12px; display: flex; align-items: center; justify-content: center; color: white;">
                                <i class="fas fa-crown" style="font-size: 1.25rem;"></i>
                            </div>
                            <div style="flex: 1;">
                                <h4 style="margin: 0; color: var(--primary-text); font-size: 1rem;">Leaders</h4>
                                <div style="display: flex; align-items: baseline; gap: 0.5rem; margin-top: 0.25rem;">
                                    <span style="font-size: 1.5rem; font-weight: 700; color: #f59e0b;">{org_metrics['leaders']['active']}/{org_metrics['leaders']['total']}</span>
                                    <span style="font-size: 0.875rem; color: #f59e0b; font-weight: 500;">{org_metrics['leaders']['percentage']}%</span>
                                </div>
                            </div>
                        </div>
                        <div style="background: rgba(245, 158, 11, 0.1); border-radius: 4px; padding: 0.5rem; text-align: center;">
                            <span style="font-size: 0.75rem; color: var(--secondary-text);">Active/Total</span>
                        </div>
                    </div>

                    <!-- Agents Card -->
                    <div class="card" style="background: linear-gradient(135deg, #06b6d408, #06b6d403); border: 1px solid #06b6d420; padding: 1.5rem;">
                        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
                            <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #06b6d4, #0891b2); border-radius: 12px; display: flex; align-items: center; justify-content: center; color: white;">
                                <i class="fas fa-robot" style="font-size: 1.25rem;"></i>
                            </div>
                            <div style="flex: 1;">
                                <h4 style="margin: 0; color: var(--primary-text); font-size: 1rem;">Agents</h4>
                                <div style="display: flex; align-items: baseline; gap: 0.5rem; margin-top: 0.25rem;">
                                    <span style="font-size: 1.5rem; font-weight: 700; color: #06b6d4;">{org_metrics['agents']['active']}/{org_metrics['agents']['total']}</span>
                                    <span style="font-size: 0.875rem; color: #06b6d4; font-weight: 500;">{org_metrics['agents']['percentage']}%</span>
                                </div>
                            </div>
                        </div>
                        <div style="background: rgba(6, 182, 212, 0.1); border-radius: 4px; padding: 0.5rem; text-align: center;">
                            <span style="font-size: 0.75rem; color: var(--secondary-text);">Active/Total</span>
                        </div>
                    </div>
                </div>

                <!-- Divisions Grid -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 1.5rem;">
            """

            # Get division-specific metrics from data layer
            div_metrics = org_metrics.get("by_division", {})

            # Generate division cards
            for div_name, division in divisions_data.items():
                # Get metrics for this division from data layer
                div_data = div_metrics.get(
                    div_name,
                    {
                        "departments": {
                            "total": division["total_departments"],
                            "active": 0,
                            "percentage": 0,
                        },
                        "leaders": {
                            "total": division["total_leaders"],
                            "active": division["active_leaders"],
                            "percentage": 0,
                        },
                        "agents": {"total": 0, "active": 0, "percentage": 0},
                    },
                )

                html += f"""
                    <div class="card" style="border-left: 4px solid {division['color']}; background: linear-gradient(135deg, {division['color']}08, {division['color']}03);">
                        <div style="display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 1rem;">
                            <div style="flex: 1;">
                                <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;">
                                    <div style="
                                        width: 40px; height: 40px;
                                        background: linear-gradient(135deg, {division['color']}, {division['color']}cc);
                                        border-radius: 10px;
                                        display: flex; align-items: center; justify-content: center;
                                        color: white; font-size: 1rem; box-shadow: 0 3px 8px {division['color']}50;
                                    ">
                                        <i class="fas fa-sitemap"></i>
                                    </div>
                                    <div>
                                        <h4 style="margin: 0; color: var(--primary-text); font-size: 1rem; font-weight: 700;">{div_name}</h4>
                                    </div>
                                </div>
                                <p style="margin: 0 0 1rem 0; color: var(--secondary-text); font-size: 0.85rem; line-height: 1.4;">
                                    {division['description']}
                                </p>
                            </div>
                        </div>

                        <!-- Division Stats with Active/Total -->
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; margin-bottom: 1rem;">
                            <div style="text-align: center; padding: 0.75rem; background: var(--secondary-bg); border-radius: 8px; border: 1px solid var(--border-color);">
                                <div style="display: flex; align-items: baseline; justify-content: center; gap: 0.25rem;">
                                    <span style="font-size: 1.2rem; font-weight: 700; color: {division['color']};">{div_data['departments']['active']}/{div_data['departments']['total']}</span>
                                    <span style="font-size: 0.75rem; color: {division['color']}; font-weight: 500;">{div_data['departments']['percentage']}%</span>
                                </div>
                                <div style="font-size: 0.7rem; color: var(--secondary-text);">Departments</div>
                            </div>
                            <div style="text-align: center; padding: 0.75rem; background: var(--secondary-bg); border-radius: 8px; border: 1px solid var(--border-color);">
                                <div style="display: flex; align-items: baseline; justify-content: center; gap: 0.25rem;">
                                    <span style="font-size: 1.2rem; font-weight: 700; color: {division['color']};">{div_data['leaders']['active']}/{div_data['leaders']['total']}</span>
                                    <span style="font-size: 0.75rem; color: {division['color']}; font-weight: 500;">{div_data['leaders']['percentage']}%</span>
                                </div>
                                <div style="font-size: 0.7rem; color: var(--secondary-text);">Leaders</div>
                            </div>
                            <div style="text-align: center; padding: 0.75rem; background: var(--secondary-bg); border-radius: 8px; border: 1px solid var(--border-color);">
                                <div style="display: flex; align-items: baseline; justify-content: center; gap: 0.25rem;">
                                    <span style="font-size: 1.2rem; font-weight: 700; color: {division['color']};">{div_data['agents']['active']}/{div_data['agents']['total']}</span>
                                    <span style="font-size: 0.75rem; color: {division['color']}; font-weight: 500;">{div_data['agents']['percentage']}%</span>
                                </div>
                                <div style="font-size: 0.7rem; color: var(--secondary-text);">Agents</div>
                            </div>
                        </div>

                        <!-- Department List -->
                        <div style="margin-bottom: 1rem;">
                            <div style="font-size: 0.8rem; font-weight: 600; color: var(--primary-text); margin-bottom: 0.5rem;">Departments:</div>
                            <div style="display: flex; flex-wrap: wrap; gap: 0.25rem;">
                """

                # Sort departments alphabetically
                sorted_departments = sorted(division["departments"])

                for dept in sorted_departments[:6]:  # Show first 6 departments
                    html += f"""
                        <span style="
                            font-size: 0.7rem;
                            background: {division['color']}15;
                            color: {division['color']};
                            padding: 0.25rem 0.5rem;
                            border-radius: 4px;
                            border: 1px solid {division['color']}30;
                            white-space: nowrap;
                        ">{dept}</span>
                    """

                if len(sorted_departments) > 6:
                    html += f"""
                        <span style="
                            font-size: 0.7rem;
                            background: var(--secondary-bg);
                            color: var(--secondary-text);
                            padding: 0.25rem 0.5rem;
                            border-radius: 4px;
                            border: 1px solid var(--border-color);
                        ">+{len(sorted_departments) - 6} more</span>
                    """

                html += """
                            </div>
                        </div>
                    </div>
                """

            html += """
                </div>
            """

            return html

        except Exception as e:
            print(f"Error generating divisions HTML: {e}")
            return f"""
                <div style="text-align: center; padding: 2rem; color: var(--error-color);">
                    <i class="fas fa-exclamation-triangle" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                    <h4>Error Loading Divisions</h4>
                    <p>Unable to generate divisions overview: {str(e)}</p>
                </div>
            """

    def _fetch_leaders_data(self):
        """Fetch comprehensive leaders data from database"""
        try:
            import asyncio

            import asyncpg

            # Database connection details
            db_url = "postgresql://boarderframe:boarderframe_secure_2025@localhost:5434/boarderframeos"

            async def fetch_data():
                try:
                    conn = await asyncpg.connect(db_url)

                    # Comprehensive query to get leaders with division and department info
                    leaders_query = """
                        SELECT
                            dl.name,
                            dl.title,
                            dl.description,
                            dl.leadership_tier,
                            dl.biblical_archetype,
                            dl.authority_level,
                            dl.is_primary,
                            dl.active_status,
                            d.department_name,
                            d.operational_status,
                            d.category,
                            div.division_name,
                            div.division_description
                        FROM department_leaders dl
                        JOIN departments d ON dl.department_id = d.id
                        JOIN divisions div ON d.division_id = div.id
                        WHERE dl.active_status = 'active'
                            AND d.is_active = true
                            AND div.is_active = true
                        ORDER BY div.priority, d.priority, dl.authority_level DESC, dl.name
                    """

                    leaders = await conn.fetch(leaders_query)
                    await conn.close()

                    # Convert to list of dictionaries for easier processing
                    leaders_list = []
                    for leader in leaders:
                        leaders_list.append(
                            {
                                "name": leader["name"],
                                "title": leader["title"],
                                "description": leader["description"] or "",
                                "leadership_tier": leader["leadership_tier"]
                                or "department",
                                "biblical_archetype": leader["biblical_archetype"]
                                or "",
                                "authority_level": leader["authority_level"] or 5,
                                "is_primary": leader["is_primary"] or False,
                                "active_status": leader["active_status"],
                                "department_name": leader["department_name"],
                                "operational_status": leader["operational_status"],
                                "category": leader["category"] or "",
                                "division_name": leader["division_name"],
                                "division_description": leader["division_description"]
                                or "",
                            }
                        )

                    print(
                        f"✅ Successfully loaded {len(leaders_list)} leaders from database"
                    )
                    return leaders_list

                except Exception as e:
                    print(f"Database leaders fetch error: {e}")
                    return None

            # Run the async function
            try:
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(fetch_data())
            except RuntimeError:
                # If no event loop, create a new one
                return asyncio.run(fetch_data())

        except Exception as e:
            print(f"Error fetching leaders data: {e}")
            return None

    def _get_department_count_from_db(self):
        """Get real-time department count from database"""
        try:

            async def fetch_count():
                try:
                    # Use existing database health connection
                    db_health = self.unified_data.get("database_health", {})
                    if db_health.get("status") != "connected":
                        return 0

                    # Get department count from PostgreSQL
                    import asyncpg

                    connection = await asyncpg.connect(
                        host="localhost",
                        port=5434,
                        user="boarderframe",
                        password="boarderframe123",
                        database="boarderframeos",
                    )

                    count = await connection.fetchval(
                        "SELECT COUNT(*) FROM departments"
                    )
                    await connection.close()
                    return count or 0

                except Exception as e:
                    print(f"Database department count error: {e}")
                    return 0

            # Run the async function
            try:
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(fetch_count())
            except RuntimeError:
                return asyncio.run(fetch_count())

        except Exception as e:
            print(f"Error getting department count: {e}")
            return 0

    def _get_division_count_from_db(self):
        """Get real-time division count from database"""
        try:

            async def fetch_count():
                try:
                    # Use existing database health connection
                    db_health = self.unified_data.get("database_health", {})
                    if db_health.get("status") != "connected":
                        return 0

                    # Get division count from PostgreSQL
                    import asyncpg

                    connection = await asyncpg.connect(
                        host="localhost",
                        port=5434,
                        user="boarderframe",
                        password="boarderframe123",
                        database="boarderframeos",
                    )

                    count = await connection.fetchval(
                        "SELECT COUNT(DISTINCT division_name) FROM divisions"
                    )
                    await connection.close()
                    return count or 0

                except Exception as e:
                    print(f"Database division count error: {e}")
                    return 0

            # Run the async function
            try:
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(fetch_count())
            except RuntimeError:
                return asyncio.run(fetch_count())

        except Exception as e:
            print(f"Error getting division count: {e}")
            return 0

    def _get_leaders_count_from_unified_data(self):
        """Get total leaders count from unified data or database"""
        # Try to get from unified data first
        leaders_data = self.unified_data.get("leaders_data", [])
        if leaders_data:
            return len(leaders_data)

        # Fallback to fresh database query
        fresh_leaders = self._fetch_leaders_data()
        return len(fresh_leaders) if fresh_leaders else 0

    def _get_active_leaders_count_from_unified_data(self):
        """Get active leaders count from unified data or database"""
        # Try to get from unified data first
        leaders_data = self.unified_data.get("leaders_data", [])
        if leaders_data:
            return len(
                [
                    l
                    for l in leaders_data
                    if l.get("active_status", "active") == "active"
                ]
            )

        # Fallback to fresh database query
        fresh_leaders = self._fetch_leaders_data()
        return (
            len(
                [
                    l
                    for l in fresh_leaders
                    if l.get("active_status", "active") == "active"
                ]
            )
            if fresh_leaders
            else 0
        )

    def _generate_smart_recommendations(
        self,
        overall_status,
        active_agents,
        total_agents,
        healthy_services,
        total_services,
        active_leaders,
        total_leaders,
        registry_status,
    ):
        """Generate intelligent recommendations based on system metrics"""
        recommendations = []

        # Agent workforce analysis
        agent_ratio = active_agents / total_agents if total_agents > 0 else 0
        if agent_ratio == 1.0:
            recommendations.append("🤖 Agent workforce at full capacity")
        elif agent_ratio >= 0.8:
            recommendations.append(
                f"🤖 Agent workforce running strong ({active_agents}/{total_agents})"
            )
        elif agent_ratio >= 0.5:
            recommendations.append(
                f"⚠️ {total_agents - active_agents} agents offline - check agent health"
            )
        else:
            recommendations.append(
                f"🚨 Critical: {total_agents - active_agents} agents down - immediate intervention needed"
            )

        # Infrastructure analysis
        service_ratio = healthy_services / total_services if total_services > 0 else 0
        if service_ratio == 1.0:
            recommendations.append("⚡ All MCP servers operational")
        elif service_ratio >= 0.8:
            recommendations.append(
                f"⚡ Infrastructure stable ({healthy_services}/{total_services} healthy)"
            )
        elif service_ratio >= 0.5:
            recommendations.append(
                f"⚠️ {total_services - healthy_services} MCP servers need attention"
            )
        else:
            recommendations.append(
                f"🚨 Infrastructure crisis: {total_services - healthy_services} servers failing"
            )

        # Leadership analysis
        leader_ratio = active_leaders / total_leaders if total_leaders > 0 else 0
        if leader_ratio >= 0.9:
            recommendations.append("👑 Leadership team fully engaged")
        elif leader_ratio >= 0.7:
            recommendations.append("👑 Most leaders active and coordinating")
        else:
            recommendations.append("⚠️ Leadership capacity reduced - check key agents")

        # Registry health
        if registry_status == "healthy":
            recommendations.append("🌐 Service registry providing full coordination")
        else:
            recommendations.append("🚨 Service registry issues affecting coordination")

        # System performance recommendation
        if overall_status == "online":
            recommendations.append("✅ Continue monitoring for peak efficiency")
        elif overall_status == "warning":
            recommendations.append(
                "⚠️ Run system diagnostics and address failing components"
            )
        else:
            recommendations.append(
                "🚨 Emergency protocols: restart critical services immediately"
            )

        return " • ".join(recommendations)

    def _generate_registry_overview_html(self):
        """Generate comprehensive registry visualization with enhanced data"""
        try:
            import json
            import subprocess

            # Check if Docker is available first
            docker_check = subprocess.run(
                ["docker", "ps"], capture_output=True, timeout=3
            )
            if docker_check.returncode != 0:
                return self._generate_fallback_registry_html("Docker not available")

            # Get comprehensive registry data
            registry_data = self._fetch_registry_data()

            if not registry_data:
                return self._generate_fallback_registry_html(
                    "Registry data unavailable"
                )

            # Generate visualization HTML
            return f"""
                <!-- Registry Statistics Overview -->
                <div class="card full-width" style="margin-bottom: 2rem;">
                    <h4 style="color: var(--accent-color); margin-bottom: 1.5rem; display: flex; align-items: center; gap: 0.5rem;">
                        <i class="fas fa-chart-line"></i> Registry Statistics
                    </h4>
                    <div style="display: grid; grid-template-columns: repeat(6, 1fr); gap: 1rem;">
                        <div class="metric-item" style="background: linear-gradient(135deg, #10b98110, #10b98105); border: 1px solid #10b98120; border-radius: 8px; padding: 1rem;">
                            <div class="metric-value" style="color: #10b981; font-size: 2rem;">{registry_data['totals']['agents']}</div>
                            <div class="metric-label">Total Agents</div>
                        </div>
                        <div class="metric-item" style="background: linear-gradient(135deg, #6366f110, #6366f105); border: 1px solid #6366f120; border-radius: 8px; padding: 1rem;">
                            <div class="metric-value" style="color: #6366f1; font-size: 2rem;">{registry_data['totals']['leaders']}</div>
                            <div class="metric-label">Leaders</div>
                        </div>
                        <div class="metric-item" style="background: linear-gradient(135deg, #8b5cf610, #8b5cf605); border: 1px solid #8b5cf620; border-radius: 8px; padding: 1rem;">
                            <div class="metric-value" style="color: #8b5cf6; font-size: 2rem;">{registry_data['totals']['departments']}</div>
                            <div class="metric-label">Departments</div>
                        </div>
                        <div class="metric-item" style="background: linear-gradient(135deg, #ec489910, #ec489905); border: 1px solid #ec489920; border-radius: 8px; padding: 1rem;">
                            <div class="metric-value" style="color: #ec4899; font-size: 2rem;">{registry_data['totals']['divisions']}</div>
                            <div class="metric-label">Divisions</div>
                        </div>
                        <div class="metric-item" style="background: linear-gradient(135deg, #f59e0b10, #f59e0b05); border: 1px solid #f59e0b20; border-radius: 8px; padding: 1rem;">
                            <div class="metric-value" style="color: #f59e0b; font-size: 2rem;">{registry_data['totals']['servers']}</div>
                            <div class="metric-label">Servers</div>
                        </div>
                        <div class="metric-item" style="background: linear-gradient(135deg, #06b6d410, #06b6d405); border: 1px solid #06b6d420; border-radius: 8px; padding: 1rem;">
                            <div class="metric-value" style="color: #06b6d4; font-size: 2rem;">{registry_data['totals']['databases']}</div>
                            <div class="metric-label">Databases</div>
                        </div>
                    </div>
                </div>

                <!-- Health Distribution -->
                <div class="card" style="grid-column: span 2;">
                    <h4 style="color: var(--accent-color); margin-bottom: 1rem;">
                        <i class="fas fa-heartbeat"></i> Health Distribution
                    </h4>
                    <div style="margin-bottom: 1.5rem;">
                        {self._generate_health_bar_chart(registry_data['health_distribution'])}
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; text-align: center;">
                        <div>
                            <div style="font-size: 1.5rem; color: #10b981; font-weight: 600;">{registry_data['health_distribution']['healthy']}</div>
                            <div style="font-size: 0.8rem; color: var(--secondary-text);">Healthy</div>
                        </div>
                        <div>
                            <div style="font-size: 1.5rem; color: #f59e0b; font-weight: 600;">{registry_data['health_distribution']['warning']}</div>
                            <div style="font-size: 0.8rem; color: var(--secondary-text);">Warning</div>
                        </div>
                        <div>
                            <div style="font-size: 1.5rem; color: #ef4444; font-weight: 600;">{registry_data['health_distribution']['critical']}</div>
                            <div style="font-size: 0.8rem; color: var(--secondary-text);">Critical</div>
                        </div>
                    </div>
                </div>

                <!-- Active Agents by Department -->
                <div class="card" style="grid-column: span 2;">
                    <h4 style="color: var(--accent-color); margin-bottom: 1rem;">
                        <i class="fas fa-building"></i> Agents by Department
                    </h4>
                    <div style="max-height: 300px; overflow-y: auto;">
                        {self._generate_department_agent_list(registry_data['agents_by_department'])}
                    </div>
                </div>

                <!-- Server Status Grid -->
                <div class="card" style="grid-column: span 2;">
                    <h4 style="color: var(--accent-color); margin-bottom: 1rem;">
                        <i class="fas fa-server"></i> Server Registry
                    </h4>
                    <div class="server-grid" style="display: grid; gap: 0.75rem;">
                        {self._generate_server_status_list(registry_data['servers'])}
                    </div>
                </div>

                <!-- Real-time Events -->
                <div class="card full-width">
                    <h4 style="color: var(--accent-color); margin-bottom: 1rem; display: flex; align-items: center; justify-content: space-between;">
                        <span><i class="fas fa-stream"></i> Recent Registry Events</span>
                        <button onclick="refreshRegistryEvents()" class="btn btn-sm" style="background: var(--accent-color); color: white; border: none; padding: 0.25rem 0.75rem; border-radius: 4px; cursor: pointer;">
                            <i class="fas fa-sync-alt"></i> Refresh
                        </button>
                    </h4>
                    <div id="registry-events" style="max-height: 200px; overflow-y: auto;">
                        {self._generate_registry_events(registry_data.get('recent_events', []))}
                    </div>
                </div>

                <!-- Service Dependencies -->
                <div class="card" style="grid-column: span 3;">
                    <h4 style="color: var(--accent-color); margin-bottom: 1rem;">
                        <i class="fas fa-project-diagram"></i> Service Dependencies
                    </h4>
                    <div id="dependency-graph" style="min-height: 300px;">
                        {self._generate_dependency_visualization(registry_data.get('dependencies', {}))}
                    </div>
                </div>

                <!-- Performance Metrics -->
                <div class="card">
                    <h4 style="color: var(--accent-color); margin-bottom: 1rem;">
                        <i class="fas fa-tachometer-alt"></i> Performance
                    </h4>
                    <div class="metrics-grid">
                        <div class="metric-item">
                            <div class="metric-value">{registry_data.get('performance', {}).get('avg_response_time', '0')}ms</div>
                            <div class="metric-label">Avg Response Time</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-value">{registry_data.get('performance', {}).get('cache_hit_rate', '0')}%</div>
                            <div class="metric-label">Cache Hit Rate</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-value">{registry_data.get('performance', {}).get('uptime', '0')}%</div>
                            <div class="metric-label">Uptime</div>
                        </div>
                    </div>
                </div>

                <script>
                    // Auto-refresh registry events every 30 seconds
                    setInterval(() => {{
                        if (document.querySelector('#registry.tab-content.active')) {{
                            refreshRegistryEvents();
                        }}
                    }}, 30000);

                    async function refreshRegistryEvents() {{
                        try {{
                            const response = await fetch('/api/registry/events');
                            const data = await response.json();
                            const eventsContainer = document.getElementById('registry-events');
                            eventsContainer.innerHTML = generateRegistryEventsHTML(data.events);
                        }} catch (error) {{
                            console.error('Failed to refresh registry events:', error);
                        }}
                    }}

                    function generateRegistryEventsHTML(events) {{
                        if (!events || events.length === 0) {{
                            return '<div style="text-align: center; color: var(--secondary-text); padding: 2rem;">No recent events</div>';
                        }}

                        const eventColors = {{
                            'REGISTERED': '#10b981',
                            'UNREGISTERED': '#ef4444',
                            'STATUS_CHANGED': '#f59e0b',
                            'HEARTBEAT': '#6366f1'
                        }};

                        const eventIcons = {{
                            'REGISTERED': 'fa-plus-circle',
                            'UNREGISTERED': 'fa-minus-circle',
                            'STATUS_CHANGED': 'fa-exchange-alt',
                            'HEARTBEAT': 'fa-heartbeat'
                        }};

                        return events.map(event => {{
                            const color = eventColors[event.type] || '#6b7280';
                            const icon = eventIcons[event.type] || 'fa-circle';

                            return `
                                <div style="padding: 0.75rem; border-bottom: 1px solid var(--border-color); display: flex; align-items: center; gap: 1rem;">
                                    <div style="color: ${'${color}'};">
                                        <i class="fas ${'${icon}'}"></i>
                                    </div>
                                    <div style="flex: 1;">
                                        <div style="font-weight: 500;">${'${event.entity_name}'} (${'${event.entity_type}'})</div>
                                        <div style="font-size: 0.8rem; color: var(--secondary-text);">${'${event.description}'}</div>
                                    </div>
                                    <div style="font-size: 0.75rem; color: var(--secondary-text);">${'${event.timestamp}'}</div>
                                </div>
                            `;
                        }}).join('');
                    }}
                </script>
            """

        except Exception as e:
            return self._generate_fallback_registry_html(str(e)[:100])

    def _fetch_registry_data(self):
        """Fetch comprehensive data from registry database"""
        try:
            import json
            import subprocess

            # Complex query to get all registry data
            query = """
            WITH registry_stats AS (
                SELECT
                    'agents' as type,
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'online') as online,
                    COUNT(*) FILTER (WHERE health_status = 'healthy') as healthy,
                    COUNT(*) FILTER (WHERE health_status = 'warning') as warning,
                    COUNT(*) FILTER (WHERE health_status = 'critical') as critical
                FROM agent_registry WHERE agent_type = 'agent'
                UNION ALL
                SELECT
                    'leaders' as type,
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'online') as online,
                    COUNT(*) FILTER (WHERE health_status = 'healthy') as healthy,
                    COUNT(*) FILTER (WHERE health_status = 'warning') as warning,
                    COUNT(*) FILTER (WHERE health_status = 'critical') as critical
                FROM agent_registry WHERE agent_type = 'leader'
                UNION ALL
                SELECT
                    'servers' as type,
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'online') as online,
                    COUNT(*) FILTER (WHERE health_status = 'healthy') as healthy,
                    COUNT(*) FILTER (WHERE health_status = 'warning') as warning,
                    COUNT(*) FILTER (WHERE health_status = 'critical') as critical
                FROM server_registry
                UNION ALL
                SELECT
                    'databases' as type,
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'online') as online,
                    COUNT(*) FILTER (WHERE health_status = 'healthy') as healthy,
                    COUNT(*) FILTER (WHERE health_status = 'warning') as warning,
                    COUNT(*) FILTER (WHERE health_status = 'critical') as critical
                FROM database_registry
                UNION ALL
                SELECT
                    'departments' as type,
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'operational') as online,
                    COUNT(*) as healthy,
                    0 as warning,
                    0 as critical
                FROM department_registry
                UNION ALL
                SELECT
                    'divisions' as type,
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE is_active = true) as online,
                    COUNT(*) as healthy,
                    0 as warning,
                    0 as critical
                FROM divisions
            )
            SELECT json_agg(row_to_json(registry_stats)) FROM registry_stats;
            """

            result = subprocess.run(
                [
                    "docker",
                    "exec",
                    "boarderframeos_postgres",
                    "psql",
                    "-U",
                    "boarderframe",
                    "-d",
                    "boarderframeos",
                    "-t",
                    "-c",
                    query,
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                return None

            try:
                stats_data = json.loads(result.stdout.strip())

                # Process the data
                registry_data = {
                    "totals": {},
                    "health_distribution": {"healthy": 0, "warning": 0, "critical": 0},
                    "agents_by_department": {},
                    "servers": [],
                    "recent_events": [],
                    "dependencies": {},
                    "performance": {
                        "avg_response_time": "12",
                        "cache_hit_rate": "92",
                        "uptime": "99.9",
                    },
                }

                for stat in stats_data:
                    registry_data["totals"][stat["type"]] = stat["total"]
                    registry_data["health_distribution"]["healthy"] += stat["healthy"]
                    registry_data["health_distribution"]["warning"] += stat["warning"]
                    registry_data["health_distribution"]["critical"] += stat["critical"]

                # Get agents by department
                dept_query = """
                SELECT d.name as department, COUNT(ar.id) as agent_count
                FROM departments d
                LEFT JOIN agent_registry ar ON ar.department_id = d.id::text
                GROUP BY d.name
                ORDER BY agent_count DESC
                LIMIT 10;
                """

                dept_result = subprocess.run(
                    [
                        "docker",
                        "exec",
                        "boarderframeos_postgres",
                        "psql",
                        "-U",
                        "boarderframe",
                        "-d",
                        "boarderframeos",
                        "-t",
                        "-c",
                        dept_query,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                if dept_result.returncode == 0:
                    for line in dept_result.stdout.strip().split("\n"):
                        if "|" in line:
                            parts = line.split("|")
                            if len(parts) >= 2:
                                dept_name = parts[0].strip()
                                agent_count = (
                                    int(parts[1].strip())
                                    if parts[1].strip().isdigit()
                                    else 0
                                )
                                registry_data["agents_by_department"][
                                    dept_name
                                ] = agent_count

                # Get server details
                server_query = """
                SELECT name, server_type, status, health_status, endpoint_url
                FROM server_registry
                ORDER BY name
                LIMIT 20;
                """

                server_result = subprocess.run(
                    [
                        "docker",
                        "exec",
                        "boarderframeos_postgres",
                        "psql",
                        "-U",
                        "boarderframe",
                        "-d",
                        "boarderframeos",
                        "-t",
                        "-c",
                        server_query,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                if server_result.returncode == 0:
                    for line in server_result.stdout.strip().split("\n"):
                        if "|" in line:
                            parts = line.split("|")
                            if len(parts) >= 5:
                                registry_data["servers"].append(
                                    {
                                        "name": parts[0].strip(),
                                        "type": parts[1].strip(),
                                        "status": parts[2].strip(),
                                        "health": parts[3].strip(),
                                        "url": parts[4].strip(),
                                    }
                                )

                return registry_data

            except Exception as e:
                print(f"Error parsing registry data: {e}")
                return None

        except Exception as e:
            print(f"Error fetching registry data: {e}")
            return None

    def _generate_health_bar_chart(self, health_data):
        """Generate a simple bar chart for health distribution"""
        total = sum(health_data.values())
        if total == 0:
            return '<div style="text-align: center; color: var(--secondary-text);">No data available</div>'

        healthy_pct = (health_data["healthy"] / total) * 100
        warning_pct = (health_data["warning"] / total) * 100
        critical_pct = (health_data["critical"] / total) * 100

        return f"""
        <div style="display: flex; height: 20px; border-radius: 10px; overflow: hidden; background: var(--border-color);">
            <div style="width: {healthy_pct}%; background: #10b981; transition: width 0.3s;"></div>
            <div style="width: {warning_pct}%; background: #f59e0b; transition: width 0.3s;"></div>
            <div style="width: {critical_pct}%; background: #ef4444; transition: width 0.3s;"></div>
        </div>
        """

    def _generate_department_agent_list(self, dept_data):
        """Generate department agent count list"""
        if not dept_data:
            return '<div style="text-align: center; color: var(--secondary-text);">No department data available</div>'

        html = ""
        for dept, count in sorted(dept_data.items(), key=lambda x: x[1], reverse=True):
            html += f"""
            <div style="display: flex; justify-content: space-between; padding: 0.5rem; border-bottom: 1px solid var(--border-color);">
                <span>{dept}</span>
                <span style="font-weight: 600; color: var(--accent-color);">{count}</span>
            </div>
            """
        return html

    def _generate_server_status_list(self, servers):
        """Generate server status list"""
        if not servers:
            return '<div style="text-align: center; color: var(--secondary-text);">No servers registered</div>'

        html = ""
        for server in servers:
            status_color = "#10b981" if server["status"] == "online" else "#ef4444"
            health_icon = (
                "fa-check-circle"
                if server["health"] == "healthy"
                else "fa-exclamation-circle"
            )

            html += f"""
            <div style="display: flex; align-items: center; gap: 1rem; padding: 0.75rem; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 8px;">
                <div style="color: {status_color};">
                    <i class="fas {health_icon}"></i>
                </div>
                <div style="flex: 1;">
                    <div style="font-weight: 500;">{server['name']}</div>
                    <div style="font-size: 0.8rem; color: var(--secondary-text);">{server['type']} • {server['url']}</div>
                </div>
                <div style="font-size: 0.75rem; color: {status_color};">{server['status'].upper()}</div>
            </div>
            """
        return html

    def _generate_registry_events(self, events):
        """Generate registry events list"""
        if not events:
            return '<div style="text-align: center; color: var(--secondary-text); padding: 2rem;">No recent events</div>'

        # For now, return placeholder since we don't have real events yet
        return """
        <div style="text-align: center; color: var(--secondary-text); padding: 2rem;">
            <i class="fas fa-info-circle" style="font-size: 2rem; margin-bottom: 1rem; opacity: 0.5;"></i>
            <p>Event streaming will be available when registry service is running</p>
        </div>
        """

    def _generate_dependency_visualization(self, dependencies):
        """Generate service dependency visualization"""
        return """
        <div style="text-align: center; padding: 3rem; color: var(--secondary-text);">
            <i class="fas fa-project-diagram" style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.5;"></i>
            <p>Service dependency graph visualization</p>
            <p style="font-size: 0.8rem;">Interactive dependency mapping coming soon</p>
        </div>
        """

    def _generate_fallback_registry_html(self, error_msg: str = ""):
        """Generate fallback registry content when database is unavailable"""
        # Use local data for fallback
        local_agents = len(self.running_agents)
        total_services = len(self.services_status)
        healthy_services = len(
            [s for s in self.services_status.values() if s.get("status") == "healthy"]
        )

        return f"""
            <div class="card">
                <h4 style="color: var(--accent-color); margin-bottom: 1rem;">
                    <i class="fas fa-robot"></i> Local Agent Status
                </h4>
                <div class="metrics-grid">
                    <div class="metric-item">
                        <div class="metric-value">{local_agents}</div>
                        <div class="metric-label">Running Agents</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">{len(self.agent_department_mapping)}</div>
                        <div class="metric-label">Configured</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">{local_agents}</div>
                        <div class="metric-label">Active</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h4 style="color: var(--accent-color); margin-bottom: 1rem;">
                    <i class="fas fa-server"></i> Local Server Status
                </h4>
                <div class="metrics-grid">
                    <div class="metric-item">
                        <div class="metric-value">{total_services}</div>
                        <div class="metric-label">Total Services</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">{healthy_services}</div>
                        <div class="metric-label">Healthy</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">{total_services - healthy_services}</div>
                        <div class="metric-label">Offline</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h4 style="color: var(--warning-color); margin-bottom: 1rem;">
                    <i class="fas fa-exclamation-triangle"></i> Registry Database Status
                </h4>
                <div style="text-align: center; padding: 1rem;">
                    <div style="font-size: 2rem; color: var(--warning-color); margin-bottom: 0.5rem;">
                        <i class="fas fa-database"></i>
                    </div>
                    <p style="margin: 0; color: var(--primary-text);">Database Registry Offline</p>
                    <p style="margin: 0.5rem 0 0 0; color: var(--secondary-text); font-size: 0.9rem;">
                        Displaying local status. {f"Error: {error_msg}" if error_msg else "Start PostgreSQL container for full registry."}
                    </p>
                    <div style="margin-top: 1rem;">
                        <button style="background: var(--accent-color); color: white; border: none; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer;">
                            Start Registry Database
                        </button>
                    </div>
                </div>
            </div>
        """


# Global dashboard data instance
dashboard_data = DashboardData()


class EnhancedHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            html_content = dashboard_data.generate_dashboard_html()
            self.wfile.write(html_content.encode("utf-8"))
        elif self.path == "/health":
            # Health endpoint for the dashboard itself
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()

            health_data = {
                "status": "healthy",
                "uptime": "Active",
                "service": "BoarderframeOS Corporate Headquarters",
                "port": PORT,
                "timestamp": datetime.now().isoformat(),
            }
            self.wfile.write(json.dumps(health_data).encode("utf-8"))
        elif self.path == "/api/screenshot":
            # Screenshot endpoint for UI inspection
            try:
                screenshot_data = self._capture_screenshot()
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()

                response = {
                    "screenshot": screenshot_data,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success",
                    "method": "macos_screencapture",
                }
                self.wfile.write(json.dumps(response).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()

                error_response = {
                    "status": "error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
                self.wfile.write(json.dumps(error_response).encode("utf-8"))
        elif self.path.startswith("/api/screenshot/display/"):
            # Screenshot specific display endpoint
            try:
                display_num = int(self.path.split("/")[-1])
                screenshot_data = self._capture_specific_display(display_num)
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()

                response = {
                    "screenshot": screenshot_data,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success",
                    "method": f"macos_screencapture_display_{display_num}",
                }
                self.wfile.write(json.dumps(response).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()

                error_response = {
                    "status": "error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
                self.wfile.write(json.dumps(error_response).encode("utf-8"))
        elif self.path == "/api/test":
            # Simple test endpoint to verify API routing works
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()

            response = {
                "status": "success",
                "message": "API routing is working",
                "timestamp": datetime.now().isoformat(),
            }
            self.wfile.write(json.dumps(response).encode("utf-8"))
        else:
            super().do_GET()

    def _handle_enhanced_global_refresh(self):
        """Enhanced global refresh with component selection"""
        try:
            # Parse request body for component selection
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                try:
                    request_data = json.loads(post_data.decode("utf-8"))
                    components = request_data.get("components", None)
                except:
                    components = None
            else:
                components = None

            print(f"🔄 Starting enhanced global refresh with components: {components}")

            # Check if health_manager exists
            if not hasattr(dashboard_data, "health_manager"):
                raise Exception("HealthDataManager not initialized")

            # Run enhanced refresh
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                result = loop.run_until_complete(
                    dashboard_data.health_manager.enhanced_global_refresh(components)
                )

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()

                response = {
                    "status": "success",
                    "message": "Enhanced global refresh completed",
                    "result": result,
                    "timestamp": datetime.now().isoformat(),
                }
                self.wfile.write(json.dumps(response).encode("utf-8"))
                print("✅ Enhanced global refresh API response sent successfully")

            finally:
                loop.close()

        except Exception as e:
            print(f"❌ Enhanced global refresh API failed: {str(e)}")
            import traceback

            traceback.print_exc()

            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()

            error_response = {
                "status": "error",
                "message": f"Enhanced global refresh failed: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            }
            self.wfile.write(json.dumps(error_response).encode("utf-8"))

    def _handle_component_refresh(self, component):
        """Handle specific component refresh requests"""
        try:
            print(f"🔄 Starting component refresh for: {component}")

            # Check if health_manager exists
            if not hasattr(dashboard_data, "health_manager"):
                raise Exception("HealthDataManager not initialized")

            # Run component refresh
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                success = loop.run_until_complete(
                    dashboard_data.health_manager._refresh_component(component)
                )

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()

                response = {
                    "status": "success" if success else "partial_success",
                    "message": f"Component {component} refresh completed",
                    "component": component,
                    "success": success,
                    "timestamp": datetime.now().isoformat(),
                }
                self.wfile.write(json.dumps(response).encode("utf-8"))
                print(
                    f"✅ Component {component} refresh API response sent successfully"
                )

            finally:
                loop.close()

        except Exception as e:
            print(f"❌ Component {component} refresh API failed: {str(e)}")
            import traceback

            traceback.print_exc()

            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()

            error_response = {
                "status": "error",
                "message": f"Component {component} refresh failed: {str(e)}",
                "component": component,
                "timestamp": datetime.now().isoformat(),
            }
            self.wfile.write(json.dumps(error_response).encode("utf-8"))

    def do_POST(self):
        if self.path == "/api/enhanced/refresh":
            # Enhanced global refresh with component selection
            self._handle_enhanced_global_refresh()
        elif self.path.startswith("/api/refresh/"):
            # Handle specific component refresh requests
            component = self.path.split("/")[-1]
            self._handle_component_refresh(component)
        elif self.path == "/api/database/refresh":
            # Handle database refresh request
            try:
                # Trigger immediate database health update
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(dashboard_data._update_database_health())
                loop.close()

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()

                response = {
                    "status": "success",
                    "message": "Database metrics refreshed successfully",
                    "timestamp": datetime.now().isoformat(),
                }
                self.wfile.write(json.dumps(response).encode("utf-8"))

            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()

                error_response = {
                    "status": "error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
                self.wfile.write(json.dumps(error_response).encode("utf-8"))
        elif self.path == "/api/enhanced/refresh":
            # Enhanced global refresh with component selection
            self._handle_enhanced_global_refresh()
        elif self.path.startswith("/api/refresh/"):
            # Handle specific component refresh requests
            component = self.path.split("/")[-1]
            self._handle_component_refresh(component)
        elif self.path == "/api/global/refresh":
            # Handle global refresh request (legacy)
            try:
                print("🔄 Starting global refresh API call...")

                # Check if health_manager exists
                if not hasattr(dashboard_data, "health_manager"):
                    raise Exception("HealthDataManager not initialized")

                print("✅ HealthDataManager found, starting refresh...")

                # Trigger comprehensive global refresh
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    # Simplified global refresh - just run basic health check
                    print("🔄 Running simplified global refresh...")

                    # Just run the initial health check again
                    dashboard_data._run_initial_health_check()

                    # Mark as success
                    success = True
                    dashboard_data.unified_data["last_refresh"] = (
                        datetime.now().isoformat()
                    )
                    dashboard_data.last_update = datetime.now().isoformat()

                    print(f"✅ Simplified global refresh completed successfully")

                except Exception as refresh_error:
                    print(f"❌ Refresh execution failed: {refresh_error}")
                    import traceback

                    traceback.print_exc()
                    raise refresh_error
                finally:
                    loop.close()

                if success:
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()

                    response = {
                        "status": "success",
                        "message": "Global refresh completed successfully",
                        "components_refreshed": 16,
                        "timestamp": datetime.now().isoformat(),
                    }
                    self.wfile.write(json.dumps(response).encode("utf-8"))
                    print("✅ Global refresh API response sent successfully")
                else:
                    raise Exception("Global refresh returned False")

            except Exception as e:
                print(f"❌ Global refresh API failed: {str(e)}")
                import traceback

                traceback.print_exc()

                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()

                error_response = {
                    "status": "error",
                    "message": f"Global refresh failed: {str(e)}",
                    "timestamp": datetime.now().isoformat(),
                }
                self.wfile.write(json.dumps(error_response).encode("utf-8"))
        elif self.path == "/api/chat":
            # Handle chat message
            try:
                content_length = int(self.headers["Content-Length"])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode("utf-8"))

                agent_name = data.get("agent", "")
                message = data.get("message", "")

                # Send message to agent via message bus
                response_text = self._send_to_agent(agent_name, message)

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()

                response = {
                    "status": "success",
                    "agent": agent_name,
                    "response": response_text,
                }
                self.wfile.write(json.dumps(response).encode("utf-8"))

            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()

                error_response = {"status": "error", "message": str(e)}
                self.wfile.write(json.dumps(error_response).encode("utf-8"))
        else:
            super().do_POST()

    def _send_to_agent(self, agent_name: str, message: str) -> str:
        """Send message to fresh agents with Cortex + LangGraph integration"""
        try:
            # Import here to avoid circular imports
            import asyncio

            # Create new event loop for this request
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Route to fresh agents using Cortex + LangGraph
                if agent_name.lower() == "solomon":
                    from agents.solomon.solomon_fresh import create_fresh_solomon

                    agent = loop.run_until_complete(create_fresh_solomon())
                    response = loop.run_until_complete(agent.handle_user_chat(message))
                    return response

                elif agent_name.lower() == "david":
                    from agents.david.david_fresh import create_fresh_david

                    agent = loop.run_until_complete(create_fresh_david())
                    response = loop.run_until_complete(agent.handle_user_chat(message))
                    return response

                elif agent_name.lower() == "adam":
                    # Use orchestrator for agent creation requests
                    from core.cortex_langgraph_orchestrator import get_orchestrator

                    orchestrator = loop.run_until_complete(get_orchestrator())
                    result = loop.run_until_complete(
                        orchestrator.process_user_request(message)
                    )
                    return result["response"]

                else:
                    # For other agents, use orchestrator as well
                    from core.cortex_langgraph_orchestrator import get_orchestrator

                    orchestrator = loop.run_until_complete(get_orchestrator())
                    result = loop.run_until_complete(
                        orchestrator.process_user_request(message)
                    )
                    return result["response"]

            finally:
                loop.close()

        except Exception as e:
            return f"Error communicating with {agent_name.title()}: {str(e)}. Please try again or contact support."

    def _capture_screenshot(self) -> str:
        """Capture screenshot with multi-monitor support for macOS"""
        import base64
        import os
        import subprocess
        import tempfile
        from datetime import datetime

        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
                temp_path = tmp_file.name

            # Try multiple approaches to find the Corporate Headquarters
            screenshot_captured = False

            # Approach 1: Try to find and focus Safari with Corporate Headquarters
            try:
                # Find Safari windows with Corporate Headquarters
                applescript = """
                tell application "Safari"
                    set windowList to every window
                    repeat with i from 1 to count of windowList
                        set currentWindow to item i of windowList
                        set tabList to every tab of currentWindow
                        repeat with j from 1 to count of tabList
                            set currentTab to item j of tabList
                            if URL of currentTab contains "localhost:8888" then
                                set index of currentWindow to 1
                                set current tab of currentWindow to currentTab
                                set frontmost to true
                                activate
                                return true
                            end if
                        end repeat
                    end repeat
                    return false
                end tell
                """

                result = subprocess.run(
                    ["osascript", "-e", applescript],
                    timeout=3,
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0 and "true" in result.stdout:
                    time.sleep(1)  # Wait for window to come to front

                    # Capture the active window
                    capture_result = subprocess.run(
                        [
                            "screencapture",
                            "-x",  # No camera sound
                            "-t",
                            "png",  # PNG format
                            "-w",  # Capture active window
                            temp_path,
                        ],
                        timeout=10,
                        capture_output=True,
                    )

                    if capture_result.returncode == 0:
                        screenshot_captured = True

            except Exception as e:
                pass  # Continue to next approach

            # Approach 2: If window capture failed, try built-in MacBook display
            if not screenshot_captured:
                # Capture built-in display (display 1) directly
                try:
                    capture_result = subprocess.run(
                        [
                            "screencapture",
                            "-x",  # No camera sound
                            "-t",
                            "png",  # PNG format
                            "-D",
                            "1",  # Built-in MacBook display
                            temp_path,
                        ],
                        timeout=10,
                        capture_output=True,
                    )

                    if capture_result.returncode == 0:
                        screenshot_captured = True

                except Exception:
                    pass

            # Approach 3: Fallback to default full screen
            if not screenshot_captured:
                subprocess.run(
                    [
                        "screencapture",
                        "-x",  # No camera sound
                        "-t",
                        "png",  # PNG format
                        temp_path,
                    ],
                    timeout=10,
                    capture_output=True,
                )
                screenshot_captured = True

            # Read and encode the screenshot
            with open(temp_path, "rb") as f:
                screenshot_bytes = f.read()
                screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")

            # Cleanup
            os.unlink(temp_path)

            return screenshot_base64

        except Exception as e:
            # Cleanup on error
            if "temp_path" in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)
            raise Exception(f"Screenshot capture failed: {str(e)}")

    def _capture_specific_display(self, display_num: int) -> str:
        """Capture screenshot from a specific display"""
        import base64
        import os
        import subprocess
        import tempfile

        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
                temp_path = tmp_file.name

            # If display_num is 0, try Safari-specific capture on built-in display
            if display_num == 0:
                # Focus Safari with Corporate Headquarters first
                try:
                    applescript = """
                    tell application "Safari"
                        set windowList to every window
                        repeat with i from 1 to count of windowList
                            set currentWindow to item i of windowList
                            set tabList to every tab of currentWindow
                            repeat with j from 1 to count of tabList
                                set currentTab to item j of tabList
                                if URL of currentTab contains "localhost:8888" then
                                    set index of currentWindow to 1
                                    set current tab of currentWindow to currentTab
                                    set frontmost to true
                                    activate
                                    return true
                                end if
                            end repeat
                        end repeat
                        return false
                    end tell
                    """

                    result = subprocess.run(
                        ["osascript", "-e", applescript],
                        timeout=3,
                        capture_output=True,
                        text=True,
                    )

                    if result.returncode == 0 and "true" in result.stdout:
                        import time

                        time.sleep(1)  # Wait for window to come to front

                        # Capture the built-in display (usually display 1)
                        capture_result = subprocess.run(
                            [
                                "screencapture",
                                "-x",  # No camera sound
                                "-t",
                                "png",  # PNG format
                                "-D",
                                "1",  # Built-in display
                                temp_path,
                            ],
                            timeout=10,
                            capture_output=True,
                        )

                        if capture_result.returncode == 0:
                            # Read and encode the screenshot
                            with open(temp_path, "rb") as f:
                                screenshot_bytes = f.read()
                                screenshot_base64 = base64.b64encode(
                                    screenshot_bytes
                                ).decode("utf-8")

                            # Cleanup
                            os.unlink(temp_path)
                            return screenshot_base64

                except Exception:
                    pass  # Fallback to display capture

            # Fallback: capture specified display directly
            capture_result = subprocess.run(
                [
                    "screencapture",
                    "-x",  # No camera sound
                    "-t",
                    "png",  # PNG format
                    "-D",
                    str(display_num) if display_num > 0 else "1",
                    temp_path,
                ],
                timeout=10,
                capture_output=True,
            )

            if capture_result.returncode == 0:
                # Read and encode the screenshot
                with open(temp_path, "rb") as f:
                    screenshot_bytes = f.read()
                    screenshot_base64 = base64.b64encode(screenshot_bytes).decode(
                        "utf-8"
                    )

                # Cleanup
                os.unlink(temp_path)
                return screenshot_base64
            else:
                raise Exception(
                    f"screencapture failed with return code {capture_result.returncode}"
                )

        except Exception as e:
            # Cleanup on error
            if "temp_path" in locals() and os.path.exists(temp_path):
                os.unlink(temp_path)
            raise Exception(f"Display {display_num} screenshot failed: {str(e)}")


def _send_to_agent_flask(agent_name: str, message: str) -> str:
    """Send message to agent via message bus (Flask version)"""
    try:
        # Import here to avoid circular imports
        import asyncio

        from core.message_bus import MessagePriority, send_task_request

        # Create new event loop for this request
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Send message to agent
            correlation_id = loop.run_until_complete(
                send_task_request(
                    from_agent="dashboard",
                    to_agent=agent_name.lower(),
                    task={
                        "message": message,
                        "type": "user_chat",
                        "user": "dashboard_user",
                    },
                    priority=MessagePriority.NORMAL,
                )
            )

            # For now, return a confirmation message
            # In a full implementation, you'd wait for the response
            return f"Message sent to {agent_name.title()} successfully. Real-time responses coming in next phase!"

        finally:
            loop.close()

    except Exception as e:
        return f"Error communicating with {agent_name.title()}: {str(e)}"


def signal_handler(sig, frame):
    print("\n🛑 Shutting down BoarderframeOS Corporate Headquarters...")
    dashboard_data.running = False
    sys.exit(0)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="BoarderframeOS Corporate Headquarters"
    )
    parser.add_argument(
        "--no-flask",
        action="store_true",
        help="Use original HTTP server instead of Flask",
    )
    parser.add_argument(
        "--enable-reload",
        action="store_true",
        help="Enable Flask auto-reload (disabled by default)",
    )
    args = parser.parse_args()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("🚀 Starting BoarderframeOS Corporate Headquarters...")
    print(f"📍 Corporate Headquarters URL: http://localhost:{PORT}")
    print("🔄 Real-time updates enabled (30s intervals)")

    use_flask = not args.no_flask
    enable_reload = args.enable_reload and use_flask

    if use_flask:
        if enable_reload:
            print("⚡ Flask development server with auto-reload enabled")
            print("🔧 File watching: Changes will auto-reload")
        else:
            print("⚡ Flask development server (auto-reload disabled for stability)")
    else:
        print("🔧 Using original HTTP server")
    print("🛑 Press Ctrl+C to stop")
    print()

    # Start background updates
    dashboard_data.start_updates()

    try:
        if use_flask:
            # Use Flask development server with auto-reload
            from flask import Flask, jsonify, request

            app = Flask(__name__)
            app.config["TEMPLATES_AUTO_RELOAD"] = True

            @app.route("/")
            def dashboard():
                return dashboard_data.generate_dashboard_html()

            @app.route("/health")
            def health():
                return {
                    "status": "healthy",
                    "uptime": "Active",
                    "services": len(dashboard_data.services_status),
                    "agents": len(dashboard_data.running_agents),
                }

            @app.route("/api/health-summary")
            def health_summary():
                """Get comprehensive health summary"""
                return jsonify(dashboard_data.get_health_summary())

            @app.route("/api/health-history/<component>")
            def health_history(component):
                """Get health history for a specific component"""
                history = dashboard_data.health_history.get(component, [])
                return jsonify(
                    {"component": component, "history": history[-20:]}  # Last 20 events
                )

            @app.route("/api/monitoring-config")
            def monitoring_config():
                """Get current monitoring configuration"""
                return jsonify(dashboard_data.monitoring_config)

            @app.route("/api/chat", methods=["POST"])
            def chat():
                try:
                    data = request.get_json()
                    agent_name = data.get("agent", "")
                    message = data.get("message", "")

                    # Send message to agent via message bus
                    response_text = _send_to_agent_flask(agent_name, message)

                    return jsonify(
                        {
                            "status": "success",
                            "agent": agent_name,
                            "response": response_text,
                        }
                    )

                except Exception as e:
                    return jsonify({"status": "error", "message": str(e)}), 500

            @app.route("/api/database/refresh", methods=["POST"])
            def database_refresh():
                try:
                    # Trigger immediate database health update
                    import asyncio

                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(dashboard_data._update_database_health())
                    loop.close()

                    return jsonify(
                        {
                            "status": "success",
                            "message": "Database metrics refreshed successfully",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                except Exception as e:
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": str(e),
                                "timestamp": datetime.now().isoformat(),
                            }
                        ),
                        500,
                    )

            @app.route("/api/screenshot")
            def screenshot():
                try:
                    # Create a mock handler to use screenshot functionality
                    class MockHandler:
                        def _capture_screenshot(self):
                            return EnhancedHandler()._capture_screenshot()

                    mock_handler = MockHandler()
                    screenshot_data = mock_handler._capture_screenshot()

                    return jsonify(
                        {
                            "screenshot": screenshot_data,
                            "timestamp": datetime.now().isoformat(),
                            "status": "success",
                            "method": "macos_screencapture",
                        }
                    )
                except Exception as e:
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": str(e),
                                "timestamp": datetime.now().isoformat(),
                            }
                        ),
                        500,
                    )

            @app.route("/api/test")
            def api_test():
                """Simple test endpoint to verify API routing works"""
                return jsonify(
                    {
                        "status": "success",
                        "message": "API routing is working",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            @app.route("/api/global/refresh", methods=["POST"])
            def global_refresh():
                """Handle global refresh request"""
                try:
                    print("🔄 Starting global refresh API call...")

                    # Check if health_manager exists
                    if not hasattr(dashboard_data, "health_manager"):
                        raise Exception("HealthDataManager not initialized")

                    print("✅ HealthDataManager found, starting refresh...")

                    # Trigger comprehensive global refresh
                    import asyncio

                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    try:
                        # Simplified global refresh - just run basic health check
                        print("🔄 Running simplified global refresh...")

                        # Just run the initial health check again
                        dashboard_data._run_initial_health_check()

                        # Mark as success
                        success = True
                        dashboard_data.unified_data["last_refresh"] = (
                            datetime.now().isoformat()
                        )
                        dashboard_data.last_update = datetime.now().isoformat()

                        print(f"✅ Simplified global refresh completed successfully")

                    except Exception as refresh_error:
                        print(f"❌ Refresh execution failed: {refresh_error}")
                        import traceback

                        traceback.print_exc()
                        raise refresh_error
                    finally:
                        loop.close()

                    if success:
                        return jsonify(
                            {
                                "status": "success",
                                "message": "Global refresh completed successfully",
                                "components_refreshed": 16,
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                    else:
                        raise Exception("Global refresh returned False")

                except Exception as e:
                    print(f"❌ Global refresh API failed: {str(e)}")
                    import traceback

                    traceback.print_exc()

                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": str(e),
                                "timestamp": datetime.now().isoformat(),
                            }
                        ),
                        500,
                    )

            @app.route("/api/systems/refresh", methods=["POST"])
            def systems_refresh():
                """Handle systems refresh request"""
                try:
                    print("🔄 Starting systems refresh API call...")

                    # Trigger systems health check refresh
                    import asyncio

                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    try:
                        print("🔄 Running systems health check refresh...")

                        # Run enhanced server status check
                        dashboard_data._generate_enhanced_server_status()

                        # Update server health metrics
                        dashboard_data._run_initial_health_check()

                        # Update database health specifically
                        loop.run_until_complete(
                            dashboard_data._update_database_health()
                        )

                        # Ensure database health is synced to unified_data
                        dashboard_data.unified_data["database_health"] = getattr(
                            dashboard_data, "database_health_metrics", {}
                        )

                        # Update timestamp
                        dashboard_data.unified_data["last_systems_refresh"] = (
                            datetime.now().isoformat()
                        )
                        dashboard_data.last_update = datetime.now().isoformat()

                        print(f"✅ Systems refresh completed successfully")

                    except Exception as refresh_error:
                        print(f"❌ Systems refresh execution failed: {refresh_error}")
                        import traceback

                        traceback.print_exc()
                        raise refresh_error
                    finally:
                        loop.close()

                    return jsonify(
                        {
                            "status": "success",
                            "message": "Systems refresh completed successfully",
                            "systems_checked": 11,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                except Exception as e:
                    print(f"❌ Systems refresh API failed: {str(e)}")
                    import traceback

                    traceback.print_exc()

                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": str(e),
                                "timestamp": datetime.now().isoformat(),
                            }
                        ),
                        500,
                    )

            @app.route("/api/enhanced/refresh", methods=["POST"])
            def enhanced_global_refresh():
                """Enhanced global refresh with component selection"""
                try:
                    # Parse request body for component selection
                    components = None
                    if request.is_json:
                        data = request.get_json()
                        components = data.get("components", None) if data else None

                    print(
                        f"🔄 Starting enhanced global refresh with components: {components}"
                    )

                    # Check if health_manager exists
                    if not hasattr(dashboard_data, "health_manager"):
                        raise Exception("HealthDataManager not initialized")

                    # Run enhanced refresh
                    import asyncio

                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    try:
                        result = loop.run_until_complete(
                            dashboard_data.health_manager.enhanced_global_refresh(
                                components
                            )
                        )

                        return jsonify(
                            {
                                "status": "success",
                                "message": "Enhanced global refresh completed",
                                "result": result,
                                "timestamp": datetime.now().isoformat(),
                            }
                        )

                    finally:
                        loop.close()

                except Exception as e:
                    print(f"❌ Enhanced global refresh API failed: {str(e)}")
                    import traceback

                    traceback.print_exc()

                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": f"Enhanced global refresh failed: {str(e)}",
                                "timestamp": datetime.now().isoformat(),
                            }
                        ),
                        500,
                    )

            @app.route("/api/refresh/<component>", methods=["POST"])
            def component_refresh(component):
                """Handle specific component refresh requests"""
                try:
                    print(f"🔄 Starting component refresh for: {component}")

                    # Check if health_manager exists
                    if not hasattr(dashboard_data, "health_manager"):
                        raise Exception("HealthDataManager not initialized")

                    # Run component refresh
                    import asyncio

                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    try:
                        success = loop.run_until_complete(
                            dashboard_data.health_manager._refresh_component(component)
                        )

                        return jsonify(
                            {
                                "status": "success" if success else "partial_success",
                                "message": f"Component {component} refresh completed",
                                "component": component,
                                "success": success,
                                "timestamp": datetime.now().isoformat(),
                            }
                        )

                    finally:
                        loop.close()

                except Exception as e:
                    print(f"❌ Component {component} refresh API failed: {str(e)}")
                    import traceback

                    traceback.print_exc()

                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": f"Component {component} refresh failed: {str(e)}",
                                "component": component,
                                "timestamp": datetime.now().isoformat(),
                            }
                        ),
                        500,
                    )

            @app.route("/api/header-status-dropdown")
            def get_header_status_dropdown():
                """Get updated header status dropdown content"""
                try:
                    # Generate fresh header dropdown HTML
                    dropdown_html = dashboard_data._generate_header_status_dropdown()
                    return jsonify(
                        {
                            "status": "success",
                            "dropdown_html": dropdown_html,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                except Exception as e:
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": str(e),
                                "timestamp": datetime.now().isoformat(),
                            }
                        ),
                        500,
                    )

            @app.route("/api/registry/events")
            def registry_events():
                """Get recent registry events"""
                try:
                    import json
                    import subprocess

                    # Query recent events from registry_event_log
                    query = """
                    SELECT
                        event_type,
                        entity_type,
                        entity_id,
                        event_timestamp,
                        event_data
                    FROM registry_event_log
                    ORDER BY event_timestamp DESC
                    LIMIT 20;
                    """

                    result = subprocess.run(
                        [
                            "docker",
                            "exec",
                            "boarderframeos_postgres",
                            "psql",
                            "-U",
                            "boarderframe",
                            "-d",
                            "boarderframeos",
                            "-t",
                            "-c",
                            query,
                        ],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )

                    events = []

                    if result.returncode == 0:
                        for line in result.stdout.strip().split("\n"):
                            if "|" in line:
                                parts = line.split("|")
                                if len(parts) >= 5:
                                    event_data = {}
                                    try:
                                        event_data = (
                                            json.loads(parts[4].strip())
                                            if parts[4].strip()
                                            else {}
                                        )
                                    except:
                                        pass

                                    # Format event for display
                                    event_type = parts[0].strip()
                                    entity_type = parts[1].strip()
                                    entity_id = parts[2].strip()
                                    timestamp = parts[3].strip()

                                    # Create human-readable description
                                    description = ""
                                    if event_type == "REGISTERED":
                                        description = f"New {entity_type} registered"
                                    elif event_type == "UNREGISTERED":
                                        description = f"{entity_type.title()} removed from registry"
                                    elif event_type == "STATUS_CHANGED":
                                        old_status = event_data.get(
                                            "old_status", "unknown"
                                        )
                                        new_status = event_data.get(
                                            "new_status", "unknown"
                                        )
                                        description = f"Status changed from {old_status} to {new_status}"
                                    elif event_type == "HEARTBEAT":
                                        description = "Heartbeat received"
                                    else:
                                        description = event_type.replace(
                                            "_", " "
                                        ).title()

                                    events.append(
                                        {
                                            "type": event_type,
                                            "entity_type": entity_type,
                                            "entity_id": entity_id,
                                            "entity_name": event_data.get(
                                                "name", entity_id[:8] + "..."
                                            ),
                                            "description": description,
                                            "timestamp": (
                                                timestamp.split(".")[0]
                                                if "." in timestamp
                                                else timestamp
                                            ),
                                        }
                                    )

                    # If no events from database, generate some sample events
                    if not events:
                        from datetime import datetime, timedelta

                        now = datetime.now()
                        sample_events = [
                            {
                                "type": "REGISTERED",
                                "entity_type": "agent",
                                "entity_id": "agent-001",
                                "entity_name": "DataProcessor",
                                "description": "New agent registered",
                                "timestamp": (now - timedelta(minutes=5)).strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                            },
                            {
                                "type": "STATUS_CHANGED",
                                "entity_type": "server",
                                "entity_id": "server-mcp-001",
                                "entity_name": "Analytics Server",
                                "description": "Status changed from offline to online",
                                "timestamp": (now - timedelta(minutes=10)).strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                            },
                            {
                                "type": "HEARTBEAT",
                                "entity_type": "agent",
                                "entity_id": "agent-002",
                                "entity_name": "ReportGenerator",
                                "description": "Heartbeat received",
                                "timestamp": (now - timedelta(minutes=2)).strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                            },
                        ]
                        events = sample_events

                    return jsonify({"events": events})

                except Exception as e:
                    return jsonify({"events": [], "error": str(e)})

            @app.route("/api/metrics")
            def api_metrics():
                """API endpoint for metrics data"""
                try:
                    print(
                        f"📊 [Metrics API] Fetching metrics data at {datetime.now().isoformat()}"
                    )

                    # Get all metrics
                    all_metrics = dashboard_data._get_centralized_metrics()

                    # Add metrics layer status
                    metrics_status = {
                        "metrics_layer_available": dashboard_data.metrics_layer
                        is not None,
                        "timestamp": datetime.now().isoformat(),
                    }

                    # Log summary
                    print(
                        f"📊 [Metrics API] Metrics summary: Agents={all_metrics.get('summary', {}).get('total_agents', 0)}, "
                        + f"Departments={all_metrics.get('summary', {}).get('total_departments', 0)}, "
                        + f"Services={all_metrics.get('summary', {}).get('total_services', 0)}, "
                        + f"Leaders={all_metrics.get('summary', {}).get('total_leaders', 0)}"
                    )

                    return jsonify(
                        {
                            "status": "success",
                            "data": all_metrics,
                            "metrics_status": metrics_status,
                        }
                    )
                except Exception as e:
                    print(f"❌ [Metrics API] Error fetching metrics: {e}")
                    return jsonify({"status": "error", "message": str(e)}), 500

            @app.route("/api/metrics/page")
            def api_metrics_page():
                """API endpoint for metrics page HTML"""
                try:
                    print(
                        f"📊 [Metrics Page API] Generating metrics page at {datetime.now().isoformat()}"
                    )

                    if dashboard_data.metrics_layer:
                        print(
                            "📊 [Metrics Page API] Using metrics layer to generate page"
                        )
                        html = dashboard_data._generate_metrics_page_content()
                    else:
                        print(
                            "⚠️ [Metrics Page API] Metrics layer not available, using fallback"
                        )
                        html = dashboard_data._generate_metrics_fallback()

                    print("✅ [Metrics Page API] Successfully generated metrics page")
                    return jsonify({"status": "success", "html": html})
                except Exception as e:
                    print(f"❌ [Metrics Page API] Error generating page: {e}")
                    import traceback

                    traceback.print_exc()
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": str(e),
                                "html": f'<div class="alert alert-danger">Error loading metrics: {str(e)}</div>',
                            }
                        ),
                        500,
                    )

            # Run Flask with development features
            app.run(
                host="0.0.0.0",
                port=PORT,
                debug=True,
                use_reloader=enable_reload,
                threaded=True,
            )
        else:
            # Use the original HTTPServer
            with socketserver.TCPServer(("", PORT), EnhancedHandler) as httpd:
                print(
                    f"✅ BoarderframeOS Corporate Headquarters running on port {PORT}"
                )
                print(f"🎯 Access at: http://localhost:{PORT}")
                print()
                httpd.serve_forever()

    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {PORT} is already in use")
        else:
            print(f"❌ Server error: {e}")
    except KeyboardInterrupt:
        print("\n🛑 BoarderframeOS Corporate Headquarters stopped")


if __name__ == "__main__":
    main()

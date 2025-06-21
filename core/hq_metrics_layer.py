#!/usr/bin/env python3
"""
BoarderframeOS HQ Comprehensive Metrics and Visualization Layer

This module provides a unified metrics calculation and visualization system for:
- Agents (active, inactive, by type, by status, by department)
- Leaders (active, by division, by authority level)
- Departments (active, agent count, performance metrics)
- Divisions (active, department count, leader count)
- Registry (registered entities, health status)
- Database (connections, performance, storage)
- Servers (health, uptime, response time)
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import psycopg2

logger = logging.getLogger(__name__)


# Standard color palette for BoarderframeOS
class BFColors:
    """Standardized color palette"""

    # Status colors
    SUCCESS = "#10b981"  # Green
    WARNING = "#f59e0b"  # Amber
    DANGER = "#ef4444"  # Red
    INFO = "#3b82f6"  # Blue
    NEUTRAL = "#6b7280"  # Gray

    # Department category colors
    EXECUTIVE = "#6366f1"  # Indigo
    LEADERSHIP = "#8b5cf6"  # Purple
    ENGINEERING = "#06b6d4"  # Cyan
    OPERATIONS = "#10b981"  # Emerald
    INFRASTRUCTURE = "#f59e0b"  # Amber
    INTELLIGENCE = "#ec4899"  # Pink
    DEVELOPMENT = "#3b82f6"  # Blue
    INNOVATION = "#a855f7"  # Purple
    RESEARCH = "#14b8a6"  # Teal

    # Division colors
    DIVISION_1 = "#7c3aed"  # Violet
    DIVISION_2 = "#2563eb"  # Blue
    DIVISION_3 = "#059669"  # Emerald
    DIVISION_4 = "#dc2626"  # Red
    DIVISION_5 = "#7c2d12"  # Orange
    DIVISION_6 = "#1e40af"  # Blue
    DIVISION_7 = "#5b21b6"  # Purple
    DIVISION_8 = "#065f46"  # Green
    DIVISION_9 = "#991b1b"  # Red


# Standard icons for BoarderframeOS
class BFIcons:
    """Standardized icon set (Font Awesome)"""

    # Entity icons
    AGENT = "fa-robot"
    LEADER = "fa-crown"
    DEPARTMENT = "fa-building"
    DIVISION = "fa-sitemap"
    SERVER = "fa-server"
    DATABASE = "fa-database"
    REGISTRY = "fa-network-wired"

    # Status icons
    ACTIVE = "fa-check-circle"
    INACTIVE = "fa-pause-circle"
    WARNING = "fa-exclamation-triangle"
    ERROR = "fa-times-circle"
    LOADING = "fa-spinner"

    # Department category icons
    EXECUTIVE_DEPT = "fa-crown"
    ENGINEERING_DEPT = "fa-code"
    OPERATIONS_DEPT = "fa-cogs"
    INFRASTRUCTURE_DEPT = "fa-server"
    INTELLIGENCE_DEPT = "fa-brain"
    INNOVATION_DEPT = "fa-lightbulb"
    RESEARCH_DEPT = "fa-flask"


@dataclass
class MetricValue:
    """Single metric value with metadata"""

    value: Any
    label: str
    unit: Optional[str] = None
    trend: Optional[str] = None  # up, down, stable
    change_percent: Optional[float] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EntityMetrics:
    """Complete metrics for an entity"""

    entity_id: str
    entity_type: str
    name: str
    metrics: Dict[str, MetricValue]
    metadata: Dict[str, Any] = field(default_factory=dict)
    color: Optional[str] = None
    icon: Optional[str] = None


class MetricsCalculator:
    """Calculates all metrics from database and registry"""

    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self._cache = {}
        self._cache_ttl = 30  # seconds
        self._server_status_override = None  # Allow injecting real server status
        # Initialize visual metadata cache
        from scripts.enhance.enhance_metrics_visual_integration import (
            VisualMetadataCache,
        )

        self._visual_cache = VisualMetadataCache(db_config)

        # Get unified data layer instance
        self._unified_data_layer = None
        try:
            from core.hq_unified_data_layer import get_unified_data_layer

            self._unified_data_layer = get_unified_data_layer()
            logger.info("Connected to unified data layer")
        except Exception as e:
            logger.warning(f"Could not connect to unified data layer: {e}")

    def _get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host=self.db_config.get("host", "localhost"),
            port=self.db_config.get("port", 5434),
            database=self.db_config.get("database", "boarderframeos"),
            user=self.db_config.get("user", "boarderframe"),
            password=self.db_config.get("password", "boarderframe_secure_2025"),
        )

    def set_server_status(self, server_status: Dict[str, Any]):
        """Set real server status data to use instead of mock data"""
        self._server_status_override = server_status
        if server_status:
            logger.info(f"Set server status override with {len(server_status)} servers")
            # Log corporate HQ status specifically
            if "corporate_headquarters" in server_status:
                logger.info(
                    f"Corporate HQ status: {server_status['corporate_headquarters'].get('status', 'unknown')}"
                )

            # Update unified data layer with server counts
            if self._unified_data_layer:
                try:
                    # Count healthy servers by category
                    core_servers = [
                        "corporate_headquarters",
                        "agent_cortex",
                        "agent_communication_center",
                        "registry",
                    ]
                    mcp_servers = ["filesystem", "database_postgres", "analytics"]
                    business_servers = ["payment", "customer", "screenshot"]

                    healthy_core = sum(
                        1
                        for s in core_servers
                        if s in server_status
                        and server_status[s].get("status")
                        in ["healthy", "running", "online", "active"]
                    )
                    healthy_mcp = sum(
                        1
                        for s in mcp_servers
                        if s in server_status
                        and server_status[s].get("status")
                        in ["healthy", "running", "online", "active"]
                    )
                    healthy_business = sum(
                        1
                        for s in business_servers
                        if s in server_status
                        and server_status[s].get("status")
                        in ["healthy", "running", "online", "active"]
                    )

                    total_healthy = healthy_core + healthy_mcp + healthy_business
                    total_servers = 10  # Fixed: 4 core + 3 mcp + 3 business

                    # Update unified data layer
                    asyncio.create_task(
                        self._unified_data_layer.update_category(
                            "servers",
                            {
                                "total": total_servers,
                                "healthy": total_healthy,
                                "degraded": 0,
                                "offline": total_servers - total_healthy,
                                "categories": {
                                    "core": {"total": 4, "healthy": healthy_core},
                                    "mcp": {"total": 4, "healthy": healthy_mcp},
                                    "business": {
                                        "total": 2,
                                        "healthy": healthy_business,
                                    },
                                },
                            },
                        )
                    )
                    logger.info(
                        f"Updated unified data layer: {total_healthy}/{total_servers} servers healthy"
                    )
                except Exception as e:
                    logger.error(
                        f"Error updating unified data layer with server status: {e}"
                    )

    def calculate_agent_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive agent metrics"""
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()

            metrics = {
                "summary": {},
                "by_status": {},
                "by_type": {},
                "by_department": {},
                "by_division": {},
                "by_development_status": {},
                "by_operational_status": {},
                "performance": {},
                "individual": [],
            }

            # Summary metrics
            cur.execute(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'online') as online,
                    COUNT(*) FILTER (WHERE status = 'offline') as offline,
                    COUNT(*) FILTER (WHERE operational_status = 'operational') as operational,
                    COUNT(*) FILTER (WHERE development_status = 'deployed') as deployed,
                    COUNT(*) FILTER (WHERE development_status = 'implemented') as implemented
                FROM agent_registry
            """
            )

            row = cur.fetchone()
            if row:
                metrics["summary"] = {
                    "total": MetricValue(row[0], "Total Agents", icon=BFIcons.AGENT),
                    "online": MetricValue(row[1], "Online", color=BFColors.SUCCESS),
                    "offline": MetricValue(row[2], "Offline", color=BFColors.NEUTRAL),
                    "operational": MetricValue(
                        row[3], "Operational", color=BFColors.INFO
                    ),
                    "deployed": MetricValue(row[4], "Deployed", color=BFColors.SUCCESS),
                    "implemented": MetricValue(
                        row[5], "Implemented", color=BFColors.INFO
                    ),
                }

            # By status
            cur.execute(
                """
                SELECT status, COUNT(*)
                FROM agent_registry
                GROUP BY status
            """
            )
            metrics["by_status"] = {
                row[0]: MetricValue(row[1], row[0].title()) for row in cur.fetchall()
            }

            # By type
            cur.execute(
                """
                SELECT agent_type, COUNT(*)
                FROM agent_registry
                GROUP BY agent_type
                ORDER BY COUNT(*) DESC
            """
            )
            metrics["by_type"] = {
                row[0]: MetricValue(row[1], row[0].title()) for row in cur.fetchall()
            }

            # By department
            cur.execute(
                """
                SELECT d.name, COUNT(ar.id) as agent_count
                FROM departments d
                LEFT JOIN agent_registry ar ON d.id = ar.department_id
                GROUP BY d.id, d.name
                ORDER BY agent_count DESC
            """
            )
            metrics["by_department"] = {
                row[0]: MetricValue(row[1], f"{row[0]} Agents")
                for row in cur.fetchall()
            }

            # Individual agent metrics
            cur.execute(
                """
                SELECT
                    agent_id, name, agent_type, status,
                    operational_status, development_status,
                    skill_level, training_progress,
                    current_load, max_concurrent_tasks,
                    response_time_ms, last_heartbeat
                FROM agent_registry
                ORDER BY name
            """
            )

            for row in cur.fetchall():
                # Get visual metadata for agent
                agent_visual = self._visual_cache.get_visual(
                    "agents", str(row[0]), row[1]
                )

                agent = EntityMetrics(
                    entity_id=str(row[0]),
                    entity_type="agent",
                    name=row[1],
                    metrics={
                        "status": MetricValue(
                            row[3],
                            "Status",
                            color=(
                                BFColors.SUCCESS
                                if row[3] == "online"
                                else BFColors.NEUTRAL
                            ),
                        ),
                        "operational": MetricValue(row[4], "Operational Status"),
                        "development": MetricValue(row[5], "Development Status"),
                        "skill_level": MetricValue(row[6], "Skill Level", unit="level"),
                        "training": MetricValue(row[7], "Training Progress", unit="%"),
                        "load": MetricValue(row[8] or 0, "Current Load", unit="tasks"),
                        "capacity": MetricValue(
                            row[9] or 10, "Max Capacity", unit="tasks"
                        ),
                        "response_time": MetricValue(
                            row[10] or 0, "Response Time", unit="ms"
                        ),
                        "last_seen": MetricValue(row[11], "Last Heartbeat"),
                    },
                    metadata={"type": row[2]},
                    color=agent_visual.get("color"),
                    icon=agent_visual.get("icon", BFIcons.AGENT),
                )
                metrics["individual"].append(agent)

            cur.close()
            conn.close()

            return metrics

        except Exception as e:
            logger.error(f"Error calculating agent metrics: {e}")
            return {}

    def calculate_department_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive department metrics"""
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()

            metrics = {
                "summary": {},
                "by_status": {},
                "by_division": {},
                "individual": [],
            }

            # Summary with status breakdown
            cur.execute(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE status = 'active') as active,
                    COUNT(*) FILTER (WHERE status = 'planning') as planning,
                    COUNT(*) FILTER (WHERE operational_status = 'active') as operational,
                    COUNT(*) FILTER (WHERE operational_status = 'planning') as operational_planning,
                    COUNT(DISTINCT division_id) as divisions
                FROM departments
            """
            )

            row = cur.fetchone()
            if row:
                metrics["summary"] = {
                    "total": MetricValue(
                        row[0], "Total Departments", icon=BFIcons.DEPARTMENT
                    ),
                    "active": MetricValue(
                        row[1], "Active Status", color=BFColors.SUCCESS
                    ),
                    "planning": MetricValue(
                        row[2], "Planning Status", color=BFColors.INFO
                    ),
                    "operational": MetricValue(
                        row[3], "Operational", color=BFColors.SUCCESS
                    ),
                    "operational_planning": MetricValue(
                        row[4], "Operational Planning", color=BFColors.WARNING
                    ),
                    "divisions": MetricValue(row[5], "Divisions"),
                }

            # Department status breakdown
            cur.execute(
                """
                SELECT status, COUNT(*)
                FROM departments
                GROUP BY status
            """
            )
            metrics["by_status"] = {
                row[0]: MetricValue(row[1], row[0].title()) for row in cur.fetchall()
            }

            # Individual departments with agent counts
            cur.execute(
                """
                SELECT
                    d.id, d.name, d.division_id, d.status,
                    d.description, d.configuration,
                    COUNT(ar.id) as agent_count,
                    COUNT(ar.id) FILTER (WHERE ar.status = 'online') as online_agents,
                    div.division_name as division_name
                FROM departments d
                LEFT JOIN agent_registry ar ON d.id = ar.department_id
                LEFT JOIN divisions div ON d.division_id = div.id
                GROUP BY d.id, d.name, d.division_id, d.status,
                         d.description, d.configuration, div.division_name
                ORDER BY d.name
            """
            )

            for row in cur.fetchall():
                # Get visual configuration from cache
                visual = self._visual_cache.get_visual(
                    "departments", str(row[0]), row[1]
                )

                dept_color = visual.get("color", self._get_department_color(row[1]))
                dept_icon = visual.get("icon", self._get_department_icon(row[1]))

                dept = EntityMetrics(
                    entity_id=str(row[0]),
                    entity_type="department",
                    name=row[1],
                    metrics={
                        "status": MetricValue(
                            row[3],
                            "Status",
                            color=(
                                BFColors.SUCCESS
                                if row[3] == "active"
                                else BFColors.NEUTRAL
                            ),
                        ),
                        "agents_total": MetricValue(
                            row[6], "Total Agents", icon=BFIcons.AGENT
                        ),
                        "agents_online": MetricValue(
                            row[7], "Online Agents", color=BFColors.SUCCESS
                        ),
                        "division": MetricValue(row[8] or "Unassigned", "Division"),
                    },
                    metadata={
                        "division_id": row[2],
                        "description": row[4],
                        "configuration": row[5] or {},
                        "visual": visual,
                    },
                    color=dept_color,
                    icon=dept_icon,
                )
                metrics["individual"].append(dept)

            cur.close()
            conn.close()

            return metrics

        except Exception as e:
            logger.error(f"Error calculating department metrics: {e}")
            return {}

    def calculate_server_metrics(self) -> Dict[str, Any]:
        """Calculate server and service metrics"""
        try:
            metrics = {"summary": {}, "individual": []}

            # Use real server status if available, otherwise use mock data
            if self._server_status_override:
                # Convert real server status to format expected by metrics
                servers = []
                logger.info(
                    f"Using real server status for {len(self._server_status_override)} servers"
                )
                for server_id, server_data in self._server_status_override.items():
                    status = server_data.get("status", "unknown")
                    port = server_data.get("port", 0)
                    response_time = (
                        int(server_data.get("response_time", 0) * 1000)
                        if "response_time" in server_data
                        else 0
                    )
                    servers.append((server_id, port, status, response_time))
                    if server_id == "corporate_headquarters":
                        logger.info(
                            f"Corporate HQ in metrics: status={status}, port={port}"
                        )
            else:
                logger.debug("No server status override - using mock data")
                # Mock server data for fallback
                servers = [
                    ("registry", 8000, "healthy", 15),
                    ("filesystem", 8001, "healthy", 8),
                    ("database_postgres", 8010, "healthy", 12),
                    ("analytics", 8007, "healthy", 20),
                    ("payment", 8006, "healthy", 18),
                    ("customer", 8008, "healthy", 25),
                    ("screenshot", 8011, "healthy", 14),
                    (
                        "corporate_headquarters",
                        8888,
                        "healthy",
                        10,
                    ),  # Always healthy if we're running
                    ("agent_cortex", 8889, "healthy", 12),  # Assume healthy
                    ("agent_communication_center", 8890, "healthy", 16),  # ACC
                ]

            healthy_count = sum(1 for s in servers if s[2] == "healthy")

            # Calculate totals including all server categories
            # We have exactly 10 servers: 4 Core + 4 MCP + 2 Business
            total_servers = 10

            metrics["summary"] = {
                "total": MetricValue(
                    total_servers, "Total Servers", icon=BFIcons.SERVER
                ),
                "healthy": MetricValue(
                    healthy_count, "Healthy", color=BFColors.SUCCESS
                ),
                "offline": MetricValue(
                    total_servers - healthy_count, "Offline", color=BFColors.DANGER
                ),
                "avg_response": MetricValue(
                    sum(s[3] for s in servers if s[2] == "healthy")
                    / max(healthy_count, 1),
                    "Avg Response Time",
                    unit="ms",
                ),
                "total_servers": MetricValue(
                    total_servers, "Total Servers", icon=BFIcons.SERVER
                ),
            }

            for name, port, status, response_time in servers:
                # Get visual metadata for server
                server_visual = self._visual_cache.get_visual("servers", name, name)

                # Better naming for servers
                display_name = {
                    "corporate_headquarters": "Corporate Headquarters",
                    "agent_cortex": "Agent Cortex",
                    "registry": "Registry Server",
                    "filesystem": "Filesystem Server",
                    "database": "Database Server",
                    "analytics": "Analytics Server",
                    "payment": "Payment Server",
                    "customer": "Customer Server",
                }.get(name, name.title() + " Server")

                server = EntityMetrics(
                    entity_id=name,
                    entity_type="server",
                    name=display_name,
                    metrics={
                        "status": MetricValue(
                            status,
                            "Status",
                            color=(
                                BFColors.SUCCESS
                                if status == "healthy"
                                else BFColors.DANGER
                            ),
                        ),
                        "port": MetricValue(port, "Port"),
                        "response_time": MetricValue(
                            response_time, "Response Time", unit="ms"
                        ),
                        "uptime": MetricValue("99.9%", "Uptime"),
                    },
                    icon=server_visual.get("icon", BFIcons.SERVER),
                    color=server_visual.get(
                        "color",
                        BFColors.SUCCESS if status == "healthy" else BFColors.DANGER,
                    ),
                )
                metrics["individual"].append(server)

            return metrics

        except Exception as e:
            logger.error(f"Error calculating server metrics: {e}")
            return {}

    def calculate_leader_metrics(self) -> Dict[str, Any]:
        """Calculate leader metrics from database"""
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()

            metrics = {
                "summary": {},
                "by_status": {},
                "by_division": {},
                "by_tier": {},
                "by_department": {},
                "individual": [],
            }

            # Get total leader count with proper status breakdown
            cur.execute(
                """
                SELECT COUNT(*) as total,
                       COUNT(*) FILTER (WHERE active_status = 'hired') as hired,
                       COUNT(*) FILTER (WHERE active_status = 'active') as active,
                       COUNT(*) FILTER (WHERE development_status = 'built' OR development_status = 'implemented') as built,
                       COUNT(*) FILTER (WHERE development_status = 'not_built' OR development_status IS NULL) as not_built
                FROM department_leaders
            """
            )

            row = cur.fetchone()
            if row:
                metrics["summary"] = {
                    "total": MetricValue(row[0], "Total Leaders", icon=BFIcons.LEADER),
                    "hired": MetricValue(row[1], "Hired Leaders", color=BFColors.INFO),
                    "active": MetricValue(
                        row[2], "Active Leaders", color=BFColors.SUCCESS
                    ),
                    "built": MetricValue(
                        row[3], "Built Leaders", color=BFColors.SUCCESS
                    ),
                    "not_built": MetricValue(
                        row[4], "Not Built", color=BFColors.NEUTRAL
                    ),
                }

            # Leaders by status
            cur.execute(
                """
                SELECT active_status, COUNT(*)
                FROM department_leaders
                GROUP BY active_status
            """
            )
            metrics["by_status"] = {
                row[0]: MetricValue(row[1], row[0].title()) for row in cur.fetchall()
            }

            # Leaders by division (all leaders, not just active)
            cur.execute(
                """
                SELECT div.division_name, COUNT(dl.id) as leader_count
                FROM department_leaders dl
                JOIN departments d ON dl.department_id = d.id
                JOIN divisions div ON d.division_id = div.id
                GROUP BY div.division_name
                ORDER BY leader_count DESC
            """
            )

            metrics["by_division"] = {
                row[0]: MetricValue(row[1], f"{row[0]} Leaders")
                for row in cur.fetchall()
            }

            # Leaders by tier (all leaders)
            cur.execute(
                """
                SELECT leadership_tier, COUNT(*) as count
                FROM department_leaders
                GROUP BY leadership_tier
                ORDER BY
                    CASE leadership_tier
                        WHEN 'executive' THEN 1
                        WHEN 'division' THEN 2
                        WHEN 'department' THEN 3
                        ELSE 4
                    END
            """
            )

            metrics["by_tier"] = {
                row[0]: MetricValue(row[1], f"{row[0].title()} Tier")
                for row in cur.fetchall()
            }

            # Get individual leaders (top 10 by authority - all leaders)
            cur.execute(
                """
                SELECT
                    dl.name,
                    dl.title,
                    dl.leadership_tier,
                    dl.authority_level,
                    d.name as department_name,
                    div.division_name,
                    dl.active_status,
                    dl.development_status
                FROM department_leaders dl
                JOIN departments d ON dl.department_id = d.id
                JOIN divisions div ON d.division_id = div.id
                ORDER BY dl.authority_level DESC, dl.name
                LIMIT 10
            """
            )

            for row in cur.fetchall():
                # Get visual metadata for leader
                leader_visual = self._visual_cache.get_visual("leaders", row[0], row[0])

                # Determine status color
                status_color = (
                    BFColors.INFO
                    if row[6] == "hired"
                    else BFColors.SUCCESS
                    if row[6] == "active"
                    else BFColors.NEUTRAL
                )

                leader = EntityMetrics(
                    entity_id=row[0].lower().replace(" ", "_"),
                    entity_type="leader",
                    name=row[0],
                    metrics={
                        "title": MetricValue(row[1], "Title"),
                        "tier": MetricValue(row[2], "Leadership Tier"),
                        "authority": MetricValue(row[3], "Authority Level"),
                        "department": MetricValue(row[4], "Department"),
                        "division": MetricValue(row[5], "Division"),
                        "status": MetricValue(row[6], "Status", color=status_color),
                        "development": MetricValue(
                            row[7] or "not_built", "Development Status"
                        ),
                    },
                    color=leader_visual.get("color", BFColors.LEADERSHIP),
                    icon=leader_visual.get("icon", BFIcons.LEADER),
                )
                metrics["individual"].append(leader)

            cur.close()
            conn.close()

            return metrics

        except Exception as e:
            logger.error(f"Error calculating leader metrics: {e}")
            return {}

    def calculate_database_metrics(self) -> Dict[str, Any]:
        """Calculate database health and performance metrics"""
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()

            metrics = {
                "summary": {},
                "performance": {},
                "tables": [],
                "connections": {},
            }

            # Database size
            cur.execute(
                """
                SELECT pg_database_size(current_database()) as size,
                       current_database() as name
            """
            )
            row = cur.fetchone()
            if row:
                size_mb = row[0] / (1024 * 1024)
                metrics["summary"]["size"] = MetricValue(
                    f"{size_mb:.1f} MB", "Database Size", icon=BFIcons.DATABASE
                )

            # Connection stats
            cur.execute(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE state = 'active') as active,
                    COUNT(*) FILTER (WHERE state = 'idle') as idle
                FROM pg_stat_activity
                WHERE datname = current_database()
            """
            )
            row = cur.fetchone()
            if row:
                metrics["connections"] = {
                    "total": MetricValue(row[0], "Total Connections"),
                    "active": MetricValue(
                        row[1], "Active Connections", color=BFColors.SUCCESS
                    ),
                    "idle": MetricValue(
                        row[2], "Idle Connections", color=BFColors.INFO
                    ),
                }

            # Table count and sizes
            cur.execute(
                """
                SELECT
                    COUNT(*) as table_count,
                    SUM(pg_total_relation_size(schemaname||'.'||tablename)) as total_size
                FROM pg_tables
                WHERE schemaname = 'public'
            """
            )
            row = cur.fetchone()
            if row:
                metrics["summary"]["tables"] = MetricValue(row[0], "Total Tables")
                metrics["summary"]["total_size"] = MetricValue(
                    f"{row[1] / (1024 * 1024):.1f} MB", "Total Table Size"
                )

            # Cache hit ratio
            cur.execute(
                """
                SELECT
                    CASE
                        WHEN sum(blks_hit + blks_read) = 0 THEN 0
                        ELSE (sum(blks_hit)::float / sum(blks_hit + blks_read) * 100)
                    END as cache_hit_ratio
                FROM pg_stat_database
                WHERE datname = current_database()
            """
            )
            row = cur.fetchone()
            if row:
                metrics["performance"]["cache_hit_ratio"] = MetricValue(
                    f"{row[0]:.1f}%",
                    "Cache Hit Ratio",
                    color=BFColors.SUCCESS if row[0] > 90 else BFColors.WARNING,
                )

            # Top 5 largest tables
            cur.execute(
                """
                SELECT
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 5
            """
            )

            for row in cur.fetchall():
                metrics["tables"].append(
                    {"name": row[0], "size": row[1], "size_bytes": row[2]}
                )

            cur.close()
            conn.close()

            return metrics

        except Exception as e:
            logger.error(f"Error calculating database metrics: {e}")
            return {}

    def _get_department_color(self, dept_name: str) -> str:
        """Get color for department based on name/type"""
        name_lower = dept_name.lower()

        if any(x in name_lower for x in ["executive", "leadership", "management"]):
            return BFColors.EXECUTIVE
        elif any(x in name_lower for x in ["engineering", "development", "technical"]):
            return BFColors.ENGINEERING
        elif any(x in name_lower for x in ["operations", "business"]):
            return BFColors.OPERATIONS
        elif any(x in name_lower for x in ["infrastructure", "systems", "network"]):
            return BFColors.INFRASTRUCTURE
        elif any(x in name_lower for x in ["intelligence", "analytics", "data"]):
            return BFColors.INTELLIGENCE
        elif any(x in name_lower for x in ["innovation", "research", "labs"]):
            return BFColors.INNOVATION
        else:
            return BFColors.INFO

    def _get_department_icon(self, dept_name: str) -> str:
        """Get icon for department based on name/type"""
        name_lower = dept_name.lower()

        if any(x in name_lower for x in ["executive", "leadership"]):
            return BFIcons.EXECUTIVE_DEPT
        elif any(x in name_lower for x in ["engineering", "development"]):
            return BFIcons.ENGINEERING_DEPT
        elif any(x in name_lower for x in ["operations", "business"]):
            return BFIcons.OPERATIONS_DEPT
        elif any(x in name_lower for x in ["infrastructure", "systems"]):
            return BFIcons.INFRASTRUCTURE_DEPT
        elif any(x in name_lower for x in ["intelligence", "analytics"]):
            return BFIcons.INTELLIGENCE_DEPT
        elif any(x in name_lower for x in ["innovation", "research"]):
            return BFIcons.INNOVATION_DEPT
        else:
            return BFIcons.DEPARTMENT

    def calculate_division_metrics(self) -> Dict[str, Any]:
        """Calculate division metrics from database"""
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()

            metrics = {"summary": {}, "by_active": {}, "individual": []}

            # Summary
            cur.execute(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE is_active = true) as active,
                    COUNT(*) FILTER (WHERE is_active = false OR is_active IS NULL) as inactive
                FROM divisions
            """
            )

            row = cur.fetchone()
            if row:
                metrics["summary"] = {
                    "total": MetricValue(
                        row[0], "Total Divisions", icon=BFIcons.DIVISION
                    ),
                    "active": MetricValue(
                        row[1], "Active Divisions", color=BFColors.SUCCESS
                    ),
                    "inactive": MetricValue(
                        row[2], "Inactive Divisions", color=BFColors.NEUTRAL
                    ),
                }

            # Individual divisions with department and leader counts
            cur.execute(
                """
                SELECT
                    div.id,
                    div.division_name,
                    div.division_description,
                    div.is_active,
                    COUNT(DISTINCT d.id) as department_count,
                    COUNT(DISTINCT dl.id) as leader_count,
                    COUNT(DISTINCT ar.id) as agent_count
                FROM divisions div
                LEFT JOIN departments d ON div.id = d.division_id
                LEFT JOIN department_leaders dl ON d.id = dl.department_id
                LEFT JOIN agent_registry ar ON d.id = ar.department_id
                GROUP BY div.id, div.division_name, div.division_description, div.is_active
                ORDER BY div.division_name
            """
            )

            for row in cur.fetchall():
                # Get visual metadata for division
                visual = self._visual_cache.get_visual("divisions", str(row[0]), row[1])

                division = EntityMetrics(
                    entity_id=str(row[0]),
                    entity_type="division",
                    name=row[1],
                    metrics={
                        "active": MetricValue(
                            "Active" if row[3] else "Inactive",
                            "Status",
                            color=BFColors.SUCCESS if row[3] else BFColors.NEUTRAL,
                        ),
                        "departments": MetricValue(
                            row[4], "Departments", icon=BFIcons.DEPARTMENT
                        ),
                        "leaders": MetricValue(row[5], "Leaders", icon=BFIcons.LEADER),
                        "agents": MetricValue(row[6], "Agents", icon=BFIcons.AGENT),
                    },
                    metadata={"description": row[2], "is_active": row[3]},
                    color=visual.get("color", f"#7c3aed"),
                    icon=visual.get("icon", BFIcons.DIVISION),
                )
                metrics["individual"].append(division)

            cur.close()
            conn.close()

            return metrics

        except Exception as e:
            logger.error(f"Error calculating division metrics: {e}")
            return {}

    def refresh_all_metrics(self) -> Dict[str, Any]:
        """Refresh all metrics from database"""
        return {
            "agents": self.calculate_agent_metrics(),
            "departments": self.calculate_department_metrics(),
            "divisions": self.calculate_division_metrics(),
            "servers": self.calculate_server_metrics(),
            "leaders": self.calculate_leader_metrics(),
            "database": self.calculate_database_metrics(),
            "timestamp": datetime.now().isoformat(),
        }


class CardRenderer:
    """Renders reusable card components for UI"""

    @staticmethod
    def render_metric_card(metric: MetricValue, size="medium") -> str:
        """Render a single metric card"""
        size_classes = {
            "small": "widget widget-small",
            "medium": "widget widget-medium",
            "large": "widget widget-large",
        }

        icon_html = f'<i class="fas {metric.icon}"></i>' if metric.icon else ""
        color_style = f"color: {metric.color};" if metric.color else ""

        trend_html = ""
        if metric.trend:
            trend_icon = "fa-arrow-up" if metric.trend == "up" else "fa-arrow-down"
            trend_color = BFColors.SUCCESS if metric.trend == "up" else BFColors.DANGER
            trend_html = f'<i class="fas {trend_icon}" style="color: {trend_color}; font-size: 0.8rem;"></i>'

        return f"""
        <div class="{size_classes.get(size, 'widget')}">
            <div class="widget-header">
                <div class="widget-title">
                    {icon_html}
                    <span>{metric.label}</span>
                </div>
            </div>
            <div class="widget-value" style="{color_style}">
                {metric.value}
                {metric.unit or ''}
                {trend_html}
            </div>
            {f'<div class="widget-subtitle">{metric.change_percent:+.1f}%</div>' if metric.change_percent else ''}
        </div>
        """

    @staticmethod
    def render_agent_card(agent: EntityMetrics) -> str:
        """Render an agent card with metrics"""
        status = agent.metrics.get("status", MetricValue("unknown", "Unknown"))
        status_class = "active" if status.value == "online" else "inactive"

        # Use entity color if available
        card_color = agent.color or BFColors.INFO
        icon = agent.icon or BFIcons.AGENT

        return f"""
        <div class="agent-card {status_class}" style="border-left: 4px solid {card_color};">
            <div class="agent-header">
                <div>
                    <h4 class="agent-name">
                        <i class="fas {icon}" style="color: {card_color}; margin-right: 0.5rem;"></i>
                        {agent.name}
                    </h4>
                    <p class="agent-type">{agent.metadata.get('type', 'Agent')}</p>
                </div>
                <div class="agent-status {status.value}">
                    {status.value.upper()}
                </div>
            </div>
            <div class="agent-metrics">
                <div class="metric-chip">
                    <i class="fas fa-tachometer-alt"></i>
                    {agent.metrics.get('load', MetricValue(0, '')).value}/{agent.metrics.get('capacity', MetricValue(10, '')).value}
                </div>
                <div class="metric-chip">
                    <i class="fas fa-clock"></i>
                    {agent.metrics.get('response_time', MetricValue(0, '')).value}ms
                </div>
            </div>
        </div>
        """

    @staticmethod
    def render_department_card(dept: EntityMetrics) -> str:
        """Render a department card"""
        return f"""
        <div class="department-card" style="border-left: 4px solid {dept.color};">
            <div class="dept-header">
                <div class="dept-icon" style="background: {dept.color};">
                    <i class="fas {dept.icon}"></i>
                </div>
                <div class="dept-info">
                    <h4>{dept.name}</h4>
                    <p>{dept.metrics.get('division', MetricValue('', '')).value}</p>
                </div>
            </div>
            <div class="dept-metrics">
                <div class="metric-row">
                    <span>Total Agents:</span>
                    <span>{dept.metrics.get('agents_total', MetricValue(0, '')).value}</span>
                </div>
                <div class="metric-row">
                    <span>Online:</span>
                    <span style="color: {BFColors.SUCCESS};">
                        {dept.metrics.get('agents_online', MetricValue(0, '')).value}
                    </span>
                </div>
            </div>
        </div>
        """


# Singleton instance
_metrics_calculator = None
_card_renderer = None


def get_metrics_calculator(
    db_config: Optional[Dict[str, Any]] = None
) -> MetricsCalculator:
    """Get or create metrics calculator instance"""
    global _metrics_calculator
    if _metrics_calculator is None:
        if db_config is None:
            db_config = {
                "host": "localhost",
                "port": 5434,
                "database": "boarderframeos",
                "user": "boarderframe",
                "password": "boarderframe_secure_2025",
            }
        _metrics_calculator = MetricsCalculator(db_config)
    return _metrics_calculator


def get_card_renderer() -> CardRenderer:
    """Get card renderer instance"""
    global _card_renderer
    if _card_renderer is None:
        _card_renderer = CardRenderer()
    return _card_renderer

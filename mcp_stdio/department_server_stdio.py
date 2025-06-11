#!/usr/bin/env python3
"""
MCP Department Server - stdio transport wrapper
Wraps the HTTP-based department server for use with Claude CLI
"""

import asyncio

# Handle MCP import conflicts by temporarily modifying sys.path
import importlib
import importlib.util
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Save original sys.path
original_path = sys.path.copy()

# Remove current and parent directories to avoid local mcp module conflicts
current_dir = str(Path(__file__).parent)
parent_dir = str(Path(__file__).parent.parent)
sys.path = [p for p in sys.path if p not in (current_dir, parent_dir, '')]

# Clear any cached local mcp modules
local_mcp_modules = [name for name in sys.modules.keys() if name.startswith('mcp')]
for module_name in local_mcp_modules:
    del sys.modules[module_name]

try:
    # Import the real MCP package
    import mcp.server.stdio
    from mcp import types
    from mcp.server import NotificationOptions, Server
    from mcp.server.models import InitializationOptions
finally:
    # Restore original sys.path
    sys.path = original_path

# Configure logging to file to avoid interfering with stdio
log_file = Path(__file__).parent / "department_stdio.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file)]
)
logger = logging.getLogger("department_stdio")

server = Server("department")

# Mock data for development - simplified department structure
departments = {
    "development": {
        "department_key": "development",
        "department_name": "Development",
        "category": "Technology",
        "description": "Software development and engineering",
        "is_active": True,
        "operational_status": "active",
        "agent_capacity": 50,
        "assigned_agents": 12,
        "active_agents": 10,
        "leaders": [{"name": "Bezalel", "title": "Master Programmer", "is_primary": True}],
        "native_agent_types": ["developer", "programmer", "architect"]
    },
    "sales": {
        "department_key": "sales",
        "department_name": "Sales",
        "category": "Business",
        "description": "Sales and revenue generation",
        "is_active": True,
        "operational_status": "active",
        "agent_capacity": 30,
        "assigned_agents": 8,
        "active_agents": 7,
        "leaders": [{"name": "Matthew", "title": "Sales Leader", "is_primary": True}],
        "native_agent_types": ["sales_agent", "account_manager"]
    },
    "support": {
        "department_key": "support",
        "department_name": "Customer Support",
        "category": "Service",
        "description": "Customer service and support",
        "is_active": True,
        "operational_status": "active",
        "agent_capacity": 25,
        "assigned_agents": 5,
        "active_agents": 4,
        "leaders": [{"name": "Ruth", "title": "Support Manager", "is_primary": True}],
        "native_agent_types": ["support_agent", "technical_support"]
    }
}

# Agent assignments tracking
agent_assignments = {}
assignment_history = []

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available department tools."""
    return [
        types.Tool(
            name="get_departments",
            description="Get all departments with their current status",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_inactive": {
                        "type": "boolean",
                        "description": "Include inactive departments",
                        "default": False
                    },
                    "division_key": {
                        "type": "string",
                        "description": "Filter by division (optional)"
                    }
                }
            }
        ),
        types.Tool(
            name="get_department_details",
            description="Get detailed information about a specific department",
            inputSchema={
                "type": "object",
                "properties": {
                    "department_key": {
                        "type": "string",
                        "description": "Department identifier"
                    }
                },
                "required": ["department_key"]
            }
        ),
        types.Tool(
            name="assign_agent",
            description="Assign an agent to a department",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Agent identifier"
                    },
                    "department_key": {
                        "type": "string",
                        "description": "Department identifier"
                    },
                    "assigned_by": {
                        "type": "string",
                        "description": "Who assigned the agent",
                        "default": "manual"
                    },
                    "assignment_type": {
                        "type": "string",
                        "description": "Type of assignment",
                        "default": "manual"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for assignment (optional)"
                    }
                },
                "required": ["agent_id", "department_key"]
            }
        ),
        types.Tool(
            name="deassign_agent",
            description="Deassign an agent from a department",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Agent identifier"
                    },
                    "department_key": {
                        "type": "string",
                        "description": "Department identifier (optional - if not provided, removes from all)"
                    },
                    "assigned_by": {
                        "type": "string",
                        "description": "Who deassigned the agent",
                        "default": "manual"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for deassignment (optional)"
                    }
                },
                "required": ["agent_id"]
            }
        ),
        types.Tool(
            name="transfer_agent",
            description="Transfer an agent from one department to another",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Agent identifier"
                    },
                    "from_department": {
                        "type": "string",
                        "description": "Source department"
                    },
                    "to_department": {
                        "type": "string",
                        "description": "Destination department"
                    },
                    "assigned_by": {
                        "type": "string",
                        "description": "Who transferred the agent",
                        "default": "manual"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for transfer (optional)"
                    }
                },
                "required": ["agent_id", "from_department", "to_department"]
            }
        ),
        types.Tool(
            name="get_agent_assignments",
            description="Get all assignments for a specific agent",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Agent identifier"
                    }
                },
                "required": ["agent_id"]
            }
        ),
        types.Tool(
            name="get_department_assignments",
            description="Get all agents assigned to a specific department",
            inputSchema={
                "type": "object",
                "properties": {
                    "department_key": {
                        "type": "string",
                        "description": "Department identifier"
                    },
                    "active_only": {
                        "type": "boolean",
                        "description": "Only return active assignments",
                        "default": True
                    }
                },
                "required": ["department_key"]
            }
        ),
        types.Tool(
            name="get_analytics_overview",
            description="Get high-level analytics about department assignments",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls."""
    try:
        if name == "get_departments":
            return await get_departments(arguments)
        elif name == "get_department_details":
            return await get_department_details(arguments)
        elif name == "assign_agent":
            return await assign_agent(arguments)
        elif name == "deassign_agent":
            return await deassign_agent(arguments)
        elif name == "transfer_agent":
            return await transfer_agent(arguments)
        elif name == "get_agent_assignments":
            return await get_agent_assignments(arguments)
        elif name == "get_department_assignments":
            return await get_department_assignments(arguments)
        elif name == "get_analytics_overview":
            return await get_analytics_overview()
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

async def get_departments(args: Dict[str, Any]) -> List[types.TextContent]:
    """Get all departments with their current status."""
    try:
        include_inactive = args.get("include_inactive", False)
        division_key = args.get("division_key")

        filtered_departments = []

        for dept in departments.values():
            if not include_inactive and not dept["is_active"]:
                continue

            # For simplicity, we're not filtering by division in mock data
            filtered_departments.append(dept)

        result = {
            "success": True,
            "departments": filtered_departments,
            "total_count": len(filtered_departments),
            "timestamp": datetime.now().isoformat()
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error getting departments: {str(e)}")]

async def get_department_details(args: Dict[str, Any]) -> List[types.TextContent]:
    """Get detailed information about a specific department."""
    try:
        department_key = args["department_key"]

        if department_key not in departments:
            result = {
                "success": False,
                "error": "Department not found",
                "department_key": department_key
            }
        else:
            dept = departments[department_key]

            # Add assignment details
            current_assignments = [
                assignment for assignment in agent_assignments.values()
                if assignment.get("department_key") == department_key and assignment.get("status") == "active"
            ]

            result = {
                "success": True,
                "department": {
                    **dept,
                    "current_assignments": current_assignments,
                    "metrics": {
                        "assigned_agents_count": len(current_assignments),
                        "active_agents_count": dept["active_agents"],
                        "productivity_score": 85.0,  # Mock metric
                        "health_score": 92.0,  # Mock metric
                        "status": "active",
                        "last_activity": datetime.now().isoformat()
                    }
                },
                "timestamp": datetime.now().isoformat()
            }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error getting department details: {str(e)}")]

async def assign_agent(args: Dict[str, Any]) -> List[types.TextContent]:
    """Assign an agent to a department."""
    try:
        agent_id = args["agent_id"]
        department_key = args["department_key"]
        assigned_by = args.get("assigned_by", "manual")
        assignment_type = args.get("assignment_type", "manual")
        reason = args.get("reason")

        if department_key not in departments:
            result = {
                "success": False,
                "error": "Department not found",
                "department_key": department_key
            }
        else:
            # Create assignment
            assignment = {
                "agent_id": agent_id,
                "department_key": department_key,
                "assigned_by": assigned_by,
                "assignment_type": assignment_type,
                "assigned_at": datetime.now().isoformat(),
                "status": "active",
                "reason": reason
            }

            agent_assignments[agent_id] = assignment

            # Add to history
            assignment_history.append({
                "action": "assigned",
                "agent_id": agent_id,
                "department_key": department_key,
                "assigned_by": assigned_by,
                "reason": reason,
                "created_at": datetime.now().isoformat()
            })

            # Update department assigned agents count
            departments[department_key]["assigned_agents"] += 1

            result = {
                "success": True,
                "message": f"Agent {agent_id} successfully assigned to {department_key}",
                "assignment": assignment,
                "timestamp": datetime.now().isoformat()
            }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error assigning agent: {str(e)}")]

async def deassign_agent(args: Dict[str, Any]) -> List[types.TextContent]:
    """Deassign an agent from a department."""
    try:
        agent_id = args["agent_id"]
        department_key = args.get("department_key")
        assigned_by = args.get("assigned_by", "manual")
        reason = args.get("reason")

        if agent_id not in agent_assignments:
            result = {
                "success": False,
                "error": "Agent assignment not found",
                "agent_id": agent_id
            }
        else:
            assignment = agent_assignments[agent_id]
            old_department = assignment["department_key"]

            # Check if specific department matches (if provided)
            if department_key and old_department != department_key:
                result = {
                    "success": False,
                    "error": f"Agent is not assigned to {department_key}",
                    "agent_id": agent_id,
                    "current_department": old_department
                }
            else:
                # Remove assignment
                assignment["status"] = "inactive"
                assignment["deassigned_at"] = datetime.now().isoformat()

                # Add to history
                assignment_history.append({
                    "action": "deassigned",
                    "agent_id": agent_id,
                    "department_key": old_department,
                    "assigned_by": assigned_by,
                    "reason": reason,
                    "created_at": datetime.now().isoformat()
                })

                # Update department assigned agents count
                departments[old_department]["assigned_agents"] -= 1

                result = {
                    "success": True,
                    "message": f"Agent {agent_id} successfully deassigned from {old_department}",
                    "deassignment": {
                        "agent_id": agent_id,
                        "department_key": old_department,
                        "deassigned_by": assigned_by,
                        "deassigned_at": datetime.now().isoformat(),
                        "reason": reason
                    },
                    "timestamp": datetime.now().isoformat()
                }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error deassigning agent: {str(e)}")]

async def transfer_agent(args: Dict[str, Any]) -> List[types.TextContent]:
    """Transfer an agent from one department to another."""
    try:
        agent_id = args["agent_id"]
        from_department = args["from_department"]
        to_department = args["to_department"]
        assigned_by = args.get("assigned_by", "manual")
        reason = args.get("reason")

        if from_department not in departments:
            result = {
                "success": False,
                "error": "Source department not found",
                "department_key": from_department
            }
        elif to_department not in departments:
            result = {
                "success": False,
                "error": "Destination department not found",
                "department_key": to_department
            }
        elif agent_id not in agent_assignments or agent_assignments[agent_id]["department_key"] != from_department:
            result = {
                "success": False,
                "error": f"Agent is not assigned to {from_department}",
                "agent_id": agent_id
            }
        else:
            # Update assignment
            assignment = agent_assignments[agent_id]
            assignment["department_key"] = to_department
            assignment["assigned_by"] = assigned_by
            assignment["transferred_at"] = datetime.now().isoformat()

            # Add to history
            assignment_history.append({
                "action": "transferred",
                "agent_id": agent_id,
                "from_department": from_department,
                "to_department": to_department,
                "assigned_by": assigned_by,
                "reason": reason,
                "created_at": datetime.now().isoformat()
            })

            # Update department counts
            departments[from_department]["assigned_agents"] -= 1
            departments[to_department]["assigned_agents"] += 1

            result = {
                "success": True,
                "message": f"Agent {agent_id} successfully transferred from {from_department} to {to_department}",
                "transfer": {
                    "agent_id": agent_id,
                    "from_department": from_department,
                    "to_department": to_department,
                    "transferred_by": assigned_by,
                    "transferred_at": datetime.now().isoformat(),
                    "reason": reason
                },
                "timestamp": datetime.now().isoformat()
            }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error transferring agent: {str(e)}")]

async def get_agent_assignments(args: Dict[str, Any]) -> List[types.TextContent]:
    """Get all assignments for a specific agent."""
    try:
        agent_id = args["agent_id"]

        assignments = []
        if agent_id in agent_assignments:
            assignments.append(agent_assignments[agent_id])

        result = {
            "success": True,
            "agent_id": agent_id,
            "assignments": assignments,
            "total_count": len(assignments),
            "timestamp": datetime.now().isoformat()
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error getting agent assignments: {str(e)}")]

async def get_department_assignments(args: Dict[str, Any]) -> List[types.TextContent]:
    """Get all agents assigned to a specific department."""
    try:
        department_key = args["department_key"]
        active_only = args.get("active_only", True)

        if department_key not in departments:
            result = {
                "success": False,
                "error": "Department not found",
                "department_key": department_key
            }
        else:
            assignments = []
            agent_ids = []

            for assignment in agent_assignments.values():
                if assignment["department_key"] == department_key:
                    if not active_only or assignment["status"] == "active":
                        assignments.append(assignment)
                        agent_ids.append(assignment["agent_id"])

            result = {
                "success": True,
                "department_key": department_key,
                "assignments": assignments,
                "agent_ids": agent_ids,
                "total_count": len(assignments),
                "timestamp": datetime.now().isoformat()
            }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error getting department assignments: {str(e)}")]

async def get_analytics_overview() -> List[types.TextContent]:
    """Get high-level analytics about department assignments."""
    try:
        total_depts = len([d for d in departments.values() if d["is_active"]])
        total_assignments = len([a for a in agent_assignments.values() if a["status"] == "active"])
        unique_agents = len(set(a["agent_id"] for a in agent_assignments.values() if a["status"] == "active"))

        # Active departments (those with assignments)
        active_depts = len(set(a["department_key"] for a in agent_assignments.values() if a["status"] == "active"))

        # Assignments by category
        category_counts = {}
        for assignment in agent_assignments.values():
            if assignment["status"] == "active":
                dept_key = assignment["department_key"]
                if dept_key in departments:
                    category = departments[dept_key]["category"]
                    category_counts[category] = category_counts.get(category, 0) + 1

        assignments_by_category = [
            {"category": cat, "assignment_count": count}
            for cat, count in category_counts.items()
        ]

        # Top departments by agent count
        dept_counts = {}
        for assignment in agent_assignments.values():
            if assignment["status"] == "active":
                dept_key = assignment["department_key"]
                dept_counts[dept_key] = dept_counts.get(dept_key, 0) + 1

        top_departments = [
            {
                "department_key": dept_key,
                "department_name": departments[dept_key]["department_name"],
                "agent_count": count
            }
            for dept_key, count in sorted(dept_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

        result = {
            "success": True,
            "overview": {
                "total_departments": total_depts,
                "active_departments": active_depts,
                "department_utilization": round((active_depts / max(total_depts, 1)) * 100, 2),
                "total_assignments": total_assignments,
                "unique_agents_assigned": unique_agents,
                "avg_assignments_per_department": round(total_assignments / max(total_depts, 1), 2)
            },
            "assignments_by_category": assignments_by_category,
            "top_departments": top_departments,
            "timestamp": datetime.now().isoformat()
        }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error getting analytics overview: {str(e)}")]

async def main():
    """Main entry point."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="department",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())

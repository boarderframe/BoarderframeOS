#!/usr/bin/env python3
"""
Department Management MCP Server
Provides tools for department management, agent assignments, and organizational structure
"""

import asyncio
import json
import logging

# Import our department registry integration
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import asyncpg
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

sys.path.append(str(Path(__file__).parent.parent))

from core.department_registry_integration import (
    DepartmentAPI,
    DepartmentRegistryManager,
)

logger = logging.getLogger(__name__)

# Pydantic models for API requests
class AgentAssignmentRequest(BaseModel):
    agent_id: str
    department_key: str
    assigned_by: str = "manual"
    reason: Optional[str] = None
    assignment_type: str = "manual"

class AgentDeassignmentRequest(BaseModel):
    agent_id: str
    department_key: Optional[str] = None
    assigned_by: str = "manual"
    reason: Optional[str] = None

class AgentTransferRequest(BaseModel):
    agent_id: str
    from_department: str
    to_department: str
    assigned_by: str = "manual"
    reason: Optional[str] = None

class DepartmentQuery(BaseModel):
    department_key: Optional[str] = None
    include_inactive: bool = False

class AgentQuery(BaseModel):
    agent_id: Optional[str] = None
    department_key: Optional[str] = None
    active_only: bool = True

# FastAPI app
app = FastAPI(
    title="Department Management Server",
    description="MCP server for department management and agent assignments",
    version="1.0.0"
)

# Global registry manager
registry_manager = None
department_api = None

@app.on_event("startup")
async def startup():
    """Initialize the department registry manager"""
    global registry_manager, department_api

    db_url = "postgresql://boarderframe:boarderframe_password@localhost:5432/boarderframe"
    registry_manager = DepartmentRegistryManager(db_url)
    await registry_manager.connect()
    department_api = DepartmentAPI(registry_manager)

    logger.info("Department Management Server started")

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    global registry_manager

    if registry_manager:
        await registry_manager.close()

    logger.info("Department Management Server stopped")

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "department_management",
        "timestamp": datetime.now().isoformat(),
        "database_connected": registry_manager.conn is not None
    }

# Division Management Endpoints
@app.get("/divisions")
async def get_divisions():
    """Get all divisions with their overview metrics"""
    try:
        divisions = await registry_manager.get_all_division_statuses()

        return {
            "success": True,
            "divisions": divisions,
            "total_count": len(divisions)
        }

    except Exception as e:
        logger.error(f"Failed to get divisions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Department Management Endpoints
@app.get("/departments")
async def get_departments(include_inactive: bool = False, division_key: str = None):
    """Get all departments with their current status, optionally filtered by division"""
    try:
        # Get department overview
        overview_result = await department_api.get_department_overview()
        if not overview_result['success']:
            raise HTTPException(status_code=500, detail=overview_result['error'])

        # Get detailed department information with division context
        query = """
            SELECT
                d.id, d.department_key, d.department_name, d.category,
                d.description, d.department_purpose, d.priority, d.is_active,
                d.operational_status, d.agent_capacity,
                div.division_name, div.division_key, div.priority as division_priority,
                COUNT(DISTINCT dl.id) as leaders_count,
                COUNT(DISTINCT dna.id) as native_agent_types_count
            FROM departments d
            LEFT JOIN divisions div ON d.division_id = div.id
            LEFT JOIN department_leaders dl ON d.id = dl.department_id AND dl.active_status = 'active'
            LEFT JOIN department_native_agents dna ON d.id = dna.department_id
        """

        where_conditions = []
        params = []
        param_count = 0

        if not include_inactive:
            where_conditions.append("d.is_active = true")

        if division_key:
            param_count += 1
            where_conditions.append(f"div.division_key = ${param_count}")
            params.append(division_key)

        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)

        query += """
            GROUP BY d.id, d.department_key, d.department_name, d.category,
                     d.description, d.department_purpose, d.priority, d.is_active,
                     d.operational_status, d.agent_capacity,
                     div.division_name, div.division_key, div.priority
            ORDER BY div.priority, d.priority, d.department_name
        """

        departments = await registry_manager.conn.fetch(query, *params)

        # Combine with status information
        department_statuses = overview_result['departments']

        result = []
        for dept in departments:
            dept_data = dict(dept)
            dept_key = dept['department_key']

            # Add status information if available
            if dept_key in department_statuses:
                dept_data.update(department_statuses[dept_key])
            else:
                dept_data.update({
                    'assigned_agents': 0,
                    'active_agents': 0,
                    'productivity_score': 0.0,
                    'health_score': 0.0,
                    'efficiency_score': 0.0,
                    'status': 'planning',
                    'last_activity': None
                })

            result.append(dept_data)

        return {
            "success": True,
            "departments": result,
            "total_count": len(result)
        }

    except Exception as e:
        logger.error(f"Failed to get departments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/departments/{department_key}")
async def get_department_details(department_key: str):
    """Get detailed information about a specific department"""
    try:
        # Get department basic info
        dept = await registry_manager.conn.fetchrow("""
            SELECT * FROM departments WHERE department_key = $1
        """, department_key)

        if not dept:
            raise HTTPException(status_code=404, detail="Department not found")

        # Get leaders
        leaders = await registry_manager.conn.fetch("""
            SELECT name, title, description, is_primary
            FROM department_leaders
            WHERE department_id = $1
            ORDER BY is_primary DESC, name
        """, dept['id'])

        # Get native agent types
        native_agents = await registry_manager.conn.fetch("""
            SELECT agent_type_name, agent_description
            FROM department_native_agents
            WHERE department_id = $1
            ORDER BY agent_type_name
        """, dept['id'])

        # Get current assignments
        assignments = await registry_manager.conn.fetch("""
            SELECT agent_id, assignment_type, assigned_by, assigned_at, assignment_status
            FROM agent_department_assignments
            WHERE department_id = $1
            ORDER BY assigned_at DESC
        """, dept['id'])

        # Get metrics
        metrics = await registry_manager.get_department_metrics(department_key)

        return {
            "success": True,
            "department": {
                **dict(dept),
                "leaders": [dict(leader) for leader in leaders],
                "native_agent_types": [dict(agent) for agent in native_agents],
                "current_assignments": [dict(assignment) for assignment in assignments],
                "metrics": {
                    "assigned_agents_count": metrics.assigned_agents_count if metrics else 0,
                    "active_agents_count": metrics.active_agents_count if metrics else 0,
                    "productivity_score": metrics.productivity_score if metrics else 0.0,
                    "health_score": metrics.health_score if metrics else 0.0,
                    "status": metrics.status.value if metrics else "inactive",
                    "last_activity": metrics.last_activity.isoformat() if metrics and metrics.last_activity else None
                }
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get department details for {department_key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Agent Assignment Endpoints
@app.post("/assignments")
async def assign_agent(request: AgentAssignmentRequest):
    """Manually assign an agent to a department"""
    try:
        success = await registry_manager.assign_agent_to_department(
            agent_id=request.agent_id,
            department_key=request.department_key,
            assigned_by=request.assigned_by,
            assignment_type=request.assignment_type,
            reason=request.reason
        )

        if success:
            return {
                "success": True,
                "message": f"Agent {request.agent_id} successfully assigned to {request.department_key}",
                "assignment": {
                    "agent_id": request.agent_id,
                    "department_key": request.department_key,
                    "assigned_by": request.assigned_by,
                    "assigned_at": datetime.now().isoformat(),
                    "assignment_type": request.assignment_type,
                    "reason": request.reason
                }
            }
        else:
            raise HTTPException(status_code=400, detail="Assignment failed")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to assign agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/assignments")
async def deassign_agent(request: AgentDeassignmentRequest):
    """Deassign an agent from a department"""
    try:
        success = await registry_manager.deassign_agent_from_department(
            agent_id=request.agent_id,
            department_key=request.department_key,
            assigned_by=request.assigned_by,
            reason=request.reason
        )

        if success:
            return {
                "success": True,
                "message": f"Agent {request.agent_id} successfully deassigned from {request.department_key or 'all departments'}",
                "deassignment": {
                    "agent_id": request.agent_id,
                    "department_key": request.department_key,
                    "deassigned_by": request.assigned_by,
                    "deassigned_at": datetime.now().isoformat(),
                    "reason": request.reason
                }
            }
        else:
            raise HTTPException(status_code=400, detail="Deassignment failed")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deassign agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/assignments/transfer")
async def transfer_agent(request: AgentTransferRequest):
    """Transfer an agent from one department to another"""
    try:
        success = await registry_manager.transfer_agent(
            agent_id=request.agent_id,
            from_department=request.from_department,
            to_department=request.to_department,
            assigned_by=request.assigned_by,
            reason=request.reason
        )

        if success:
            return {
                "success": True,
                "message": f"Agent {request.agent_id} successfully transferred from {request.from_department} to {request.to_department}",
                "transfer": {
                    "agent_id": request.agent_id,
                    "from_department": request.from_department,
                    "to_department": request.to_department,
                    "transferred_by": request.assigned_by,
                    "transferred_at": datetime.now().isoformat(),
                    "reason": request.reason
                }
            }
        else:
            raise HTTPException(status_code=400, detail="Transfer failed")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to transfer agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/assignments/agent/{agent_id}")
async def get_agent_assignments(agent_id: str):
    """Get all assignments for a specific agent"""
    try:
        assignments = await registry_manager.get_agent_assignments(agent_id)

        return {
            "success": True,
            "agent_id": agent_id,
            "assignments": [
                {
                    "department_id": assignment.department_id,
                    "department_key": assignment.department_key,
                    "assignment_type": assignment.assignment_type,
                    "assigned_by": assignment.assigned_by,
                    "assignment_status": assignment.assignment_status.value,
                    "assigned_at": assignment.assigned_at.isoformat(),
                    "metadata": assignment.metadata
                }
                for assignment in assignments
            ],
            "total_count": len(assignments)
        }

    except Exception as e:
        logger.error(f"Failed to get agent assignments for {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/assignments/department/{department_key}")
async def get_department_assignments(department_key: str, active_only: bool = True):
    """Get all agents assigned to a specific department"""
    try:
        agent_ids = await registry_manager.get_department_agents(department_key, active_only)

        # Get detailed assignment information
        status_filter = "AND ada.assignment_status = 'active'" if active_only else ""

        assignments = await registry_manager.conn.fetch(f"""
            SELECT
                ada.agent_id, ada.assignment_type, ada.assigned_by,
                ada.assigned_at, ada.assignment_status, ada.assignment_reason
            FROM agent_department_assignments ada
            JOIN departments d ON ada.department_id = d.id
            WHERE d.department_key = $1 {status_filter}
            ORDER BY ada.assigned_at DESC
        """, department_key)

        return {
            "success": True,
            "department_key": department_key,
            "assignments": [dict(assignment) for assignment in assignments],
            "agent_ids": agent_ids,
            "total_count": len(assignments)
        }

    except Exception as e:
        logger.error(f"Failed to get department assignments for {department_key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analytics and Reporting Endpoints
@app.get("/analytics/overview")
async def get_analytics_overview():
    """Get high-level analytics about department assignments"""
    try:
        # Total departments
        total_depts = await registry_manager.conn.fetchval(
            "SELECT COUNT(*) FROM departments WHERE is_active = true"
        )

        # Total assignments
        total_assignments = await registry_manager.conn.fetchval(
            "SELECT COUNT(*) FROM agent_department_assignments WHERE assignment_status = 'active'"
        )

        # Unique agents assigned
        unique_agents = await registry_manager.conn.fetchval(
            "SELECT COUNT(DISTINCT agent_id) FROM agent_department_assignments WHERE assignment_status = 'active'"
        )

        # Department utilization (departments with assignments)
        active_depts = await registry_manager.conn.fetchval("""
            SELECT COUNT(DISTINCT d.id)
            FROM departments d
            JOIN agent_department_assignments ada ON d.id = ada.department_id
            WHERE d.is_active = true AND ada.assignment_status = 'active'
        """)

        # Assignments by category
        assignments_by_category = await registry_manager.conn.fetch("""
            SELECT d.category, COUNT(ada.id) as assignment_count
            FROM departments d
            LEFT JOIN agent_department_assignments ada ON d.id = ada.department_id AND ada.assignment_status = 'active'
            WHERE d.is_active = true
            GROUP BY d.category
            ORDER BY assignment_count DESC
        """)

        # Top departments by agent count
        top_departments = await registry_manager.conn.fetch("""
            SELECT d.department_key, d.department_name, COUNT(ada.id) as agent_count
            FROM departments d
            LEFT JOIN agent_department_assignments ada ON d.id = ada.department_id AND ada.assignment_status = 'active'
            WHERE d.is_active = true
            GROUP BY d.id, d.department_key, d.department_name
            ORDER BY agent_count DESC
            LIMIT 10
        """)

        return {
            "success": True,
            "overview": {
                "total_departments": total_depts,
                "active_departments": active_depts,
                "department_utilization": round((active_depts / max(total_depts, 1)) * 100, 2),
                "total_assignments": total_assignments,
                "unique_agents_assigned": unique_agents,
                "avg_assignments_per_department": round(total_assignments / max(total_depts, 1), 2)
            },
            "assignments_by_category": [dict(row) for row in assignments_by_category],
            "top_departments": [dict(row) for row in top_departments]
        }

    except Exception as e:
        logger.error(f"Failed to get analytics overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/history")
async def get_assignment_history(
    agent_id: Optional[str] = None,
    department_key: Optional[str] = None,
    limit: int = 100
):
    """Get assignment history with optional filtering"""
    try:
        query = """
            SELECT
                dah.agent_id, d.department_key, d.department_name,
                dah.action, dah.assigned_by, dah.reason, dah.created_at,
                pd.department_key as previous_department_key
            FROM department_assignment_history dah
            JOIN departments d ON dah.department_id = d.id
            LEFT JOIN departments pd ON dah.previous_department_id = pd.id
            WHERE 1=1
        """
        params = []

        if agent_id:
            query += " AND dah.agent_id = $1"
            params.append(agent_id)

        if department_key:
            query += f" AND d.department_key = ${len(params) + 1}"
            params.append(department_key)

        query += f" ORDER BY dah.created_at DESC LIMIT ${len(params) + 1}"
        params.append(limit)

        history = await registry_manager.conn.fetch(query, *params)

        return {
            "success": True,
            "history": [dict(row) for row in history],
            "total_count": len(history)
        }

    except Exception as e:
        logger.error(f"Failed to get assignment history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Sync and Maintenance Endpoints
@app.post("/sync")
async def sync_with_registry():
    """Manually trigger synchronization with the central registry"""
    try:
        await registry_manager.sync_with_registry()

        return {
            "success": True,
            "message": "Synchronization completed successfully",
            "synced_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to sync with registry: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Department Management MCP Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8010, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info(f"Starting Department Management Server on {args.host}:{args.port}")
    uvicorn.run(
        "department_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )

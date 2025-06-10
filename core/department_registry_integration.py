#!/usr/bin/env python3
"""
Department Registry Integration
Handles live department assignments, status updates, and registry synchronization
"""

import asyncio
import asyncpg
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)

class AssignmentStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive" 
    PENDING = "pending"
    SUSPENDED = "suspended"

class DepartmentStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    DEGRADED = "degraded"

@dataclass
class AgentAssignment:
    agent_id: str
    department_id: int
    department_key: str
    assignment_type: str
    assigned_by: str
    assignment_status: AssignmentStatus
    assigned_at: datetime
    metadata: Dict[str, Any]

@dataclass
class DepartmentMetrics:
    department_id: int
    assigned_agents_count: int
    active_agents_count: int
    productivity_score: float
    health_score: float
    status: DepartmentStatus
    last_activity: Optional[datetime]
    metrics: Dict[str, Any]

class DepartmentRegistryManager:
    """
    Manages the integration between the department system and the agent registry.
    Handles live assignments, status updates, and synchronization.
    """
    
    def __init__(self, db_url: str = "postgresql://boarderframe:boarderframe_secure_2025@localhost:5434/boarderframeos", registry_url: str = "http://localhost:8000"):
        self.db_url = db_url
        self.registry_url = registry_url
        self.conn = None
        self._assignment_cache = {}
        self._department_cache = {}
        self._division_cache = {}
        self._last_sync = None
        
    async def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = await asyncpg.connect(self.db_url)
            logger.info("Department registry manager connected to database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def close(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()
            
    # Assignment Management
    async def assign_agent_to_department(
        self, 
        agent_id: str, 
        department_key: str, 
        assigned_by: str,
        assignment_type: str = "manual",
        reason: str = None,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Manually assign an agent to a department"""
        try:
            # Get department ID
            dept_id = await self.conn.fetchval(
                "SELECT id FROM departments WHERE department_key = $1 AND is_active = true",
                department_key
            )
            
            if not dept_id:
                logger.error(f"Department {department_key} not found or inactive")
                return False
            
            # Check if agent is already assigned to this department
            existing = await self.conn.fetchval("""
                SELECT id FROM agent_department_assignments 
                WHERE agent_id = $1 AND department_id = $2 AND assignment_status = 'active'
            """, agent_id, dept_id)
            
            if existing:
                logger.warning(f"Agent {agent_id} already assigned to department {department_key}")
                return False
            
            # Deactivate any existing assignments for this agent
            await self.conn.execute("""
                UPDATE agent_department_assignments 
                SET assignment_status = 'inactive', deassigned_at = CURRENT_TIMESTAMP
                WHERE agent_id = $1 AND assignment_status = 'active'
            """, agent_id)
            
            # Create new assignment
            assignment_id = await self.conn.fetchval("""
                INSERT INTO agent_department_assignments (
                    agent_id, department_id, assignment_type, assigned_by, 
                    assignment_status, assignment_reason
                ) VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """, agent_id, dept_id, assignment_type, assigned_by, 'active', reason)
            
            # Log to history
            await self.conn.execute("""
                INSERT INTO department_assignment_history (
                    agent_id, department_id, action, assigned_by, reason, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """, agent_id, dept_id, 'assigned', assigned_by, reason, json.dumps(metadata or {}))
            
            # Update registry
            await self._update_agent_registry(agent_id, department_key, 'assigned')
            
            # Update department status
            await self._refresh_department_status(dept_id)
            
            logger.info(f"Agent {agent_id} assigned to department {department_key} by {assigned_by}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to assign agent {agent_id} to department {department_key}: {e}")
            return False
    
    async def deassign_agent_from_department(
        self, 
        agent_id: str, 
        department_key: str = None,
        assigned_by: str = None,
        reason: str = None
    ) -> bool:
        """Deassign an agent from a department (or all departments)"""
        try:
            # Build query based on parameters
            if department_key:
                # Deassign from specific department
                dept_id = await self.conn.fetchval(
                    "SELECT id FROM departments WHERE department_key = $1",
                    department_key
                )
                if not dept_id:
                    logger.error(f"Department {department_key} not found")
                    return False
                
                # Update assignment
                updated = await self.conn.execute("""
                    UPDATE agent_department_assignments 
                    SET assignment_status = 'inactive', deassigned_at = CURRENT_TIMESTAMP
                    WHERE agent_id = $1 AND department_id = $2 AND assignment_status = 'active'
                """, agent_id, dept_id)
                
                if updated == 'UPDATE 0':
                    logger.warning(f"Agent {agent_id} not actively assigned to department {department_key}")
                    return False
                
                # Log to history
                await self.conn.execute("""
                    INSERT INTO department_assignment_history (
                        agent_id, department_id, action, assigned_by, reason
                    ) VALUES ($1, $2, $3, $4, $5)
                """, agent_id, dept_id, 'deassigned', assigned_by, reason)
                
                # Update department status
                await self._refresh_department_status(dept_id)
                
            else:
                # Deassign from all departments
                assignments = await self.conn.fetch("""
                    SELECT department_id FROM agent_department_assignments 
                    WHERE agent_id = $1 AND assignment_status = 'active'
                """, agent_id)
                
                # Update all assignments
                await self.conn.execute("""
                    UPDATE agent_department_assignments 
                    SET assignment_status = 'inactive', deassigned_at = CURRENT_TIMESTAMP
                    WHERE agent_id = $1 AND assignment_status = 'active'
                """, agent_id)
                
                # Log to history for each
                for assignment in assignments:
                    await self.conn.execute("""
                        INSERT INTO department_assignment_history (
                            agent_id, department_id, action, assigned_by, reason
                        ) VALUES ($1, $2, $3, $4, $5)
                    """, agent_id, assignment['department_id'], 'deassigned', assigned_by, reason)
                    
                    # Update department status
                    await self._refresh_department_status(assignment['department_id'])
            
            # Update registry
            await self._update_agent_registry(agent_id, None, 'deassigned')
            
            logger.info(f"Agent {agent_id} deassigned from {department_key or 'all departments'} by {assigned_by}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deassign agent {agent_id}: {e}")
            return False
    
    async def transfer_agent(
        self, 
        agent_id: str, 
        from_department: str, 
        to_department: str,
        assigned_by: str,
        reason: str = None
    ) -> bool:
        """Transfer an agent from one department to another"""
        try:
            # Get department IDs
            from_dept_id = await self.conn.fetchval(
                "SELECT id FROM departments WHERE department_key = $1", from_department
            )
            to_dept_id = await self.conn.fetchval(
                "SELECT id FROM departments WHERE department_key = $1 AND is_active = true", to_department
            )
            
            if not from_dept_id or not to_dept_id:
                logger.error(f"Invalid departments for transfer: {from_department} -> {to_department}")
                return False
            
            # Verify agent is currently assigned to from_department
            current_assignment = await self.conn.fetchval("""
                SELECT id FROM agent_department_assignments 
                WHERE agent_id = $1 AND department_id = $2 AND assignment_status = 'active'
            """, agent_id, from_dept_id)
            
            if not current_assignment:
                logger.error(f"Agent {agent_id} not currently assigned to {from_department}")
                return False
            
            # Perform transfer in transaction
            async with self.conn.transaction():
                # Deassign from old department
                await self.conn.execute("""
                    UPDATE agent_department_assignments 
                    SET assignment_status = 'inactive', deassigned_at = CURRENT_TIMESTAMP
                    WHERE id = $1
                """, current_assignment)
                
                # Assign to new department
                await self.conn.execute("""
                    INSERT INTO agent_department_assignments (
                        agent_id, department_id, assignment_type, assigned_by, 
                        assignment_status, assignment_reason
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                """, agent_id, to_dept_id, 'transfer', assigned_by, 'active', reason)
                
                # Log transfer to history
                await self.conn.execute("""
                    INSERT INTO department_assignment_history (
                        agent_id, department_id, action, previous_department_id, assigned_by, reason
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                """, agent_id, to_dept_id, 'transferred', from_dept_id, assigned_by, reason)
            
            # Update both department statuses
            await self._refresh_department_status(from_dept_id)
            await self._refresh_department_status(to_dept_id)
            
            # Update registry
            await self._update_agent_registry(agent_id, to_department, 'transferred')
            
            logger.info(f"Agent {agent_id} transferred from {from_department} to {to_department} by {assigned_by}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to transfer agent {agent_id}: {e}")
            return False
    
    # Status and Metrics Management
    async def _refresh_department_status(self, department_id: int):
        """Refresh department status and metrics"""
        try:
            # Get current assignment counts
            result = await self.conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_assigned,
                    COUNT(CASE WHEN assignment_status = 'active' THEN 1 END) as active_assigned
                FROM agent_department_assignments 
                WHERE department_id = $1
            """, department_id)
            
            total_assigned = result['total_assigned'] or 0
            active_assigned = result['active_assigned'] or 0
            
            # Calculate basic metrics
            health_score = min(1.0, active_assigned / max(1, total_assigned)) if total_assigned > 0 else 0.0
            productivity_score = 0.8 if active_assigned > 0 else 0.0  # Basic calculation
            
            # Determine status
            if active_assigned == 0:
                status = DepartmentStatus.INACTIVE
            elif active_assigned < total_assigned * 0.5:
                status = DepartmentStatus.DEGRADED
            else:
                status = DepartmentStatus.ACTIVE
            
            # Update department status
            await self.conn.execute("""
                INSERT INTO department_status (
                    department_id, assigned_agents_count, active_agents_count,
                    productivity_score, health_score, status, last_activity
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (department_id) DO UPDATE SET
                    assigned_agents_count = EXCLUDED.assigned_agents_count,
                    active_agents_count = EXCLUDED.active_agents_count,
                    productivity_score = EXCLUDED.productivity_score,
                    health_score = EXCLUDED.health_score,
                    status = EXCLUDED.status,
                    last_activity = EXCLUDED.last_activity,
                    updated_at = CURRENT_TIMESTAMP
            """, department_id, total_assigned, active_assigned, productivity_score, health_score, status.value, datetime.now())
            
        except Exception as e:
            logger.error(f"Failed to refresh department status for {department_id}: {e}")
    
    async def _update_agent_registry(self, agent_id: str, department_key: Optional[str], action: str):
        """Update agent registry with department assignment information"""
        try:
            # This would integrate with the actual registry system
            # For now, we'll log the action and store it locally
            
            registry_data = {
                'agent_id': agent_id,
                'department': department_key,
                'action': action,
                'timestamp': datetime.now().isoformat(),
                'source': 'department_manager'
            }
            
            # In a real implementation, this would make HTTP calls to the registry
            logger.info(f"Registry update: {json.dumps(registry_data)}")
            
            # Store in local cache for now
            self._assignment_cache[agent_id] = {
                'department': department_key,
                'last_updated': datetime.now(),
                'action': action
            }
            
        except Exception as e:
            logger.error(f"Failed to update agent registry for {agent_id}: {e}")
    
    # Query Methods
    async def get_agent_assignments(self, agent_id: str) -> List[AgentAssignment]:
        """Get all assignments for an agent"""
        try:
            rows = await self.conn.fetch("""
                SELECT 
                    ada.agent_id, ada.department_id, d.department_key,
                    ada.assignment_type, ada.assigned_by, ada.assignment_status,
                    ada.assigned_at, ada.assignment_reason as metadata
                FROM agent_department_assignments ada
                JOIN departments d ON ada.department_id = d.id
                WHERE ada.agent_id = $1
                ORDER BY ada.assigned_at DESC
            """, agent_id)
            
            return [
                AgentAssignment(
                    agent_id=row['agent_id'],
                    department_id=row['department_id'],
                    department_key=row['department_key'],
                    assignment_type=row['assignment_type'],
                    assigned_by=row['assigned_by'],
                    assignment_status=AssignmentStatus(row['assignment_status']),
                    assigned_at=row['assigned_at'],
                    metadata={'reason': row['metadata']}
                )
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"Failed to get agent assignments for {agent_id}: {e}")
            return []
    
    async def get_department_agents(self, department_key: str, active_only: bool = True) -> List[str]:
        """Get all agents assigned to a department"""
        try:
            status_filter = "AND ada.assignment_status = 'active'" if active_only else ""
            
            rows = await self.conn.fetch(f"""
                SELECT ada.agent_id
                FROM agent_department_assignments ada
                JOIN departments d ON ada.department_id = d.id
                WHERE d.department_key = $1 {status_filter}
                ORDER BY ada.assigned_at
            """, department_key)
            
            return [row['agent_id'] for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get department agents for {department_key}: {e}")
            return []
    
    async def get_department_metrics(self, department_key: str) -> Optional[DepartmentMetrics]:
        """Get current metrics for a department"""
        try:
            row = await self.conn.fetchrow("""
                SELECT 
                    ds.department_id, ds.assigned_agents_count, ds.active_agents_count,
                    ds.productivity_score, ds.health_score, ds.status, ds.last_activity, ds.metrics
                FROM department_status ds
                JOIN departments d ON ds.department_id = d.id
                WHERE d.department_key = $1
            """, department_key)
            
            if not row:
                return None
                
            return DepartmentMetrics(
                department_id=row['department_id'],
                assigned_agents_count=row['assigned_agents_count'],
                active_agents_count=row['active_agents_count'],
                productivity_score=row['productivity_score'],
                health_score=row['health_score'],
                status=DepartmentStatus(row['status']),
                last_activity=row['last_activity'],
                metrics=row['metrics'] or {}
            )
            
        except Exception as e:
            logger.error(f"Failed to get department metrics for {department_key}: {e}")
            return None
    
    async def get_all_department_statuses(self) -> Dict[str, DepartmentMetrics]:
        """Get status for all departments with division information"""
        try:
            rows = await self.conn.fetch("""
                SELECT 
                    d.department_key,
                    dp.department_id, dp.assigned_agents_count, dp.active_agents_count,
                    dp.productivity_score, dp.health_score, dp.status, dp.last_activity, dp.metrics,
                    div.division_name, div.division_key
                FROM departments d
                LEFT JOIN divisions div ON d.division_id = div.id
                LEFT JOIN department_performance dp ON d.id = dp.department_id
                WHERE d.is_active = true
                ORDER BY div.priority, d.priority, d.department_name
            """)
            
            result = {}
            for row in rows:
                if row['department_id']:  # Has status record
                    result[row['department_key']] = DepartmentMetrics(
                        department_id=row['department_id'],
                        assigned_agents_count=row['assigned_agents_count'] or 0,
                        active_agents_count=row['active_agents_count'] or 0,
                        productivity_score=row['productivity_score'] or 0.0,
                        health_score=row['health_score'] or 0.0,
                        status=DepartmentStatus(row['status']) if row['status'] else DepartmentStatus.INACTIVE,
                        last_activity=row['last_activity'],
                        metrics=row['metrics'] or {}
                    )
                else:  # No status record, create default
                    result[row['department_key']] = DepartmentMetrics(
                        department_id=str(row['department_id']) if row['department_id'] else None,
                        assigned_agents_count=0,
                        active_agents_count=0,
                        productivity_score=0.0,
                        health_score=0.0,
                        status=DepartmentStatus.INACTIVE,
                        last_activity=None,
                        metrics={}
                    )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get all department statuses: {e}")
            return {}
    
    async def get_all_division_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status overview for all divisions"""
        try:
            rows = await self.conn.fetch("""
                SELECT 
                    div.division_key,
                    div.division_name,
                    div.priority,
                    COUNT(DISTINCT d.id) as departments_count,
                    COUNT(DISTINCT dl.id) as leaders_count,
                    COUNT(DISTINCT ada.agent_id) as assigned_agents_count,
                    ROUND(AVG(dp.health_score), 2) as avg_health_score,
                    ROUND(AVG(dp.productivity_score), 2) as avg_productivity_score,
                    ROUND(AVG(dp.efficiency_score), 2) as avg_efficiency_score
                FROM divisions div
                LEFT JOIN departments d ON div.id = d.division_id AND d.is_active = true
                LEFT JOIN department_leaders dl ON d.id = dl.department_id AND dl.active_status = 'active'
                LEFT JOIN agent_department_assignments ada ON d.id = ada.department_id AND ada.assignment_status = 'active'
                LEFT JOIN department_performance dp ON d.id = dp.department_id
                WHERE div.is_active = true
                GROUP BY div.id, div.division_key, div.division_name, div.priority
                ORDER BY div.priority
            """)
            
            result = {}
            for row in rows:
                result[row['division_key']] = {
                    'division_name': row['division_name'],
                    'priority': row['priority'],
                    'departments_count': row['departments_count'] or 0,
                    'leaders_count': row['leaders_count'] or 0,
                    'assigned_agents_count': row['assigned_agents_count'] or 0,
                    'avg_health_score': float(row['avg_health_score']) if row['avg_health_score'] else 0.0,
                    'avg_productivity_score': float(row['avg_productivity_score']) if row['avg_productivity_score'] else 0.0,
                    'avg_efficiency_score': float(row['avg_efficiency_score']) if row['avg_efficiency_score'] else 0.0
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get all division statuses: {e}")
            return {}
    
    # Synchronization
    async def sync_with_registry(self):
        """Synchronize department assignments with the central registry"""
        try:
            # This would implement full synchronization with the registry
            # For now, we'll refresh all department statuses
            
            departments = await self.conn.fetch("SELECT id FROM departments WHERE is_active = true")
            
            for dept in departments:
                await self._refresh_department_status(dept['id'])
            
            self._last_sync = datetime.now()
            logger.info(f"Synchronized {len(departments)} departments with registry")
            
        except Exception as e:
            logger.error(f"Failed to sync with registry: {e}")

# Registry Integration API endpoints (for use in web server)
class DepartmentAPI:
    """API endpoints for department management"""
    
    def __init__(self, registry_manager: DepartmentRegistryManager):
        self.registry = registry_manager
    
    async def assign_agent(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """API endpoint to assign an agent to a department"""
        try:
            agent_id = request_data.get('agent_id')
            department_key = request_data.get('department_key')
            assigned_by = request_data.get('assigned_by', 'system')
            reason = request_data.get('reason')
            
            if not agent_id or not department_key:
                return {'success': False, 'error': 'Missing required fields'}
            
            success = await self.registry.assign_agent_to_department(
                agent_id, department_key, assigned_by, reason=reason
            )
            
            return {
                'success': success,
                'message': f'Agent {agent_id} assigned to {department_key}' if success else 'Assignment failed'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def get_department_overview(self) -> Dict[str, Any]:
        """API endpoint to get overview of all departments"""
        try:
            statuses = await self.registry.get_all_department_statuses()
            
            # Convert to serializable format
            overview = {}
            for dept_key, metrics in statuses.items():
                overview[dept_key] = {
                    'assigned_agents': metrics.assigned_agents_count,
                    'active_agents': metrics.active_agents_count,
                    'productivity_score': metrics.productivity_score,
                    'health_score': metrics.health_score,
                    'status': metrics.status.value,
                    'last_activity': metrics.last_activity.isoformat() if metrics.last_activity else None
                }
            
            return {'success': True, 'departments': overview}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
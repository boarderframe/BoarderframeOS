"""
Agent Teams - CrewAI-style role-based agent teams with delegation
Enables sophisticated multi-agent collaboration patterns
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from .agent_workflows import WorkflowConfig, workflow_orchestrator
from .enhanced_agent_base import EnhancedAgentConfig, EnhancedBaseAgent
from .message_bus import MessagePriority, message_bus


class TeamRole(Enum):
    """Standard team roles"""

    MANAGER = "manager"
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    EXECUTOR = "executor"
    REVIEWER = "reviewer"
    SPECIALIST = "specialist"
    COORDINATOR = "coordinator"


@dataclass
class TeamMember:
    """Represents a team member with specific role and capabilities"""

    agent_name: str
    role: TeamRole
    responsibilities: List[str]
    skills: List[str]
    delegation_authority: bool = False
    max_concurrent_tasks: int = 3
    current_tasks: List[str] = field(default_factory=list)


@dataclass
class TeamTask:
    """Represents a task assigned to the team"""

    task_id: str
    description: str
    requirements: List[str]
    assigned_to: Optional[str] = None
    status: str = "pending"
    priority: MessagePriority = MessagePriority.NORMAL
    deadline: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


@dataclass
class TeamConfig:
    """Configuration for an agent team"""

    name: str
    description: str
    goal: str
    members: List[TeamMember]
    manager: str  # Agent name of team manager
    max_team_size: int = 10
    enable_dynamic_roles: bool = True
    enable_skill_learning: bool = True
    communication_style: str = "collaborative"  # collaborative, hierarchical, flat


class AgentTeam:
    """CrewAI-style agent team with role-based collaboration"""

    def __init__(self, config: TeamConfig):
        self.config = config
        self.team_id = str(uuid4())
        self.logger = logging.getLogger(f"Team-{config.name}")

        # Team state
        self.members: Dict[str, TeamMember] = {
            member.agent_name: member for member in config.members
        }
        self.tasks: Dict[str, TeamTask] = {}
        self.team_memory: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, Any] = {
            "tasks_completed": 0,
            "average_completion_time": 0,
            "success_rate": 0,
            "collaboration_score": 0,
        }

        # Communication channels
        self.team_channel = f"team-{self.team_id}"
        self._initialized = False

    async def initialize(self):
        """Initialize the team"""
        if self._initialized:
            return

        try:
            # Register team channel with message bus
            await message_bus.register_agent(self.team_channel)

            # Subscribe all team members to team channel
            for member_name in self.members:
                await message_bus.subscribe_to_topic(member_name, self.team_channel)

            self._initialized = True
            self.logger.info(
                f"Team {self.config.name} initialized with {len(self.members)} members"
            )

        except Exception as e:
            self.logger.error(f"Failed to initialize team: {e}")
            raise

    async def assign_task(
        self,
        task_description: str,
        requirements: List[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        deadline: Optional[datetime] = None,
    ) -> str:
        """Assign a task to the team"""
        task = TeamTask(
            task_id=str(uuid4()),
            description=task_description,
            requirements=requirements or [],
            priority=priority,
            deadline=deadline,
        )

        self.tasks[task.task_id] = task

        # Determine best team member for the task
        assigned_member = await self._find_best_member_for_task(task)

        if assigned_member:
            task.assigned_to = assigned_member
            await self._assign_task_to_member(task, assigned_member)
        else:
            # Assign to manager for delegation
            task.assigned_to = self.config.manager
            await self._assign_task_to_member(task, self.config.manager)

        return task.task_id

    async def _find_best_member_for_task(self, task: TeamTask) -> Optional[str]:
        """Find the best team member for a task based on skills and availability"""
        best_member = None
        best_score = -1

        for member_name, member in self.members.items():
            # Skip if member is at capacity
            if len(member.current_tasks) >= member.max_concurrent_tasks:
                continue

            # Calculate fitness score
            score = 0

            # Check skill match
            for requirement in task.requirements:
                if requirement.lower() in [skill.lower() for skill in member.skills]:
                    score += 10

            # Check responsibility match
            for responsibility in member.responsibilities:
                if any(req in responsibility for req in task.requirements):
                    score += 5

            # Prefer specialists for specialized tasks
            if member.role == TeamRole.SPECIALIST and task.requirements:
                score += 3

            # Consider current workload
            score -= len(member.current_tasks) * 2

            if score > best_score:
                best_score = score
                best_member = member_name

        return best_member

    async def _assign_task_to_member(self, task: TeamTask, member_name: str):
        """Assign a task to a specific team member"""
        member = self.members.get(member_name)
        if not member:
            self.logger.error(f"Member {member_name} not found in team")
            return

        # Update member's current tasks
        member.current_tasks.append(task.task_id)

        # Send task assignment via message bus
        assignment_message = {
            "from_agent": self.team_channel,
            "to_agent": member_name,
            "message_type": "task_request",
            "content": {
                "task_id": task.task_id,
                "description": task.description,
                "requirements": task.requirements,
                "team_context": {
                    "team_name": self.config.name,
                    "team_goal": self.config.goal,
                    "your_role": member.role.value,
                    "delegation_allowed": member.delegation_authority,
                },
            },
            "priority": task.priority,
            "correlation_id": task.task_id,
        }

        await message_bus.send_message(assignment_message)

        # Record in team memory
        self.team_memory.append(
            {
                "timestamp": datetime.now().isoformat(),
                "event": "task_assigned",
                "task_id": task.task_id,
                "assigned_to": member_name,
                "description": task.description,
            }
        )

        self.logger.info(f"Task {task.task_id} assigned to {member_name}")

    async def delegate_task(
        self, task_id: str, from_member: str, to_member: str, reason: str
    ):
        """Delegate a task from one member to another"""
        task = self.tasks.get(task_id)
        if not task:
            self.logger.error(f"Task {task_id} not found")
            return False

        from_agent = self.members.get(from_member)
        to_agent = self.members.get(to_member)

        if not from_agent or not to_agent:
            self.logger.error("Invalid delegation: member not found")
            return False

        # Check delegation authority
        if not from_agent.delegation_authority and from_member != self.config.manager:
            self.logger.warning(f"{from_member} does not have delegation authority")
            return False

        # Update task assignment
        if task_id in from_agent.current_tasks:
            from_agent.current_tasks.remove(task_id)

        task.assigned_to = to_member
        to_agent.current_tasks.append(task_id)

        # Notify the new assignee
        await self._assign_task_to_member(task, to_member)

        # Record delegation
        self.team_memory.append(
            {
                "timestamp": datetime.now().isoformat(),
                "event": "task_delegated",
                "task_id": task_id,
                "from": from_member,
                "to": to_member,
                "reason": reason,
            }
        )

        return True

    async def report_task_progress(
        self,
        task_id: str,
        member_name: str,
        status: str,
        results: Dict[str, Any] = None,
    ):
        """Report progress on a task"""
        task = self.tasks.get(task_id)
        if not task:
            return

        task.status = status
        if results:
            task.results.update(results)

        if status == "completed":
            task.completed_at = datetime.now()
            member = self.members.get(member_name)
            if member and task_id in member.current_tasks:
                member.current_tasks.remove(task_id)

            # Update metrics
            self.performance_metrics["tasks_completed"] += 1

            # Calculate completion time
            if task.created_at:
                completion_time = (task.completed_at - task.created_at).total_seconds()
                current_avg = self.performance_metrics["average_completion_time"]
                completed = self.performance_metrics["tasks_completed"]
                new_avg = (
                    (current_avg * (completed - 1)) + completion_time
                ) / completed
                self.performance_metrics["average_completion_time"] = new_avg

        # Broadcast status to team
        await self._broadcast_to_team(
            {
                "event": "task_update",
                "task_id": task_id,
                "status": status,
                "member": member_name,
                "results": results,
            }
        )

    async def collaborate_on_task(
        self, task_id: str, requesting_member: str, required_skills: List[str]
    ) -> List[str]:
        """Find team members to collaborate on a task"""
        collaborators = []
        task = self.tasks.get(task_id)

        if not task:
            return collaborators

        for member_name, member in self.members.items():
            if member_name == requesting_member:
                continue

            # Check if member has required skills
            if any(skill in member.skills for skill in required_skills):
                # Check availability
                if len(member.current_tasks) < member.max_concurrent_tasks:
                    collaborators.append(member_name)

        # Notify collaborators
        for collaborator in collaborators:
            await message_bus.send_message(
                {
                    "from_agent": requesting_member,
                    "to_agent": collaborator,
                    "message_type": "coordination",
                    "content": {
                        "request": "collaborate",
                        "task_id": task_id,
                        "task_description": task.description,
                        "required_skills": required_skills,
                        "requester": requesting_member,
                    },
                    "priority": MessagePriority.HIGH,
                }
            )

        return collaborators

    async def conduct_team_review(self, task_id: str) -> Dict[str, Any]:
        """Conduct a team review of completed task"""
        task = self.tasks.get(task_id)
        if not task or task.status != "completed":
            return {"error": "Task not found or not completed"}

        reviewers = []
        for member_name, member in self.members.items():
            if member.role == TeamRole.REVIEWER or member.role == TeamRole.MANAGER:
                reviewers.append(member_name)

        review_results = []

        # Request reviews from all reviewers
        for reviewer in reviewers:
            review_request = {
                "from_agent": self.team_channel,
                "to_agent": reviewer,
                "message_type": "task_request",
                "content": {
                    "action": "review_task",
                    "task_id": task_id,
                    "task_results": task.results,
                    "task_description": task.description,
                    "completed_by": task.assigned_to,
                },
                "priority": MessagePriority.NORMAL,
                "correlation_id": f"review-{task_id}-{reviewer}",
            }

            await message_bus.send_message(review_request)

            # Wait for review response
            try:
                response = await asyncio.wait_for(
                    message_bus.wait_for_response(review_request["correlation_id"]),
                    timeout=30,
                )
                if response:
                    review_results.append(
                        {"reviewer": reviewer, "feedback": response.content}
                    )
            except asyncio.TimeoutError:
                self.logger.warning(f"Review timeout from {reviewer}")

        # Aggregate reviews
        return {
            "task_id": task_id,
            "reviews": review_results,
            "consensus": self._calculate_review_consensus(review_results),
        }

    def _calculate_review_consensus(self, reviews: List[Dict[str, Any]]) -> str:
        """Calculate consensus from multiple reviews"""
        if not reviews:
            return "no_reviews"

        # Simple consensus calculation (can be enhanced)
        positive_reviews = sum(
            1 for review in reviews if review.get("feedback", {}).get("approval", False)
        )

        if positive_reviews == len(reviews):
            return "unanimous_approval"
        elif positive_reviews > len(reviews) / 2:
            return "majority_approval"
        elif positive_reviews > 0:
            return "mixed_feedback"
        else:
            return "needs_improvement"

    async def _broadcast_to_team(self, message: Dict[str, Any]):
        """Broadcast a message to all team members"""
        broadcast_msg = {
            "from_agent": self.team_channel,
            "to_agent": "broadcast",
            "message_type": "coordination",
            "content": {
                "team_id": self.team_id,
                "team_name": self.config.name,
                **message,
            },
            "priority": MessagePriority.NORMAL,
        }

        # Send to each team member
        for member_name in self.members:
            broadcast_msg["to_agent"] = member_name
            await message_bus.send_message(broadcast_msg)

    def get_team_status(self) -> Dict[str, Any]:
        """Get current team status"""
        active_tasks = [
            task
            for task in self.tasks.values()
            if task.status not in ["completed", "cancelled"]
        ]

        member_workloads = {
            member_name: {
                "current_tasks": len(member.current_tasks),
                "capacity": member.max_concurrent_tasks,
                "utilization": len(member.current_tasks) / member.max_concurrent_tasks,
            }
            for member_name, member in self.members.items()
        }

        return {
            "team_id": self.team_id,
            "name": self.config.name,
            "goal": self.config.goal,
            "members": len(self.members),
            "active_tasks": len(active_tasks),
            "completed_tasks": self.performance_metrics["tasks_completed"],
            "average_completion_time": self.performance_metrics[
                "average_completion_time"
            ],
            "member_workloads": member_workloads,
            "team_health": self._calculate_team_health(),
        }

    def _calculate_team_health(self) -> str:
        """Calculate overall team health"""
        # Calculate average utilization
        total_utilization = sum(
            len(member.current_tasks) / member.max_concurrent_tasks
            for member in self.members.values()
        )
        avg_utilization = total_utilization / len(self.members) if self.members else 0

        if avg_utilization < 0.3:
            return "underutilized"
        elif avg_utilization < 0.7:
            return "healthy"
        elif avg_utilization < 0.9:
            return "busy"
        else:
            return "overloaded"


class TeamFormation:
    """Handles dynamic team formation based on requirements"""

    def __init__(self):
        self.teams: Dict[str, AgentTeam] = {}
        self.available_agents: Set[str] = set()
        self.agent_skills: Dict[str, List[str]] = {}
        self.logger = logging.getLogger("TeamFormation")

    def register_agent(self, agent_name: str, skills: List[str]):
        """Register an agent as available for team formation"""
        self.available_agents.add(agent_name)
        self.agent_skills[agent_name] = skills
        self.logger.info(f"Registered agent {agent_name} with skills: {skills}")

    async def form_team(
        self, goal: str, required_skills: List[str], team_size: int = 5
    ) -> Optional[AgentTeam]:
        """Form a team based on requirements"""
        # Find agents with required skills
        candidates = []

        for agent_name in self.available_agents:
            agent_skills = self.agent_skills.get(agent_name, [])
            skill_match = sum(1 for skill in required_skills if skill in agent_skills)

            if skill_match > 0:
                candidates.append((agent_name, skill_match, agent_skills))

        # Sort by skill match
        candidates.sort(key=lambda x: x[1], reverse=True)

        if len(candidates) < 2:  # Need at least 2 members
            self.logger.warning("Not enough qualified agents for team formation")
            return None

        # Select team members
        selected_members = []
        selected_names = set()

        # Always need a manager
        manager_name = candidates[0][0]
        selected_members.append(
            TeamMember(
                agent_name=manager_name,
                role=TeamRole.MANAGER,
                responsibilities=[
                    "Team coordination",
                    "Task delegation",
                    "Decision making",
                ],
                skills=candidates[0][2],
                delegation_authority=True,
            )
        )
        selected_names.add(manager_name)

        # Add other members based on skills
        for agent_name, _, skills in candidates[1:]:
            if len(selected_members) >= team_size:
                break

            if agent_name not in selected_names:
                # Determine role based on skills
                role = self._determine_role(skills, required_skills)

                selected_members.append(
                    TeamMember(
                        agent_name=agent_name,
                        role=role,
                        responsibilities=self._get_role_responsibilities(role),
                        skills=skills,
                        delegation_authority=(role == TeamRole.COORDINATOR),
                    )
                )
                selected_names.add(agent_name)

        # Create team configuration
        team_config = TeamConfig(
            name=f"Team-{goal[:20]}",
            description=f"Dynamic team formed for: {goal}",
            goal=goal,
            members=selected_members,
            manager=manager_name,
        )

        # Create and initialize team
        team = AgentTeam(team_config)
        await team.initialize()

        self.teams[team.team_id] = team

        # Mark agents as unavailable
        for member in selected_members:
            self.available_agents.discard(member.agent_name)

        self.logger.info(
            f"Formed team {team.team_id} with {len(selected_members)} members"
        )
        return team

    def _determine_role(
        self, agent_skills: List[str], required_skills: List[str]
    ) -> TeamRole:
        """Determine best role for agent based on skills"""
        # Simple role assignment logic (can be enhanced)
        if "research" in agent_skills or "analysis" in agent_skills:
            return TeamRole.RESEARCHER
        elif "planning" in agent_skills or "strategy" in agent_skills:
            return TeamRole.ANALYST
        elif "implementation" in agent_skills or "execution" in agent_skills:
            return TeamRole.EXECUTOR
        elif "review" in agent_skills or "quality" in agent_skills:
            return TeamRole.REVIEWER
        elif any(skill in required_skills for skill in agent_skills):
            return TeamRole.SPECIALIST
        else:
            return TeamRole.COORDINATOR

    def _get_role_responsibilities(self, role: TeamRole) -> List[str]:
        """Get standard responsibilities for a role"""
        responsibilities_map = {
            TeamRole.MANAGER: [
                "Team coordination",
                "Task delegation",
                "Decision making",
            ],
            TeamRole.RESEARCHER: [
                "Information gathering",
                "Research tasks",
                "Data collection",
            ],
            TeamRole.ANALYST: [
                "Data analysis",
                "Pattern recognition",
                "Insights generation",
            ],
            TeamRole.EXECUTOR: [
                "Task implementation",
                "Action execution",
                "Result delivery",
            ],
            TeamRole.REVIEWER: [
                "Quality assurance",
                "Result validation",
                "Feedback provision",
            ],
            TeamRole.SPECIALIST: [
                "Domain expertise",
                "Specialized tasks",
                "Technical guidance",
            ],
            TeamRole.COORDINATOR: [
                "Inter-team communication",
                "Resource coordination",
                "Support tasks",
            ],
        }

        return responsibilities_map.get(role, ["General support", "Task assistance"])

    async def dissolve_team(self, team_id: str):
        """Dissolve a team and return agents to available pool"""
        team = self.teams.get(team_id)
        if not team:
            return

        # Return agents to available pool
        for member_name in team.members:
            self.available_agents.add(member_name)

        # Clean up team
        del self.teams[team_id]

        self.logger.info(f"Dissolved team {team_id}")


# Global team formation manager
team_formation = TeamFormation()


# Pre-defined team templates
TEAM_TEMPLATES = {
    "customer_support": {
        "goal": "Provide excellent customer support",
        "required_skills": ["customer_service", "problem_solving", "communication"],
        "ideal_size": 4,
    },
    "product_development": {
        "goal": "Develop new product features",
        "required_skills": ["programming", "design", "testing", "planning"],
        "ideal_size": 6,
    },
    "revenue_optimization": {
        "goal": "Optimize revenue streams",
        "required_skills": ["analytics", "finance", "marketing", "strategy"],
        "ideal_size": 5,
    },
    "system_maintenance": {
        "goal": "Maintain system health and performance",
        "required_skills": [
            "monitoring",
            "debugging",
            "optimization",
            "infrastructure",
        ],
        "ideal_size": 4,
    },
}

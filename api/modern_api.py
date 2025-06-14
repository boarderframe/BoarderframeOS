"""
Modern API Backend - FastAPI server with REST and GraphQL support
Provides enhanced API layer while maintaining compatibility with existing systems
"""

import asyncio
import json
import logging
import os

# Import core components
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx
import strawberry
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from strawberry.fastapi import GraphQLRouter

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent_teams import TeamRole, team_formation
from core.agent_workflows import (
    WORKFLOW_TEMPLATES,
    WorkflowConfig,
    workflow_orchestrator,
)
from core.enhanced_agent_base import EnhancedAgentConfig
from core.message_bus import MessagePriority, message_bus


# Pydantic models for request/response
class AgentStatus(BaseModel):
    agent_id: str
    name: str
    status: str
    current_tasks: int
    performance_metrics: Dict[str, Any]
    last_heartbeat: Optional[datetime]


class TaskRequest(BaseModel):
    description: str
    agent_id: Optional[str] = None
    team_id: Optional[str] = None
    priority: str = "normal"
    requirements: List[str] = Field(default_factory=list)
    deadline: Optional[datetime] = None


class TaskResponse(BaseModel):
    task_id: str
    status: str
    assigned_to: Optional[str]
    created_at: datetime


class TeamFormationRequest(BaseModel):
    goal: str
    required_skills: List[str]
    team_size: int = 5


class ChatMessage(BaseModel):
    agent_id: str
    message: str
    context: Optional[Dict[str, Any]] = None


class WorkflowRequest(BaseModel):
    workflow_type: str
    initial_context: Dict[str, Any]
    starting_agent: str


# GraphQL schema
@strawberry.type
class Agent:
    id: str
    name: str
    role: str
    status: str
    department: str
    skills: List[str]
    current_tasks: int

    @strawberry.field
    async def performance_metrics(self) -> Dict[str, Any]:
        # Fetch real-time metrics
        return {}


@strawberry.type
class Team:
    id: str
    name: str
    goal: str
    members: List[Agent]
    active_tasks: int
    health: str


@strawberry.type
class Workflow:
    id: str
    name: str
    status: str
    current_step: str
    progress: float


@strawberry.type
class Query:
    @strawberry.field
    async def agents(self) -> List[Agent]:
        # Fetch from database
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8010/agents")
            if response.status_code == 200:
                data = response.json()
                return [
                    Agent(
                        id=agent["id"],
                        name=agent["name"],
                        role=agent.get("role", ""),
                        status=agent.get("status", "active"),
                        department=agent.get("department", ""),
                        skills=agent.get("skills", []),
                        current_tasks=0,
                    )
                    for agent in data.get("agents", [])
                ]
        return []

    @strawberry.field
    async def teams(self) -> List[Team]:
        # Get active teams
        teams = []
        for team_id, team in team_formation.teams.items():
            status = team.get_team_status()
            teams.append(
                Team(
                    id=team_id,
                    name=team.config.name,
                    goal=team.config.goal,
                    members=[],  # Would fetch member details
                    active_tasks=status["active_tasks"],
                    health=status["team_health"],
                )
            )
        return teams

    @strawberry.field
    async def workflows(self) -> List[Workflow]:
        # Get workflow status
        workflows = []
        for workflow_id in workflow_orchestrator.workflows:
            status = workflow_orchestrator.get_workflow_status(workflow_id)
            workflows.append(
                Workflow(
                    id=workflow_id,
                    name=workflow_id,  # Would get from config
                    status=status["status"],
                    current_step="",
                    progress=0.0,
                )
            )
        return workflows


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_team(
        self, goal: str, required_skills: List[str], team_size: int = 5
    ) -> Team:
        team = await team_formation.form_team(goal, required_skills, team_size)
        if team:
            return Team(
                id=team.team_id,
                name=team.config.name,
                goal=team.config.goal,
                members=[],
                active_tasks=0,
                health="healthy",
            )
        raise Exception("Failed to form team")

    @strawberry.mutation
    async def start_workflow(
        self, workflow_type: str, context: Dict[str, Any], starting_agent: str
    ) -> Workflow:
        if workflow_type not in WORKFLOW_TEMPLATES:
            raise Exception(f"Unknown workflow type: {workflow_type}")

        config = WORKFLOW_TEMPLATES[workflow_type]
        workflow = workflow_orchestrator.create_workflow(config)

        # Start workflow asynchronously
        asyncio.create_task(
            workflow_orchestrator.run_workflow(
                workflow.workflow_id, context, starting_agent
            )
        )

        return Workflow(
            id=workflow.workflow_id,
            name=config.name,
            status="running",
            current_step=config.steps[0]["name"] if config.steps else "",
            progress=0.0,
        )


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)

    def disconnect(self, websocket: WebSocket, client_id: str):
        if client_id in self.active_connections:
            self.active_connections[client_id].remove(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            for connection in self.active_connections[client_id]:
                await connection.send_text(message)

    async def broadcast(self, message: str, exclude: Optional[str] = None):
        for client_id, connections in self.active_connections.items():
            if client_id != exclude:
                for connection in connections:
                    await connection.send_text(message)


manager = ConnectionManager()


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logging.info("Starting Modern API server...")

    # Initialize message bus connection
    await message_bus.start()

    # Register API as an agent
    await message_bus.register_agent("modern_api")

    yield

    # Shutdown
    logging.info("Shutting down Modern API server...")
    await message_bus.stop()


# Create FastAPI app
app = FastAPI(
    title="BoarderframeOS Modern API",
    description="Enhanced API with REST, GraphQL, and WebSocket support",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GraphQL router
schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")


# REST API Endpoints


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "message_bus": "connected",
            "database": "connected",  # Would check actual connection
            "websocket": "active",
        },
    }


@app.get("/api/v1/agents", response_model=List[AgentStatus])
async def get_agents():
    """Get all agents with their current status"""
    try:
        # Fetch from PostgreSQL via MCP
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8010/query",
                json={"sql": "SELECT * FROM agents WHERE status = 'active'"},
            )

            if response.status_code == 200:
                data = response.json()
                agents = []

                for row in data.get("data", []):
                    agents.append(
                        AgentStatus(
                            agent_id=row["id"],
                            name=row["name"],
                            status=row["status"],
                            current_tasks=0,  # Would fetch from orchestrator
                            performance_metrics={},
                            last_heartbeat=row.get("last_seen"),
                        )
                    )

                return agents
    except Exception as e:
        logging.error(f"Failed to fetch agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch agents")


@app.post("/api/v1/tasks", response_model=TaskResponse)
async def create_task(task: TaskRequest):
    """Create a new task for an agent or team"""
    try:
        task_id = str(uuid4())

        if task.team_id:
            # Assign to team
            team = team_formation.teams.get(task.team_id)
            if not team:
                raise HTTPException(status_code=404, detail="Team not found")

            assigned_task_id = await team.assign_task(
                task.description,
                task.requirements,
                MessagePriority[task.priority.upper()],
                task.deadline,
            )

            return TaskResponse(
                task_id=assigned_task_id,
                status="assigned",
                assigned_to=task.team_id,
                created_at=datetime.now(),
            )

        elif task.agent_id:
            # Direct agent assignment
            # Would use orchestrator to assign task
            return TaskResponse(
                task_id=task_id,
                status="assigned",
                assigned_to=task.agent_id,
                created_at=datetime.now(),
            )

        else:
            # Auto-assign based on requirements
            # Would use intelligent routing
            return TaskResponse(
                task_id=task_id,
                status="pending",
                assigned_to=None,
                created_at=datetime.now(),
            )

    except Exception as e:
        logging.error(f"Failed to create task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/teams")
async def create_team(request: TeamFormationRequest):
    """Form a new agent team"""
    try:
        team = await team_formation.form_team(
            request.goal, request.required_skills, request.team_size
        )

        if not team:
            raise HTTPException(
                status_code=400, detail="Unable to form team with available agents"
            )

        return {
            "team_id": team.team_id,
            "name": team.config.name,
            "members": [
                {
                    "agent": member.agent_name,
                    "role": member.role.value,
                    "skills": member.skills,
                }
                for member in team.members.values()
            ],
        }

    except Exception as e:
        logging.error(f"Failed to create team: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/chat")
async def send_chat_message(message: ChatMessage):
    """Send a chat message to an agent"""
    try:
        # Send via message bus
        await message_bus.send_message(
            {
                "from_agent": "modern_api",
                "to_agent": message.agent_id,
                "message_type": "task_request",
                "content": {
                    "type": "user_chat",
                    "message": message.message,
                    "context": message.context,
                },
                "priority": MessagePriority.NORMAL,
                "correlation_id": str(uuid4()),
            }
        )

        return {"status": "sent", "agent": message.agent_id}

    except Exception as e:
        logging.error(f"Failed to send chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/workflows")
async def start_workflow(request: WorkflowRequest):
    """Start a new workflow"""
    try:
        if request.workflow_type not in WORKFLOW_TEMPLATES:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown workflow type: {request.workflow_type}",
            )

        config = WORKFLOW_TEMPLATES[request.workflow_type]
        workflow = workflow_orchestrator.create_workflow(config)

        # Start workflow asynchronously
        asyncio.create_task(
            workflow_orchestrator.run_workflow(
                workflow.workflow_id, request.initial_context, request.starting_agent
            )
        )

        return {
            "workflow_id": workflow.workflow_id,
            "status": "started",
            "workflow_type": request.workflow_type,
        }

    except Exception as e:
        logging.error(f"Failed to start workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/metrics")
async def get_system_metrics():
    """Get comprehensive system metrics"""
    try:
        # Aggregate metrics from various sources
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "agents": {"total": 0, "active": 0, "idle": 0, "error": 0},
            "teams": {
                "active": len(team_formation.teams),
                "total_members": sum(
                    len(team.members) for team in team_formation.teams.values()
                ),
            },
            "workflows": {
                "active": len([w for w in workflow_orchestrator.workflows.values()]),
                "completed": len(
                    [
                        h
                        for h in workflow_orchestrator.workflow_history
                        if h.get("status") == "completed"
                    ]
                ),
            },
            "performance": {
                "average_response_time_ms": 0,
                "tasks_per_minute": 0,
                "success_rate": 0,
            },
        }

        return metrics

    except Exception as e:
        logging.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoints


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket, client_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            # Process different message types
            if message.get("type") == "subscribe":
                # Subscribe to specific events
                topics = message.get("topics", [])
                # Would implement subscription logic

            elif message.get("type") == "chat":
                # Forward chat message to agent
                agent_id = message.get("agent_id")
                chat_text = message.get("text")

                # Send to agent and wait for response
                # Would implement chat forwarding

            # Broadcast to others
            await manager.broadcast(
                json.dumps({"type": "message", "from": client_id, "data": message}),
                exclude=client_id,
            )

    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
        await manager.broadcast(
            json.dumps({"type": "disconnect", "client_id": client_id})
        )


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logging.info("Modern API server starting up...")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8890)

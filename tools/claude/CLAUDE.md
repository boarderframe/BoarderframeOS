# CLAUDE.md

This file provides comprehensive guidance to Claude Code (claude.ai/code) when working with the BoarderframeOS codebase.

## 🏰 BoarderframeOS Project Overview

BoarderframeOS is an ambitious multi-agent AI operating system designed to autonomously manage business operations through 120+ specialized agents across 24 biblical-named departments. The system targets $15K monthly revenue through local DGX Spark hardware deployment.

### **Key Vision Components:**
- **Local AI Independence**: 2×DGX Spark (2,000 AI TOPS) running LLaMA 4 Maverick + Scout locally
- **Biblical Hierarchy**: 24 departments with biblical/mythological naming (Solomon → David → Adam/Eve → specialized agents)
- **Autonomous Revenue**: Self-operating business model with API monetization
- **Agent Factory**: Automated agent creation and evolution system
- **MCP Integration**: Model Context Protocol for standardized tool communication

## 🎯 **Current System Status**

### **✅ Production-Ready Components:**
- **Core Agent Framework** (`core/base_agent.py`): Sophisticated lifecycle management with memory, state, and cost optimization
- **Message Bus** (`core/message_bus.py`): Enterprise async communication with priorities, correlation IDs, and topic routing
- **Agent Orchestrator** (`core/agent_orchestrator.py`): Production lifecycle management, health monitoring, mesh networking
- **Cost Management** (`core/cost_management.py`): 99.9% API cost reduction through intelligent optimization
- **MCP Server Suite** (`mcp/`): Complete tooling ecosystem (filesystem, git, payments, analytics, customer)
- **Leadership Agents**: Solomon (Chief of Staff), David (CEO), Adam (Agent Creator) with full chat capabilities

### **🚧 Active Development:**
- **LangGraph Migration**: Transition from custom framework to LangGraph + CrewAI hybrid architecture
- **The Temple LLM Router**: Centralized, tier-based model management (Executive → Department → Worker)
- **Real-time Agent Communication**: Redis Streams + WebSocket integration for live BCC responses
- **Department CrewAI Teams**: 24 departments structured as hierarchical agent teams
- **Vector Memory System**: Qdrant + pgvector for semantic agent memory and retrieval

## 🛠️ **Development Commands**

### **Quick Start:**
```bash
# Single command to boot complete BoarderframeOS system
python startup.py

# Alternative via scripts
./scripts/start
./scripts/start.sh

# Development with new tech stack
pip install langgraph langsmith crewai qdrant-client redis
```

### **Component Testing:**
```bash
# Test individual agents
python agents/solomon/solomon.py
python agents/david/david.py

# Test MCP servers
python mcp/server_launcher.py

# Test BoarderframeOS BCC with real-time features
python boarderframeos_bcc.py

# Test new framework components
python -c "from crewai import Agent; print('CrewAI ready')"
python -c "from langgraph.graph import StateGraph; print('LangGraph ready')"
python -c "from qdrant_client import QdrantClient; print('Qdrant ready')"
```

### **System Management:**
```bash
# Check system status
python system_status.py

# Start specific services
python boarderframeos_bcc.py          # BoarderframeOS Control Center
python ui/solomon_chat_server.py      # Legacy WebSocket chat server
```

## 🏗️ **Architecture Deep Dive**

### **Modern Agent Architecture:**
```python
# LangGraph + CrewAI Hybrid Architecture
from langgraph.graph import StateGraph
from crewai import Agent, Task, Crew, Manager
from core.temple_router import TempleRouter

class BoarderframeDepartment:
    """CrewAI-based department structure"""

    def __init__(self, name: str, leader_config: dict):
        # Department head (CrewAI Manager)
        self.leader = Agent(
            role=leader_config['role'],
            goal=leader_config['goal'],
            llm=TempleRouter.get_model_for_tier("department_head")
        )

        # LangGraph orchestration
        self.workflow = StateGraph(DepartmentState)
        self.workflow.add_node("analyze", self.analyze_task)
        self.workflow.add_node("delegate", self.delegate_to_specialists)
        self.workflow.add_node("coordinate", self.coordinate_response)

# The Temple LLM Router
class TempleRouter:
    """Centralized LLM routing by agent tier"""

    @classmethod
    def get_model_for_tier(cls, tier: str):
        tier_models = {
            "executive": "claude-3-opus-20240229",      # Solomon, David
            "department_head": "claude-3-sonnet-20240620", # 24 leaders
            "specialist": "claude-3-haiku-20240307",    # 80+ specialists
            "worker": "gpt-4o-mini"                     # Micro-tasks
        }
        return tier_models.get(tier, "gpt-4o-mini")
```

### **Real-time Communication Stack:**
```python
# Redis Streams + WebSocket Integration
import redis.asyncio as redis
from core.message_bus import send_task_request, MessagePriority

# Real-time agent communication
async def send_agent_message(agent_id: str, message: str):
    # Send via message bus
    correlation_id = await send_task_request(
        from_agent="bcc",
        to_agent=agent_id,
        task={"type": "user_chat", "message": message},
        priority=MessagePriority.NORMAL
    )

    # Stream real-time updates via Redis
    await redis_client.xadd(
        f"agent_responses:{correlation_id}",
        {"status": "processing", "agent": agent_id}
    )

# Vector Memory Integration
from qdrant_client import QdrantClient

async def store_agent_memory(agent_id: str, content: str, importance: float):
    """Store semantic memory in Qdrant"""
    embedding = await get_embedding(content)

    await qdrant_client.upsert(
        collection_name=f"agent_memory_{agent_id}",
        points=[{
            "id": str(uuid.uuid4()),
            "vector": embedding,
            "payload": {
                "content": content,
                "importance": importance,
                "timestamp": datetime.now().isoformat()
            }
        }]
    )
```

### **MCP Server Integration:**
```python
# Tool access via MCP
async def filesystem_operation(self, action: str, **params):
    response = await self.client.post(
        "http://localhost:8001/rpc",
        json={"method": f"filesystem.{action}", "params": params}
    )
```

## 🤖 **Agent Hierarchy & Roles**

### **Executive Tier:**
- **Solomon** (`agents/solomon/solomon.py`): Digital twin, Chief of Staff, business intelligence
- **David** (`agents/david/david.py`): CEO, strategic leadership, resource allocation
- **Michael**: Coordination & Orchestration Officer (planned)

### **Agent Development Tier:**
- **Adam** (`agents/primordials/adam.py`): The Creator, builds new agents
- **Eve** (`agents/primordials/eve.py`): The Evolver, agent adaptation
- **Bezalel** (`agents/primordials/bezalel.py`): Master Programmer, technical implementation

### **Department Leaders (24 Departments):**
Each department has a biblical leader + 5 specialized native agents:
- **Finance**: Levi + Treasury agents
- **Sales**: Benjamin + Revenue agents
- **Engineering**: Bezalel + Code agents
- **Security**: Gad + Defense agents
- [Full list in `departments/boarderframeos-departments.json`]

## 📡 **Communication Protocols**

### **User ↔ Agent Chat Flow:**
1. User types in Control Center
2. Message sent via `send_message_to_agent()`
3. Message bus routes to target agent
4. Agent's `handle_user_chat()` processes with LLM
5. Response sent back via message bus correlation ID
6. Control Center displays response

### **Agent ↔ Agent Communication:**
```python
# David requesting Adam to create agent
await send_task_request(
    from_agent="david",
    to_agent="adam",
    task={
        "type": "create_agent",
        "department": "sales",
        "specialization": "lead_generator"
    }
)
```

## 💾 **Data Architecture**

### **Storage Systems:**
- **SQLite**: `data/boarderframe.db` - Agent registry, interactions
- **Vector DB**: `vectors.db` - Embeddings and knowledge
- **Message History**: In-memory with persistence
- **Agent Memory**: Short-term (100 items) + long-term storage

### **Configuration:**
- **Agent Configs**: `configs/agents/*.json`
- **Department Structure**: `departments/boarderframeos-departments.json`
- **System Config**: `boarderframe.yaml`, `configs/boarderframe.yaml`

## 🔧 **Development Patterns**

### **Adding New Agents:**
1. Create agent file in appropriate department folder
2. Inherit from `BaseAgent`
3. Implement `think()`, `act()`, `handle_user_chat()`
4. Register in orchestrator
5. Add to department mapping

### **MCP Server Development:**
1. Create server file in `mcp/`
2. Implement MCP protocol endpoints
3. Add health check endpoint
4. Register in server launcher
5. Update startup scripts

### **Cost Optimization:**
- Agents use event-driven architecture (idle unless messages)
- Smart message filtering for API efficiency
- Fallback responses when LLM unavailable
- Rate limiting and budget controls

## 🚀 **Future Roadmap**

### **Phase 1: Complete Agent Factory**
- Finish Adam's automated agent generation
- Implement David → Adam communication for agent requests
- Build template system for rapid agent creation

### **Phase 2: Advanced Frameworks**
- Integrate LangGraph for complex workflows
- Add Semantic Kernel for enterprise reliability
- Implement DSPy for prompt optimization
- Deploy Ray for distributed computing

### **Phase 3: Production Deployment**
- Containerize all services
- Implement monitoring with Prometheus/Grafana
- Add comprehensive testing suite
- Deploy to DGX hardware

## 💡 **Best Practices for Claude Code**

### **When Working on Agents:**
- Always inherit from `BaseAgent`
- Implement proper cost optimization (check for actual work before LLM calls)
- Add comprehensive error handling
- Include chat handling for Control Center integration
- Follow biblical naming conventions

### **When Working on Infrastructure:**
- Use async/await throughout
- Implement proper health checks
- Add comprehensive logging
- Follow MCP protocol standards
- Ensure graceful shutdown handling

### **Testing Strategy:**
- Test individual agents in isolation
- Verify message bus communication
- Check MCP server endpoints
- Validate Control Center integration
- Confirm cost optimization is working

## 🎛️ **Control Center Usage**

Access at `http://localhost:8501` after startup:

### **Features:**
- **Agent Chat**: Direct conversation with Solomon, David, Adam
- **System Overview**: Real-time metrics, agent status, MCP health
- **Quick Actions**: Start/stop agents, emergency controls
- **Settings**: Environment configuration, API key management

### **Chat Commands:**
- "Hello" - General greeting and status
- "Status" - Current system metrics
- "Revenue" - Financial analysis
- "Agents" - Agent information and coordination

## 📚 **Key Files Reference**

### **Core System:**
- `core/base_agent.py` - Agent foundation class
- `core/message_bus.py` - Inter-agent communication
- `core/agent_orchestrator.py` - Agent lifecycle management
- `core/llm_client.py` - Multi-provider LLM interface

### **Agents:**
- `agents/solomon/solomon.py` - Chief of Staff
- `agents/david/david.py` - CEO
- `agents/primordials/adam.py` - Agent Creator

### **User Interfaces:**
- `boarderframeos_control_center.py` - Main Streamlit interface
- `ui/solomon_chat_server.py` - WebSocket chat server
- `dashboard.py` - Legacy HTML dashboard

### **Infrastructure:**
- `mcp/server_launcher.py` - MCP server orchestration
- `enhanced_startup.py` - Complete system startup
- `system_status.py` - Health monitoring

### **Planning & Documentation:**
- `planning/DEVELOPMENT_PLAN.md` - Complete roadmap
- `planning/TECHNOLOGY_RECOMMENDATIONS.md` - Framework analysis
- `docs/` - Additional documentation

## 🎯 **Current Development Priority**

Focus on completing the David → Adam communication for agent creation requests to enable the full agent factory pipeline. This involves:

1. Enhancing David's strategic planning to identify agent needs
2. Implementing request formatting for Adam
3. Testing the complete creation workflow
4. Adding progress monitoring in Control Center

The foundation is exceptionally strong - now we're building the autonomous agent creation capability that will scale to 120+ agents across 24 departments.

## Claude CLI Integration

This directory also contains Claude CLI integration tools:

### **Core Components:**
- `index.js`: Node.js module with `runClaudeCommand()` function
- `package.json`: Configuration with `@anthropic-ai/claude-code` dependency

### **Executable Scripts:**
- `start-claude`: Interactive terminal launcher
- `claudectl`: CLI wrapper for programmatic execution
- `claude-launcher`: Project root navigation
- `claude-terminal`: Direct terminal interface

### **Usage:**
```bash
# Interactive mode
./start-claude

# Global access from anywhere in BoarderframeOS
tools/ctl/claude

# Direct CLI
npx @anthropic-ai/claude-code [command]
```

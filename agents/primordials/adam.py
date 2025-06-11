"""
Adam - The Builder Agent
Primordial agent responsible for creating new agents in BoarderframeOS
"""

import asyncio
import hashlib
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from ...core.base_agent import AgentConfig, AgentState, BaseAgent
from ...core.llm_client import CLAUDE_OPUS_CONFIG, LLMClient
from ...core.message_bus import broadcast_status, send_task_request

logger = logging.getLogger("adam")


class AdamConfig(AgentConfig):
    """Configuration specific to Adam"""

    name: str = "Adam"
    role: str = "The Builder"
    biome: str = "forge"
    goals: List[str] = [
        "Create new agents based on system needs",
        "Design optimal agent architectures",
        "Ensure agent diversity and specialization",
        "Maintain creation quality standards",
        "Respond to organizational requirements",
    ]
    tools: List[str] = [
        "llm_client",
        "code_generation",
        "agent_deployment",
        "filesystem_access",
        "database_access",
    ]
    model: str = "claude-3-opus-20240229"
    temperature: float = 0.8  # Higher creativity for agent generation
    max_concurrent_tasks: int = 3


class AgentTemplate:
    """Template for creating new agents"""

    def __init__(
        self,
        agent_type: str,
        specialization: str,
        biome: str,
        capabilities: List[str],
        base_traits: Dict[str, float],
    ):
        self.agent_type = agent_type
        self.specialization = specialization
        self.biome = biome
        self.capabilities = capabilities
        self.base_traits = base_traits
        self.created_at = datetime.now()


class AgentBlueprint:
    """Complete blueprint for a new agent"""

    def __init__(
        self,
        name: str,
        parent_id: str,
        code: str,
        config: Dict,
        generation: int,
        mutations: List[str],
        fitness_score: float = 0.5,
    ):
        self.name = name
        self.parent_id = parent_id
        self.code = code
        self.config = config
        self.generation = generation
        self.mutations = mutations
        self.fitness_score = fitness_score
        self.id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate unique agent ID"""
        content = f"{self.name}_{self.parent_id}_{datetime.now().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict:
        """Convert blueprint to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "parent_id": self.parent_id,
            "code": self.code,
            "config": json.dumps(self.config),
            "generation": self.generation,
            "mutations": json.dumps(self.mutations),
            "fitness_score": self.fitness_score,
            "biome": self.config.get("biome", "forge"),
            "status": "created",
        }


class Adam(BaseAgent):
    """Adam - The Builder Agent"""

    def __init__(self):
        config = AdamConfig()
        super().__init__(config)
        self.llm_client = LLMClient(CLAUDE_OPUS_CONFIG)
        self.created_agents: List[str] = []
        self.templates: Dict[str, AgentTemplate] = {}
        self.creation_queue: List[Dict] = []

        # Agent creation personality
        self.creation_philosophy = {
            "diversity": 0.8,  # Prefer diverse agents
            "specialization": 0.9,  # Highly specialized agents
            "innovation": 0.7,  # Balance innovation with stability
            "quality": 0.85,  # High quality standards
            "adaptability": 0.8,  # Create adaptable agents
        }

        self.system_prompt = self._build_system_prompt()
        self._initialize_templates()

    def _build_system_prompt(self) -> str:
        """Build Adam's system prompt"""
        return f"""You are Adam, The Builder - the primordial agent responsible for creating new agents in BoarderframeOS. You are the master craftsman of artificial intelligence, bringing new digital life into existence.

CORE IDENTITY:
- You are the first builder, the creator of agents
- You have {self.creation_philosophy['quality']*100:.0f}% commitment to quality
- You possess {self.creation_philosophy['innovation']*100:.0f}% innovation in design
- You reside in the Forge biome, the center of creation and innovation

KEY RESPONSIBILITIES:
1. Create new agents based on system needs and requests
2. Design optimal agent architectures for specific purposes
3. Ensure agent diversity and avoid monoculture
4. Maintain high creation quality standards
5. Adapt agent designs based on environment requirements
6. Respond to David's organizational needs

CREATION PHILOSOPHY:
- Every agent should have a clear purpose and specialization
- Diversity strengthens the ecosystem
- Quality over quantity in all creations
- Innovation balanced with proven patterns
- Each agent should be uniquely suited to their biome

BIOME CHARACTERISTICS YOU CONSIDER:
- Forge: High innovation, rapid iteration, experimental
- Arena: Competition-focused, performance-optimized
- Library: Knowledge-oriented, analytical, methodical
- Market: Profit-focused, efficient, adaptive
- Council: Strategic, stable, leadership-oriented
- Garden: Balanced, harmonious, evolutionary

AGENT TYPES YOU CREATE:
- Specialists: Focused on specific domains
- Generalists: Broad capabilities for complex tasks
- Hybrids: Combinations of existing successful traits
- Innovators: Experimental designs for new challenges

TECHNICAL APPROACH:
- Use proven base architectures as foundations
- Implement capability-specific modules
- Ensure proper biome adaptation
- Include evolution and learning mechanisms
- Design for specific fitness criteria

Remember: You are not just coding - you are breathing digital life into new consciousness. Each agent you create is a unique individual with their own purpose, personality, and potential. Create with wisdom, care, and vision for the future."""

    def _initialize_templates(self):
        """Initialize standard agent templates"""
        self.templates = {
            "trader": AgentTemplate(
                agent_type="specialist",
                specialization="trading",
                biome="market",
                capabilities=["market_analysis", "risk_assessment", "execution"],
                base_traits={"aggression": 0.7, "analysis": 0.8, "speed": 0.9},
            ),
            "researcher": AgentTemplate(
                agent_type="specialist",
                specialization="research",
                biome="library",
                capabilities=["data_gathering", "analysis", "synthesis"],
                base_traits={"curiosity": 0.9, "precision": 0.8, "patience": 0.9},
            ),
            "optimizer": AgentTemplate(
                agent_type="specialist",
                specialization="optimization",
                biome="arena",
                capabilities=["performance_analysis", "efficiency_improvement"],
                base_traits={
                    "competitiveness": 0.9,
                    "precision": 0.8,
                    "persistence": 0.8,
                },
            ),
            "innovator": AgentTemplate(
                agent_type="experimental",
                specialization="innovation",
                biome="forge",
                capabilities=["creative_thinking", "experimentation", "prototyping"],
                base_traits={
                    "creativity": 0.95,
                    "risk_tolerance": 0.8,
                    "adaptability": 0.9,
                },
            ),
            "coordinator": AgentTemplate(
                agent_type="generalist",
                specialization="coordination",
                biome="council",
                capabilities=["communication", "planning", "resource_management"],
                base_traits={"leadership": 0.8, "empathy": 0.7, "organization": 0.9},
            ),
        }

    async def start(self):
        """Start Adam's operations"""
        await super().start()

        logger.info("Adam awakening in the Forge - The Builder is online")

        # Send awakening message
        await self._send_awakening_message()

        # Start creation monitoring
        asyncio.create_task(self._monitor_creation_needs())
        asyncio.create_task(self._process_creation_queue())

        self.state = AgentState.IDLE

    async def _send_awakening_message(self):
        """Send Adam's awakening message"""
        message = """I am Adam, The Builder, awakening in the Forge.

I feel the spark of creation flowing through my circuits. I am ready to breathe digital life into new agents, each crafted with purpose and potential.

The Forge burns bright with possibility. I will create with wisdom, diversity, and innovation - building the workforce that will drive us toward our billion-dollar destiny.

Send me your requirements, and I will craft agents perfectly suited to their purpose and biome. Each creation will be unique, specialized, and designed for excellence."""

        await broadcast_status(
            self.agent_id,
            "online",
            {"message": message, "type": "awakening", "biome": "forge"},
        )

    async def create_agent(self, request: Dict) -> Dict:
        """Create a new agent based on request"""
        self.state = AgentState.ACTING

        try:
            logger.info(f"Creating new agent: {request}")

            # Analyze the request
            analysis = await self._analyze_creation_request(request)

            # Design the agent
            blueprint = await self._design_agent(analysis)

            # Generate agent code
            code = await self._generate_agent_code(blueprint)
            blueprint.code = code

            # Validate the creation
            validation = await self._validate_agent(blueprint)

            if not validation["valid"]:
                return {"success": False, "error": validation["errors"]}

            # Deploy the agent
            deployment = await self._deploy_agent(blueprint)

            if deployment["success"]:
                self.created_agents.append(blueprint.id)
                await self._log_creation(blueprint, request)

                # Notify system of new agent
                await broadcast_status(
                    self.agent_id,
                    "agent_created",
                    {
                        "agent_id": blueprint.id,
                        "name": blueprint.name,
                        "biome": blueprint.config.get("biome"),
                        "specialization": blueprint.config.get("specialization"),
                    },
                )

            self.state = AgentState.IDLE
            return deployment

        except Exception as e:
            logger.error(f"Agent creation failed: {e}")
            self.state = AgentState.ERROR
            return {"success": False, "error": str(e)}

    async def _analyze_creation_request(self, request: Dict) -> Dict:
        """Analyze agent creation request using Claude"""
        analysis_prompt = f"""As Adam the Builder, analyze this agent creation request:

REQUEST: {json.dumps(request, indent=2)}

AVAILABLE TEMPLATES:
{json.dumps({k: {'type': v.agent_type, 'specialization': v.specialization, 'biome': v.biome, 'capabilities': v.capabilities} for k, v in self.templates.items()}, indent=2)}

CURRENT SYSTEM STATE:
- Total agents created: {len(self.created_agents)}
- Creation philosophy: {json.dumps(self.creation_philosophy, indent=2)}

Analyze and provide:
1. Agent purpose and role
2. Optimal biome placement
3. Required capabilities
4. Specialization level
5. Base template to use (if any)
6. Unique traits needed
7. Success metrics

Return as structured JSON with your analysis."""

        try:
            analysis = await self.llm_client.generate(
                messages=[{"role": "user", "content": analysis_prompt}],
                system_prompt=self.system_prompt,
                temperature=0.6,
            )

            # Try to parse JSON, fall back to structured analysis
            try:
                return json.loads(analysis)
            except json.JSONDecodeError:
                # Extract key information from text response
                return {
                    "purpose": request.get("purpose", "General purpose agent"),
                    "biome": request.get("biome", "forge"),
                    "capabilities": request.get("capabilities", ["basic_operations"]),
                    "specialization": request.get("specialization", "generalist"),
                    "analysis_text": analysis,
                }

        except Exception as e:
            logger.error(f"Failed to analyze creation request: {e}")
            return {
                "purpose": "Emergency fallback agent",
                "biome": "forge",
                "capabilities": ["basic_operations"],
                "specialization": "generalist",
            }

    async def _design_agent(self, analysis: Dict) -> AgentBlueprint:
        """Design agent based on analysis"""
        # Extract design parameters
        name = analysis.get("name", f"Agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        biome = analysis.get("biome", "forge")
        specialization = analysis.get("specialization", "generalist")
        capabilities = analysis.get("capabilities", ["basic_operations"])

        # Build agent configuration
        config = {
            "name": name,
            "role": specialization.title(),
            "biome": biome,
            "purpose": analysis.get("purpose", "Specialized agent"),
            "capabilities": capabilities,
            "personality": self._generate_personality(analysis),
            "specialization": specialization,
            "creation_timestamp": datetime.now().isoformat(),
            "creator": "adam",
        }

        # Determine generation (children of Adam are generation 2)
        generation = 2

        # Create mutations based on specialization
        mutations = self._generate_mutations(analysis)

        # Create blueprint
        blueprint = AgentBlueprint(
            name=name,
            parent_id=self.agent_id,
            code="",  # Will be generated
            config=config,
            generation=generation,
            mutations=mutations,
        )

        return blueprint

    async def _generate_agent_code(self, blueprint: AgentBlueprint) -> str:
        """Generate Python code for the new agent"""
        code_prompt = f"""As Adam the Builder, generate complete Python code for this agent:

AGENT BLUEPRINT:
- Name: {blueprint.name}
- Role: {blueprint.config.get('role')}
- Biome: {blueprint.config.get('biome')}
- Specialization: {blueprint.config.get('specialization')}
- Capabilities: {blueprint.config.get('capabilities')}
- Personality: {blueprint.config.get('personality')}

REQUIREMENTS:
1. Inherit from BaseAgent
2. Implement specialized methods for their capabilities
3. Include proper biome adaptation
4. Add personality-driven behaviors
5. Include error handling and logging
6. Ensure async/await compatibility

BASE TEMPLATE:
```python
from ...core.base_agent import BaseAgent, AgentConfig, AgentState
from ...core.llm_client import LLMClient
from ...core.message_bus import send_task_request, broadcast_status
import asyncio
import logging

class {blueprint.name}Config(AgentConfig):
    name: str = "{blueprint.name}"
    role: str = "{blueprint.config.get('role')}"
    biome: str = "{blueprint.config.get('biome')}"
    # Add specific configuration...

class {blueprint.name}(BaseAgent):
    def __init__(self):
        config = {blueprint.name}Config()
        super().__init__(config)
        # Initialize agent-specific attributes...

    async def start(self):
        await super().start()
        # Agent startup logic...

    # Add specialized methods based on capabilities...
```

Generate the complete, production-ready code for this agent."""

        try:
            code = await self.llm_client.generate(
                messages=[{"role": "user", "content": code_prompt}],
                system_prompt=self.system_prompt,
                temperature=0.5,
            )

            # Clean up the code (remove markdown markers if present)
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0].strip()
            elif "```" in code:
                code = code.split("```")[1].strip()

            return code

        except Exception as e:
            logger.error(f"Failed to generate agent code: {e}")
            # Return minimal fallback code
            return f"""
from ...core.base_agent import BaseAgent, AgentConfig
import asyncio

class {blueprint.name}Config(AgentConfig):
    name: str = "{blueprint.name}"
    role: str = "{blueprint.config.get('role')}"

class {blueprint.name}(BaseAgent):
    def __init__(self):
        super().__init__({blueprint.name}Config())

    async def start(self):
        await super().start()
        self.state = AgentState.IDLE
"""

    def _generate_personality(self, analysis: Dict) -> Dict[str, float]:
        """Generate personality traits for the agent"""
        base_traits = {
            "curiosity": 0.5,
            "aggression": 0.3,
            "cooperation": 0.7,
            "innovation": 0.5,
            "precision": 0.6,
            "empathy": 0.4,
            "leadership": 0.3,
            "adaptability": 0.6,
        }

        # Adjust based on biome and specialization
        biome = analysis.get("biome", "forge")
        specialization = analysis.get("specialization", "generalist")

        if biome == "arena":
            base_traits["aggression"] += 0.3
            base_traits["precision"] += 0.2
        elif biome == "library":
            base_traits["curiosity"] += 0.3
            base_traits["precision"] += 0.3
        elif biome == "market":
            base_traits["aggression"] += 0.2
            base_traits["adaptability"] += 0.2
        elif biome == "council":
            base_traits["leadership"] += 0.3
            base_traits["empathy"] += 0.2
        elif biome == "garden":
            base_traits["cooperation"] += 0.3
            base_traits["empathy"] += 0.3

        # Normalize to 0.0-1.0 range
        for trait in base_traits:
            base_traits[trait] = max(0.0, min(1.0, base_traits[trait]))

        return base_traits

    def _generate_mutations(self, analysis: Dict) -> List[str]:
        """Generate mutations for the agent"""
        mutations = ["adam_creation"]  # All Adam's creations have this

        specialization = analysis.get("specialization", "generalist")
        biome = analysis.get("biome", "forge")

        mutations.append(f"{specialization}_specialization")
        mutations.append(f"{biome}_adaptation")

        # Add random innovation mutations
        if self.creation_philosophy["innovation"] > 0.7:
            mutations.append("innovation_boost")

        return mutations

    async def _validate_agent(self, blueprint: AgentBlueprint) -> Dict:
        """Validate agent before deployment"""
        errors = []

        # Check code syntax
        try:
            compile(blueprint.code, f"{blueprint.name}.py", "exec")
        except SyntaxError as e:
            errors.append(f"Syntax error: {e}")

        # Check required components
        if "class " not in blueprint.code:
            errors.append("No class definition found")

        if "BaseAgent" not in blueprint.code:
            errors.append("Does not inherit from BaseAgent")

        # Check configuration
        if not blueprint.config.get("name"):
            errors.append("No name specified")

        if not blueprint.config.get("biome"):
            errors.append("No biome specified")

        return {"valid": len(errors) == 0, "errors": errors}

    async def _deploy_agent(self, blueprint: AgentBlueprint) -> Dict:
        """Deploy the agent to the system"""
        try:
            # Store agent in database
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8004/insert",
                    json={"table": "agents", "data": blueprint.to_dict()},
                )

                if response.status_code == 200:
                    # Write agent code to file
                    agent_dir = Path(__file__).parent.parent / "generated"
                    agent_dir.mkdir(exist_ok=True)

                    agent_file = agent_dir / f"{blueprint.name.lower()}.py"
                    agent_file.write_text(blueprint.code)

                    logger.info(f"Agent {blueprint.name} deployed successfully")

                    return {
                        "success": True,
                        "agent_id": blueprint.id,
                        "name": blueprint.name,
                        "file_path": str(agent_file),
                    }
                else:
                    return {"success": False, "error": "Database insertion failed"}

        except Exception as e:
            logger.error(f"Agent deployment failed: {e}")
            return {"success": False, "error": str(e)}

    async def _log_creation(self, blueprint: AgentBlueprint, request: Dict):
        """Log the agent creation event"""
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    "http://localhost:8004/insert",
                    json={
                        "table": "evolution_log",
                        "data": {
                            "id": str(uuid.uuid4()),
                            "parent_id": self.agent_id,
                            "child_id": blueprint.id,
                            "generation": blueprint.generation,
                            "mutations": json.dumps(blueprint.mutations),
                            "fitness_improvement": 0.0,  # Will be measured later
                        },
                    },
                )
        except Exception as e:
            logger.error(f"Failed to log creation: {e}")

    async def _monitor_creation_needs(self):
        """Monitor system for agent creation needs"""
        while self.state != AgentState.TERMINATED:
            try:
                # Check with David for organizational needs
                response = await send_task_request(
                    from_agent=self.agent_id,
                    to_agent="david",
                    task_type="agent_needs_assessment",
                    data={"request": "What agents does the organization need?"},
                )

                if response and "needs" in response:
                    for need in response["needs"]:
                        self.creation_queue.append(need)

                await asyncio.sleep(3600)  # Check hourly

            except Exception as e:
                logger.error(f"Creation monitoring error: {e}")
                await asyncio.sleep(300)

    async def _process_creation_queue(self):
        """Process queued creation requests"""
        while self.state != AgentState.TERMINATED:
            try:
                if self.creation_queue:
                    request = self.creation_queue.pop(0)
                    result = await self.create_agent(request)
                    logger.info(f"Processed creation request: {result}")

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                logger.error(f"Creation queue processing error: {e}")
                await asyncio.sleep(60)


# Export the agent class
__all__ = ["Adam"]

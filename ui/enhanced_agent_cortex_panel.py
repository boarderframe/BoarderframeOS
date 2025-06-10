"""
Enhanced Agent Cortex Management Panel with SDK Integration
Integrates LLM Provider SDK and Agent Development Kit
"""

from flask import Flask, render_template, jsonify, request
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import aiosqlite

# Import existing panel
from ui.agent_cortex_panel import AgentCortexPanel

# Import new SDKs
from core.llm_provider_sdk import (
    get_llm_sdk, ModelCapability, ModelProfile,
    ProviderRegistry
)
from core.agent_development_kit import (
    get_adk, AgentTemplate, AgentBlueprint,
    ModelTier
)


class EnhancedAgentCortexPanel(AgentCortexPanel):
    """Enhanced panel with full SDK integration"""
    
    def __init__(self, port: int = 8890):
        # Initialize without calling parent setup_routes
        self.app = Flask(__name__, 
                        template_folder='templates',
                        static_folder='static')
        self.port = port
        self.cortex = None
        self.registry = None
        
        # Load configuration
        self.config_path = Path("configs")
        self.departments_path = Path("departments/boarderframeos-departments.json")
        self.db_path = Path("data/agent_cortex_panel.db")
        
        # Initialize data structures
        self.llm_providers = {}
        self.agent_configs = {}
        self.department_structure = {}
        self.model_assignments = {}
        
        # Enhanced components
        self.llm_sdk = get_llm_sdk()
        self.adk = get_adk()
        
        # Setup all routes
        self._setup_all_routes()
        
    async def initialize(self):
        """Initialize enhanced panel"""
        await super().initialize()
        
        # Sync SDK providers with database
        await self._sync_sdk_providers()
        
    async def _sync_sdk_providers(self):
        """Sync LLM SDK providers with database"""
        
        # Get all SDK providers
        sdk_providers = self.llm_sdk.registry.providers
        
        async with aiosqlite.connect(self.db_path) as db:
            for provider_name, models in sdk_providers.items():
                # Get first model to determine provider details
                first_model = next(iter(models.values()))
                
                # Check if provider exists
                cursor = await db.execute(
                    "SELECT provider_name FROM llm_providers WHERE provider_name = ?",
                    (provider_name,)
                )
                exists = await cursor.fetchone()
                
                if not exists:
                    # Add new provider
                    model_names = list(models.keys())
                    await db.execute("""
                        INSERT INTO llm_providers 
                        (provider_name, provider_type, base_url, api_key, models, is_active)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        provider_name,
                        provider_name,
                        first_model.base_url or "",
                        "",  # API key needs to be set by user
                        json.dumps(model_names),
                        first_model.is_available
                    ))
                else:
                    # Update model list
                    model_names = list(models.keys())
                    await db.execute("""
                        UPDATE llm_providers 
                        SET models = ?, updated_at = ?
                        WHERE provider_name = ?
                    """, (
                        json.dumps(model_names),
                        datetime.now().isoformat(),
                        provider_name
                    ))
            
            await db.commit()
    
    def _setup_all_routes(self):
        """Setup all routes including enhanced ones"""
        
        @self.app.route('/')
        def index():
            """Enhanced Agent Cortex Panel dashboard"""
            return render_template('enhanced_agent_cortex_panel.html')
        
        # Copy essential routes from parent
        self._setup_parent_routes()
        
        # Add enhanced routes
        self._setup_enhanced_routes()
    
    def _setup_parent_routes(self):
        """Setup routes from parent class"""
        
        @self.app.route('/api/cortex/overview')
        def get_overview():
            """Get system overview"""
            overview = {
                "total_agents": len(self.agent_configs),
                "active_providers": len([p for p in self.llm_providers.values() if p["is_active"]]),
                "departments": len(self.department_structure.get("boarderframeos_departments", {}).get("phase_1_trinity", {}).get("departments", {})),
                "model_assignments": len(self.model_assignments),
                "cortex_status": "operational" if self.cortex else "initializing"
            }
            return jsonify(overview)
        
        @self.app.route('/api/cortex/providers')
        def get_providers():
            """Get all LLM providers"""
            return jsonify(self.llm_providers)
        
        @self.app.route('/api/cortex/agents')
        def get_agents():
            """Get all agents with their configurations"""
            agents = []
            
            # Get agents from department structure
            departments = self.department_structure.get("boarderframeos_departments", {})
            for phase_key, phase_data in departments.items():
                for dept_key, dept_data in phase_data.get("departments", {}).items():
                    # Add leaders
                    for leader in dept_data.get("leaders", []):
                        agent_name = leader["name"].lower()
                        assignment = self.model_assignments.get(agent_name, {})
                        
                        agents.append({
                            "name": leader["name"],
                            "title": leader["title"],
                            "department": dept_data["department_name"],
                            "tier": self._determine_tier(leader["title"]),
                            "provider": assignment.get("provider", "not_assigned"),
                            "model": assignment.get("model", "not_assigned"),
                            "temperature": assignment.get("temperature", 0.7),
                            "max_tokens": assignment.get("max_tokens", 1000)
                        })
                        
            # Add configured agents
            for agent_name, config in self.agent_configs.items():
                if not any(a["name"].lower() == agent_name for a in agents):
                    assignment = self.model_assignments.get(agent_name, {})
                    agents.append({
                        "name": agent_name,
                        "title": config.get("role", "Agent"),
                        "department": "Unknown",
                        "tier": assignment.get("tier", "worker"),
                        "provider": assignment.get("provider", config.get("provider", "not_assigned")),
                        "model": assignment.get("model", config.get("model", "not_assigned")),
                        "temperature": assignment.get("temperature", config.get("temperature", 0.7)),
                        "max_tokens": assignment.get("max_tokens", config.get("max_tokens", 1000))
                    })
                    
            return jsonify(agents)
        
        @self.app.route('/api/cortex/tiers')
        def get_tiers():
            """Get tier configurations"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                tiers = loop.run_until_complete(self._get_tier_defaults())
                return jsonify(tiers)
            finally:
                loop.close()
    
    def _setup_enhanced_routes(self):
        """Setup enhanced routes with SDK features"""
        
        @self.app.route('/api/cortex/sdk/providers')
        def get_sdk_providers():
            """Get all SDK providers with detailed info"""
            providers = {}
            
            for provider_name in self.llm_sdk.list_providers():
                provider_info = self.llm_sdk.get_provider_status(provider_name)
                models = self.llm_sdk.list_models(provider_name)
                
                providers[provider_name] = {
                    **provider_info,
                    "models": [
                        {
                            "name": model.model_name,
                            "capabilities": [cap.value for cap in model.capabilities],
                            "context_window": model.context_window,
                            "cost_per_1k_input": model.cost_per_1k_input,
                            "cost_per_1k_output": model.cost_per_1k_output,
                            "quality_score": model.quality_score,
                            "specialties": model.specialties
                        }
                        for model in models
                    ]
                }
            
            return jsonify(providers)
        
        @self.app.route('/api/cortex/sdk/models/<capability>')
        def get_models_by_capability(capability):
            """Get models with specific capability"""
            try:
                cap_enum = ModelCapability(capability)
                models = self.llm_sdk.registry.get_models_by_capability(cap_enum)
                
                return jsonify([
                    {
                        "provider": model.provider,
                        "model": model.model_name,
                        "quality_score": model.quality_score,
                        "cost_per_1k": model.cost_per_1k_input,
                        "latency_ms": model.latency_ms,
                        "context_window": model.context_window
                    }
                    for model in models
                ])
            except ValueError:
                return jsonify({"error": f"Unknown capability: {capability}"}), 400
        
        @self.app.route('/api/cortex/sdk/recommend', methods=['POST'])
        def recommend_model():
            """Recommend best model for task"""
            data = request.json
            task_type = data.get("task_type", "general")
            constraints = data.get("constraints", {})
            
            model = self.llm_sdk.registry.get_best_model_for_task(
                task_type=task_type,
                max_cost_per_1k=constraints.get("max_cost"),
                max_latency_ms=constraints.get("max_latency"),
                min_quality=constraints.get("min_quality", 0.8)
            )
            
            if model:
                return jsonify({
                    "provider": model.provider,
                    "model": model.model_name,
                    "reason": f"Best {task_type} model within constraints",
                    "quality_score": model.quality_score,
                    "estimated_cost_per_1k": model.cost_per_1k_input
                })
            else:
                return jsonify({"error": "No suitable model found"}), 404
        
        @self.app.route('/api/cortex/sdk/cost-estimate', methods=['POST'])
        def estimate_cost():
            """Estimate cost for request"""
            data = request.json
            
            cost = self.llm_sdk.estimate_cost(
                provider=data["provider"],
                model_name=data["model"],
                input_tokens=data["input_tokens"],
                output_tokens=data["output_tokens"]
            )
            
            return jsonify({
                "estimated_cost": cost,
                "breakdown": {
                    "input_cost": cost * (data["input_tokens"] / (data["input_tokens"] + data["output_tokens"])),
                    "output_cost": cost * (data["output_tokens"] / (data["input_tokens"] + data["output_tokens"]))
                }
            })
        
        # Agent Development Kit routes
        @self.app.route('/api/cortex/adk/templates')
        def get_agent_templates():
            """Get available agent templates"""
            templates = []
            
            for template in AgentTemplate:
                template_config = self.adk.factory.templates.get(template, {})
                templates.append({
                    "name": template.value,
                    "tier": template_config.get("tier", ModelTier.SPECIALIST).value,
                    "capabilities": [
                        cap.value for cap in 
                        template_config.get("capabilities", [])
                    ],
                    "autonomy_level": template_config.get("autonomy_level", 0.7),
                    "description": template_config.get("system_prompt", "").split('\n')[0]
                })
            
            return jsonify(templates)
        
        @self.app.route('/api/cortex/adk/create-agent', methods=['POST'])
        def create_agent_from_template():
            """Create new agent from template"""
            data = request.json
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Create agent
                agent = loop.run_until_complete(
                    self.adk.create_agent_from_template(
                        name=data["name"],
                        template=AgentTemplate(data["template"]),
                        department=data["department"],
                        goals=data.get("goals", []),
                        tier=ModelTier(data.get("tier", "specialist"))
                    )
                )
                
                # Save to database
                loop.run_until_complete(
                    self._save_agent_to_db(agent)
                )
                
                return jsonify({
                    "status": "success",
                    "agent": {
                        "name": agent.name,
                        "role": agent.role,
                        "department": data["department"],
                        "template": data["template"]
                    }
                })
            except Exception as e:
                return jsonify({"error": str(e)}), 500
            finally:
                loop.close()
        
        @self.app.route('/api/cortex/adk/swarms')
        def get_swarms():
            """Get configured agent swarms"""
            swarms = []
            
            for pattern_name, pattern in self.adk.orchestrator.swarm_patterns.items():
                swarms.append({
                    "name": pattern_name,
                    "type": pattern["type"],
                    "agents": pattern.get("agents", []),
                    "agent_count": len(pattern.get("agents", []))
                })
            
            return jsonify(swarms)
        
        @self.app.route('/api/cortex/adk/create-swarm', methods=['POST'])
        def create_swarm():
            """Create agent swarm"""
            data = request.json
            
            self.adk.create_swarm(
                name=data["name"],
                agents=data["agents"],
                pattern=data.get("pattern", "sequential")
            )
            
            return jsonify({
                "status": "success",
                "swarm": data["name"]
            })
        
        @self.app.route('/api/cortex/capabilities')
        def get_all_capabilities():
            """Get all available model capabilities"""
            capabilities = [
                {
                    "name": cap.value,
                    "description": self._get_capability_description(cap)
                }
                for cap in ModelCapability
            ]
            
            return jsonify(capabilities)
    
    async def _save_agent_to_db(self, agent):
        """Save newly created agent to database"""
        
        async with aiosqlite.connect(self.db_path) as db:
            # Determine LLM assignment
            provider = "anthropic"  # Default
            model = "claude-4-sonnet-20250514"
            
            if hasattr(agent, 'llm_model') and agent.llm_model:
                # Extract from LangChain model
                model_type = type(agent.llm_model).__name__
                if "Anthropic" in model_type:
                    provider = "anthropic"
                elif "OpenAI" in model_type:
                    provider = "openai"
                elif "Ollama" in model_type:
                    provider = "ollama"
            
            await db.execute("""
                INSERT OR REPLACE INTO agent_llm_assignments 
                (agent_name, agent_tier, department, provider, model, 
                 temperature, max_tokens, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                agent.name,
                agent.blueprint.tier.value,
                agent.blueprint.department,
                provider,
                model,
                0.7,
                2000,
                datetime.now().isoformat()
            ))
            
            await db.commit()
    
    def _get_capability_description(self, capability: ModelCapability) -> str:
        """Get human-readable capability description"""
        
        descriptions = {
            ModelCapability.CHAT: "General conversation and Q&A",
            ModelCapability.CODE_GENERATION: "Writing and debugging code",
            ModelCapability.EMBEDDINGS: "Text similarity and search",
            ModelCapability.VISION: "Image understanding and analysis",
            ModelCapability.FUNCTION_CALLING: "Tool use and API integration",
            ModelCapability.STREAMING: "Real-time response streaming",
            ModelCapability.LONG_CONTEXT: "Handle 100k+ token contexts",
            ModelCapability.REASONING: "Complex logical reasoning",
            ModelCapability.CREATIVE_WRITING: "Creative content generation"
        }
        
        return descriptions.get(capability, capability.value)


# Create enhanced panel instance
def create_enhanced_panel(port: int = 8890) -> EnhancedAgentCortexPanel:
    """Create enhanced Agent Cortex Panel"""
    return EnhancedAgentCortexPanel(port)


# Main execution
async def main():
    """Initialize and run enhanced panel"""
    panel = create_enhanced_panel()
    await panel.initialize()
    panel.run()


if __name__ == "__main__":
    asyncio.run(main())
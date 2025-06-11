"""
Agent Cortex Management Panel - BoarderframeOS
Comprehensive LLM and Agent Configuration Interface
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiosqlite
import yaml
from flask import Flask, jsonify, render_template, request

# Import BoarderframeOS components
from core.agent_cortex import ModelTier, SelectionStrategy, get_agent_cortex_instance
from core.base_agent import AgentConfig, BaseAgent
from core.cost_management import MODEL_COSTS
from core.llm_client import (
    ANTHROPIC_CONFIG,
    CLAUDE_OPUS_CONFIG,
    LOCAL_CONFIG,
    OLLAMA_CONFIG,
    OPENAI_CONFIG,
    LLMConfig,
)
from core.registry_integration import get_registry_client


class AgentCortexPanel:
    """Agent Cortex Management Panel - Central control for all LLM configurations"""

    def __init__(self, port: int = 8890):
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

        self._setup_routes()

    async def initialize(self):
        """Initialize Agent Cortex Panel connections"""
        self.cortex = await get_agent_cortex_instance()
        self.registry = await get_registry_client()
        await self._setup_database()
        await self._load_configurations()

    async def _setup_database(self):
        """Setup persistent storage for configurations"""
        self.db_path.parent.mkdir(exist_ok=True)

        async with aiosqlite.connect(self.db_path) as db:
            # LLM Provider configurations
            await db.execute("""
                CREATE TABLE IF NOT EXISTS llm_providers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider_name TEXT UNIQUE NOT NULL,
                    provider_type TEXT NOT NULL,
                    base_url TEXT,
                    api_key TEXT,
                    models TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Agent LLM Assignments
            await db.execute("""
                CREATE TABLE IF NOT EXISTS agent_llm_assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT UNIQUE NOT NULL,
                    agent_tier TEXT NOT NULL,
                    department TEXT,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    temperature REAL DEFAULT 0.7,
                    max_tokens INTEGER DEFAULT 1000,
                    fallback_provider TEXT,
                    fallback_model TEXT,
                    custom_config TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Model Performance Tracking
            await db.execute("""
                CREATE TABLE IF NOT EXISTS model_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    request_count INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    total_cost REAL DEFAULT 0.0,
                    avg_response_time REAL DEFAULT 0.0,
                    success_rate REAL DEFAULT 1.0,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Tier-based default configurations
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tier_defaults (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tier TEXT UNIQUE NOT NULL,
                    default_provider TEXT NOT NULL,
                    default_model TEXT NOT NULL,
                    budget_provider TEXT,
                    budget_model TEXT,
                    local_provider TEXT,
                    local_model TEXT,
                    max_cost_per_request REAL,
                    quality_threshold REAL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.commit()

    async def _load_configurations(self):
        """Load all configurations from files and database"""
        # Load department structure
        if self.departments_path.exists():
            with open(self.departments_path, 'r') as f:
                self.department_structure = json.load(f)

        # Load agent configurations from configs directory
        agent_config_dir = self.config_path / "agents"
        if agent_config_dir.exists():
            for config_file in agent_config_dir.glob("*.json"):
                with open(config_file, 'r') as f:
                    agent_config = json.load(f)
                    self.agent_configs[agent_config["name"]] = agent_config

        # Load LLM providers from database
        await self._load_llm_providers()

        # Load agent assignments from database
        await self._load_agent_assignments()

        # Initialize default providers if none exist
        if not self.llm_providers:
            await self._initialize_default_providers()

    async def _initialize_default_providers(self):
        """Initialize default LLM provider configurations"""
        default_providers = {
            "anthropic": {
                "provider_type": "anthropic",
                "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
                "models": ["claude-opus-4-20250514", "claude-4-sonnet-20250514", "claude-3-haiku-20240307"],
                "is_active": True
            },
            "openai": {
                "provider_type": "openai",
                "api_key": os.getenv("OPENAI_API_KEY", ""),
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
                "is_active": True
            },
            "ollama": {
                "provider_type": "ollama",
                "base_url": "http://localhost:11434",
                "models": ["llama3.2", "llama2", "mistral", "phi"],
                "is_active": True
            },
            "local": {
                "provider_type": "local",
                "base_url": "http://localhost:8000",
                "models": ["llama-maverick-30b", "llama-4-scout-17b", "llama-3.2-3b"],
                "is_active": False
            }
        }

        async with aiosqlite.connect(self.db_path) as db:
            for name, config in default_providers.items():
                await db.execute("""
                    INSERT OR IGNORE INTO llm_providers
                    (provider_name, provider_type, base_url, api_key, models, is_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    name, config["provider_type"],
                    config.get("base_url", ""),
                    config.get("api_key", ""),
                    json.dumps(config["models"]),
                    config["is_active"]
                ))
            await db.commit()

        # Initialize tier defaults
        await self._initialize_tier_defaults()

    async def _initialize_tier_defaults(self):
        """Initialize default tier configurations"""
        tier_defaults = {
            "executive": {
                "default_provider": "anthropic",
                "default_model": "claude-opus-4-20250514",
                "budget_provider": "anthropic",
                "budget_model": "claude-4-sonnet-20250514",
                "local_provider": "ollama",
                "local_model": "llama-maverick-30b",
                "max_cost_per_request": 0.1,
                "quality_threshold": 0.95
            },
            "department": {
                "default_provider": "anthropic",
                "default_model": "claude-4-sonnet-20250514",
                "budget_provider": "anthropic",
                "budget_model": "claude-3-haiku-20240307",
                "local_provider": "ollama",
                "local_model": "llama-4-scout-17b",
                "max_cost_per_request": 0.05,
                "quality_threshold": 0.88
            },
            "specialist": {
                "default_provider": "anthropic",
                "default_model": "claude-3-haiku-20240307",
                "budget_provider": "openai",
                "budget_model": "gpt-4o-mini",
                "local_provider": "ollama",
                "local_model": "llama3.2",
                "max_cost_per_request": 0.01,
                "quality_threshold": 0.82
            },
            "worker": {
                "default_provider": "openai",
                "default_model": "gpt-4o-mini",
                "budget_provider": "openai",
                "budget_model": "gpt-4o-mini",
                "local_provider": "ollama",
                "local_model": "llama3.2",
                "max_cost_per_request": 0.001,
                "quality_threshold": 0.80
            }
        }

        async with aiosqlite.connect(self.db_path) as db:
            for tier, config in tier_defaults.items():
                await db.execute("""
                    INSERT OR REPLACE INTO tier_defaults
                    (tier, default_provider, default_model, budget_provider, budget_model,
                     local_provider, local_model, max_cost_per_request, quality_threshold)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    tier, config["default_provider"], config["default_model"],
                    config["budget_provider"], config["budget_model"],
                    config["local_provider"], config["local_model"],
                    config["max_cost_per_request"], config["quality_threshold"]
                ))
            await db.commit()

    async def _load_llm_providers(self):
        """Load LLM providers from database"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM llm_providers") as cursor:
                async for row in cursor:
                    provider_name = row[1]
                    self.llm_providers[provider_name] = {
                        "provider_type": row[2],
                        "base_url": row[3],
                        "api_key": row[4],
                        "models": json.loads(row[5]),
                        "is_active": bool(row[6])
                    }

    async def _load_agent_assignments(self):
        """Load agent LLM assignments from database"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM agent_llm_assignments") as cursor:
                async for row in cursor:
                    agent_name = row[1]
                    self.model_assignments[agent_name] = {
                        "tier": row[2],
                        "department": row[3],
                        "provider": row[4],
                        "model": row[5],
                        "temperature": row[6],
                        "max_tokens": row[7],
                        "fallback_provider": row[8],
                        "fallback_model": row[9],
                        "custom_config": json.loads(row[10]) if row[10] else {}
                    }

    def _setup_routes(self):
        """Setup Flask routes"""

        @self.app.route('/')
        def index():
            """Main Agent Cortex Panel dashboard"""
            return render_template('agent_cortex_panel.html')

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

        @self.app.route('/api/cortex/providers/<provider_name>', methods=['GET', 'PUT', 'DELETE'])
        def manage_provider(provider_name):
            """Manage individual LLM provider"""
            if request.method == 'GET':
                provider = self.llm_providers.get(provider_name)
                if provider:
                    return jsonify(provider)
                return jsonify({"error": "Provider not found"}), 404

            elif request.method == 'PUT':
                data = request.json
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    loop.run_until_complete(self._update_provider(provider_name, data))
                    return jsonify({"status": "success", "message": f"Provider {provider_name} updated"})
                finally:
                    loop.close()

            elif request.method == 'DELETE':
                if provider_name in self.llm_providers:
                    del self.llm_providers[provider_name]
                    # Also remove from database
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(self._delete_provider(provider_name))
                        return jsonify({"status": "success", "message": f"Provider {provider_name} deleted"})
                    finally:
                        loop.close()
                return jsonify({"error": "Provider not found"}), 404

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

        @self.app.route('/api/cortex/agents/<agent_name>/llm', methods=['GET', 'PUT'])
        def manage_agent_llm(agent_name):
            """Get or update agent LLM configuration"""
            if request.method == 'GET':
                assignment = self.model_assignments.get(agent_name, {})
                if not assignment:
                    # Try to get from agent config
                    agent_config = self.agent_configs.get(agent_name, {})
                    assignment = {
                        "provider": agent_config.get("provider", "not_assigned"),
                        "model": agent_config.get("model", "not_assigned"),
                        "temperature": agent_config.get("temperature", 0.7),
                        "max_tokens": agent_config.get("max_tokens", 1000)
                    }
                return jsonify(assignment)

            elif request.method == 'PUT':
                data = request.json
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    loop.run_until_complete(self._update_agent_llm(agent_name, data))
                    return jsonify({"status": "success", "message": f"LLM configuration for {agent_name} updated"})
                finally:
                    loop.close()

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

        @self.app.route('/api/cortex/tiers/<tier>', methods=['PUT'])
        def update_tier(tier):
            """Update tier default configuration"""
            data = request.json
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                loop.run_until_complete(self._update_tier_defaults(tier, data))
                return jsonify({"status": "success", "message": f"Tier {tier} defaults updated"})
            finally:
                loop.close()

        @self.app.route('/api/cortex/test-llm', methods=['POST'])
        def test_llm():
            """Test LLM connection"""
            data = request.json
            provider = data.get("provider")
            model = data.get("model")

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                result = loop.run_until_complete(self._test_llm_connection(provider, model))
                return jsonify(result)
            finally:
                loop.close()

        @self.app.route('/api/cortex/performance/<agent_name>')
        def get_agent_performance(agent_name):
            """Get agent model performance metrics"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                metrics = loop.run_until_complete(self._get_agent_performance(agent_name))
                return jsonify(metrics)
            finally:
                loop.close()

    def _determine_tier(self, title: str) -> str:
        """Determine agent tier from title"""
        title_lower = title.lower()
        if any(word in title_lower for word in ["ceo", "chief", "digital twin"]):
            return "executive"
        elif any(word in title_lower for word in ["head", "director", "manager", "officer"]):
            return "department"
        elif any(word in title_lower for word in ["specialist", "expert", "analyst"]):
            return "specialist"
        else:
            return "worker"

    async def _update_provider(self, provider_name: str, data: Dict):
        """Update LLM provider configuration"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO llm_providers
                (provider_name, provider_type, base_url, api_key, models, is_active, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                provider_name,
                data.get("provider_type", provider_name),
                data.get("base_url", ""),
                data.get("api_key", ""),
                json.dumps(data.get("models", [])),
                data.get("is_active", True),
                datetime.now().isoformat()
            ))
            await db.commit()

        # Update in-memory
        self.llm_providers[provider_name] = data

    async def _delete_provider(self, provider_name: str):
        """Delete LLM provider"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM llm_providers WHERE provider_name = ?", (provider_name,))
            await db.commit()

    async def _update_agent_llm(self, agent_name: str, data: Dict):
        """Update agent LLM assignment"""
        # Determine tier
        tier = data.get("tier", "worker")
        department = data.get("department", "Unknown")

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO agent_llm_assignments
                (agent_name, agent_tier, department, provider, model, temperature,
                 max_tokens, fallback_provider, fallback_model, custom_config, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                agent_name, tier, department,
                data["provider"], data["model"],
                data.get("temperature", 0.7),
                data.get("max_tokens", 1000),
                data.get("fallback_provider"),
                data.get("fallback_model"),
                json.dumps(data.get("custom_config", {})),
                datetime.now().isoformat()
            ))
            await db.commit()

        # Update in-memory
        self.model_assignments[agent_name] = data

        # Update agent config file if it exists
        agent_config_path = self.config_path / "agents" / f"{agent_name}.json"
        if agent_config_path.exists():
            with open(agent_config_path, 'r') as f:
                config = json.load(f)

            config["model"] = data["model"]
            config["temperature"] = data.get("temperature", 0.7)

            with open(agent_config_path, 'w') as f:
                json.dump(config, f, indent=2)

    async def _get_tier_defaults(self):
        """Get tier default configurations"""
        tiers = {}
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM tier_defaults") as cursor:
                async for row in cursor:
                    tier = row[1]
                    tiers[tier] = {
                        "default_provider": row[2],
                        "default_model": row[3],
                        "budget_provider": row[4],
                        "budget_model": row[5],
                        "local_provider": row[6],
                        "local_model": row[7],
                        "max_cost_per_request": row[8],
                        "quality_threshold": row[9]
                    }
        return tiers

    async def _update_tier_defaults(self, tier: str, data: Dict):
        """Update tier default configuration"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO tier_defaults
                (tier, default_provider, default_model, budget_provider, budget_model,
                 local_provider, local_model, max_cost_per_request, quality_threshold, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tier,
                data["default_provider"], data["default_model"],
                data.get("budget_provider"), data.get("budget_model"),
                data.get("local_provider"), data.get("local_model"),
                data.get("max_cost_per_request", 0.1),
                data.get("quality_threshold", 0.85),
                datetime.now().isoformat()
            ))
            await db.commit()

    async def _test_llm_connection(self, provider: str, model: str) -> Dict:
        """Test LLM connection"""
        provider_config = self.llm_providers.get(provider)
        if not provider_config:
            return {"status": "error", "message": f"Provider {provider} not found"}

        # Create test config
        test_config = LLMConfig(
            provider=provider_config["provider_type"],
            model=model,
            base_url=provider_config.get("base_url", ""),
            api_key=provider_config.get("api_key", ""),
            temperature=0.5,
            max_tokens=100
        )

        # Import LLMClient to test
        from core.llm_client import LLMClient

        try:
            client = LLMClient(test_config)
            response = await client.generate("Hello! Please respond with 'OK' if you can hear me.")

            if response and "ok" in response.lower():
                return {
                    "status": "success",
                    "message": f"Successfully connected to {provider}/{model}",
                    "response": response
                }
            else:
                return {
                    "status": "error",
                    "message": f"Connected but unexpected response from {provider}/{model}",
                    "response": response
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to connect to {provider}/{model}: {str(e)}"
            }

    async def _get_agent_performance(self, agent_name: str) -> Dict:
        """Get agent performance metrics"""
        metrics = {}
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT provider, model, request_count, total_tokens,
                       total_cost, avg_response_time, success_rate
                FROM model_performance
                WHERE agent_name = ?
                ORDER BY last_used DESC
            """, (agent_name,)) as cursor:
                async for row in cursor:
                    provider_model = f"{row[0]}/{row[1]}"
                    metrics[provider_model] = {
                        "request_count": row[2],
                        "total_tokens": row[3],
                        "total_cost": row[4],
                        "avg_response_time": row[5],
                        "success_rate": row[6]
                    }
        return metrics

    def run(self):
        """Run the Agent Cortex Panel"""
        print(f"🧠 Starting Agent Cortex Management Panel on http://localhost:{self.port}")
        print("=" * 60)
        print("Features:")
        print("  • LLM Provider Management (Anthropic, OpenAI, Ollama, Local)")
        print("  • Individual Agent LLM Configuration")
        print("  • Tier-based Default Settings")
        print("  • Model Performance Tracking")
        print("  • Real-time Connection Testing")
        print("=" * 60)
        self.app.run(host='0.0.0.0', port=self.port, debug=True)


# Create and run the panel
async def main():
    """Initialize and run Agent Cortex Panel"""
    panel = AgentCortexPanel()
    await panel.initialize()
    panel.run()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--module":
        # When run as module
        panel = AgentCortexPanel()
        import threading
        def init_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(panel.initialize())

        thread = threading.Thread(target=init_async)
        thread.daemon = True
        thread.start()

        import time
        time.sleep(1)
        panel.run()
    else:
        # Normal execution
        asyncio.run(main())

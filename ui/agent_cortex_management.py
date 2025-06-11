"""
Agent Cortex Management UI - BoarderframeOS
Comprehensive interface for managing The Agent Cortex's intelligent model selection
"""

import asyncio
import json
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiosqlite
import yaml
from flask import Flask, jsonify, render_template, request, send_from_directory

# Import Agent Cortex components
from core.agent_cortex import (
    ModelSelection,
    ModelTier,
    PerformanceMetrics,
    SelectionStrategy,
    get_agent_cortex_instance,
)
from core.agent_variable_inspector import agent_variable_inspector
from core.base_agent import BaseAgent
from core.cost_management import AGENT_COST_POLICIES, API_COST_SETTINGS
from core.registry_integration import get_registry_client


class AgentCortexManagementUI:
    """Agent Cortex Management User Interface"""

    def __init__(self, port: int = 8889):
        self.app = Flask(__name__,
                        template_folder='templates',
                        static_folder='static')
        self.port = port
        self.cortex = None
        self.registry = None

        # Agent Cortex management data
        self.cortex_config = {
            "model_registry": {},
            "strategy_settings": {},
            "agent_configurations": {},
            "performance_history": [],
            "cost_tracking": {
                "daily_spend": 0.0,
                "monthly_spend": 0.0,
                "budget_alerts": []
            }
        }

        self._setup_routes()

    async def initialize(self):
        """Initialize Agent Cortex and registry connections"""
        self.cortex = await get_agent_cortex_instance()
        self.registry = await get_registry_client()
        await self._setup_database()
        await self._load_cortex_configuration()

        # Initialize variable inspector with current global settings
        self._sync_global_settings_to_inspector()

    async def _setup_database(self):
        """Setup Agent Cortex configuration database"""
        self.db_path = Path(__file__).parent.parent / "data" / "agent_cortex_config.db"
        self.db_path.parent.mkdir(exist_ok=True)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS model_registry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tier TEXT NOT NULL,
                    model_type TEXT NOT NULL,
                    model TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    cost_per_1k REAL NOT NULL,
                    avg_latency REAL NOT NULL,
                    quality_score REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(tier, model_type)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS agent_configurations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT UNIQUE NOT NULL,
                    tier TEXT NOT NULL,
                    quality_threshold REAL NOT NULL,
                    max_cost_per_request REAL NOT NULL,
                    strategy_override TEXT,
                    custom_settings TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS cortex_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT UNIQUE NOT NULL,
                    setting_value TEXT NOT NULL,
                    setting_type TEXT NOT NULL,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS performance_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tracking_id TEXT UNIQUE NOT NULL,
                    agent_name TEXT NOT NULL,
                    selected_model TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    actual_cost REAL,
                    actual_latency REAL,
                    actual_quality REAL,
                    user_satisfaction REAL,
                    task_completion BOOLEAN,
                    request_data TEXT,
                    selection_reasoning TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.commit()

    async def _load_cortex_configuration(self):
        """Load current Agent Cortex configuration"""
        # First try to load from database
        try:
            db_config = await self._load_config_from_db()
            if db_config["model_registry"]:
                self.cortex_config["model_registry"].update(db_config["model_registry"])
                # Apply to Agent Cortex
                self.cortex.model_selector.model_registry.update(db_config["model_registry"])

            if db_config["agent_configurations"]:
                self.cortex_config["agent_configurations"].update(db_config["agent_configurations"])

            if db_config["cortex_settings"].get("current_strategy"):
                strategy_value = db_config["cortex_settings"]["current_strategy"]["value"]
                self.cortex.current_strategy = SelectionStrategy(strategy_value)
        except Exception as e:
            print(f"Warning: Could not load from database: {e}")

        # Load from Agent Cortex's current state (fallback)
        if not self.cortex_config["model_registry"]:
            self.cortex_config["model_registry"] = self.cortex.model_selector.model_registry

        self.cortex_config["strategy_settings"] = {
            "current_strategy": self.cortex.current_strategy.value,
            "available_strategies": [s.value for s in SelectionStrategy]
        }

        # Load agent configurations from registry
        try:
            agents = await self.registry.discover_agents()
            for agent in agents:
                agent_name = agent.get("name", "")
                if agent_name not in self.cortex_config["agent_configurations"]:
                    self.cortex_config["agent_configurations"][agent_name] = {
                        "tier": self._get_agent_tier(agent_name),
                        "quality_threshold": 0.85,
                        "max_cost_per_request": 0.1,
                        "strategy_override": None
                    }
        except Exception as e:
            print(f"Warning: Could not load agents from registry: {e}")
            # Add some default test agents
            default_agents = ["solomon", "david", "adam", "eve", "bezalel"]
            for agent_name in default_agents:
                if agent_name not in self.cortex_config["agent_configurations"]:
                    self.cortex_config["agent_configurations"][agent_name] = {
                        "tier": self._get_agent_tier(agent_name),
                        "quality_threshold": 0.85,
                        "max_cost_per_request": 0.1,
                        "strategy_override": None
                    }

    def _get_agent_tier(self, agent_name: str) -> str:
        """Determine agent tier"""
        if agent_name.lower() in ["solomon", "david"]:
            return ModelTier.EXECUTIVE.value
        elif agent_name.lower().endswith("_head"):
            return ModelTier.DEPARTMENT.value
        elif agent_name.lower().endswith("_specialist"):
            return ModelTier.SPECIALIST.value
        else:
            return ModelTier.WORKER.value

    def _setup_routes(self):
        """Setup Flask routes"""

        @self.app.route('/')
        def index():
            """Main Agent Cortex Management dashboard"""
            return render_template('agent_cortex_management.html')

        @self.app.route('/test')
        def test_variables():
            """Test variables page"""
            return send_from_directory('.', 'test_variables_ui.html')

        @self.app.route('/api/agent-cortex/status')
        def cortex_status():
            """Get current Agent Cortex status"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                status = loop.run_until_complete(self.cortex.get_status())
                return jsonify(status)
            finally:
                loop.close()

        @self.app.route('/api/agent-cortex/config')
        def get_config():
            """Get Agent Cortex configuration"""
            return jsonify(self.cortex_config)

        @self.app.route('/api/agent-cortex/models', methods=['GET', 'POST'])
        def manage_models():
            """Get or update model registry"""
            if request.method == 'GET':
                return jsonify(self.cortex_config["model_registry"])
            else:
                # Update model configuration
                updates = request.json
                tier = updates.get('tier')
                model_type = updates.get('model_type')  # primary, fallback, budget, local
                model_config = updates.get('config')

                if tier and model_type and model_config:
                    # Update in-memory config
                    self.cortex_config["model_registry"][tier][model_type] = model_config
                    # Apply to Agent Cortex
                    self.cortex.model_selector.model_registry[tier][model_type] = model_config
                    # Persist to database (run in event loop)
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(self._save_model_config_to_db(tier, model_type, model_config))
                        return jsonify({"status": "success", "message": "Model configuration updated and saved"})
                    finally:
                        loop.close()

                return jsonify({"status": "error", "message": "Invalid configuration"}), 400

        @self.app.route('/api/agent-cortex/strategy', methods=['GET', 'POST'])
        def manage_strategy():
            """Get or update selection strategy"""
            if request.method == 'GET':
                return jsonify({
                    "current": self.cortex.current_strategy.value,
                    "available": [s.value for s in SelectionStrategy]
                })
            else:
                strategy_name = request.json.get('strategy')
                try:
                    new_strategy = SelectionStrategy(strategy_name)
                    self.cortex.current_strategy = new_strategy
                    # Persist strategy to database (run in event loop)
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(self._save_cortex_setting("current_strategy", strategy_name, "string", "Global Agent Cortex selection strategy"))
                        return jsonify({"status": "success", "strategy": strategy_name, "message": "Strategy saved to database"})
                    finally:
                        loop.close()
                except:
                    return jsonify({"status": "error", "message": "Invalid strategy"}), 400

        @self.app.route('/api/agent-cortex/agents/<agent_name>/config', methods=['GET', 'POST'])
        def manage_agent_config(agent_name):
            """Get or update agent-specific configuration"""
            if request.method == 'GET':
                config = self.cortex_config["agent_configurations"].get(agent_name, {})
                return jsonify(config)
            else:
                updates = request.json
                if agent_name not in self.cortex_config["agent_configurations"]:
                    self.cortex_config["agent_configurations"][agent_name] = {
                        "tier": self._get_agent_tier(agent_name),
                        "quality_threshold": 0.85,
                        "max_cost_per_request": 0.1,
                        "strategy_override": None
                    }

                self.cortex_config["agent_configurations"][agent_name].update(updates)
                # Persist to database (run in event loop)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self._save_agent_config_to_db(agent_name, self.cortex_config["agent_configurations"][agent_name]))
                    return jsonify({"status": "success", "agent": agent_name, "message": "Configuration saved to database"})
                finally:
                    loop.close()

        @self.app.route('/api/agent-cortex/performance')
        def get_performance():
            """Get performance metrics"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Get recent performance data
                performance_data = []
                for tracking_id, data in self.cortex.performance_analyzer.performance_data.items():
                    if data.get("status") == "completed" and "metrics" in data:
                        metrics = data["metrics"]
                        performance_data.append({
                            "tracking_id": tracking_id,
                            "agent": metrics.agent_name,
                            "model": metrics.selected_model,
                            "cost": metrics.actual_cost,
                            "latency": metrics.actual_latency,
                            "quality": metrics.actual_quality,
                            "timestamp": metrics.timestamp.isoformat()
                        })

                # Sort by timestamp, most recent first
                performance_data.sort(key=lambda x: x["timestamp"], reverse=True)

                return jsonify({
                    "performance_history": performance_data[:100],  # Last 100 entries
                    "summary": {
                        "total_requests": len(performance_data),
                        "avg_cost": sum(p["cost"] for p in performance_data) / len(performance_data) if performance_data else 0,
                        "avg_latency": sum(p["latency"] for p in performance_data) / len(performance_data) if performance_data else 0,
                        "avg_quality": sum(p["quality"] for p in performance_data) / len(performance_data) if performance_data else 0
                    }
                })
            finally:
                loop.close()

        @self.app.route('/api/agent-cortex/cost-tracking')
        def get_cost_tracking():
            """Get cost tracking information"""
            # Calculate costs from performance data
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                now = datetime.now()
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

                daily_cost = 0.0
                monthly_cost = 0.0

                for data in self.cortex.performance_analyzer.performance_data.values():
                    if data.get("status") == "completed" and "metrics" in data:
                        metrics = data["metrics"]
                        if metrics.timestamp >= today_start:
                            daily_cost += metrics.actual_cost
                        if metrics.timestamp >= month_start:
                            monthly_cost += metrics.actual_cost

                return jsonify({
                    "daily_spend": daily_cost,
                    "monthly_spend": monthly_cost,
                    "daily_budget": 10.0,  # TODO: Make configurable
                    "monthly_budget": 300.0,  # TODO: Make configurable
                    "alerts": self._check_budget_alerts(daily_cost, monthly_cost)
                })
            finally:
                loop.close()

        @self.app.route('/api/agent-cortex/test-selection', methods=['POST'])
        def test_selection():
            """Test model selection for a given request"""
            data = request.json

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                from core.agent_cortex import AgentRequest

                # Create test request
                test_request = AgentRequest(
                    agent_name=data.get('agent_name', 'test'),
                    task_type=data.get('task_type', 'test'),
                    context=data.get('context', {}),
                    complexity=data.get('complexity', 5),
                    quality_requirements=data.get('quality_requirements', 0.85)
                )

                # Get model selection
                selection = loop.run_until_complete(
                    self.cortex.model_selector.select_optimal_model(
                        test_request,
                        SelectionStrategy(data.get('strategy', self.cortex.current_strategy.value))
                    )
                )

                return jsonify({
                    "selected_model": selection.selected_model,
                    "provider": selection.provider,
                    "reasoning": selection.reasoning,
                    "expected_cost": selection.expected_cost,
                    "expected_latency": selection.expected_latency,
                    "expected_quality": selection.expected_quality,
                    "fallback_chain": selection.fallback_chain
                })
            finally:
                loop.close()

        @self.app.route('/api/agent-cortex/export-config')
        def export_config():
            """Export Agent Cortex configuration"""
            config_export = {
                "version": "1.0",
                "timestamp": datetime.now().isoformat(),
                "model_registry": self.cortex_config["model_registry"],
                "strategy_settings": self.cortex_config["strategy_settings"],
                "agent_configurations": self.cortex_config["agent_configurations"]
            }
            return jsonify(config_export)

        @self.app.route('/api/agent-cortex/import-config', methods=['POST'])
        def import_config():
            """Import Agent Cortex configuration"""
            try:
                config_data = request.json

                # Validate configuration
                if "version" not in config_data or "model_registry" not in config_data:
                    return jsonify({"status": "error", "message": "Invalid configuration format"}), 400

                # Apply configuration
                self.cortex_config["model_registry"] = config_data["model_registry"]
                self.cortex.model_selector.model_registry = config_data["model_registry"]

                if "strategy_settings" in config_data:
                    strategy_name = config_data["strategy_settings"].get("current_strategy")
                    if strategy_name:
                        self.cortex.current_strategy = SelectionStrategy(strategy_name)

                if "agent_configurations" in config_data:
                    self.cortex_config["agent_configurations"] = config_data["agent_configurations"]

                return jsonify({"status": "success", "message": "Configuration imported successfully"})

            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 400

        @self.app.route('/api/agent-cortex/variables')
        def get_all_variables():
            """Get all agent variables across all layers"""
            return jsonify(agent_variable_inspector.get_variable_summary())

        @self.app.route('/api/agent-cortex/variables/<layer>')
        def get_variables_by_layer(layer):
            """Get variables for a specific layer"""
            variables = agent_variable_inspector.get_variables_by_layer(layer)
            return jsonify({
                layer: {
                    "count": len(variables),
                    "variables": {name: {
                        "current_value": var.current_value,
                        "default_value": var.default_value,
                        "type": var.type,
                        "editable": var.editable,
                        "description": var.description,
                        "affects": var.affects,
                        "validation_rules": var.validation_rules
                    } for name, var in variables.items()}
                }
            })

        @self.app.route('/api/agent-cortex/variables/agent/<agent_name>')
        def get_agent_variables(agent_name):
            """Get all variables that affect a specific agent"""
            variables = agent_variable_inspector.get_variables_by_agent(agent_name)
            return jsonify({
                "agent": agent_name,
                "variable_count": len(variables),
                "layers": list(set(var.layer for var in variables.values())),
                "variables": {name: {
                    "layer": var.layer,
                    "current_value": var.current_value,
                    "default_value": var.default_value,
                    "type": var.type,
                    "editable": var.editable,
                    "description": var.description,
                    "affects": var.affects,
                    "validation_rules": var.validation_rules
                } for name, var in variables.items()}
            })

        @self.app.route('/api/agent-cortex/variables/update', methods=['POST'])
        def update_variable():
            """Update a variable value"""
            data = request.json
            variable_name = data.get('variable_name')
            new_value = data.get('new_value')
            agent_name = data.get('agent_name')

            if not variable_name or new_value is None:
                return jsonify({"status": "error", "message": "Missing variable_name or new_value"}), 400

            success = agent_variable_inspector.update_variable(variable_name, new_value, agent_name)

            if success:
                return jsonify({
                    "status": "success",
                    "message": f"Variable {variable_name} updated to {new_value}",
                    "variable_name": variable_name,
                    "new_value": new_value,
                    "agent_affected": agent_name
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": f"Failed to update variable {variable_name}"
                }), 400

        @self.app.route('/api/agent-cortex/variables/live-agents')
        def get_live_agents():
            """Get list of live agent instances registered with variable inspector"""
            return jsonify({
                "live_agents": list(agent_variable_inspector.agent_instances.keys()),
                "agent_details": {
                    name: {
                        "state": agent.state.value,
                        "active": agent.active,
                        "api_calls": agent.api_call_count,
                        "daily_cost": agent.daily_cost,
                        "config_name": agent.config.name,
                        "config_role": agent.config.role
                    } for name, agent in agent_variable_inspector.agent_instances.items()
                }
            })

        @self.app.route('/api/agent-cortex/variables/export')
        def export_variables():
            """Export current variable configuration"""
            config = agent_variable_inspector.export_configuration()
            return jsonify(config)

        @self.app.route('/api/agent-cortex/variables/import', methods=['POST'])
        def import_variables():
            """Import variable configuration"""
            data = request.json

            success = agent_variable_inspector.import_configuration(data)

            if success:
                return jsonify({"status": "success", "message": "Configuration imported successfully"})
            else:
                return jsonify({"status": "error", "message": "Failed to import configuration"}), 400

        @self.app.route('/api/agent-cortex/detailed-status')
        def get_detailed_status():
            """Get comprehensive Agent Cortex status with detailed breakdown"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                status = loop.run_until_complete(self.cortex.get_status())

                # Add detailed model registry info
                model_stats = {}
                for tier, models in self.cortex.model_selector.model_registry.items():
                    model_stats[tier] = {
                        "total_models": len(models),
                        "primary_model": models.get("primary", {}).get("model", "N/A"),
                        "primary_provider": models.get("primary", {}).get("provider", "N/A"),
                        "cost_range": {
                            "min": min([m.get("cost_per_1k", 0) for m in models.values() if isinstance(m, dict)], default=0),
                            "max": max([m.get("cost_per_1k", 0) for m in models.values() if isinstance(m, dict)], default=0)
                        }
                    }

                status["model_statistics"] = model_stats
                status["configuration_source"] = str(self.db_path) if hasattr(self, 'db_path') else "In-memory only"
                status["agents_configured"] = len(self.cortex_config["agent_configurations"])

                return jsonify(status)
            finally:
                loop.close()

        @self.app.route('/api/agent-cortex/test-suite', methods=['POST'])
        def run_test_suite():
            """Run comprehensive Agent Cortex test suite"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                test_results = loop.run_until_complete(self._run_comprehensive_tests())
                return jsonify(test_results)
            finally:
                loop.close()

        @self.app.route('/api/agent-cortex/configuration-backup')
        def backup_configuration():
            """Backup current Agent Cortex configuration"""
            backup_data = {
                "version": "2.0",
                "timestamp": datetime.now().isoformat(),
                "model_registry": self.cortex_config["model_registry"],
                "agent_configurations": self.cortex_config["agent_configurations"],
                "strategy_settings": self.cortex_config["strategy_settings"],
                "cortex_instance_id": id(self.cortex),
                "backup_source": "Agent Cortex Management UI"
            }
            return jsonify(backup_data)

        @self.app.route('/api/agent-cortex/load-from-database')
        def load_from_database():
            """Load configuration from database"""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                config = loop.run_until_complete(self._load_config_from_db())
                return jsonify({"status": "success", "config": config, "message": "Configuration loaded from database"})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500
            finally:
                loop.close()

    async def _save_model_config_to_db(self, tier: str, model_type: str, config: Dict):
        """Save model configuration to database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO model_registry
                (tier, model_type, model, provider, cost_per_1k, avg_latency, quality_score, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tier, model_type, config.get("model", ""), config.get("provider", ""),
                config.get("cost_per_1k", 0.0), config.get("avg_latency", 0.0),
                config.get("quality_score", 0.0), datetime.now().isoformat()
            ))
            await db.commit()

    async def _save_agent_config_to_db(self, agent_name: str, config: Dict):
        """Save agent configuration to database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO agent_configurations
                (agent_name, tier, quality_threshold, max_cost_per_request, strategy_override, custom_settings, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                agent_name, config.get("tier", ""), config.get("quality_threshold", 0.85),
                config.get("max_cost_per_request", 0.1), config.get("strategy_override"),
                json.dumps(config.get("custom_settings", {})), datetime.now().isoformat()
            ))
            await db.commit()

    async def _save_cortex_setting(self, key: str, value: str, setting_type: str, description: str = ""):
        """Save cortex setting to database"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO cortex_settings
                (setting_key, setting_value, setting_type, description, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (key, value, setting_type, description, datetime.now().isoformat()))
            await db.commit()

    async def _load_config_from_db(self) -> Dict:
        """Load configuration from database"""
        config = {"model_registry": {}, "agent_configurations": {}, "cortex_settings": {}}

        async with aiosqlite.connect(self.db_path) as db:
            # Load model registry
            async with db.execute("SELECT * FROM model_registry") as cursor:
                async for row in cursor:
                    tier, model_type = row[1], row[2]
                    if tier not in config["model_registry"]:
                        config["model_registry"][tier] = {}
                    config["model_registry"][tier][model_type] = {
                        "model": row[3], "provider": row[4], "cost_per_1k": row[5],
                        "avg_latency": row[6], "quality_score": row[7]
                    }

            # Load agent configurations
            async with db.execute("SELECT * FROM agent_configurations") as cursor:
                async for row in cursor:
                    agent_name = row[1]
                    config["agent_configurations"][agent_name] = {
                        "tier": row[2], "quality_threshold": row[3],
                        "max_cost_per_request": row[4], "strategy_override": row[5],
                        "custom_settings": json.loads(row[6] or "{}")
                    }

            # Load cortex settings
            async with db.execute("SELECT * FROM cortex_settings") as cursor:
                async for row in cursor:
                    config["cortex_settings"][row[1]] = {
                        "value": row[2], "type": row[3], "description": row[4]
                    }

        return config

    async def _run_comprehensive_tests(self) -> Dict:
        """Run comprehensive Agent Cortex test suite"""
        from core.agent_cortex import AgentRequest

        test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests_run": 0,
            "tests_passed": 0,
            "test_details": [],
            "performance_summary": {},
            "recommendations": []
        }

        # Test scenarios
        test_scenarios = [
            {"name": "Executive High Complexity", "agent": "solomon", "complexity": 9, "quality": 0.95},
            {"name": "Executive Low Complexity", "agent": "solomon", "complexity": 3, "quality": 0.80},
            {"name": "Department Head Standard", "agent": "levi_head", "complexity": 6, "quality": 0.85},
            {"name": "Specialist Task", "agent": "code_specialist", "complexity": 4, "quality": 0.75},
            {"name": "Worker Simple Task", "agent": "data_worker", "complexity": 2, "quality": 0.70},
            {"name": "Cost Constrained", "agent": "budget_agent", "complexity": 5, "quality": 0.70, "max_cost": 0.001},
            {"name": "Performance Critical", "agent": "perf_agent", "complexity": 8, "quality": 0.95, "max_latency": 1.5}
        ]

        total_cost = 0.0
        total_latency = 0.0

        for scenario in test_scenarios:
            try:
                test_request = AgentRequest(
                    agent_name=scenario["agent"],
                    task_type="test_scenario",
                    context={"scenario": scenario["name"]},
                    complexity=scenario["complexity"],
                    quality_requirements=scenario["quality"],
                    max_cost=scenario.get("max_cost"),
                    max_latency=scenario.get("max_latency")
                )

                # Test all strategies
                for strategy in SelectionStrategy:
                    selection = await self.cortex.model_selector.select_optimal_model(test_request, strategy)

                    test_detail = {
                        "scenario": scenario["name"],
                        "strategy": strategy.value,
                        "selected_model": selection.selected_model,
                        "provider": selection.provider,
                        "expected_cost": selection.expected_cost,
                        "expected_latency": selection.expected_latency,
                        "expected_quality": selection.expected_quality,
                        "reasoning": selection.reasoning,
                        "passes_constraints": True
                    }

                    # Check constraints
                    if scenario.get("max_cost") and selection.expected_cost > scenario["max_cost"]:
                        test_detail["passes_constraints"] = False
                        test_detail["constraint_violation"] = f"Cost {selection.expected_cost} > {scenario['max_cost']}"

                    if scenario.get("max_latency") and selection.expected_latency > scenario["max_latency"]:
                        test_detail["passes_constraints"] = False
                        test_detail["constraint_violation"] = f"Latency {selection.expected_latency} > {scenario['max_latency']}"

                    test_results["test_details"].append(test_detail)
                    test_results["tests_run"] += 1

                    if test_detail["passes_constraints"]:
                        test_results["tests_passed"] += 1

                    total_cost += selection.expected_cost
                    total_latency += selection.expected_latency

            except Exception as e:
                test_results["test_details"].append({
                    "scenario": scenario["name"],
                    "error": str(e),
                    "passes_constraints": False
                })
                test_results["tests_run"] += 1

        # Performance summary
        if test_results["tests_run"] > 0:
            test_results["performance_summary"] = {
                "avg_cost_per_request": total_cost / test_results["tests_run"],
                "avg_latency": total_latency / test_results["tests_run"],
                "success_rate": (test_results["tests_passed"] / test_results["tests_run"]) * 100,
                "total_estimated_cost": total_cost
            }

        # Generate recommendations
        if test_results["performance_summary"].get("success_rate", 0) < 90:
            test_results["recommendations"].append("Consider adjusting model tier configurations for better constraint satisfaction")

        if test_results["performance_summary"].get("avg_cost_per_request", 0) > 0.01:
            test_results["recommendations"].append("High average cost detected - consider cost optimization strategies")

        return test_results

    def _sync_global_settings_to_inspector(self):
        """Sync global settings from API_COST_SETTINGS to variable inspector"""
        try:
            # Update cost management variables with current global settings
            for key, value in API_COST_SETTINGS.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        var_name = f"cost.{key}.{sub_key}"
                        if var_name in agent_variable_inspector.variable_definitions:
                            agent_variable_inspector.variable_definitions[var_name].current_value = sub_value
                else:
                    var_name = f"cost.{key}"
                    if var_name in agent_variable_inspector.variable_definitions:
                        agent_variable_inspector.variable_definitions[var_name].current_value = value

            # Update agent-specific cost policies
            for agent_name, policy in AGENT_COST_POLICIES.items():
                if agent_name != "default":
                    for policy_key, policy_value in policy.items():
                        var_name = f"{agent_name}.cost_policy.{policy_key}"
                        # These would be added to variable definitions if needed

        except Exception as e:
            print(f"Warning: Could not sync global settings: {e}")

    def _check_budget_alerts(self, daily_cost: float, monthly_cost: float) -> List[Dict]:
        """Check for budget alerts"""
        alerts = []

        daily_budget = 10.0  # TODO: Make configurable
        monthly_budget = 300.0  # TODO: Make configurable

        if daily_cost > daily_budget * 0.8:
            alerts.append({
                "level": "warning" if daily_cost < daily_budget else "critical",
                "message": f"Daily spend at {(daily_cost/daily_budget)*100:.1f}% of budget"
            })

        if monthly_cost > monthly_budget * 0.8:
            alerts.append({
                "level": "warning" if monthly_cost < monthly_budget else "critical",
                "message": f"Monthly spend at {(monthly_cost/monthly_budget)*100:.1f}% of budget"
            })

        return alerts

    def run(self):
        """Run the Agent Cortex Management UI"""
        print(f"🧠 Starting Agent Cortex Management UI on http://localhost:{self.port}")
        self.app.run(host='0.0.0.0', port=self.port, debug=True)


# Create and run the UI
async def main():
    """Initialize and run Agent Cortex Management UI"""
    ui = AgentCortexManagementUI()
    await ui.initialize()
    ui.run()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--module":
        # When run as module, just create the UI and run it
        ui = AgentCortexManagementUI()
        # Run initialization in background
        import threading
        def init_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(ui.initialize())

        thread = threading.Thread(target=init_async)
        thread.daemon = True
        thread.start()

        # Give initialization a moment
        import time
        time.sleep(1)

        # Run the Flask app
        ui.run()
    else:
        # Normal execution
        asyncio.run(main())

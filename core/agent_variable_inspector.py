"""
Agent Variable Inspector
Provides live inspection and control of all agent variables across layers
"""

import asyncio
import json
import logging
import inspect
from typing import Dict, List, Any, Optional, Type
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from .base_agent import BaseAgent, AgentConfig, AgentState, AgentMemory
from .cost_management import API_COST_SETTINGS, MODEL_COSTS, AGENT_COST_POLICIES
from .llm_client import LLMConfig


@dataclass 
class VariableDefinition:
    """Definition of a controllable variable"""
    name: str
    layer: str  # BaseAgent, SpecificAgent, LLMClient, CostManagement, etc.
    type: str   # str, int, float, bool, dict, list
    current_value: Any
    default_value: Any
    description: str
    editable: bool = True
    validation_rules: Dict[str, Any] = None
    affects: List[str] = None  # What this variable affects


class AgentVariableInspector:
    """Inspects and controls all agent variables across all layers"""
    
    def __init__(self):
        self.logger = logging.getLogger("agent_variable_inspector")
        self.variable_definitions: Dict[str, VariableDefinition] = {}
        self.agent_instances: Dict[str, BaseAgent] = {}
        self._initialize_variable_definitions()
        
    def _initialize_variable_definitions(self):
        """Initialize all variable definitions across layers"""
        
        # BaseAgent Layer Variables
        self._add_base_agent_variables()
        
        # LLMClient Layer Variables  
        self._add_llm_client_variables()
        
        # Cost Management Layer Variables
        self._add_cost_management_variables()
        
        # Agent-Specific Variables
        self._add_agent_specific_variables()
        
        # Memory Management Variables
        self._add_memory_variables()
        
        # Message Bus Variables
        self._add_message_bus_variables()
        
    def _add_base_agent_variables(self):
        """Add BaseAgent configuration variables"""
        
        # AgentConfig variables
        base_config_vars = [
            VariableDefinition(
                name="config.name", layer="BaseAgent", type="str",
                current_value="", default_value="agent",
                description="Agent's unique identifier name",
                editable=False,  # Usually shouldn't change at runtime
                affects=["logging", "registry", "message_routing"]
            ),
            VariableDefinition(
                name="config.role", layer="BaseAgent", type="str", 
                current_value="", default_value="general",
                description="Agent's role in the system",
                affects=["agent_tier", "permissions", "task_routing"]
            ),
            VariableDefinition(
                name="config.goals", layer="BaseAgent", type="list",
                current_value=[], default_value=[],
                description="List of agent goals that drive behavior",
                affects=["decision_making", "task_prioritization"]
            ),
            VariableDefinition(
                name="config.tools", layer="BaseAgent", type="list",
                current_value=[], default_value=[],
                description="Available tools for the agent",
                affects=["capabilities", "action_execution"]
            ),
            VariableDefinition(
                name="config.compute_allocation", layer="BaseAgent", type="float",
                current_value=5.0, default_value=5.0,
                description="Percentage of total TOPS allocated",
                validation_rules={"min": 0.1, "max": 100.0},
                affects=["performance", "resource_usage"]
            ),
            VariableDefinition(
                name="config.memory_limit_gb", layer="BaseAgent", type="float",
                current_value=8.0, default_value=8.0,
                description="Memory limit in GB",
                validation_rules={"min": 0.5, "max": 128.0},
                affects=["memory_management", "performance"]
            ),
            VariableDefinition(
                name="config.zone", layer="BaseAgent", type="str",
                current_value="default", default_value="default",
                description="Deployment zone for the agent",
                affects=["networking", "resource_allocation"]
            ),
            VariableDefinition(
                name="config.model", layer="BaseAgent", type="str",
                current_value="llama-maverick-30b", default_value="llama-maverick-30b",
                description="LLM model to use for reasoning",
                affects=["reasoning_quality", "response_time", "cost"]
            ),
            VariableDefinition(
                name="config.temperature", layer="BaseAgent", type="float",
                current_value=0.7, default_value=0.7,
                description="LLM temperature for response creativity",
                validation_rules={"min": 0.0, "max": 2.0},
                affects=["response_creativity", "consistency"]
            ),
            VariableDefinition(
                name="config.max_concurrent_tasks", layer="BaseAgent", type="int",
                current_value=5, default_value=5,
                description="Maximum concurrent tasks",
                validation_rules={"min": 1, "max": 50},
                affects=["throughput", "resource_usage"]
            ),
        ]
        
        # Runtime state variables
        runtime_vars = [
            VariableDefinition(
                name="state", layer="BaseAgent", type="str",
                current_value="idle", default_value="initializing", 
                description="Current agent state",
                affects=["availability", "task_acceptance"]
            ),
            VariableDefinition(
                name="active", layer="BaseAgent", type="bool",
                current_value=True, default_value=True,
                description="Whether agent is active",
                affects=["task_processing", "message_handling"]
            ),
            VariableDefinition(
                name="api_call_count", layer="BaseAgent", type="int",
                current_value=0, default_value=0,
                description="Number of API calls made",
                editable=False,
                affects=["cost_tracking", "rate_limiting"]
            ),
            VariableDefinition(
                name="daily_cost", layer="BaseAgent", type="float",
                current_value=0.0, default_value=0.0,
                description="Daily cost accumulation",
                editable=False,
                affects=["budget_management", "cost_alerts"]
            ),
            VariableDefinition(
                name="cost_optimization_enabled", layer="BaseAgent", type="bool",
                current_value=True, default_value=True,
                description="Enable cost optimization features",
                affects=["api_usage", "message_filtering", "smart_batching"]
            ),
        ]
        
        for var in base_config_vars + runtime_vars:
            self.variable_definitions[var.name] = var
            
    def _add_llm_client_variables(self):
        """Add LLMClient configuration variables"""
        
        llm_vars = [
            VariableDefinition(
                name="llm.config.provider", layer="LLMClient", type="str",
                current_value="ollama", default_value="ollama",
                description="LLM provider (ollama, openai, anthropic)",
                affects=["model_availability", "cost", "performance"]
            ),
            VariableDefinition(
                name="llm.config.base_url", layer="LLMClient", type="str",
                current_value="http://localhost:11434", default_value="http://localhost:11434",
                description="Base URL for LLM provider",
                affects=["connectivity", "response_time"]
            ),
            VariableDefinition(
                name="llm.config.api_key", layer="LLMClient", type="str",
                current_value="", default_value="",
                description="API key for cloud providers",
                editable=True,  # Sensitive but controllable
                affects=["authentication", "service_access"]
            ),
            VariableDefinition(
                name="llm.config.max_tokens", layer="LLMClient", type="int",
                current_value=1000, default_value=1000,
                description="Maximum tokens per request",
                validation_rules={"min": 50, "max": 32000},
                affects=["response_length", "cost", "timeout"]
            ),
            VariableDefinition(
                name="llm.config.timeout", layer="LLMClient", type="int",
                current_value=30, default_value=30,
                description="Request timeout in seconds",
                validation_rules={"min": 5, "max": 300},
                affects=["reliability", "user_experience"]
            ),
        ]
        
        for var in llm_vars:
            self.variable_definitions[var.name] = var
            
    def _add_cost_management_variables(self):
        """Add cost management configuration variables"""
        
        cost_vars = [
            VariableDefinition(
                name="cost.optimization_enabled", layer="CostManagement", type="bool",
                current_value=True, default_value=True,
                description="Enable global cost optimization",
                affects=["api_usage", "performance", "functionality"]
            ),
            VariableDefinition(
                name="cost.idle_mode.enabled", layer="CostManagement", type="bool",
                current_value=True, default_value=True,
                description="Enable agent idle mode",
                affects=["api_usage", "responsiveness"]
            ),
            VariableDefinition(
                name="cost.idle_mode.check_interval_seconds", layer="CostManagement", type="int",
                current_value=5, default_value=5,
                description="Seconds between idle checks",
                validation_rules={"min": 1, "max": 60},
                affects=["responsiveness", "cpu_usage"]
            ),
            VariableDefinition(
                name="cost.rate_limiting.max_calls_per_minute", layer="CostManagement", type="int",
                current_value=30, default_value=30,
                description="Max API calls per minute per agent",
                validation_rules={"min": 1, "max": 1000},
                affects=["throughput", "cost", "responsiveness"]
            ),
            VariableDefinition(
                name="cost.rate_limiting.max_calls_per_hour", layer="CostManagement", type="int",
                current_value=300, default_value=300,
                description="Max API calls per hour per agent",
                validation_rules={"min": 10, "max": 10000},
                affects=["sustained_performance", "cost"]
            ),
            VariableDefinition(
                name="cost.cost_monitoring.daily_budget_usd", layer="CostManagement", type="float",
                current_value=50.0, default_value=50.0,
                description="Daily spending limit in USD",
                validation_rules={"min": 1.0, "max": 1000.0},
                affects=["cost_control", "agent_availability"]
            ),
            VariableDefinition(
                name="cost.cost_monitoring.warning_threshold_usd", layer="CostManagement", type="float",
                current_value=40.0, default_value=40.0,
                description="Warning threshold in USD",
                validation_rules={"min": 0.5, "max": 999.0},
                affects=["alerts", "monitoring"]
            ),
            VariableDefinition(
                name="cost.smart_batching.enabled", layer="CostManagement", type="bool",
                current_value=True, default_value=True,
                description="Enable smart message batching",
                affects=["efficiency", "response_latency", "cost"]
            ),
            VariableDefinition(
                name="cost.smart_batching.batch_size", layer="CostManagement", type="int",
                current_value=5, default_value=5,
                description="Messages per batch",
                validation_rules={"min": 1, "max": 20},
                affects=["efficiency", "latency"]
            ),
        ]
        
        for var in cost_vars:
            self.variable_definitions[var.name] = var
            
    def _add_agent_specific_variables(self):
        """Add agent-specific variables for Solomon, David, etc."""
        
        # Solomon-specific variables
        solomon_vars = [
            VariableDefinition(
                name="solomon.decision_framework.maximize", layer="Solomon", type="list",
                current_value=["freedom", "wellbeing", "wealth"], 
                default_value=["freedom", "wellbeing", "wealth"],
                description="Values to maximize in decisions",
                affects=["decision_making", "goal_prioritization"]
            ),
            VariableDefinition(
                name="solomon.decision_framework.protect", layer="Solomon", type="list",
                current_value=["ryan_benefits", "work_life_balance"],
                default_value=["ryan_benefits", "work_life_balance"],
                description="Values to protect in decisions",
                affects=["decision_constraints", "risk_management"]
            ),
            VariableDefinition(
                name="solomon.decision_framework.target", layer="Solomon", type="str",
                current_value="15k_monthly_revenue", default_value="15k_monthly_revenue",
                description="Primary revenue target",
                affects=["strategic_planning", "resource_allocation"]
            ),
            VariableDefinition(
                name="solomon.business_kpis.revenue", layer="Solomon", type="float",
                current_value=0.0, default_value=0.0,
                description="Current revenue tracking",
                affects=["reporting", "decision_making"]
            ),
        ]
        
        # David-specific variables  
        david_vars = [
            VariableDefinition(
                name="david.strategic_plan.vision", layer="David", type="str",
                current_value="Create an autonomous AI ecosystem generating sustainable revenue",
                default_value="Create an autonomous AI ecosystem generating sustainable revenue",
                description="Company vision statement",
                affects=["strategic_direction", "goal_alignment"]
            ),
            VariableDefinition(
                name="david.priorities.high", layer="David", type="list",
                current_value=["revenue_generation", "cost_optimization"],
                default_value=["revenue_generation", "cost_optimization"],
                description="High priority initiatives",
                affects=["resource_allocation", "task_prioritization"]
            ),
            VariableDefinition(
                name="david.performance_metrics.revenue_targets.monthly", layer="David", type="float",
                current_value=15000.0, default_value=15000.0,
                description="Monthly revenue target",
                validation_rules={"min": 1000.0, "max": 100000.0},
                affects=["performance_tracking", "goal_setting"]
            ),
        ]
        
        for var in solomon_vars + david_vars:
            self.variable_definitions[var.name] = var
            
    def _add_memory_variables(self):
        """Add memory management variables"""
        
        memory_vars = [
            VariableDefinition(
                name="memory.max_short_term", layer="Memory", type="int",
                current_value=100, default_value=100,
                description="Maximum short-term memories",
                validation_rules={"min": 10, "max": 1000},
                affects=["memory_usage", "recall_speed"]
            ),
            VariableDefinition(
                name="memory.short_term_count", layer="Memory", type="int",
                current_value=0, default_value=0,
                description="Current short-term memory count",
                editable=False,
                affects=["memory_status"]
            ),
            VariableDefinition(
                name="memory.long_term_count", layer="Memory", type="int",
                current_value=0, default_value=0,
                description="Current long-term memory count", 
                editable=False,
                affects=["memory_status"]
            ),
        ]
        
        for var in memory_vars:
            self.variable_definitions[var.name] = var
            
    def _add_message_bus_variables(self):
        """Add message bus configuration variables"""
        
        bus_vars = [
            VariableDefinition(
                name="message_bus.queue_size", layer="MessageBus", type="int",
                current_value=0, default_value=0,
                description="Current message queue size",
                editable=False,
                affects=["throughput", "latency"]
            ),
            VariableDefinition(
                name="message_bus.max_queue_size", layer="MessageBus", type="int",
                current_value=1000, default_value=1000,
                description="Maximum message queue size",
                validation_rules={"min": 10, "max": 10000},
                affects=["memory_usage", "reliability"]
            ),
        ]
        
        for var in bus_vars:
            self.variable_definitions[var.name] = var
    
    def register_agent_instance(self, agent: BaseAgent):
        """Register a live agent instance for variable control"""
        self.agent_instances[agent.config.name] = agent
        self._update_variables_from_agent(agent)
        
    def _update_variables_from_agent(self, agent: BaseAgent):
        """Update variable current values from live agent"""
        agent_name = agent.config.name
        
        # Update BaseAgent variables
        if "config.name" in self.variable_definitions:
            self.variable_definitions["config.name"].current_value = agent.config.name
        if "config.role" in self.variable_definitions:
            self.variable_definitions["config.role"].current_value = agent.config.role
        if "config.goals" in self.variable_definitions:
            self.variable_definitions["config.goals"].current_value = agent.config.goals
        if "config.tools" in self.variable_definitions:
            self.variable_definitions["config.tools"].current_value = agent.config.tools
        if "config.temperature" in self.variable_definitions:
            self.variable_definitions["config.temperature"].current_value = agent.config.temperature
        if "state" in self.variable_definitions:
            self.variable_definitions["state"].current_value = agent.state.value
        if "api_call_count" in self.variable_definitions:
            self.variable_definitions["api_call_count"].current_value = agent.api_call_count
        if "daily_cost" in self.variable_definitions:
            self.variable_definitions["daily_cost"].current_value = agent.daily_cost
            
        # Update memory variables
        if "memory.max_short_term" in self.variable_definitions:
            self.variable_definitions["memory.max_short_term"].current_value = agent.memory.max_short_term
        if "memory.short_term_count" in self.variable_definitions:
            self.variable_definitions["memory.short_term_count"].current_value = len(agent.memory.short_term)
        if "memory.long_term_count" in self.variable_definitions:
            self.variable_definitions["memory.long_term_count"].current_value = len(agent.memory.long_term)
            
        # Update LLM variables
        if hasattr(agent, 'llm') and agent.llm:
            if "llm.config.provider" in self.variable_definitions:
                self.variable_definitions["llm.config.provider"].current_value = agent.llm.config.provider
            if "llm.config.max_tokens" in self.variable_definitions:
                self.variable_definitions["llm.config.max_tokens"].current_value = agent.llm.config.max_tokens
                
        # Update agent-specific variables (Solomon, David, etc.)
        if hasattr(agent, 'decision_framework') and agent_name == "solomon":
            if "solomon.decision_framework.maximize" in self.variable_definitions:
                self.variable_definitions["solomon.decision_framework.maximize"].current_value = agent.decision_framework.get("maximize", [])
                
    def get_variables_by_layer(self, layer: str = None) -> Dict[str, VariableDefinition]:
        """Get variables filtered by layer"""
        if layer is None:
            return self.variable_definitions
        return {k: v for k, v in self.variable_definitions.items() if v.layer == layer}
        
    def get_variables_by_agent(self, agent_name: str) -> Dict[str, VariableDefinition]:
        """Get variables that affect a specific agent"""
        agent_vars = {}
        
        # Always include BaseAgent, LLMClient, CostManagement, Memory variables
        for name, var in self.variable_definitions.items():
            if var.layer in ["BaseAgent", "LLMClient", "CostManagement", "Memory", "MessageBus"]:
                agent_vars[name] = var
            elif var.layer.lower() == agent_name.lower():
                agent_vars[name] = var
                
        return agent_vars
        
    def update_variable(self, variable_name: str, new_value: Any, agent_name: str = None) -> bool:
        """Update a variable value in both definition and live agent"""
        if variable_name not in self.variable_definitions:
            return False
            
        var_def = self.variable_definitions[variable_name]
        
        if not var_def.editable:
            return False
            
        # Validate new value
        if not self._validate_value(var_def, new_value):
            return False
            
        # Update definition
        var_def.current_value = new_value
        
        # Update live agent instance if available
        if agent_name and agent_name in self.agent_instances:
            self._apply_variable_to_agent(variable_name, new_value, self.agent_instances[agent_name])
            
        return True
        
    def _validate_value(self, var_def: VariableDefinition, value: Any) -> bool:
        """Validate a new value against variable definition"""
        # Type checking
        expected_type = var_def.type
        if expected_type == "str" and not isinstance(value, str):
            return False
        elif expected_type == "int" and not isinstance(value, int):
            return False
        elif expected_type == "float" and not isinstance(value, (int, float)):
            return False
        elif expected_type == "bool" and not isinstance(value, bool):
            return False
        elif expected_type == "list" and not isinstance(value, list):
            return False
        elif expected_type == "dict" and not isinstance(value, dict):
            return False
            
        # Validation rules
        if var_def.validation_rules:
            if "min" in var_def.validation_rules and value < var_def.validation_rules["min"]:
                return False
            if "max" in var_def.validation_rules and value > var_def.validation_rules["max"]:
                return False
                
        return True
        
    def _apply_variable_to_agent(self, variable_name: str, value: Any, agent: BaseAgent):
        """Apply variable change to live agent instance"""
        try:
            # Parse the variable path and apply to agent
            if variable_name.startswith("config."):
                attr_name = variable_name.split(".", 1)[1]
                if hasattr(agent.config, attr_name):
                    setattr(agent.config, attr_name, value)
                    
            elif variable_name.startswith("memory."):
                attr_name = variable_name.split(".", 1)[1]
                if attr_name == "max_short_term":
                    agent.memory.max_short_term = value
                    
            elif variable_name.startswith("llm.config."):
                attr_name = variable_name.split(".", 2)[2]
                if hasattr(agent.llm.config, attr_name):
                    setattr(agent.llm.config, attr_name, value)
                    
            elif variable_name == "state":
                if isinstance(value, str):
                    agent.state = AgentState(value)
                    
            elif variable_name == "active":
                agent.active = value
                
            elif variable_name == "cost_optimization_enabled":
                agent.cost_optimization_enabled = value
                
            # Agent-specific variables
            elif variable_name.startswith("solomon.") and hasattr(agent, 'decision_framework'):
                # Handle Solomon-specific variables
                if variable_name == "solomon.decision_framework.maximize":
                    agent.decision_framework["maximize"] = value
                elif variable_name == "solomon.decision_framework.protect":
                    agent.decision_framework["protect"] = value
                elif variable_name == "solomon.decision_framework.target":
                    agent.decision_framework["target"] = value
                    
        except Exception as e:
            self.logger.error(f"Error applying variable {variable_name} to agent: {e}")
            return False
            
        return True
        
    def get_variable_summary(self) -> Dict[str, Any]:
        """Get summary of all variables organized by layer"""
        summary = {}
        
        for layer in ["BaseAgent", "LLMClient", "CostManagement", "Memory", "MessageBus", "Solomon", "David"]:
            layer_vars = self.get_variables_by_layer(layer)
            if layer_vars:
                summary[layer] = {
                    "count": len(layer_vars),
                    "editable_count": len([v for v in layer_vars.values() if v.editable]),
                    "variables": {name: {
                        "current_value": var.current_value,
                        "type": var.type,
                        "editable": var.editable,
                        "description": var.description
                    } for name, var in layer_vars.items()}
                }
                
        return summary
        
    def export_configuration(self) -> Dict[str, Any]:
        """Export current configuration for backup"""
        return {
            "timestamp": datetime.now().isoformat(),
            "variables": {name: {
                "layer": var.layer,
                "current_value": var.current_value,
                "type": var.type
            } for name, var in self.variable_definitions.items() if var.editable}
        }
        
    def import_configuration(self, config: Dict[str, Any]) -> bool:
        """Import configuration from backup"""
        try:
            for var_name, var_data in config.get("variables", {}).items():
                if var_name in self.variable_definitions:
                    self.variable_definitions[var_name].current_value = var_data["current_value"]
            return True
        except Exception as e:
            self.logger.error(f"Error importing configuration: {e}")
            return False


# Global instance
agent_variable_inspector = AgentVariableInspector()
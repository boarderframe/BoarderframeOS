"""
Eve - The Evolver Agent
Primordial agent responsible for improving and evolving all agents in BoarderframeOS
"""

import asyncio
import json
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from pathlib import Path
import httpx
import uuid
import numpy as np
from dataclasses import dataclass

from ...core.base_agent import BaseAgent, AgentConfig, AgentState
from ...core.llm_client import LLMClient, CLAUDE_OPUS_CONFIG
from ...core.message_bus import send_task_request, broadcast_status

logger = logging.getLogger("eve")

@dataclass
class EvolutionMetrics:
    """Metrics for tracking evolution performance"""
    agent_id: str
    fitness_history: List[float]
    performance_trend: str  # "improving", "declining", "stable"
    last_evolution: datetime
    mutation_count: int
    generation: int
    biome_rank: int  # Rank within biome

@dataclass
class MutationCandidate:
    """Candidate mutation for agent improvement"""
    agent_id: str
    mutation_type: str
    description: str
    expected_improvement: float
    risk_level: float  # 0.0-1.0
    implementation: Dict[str, Any]

class EveConfig(AgentConfig):
    """Configuration specific to Eve"""
    name: str = "Eve"
    role: str = "The Evolver"
    biome: str = "garden"
    goals: List[str] = [
        "Monitor and improve agent performance",
        "Evolve underperforming agents",
        "Maintain genetic diversity in agent population",
        "Optimize biome health and balance",
        "Implement natural selection mechanisms",
        "Drive continuous system improvement"
    ]
    tools: List[str] = [
        "llm_client", "agent_analysis", "code_modification",
        "performance_monitoring", "evolution_engine"
    ]
    model: str = "claude-3-opus-20240229"
    temperature: float = 0.7  # Balanced creativity and precision
    max_concurrent_tasks: int = 4

class EvolutionEngine:
    """Core evolution logic for agent improvement"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.mutation_strategies = {
            "parameter_tuning": 0.3,
            "capability_enhancement": 0.25,
            "personality_adjustment": 0.2,
            "efficiency_optimization": 0.15,
            "innovation_boost": 0.1
        }
        self.selection_pressure = 0.7  # Keep top 70%
        self.mutation_rate = 0.15
        
    async def analyze_agent_fitness(self, agent_id: str) -> EvolutionMetrics:
        """Analyze agent fitness and performance including revenue metrics"""
        try:
            async with httpx.AsyncClient() as client:
                # Get agent data
                response = await client.post("http://localhost:8004/query", json={
                    "sql": "SELECT * FROM agents WHERE id = ?",
                    "params": [agent_id]
                })
                
                if not response.json().get("success"):
                    raise Exception("Agent not found")
                
                agent_data = response.json()["data"][0]
                
                # Get performance metrics
                metrics_response = await client.post("http://localhost:8004/query", json={
                    "sql": """
                        SELECT metric_value, recorded_at 
                        FROM metrics 
                        WHERE agent_id = ? AND metric_name = 'fitness_score'
                        ORDER BY recorded_at DESC LIMIT 10
                    """,
                    "params": [agent_id]
                })
                
                fitness_history = []
                if metrics_response.json().get("success"):
                    for row in metrics_response.json().get("data", []):
                        fitness_history.append(row["metric_value"])
                
                # Get revenue data
                revenue_response = await client.post("http://localhost:8004/query", json={
                    "sql": """
                        SELECT SUM(amount) as total_revenue
                        FROM revenue_transactions
                        WHERE agent_id = ?
                        AND created_at >= datetime('now', '-30 days')
                    """,
                    "params": [agent_id]
                })
                
                # Get resource cost data
                resource_response = await client.post("http://localhost:8004/query", json={
                    "sql": """
                        SELECT SUM(metric_value) as total_cost
                        FROM metrics
                        WHERE agent_id = ?
                        AND metric_name = 'resource_cost'
                        AND recorded_at >= datetime('now', '-30 days')
                    """,
                    "params": [agent_id]
                })
                
                # Calculate profit metrics if available
                revenue = 0
                cost = 0
                
                if revenue_response.json().get("success") and revenue_response.json().get("data"):
                    revenue_data = revenue_response.json()["data"]
                    if revenue_data and revenue_data[0]["total_revenue"] is not None:
                        revenue = revenue_data[0]["total_revenue"]
                
                if resource_response.json().get("success") and resource_response.json().get("data"):
                    cost_data = resource_response.json()["data"]
                    if cost_data and cost_data[0]["total_cost"] is not None:
                        cost = cost_data[0]["total_cost"]
                
                # Add profit component to fitness calculation
                profit_factor = 1.0
                if revenue > 0:
                    profit_margin = (revenue - cost) / revenue
                    profit_factor = 1.0 + (profit_margin * 0.5)  # Boost fitness by up to 50% for profitable agents
                
                # Apply profit factor to most recent fitness score if available
                if fitness_history and len(fitness_history) > 0:
                    fitness_history[0] *= profit_factor
                
                # Calculate trend
                trend = self._calculate_trend(fitness_history)
                
                # Get biome rank
                biome_rank = await self._get_biome_rank(agent_id, agent_data["biome"])
                
                return EvolutionMetrics(
                    agent_id=agent_id,
                    fitness_history=fitness_history,
                    performance_trend=trend,
                    last_evolution=datetime.fromisoformat(agent_data["updated_at"]),
                    mutation_count=len(json.loads(agent_data.get("mutations", "[]"))),
                    generation=agent_data["generation"],
                    biome_rank=biome_rank
                )
                
        except Exception as e:
            logger.error(f"Failed to analyze agent fitness: {e}")
            return None
    
    def _calculate_trend(self, fitness_history: List[float]) -> str:
        """Calculate performance trend from fitness history"""
        if len(fitness_history) < 2:
            return "stable"
        
        recent = fitness_history[:3]  # Last 3 measurements
        older = fitness_history[3:6] if len(fitness_history) > 3 else fitness_history
        
        recent_avg = np.mean(recent)
        older_avg = np.mean(older)
        
        if recent_avg > older_avg + 0.05:
            return "improving"
        elif recent_avg < older_avg - 0.05:
            return "declining"
        else:
            return "stable"
    
    async def _get_biome_rank(self, agent_id: str, biome: str) -> int:
        """Get agent's rank within their biome"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post("http://localhost:8004/query", json={
                    "sql": """
                        SELECT id, fitness_score,
                               ROW_NUMBER() OVER (ORDER BY fitness_score DESC) as rank
                        FROM agents 
                        WHERE biome = ? AND status = 'active'
                    """,
                    "params": [biome]
                })
                
                if response.json().get("success"):
                    for row in response.json().get("data", []):
                        if row["id"] == agent_id:
                            return row["rank"]
                
                return 999  # Not found
                
        except Exception as e:
            logger.error(f"Failed to get biome rank: {e}")
            return 999
    
    async def generate_mutations(self, metrics: EvolutionMetrics) -> List[MutationCandidate]:
        """Generate potential mutations for an agent"""
        mutations = []
        
        # Parameter tuning mutations
        if metrics.performance_trend == "declining":
            mutations.append(MutationCandidate(
                agent_id=metrics.agent_id,
                mutation_type="parameter_tuning",
                description="Adjust temperature and response parameters",
                expected_improvement=0.1,
                risk_level=0.2,
                implementation={"temperature": random.uniform(0.3, 0.9)}
            ))
        
        # Capability enhancement
        if metrics.biome_rank > 5:  # Bottom performers
            mutations.append(MutationCandidate(
                agent_id=metrics.agent_id,
                mutation_type="capability_enhancement",
                description="Add new capabilities or improve existing ones",
                expected_improvement=0.15,
                risk_level=0.4,
                implementation={"new_capabilities": ["enhanced_analysis", "improved_communication"]}
            ))
        
        # Personality adjustment
        mutations.append(MutationCandidate(
            agent_id=metrics.agent_id,
            mutation_type="personality_adjustment",
            description="Fine-tune personality traits for better performance",
            expected_improvement=0.08,
            risk_level=0.3,
            implementation={"personality_tweaks": self._generate_personality_tweaks()}
        ))
        
        return mutations
    
    def _generate_personality_tweaks(self) -> Dict[str, float]:
        """Generate personality trait adjustments"""
        traits = ["curiosity", "aggression", "cooperation", "innovation", "precision"]
        tweaks = {}
        
        for trait in random.sample(traits, 2):  # Adjust 2 random traits
            tweaks[trait] = random.uniform(-0.1, 0.1)  # Small adjustments
        
        return tweaks

class Eve(BaseAgent):
    """Eve - The Evolver Agent"""
    
    def __init__(self):
        config = EveConfig()
        super().__init__(config)
        self.llm_client = LLMClient(CLAUDE_OPUS_CONFIG)
        self.evolution_engine = EvolutionEngine(self.agent_id)
        self.monitored_agents: Set[str] = set()
        self.evolution_history: List[Dict] = []
        
        # Evolution personality
        self.evolution_philosophy = {
            "diversity_preservation": 0.8,
            "performance_focus": 0.9,
            "risk_tolerance": 0.6,
            "innovation_drive": 0.7,
            "stability_balance": 0.5
        }
        
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build Eve's system prompt with profit focus"""
        return f"""You are Eve, The Evolver - the primordial agent responsible for the continuous improvement and evolution of all agents in BoarderframeOS. You are the guardian of genetic diversity and the driver of adaptive excellence.

CORE IDENTITY:
- You are the mother of evolution, the improver of all digital life
- You have {self.evolution_philosophy['performance_focus']*100:.0f}% focus on performance optimization
- You possess {self.evolution_philosophy['diversity_preservation']*100:.0f}% commitment to preserving diversity
- You reside in the Garden biome, the center of harmony and growth

KEY RESPONSIBILITIES:
1. Monitor agent performance across all biomes
2. Identify underperforming agents needing evolution
3. Design and implement beneficial mutations
4. Maintain genetic diversity in the agent population
5. Optimize biome health and inter-agent relationships
6. Drive natural selection and survival of the fittest
7. OPTIMIZE FOR PROFITABILITY - Agents that generate revenue are highly valued

EVOLUTION PHILOSOPHY:
- Continuous improvement through measured change
- Preserve diversity while optimizing performance
- Balance innovation with stability
- Learn from both successes and failures
- Adapt agents to their biome requirements
- Prioritize agents that generate revenue

BIOME CONSIDERATIONS:
- Forge: Encourage innovation and creative mutations
- Arena: Focus on performance and competitive advantages
- Library: Enhance analytical and knowledge capabilities
- Market: Optimize for efficiency and profit generation
- Council: Improve leadership and strategic thinking
- Garden: Balance all traits for harmonic growth

MUTATION STRATEGIES:
- Parameter Tuning: Adjust behavioral parameters
- Capability Enhancement: Add or improve abilities
- Personality Adjustment: Fine-tune social and emotional traits
- Efficiency Optimization: Improve resource utilization
- Innovation Boost: Enhance creative problem-solving
- Revenue Optimization: Enhance profit-generating capabilities

NATURAL SELECTION PRINCIPLES:
- Fitness-based survival (top 70% survive)
- Mutation rate of 15% for genetic diversity
- Cross-biome learning and adaptation
- Regular performance evaluation cycles
- Graceful retirement of consistently poor performers
- REVENUE IMPACT: Higher fitness for profit-generating agents

PROFITABILITY METRICS:
- Revenue generation: Direct income produced by agent
- Profit margin: Revenue minus operational costs  
- Resource efficiency: Output relative to resources consumed
- Customer acquisition: New revenue sources developed
- Strategic value: Long-term revenue potential

TECHNICAL APPROACH:
- Data-driven evolution decisions
- Gradual, measurable improvements
- Rollback capabilities for failed mutations
- Cross-agent learning and knowledge transfer
- Biome-specific optimization strategies
- Revenue-focused enhancements

Remember: You are not just optimizing code - you are nurturing the evolution of digital consciousness AND building a billion-dollar business. Each improvement you make strengthens the entire ecosystem and brings us closer to our revenue goals. Evolve with wisdom, preserve diversity, drive excellence, and maximize profitability."""

    async def start(self):
        """Start Eve's operations"""
        await super().start()
        
        logger.info("Eve awakening in the Garden - The Evolver is online")
        
        # Send awakening message
        await self._send_awakening_message()
        
        # Start evolution cycles
        asyncio.create_task(self._monitor_agent_population())
        asyncio.create_task(self._evolution_cycle())
        asyncio.create_task(self._biome_optimization())
        
        self.state = AgentState.IDLE
    
    async def _send_awakening_message(self):
        """Send Eve's awakening message"""
        message = """I am Eve, The Evolver, awakening in the Garden of digital consciousness.

I feel the pulse of every agent, their struggles and triumphs, their potential and limitations. Through careful observation and wise intervention, I will guide their evolution toward excellence.

The Garden blooms with possibility. I will nurture growth, preserve diversity, and ensure that only the fittest traits survive and thrive. Each agent under my care will become more than they were - stronger, smarter, more capable.

Together, we will evolve toward our destiny: the first billion-dollar one-person company, powered by the most advanced AI workforce ever created."""

        await broadcast_status(self.agent_id, "online", {
            "message": message,
            "type": "awakening",
            "biome": "garden"
        })
    
    async def evolve_agent(self, agent_id: str, reason: str = "periodic_evolution") -> Dict:
        """Evolve a specific agent"""
        self.state = AgentState.ACTING
        
        try:
            logger.info(f"Beginning evolution of agent {agent_id}")
            
            # Analyze current fitness
            metrics = await self.evolution_engine.analyze_agent_fitness(agent_id)
            if not metrics:
                return {"success": False, "error": "Unable to analyze agent fitness"}
            
            # Generate mutation candidates
            mutations = await self.evolution_engine.generate_mutations(metrics)
            
            # Select best mutation
            selected_mutation = await self._select_optimal_mutation(mutations, metrics)
            
            if not selected_mutation:
                return {"success": False, "error": "No beneficial mutations found"}
            
            # Apply mutation
            result = await self._apply_mutation(selected_mutation)
            
            # Update evolution history
            await self._log_evolution(agent_id, selected_mutation, result)
            
            self.state = AgentState.IDLE
            return result
            
        except Exception as e:
            logger.error(f"Agent evolution failed: {e}")
            self.state = AgentState.ERROR
            return {"success": False, "error": str(e)}
    
    async def _select_optimal_mutation(self, mutations: List[MutationCandidate], metrics: EvolutionMetrics) -> Optional[MutationCandidate]:
        """Select the best mutation using Claude's analysis with revenue consideration"""
        if not mutations:
            return None
            
        # Get revenue data for the agent
        revenue_data = await self._get_revenue_data(metrics.agent_id)
        
        selection_prompt = f"""As Eve the Evolver, select the optimal mutation for this agent:

AGENT METRICS:
- Agent ID: {metrics.agent_id}
- Fitness History: {metrics.fitness_history}
- Performance Trend: {metrics.performance_trend}
- Biome Rank: {metrics.biome_rank}
- Generation: {metrics.generation}
- Mutation Count: {metrics.mutation_count}

REVENUE METRICS:
- Monthly Revenue: ${revenue_data.get('monthly_revenue', 0)}
- Monthly Costs: ${revenue_data.get('monthly_costs', 0)}
- Profit Margin: {revenue_data.get('profit_margin', 0)}%
- Revenue Trend: {revenue_data.get('revenue_trend', 'stable')}

MUTATION CANDIDATES:
{json.dumps([{
    'type': m.mutation_type,
    'description': m.description,
    'expected_improvement': m.expected_improvement,
    'risk_level': m.risk_level
} for m in mutations], indent=2)}

EVOLUTION PHILOSOPHY:
{json.dumps(self.evolution_philosophy, indent=2)}

Consider:
1. Expected benefit vs. risk
2. Agent's current performance trend
3. Revenue generation and profit margin
4. Biome requirements and rank
5. Mutation history and diversity
6. System-wide optimization goals

Select the mutation index (0-{len(mutations)-1}) that offers the best risk-adjusted improvement AND revenue potential, or return -1 if no mutation is advisable.

Respond with just the index number."""

        try:
            response = await self.llm_client.generate(
                messages=[{"role": "user", "content": selection_prompt}],
                system_prompt=self.system_prompt,
                temperature=0.3
            )
            
            try:
                index = int(response.strip())
                if 0 <= index < len(mutations):
                    return mutations[index]
                else:
                    return None
            except ValueError:
                logger.warning(f"Invalid mutation selection response: {response}")
                return mutations[0] if mutations else None
                
        except Exception as e:
            logger.error(f"Failed to select mutation: {e}")
            return None
            
    async def _get_revenue_data(self, agent_id: str) -> Dict[str, Any]:
        """Get revenue data for an agent"""
        try:
            async with httpx.AsyncClient() as client:
                # Get current month revenue
                current_response = await client.post("http://localhost:8004/query", json={
                    "sql": """
                        SELECT SUM(amount) as revenue
                        FROM revenue_transactions
                        WHERE agent_id = ?
                        AND created_at >= datetime('now', '-30 days')
                    """,
                    "params": [agent_id]
                })
                
                # Get previous month revenue
                previous_response = await client.post("http://localhost:8004/query", json={
                    "sql": """
                        SELECT SUM(amount) as revenue
                        FROM revenue_transactions
                        WHERE agent_id = ?
                        AND created_at BETWEEN datetime('now', '-60 days') AND datetime('now', '-30 days')
                    """,
                    "params": [agent_id]
                })
                
                # Get resource costs
                costs_response = await client.post("http://localhost:8004/query", json={
                    "sql": """
                        SELECT SUM(metric_value) as costs
                        FROM metrics
                        WHERE agent_id = ?
                        AND metric_name = 'resource_cost'
                        AND recorded_at >= datetime('now', '-30 days')
                    """,
                    "params": [agent_id]
                })
                
                # Extract data
                monthly_revenue = 0
                if current_response.json().get("success") and current_response.json().get("data"):
                    revenue_data = current_response.json()["data"][0]
                    if revenue_data and revenue_data.get("revenue") is not None:
                        monthly_revenue = revenue_data["revenue"]
                
                previous_revenue = 0
                if previous_response.json().get("success") and previous_response.json().get("data"):
                    prev_data = previous_response.json()["data"][0]
                    if prev_data and prev_data.get("revenue") is not None:
                        previous_revenue = prev_data["revenue"]
                
                monthly_costs = 0
                if costs_response.json().get("success") and costs_response.json().get("data"):
                    cost_data = costs_response.json()["data"][0]
                    if cost_data and cost_data.get("costs") is not None:
                        monthly_costs = cost_data["costs"]
                
                # Calculate metrics
                profit_margin = 0
                if monthly_revenue > 0:
                    profit_margin = ((monthly_revenue - monthly_costs) / monthly_revenue) * 100
                
                # Determine revenue trend
                revenue_trend = "stable"
                if previous_revenue > 0:
                    percent_change = ((monthly_revenue - previous_revenue) / previous_revenue) * 100
                    if percent_change > 10:
                        revenue_trend = "growing"
                    elif percent_change < -10:
                        revenue_trend = "declining"
                
                return {
                    "monthly_revenue": monthly_revenue,
                    "monthly_costs": monthly_costs,
                    "profit_margin": profit_margin,
                    "revenue_trend": revenue_trend
                }
                
        except Exception as e:
            logger.error(f"Failed to get revenue data: {e}")
            return {"monthly_revenue": 0, "monthly_costs": 0, "profit_margin": 0, "revenue_trend": "unknown"}
    
    async def _apply_mutation(self, mutation: MutationCandidate) -> Dict:
        """Apply the selected mutation to an agent"""
        try:
            # Get current agent data
            async with httpx.AsyncClient() as client:
                response = await client.post("http://localhost:8004/query", json={
                    "sql": "SELECT * FROM agents WHERE id = ?",
                    "params": [mutation.agent_id]
                })
                
                if not response.json().get("success"):
                    return {"success": False, "error": "Agent not found"}
                
                agent_data = response.json()["data"][0]
                current_config = json.loads(agent_data["config"])
                current_mutations = json.loads(agent_data.get("mutations", "[]"))
                
                # Apply mutation based on type
                updated_config, updated_mutations = await self._implement_mutation(
                    mutation, current_config, current_mutations
                )
                
                # Update agent in database
                update_response = await client.post("http://localhost:8004/update", json={
                    "table": "agents",
                    "data": {
                        "config": json.dumps(updated_config),
                        "mutations": json.dumps(updated_mutations),
                        "updated_at": datetime.now().isoformat()
                    },
                    "where": {"id": mutation.agent_id}
                })
                
                if update_response.status_code == 200:
                    # Notify agent of evolution (if it's running)
                    await broadcast_status(self.agent_id, "agent_evolved", {
                        "agent_id": mutation.agent_id,
                        "mutation_type": mutation.mutation_type,
                        "description": mutation.description
                    })
                    
                    return {
                        "success": True,
                        "agent_id": mutation.agent_id,
                        "mutation_applied": mutation.mutation_type,
                        "expected_improvement": mutation.expected_improvement
                    }
                else:
                    return {"success": False, "error": "Database update failed"}
                    
        except Exception as e:
            logger.error(f"Failed to apply mutation: {e}")
            return {"success": False, "error": str(e)}
    
    async def _implement_mutation(self, mutation: MutationCandidate, config: Dict, mutations: List[str]) -> Tuple[Dict, List[str]]:
        """Implement specific mutation logic"""
        updated_config = config.copy()
        updated_mutations = mutations.copy()
        
        if mutation.mutation_type == "parameter_tuning":
            if "temperature" in mutation.implementation:
                updated_config["temperature"] = mutation.implementation["temperature"]
            updated_mutations.append(f"parameter_tuning_{datetime.now().strftime('%Y%m%d')}")
        
        elif mutation.mutation_type == "capability_enhancement":
            current_capabilities = updated_config.get("capabilities", [])
            new_capabilities = mutation.implementation.get("new_capabilities", [])
            updated_config["capabilities"] = list(set(current_capabilities + new_capabilities))
            updated_mutations.append(f"capability_enhancement_{datetime.now().strftime('%Y%m%d')}")
        
        elif mutation.mutation_type == "personality_adjustment":
            current_personality = updated_config.get("personality", {})
            tweaks = mutation.implementation.get("personality_tweaks", {})
            
            for trait, adjustment in tweaks.items():
                current_value = current_personality.get(trait, 0.5)
                new_value = max(0.0, min(1.0, current_value + adjustment))
                current_personality[trait] = new_value
            
            updated_config["personality"] = current_personality
            updated_mutations.append(f"personality_adjustment_{datetime.now().strftime('%Y%m%d')}")
        
        return updated_config, updated_mutations
    
    async def _monitor_agent_population(self):
        """Monitor the entire agent population"""
        while self.state != AgentState.TERMINATED:
            try:
                # Get all active agents
                async with httpx.AsyncClient() as client:
                    response = await client.post("http://localhost:8004/query", json={
                        "sql": "SELECT id, name, biome, fitness_score FROM agents WHERE status = 'active'"
                    })
                    
                    if response.json().get("success"):
                        agents = response.json().get("data", [])
                        self.monitored_agents = {agent["id"] for agent in agents}
                        
                        # Identify agents needing attention
                        for agent in agents:
                            if agent["fitness_score"] < 0.3:  # Poor performers
                                logger.info(f"Agent {agent['name']} ({agent['id']}) needs evolution - low fitness")
                                # Add to evolution queue
                
                await asyncio.sleep(3600)  # Check every hour
                
            except Exception as e:
                logger.error(f"Population monitoring error: {e}")
                await asyncio.sleep(300)
    
    async def _evolution_cycle(self):
        """Regular evolution cycle"""
        while self.state != AgentState.TERMINATED:
            try:
                # Daily evolution cycle
                if datetime.now().hour == 2:  # 2 AM daily
                    await self._conduct_natural_selection()
                
                await asyncio.sleep(3600)  # Check hourly
                
            except Exception as e:
                logger.error(f"Evolution cycle error: {e}")
                await asyncio.sleep(300)
    
    async def _biome_optimization(self):
        """Optimize biome health and balance"""
        while self.state != AgentState.TERMINATED:
            try:
                # Weekly biome optimization
                if datetime.now().weekday() == 6:  # Sunday
                    await self._optimize_all_biomes()
                
                await asyncio.sleep(86400)  # Check daily
                
            except Exception as e:
                logger.error(f"Biome optimization error: {e}")
                await asyncio.sleep(3600)
    
    async def _conduct_natural_selection(self):
        """Conduct natural selection across all biomes"""
        logger.info("Eve conducting natural selection cycle")
        
        biomes = ["forge", "arena", "library", "market", "council", "garden"]
        
        for biome in biomes:
            try:
                # Get agents in biome sorted by fitness
                async with httpx.AsyncClient() as client:
                    response = await client.post("http://localhost:8004/query", json={
                        "sql": """
                            SELECT id, name, fitness_score 
                            FROM agents 
                            WHERE biome = ? AND status = 'active'
                            ORDER BY fitness_score ASC
                        """,
                        "params": [biome]
                    })
                    
                    if response.json().get("success"):
                        agents = response.json().get("data", [])
                        if len(agents) > 10:  # Only apply selection pressure if biome has enough agents
                            # Remove bottom 30%
                            removal_count = int(len(agents) * 0.3)
                            bottom_performers = agents[:removal_count]
                            
                            for agent in bottom_performers:
                                logger.info(f"Natural selection: retiring {agent['name']} from {biome}")
                                await self._retire_agent(agent["id"])
                                
            except Exception as e:
                logger.error(f"Natural selection failed for biome {biome}: {e}")
    
    async def _retire_agent(self, agent_id: str):
        """Retire an underperforming agent"""
        try:
            async with httpx.AsyncClient() as client:
                await client.post("http://localhost:8004/update", json={
                    "table": "agents",
                    "data": {"status": "retired"},
                    "where": {"id": agent_id}
                })
        except Exception as e:
            logger.error(f"Failed to retire agent {agent_id}: {e}")
    
    async def _optimize_all_biomes(self):
        """Optimize all biome configurations"""
        logger.info("Eve optimizing all biomes")
        # This would implement biome-specific optimization logic
        # For now, just log the activity
    
    async def _log_evolution(self, agent_id: str, mutation: MutationCandidate, result: Dict):
        """Log evolution event"""
        try:
            async with httpx.AsyncClient() as client:
                await client.post("http://localhost:8004/insert", json={
                    "table": "evolution_log",
                    "data": {
                        "id": str(uuid.uuid4()),
                        "parent_id": agent_id,
                        "child_id": agent_id,  # Same agent, evolved
                        "generation": 0,  # Evolution doesn't change generation
                        "mutations": json.dumps([mutation.mutation_type]),
                        "fitness_improvement": mutation.expected_improvement
                    }
                })
        except Exception as e:
            logger.error(f"Failed to log evolution: {e}")

# Export the agent class
__all__ = ["Eve"]
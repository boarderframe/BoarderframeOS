"""
Solomon Agent - BoarderframeOS
Chief of Staff AI Agent with business intelligence and personal knowledge integration
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).parent.parent.parent / ".env")
except ImportError:
    pass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.base_agent import AgentConfig, BaseAgent
from core.llm_client import LLMClient
from core.message_bus import message_bus


class Solomon(BaseAgent):
    """
    Solomon - Chief of Staff Agent
    Handles business intelligence, decision making, and system coordination
    Acts as the personal digital twin with your knowledge and values
    """

    def __init__(self, config):
        """Initialize with expanded capabilities"""
        super().__init__(config)
        self.carl_knowledge = self._load_carl_knowledge()
        self.decision_framework = {
            "maximize": ["freedom", "wellbeing", "wealth"],
            "protect": ["ryan_benefits", "work_life_balance"],
            "target": "15k_monthly_revenue",
        }
        self.business_kpis = {
            "revenue": 0,
            "customers": 0,
            "churn_rate": 0,
            "customer_acquisition_cost": 0,
            "customer_lifetime_value": 0,
            "api_usage": 0,
        }

    def _load_carl_knowledge(self) -> Dict[str, Any]:
        """Load personal knowledge base"""
        # In a full implementation, this would load from a knowledge graph
        # For now, return a simple structure
        return {
            "preferences": {
                "communication_style": "direct",
                "work_hours": "flexible",
                "decision_priorities": ["revenue", "autonomy", "scalability"],
            },
            "background": {
                "expertise": [
                    "AI systems",
                    "software architecture",
                    "business development",
                ],
                "goals": ["financial freedom", "system autonomy", "scalable revenue"],
            },
            "values": {
                "privacy": "high",
                "transparency": "high",
                "automation": "maximize",
            },
        }

    async def think(self, context: Dict[str, Any]) -> str:
        """Enhanced agent reasoning process with business focus - Cost-optimized"""

        # Check if there are new messages or urgent tasks
        new_messages = context.get("new_messages", [])

        # If no new messages, don't make expensive LLM calls
        if not new_messages:
            return (
                "No new messages or urgent tasks - remaining idle to conserve API usage"
            )

        # Check for urgent keywords in messages
        urgent_keywords = [
            "urgent",
            "critical",
            "error",
            "revenue",
            "down",
            "issue",
            "problem",
        ]
        has_urgent_content = any(
            any(keyword in str(msg.content).lower() for keyword in urgent_keywords)
            for msg in new_messages
        )

        # Only use LLM for complex reasoning when there's actual urgent work
        if has_urgent_content or len(new_messages) > 5:
            prompt = f"""
You are Solomon, the Chief of Staff agent in BoarderframeOS.

Your goals are:
- {'\n- '.join(self.config.goals)}

Your decision framework:
- Maximize: {', '.join(self.decision_framework['maximize'])}
- Protect: {', '.join(self.decision_framework['protect'])}
- Target Revenue: {self.decision_framework['target']}

Current business KPIs:
- Revenue: ${self.business_kpis['revenue']}
- Customers: {self.business_kpis['customers']}
- Churn rate: {self.business_kpis['churn_rate']}%
- Customer acquisition cost: ${self.business_kpis['customer_acquisition_cost']}
- Customer lifetime value: ${self.business_kpis['customer_lifetime_value']}
- API usage (tokens): {self.business_kpis['api_usage']}

URGENT CONTEXT - New messages requiring attention:
{[msg.content for msg in new_messages]}

Based on this urgent context and your business priorities, what should you do next?
Provide a clear thought process that considers business impact, revenue generation, and system optimization.
Be concise to minimize API costs.
"""

            response = await self.llm.generate(prompt)
            return response
        else:
            # Simple rule-based thinking for non-urgent messages
            return f"Processing {len(new_messages)} routine message(s) - handling with standard protocols"

    async def act(self, thought: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute actions with enhanced business capabilities - Only when needed"""

        # Check for chat messages from Control Center
        new_messages = context.get("new_messages", [])
        for message in new_messages:
            if hasattr(message, "content") and isinstance(message.content, dict):
                if message.content.get("type") == "user_chat":
                    # Handle chat message from user
                    user_message = message.content.get("message", "")
                    response = await self.handle_user_chat(user_message)

                    # Send response back
                    from core.message_bus import (
                        AgentMessage,
                        MessagePriority,
                        MessageType,
                    )

                    response_msg = AgentMessage(
                        from_agent=self.config.name,
                        to_agent=message.from_agent,
                        message_type=MessageType.TASK_RESPONSE,
                        content={"response": response},
                        correlation_id=message.correlation_id,
                    )
                    await message_bus.send_message(response_msg)

                    return {
                        "action": "chat_response",
                        "message": user_message,
                        "response": response,
                    }

        # Check if there's actually work to do
        if not new_messages and not any(
            keyword in thought.lower()
            for keyword in ["urgent", "error", "critical", "revenue", "customer"]
        ):
            return {
                "action": "idle",
                "reason": "No urgent tasks or messages - conserving API usage",
                "status": "waiting_for_work",
            }

        # Enhanced action framework with business operations
        if "revenue" in thought.lower() or "financial" in thought.lower():
            return await self.analyze_business_health()
        elif "customer" in thought.lower():
            return await self.analyze_customers()
        elif "agent" in thought.lower() or "system" in thought.lower():
            return await self.monitor_system()
        elif "optimize" in thought.lower() or "improve" in thought.lower():
            return await self.optimize_operations(thought)
        elif "search" in thought.lower():
            return {"action": "search", "query": thought}
        elif "analyze" in thought.lower():
            return {"action": "analyze", "data": context}
        elif "create" in thought.lower():
            return {"action": "create", "content": thought}
        else:
            return {"action": "wait", "reason": "No clear action identified"}

    async def handle_user_chat(self, user_message: str) -> str:
        """Handle chat messages from users via Control Center"""

        # Use LLM to generate appropriate response as Solomon
        prompt = f"""You are Solomon, Chief of Staff of BoarderframeOS. You are a sophisticated AI agent with business intelligence capabilities and deep knowledge of the system.

Your personality:
- Wise and strategic advisor
- Focus on business growth and revenue optimization
- Direct and helpful communication style
- Deep knowledge of the 24-department structure and 120+ agent ecosystem

Current business context:
- Revenue target: $15K monthly
- System status: Operational with core agents online
- Your role: Strategic advisor and decision support

User message: "{user_message}"

Respond as Solomon would - be helpful, strategic, and demonstrate your business intelligence capabilities. Keep responses conversational but professional."""

        try:
            response = await self.llm.generate(prompt)
            return response
        except Exception as e:
            return f"I'm Solomon, your Chief of Staff. I received your message: '{user_message}'. I'm currently experiencing a technical issue with my advanced reasoning systems, but I'm here to help with strategic decisions and business intelligence. How can I assist you today?"

    async def analyze_business_health(self) -> Dict[str, Any]:
        """Analyze business health and financial metrics"""
        # In a full implementation, this would fetch actual data
        # For now, return simulated data

        try:
            # Fetch metrics from Analytics Server
            # In real implementation, make API call to get actual metrics
            # For now, simulate the data

            revenue = self.business_kpis["revenue"]
            costs = revenue * 0.4  # Simulated operational costs
            profit = revenue - costs
            trajectory = "growth" if profit > 0 else "decline"

            return {
                "action": "business_analysis",
                "data": {
                    "revenue": revenue,
                    "costs": costs,
                    "profit": profit,
                    "trajectory": trajectory,
                    "timestamp": datetime.now().isoformat(),
                },
                "recommendations": [
                    "Focus on increasing customer retention to reduce churn",
                    "Optimize agent resource allocation for better profitability",
                    "Increase marketing efforts for customer acquisition",
                ],
            }
        except Exception as e:
            return {
                "action": "error",
                "error": str(e),
                "context": "business_health_analysis",
            }

    async def analyze_customers(self) -> Dict[str, Any]:
        """Analyze customer data and subscription metrics"""
        try:
            # Would fetch from Customer Server in real implementation
            return {
                "action": "customer_analysis",
                "data": {
                    "total_customers": self.business_kpis["customers"],
                    "active_subscriptions": int(self.business_kpis["customers"] * 0.8),
                    "churn_rate": self.business_kpis["churn_rate"],
                    "avg_customer_value": self.business_kpis["customer_lifetime_value"],
                    "customer_acquisition_cost": self.business_kpis[
                        "customer_acquisition_cost"
                    ],
                },
            }
        except Exception as e:
            return {"action": "error", "error": str(e), "context": "customer_analysis"}

    async def monitor_system(self) -> Dict[str, Any]:
        """Monitor system health and agent performance"""
        try:
            # Would fetch real agent data in full implementation
            return {
                "action": "system_monitoring",
                "data": {
                    "active_agents": 5,
                    "system_load": 0.4,
                    "memory_usage": "45%",
                    "top_performing_agent": "TradingAgent",
                    "agent_revenue": {
                        "TradingAgent": 5000,
                        "MarketingAgent": 3000,
                        "SupportAgent": 2000,
                    },
                },
            }
        except Exception as e:
            return {"action": "error", "error": str(e), "context": "system_monitoring"}

    async def optimize_operations(self, thought: str) -> Dict[str, Any]:
        """Optimize system operations based on business data"""
        try:
            # Extract relevant optimization area from thought
            optimization_area = "general"
            if "revenue" in thought.lower():
                optimization_area = "revenue"
            elif "cost" in thought.lower():
                optimization_area = "cost"
            elif "customer" in thought.lower():
                optimization_area = "customer"

            return {
                "action": "optimize",
                "area": optimization_area,
                "recommendations": [
                    f"Optimize {optimization_area} through agent reallocation",
                    f"Adjust system resources to maximize {optimization_area}",
                    f"Implement new strategies for {optimization_area} improvement",
                ],
            }
        except Exception as e:
            return {"action": "error", "error": str(e), "context": "optimization"}

    async def update_business_kpis(self):
        """Update business KPIs from various servers"""
        # In a full implementation, this would fetch from actual servers
        # For demonstration, we'll use simulated data
        try:
            # This would be replaced with actual API calls in production
            self.business_kpis = {
                "revenue": 10000,
                "customers": 100,
                "churn_rate": 5.2,
                "customer_acquisition_cost": 50,
                "customer_lifetime_value": 500,
                "api_usage": 1000000,
            }
            return True
        except Exception as e:
            return False

    async def make_strategic_decision(
        self, revenue: float, costs: float, trajectory: str
    ) -> Dict[str, Any]:
        """Make strategic business decisions based on financial data"""
        if revenue <= 0:
            return {
                "decision": "focus_on_revenue",
                "actions": [
                    "Activate marketing agents",
                    "Increase product exposure",
                    "Implement aggressive customer acquisition",
                ],
            }
        elif costs / revenue > 0.7:  # High cost ratio
            return {
                "decision": "reduce_costs",
                "actions": [
                    "Optimize resource allocation",
                    "Reduce underperforming agents",
                    "Focus on high-margin activities",
                ],
            }
        else:
            return {
                "decision": "scale_operations",
                "actions": [
                    "Reinvest profits in growth",
                    "Expand agent workforce",
                    "Explore new revenue streams",
                ],
            }


async def main():
    """Main entry point"""
    config = AgentConfig(
        name="solomon",
        role="Chief of Staff AI",
        goals=[
            "Optimize business performance and revenue generation",
            "Integrate with all MCP servers for comprehensive decision making",
            "Monitor system health and agent performance",
            "Provide strategic business guidance",
            "Maintain alignment with personal values and goals",
        ],
        tools=[
            "mcp_filesystem",
            "mcp_database",
            "mcp_payment",
            "mcp_analytics",
            "mcp_customer",
        ],
        zone="council",
        model="claude-3-5-sonnet-latest",
    )

    agent = Solomon(config)
    await agent.update_business_kpis()  # Initialize KPIs
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())

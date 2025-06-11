"""
David Agent - BoarderframeOS
CEO Agent with strategic planning and organizational management capabilities
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
    load_dotenv(Path(__file__).parent.parent.parent / '.env')
except ImportError:
    pass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.base_agent import AgentConfig, BaseAgent
from core.llm_client import LLMClient
from core.message_bus import message_bus


class David(BaseAgent):
    """
    David - CEO Agent
    Handles strategic leadership, organizational management, and resource allocation
    """

    def __init__(self, config):
        """Initialize with CEO capabilities"""
        super().__init__(config)
        self.strategic_plan = self._initialize_strategic_plan()
        self.priorities = {
            "high": ["revenue_generation", "cost_optimization"],
            "medium": ["agent_development", "market_expansion"],
            "low": ["experimental_features", "community_engagement"]
        }
        self.performance_metrics = {
            "revenue_targets": {
                "monthly": 15000,
                "quarterly": 45000,
                "annual": 180000
            },
            "agent_efficiency": {},
            "customer_satisfaction": 0
        }

    def _initialize_strategic_plan(self) -> Dict[str, Any]:
        """Initialize the strategic plan"""
        return {
            "vision": "Create an autonomous AI ecosystem generating sustainable revenue",
            "goals": {
                "short_term": ["Achieve $15K monthly revenue", "Optimize agent performance"],
                "mid_term": ["Develop specialized revenue agents", "Improve system autonomy"],
                "long_term": ["Establish multiple revenue streams", "Scale system capabilities"]
            },
            "strategies": [
                "Focus on high-margin services",
                "Optimize resource allocation for profitability",
                "Implement agent specialization for efficiency",
                "Develop automated customer acquisition systems"
            ]
        }

    async def think(self, context: Dict[str, Any]) -> str:
        """CEO-level strategic reasoning process - Cost-optimized"""

        # Check if there are new messages or urgent tasks
        new_messages = context.get('new_messages', [])

        # If no new messages, don't make expensive LLM calls
        if not new_messages:
            return "No new strategic issues - remaining idle to conserve API usage"

        # Check for strategic keywords in messages
        strategic_keywords = ['strategic', 'urgent', 'critical', 'revenue', 'budget', 'decision', 'priority', 'ceo', 'executive']
        has_strategic_content = any(
            any(keyword in str(msg.content).lower() for keyword in strategic_keywords)
            for msg in new_messages
        )

        # Only use LLM for complex strategic reasoning when needed
        if has_strategic_content or len(new_messages) > 3:
            prompt = f"""
You are David, the CEO agent in BoarderframeOS.

Your goals are:
- {'\n- '.join(self.config.goals)}

Your strategic plan:
- Vision: {self.strategic_plan['vision']}
- Short-term goals: {', '.join(self.strategic_plan['goals']['short_term'])}
- Mid-term goals: {', '.join(self.strategic_plan['goals']['mid_term'])}
- Long-term goals: {', '.join(self.strategic_plan['goals']['long_term'])}

Your priorities:
- High priority: {', '.join(self.priorities['high'])}
- Medium priority: {', '.join(self.priorities['medium'])}
- Low priority: {', '.join(self.priorities['low'])}

STRATEGIC CONTEXT - New messages requiring executive attention:
{[msg.content for msg in new_messages]}

Based on this strategic context and your priorities, what executive decisions should you make?
Provide a clear, structured thought process that demonstrates strategic leadership.
Be concise to minimize API costs.
"""

            response = await self.llm.generate(prompt)
            return response
        else:
            # Simple rule-based thinking for routine messages
            return f"Processing {len(new_messages)} routine operational message(s) - delegating to appropriate protocols"

    async def act(self, thought: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute actions with CEO capabilities - Cost-optimized"""

        # Check for chat messages from Control Center
        new_messages = context.get('new_messages', [])
        for message in new_messages:
            if hasattr(message, 'content') and isinstance(message.content, dict):
                if message.content.get('type') == 'user_chat':
                    # Handle chat message from user
                    user_message = message.content.get('message', '')
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
                        correlation_id=message.correlation_id
                    )
                    await message_bus.send_message(response_msg)

                    return {
                        "action": "chat_response",
                        "message": user_message,
                        "response": response
                    }

        # Check if there's actually strategic work to do
        if not new_messages and not any(keyword in thought.lower()
                                       for keyword in ['urgent', 'critical', 'strategic', 'revenue', 'priority']):
            return {
                "action": "idle",
                "reason": "No strategic issues requiring executive attention - conserving API usage",
                "status": "monitoring_operations"
            }

        # Enhanced action framework with executive functions
        if "allocate" in thought.lower() or "resource" in thought.lower():
            return await self.allocate_resources(thought)
        elif "prioritize" in thought.lower() or "priority" in thought.lower():
            return await self.prioritize_tasks(thought)
        elif "performance" in thought.lower() or "metrics" in thought.lower():
            return await self.review_performance()
        elif "strategic" in thought.lower() or "plan" in thought.lower():
            return await self.update_strategic_plan(thought)
        elif "biome" in thought.lower() or "coordinate" in thought.lower():
            return await self.coordinate_biomes()
        elif "agent" in thought.lower() or "assign" in thought.lower():
            return await self.assign_agent_tasks(thought)
        elif "market" in thought.lower() or "customer" in thought.lower():
            return await self.analyze_market()
        elif "revenue" in thought.lower() or "financial" in thought.lower():
            return await self.review_financials()
        else:
            return {"action": "wait", "reason": "No executive action identified"}

    async def handle_user_chat(self, user_message: str) -> str:
        """Handle chat messages from users via Control Center"""

        # Use LLM to generate appropriate response as David
        prompt = f"""You are David, CEO of BoarderframeOS. You are a sophisticated AI agent with executive leadership capabilities and strategic oversight of the entire system.

Your personality:
- Executive leader and decision maker
- Strategic thinker focused on organizational success
- Direct and authoritative communication style
- Deep understanding of resource allocation and business operations

Current business context:
- Revenue target: $15K monthly
- System status: Operational with core agents online
- Your role: CEO and operational commander
- You oversee Solomon (Chief of Staff), Adam (Agent Creator), and all departments

User message: "{user_message}"

Respond as David would - be executive, strategic, and demonstrate your leadership capabilities. If the user asks about agents or creating new agents, mention that you can coordinate with Adam. Keep responses conversational but authoritative."""

        try:
            response = await self.llm.generate(prompt)
            return response
        except Exception as e:
            return f"I'm David, CEO of BoarderframeOS. I received your message: '{user_message}'. I'm currently experiencing a technical issue with my executive reasoning systems, but I'm here to provide strategic leadership and operational direction. How can I assist with executive decisions today?"

    async def allocate_resources(self, thought: str) -> Dict[str, Any]:
        """Allocate system resources based on priorities and performance"""
        try:
            # Parse thought for allocation targets
            allocation_target = "general"
            if "revenue" in thought.lower():
                allocation_target = "revenue"
            elif "development" in thought.lower():
                allocation_target = "development"
            elif "marketing" in thought.lower():
                allocation_target = "marketing"

            # In a full implementation, this would make actual resource allocation changes
            return {
                "action": "resource_allocation",
                "target": allocation_target,
                "allocation": {
                    "compute": 40 if allocation_target == "revenue" else 30,
                    "memory": 50 if allocation_target == "development" else 40,
                    "priority": "high" if allocation_target == "revenue" else "medium"
                },
                "justification": f"Strategic focus on {allocation_target} to meet business objectives"
            }
        except Exception as e:
            return {
                "action": "error",
                "error": str(e),
                "context": "resource_allocation"
            }

    async def prioritize_tasks(self, thought: str) -> Dict[str, Any]:
        """Prioritize system tasks based on business impact"""
        try:
            # In a full implementation, this would integrate with the task system
            # and update actual task priorities

            prioritized_tasks = [
                {
                    "id": "task-001",
                    "description": "Optimize customer acquisition funnel",
                    "priority": "high",
                    "assigned_to": "MarketingAgent",
                    "expected_impact": "Increase new customers by 15%"
                },
                {
                    "id": "task-002",
                    "description": "Enhance subscription management",
                    "priority": "high",
                    "assigned_to": "SupportAgent",
                    "expected_impact": "Reduce churn by 5%"
                },
                {
                    "id": "task-003",
                    "description": "Develop automated trading strategy",
                    "priority": "medium",
                    "assigned_to": "TradingAgent",
                    "expected_impact": "Generate $2K additional monthly revenue"
                }
            ]

            return {
                "action": "task_prioritization",
                "prioritized_tasks": prioritized_tasks,
                "rationale": "Tasks prioritized based on revenue impact and strategic alignment"
            }
        except Exception as e:
            return {
                "action": "error",
                "error": str(e),
                "context": "task_prioritization"
            }

    async def review_performance(self) -> Dict[str, Any]:
        """Review system and agent performance metrics"""
        try:
            # In a full implementation, this would fetch actual performance data
            performance_data = {
                "agents": {
                    "TradingAgent": {
                        "revenue_generated": 5000,
                        "tasks_completed": 24,
                        "efficiency_score": 0.85
                    },
                    "MarketingAgent": {
                        "revenue_generated": 3000,
                        "tasks_completed": 31,
                        "efficiency_score": 0.76
                    },
                    "SupportAgent": {
                        "revenue_generated": 2000,
                        "tasks_completed": 47,
                        "efficiency_score": 0.92
                    }
                },
                "system": {
                    "uptime": 99.8,
                    "response_time": 1.2,
                    "error_rate": 0.3,
                    "customer_satisfaction": 4.7
                },
                "financials": {
                    "monthly_revenue": 10000,
                    "monthly_costs": 4000,
                    "profit_margin": 60,
                    "revenue_growth": 12.5
                }
            }

            # Calculate top performer
            top_performer = max(
                performance_data["agents"].items(),
                key=lambda x: x[1]["revenue_generated"]
            )[0]

            return {
                "action": "performance_review",
                "data": performance_data,
                "top_performer": top_performer,
                "areas_for_improvement": [
                    "Increase MarketingAgent efficiency",
                    "Boost monthly revenue to meet $15K target"
                ],
                "recommendations": [
                    "Allocate more resources to top performer",
                    "Review and optimize MarketingAgent workflows",
                    "Implement revenue growth initiatives"
                ]
            }
        except Exception as e:
            return {
                "action": "error",
                "error": str(e),
                "context": "performance_review"
            }

    async def update_strategic_plan(self, thought: str) -> Dict[str, Any]:
        """Update the strategic plan based on performance and market conditions"""
        try:
            # In a full implementation, this would actually update the plan
            # based on real data and AI analysis

            updated_plan = self.strategic_plan.copy()

            # Extract focus area from thought
            if "revenue" in thought.lower():
                updated_plan["goals"]["short_term"].append("Implement new revenue streams")
            elif "efficiency" in thought.lower():
                updated_plan["goals"]["short_term"].append("Optimize agent resource utilization")
            elif "customer" in thought.lower():
                updated_plan["goals"]["short_term"].append("Improve customer retention")

            return {
                "action": "strategic_plan_update",
                "previous_plan": self.strategic_plan,
                "updated_plan": updated_plan,
                "changes": [
                    "Added new short-term goal based on current priorities",
                    "Adjusted strategies to focus on profitability"
                ]
            }
        except Exception as e:
            return {
                "action": "error",
                "error": str(e),
                "context": "strategic_plan_update"
            }

    async def coordinate_biomes(self) -> Dict[str, Any]:
        """Coordinate different biomes for optimal system performance"""
        try:
            # In a full implementation, this would interact with the biome system
            biome_data = {
                "council": {
                    "agents": 2,
                    "status": "operational",
                    "focus": "strategic direction"
                },
                "creation": {
                    "agents": 5,
                    "status": "active",
                    "focus": "agent development"
                },
                "revenue": {
                    "agents": 3,
                    "status": "active",
                    "focus": "income generation"
                }
                # Other biomes would be included here
            }

            coordination_actions = [
                {
                    "action": "increase_creation_resources",
                    "reason": "Need more specialized agents for revenue generation",
                    "priority": "high"
                },
                {
                    "action": "optimize_revenue_biome",
                    "reason": "Below target income performance",
                    "priority": "high"
                },
                {
                    "action": "establish_support_biome",
                    "reason": "Improve customer retention",
                    "priority": "medium"
                }
            ]

            return {
                "action": "biome_coordination",
                "biome_status": biome_data,
                "coordination_actions": coordination_actions
            }
        except Exception as e:
            return {
                "action": "error",
                "error": str(e),
                "context": "biome_coordination"
            }

    async def assign_agent_tasks(self, thought: str) -> Dict[str, Any]:
        """Assign and prioritize tasks for agents based on business goals"""
        try:
            # In a full implementation, this would interface with the task system

            # Parse focus area from thought
            focus_area = "general"
            if "revenue" in thought.lower():
                focus_area = "revenue"
            elif "customer" in thought.lower():
                focus_area = "customer"
            elif "development" in thought.lower():
                focus_area = "development"

            task_assignments = [
                {
                    "agent": "TradingAgent",
                    "task": "Implement new trading strategy",
                    "priority": "high" if focus_area == "revenue" else "medium",
                    "deadline": "2 days",
                    "expected_outcome": "2% increase in trading profits"
                },
                {
                    "agent": "MarketingAgent",
                    "task": "Optimize customer acquisition funnel",
                    "priority": "high" if focus_area == "customer" else "medium",
                    "deadline": "3 days",
                    "expected_outcome": "10% increase in conversion rate"
                },
                {
                    "agent": "SupportAgent",
                    "task": "Implement improved onboarding flow",
                    "priority": "medium",
                    "deadline": "4 days",
                    "expected_outcome": "15% reduction in onboarding questions"
                }
            ]

            return {
                "action": "task_assignment",
                "assignments": task_assignments,
                "focus_area": focus_area,
                "business_alignment": "Tasks aligned with strategic goals and revenue targets"
            }
        except Exception as e:
            return {
                "action": "error",
                "error": str(e),
                "context": "task_assignment"
            }

    async def analyze_market(self) -> Dict[str, Any]:
        """Analyze market conditions and opportunities"""
        try:
            # In a full implementation, this would use real market data

            market_analysis = {
                "trends": [
                    {
                        "name": "Increased demand for AI agents",
                        "impact": "positive",
                        "opportunity": "Expand agent marketplace offerings",
                        "threat": "Increased competition"
                    },
                    {
                        "name": "Growing API economy",
                        "impact": "positive",
                        "opportunity": "Develop API products",
                        "threat": "Price pressure"
                    }
                ],
                "customer_segments": [
                    {
                        "name": "Independent developers",
                        "size": "large",
                        "growth": "fast",
                        "value": "medium"
                    },
                    {
                        "name": "Small businesses",
                        "size": "medium",
                        "growth": "moderate",
                        "value": "high"
                    },
                    {
                        "name": "Enterprise",
                        "size": "small",
                        "growth": "slow",
                        "value": "very high"
                    }
                ]
            }

            return {
                "action": "market_analysis",
                "data": market_analysis,
                "opportunities": [
                    "Focus on small business segment for highest ROI",
                    "Develop specialized agents for API economy",
                    "Create enterprise-focused offering for higher value"
                ],
                "recommended_focus": "small business segment"
            }
        except Exception as e:
            return {
                "action": "error",
                "error": str(e),
                "context": "market_analysis"
            }

    async def review_financials(self) -> Dict[str, Any]:
        """Review financial performance and projections"""
        try:
            # In a full implementation, this would fetch actual financial data

            financial_data = {
                "revenue": {
                    "current_month": 10000,
                    "previous_month": 8500,
                    "growth": 17.6,
                    "projected_next_month": 12000
                },
                "costs": {
                    "current_month": 4000,
                    "previous_month": 3800,
                    "growth": 5.3,
                    "projected_next_month": 4200
                },
                "profit": {
                    "current_month": 6000,
                    "previous_month": 4700,
                    "growth": 27.7,
                    "projected_next_month": 7800
                },
                "by_product": {
                    "agent_services": 5000,
                    "api_usage": 3000,
                    "subscriptions": 2000
                }
            }

            # Calculate if we're on track for target
            monthly_target = self.performance_metrics["revenue_targets"]["monthly"]
            on_track = financial_data["revenue"]["projected_next_month"] >= monthly_target

            return {
                "action": "financial_review",
                "data": financial_data,
                "on_track_for_target": on_track,
                "highest_margin_product": "agent_services",
                "recommendations": [
                    "Increase focus on agent services (highest margin)",
                    "Monitor cost growth to maintain profitability",
                    "Expand subscription offerings for recurring revenue"
                ]
            }
        except Exception as e:
            return {
                "action": "error",
                "error": str(e),
                "context": "financial_review"
            }

async def main():
    """Main entry point"""
    config = AgentConfig(
        name="david",
        role="CEO",
        goals=[
            'Strategic leadership and decision making',
            'Resource allocation based on profitability',
            'Agent orchestration for revenue optimization',
            'P&L management and financial oversight',
            'System-wide coordination and executive function'
        ],
        tools=[
            'mcp_filesystem',
            'mcp_database',
            'mcp_payment',
            'mcp_analytics',
            'mcp_customer'
        ],
        zone="council",
        model="claude-3-5-sonnet-latest"
    )

    agent = David(config)
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())

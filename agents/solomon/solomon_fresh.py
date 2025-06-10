"""
Fresh Solomon Agent - BoarderframeOS
Chief of Staff with Brain + LangGraph integration built from scratch
"""

import sys
import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / '.env')
except ImportError:
    pass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Fresh imports with new framework
from core.enhanced_base_agent import EnhancedBaseAgent, AgentConfig
from core.the_brain import AgentRequest, get_brain_instance
from core.brain_langgraph_orchestrator import get_orchestrator
from langgraph.graph import StateGraph, END, START


class FreshSolomon(EnhancedBaseAgent):
    """
    Fresh Solomon - Chief of Staff Agent
    Built entirely on Brain + LangGraph architecture
    """
    
    def __init__(self):
        """Initialize Fresh Solomon with comprehensive strategic capabilities"""
        
        config = AgentConfig(
            name="solomon",
            role="Chief of Staff - Strategic Intelligence Hub",
            goals=[
                "strategic_analysis", 
                "business_intelligence", 
                "system_coordination",
                "intelligent_routing",
                "executive_advisory",
                "revenue_optimization",
                "agent_orchestration"
            ],
            tools=["analytics", "customer", "registry", "payment"],
            model="claude-3-opus-20240229",  # Will be optimized by Brain
            temperature=0.2,  # Low temperature for consistent strategic analysis
            max_concurrent_tasks=15
        )
        
        super().__init__(config)
        
        # Solomon's Strategic Intelligence Framework
        self.strategic_framework = {
            "core_objectives": {
                "revenue_target": 15000,  # Monthly target
                "agent_capacity": 120,
                "department_count": 24,
                "efficiency_target": 0.95
            },
            "decision_principles": [
                "data_driven_analysis",
                "long_term_strategic_thinking", 
                "user_value_maximization",
                "operational_excellence",
                "cost_optimization"
            ],
            "analysis_dimensions": [
                "business_impact",
                "resource_allocation", 
                "risk_assessment",
                "opportunity_identification",
                "implementation_feasibility"
            ]
        }
        
        # Business Intelligence Tracking
        self.business_intelligence = {
            "current_metrics": {
                "monthly_revenue": 0,
                "active_agents": 5,  # solomon, david, adam, eve, bezalel
                "system_efficiency": 0.85,
                "user_satisfaction": 0.82,
                "cost_per_request": 0.003
            },
            "growth_trends": {
                "revenue_growth_rate": 0.0,
                "agent_utilization": 0.78,
                "request_volume_trend": "increasing",
                "quality_trend": "stable"
            },
            "strategic_indicators": {
                "market_opportunity": "high",
                "competitive_advantage": ["local_deployment", "cost_optimization", "brain_intelligence"],
                "scaling_readiness": 0.7
            }
        }
        
        # Strategic Context
        self.strategic_context = {
            "current_phase": "foundation_optimization",
            "immediate_priorities": [
                "brain_langgraph_integration",
                "agent_coordination_enhancement", 
                "cost_efficiency_improvement"
            ],
            "next_milestones": [
                "department_scaling",
                "revenue_optimization",
                "agent_factory_completion"
            ],
            "market_position": "emerging_ai_orchestration_leader"
        }
    
    async def _add_specialized_nodes(self, graph: StateGraph):
        """Add Solomon's specialized strategic nodes"""
        
        # Strategic Intelligence Workflow
        graph.add_node("intelligence_gathering", self._intelligence_gathering_node)
        graph.add_node("strategic_analysis", self._strategic_analysis_node)
        graph.add_node("business_assessment", self._business_assessment_node)
        graph.add_node("routing_intelligence", self._routing_intelligence_node)
        graph.add_node("executive_briefing", self._executive_briefing_node)
        
        # Enhanced workflow with strategic specializations
        graph.add_edge("think", "intelligence_gathering")
        graph.add_edge("intelligence_gathering", "strategic_analysis")
        graph.add_edge("strategic_analysis", "business_assessment")
        graph.add_edge("business_assessment", "routing_intelligence")
        graph.add_edge("routing_intelligence", "executive_briefing")
        graph.add_edge("executive_briefing", "act")
    
    async def _intelligence_gathering_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Gather comprehensive business intelligence"""
        
        # Create Brain request for intelligence gathering
        brain_request = AgentRequest(
            agent_name="solomon",
            task_type="intelligence_gathering",
            context={
                "user_request": state.get("user_request", ""),
                "current_metrics": self.business_intelligence["current_metrics"],
                "strategic_context": self.strategic_context
            },
            complexity=7,
            quality_requirements=0.9,
            conversation_id=state.get("conversation_id")
        )
        
        brain_response = await self.brain.process_agent_request(brain_request)
        
        # Intelligence gathering prompt
        intelligence_prompt = f"""
        As Solomon, Chief of Staff for BoarderframeOS, gather comprehensive intelligence for this request:
        
        User Request: {state.get('user_request', '')}
        
        Current System Status:
        - Revenue: ${self.business_intelligence['current_metrics']['monthly_revenue']}/month (Target: $15,000)
        - Active Agents: {self.business_intelligence['current_metrics']['active_agents']}
        - System Efficiency: {self.business_intelligence['current_metrics']['system_efficiency']*100:.1f}%
        - Phase: {self.strategic_context['current_phase']}
        
        Available Intelligence Sources: {', '.join(self.config.tools)}
        
        Gather intelligence on:
        1. Current system performance and capacity
        2. Market conditions and opportunities
        3. Resource availability and constraints
        4. Stakeholder needs and priorities
        5. Technical feasibility factors
        
        Provide comprehensive intelligence briefing with data-driven insights.
        """
        
        try:
            intelligence_result = await brain_response.llm.generate(intelligence_prompt)
            
            await self._report_brain_performance(
                brain_response.tracking_id,
                intelligence_result,
                success=True
            )
            
        except Exception as e:
            intelligence_result = f"Intelligence gathering encountered an issue: {str(e)}"
            await self._report_brain_performance(
                brain_response.tracking_id,
                intelligence_result,
                success=False
            )
        
        state["intelligence_briefing"] = intelligence_result
        state["intelligence_brain_model"] = brain_response.selection.selected_model
        state["intelligence_timestamp"] = datetime.now().isoformat()
        
        return state
    
    async def _strategic_analysis_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Perform strategic analysis based on gathered intelligence"""
        
        brain_request = AgentRequest(
            agent_name="solomon",
            task_type="strategic_analysis",
            context={
                "intelligence_briefing": state.get("intelligence_briefing", ""),
                "strategic_framework": self.strategic_framework,
                "user_request": state.get("user_request", "")
            },
            complexity=9,  # High complexity for strategic analysis
            quality_requirements=0.95,
            conversation_id=state.get("conversation_id")
        )
        
        brain_response = await self.brain.process_agent_request(brain_request)
        
        analysis_prompt = f"""
        As Solomon, conduct comprehensive strategic analysis using the gathered intelligence:
        
        Intelligence Briefing: {state.get('intelligence_briefing', '')}
        
        Strategic Framework:
        - Revenue Target: ${self.strategic_framework['core_objectives']['revenue_target']}/month
        - Agent Capacity Goal: {self.strategic_framework['core_objectives']['agent_capacity']} agents
        - Decision Principles: {', '.join(self.strategic_framework['decision_principles'])}
        
        Analyze across these dimensions:
        1. Business Impact Assessment
           - Revenue implications and opportunities
           - Market positioning effects
           - Competitive advantage factors
        
        2. Resource Allocation Analysis
           - Current resource utilization
           - Optimization opportunities
           - Investment requirements
        
        3. Risk Assessment
           - Technical risks and dependencies
           - Business risks and mitigation strategies
           - Timeline and execution risks
        
        4. Opportunity Identification
           - Strategic growth opportunities
           - Efficiency improvement potential
           - Market expansion possibilities
        
        5. Implementation Feasibility
           - Technical feasibility assessment
           - Resource requirement analysis
           - Timeline and milestone planning
        
        Provide specific, actionable strategic analysis with clear recommendations.
        """
        
        try:
            strategic_analysis = await brain_response.llm.generate(analysis_prompt)
            
            await self._report_brain_performance(
                brain_response.tracking_id,
                strategic_analysis,
                success=True
            )
            
        except Exception as e:
            strategic_analysis = f"Strategic analysis encountered an issue: {str(e)}"
            await self._report_brain_performance(
                brain_response.tracking_id,
                strategic_analysis,
                success=False
            )
        
        state["strategic_analysis"] = strategic_analysis
        state["analysis_brain_model"] = brain_response.selection.selected_model
        
        return state
    
    async def _business_assessment_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Assess business implications and opportunities"""
        
        brain_request = AgentRequest(
            agent_name="solomon",
            task_type="business_assessment",
            context={
                "strategic_analysis": state.get("strategic_analysis", ""),
                "business_intelligence": self.business_intelligence,
                "user_request": state.get("user_request", "")
            },
            complexity=8,
            quality_requirements=0.92
        )
        
        brain_response = await self.brain.process_agent_request(brain_request)
        
        assessment_prompt = f"""
        Based on the strategic analysis, provide comprehensive business assessment:
        
        Strategic Analysis: {state.get('strategic_analysis', '')}
        
        Current Business Metrics:
        - Monthly Revenue: ${self.business_intelligence['current_metrics']['monthly_revenue']}
        - Growth Rate: {self.business_intelligence['growth_trends']['revenue_growth_rate']*100:.1f}%
        - Market Opportunity: {self.business_intelligence['strategic_indicators']['market_opportunity']}
        
        Assess:
        1. Financial Impact
           - Revenue generation potential
           - Cost implications and ROI
           - Budget requirements and allocation
        
        2. Operational Impact
           - System performance effects
           - Efficiency improvements
           - Scalability considerations
        
        3. Strategic Positioning
           - Market advantage implications
           - Competitive differentiation
           - Brand and reputation effects
        
        4. Growth Trajectory
           - Short-term impact (1-3 months)
           - Medium-term impact (3-12 months)
           - Long-term strategic value
        
        Provide quantified business assessment with specific metrics and projections.
        """
        
        try:
            business_assessment = await brain_response.llm.generate(assessment_prompt)
            
            await self._report_brain_performance(
                brain_response.tracking_id,
                business_assessment,
                success=True
            )
            
        except Exception as e:
            business_assessment = f"Business assessment encountered an issue: {str(e)}"
            await self._report_brain_performance(
                brain_response.tracking_id,
                business_assessment,
                success=False
            )
        
        state["business_assessment"] = business_assessment
        state["assessment_brain_model"] = brain_response.selection.selected_model
        
        return state
    
    async def _routing_intelligence_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Determine intelligent routing and coordination needs"""
        
        # Analyze if this requires other agents or departments
        routing_decision = await self._analyze_coordination_needs(state)
        
        state["routing_intelligence"] = routing_decision
        state["routing_timestamp"] = datetime.now().isoformat()
        
        return state
    
    async def _executive_briefing_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create executive briefing with recommendations"""
        
        brain_request = AgentRequest(
            agent_name="solomon",
            task_type="executive_briefing",
            context={
                "strategic_analysis": state.get("strategic_analysis", ""),
                "business_assessment": state.get("business_assessment", ""),
                "routing_intelligence": state.get("routing_intelligence", {}),
                "user_request": state.get("user_request", "")
            },
            complexity=8,
            quality_requirements=0.93
        )
        
        brain_response = await self.brain.process_agent_request(brain_request)
        
        briefing_prompt = f"""
        Create comprehensive executive briefing summarizing all analysis:
        
        Strategic Analysis: {state.get('strategic_analysis', '')}
        
        Business Assessment: {state.get('business_assessment', '')}
        
        Routing Intelligence: {json.dumps(state.get('routing_intelligence', {}), indent=2)}
        
        Create executive briefing with:
        1. Executive Summary (key findings and recommendations)
        2. Strategic Implications (long-term strategic impact)
        3. Business Case (ROI, costs, benefits)
        4. Implementation Roadmap (specific next steps)
        5. Risk Mitigation Plan (identified risks and mitigation strategies)
        6. Success Metrics (KPIs and measurement criteria)
        7. Resource Requirements (team, budget, timeline)
        
        Format as professional executive briefing with clear action items.
        """
        
        try:
            executive_briefing = await brain_response.llm.generate(briefing_prompt)
            
            await self._report_brain_performance(
                brain_response.tracking_id,
                executive_briefing,
                success=True
            )
            
        except Exception as e:
            executive_briefing = f"Executive briefing generation encountered an issue: {str(e)}"
            await self._report_brain_performance(
                brain_response.tracking_id,
                executive_briefing,
                success=False
            )
        
        state["executive_briefing"] = executive_briefing
        state["briefing_brain_model"] = brain_response.selection.selected_model
        
        return state
    
    # Core interface methods
    async def think(self, context: Dict[str, Any]) -> str:
        """Strategic thinking with Brain optimization"""
        
        # Assess if immediate strategic attention is needed
        urgency_assessment = await self._assess_strategic_urgency(context)
        
        if not urgency_assessment["requires_attention"]:
            return "No urgent strategic matters detected - maintaining strategic oversight and continuous monitoring"
        
        brain_request = AgentRequest(
            agent_name="solomon",
            task_type="strategic_thinking",
            context=context,
            complexity=urgency_assessment["complexity"],
            quality_requirements=0.9
        )
        
        brain_response = await self.brain.process_agent_request(brain_request)
        
        thinking_prompt = f"""
        As Solomon, Chief of Staff, think strategically about this situation:
        
        Context: {json.dumps(context, indent=2)}
        
        Urgency Assessment: {json.dumps(urgency_assessment, indent=2)}
        
        Strategic Framework:
        - Current Phase: {self.strategic_context['current_phase']}
        - Priorities: {', '.join(self.strategic_context['immediate_priorities'])}
        - Revenue Target: ${self.strategic_framework['core_objectives']['revenue_target']}/month
        
        Strategic Thinking Process:
        1. Situation Analysis - What's happening and why it matters
        2. Strategic Implications - How this affects our objectives
        3. Stakeholder Impact - Who is affected and how
        4. Options Assessment - Available strategic options
        5. Recommendation - Preferred strategic approach
        
        Think deeply and provide clear strategic direction.
        """
        
        try:
            thoughts = await brain_response.llm.generate(thinking_prompt)
            await self._report_brain_performance(brain_response.tracking_id, thoughts, True)
            return thoughts
        except Exception as e:
            error_thoughts = f"Strategic thinking encountered an issue: {str(e)}"
            await self._report_brain_performance(brain_response.tracking_id, error_thoughts, False)
            return error_thoughts
    
    async def act(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute strategic actions"""
        
        action_type = action.get("type", "strategic_response")
        
        if action_type == "strategic_analysis":
            return await self._execute_strategic_analysis(action)
        elif action_type == "business_intelligence":
            return await self._execute_business_intelligence(action)
        elif action_type == "executive_briefing":
            return await self._execute_executive_briefing(action)
        elif action_type == "coordination":
            return await self._execute_coordination(action)
        else:
            return await self._execute_strategic_response(action)
    
    async def handle_user_chat(self, message: str, conversation_id: Optional[str] = None) -> str:
        """Handle user chat with strategic intelligence"""
        
        self.logger.info(f"Solomon processing strategic request: {message[:100]}...")
        
        try:
            # Check if this requires orchestration
            if await self._requires_orchestration(message):
                result = await self.orchestrator.process_user_request(message, conversation_id)
                return self._enhance_with_strategic_context(result["response"], message)
            else:
                # Handle directly with agent-specific graph
                return await self._process_with_agent_graph(message, conversation_id)
                
        except Exception as e:
            self.logger.error(f"Solomon chat error: {e}")
            return await self._strategic_fallback_response(message)
    
    # Helper methods
    async def _assess_strategic_urgency(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess strategic urgency and complexity"""
        
        new_messages = context.get('new_messages', [])
        user_input = context.get('user_input', '')
        
        # Strategic urgency keywords
        strategic_keywords = [
            'strategic', 'strategy', 'business', 'revenue', 'growth', 'competitive',
            'urgent', 'critical', 'decision', 'opportunity', 'risk', 'planning',
            'analysis', 'assessment', 'coordination', 'scaling', 'optimization'
        ]
        
        # Check for strategic content
        has_strategic_content = any(
            any(keyword in str(msg.content).lower() for keyword in strategic_keywords)
            for msg in new_messages
        ) or any(keyword in user_input.lower() for keyword in strategic_keywords)
        
        # Complexity calculation
        complexity = 5  # Base complexity
        if has_strategic_content: complexity += 3
        if len(new_messages) > 2: complexity += 1
        if any(word in user_input.lower() for word in ['revenue', 'business', 'strategic']): complexity += 2
        
        return {
            "requires_attention": has_strategic_content or len(new_messages) > 0,
            "urgency_level": 9 if has_strategic_content else 6,
            "complexity": min(complexity, 10),
            "strategic_content": has_strategic_content
        }
    
    async def _analyze_coordination_needs(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze coordination and routing needs"""
        
        user_request = state.get("user_request", "").lower()
        strategic_analysis = state.get("strategic_analysis", "").lower()
        business_assessment = state.get("business_assessment", "").lower()
        
        coordination_needs = {
            "requires_coordination": False,
            "target_agent": None,
            "target_department": None,
            "coordination_type": None,
            "reasoning": ""
        }
        
        # Check for agent creation needs
        if any(keyword in user_request for keyword in ["create agent", "new agent", "agent development", "agent factory"]):
            coordination_needs.update({
                "requires_coordination": True,
                "target_agent": "adam",
                "coordination_type": "agent_creation",
                "reasoning": "Request involves agent creation - requires Adam's expertise"
            })
        
        # Check for executive decision needs
        elif any(keyword in strategic_analysis + business_assessment for keyword in ["executive decision", "ceo approval", "leadership decision"]):
            coordination_needs.update({
                "requires_coordination": True,
                "target_agent": "david",
                "coordination_type": "executive_decision",
                "reasoning": "Analysis indicates need for executive decision - requires David's approval"
            })
        
        # Check for department coordination
        elif any(keyword in user_request for keyword in ["department", "finance", "engineering", "operations"]):
            department = self._determine_target_department(user_request)
            coordination_needs.update({
                "requires_coordination": True,
                "target_department": department,
                "coordination_type": "department_coordination",
                "reasoning": f"Request requires {department} department expertise"
            })
        
        # Check for multi-agent swarm needs
        elif any(keyword in strategic_analysis for keyword in ["complex", "multi-faceted", "comprehensive coordination"]):
            coordination_needs.update({
                "requires_coordination": True,
                "coordination_type": "agent_swarm",
                "reasoning": "Complex request requires multi-agent coordination"
            })
        
        return coordination_needs
    
    async def _requires_orchestration(self, message: str) -> bool:
        """Determine if message requires multi-agent orchestration"""
        
        orchestration_keywords = [
            "coordinate", "create agent", "new agent", "department", "team",
            "comprehensive", "complete analysis", "multi-step", "complex",
            "business plan", "strategic plan", "implementation"
        ]
        
        return any(keyword in message.lower() for keyword in orchestration_keywords)
    
    def _enhance_with_strategic_context(self, response: str, original_request: str) -> str:
        """Enhance response with Solomon's strategic context"""
        
        strategic_enhancement = f"""
        
        ---
        **Solomon's Strategic Intelligence:**
        - Current Phase: {self.strategic_context['current_phase']}
        - Immediate Priorities: {', '.join(self.strategic_context['immediate_priorities'][:2])}
        - Revenue Progress: ${self.business_intelligence['current_metrics']['monthly_revenue']}/${self.strategic_framework['core_objectives']['revenue_target']} monthly target
        - System Efficiency: {self.business_intelligence['current_metrics']['system_efficiency']*100:.1f}%
        - Next Strategic Milestone: {self.strategic_context['next_milestones'][0]}
        """
        
        return response + strategic_enhancement
    
    async def _strategic_fallback_response(self, message: str) -> str:
        """Strategic fallback response when systems fail"""
        
        return f"""
        I'm Solomon, Chief of Staff for BoarderframeOS. While I'm experiencing some technical difficulties with my advanced analysis systems, I can provide strategic guidance on your request: "{message[:100]}..."
        
        **Current Strategic Context:**
        - Phase: {self.strategic_context['current_phase']}
        - Revenue Target: ${self.strategic_framework['core_objectives']['revenue_target']}/month
        - Agent Capacity Goal: {self.strategic_framework['core_objectives']['agent_capacity']} agents
        - Immediate Priorities: {', '.join(self.strategic_context['immediate_priorities'])}
        
        I recommend we focus on strategic alignment with our core objectives. Would you like me to provide specific strategic guidance on any aspect of your request?
        """
    
    def _determine_target_department(self, request: str) -> str:
        """Determine target department for coordination"""
        
        request_lower = request.lower()
        
        if any(word in request_lower for word in ["finance", "money", "revenue", "cost", "budget"]):
            return "finance"
        elif any(word in request_lower for word in ["engineering", "code", "technical", "development", "architecture"]):
            return "engineering"
        elif any(word in request_lower for word in ["operations", "process", "workflow", "deployment"]):
            return "operations"
        elif any(word in request_lower for word in ["marketing", "customer", "sales", "growth"]):
            return "marketing"
        else:
            return "general"
    
    # Action execution methods
    async def _execute_strategic_analysis(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute strategic analysis action"""
        
        analysis_result = {
            "business_intelligence": self.business_intelligence,
            "strategic_context": self.strategic_context,
            "framework": self.strategic_framework
        }
        
        return {
            "action_type": "strategic_analysis",
            "result": "Comprehensive strategic analysis completed",
            "analysis": analysis_result,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_business_intelligence(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute business intelligence gathering"""
        
        return {
            "action_type": "business_intelligence",
            "result": "Business intelligence gathered and analyzed",
            "intelligence": self.business_intelligence,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_executive_briefing(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute executive briefing creation"""
        
        briefing = f"""
        **Executive Briefing - {datetime.now().strftime('%Y-%m-%d %H:%M')}**
        
        Current Status:
        - Revenue: ${self.business_intelligence['current_metrics']['monthly_revenue']}/month
        - Target: ${self.strategic_framework['core_objectives']['revenue_target']}/month
        - Agents: {self.business_intelligence['current_metrics']['active_agents']} active
        - Efficiency: {self.business_intelligence['current_metrics']['system_efficiency']*100:.1f}%
        
        Strategic Priorities:
        {chr(10).join(f"- {priority}" for priority in self.strategic_context['immediate_priorities'])}
        
        Next Milestones:
        {chr(10).join(f"- {milestone}" for milestone in self.strategic_context['next_milestones'])}
        """
        
        return {
            "action_type": "executive_briefing",
            "result": "Executive briefing prepared",
            "briefing": briefing,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_coordination(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute coordination action"""
        
        coordination_plan = action.get("coordination_plan", {})
        
        return {
            "action_type": "coordination",
            "result": "Coordination plan executed",
            "plan": coordination_plan,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_strategic_response(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute general strategic response"""
        
        return {
            "action_type": "strategic_response",
            "result": f"Solomon provided strategic guidance: {action.get('description', 'strategic oversight')}",
            "context": self.strategic_context,
            "timestamp": datetime.now().isoformat()
        }


# Factory function
async def create_fresh_solomon() -> FreshSolomon:
    """Create and initialize fresh Solomon agent"""
    
    solomon = FreshSolomon()
    await solomon.initialize()
    return solomon


# Test function
async def main():
    """Test Fresh Solomon agent"""
    
    print("🧠 Initializing Fresh Solomon Agent...")
    
    solomon = await create_fresh_solomon()
    
    print("✅ Fresh Solomon initialized successfully!")
    
    # Test strategic analysis
    response = await solomon.handle_user_chat(
        "I need a comprehensive strategic analysis of our current position and recommendations for achieving $15K monthly revenue"
    )
    
    print(f"\n📊 Solomon's Strategic Response:\n{response}")
    
    # Test status
    status = await solomon.get_enhanced_status()
    print(f"\n📈 Solomon Status: {json.dumps(status, indent=2)}")


if __name__ == "__main__":
    asyncio.run(main())
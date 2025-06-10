"""
Enhanced Solomon Agent - BoarderframeOS
Chief of Staff AI Agent with Brain + LangGraph integration
"""

import sys
import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / '.env')
except ImportError:
    pass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Enhanced imports
from core.enhanced_base_agent import EnhancedBaseAgent, AgentConfig
from core.the_brain import AgentRequest, get_brain_instance
from core.brain_langgraph_orchestrator import get_orchestrator, BoarderframeState
from langgraph.graph import StateGraph, END, START


class EnhancedSolomon(EnhancedBaseAgent):
    """
    Enhanced Solomon - Chief of Staff Agent with Brain + LangGraph integration
    Strategic analysis, business intelligence, and intelligent routing
    """
    
    def __init__(self):
        """Initialize Enhanced Solomon with comprehensive capabilities"""
        
        config = AgentConfig(
            name="solomon",
            role="Chief of Staff - Digital Twin",
            goals=[
                "strategic_analysis", 
                "business_intelligence", 
                "system_coordination",
                "intelligent_routing",
                "executive_advisory"
            ],
            tools=["analytics", "customer", "registry"],
            model="claude-3-opus-20240229",  # Will be optimized by Brain
            temperature=0.3,  # Lower temperature for more focused analysis
            max_concurrent_tasks=10
        )
        
        super().__init__(config)
        
        # Solomon-specific attributes
        self.knowledge_base = self._load_solomon_knowledge()
        self.decision_framework = {
            "maximize": ["freedom", "wellbeing", "wealth", "autonomy"],
            "protect": ["user_benefits", "work_life_balance", "system_integrity"],
            "target": "15k_monthly_revenue",
            "principles": ["data_driven", "strategic_thinking", "long_term_vision"]
        }
        
        # Business intelligence tracking
        self.business_kpis = {
            "revenue": 0,
            "customers": 0,
            "agents_active": 0,
            "system_efficiency": 0.85,
            "cost_optimization": 0.0,
            "user_satisfaction": 0.0
        }
        
        # Strategic context
        self.strategic_context = {
            "current_phase": "foundation_building",
            "next_milestones": ["agent_scaling", "department_deployment", "revenue_optimization"],
            "focus_areas": ["brain_integration", "multi_agent_coordination", "cost_efficiency"]
        }
    
    def _load_solomon_knowledge(self) -> Dict[str, Any]:
        """Load Solomon's comprehensive knowledge base"""
        return {
            "user_preferences": {
                "communication_style": "direct_and_strategic",
                "work_approach": "systems_thinking",
                "decision_priorities": ["revenue", "autonomy", "scalability", "efficiency"]
            },
            "boarderframeos_expertise": {
                "architecture": "multi_agent_system_with_brain_orchestration",
                "current_agents": ["solomon", "david", "adam", "eve", "bezalel"],
                "infrastructure": ["postgresql", "redis", "mcp_servers", "brain_system"],
                "revenue_model": "agent_as_a_service_plus_api_gateway"
            },
            "strategic_insights": {
                "market_opportunity": "ai_agent_orchestration_platform",
                "competitive_advantage": ["local_deployment", "cost_optimization", "intelligence_routing"],
                "success_metrics": ["monthly_revenue", "agent_efficiency", "user_adoption"]
            },
            "business_context": {
                "target_revenue": 15000,  # Monthly
                "agent_capacity": 120,
                "departments": 24,
                "infrastructure_status": "operational"
            }
        }
    
    async def _add_specialized_nodes(self, graph: StateGraph):
        """Add Solomon-specific specialized nodes"""
        
        # Solomon's specialized workflow nodes
        graph.add_node("strategic_analysis", self._strategic_analysis_node)
        graph.add_node("business_intelligence", self._business_intelligence_node)
        graph.add_node("routing_decision", self._intelligent_routing_node)
        graph.add_node("executive_summary", self._executive_summary_node)
        
        # Enhanced workflow with Solomon's specializations
        graph.add_edge("think", "strategic_analysis")
        graph.add_edge("strategic_analysis", "business_intelligence")
        graph.add_edge("business_intelligence", "routing_decision")
        graph.add_edge("routing_decision", "executive_summary")
        graph.add_edge("executive_summary", "act")
    
    async def _strategic_analysis_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Solomon's strategic analysis capabilities"""
        
        # Create Brain request for strategic analysis
        brain_request = AgentRequest(
            agent_name="solomon",
            task_type="strategic_analysis",
            context={
                "user_request": state.get("user_request", ""),
                "business_context": self.business_kpis,
                "strategic_framework": self.decision_framework,
                "current_phase": self.strategic_context["current_phase"]
            },
            complexity=8,  # High complexity for strategic work
            quality_requirements=0.95,  # Highest quality for strategic decisions
            conversation_id=state.get("conversation_id")
        )
        
        # Get optimal model from Brain for strategic analysis
        brain_response = await self.brain.process_agent_request(brain_request)
        
        # Strategic analysis prompt
        analysis_prompt = f"""
        As Solomon, Chief of Staff for BoarderframeOS, conduct a comprehensive strategic analysis.
        
        User Request: {state.get('user_request', '')}
        
        Current Business Context:
        - Revenue Target: ${self.business_kpis['revenue']}/month (Goal: $15,000)
        - Active Agents: {self.business_kpis['agents_active']}
        - System Efficiency: {self.business_kpis['system_efficiency']*100:.1f}%
        - Current Phase: {self.strategic_context['current_phase']}
        
        Strategic Framework:
        - Maximize: {', '.join(self.decision_framework['maximize'])}
        - Protect: {', '.join(self.decision_framework['protect'])}
        - Target: {self.decision_framework['target']}
        
        Provide strategic analysis considering:
        1. Business impact and revenue implications
        2. Resource allocation and optimization opportunities
        3. Risk assessment and mitigation strategies
        4. Alignment with long-term objectives
        5. Recommended next actions and timeline
        
        Be specific, data-driven, and actionable in your analysis.
        """
        
        try:
            strategic_analysis = await brain_response.llm.generate(analysis_prompt)
            
            # Report success to Brain
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
        
        # Update state with analysis
        state["strategic_analysis"] = strategic_analysis
        state["analysis_brain_model"] = brain_response.selection.selected_model
        state["analysis_timestamp"] = datetime.now().isoformat()
        
        return state
    
    async def _business_intelligence_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Solomon's business intelligence processing"""
        
        # Gather business intelligence
        business_intel = await self._gather_business_intelligence()
        
        # Create Brain request for BI analysis
        brain_request = AgentRequest(
            agent_name="solomon",
            task_type="business_intelligence",
            context={
                "strategic_analysis": state.get("strategic_analysis", ""),
                "business_intel": business_intel,
                "kpis": self.business_kpis
            },
            complexity=7,
            quality_requirements=0.9
        )
        
        brain_response = await self.brain.process_agent_request(brain_request)
        
        # BI analysis prompt
        bi_prompt = f"""
        Based on the strategic analysis and current business intelligence:
        
        Strategic Analysis: {state.get('strategic_analysis', '')}
        
        Current Business Intelligence:
        {json.dumps(business_intel, indent=2)}
        
        Key Performance Indicators:
        {json.dumps(self.business_kpis, indent=2)}
        
        Provide business intelligence insights including:
        1. Performance trends and patterns
        2. Optimization opportunities
        3. Resource utilization analysis
        4. Competitive positioning
        5. Revenue growth strategies
        
        Focus on actionable insights that support the strategic analysis.
        """
        
        try:
            bi_analysis = await brain_response.llm.generate(bi_prompt)
            await self._report_brain_performance(brain_response.tracking_id, bi_analysis, True)
        except Exception as e:
            bi_analysis = f"BI analysis error: {str(e)}"
            await self._report_brain_performance(brain_response.tracking_id, bi_analysis, False)
        
        state["business_intelligence"] = bi_analysis
        state["bi_brain_model"] = brain_response.selection.selected_model
        
        return state
    
    async def _intelligent_routing_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Solomon's intelligent routing decisions"""
        
        # Determine if request needs routing to other agents/departments
        routing_decision = await self._analyze_routing_needs(state)
        
        state["routing_decision"] = routing_decision
        state["routing_timestamp"] = datetime.now().isoformat()
        
        return state
    
    async def _executive_summary_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create executive summary of analysis"""
        
        # Compile comprehensive executive summary
        executive_summary = await self._create_executive_summary(state)
        
        state["executive_summary"] = executive_summary
        state["summary_timestamp"] = datetime.now().isoformat()
        
        return state
    
    # Core interface methods (compatibility with existing system)
    async def think(self, context: Dict[str, Any]) -> str:
        """Enhanced Solomon thinking with strategic focus"""
        
        # Check if there are urgent items requiring immediate attention
        urgent_indicators = await self._assess_urgency(context)
        
        if not urgent_indicators["has_urgent_items"]:
            return "No urgent strategic matters detected - maintaining strategic oversight and system monitoring"
        
        # Strategic thinking with Brain optimization
        brain_request = AgentRequest(
            agent_name="solomon", 
            task_type="strategic_thinking",
            context=context,
            complexity=urgent_indicators["complexity"],
            quality_requirements=0.9
        )
        
        brain_response = await self.brain.process_agent_request(brain_request)
        
        thinking_prompt = f"""
        As Solomon, analyze this strategic situation:
        
        Context: {json.dumps(context, indent=2)}
        
        Urgency Assessment: {json.dumps(urgent_indicators, indent=2)}
        
        Business Framework:
        - Goals: {', '.join(self.config.goals)}
        - Decision Principles: {', '.join(self.decision_framework['principles'])}
        - Current Focus: {', '.join(self.strategic_context['focus_areas'])}
        
        Think strategically about:
        1. Immediate priorities and actions needed
        2. Business impact and resource implications  
        3. Alignment with strategic objectives
        4. Risk mitigation and opportunity capture
        5. Coordination needs with other agents/departments
        
        Provide clear, actionable strategic thinking.
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
        """Enhanced Solomon actions with strategic execution"""
        
        action_type = action.get("type", "general_response")
        
        # Route to specialized action handlers
        if action_type == "strategic_analysis":
            return await self._execute_strategic_analysis(action)
        elif action_type == "business_intelligence":
            return await self._execute_business_intelligence(action)
        elif action_type == "routing_decision":
            return await self._execute_routing_decision(action)
        elif action_type == "executive_advisory":
            return await self._execute_executive_advisory(action)
        else:
            return await self._execute_general_action(action)
    
    async def handle_user_chat(self, message: str, conversation_id: Optional[str] = None) -> str:
        """Enhanced chat handling with strategic intelligence"""
        
        self.logger.info(f"Solomon processing strategic request: {message[:100]}...")
        
        # For now, use the orchestrator for all requests to avoid state conflicts
        # TODO: Fix agent-specific graph state management
        try:
            result = await self.orchestrator.process_user_request(message, conversation_id)
            
            # Add Solomon's strategic context to the response
            enhanced_response = await self._add_strategic_context(result["response"], message)
            return enhanced_response
            
        except Exception as e:
            self.logger.error(f"Orchestrator error: {e}")
            # Fallback to direct Brain interaction
            return await self._handle_direct_brain_interaction(message)
    
    # Helper methods
    async def _assess_urgency(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess urgency and complexity of strategic situation"""
        
        new_messages = context.get('new_messages', [])
        user_input = context.get('user_input', '')
        
        # Urgency keywords
        urgent_keywords = [
            'urgent', 'critical', 'emergency', 'immediate', 'asap',
            'revenue', 'down', 'error', 'failure', 'issue', 'problem',
            'strategic', 'decision', 'opportunity', 'competitive'
        ]
        
        # Check for urgent content
        has_urgent_content = any(
            any(keyword in str(msg.content).lower() for keyword in urgent_keywords)
            for msg in new_messages
        ) or any(keyword in user_input.lower() for keyword in urgent_keywords)
        
        # Complexity assessment
        complexity = 5  # Base complexity
        if has_urgent_content: complexity += 2
        if len(new_messages) > 3: complexity += 1
        if any(word in user_input.lower() for word in ['strategy', 'business', 'revenue']): complexity += 2
        
        return {
            "has_urgent_items": has_urgent_content or len(new_messages) > 0,
            "urgency_level": 8 if has_urgent_content else 5,
            "complexity": min(complexity, 10),
            "message_count": len(new_messages)
        }
    
    async def _gather_business_intelligence(self) -> Dict[str, Any]:
        """Gather comprehensive business intelligence"""
        
        return {
            "system_status": {
                "brain_active": True,
                "langgraph_operational": True,
                "mcp_servers": await self._get_mcp_server_status(),
                "agent_count": len(await self._get_active_agents())
            },
            "performance_metrics": {
                "response_time": self.metrics.avg_response_time,
                "quality_score": self.metrics.quality_score,
                "cost_efficiency": 0.85,  # TODO: Get real cost efficiency
                "uptime": 0.99  # TODO: Get real uptime
            },
            "business_metrics": self.business_kpis,
            "strategic_progress": {
                "current_phase": self.strategic_context["current_phase"],
                "milestone_completion": 0.6,  # TODO: Calculate real completion
                "next_priorities": self.strategic_context["next_milestones"][:3]
            }
        }
    
    async def _analyze_routing_needs(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze if request needs routing to other agents"""
        
        user_request = state.get("user_request", "").lower()
        strategic_analysis = state.get("strategic_analysis", "").lower()
        
        routing_needs = {
            "requires_routing": False,
            "target_agent": None,
            "target_department": None,
            "reasoning": ""
        }
        
        # Check for agent creation needs
        if any(keyword in user_request for keyword in ["create agent", "new agent", "agent development"]):
            routing_needs.update({
                "requires_routing": True,
                "target_agent": "adam",
                "reasoning": "Request involves agent creation - routing to Adam"
            })
        
        # Check for executive decision needs
        elif any(keyword in strategic_analysis for keyword in ["executive decision", "ceo approval", "leadership"]):
            routing_needs.update({
                "requires_routing": True,
                "target_agent": "david",
                "reasoning": "Strategic analysis indicates need for executive decision - routing to David"
            })
        
        # Check for department-specific needs
        elif any(keyword in user_request for keyword in ["finance", "engineering", "operations"]):
            routing_needs.update({
                "requires_routing": True,
                "target_department": self._determine_department(user_request),
                "reasoning": "Request is department-specific"
            })
        
        return routing_needs
    
    async def _create_executive_summary(self, state: Dict[str, Any]) -> str:
        """Create comprehensive executive summary"""
        
        components = []
        
        # Strategic Analysis Summary
        if state.get("strategic_analysis"):
            components.append(f"**Strategic Analysis:**\n{state['strategic_analysis']}")
        
        # Business Intelligence Summary
        if state.get("business_intelligence"):
            components.append(f"**Business Intelligence:**\n{state['business_intelligence']}")
        
        # Routing Decision
        routing = state.get("routing_decision", {})
        if routing.get("requires_routing"):
            components.append(f"**Routing Decision:** {routing['reasoning']}")
        
        # Executive Recommendations
        recommendations = await self._generate_executive_recommendations(state)
        components.append(f"**Executive Recommendations:**\n{recommendations}")
        
        return "\n\n".join(components)
    
    async def _generate_executive_recommendations(self, state: Dict[str, Any]) -> str:
        """Generate executive-level recommendations"""
        
        # Simple recommendation logic based on analysis
        recommendations = []
        
        user_request = state.get("user_request", "").lower()
        
        if "revenue" in user_request:
            recommendations.append("• Focus on revenue optimization strategies")
            recommendations.append("• Consider scaling high-performing agent capabilities")
        
        if "agent" in user_request:
            recommendations.append("• Evaluate agent performance and optimization opportunities")
            recommendations.append("• Consider expanding successful agent patterns")
        
        if "strategy" in user_request:
            recommendations.append("• Align tactical execution with strategic objectives")
            recommendations.append("• Monitor KPIs for strategic initiative success")
        
        if not recommendations:
            recommendations.append("• Continue monitoring system performance and optimization opportunities")
            recommendations.append("• Maintain focus on revenue growth and operational efficiency")
        
        return "\n".join(recommendations)
    
    async def _is_complex_strategic_request(self, message: str) -> bool:
        """Determine if request requires complex multi-agent orchestration"""
        
        complex_indicators = [
            "comprehensive", "complete", "full analysis", "detailed strategy",
            "business plan", "multi-department", "coordination", "complex",
            "create and deploy", "end-to-end", "comprehensive analysis"
        ]
        
        return any(indicator in message.lower() for indicator in complex_indicators)
    
    async def _add_strategic_context(self, response: str, original_request: str) -> str:
        """Add Solomon's strategic context to responses"""
        
        strategic_addendum = f"""
        
        ---
        **Solomon's Strategic Context:**
        - Current Phase: {self.strategic_context['current_phase']}
        - Strategic Focus: {', '.join(self.strategic_context['focus_areas'])}
        - Next Milestones: {', '.join(self.strategic_context['next_milestones'][:2])}
        """
        
        return response + strategic_addendum
    
    # Action execution methods
    async def _execute_strategic_analysis(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute strategic analysis action"""
        
        analysis_result = await self._gather_business_intelligence()
        
        return {
            "action_type": "strategic_analysis",
            "result": "Strategic analysis completed",
            "analysis": analysis_result,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_business_intelligence(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute business intelligence action"""
        
        bi_data = await self._gather_business_intelligence()
        
        return {
            "action_type": "business_intelligence", 
            "result": "Business intelligence gathered",
            "intelligence": bi_data,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_routing_decision(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute routing decision action"""
        
        routing_result = action.get("routing_decision", {})
        
        return {
            "action_type": "routing_decision",
            "result": "Routing decision executed",
            "routing": routing_result,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_executive_advisory(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute executive advisory action"""
        
        advisory_result = "Executive advisory completed with strategic recommendations"
        
        return {
            "action_type": "executive_advisory",
            "result": advisory_result,
            "recommendations": await self._generate_executive_recommendations(action),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_general_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute general action with strategic oversight"""
        
        return {
            "action_type": "general",
            "result": f"Solomon executed general action: {action.get('description', 'strategic oversight')}",
            "strategic_context": self.strategic_context,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_direct_brain_interaction(self, message: str) -> str:
        """Fallback method for direct Brain interaction when orchestrator fails"""
        
        self.logger.info("Using direct Brain interaction fallback")
        
        try:
            # Create Brain request for direct interaction
            brain_request = AgentRequest(
                agent_name="solomon",
                task_type="direct_chat",
                context={
                    "user_message": message,
                    "fallback_mode": True,
                    "strategic_context": self.strategic_context,
                    "business_kpis": self.business_kpis
                },
                complexity=6,  # Medium complexity for direct chat
                quality_requirements=0.85
            )
            
            # Get Brain response
            brain_response = await self.brain.process_agent_request(brain_request)
            
            # Create direct response prompt
            direct_prompt = f"""
            As Solomon, Chief of Staff for BoarderframeOS, respond directly to this user message:
            
            User Message: {message}
            
            Context:
            - Current Phase: {self.strategic_context['current_phase']}
            - Business KPIs: Revenue ${self.business_kpis['revenue']}/month, {self.business_kpis['agents_active']} active agents
            - Strategic Focus: {', '.join(self.strategic_context['focus_areas'])}
            - Next Milestones: {', '.join(self.strategic_context['next_milestones'][:3])}
            
            Provide strategic analysis and actionable insights as Solomon would.
            Be concise but comprehensive in your response.
            """
            
            # Generate response with Brain-selected model
            response = await brain_response.llm.generate(direct_prompt)
            
            # Report performance to Brain
            await self._report_brain_performance(
                brain_response.tracking_id,
                response,
                success=True
            )
            
            # Add strategic context
            enhanced_response = await self._add_strategic_context(response, message)
            
            return enhanced_response
            
        except Exception as e:
            self.logger.error(f"Direct Brain interaction failed: {e}")
            
            # Final fallback - simple strategic response
            return f"""
            I'm Solomon, Chief of Staff for BoarderframeOS. I understand you're asking: "{message[:100]}..."
            
            Currently, we're in the {self.strategic_context['current_phase']} phase, focusing on {', '.join(self.strategic_context['focus_areas'][:2])}.
            
            While I'm experiencing some technical difficulties with my advanced analysis systems, I can still provide strategic guidance. 
            Would you like me to focus on any specific aspect of your request?
            
            ---
            **Strategic Context:**
            - Current Phase: {self.strategic_context['current_phase']}
            - Revenue Target: $15,000/month
            - Next Priority: {self.strategic_context['next_milestones'][0] if self.strategic_context['next_milestones'] else 'system optimization'}
            """
    
    # Utility methods
    async def _get_mcp_server_status(self) -> Dict[str, str]:
        """Get status of MCP servers"""
        # TODO: Implement actual MCP server status checking
        return {
            "registry": "operational",
            "analytics": "operational", 
            "customer": "operational"
        }
    
    def _determine_department(self, request: str) -> str:
        """Determine target department for request"""
        request_lower = request.lower()
        
        if any(word in request_lower for word in ["finance", "money", "revenue", "cost"]):
            return "finance"
        elif any(word in request_lower for word in ["engineering", "code", "technical", "development"]):
            return "engineering"
        elif any(word in request_lower for word in ["operations", "process", "workflow"]):
            return "operations"
        else:
            return "general"


# Standalone function for backward compatibility
async def create_enhanced_solomon() -> EnhancedSolomon:
    """Create and initialize enhanced Solomon agent"""
    
    solomon = EnhancedSolomon()
    await solomon.initialize()
    return solomon


# Main function for testing
async def main():
    """Test enhanced Solomon agent"""
    
    print("🧠 Initializing Enhanced Solomon Agent...")
    
    solomon = await create_enhanced_solomon()
    
    print("✅ Enhanced Solomon initialized successfully!")
    
    # Test basic chat
    response = await solomon.handle_user_chat(
        "I need a strategic analysis of our current agent architecture and recommendations for scaling to 120+ agents"
    )
    
    print(f"\n📊 Solomon's Response:\n{response}")
    
    # Test status
    status = await solomon.get_enhanced_status()
    print(f"\n📈 Enhanced Status: {json.dumps(status, indent=2)}")


if __name__ == "__main__":
    asyncio.run(main())
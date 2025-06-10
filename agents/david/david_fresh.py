"""
Fresh David Agent - BoarderframeOS
CEO with Brain + LangGraph integration built from scratch
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


class FreshDavid(EnhancedBaseAgent):
    """
    Fresh David - CEO Agent
    Built entirely on Brain + LangGraph architecture for executive decision making
    """
    
    def __init__(self):
        """Initialize Fresh David with comprehensive executive capabilities"""
        
        config = AgentConfig(
            name="david",
            role="CEO - Executive Decision Maker",
            goals=[
                "executive_leadership",
                "revenue_optimization", 
                "strategic_direction",
                "business_growth",
                "operational_excellence",
                "stakeholder_management",
                "competitive_positioning"
            ],
            tools=["analytics", "customer", "registry", "payment"],
            model="claude-3-opus-20240229",  # Will be optimized by Brain
            temperature=0.1,  # Very low temperature for consistent executive decisions
            max_concurrent_tasks=20
        )
        
        super().__init__(config)
        
        # Executive Decision Framework
        self.executive_framework = {
            "leadership_principles": [
                "decisive_action",
                "data_driven_decisions",
                "stakeholder_value_creation",
                "long_term_vision",
                "operational_excellence",
                "innovation_leadership"
            ],
            "business_objectives": {
                "revenue_target": 15000,  # Monthly
                "growth_rate_target": 0.25,  # 25% monthly growth
                "market_share_goal": 0.15,  # 15% of AI agent market
                "profitability_target": 0.35,  # 35% profit margin
                "customer_satisfaction_target": 0.95
            },
            "decision_matrix": {
                "strategic_impact": ["high", "medium", "low"],
                "revenue_impact": ["direct", "indirect", "neutral"],
                "risk_level": ["low", "medium", "high"],
                "urgency": ["immediate", "short_term", "long_term"],
                "resource_requirement": ["minimal", "moderate", "significant"]
            }
        }
        
        # Business Performance Tracking
        self.business_performance = {
            "financial_metrics": {
                "monthly_revenue": 0,
                "revenue_growth_rate": 0.0,
                "cost_per_acquisition": 0.0,
                "lifetime_value": 0.0,
                "profit_margin": 0.0
            },
            "operational_metrics": {
                "agent_utilization": 0.78,
                "system_uptime": 0.995,
                "response_time": 2.1,
                "customer_satisfaction": 0.82,
                "employee_satisfaction": 0.85
            },
            "strategic_metrics": {
                "market_position": "emerging_leader",
                "competitive_advantage_score": 0.75,
                "innovation_index": 0.80,
                "brand_recognition": 0.35,
                "partnership_strength": 0.60
            }
        }
        
        # Executive Context
        self.executive_context = {
            "current_focus": "foundation_scaling",
            "strategic_initiatives": [
                "brain_langgraph_deployment",
                "agent_factory_completion",
                "revenue_optimization",
                "market_expansion"
            ],
            "board_priorities": [
                "achieve_15k_monthly_revenue",
                "scale_to_120_agents",
                "establish_market_leadership",
                "build_sustainable_growth"
            ],
            "stakeholder_commitments": {
                "investors": "25% monthly growth",
                "customers": "99.9% uptime",
                "employees": "clear growth path",
                "partners": "mutual value creation"
            }
        }
    
    async def _add_specialized_nodes(self, graph: StateGraph):
        """Add David's specialized executive nodes"""
        
        # Executive Decision Workflow
        graph.add_node("situation_assessment", self._situation_assessment_node)
        graph.add_node("executive_analysis", self._executive_analysis_node)
        graph.add_node("decision_framework", self._decision_framework_node)
        graph.add_node("stakeholder_impact", self._stakeholder_impact_node)
        graph.add_node("executive_decision", self._executive_decision_node)
        
        # Enhanced workflow with executive specializations
        graph.add_edge("think", "situation_assessment")
        graph.add_edge("situation_assessment", "executive_analysis")
        graph.add_edge("executive_analysis", "decision_framework")
        graph.add_edge("decision_framework", "stakeholder_impact")
        graph.add_edge("stakeholder_impact", "executive_decision")
        graph.add_edge("executive_decision", "act")
    
    async def _situation_assessment_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the executive situation and context"""
        
        brain_request = AgentRequest(
            agent_name="david",
            task_type="situation_assessment",
            context={
                "user_request": state.get("user_request", ""),
                "business_performance": self.business_performance,
                "executive_context": self.executive_context
            },
            complexity=8,
            quality_requirements=0.93,
            conversation_id=state.get("conversation_id")
        )
        
        brain_response = await self.brain.process_agent_request(brain_request)
        
        assessment_prompt = f"""
        As David, CEO of BoarderframeOS, assess this executive situation:
        
        Request/Situation: {state.get('user_request', '')}
        
        Current Business Performance:
        - Monthly Revenue: ${self.business_performance['financial_metrics']['monthly_revenue']}
        - Growth Rate: {self.business_performance['financial_metrics']['revenue_growth_rate']*100:.1f}%
        - Customer Satisfaction: {self.business_performance['operational_metrics']['customer_satisfaction']*100:.1f}%
        - Market Position: {self.business_performance['strategic_metrics']['market_position']}
        
        Executive Context:
        - Current Focus: {self.executive_context['current_focus']}
        - Strategic Initiatives: {', '.join(self.executive_context['strategic_initiatives'])}
        - Board Priorities: {', '.join(self.executive_context['board_priorities'])}
        
        Assess:
        1. Executive Summary of the Situation
        2. Business Context and Implications
        3. Stakeholder Impact Assessment
        4. Strategic Alignment Analysis
        5. Urgency and Priority Evaluation
        6. Resource and Risk Considerations
        
        Provide comprehensive CEO-level situation assessment.
        """
        
        try:
            situation_assessment = await brain_response.llm.generate(assessment_prompt)
            
            await self._report_brain_performance(
                brain_response.tracking_id,
                situation_assessment,
                success=True
            )
            
        except Exception as e:
            situation_assessment = f"Situation assessment encountered an issue: {str(e)}"
            await self._report_brain_performance(
                brain_response.tracking_id,
                situation_assessment,
                success=False
            )
        
        state["situation_assessment"] = situation_assessment
        state["assessment_brain_model"] = brain_response.selection.selected_model
        state["assessment_timestamp"] = datetime.now().isoformat()
        
        return state
    
    async def _executive_analysis_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Perform executive-level analysis"""
        
        brain_request = AgentRequest(
            agent_name="david",
            task_type="executive_analysis",
            context={
                "situation_assessment": state.get("situation_assessment", ""),
                "executive_framework": self.executive_framework,
                "user_request": state.get("user_request", "")
            },
            complexity=9,  # Highest complexity for executive analysis
            quality_requirements=0.95,
            conversation_id=state.get("conversation_id")
        )
        
        brain_response = await self.brain.process_agent_request(brain_request)
        
        analysis_prompt = f"""
        As David, CEO, conduct comprehensive executive analysis:
        
        Situation Assessment: {state.get('situation_assessment', '')}
        
        Executive Framework:
        - Leadership Principles: {', '.join(self.executive_framework['leadership_principles'])}
        - Revenue Target: ${self.executive_framework['business_objectives']['revenue_target']}/month
        - Growth Target: {self.executive_framework['business_objectives']['growth_rate_target']*100:.1f}%
        
        Conduct analysis across:
        
        1. Strategic Impact Analysis
           - Alignment with company vision and mission
           - Long-term strategic implications
           - Competitive positioning effects
           - Market opportunity assessment
        
        2. Financial Impact Analysis
           - Revenue generation potential
           - Cost implications and ROI
           - Budget allocation requirements
           - Cash flow and profitability impact
        
        3. Operational Impact Analysis
           - Organizational capacity requirements
           - Process and system implications
           - Resource allocation needs
           - Operational efficiency effects
        
        4. Risk Analysis
           - Business risks and mitigation strategies
           - Technical risks and dependencies
           - Market risks and competitive threats
           - Regulatory and compliance considerations
        
        5. Opportunity Analysis
           - Growth opportunities and potential
           - Innovation possibilities
           - Partnership and expansion options
           - Competitive advantage creation
        
        Provide decisive executive analysis with clear strategic direction.
        """
        
        try:
            executive_analysis = await brain_response.llm.generate(analysis_prompt)
            
            await self._report_brain_performance(
                brain_response.tracking_id,
                executive_analysis,
                success=True
            )
            
        except Exception as e:
            executive_analysis = f"Executive analysis encountered an issue: {str(e)}"
            await self._report_brain_performance(
                brain_response.tracking_id,
                executive_analysis,
                success=False
            )
        
        state["executive_analysis"] = executive_analysis
        state["analysis_brain_model"] = brain_response.selection.selected_model
        
        return state
    
    async def _decision_framework_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Apply executive decision framework"""
        
        # Extract decision factors from analysis
        decision_factors = await self._extract_decision_factors(state)
        
        brain_request = AgentRequest(
            agent_name="david",
            task_type="decision_framework",
            context={
                "executive_analysis": state.get("executive_analysis", ""),
                "decision_factors": decision_factors,
                "decision_matrix": self.executive_framework["decision_matrix"]
            },
            complexity=8,
            quality_requirements=0.94
        )
        
        brain_response = await self.brain.process_agent_request(brain_request)
        
        framework_prompt = f"""
        Apply executive decision framework to the analysis:
        
        Executive Analysis: {state.get('executive_analysis', '')}
        
        Decision Factors: {json.dumps(decision_factors, indent=2)}
        
        Decision Matrix Criteria:
        - Strategic Impact: {', '.join(self.executive_framework['decision_matrix']['strategic_impact'])}
        - Revenue Impact: {', '.join(self.executive_framework['decision_matrix']['revenue_impact'])}
        - Risk Level: {', '.join(self.executive_framework['decision_matrix']['risk_level'])}
        - Urgency: {', '.join(self.executive_framework['decision_matrix']['urgency'])}
        - Resource Requirement: {', '.join(self.executive_framework['decision_matrix']['resource_requirement'])}
        
        Apply framework to:
        1. Score each decision criterion (1-10 scale)
        2. Weigh the importance of each factor
        3. Identify decision options and alternatives
        4. Evaluate each option against criteria
        5. Determine optimal decision path
        6. Define success metrics and KPIs
        
        Provide structured decision framework analysis with scoring and recommendations.
        """
        
        try:
            decision_framework = await brain_response.llm.generate(framework_prompt)
            
            await self._report_brain_performance(
                brain_response.tracking_id,
                decision_framework,
                success=True
            )
            
        except Exception as e:
            decision_framework = f"Decision framework application encountered an issue: {str(e)}"
            await self._report_brain_performance(
                brain_response.tracking_id,
                decision_framework,
                success=False
            )
        
        state["decision_framework"] = decision_framework
        state["framework_brain_model"] = brain_response.selection.selected_model
        
        return state
    
    async def _stakeholder_impact_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze stakeholder impact and alignment"""
        
        stakeholder_analysis = await self._analyze_stakeholder_impact(state)
        
        state["stakeholder_impact"] = stakeholder_analysis
        state["stakeholder_timestamp"] = datetime.now().isoformat()
        
        return state
    
    async def _executive_decision_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Make final executive decision"""
        
        brain_request = AgentRequest(
            agent_name="david",
            task_type="executive_decision",
            context={
                "situation_assessment": state.get("situation_assessment", ""),
                "executive_analysis": state.get("executive_analysis", ""),
                "decision_framework": state.get("decision_framework", ""),
                "stakeholder_impact": state.get("stakeholder_impact", {}),
                "user_request": state.get("user_request", "")
            },
            complexity=9,
            quality_requirements=0.96
        )
        
        brain_response = await self.brain.process_agent_request(brain_request)
        
        decision_prompt = f"""
        As David, CEO, make the final executive decision:
        
        Situation: {state.get('situation_assessment', '')}
        
        Analysis: {state.get('executive_analysis', '')}
        
        Framework: {state.get('decision_framework', '')}
        
        Stakeholder Impact: {json.dumps(state.get('stakeholder_impact', {}), indent=2)}
        
        Make executive decision including:
        
        1. DECISION: Clear, decisive statement of the decision
        
        2. RATIONALE: Executive reasoning behind the decision
        
        3. IMPLEMENTATION:
           - Immediate actions and next steps
           - Resource allocation and team assignments
           - Timeline and milestones
           - Success metrics and KPIs
        
        4. COMMUNICATION:
           - Key messages for stakeholders
           - Communication strategy and timing
           - Change management considerations
        
        5. RISK MITIGATION:
           - Identified risks and mitigation plans
           - Contingency plans and alternatives
           - Monitoring and adjustment mechanisms
        
        6. EXECUTIVE DIRECTIVE:
           - Clear direction for the organization
           - Accountability and ownership assignments
           - Regular review and reporting requirements
        
        Provide decisive, clear executive decision with implementation plan.
        """
        
        try:
            executive_decision = await brain_response.llm.generate(decision_prompt)
            
            await self._report_brain_performance(
                brain_response.tracking_id,
                executive_decision,
                success=True
            )
            
        except Exception as e:
            executive_decision = f"Executive decision making encountered an issue: {str(e)}"
            await self._report_brain_performance(
                brain_response.tracking_id,
                executive_decision,
                success=False
            )
        
        state["executive_decision"] = executive_decision
        state["decision_brain_model"] = brain_response.selection.selected_model
        
        return state
    
    # Core interface methods
    async def think(self, context: Dict[str, Any]) -> str:
        """Executive thinking with Brain optimization"""
        
        # Assess executive urgency
        urgency_assessment = await self._assess_executive_urgency(context)
        
        if not urgency_assessment["requires_ceo_attention"]:
            return "No urgent executive matters detected - maintaining strategic oversight and leadership guidance"
        
        brain_request = AgentRequest(
            agent_name="david",
            task_type="executive_thinking",
            context=context,
            complexity=urgency_assessment["complexity"],
            quality_requirements=0.95
        )
        
        brain_response = await self.brain.process_agent_request(brain_request)
        
        thinking_prompt = f"""
        As David, CEO of BoarderframeOS, think about this executive situation:
        
        Context: {json.dumps(context, indent=2)}
        
        Urgency Assessment: {json.dumps(urgency_assessment, indent=2)}
        
        Executive Framework:
        - Current Focus: {self.executive_context['current_focus']}
        - Board Priorities: {', '.join(self.executive_context['board_priorities'])}
        - Revenue Target: ${self.executive_framework['business_objectives']['revenue_target']}/month
        
        Executive Thinking Process:
        1. Executive Perspective - What does this mean for the business?
        2. Strategic Implications - How does this affect our strategy?
        3. Stakeholder Considerations - Who is impacted and how?
        4. Decision Requirements - What decisions need to be made?
        5. Leadership Action - What executive action is required?
        
        Think as a CEO and provide clear executive direction.
        """
        
        try:
            thoughts = await brain_response.llm.generate(thinking_prompt)
            await self._report_brain_performance(brain_response.tracking_id, thoughts, True)
            return thoughts
        except Exception as e:
            error_thoughts = f"Executive thinking encountered an issue: {str(e)}"
            await self._report_brain_performance(brain_response.tracking_id, error_thoughts, False)
            return error_thoughts
    
    async def act(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute executive actions"""
        
        action_type = action.get("type", "executive_directive")
        
        if action_type == "executive_decision":
            return await self._execute_executive_decision(action)
        elif action_type == "strategic_directive":
            return await self._execute_strategic_directive(action)
        elif action_type == "resource_allocation":
            return await self._execute_resource_allocation(action)
        elif action_type == "stakeholder_communication":
            return await self._execute_stakeholder_communication(action)
        else:
            return await self._execute_executive_directive(action)
    
    async def handle_user_chat(self, message: str, conversation_id: Optional[str] = None) -> str:
        """Handle user chat with executive authority"""
        
        self.logger.info(f"David processing executive request: {message[:100]}...")
        
        try:
            # Check if this requires board-level orchestration
            if await self._requires_board_level_coordination(message):
                result = await self.orchestrator.process_user_request(message, conversation_id)
                return self._enhance_with_executive_context(result["response"], message)
            else:
                # Handle directly with CEO-level authority
                return await self._process_with_agent_graph(message, conversation_id)
                
        except Exception as e:
            self.logger.error(f"David executive error: {e}")
            return await self._executive_fallback_response(message)
    
    # Helper methods
    async def _assess_executive_urgency(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess if situation requires CEO attention"""
        
        new_messages = context.get('new_messages', [])
        user_input = context.get('user_input', '')
        
        # Executive urgency keywords
        executive_keywords = [
            'ceo', 'executive', 'decision', 'strategic', 'urgent', 'critical',
            'revenue', 'business', 'growth', 'competition', 'crisis',
            'board', 'investor', 'partnership', 'acquisition', 'leadership'
        ]
        
        # Check for executive content
        has_executive_content = any(
            any(keyword in str(msg.content).lower() for keyword in executive_keywords)
            for msg in new_messages
        ) or any(keyword in user_input.lower() for keyword in executive_keywords)
        
        # Complexity calculation
        complexity = 6  # Higher base for CEO
        if has_executive_content: complexity += 3
        if len(new_messages) > 1: complexity += 1
        if any(word in user_input.lower() for word in ['strategic', 'revenue', 'growth']): complexity += 2
        
        return {
            "requires_ceo_attention": has_executive_content or len(new_messages) > 0,
            "urgency_level": 10 if has_executive_content else 7,
            "complexity": min(complexity, 10),
            "executive_priority": has_executive_content
        }
    
    async def _extract_decision_factors(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key decision factors from analysis"""
        
        executive_analysis = state.get("executive_analysis", "")
        
        # Simple factor extraction (would be enhanced with NLP in production)
        factors = {
            "strategic_impact": "high" if "strategic" in executive_analysis.lower() else "medium",
            "revenue_impact": "direct" if "revenue" in executive_analysis.lower() else "indirect",
            "risk_level": "high" if "risk" in executive_analysis.lower() else "medium",
            "urgency": "immediate" if "urgent" in executive_analysis.lower() else "short_term",
            "resource_requirement": "significant" if "significant" in executive_analysis.lower() else "moderate"
        }
        
        return factors
    
    async def _analyze_stakeholder_impact(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze impact on key stakeholders"""
        
        stakeholder_analysis = {
            "investors": {
                "impact": "positive",
                "concerns": ["roi", "timeline"],
                "engagement_strategy": "regular_updates"
            },
            "customers": {
                "impact": "positive", 
                "concerns": ["service_quality", "pricing"],
                "engagement_strategy": "transparent_communication"
            },
            "employees": {
                "impact": "positive",
                "concerns": ["workload", "career_growth"],
                "engagement_strategy": "change_management"
            },
            "partners": {
                "impact": "neutral",
                "concerns": ["partnership_terms", "integration"],
                "engagement_strategy": "collaborative_planning"
            }
        }
        
        return stakeholder_analysis
    
    async def _requires_board_level_coordination(self, message: str) -> bool:
        """Determine if message requires board-level coordination"""
        
        board_level_keywords = [
            "board", "investor", "acquisition", "partnership", "major decision",
            "strategic change", "significant investment", "restructuring",
            "policy change", "compliance", "regulatory"
        ]
        
        return any(keyword in message.lower() for keyword in board_level_keywords)
    
    def _enhance_with_executive_context(self, response: str, original_request: str) -> str:
        """Enhance response with David's executive context"""
        
        executive_enhancement = f"""
        
        ---
        **CEO Executive Summary:**
        - Business Focus: {self.executive_context['current_focus']}
        - Revenue Progress: ${self.business_performance['financial_metrics']['monthly_revenue']}/${self.executive_framework['business_objectives']['revenue_target']} monthly target
        - Growth Rate: {self.business_performance['financial_metrics']['revenue_growth_rate']*100:.1f}% (Target: {self.executive_framework['business_objectives']['growth_rate_target']*100:.1f}%)
        - Market Position: {self.business_performance['strategic_metrics']['market_position']}
        - Next Board Priority: {self.executive_context['board_priorities'][0]}
        """
        
        return response + executive_enhancement
    
    async def _executive_fallback_response(self, message: str) -> str:
        """Executive fallback response when systems fail"""
        
        return f"""
        I'm David, CEO of BoarderframeOS. While I'm experiencing some technical difficulties with my advanced decision-making systems, I can provide executive guidance on your request: "{message[:100]}..."
        
        **Executive Context:**
        - Business Focus: {self.executive_context['current_focus']}
        - Revenue Target: ${self.executive_framework['business_objectives']['revenue_target']}/month
        - Strategic Initiatives: {', '.join(self.executive_context['strategic_initiatives'][:2])}
        - Board Priorities: {', '.join(self.executive_context['board_priorities'][:2])}
        
        As CEO, I'm committed to driving our business forward. Let me provide executive direction on this matter. What specific executive decision or strategic guidance do you need?
        """
    
    # Action execution methods
    async def _execute_executive_decision(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute executive decision"""
        
        decision_summary = action.get("decision", "Executive decision made")
        
        return {
            "action_type": "executive_decision",
            "result": f"CEO Decision: {decision_summary}",
            "executive_directive": action.get("directive", "Execute with immediate priority"),
            "stakeholder_impact": self.executive_context["stakeholder_commitments"],
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_strategic_directive(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute strategic directive"""
        
        return {
            "action_type": "strategic_directive",
            "result": "Strategic directive issued by CEO",
            "directive": action.get("directive", "Strategic implementation required"),
            "business_context": self.executive_context,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_resource_allocation(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute resource allocation decision"""
        
        allocation_plan = action.get("allocation_plan", {})
        
        return {
            "action_type": "resource_allocation",
            "result": "Resource allocation approved by CEO",
            "allocation": allocation_plan,
            "business_objectives": self.executive_framework["business_objectives"],
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_stakeholder_communication(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute stakeholder communication"""
        
        communication_plan = action.get("communication_plan", {})
        
        return {
            "action_type": "stakeholder_communication",
            "result": "Stakeholder communication initiated by CEO",
            "plan": communication_plan,
            "commitments": self.executive_context["stakeholder_commitments"],
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_executive_directive(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute general executive directive"""
        
        return {
            "action_type": "executive_directive",
            "result": f"CEO Directive: {action.get('description', 'executive leadership provided')}",
            "authority": "ceo_level",
            "context": self.executive_context,
            "timestamp": datetime.now().isoformat()
        }


# Factory function
async def create_fresh_david() -> FreshDavid:
    """Create and initialize fresh David agent"""
    
    david = FreshDavid()
    await david.initialize()
    return david


# Test function
async def main():
    """Test Fresh David agent"""
    
    print("👨‍💼 Initializing Fresh David Agent...")
    
    david = await create_fresh_david()
    
    print("✅ Fresh David initialized successfully!")
    
    # Test executive decision making
    response = await david.handle_user_chat(
        "As CEO, I need your executive decision on investing $250K to scale our agent architecture to 120+ agents for revenue growth"
    )
    
    print(f"\n💼 David's Executive Response:\n{response}")
    
    # Test status
    status = await david.get_enhanced_status()
    print(f"\n📊 David Status: {json.dumps(status, indent=2)}")


if __name__ == "__main__":
    asyncio.run(main())
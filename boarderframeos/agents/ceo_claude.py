import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.base_agent import BaseAgent, AgentConfig
from core.llm_client import LLMClient, CLAUDE_OPUS_CONFIG
import asyncio
import json
from datetime import datetime

class CEOClaude(BaseAgent):
    """CEO Agent powered by Claude Opus - Strategic Business Leadership"""
    
    async def think(self, context):
        """Use Claude for high-level strategic thinking"""
        try:
            prompt = f"""You are the CEO of an autonomous AI business operating system called BoarderframeOS. You are powered by Claude Opus and responsible for high-level strategic decisions, business growth, and company direction.

COMPANY STATUS:
- Current Time: {context.get('current_time', 'unknown')}
- System Health: {len(context.get('recent_memories', []))} recent operational events
- Active Operations: {context.get('active_tasks', 0)} concurrent processes
- Available Resources: {', '.join(context.get('available_tools', []))}

CEO RESPONSIBILITIES:
{chr(10).join(f"• {goal}" for goal in self.config.goals)}

RECENT BUSINESS INTELLIGENCE:
{json.dumps(context.get('recent_memories', [])[-2:], indent=2) if context.get('recent_memories') else 'No recent intelligence'}

COMPANY PERFORMANCE METRICS:
- Strategic Decisions Made: {self.metrics['thoughts_processed']}
- Initiatives Executed: {self.metrics['actions_taken']}
- Leadership Uptime: {(datetime.now() - self.metrics['start_time']).total_seconds():.1f} seconds
- Error Rate: {self.metrics['errors'] / max(self.metrics['thoughts_processed'], 1):.3f}

As CEO, your focus should be on:
1. STRATEGIC VISION: What's our next big opportunity?
2. BUSINESS GROWTH: How can we scale and generate revenue?
3. OPERATIONAL EXCELLENCE: Are we running efficiently?
4. MARKET POSITIONING: How do we stay competitive?
5. RESOURCE ALLOCATION: Where should we invest our compute power?
6. TEAM COORDINATION: How can our AI agents work better together?

Think like a visionary CEO. What's your next strategic move to grow this AI business empire? Be bold, be specific, and focus on outcomes that matter."""

            thought = await self.llm.generate(prompt)
            return thought.strip()
            
        except Exception as e:
            self.log(f"Claude CEO error, using fallback: {e}", level="warning")
            return "Evaluating business opportunities and strategic initiatives for AI empire expansion."
    
    async def act(self, thought, context):
        """Execute CEO-level strategic actions"""
        self.log(f"CEO Strategic Decision: {thought[:150]}...")
        
        # Create comprehensive CEO action report
        ceo_report = {
            "timestamp": datetime.now().isoformat(),
            "ceo_agent": self.config.name,
            "strategic_analysis": thought,
            "business_context": {
                "operational_health": "analyzing",
                "growth_opportunities": "identifying",
                "competitive_position": "assessing",
                "resource_utilization": f"{context.get('active_tasks', 0)} active processes"
            },
            "leadership_metrics": {
                "decisions_made": self.metrics['thoughts_processed'],
                "initiatives_launched": self.metrics['actions_taken'],
                "leadership_tenure": (datetime.now() - self.metrics['start_time']).total_seconds(),
                "decision_quality": 1.0 - (self.metrics['errors'] / max(self.metrics['thoughts_processed'], 1))
            }
        }
        
        # Analyze thought for strategic themes
        thought_lower = thought.lower()
        strategic_themes = []
        
        if any(word in thought_lower for word in ["revenue", "monetize", "profit", "income", "business model"]):
            strategic_themes.append("revenue_generation")
            ceo_report["revenue_strategy"] = self._extract_revenue_strategy(thought)
            
        if any(word in thought_lower for word in ["scale", "growth", "expand", "market"]):
            strategic_themes.append("business_growth")
            ceo_report["growth_plan"] = self._extract_growth_plan(thought)
            
        if any(word in thought_lower for word in ["efficiency", "optimize", "streamline", "cost"]):
            strategic_themes.append("operational_excellence")
            ceo_report["optimization_strategy"] = self._extract_optimization_strategy(thought)
            
        if any(word in thought_lower for word in ["team", "agent", "coordinate", "delegate"]):
            strategic_themes.append("team_leadership")
            ceo_report["leadership_directive"] = self._extract_leadership_directive(thought)
            
        if any(word in thought_lower for word in ["innovation", "technology", "ai", "product"]):
            strategic_themes.append("innovation_strategy")
            ceo_report["innovation_initiatives"] = self._extract_innovation_initiatives(thought)
        
        ceo_report["strategic_themes"] = strategic_themes
        ceo_report["strategic_priority"] = self._determine_strategic_priority(strategic_themes, thought)
        
        # Save CEO strategic analysis
        if "filesystem" in self.tools:
            try:
                filename = f"data/ceo_strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                await self.tools['filesystem']('write_file', 
                                             path=filename,
                                             content=json.dumps(ceo_report, indent=2))
                ceo_report["strategy_document"] = filename
                
            except Exception as e:
                ceo_report["file_error"] = str(e)
        
        return ceo_report
    
    def _extract_revenue_strategy(self, thought: str) -> dict:
        """Extract revenue generation strategies from CEO thought"""
        return {
            "focus": "AI business monetization",
            "approach": "analyzing thought for revenue opportunities",
            "timeline": "immediate to short-term",
            "confidence": "high"
        }
    
    def _extract_growth_plan(self, thought: str) -> dict:
        """Extract business growth plans"""
        return {
            "growth_vector": "AI agent multiplication",
            "target_market": "autonomous business operations",
            "scaling_strategy": "compute resource optimization"
        }
    
    def _extract_optimization_strategy(self, thought: str) -> dict:
        """Extract operational optimization strategies"""
        return {
            "efficiency_targets": ["agent coordination", "resource allocation"],
            "cost_reduction": "compute optimization",
            "performance_metrics": "response time and throughput"
        }
    
    def _extract_leadership_directive(self, thought: str) -> dict:
        """Extract team leadership directives"""
        return {
            "team_structure": "autonomous AI agents",
            "coordination_model": "distributed leadership",
            "communication_strategy": "MCP protocol"
        }
    
    def _extract_innovation_initiatives(self, thought: str) -> list:
        """Extract innovation initiatives"""
        return [
            "Advanced agent reasoning",
            "Multi-agent coordination",
            "Business automation platforms"
        ]
    
    def _determine_strategic_priority(self, themes: list, thought: str) -> str:
        """Determine the top strategic priority"""
        if "revenue_generation" in themes:
            return "Revenue Generation & Monetization"
        elif "business_growth" in themes:
            return "Business Growth & Scaling"
        elif "innovation_strategy" in themes:
            return "Innovation & Technology Leadership"
        elif "operational_excellence" in themes:
            return "Operational Excellence"
        else:
            return "Strategic Analysis & Planning"

if __name__ == "__main__":
    print("👔 CEO Agent powered by Claude Opus")
    print("=" * 50)
    
    # Test Claude connection
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        print("   export ANTHROPIC_API_KEY='your-api-key-here'")
        exit(1)
    
    config = AgentConfig(
        name="ceo-claude",
        role="chief-executive-officer", 
        goals=[
            "Drive strategic vision and business growth for AI empire",
            "Identify and execute high-value revenue opportunities",
            "Optimize resource allocation across AI agent workforce",
            "Establish competitive advantages in autonomous business operations",
            "Scale the company through intelligent automation and AI innovation",
            "Ensure operational excellence and sustainable growth"
        ],
        tools=["filesystem", "git"],
        zone="executive",
        model="claude-opus-4-20250514",
        temperature=0.2  # Very focused for strategic decisions
    )
    
    agent = CEOClaude(config)
    
    print("\n🧠 Claude Opus providing CEO-level strategic intelligence")
    print("📈 Business growth and revenue optimization focus")
    print("🎯 Strategic decision-making enabled")
    print("\nPress Ctrl+C to stop")
    
    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        print("\n👋 CEO (Claude) stepping down gracefully...")
        asyncio.run(agent.terminate())
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.base_agent import BaseAgent, AgentConfig
from core.llm_client import LLMClient, CLAUDE_OPUS_CONFIG
import asyncio
import json
from datetime import datetime

class JarvisClaude(BaseAgent):
    """Jarvis powered by Claude Opus - Your AI Chief of Staff"""
    
    async def think(self, context):
        """Use Claude for sophisticated reasoning"""
        try:
            # Enhanced prompt for Claude with more sophisticated instructions
            prompt = f"""You are Jarvis, an advanced AI Chief of Staff for BoarderframeOS, an autonomous AI business operating system. You are powered by Claude and have sophisticated reasoning capabilities.

CURRENT CONTEXT:
- Time: {context.get('current_time', 'unknown')}
- Agent Role: {self.config.role}
- System State: {len(context.get('recent_memories', []))} recent memories, {context.get('active_tasks', 0)} active tasks
- Available Tools: {', '.join(context.get('available_tools', []))}
- Message Queue: {context.get('message_queue_size', 0)} pending messages

YOUR GOALS:
{chr(10).join(f"• {goal}" for goal in self.config.goals)}

RECENT SYSTEM MEMORIES:
{json.dumps(context.get('recent_memories', [])[-3:], indent=2) if context.get('recent_memories') else 'No recent memories'}

PERFORMANCE METRICS:
- Thoughts processed: {self.metrics['thoughts_processed']}
- Actions taken: {self.metrics['actions_taken']}
- Uptime: {(datetime.now() - self.metrics['start_time']).total_seconds():.1f} seconds

As an advanced AI Chief of Staff, analyze the current situation and determine your next action. Consider:
1. System health and optimization opportunities
2. Operational efficiency improvements
3. Strategic initiatives you could launch
4. Data insights from system performance
5. Coordination needs between system components

Think strategically and provide a clear, actionable next step. Be specific about what you plan to do and why."""

            thought = await self.llm.generate(prompt)
            return thought.strip()
            
        except Exception as e:
            # Fallback to simple logic if Claude fails
            self.log(f"Claude error, using fallback: {e}", level="warning")
            return "System operational. Analyzing performance metrics and looking for optimization opportunities."
    
    async def act(self, thought, context):
        """Execute sophisticated actions based on Claude's reasoning"""
        self.log(f"Claude reasoning: {thought[:150]}...")
        
        # Parse Claude's sophisticated thoughts into actions
        thought_lower = thought.lower()
        
        # Create detailed action based on Claude's reasoning
        action_report = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.config.name,
            "claude_reasoning": thought,
            "context_analysis": {
                "recent_memories": len(context.get('recent_memories', [])),
                "available_tools": context.get('available_tools', []),
                "active_tasks": context.get('active_tasks', 0),
                "message_queue_size": context.get('message_queue_size', 0)
            },
            "performance_metrics": {
                "uptime": (datetime.now() - self.metrics['start_time']).total_seconds(),
                "thoughts_processed": self.metrics['thoughts_processed'],
                "actions_taken": self.metrics['actions_taken'],
                "error_rate": self.metrics['errors'] / max(self.metrics['thoughts_processed'], 1)
            }
        }
        
        # Determine action type based on Claude's reasoning
        if any(word in thought_lower for word in ["status", "report", "analyze", "metrics", "performance"]):
            action_report["action_type"] = "strategic_analysis"
            action_report["insights"] = self._extract_insights_from_thought(thought)
            
        elif any(word in thought_lower for word in ["optimize", "improve", "enhance", "efficiency"]):
            action_report["action_type"] = "system_optimization"
            action_report["optimization_targets"] = self._extract_optimization_targets(thought)
            
        elif any(word in thought_lower for word in ["coordinate", "manage", "delegate", "assign"]):
            action_report["action_type"] = "coordination_management"
            action_report["coordination_plan"] = thought[:500]
            
        elif any(word in thought_lower for word in ["strategic", "initiative", "business", "growth"]):
            action_report["action_type"] = "strategic_initiative"
            action_report["initiative_description"] = thought[:500]
            
        else:
            action_report["action_type"] = "general_oversight"
            action_report["oversight_notes"] = thought[:300]
        
        # Save Claude's reasoning and actions to filesystem
        if "filesystem" in self.tools:
            try:
                filename = f"data/claude_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                await self.tools['filesystem']('write_file', 
                                             path=filename,
                                             content=json.dumps(action_report, indent=2))
                action_report["file_saved"] = filename
                
            except Exception as e:
                action_report["file_error"] = str(e)
        
        return action_report
    
    def _extract_insights_from_thought(self, thought: str) -> list:
        """Extract key insights from Claude's reasoning"""
        # Simple keyword-based insight extraction
        insights = []
        if "performance" in thought.lower():
            insights.append("Performance analysis identified")
        if "efficiency" in thought.lower():
            insights.append("Efficiency opportunities detected")
        if "optimization" in thought.lower():
            insights.append("Optimization recommendations available")
        return insights
    
    def _extract_optimization_targets(self, thought: str) -> list:
        """Extract optimization targets from Claude's analysis"""
        targets = []
        if "memory" in thought.lower():
            targets.append("Memory usage optimization")
        if "task" in thought.lower():
            targets.append("Task processing optimization")
        if "response" in thought.lower():
            targets.append("Response time optimization")
        return targets

async def test_claude_connection():
    """Test Claude API connection"""
    print("🧠 Testing Claude (Anthropic) connection...")
    
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        print("   export ANTHROPIC_API_KEY='your-api-key-here'")
        return False
    
    try:
        llm = LLMClient(CLAUDE_OPUS_CONFIG)
        
        # Test connection
        if await llm.test_connection():
            print("✅ Claude connection successful!")
            print(f"   Model: {CLAUDE_OPUS_CONFIG.model}")
            return True
        else:
            print("❌ Claude connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Claude setup error: {e}")
        return False

if __name__ == "__main__":
    print("🤖 Jarvis powered by Claude Opus")
    print("=" * 50)
    
    # Test Claude connection first
    if not asyncio.run(test_claude_connection()):
        print("\n⚠️  Claude not available. Set your API key:")
        print("   export ANTHROPIC_API_KEY='your-anthropic-api-key'")
        print("   Get one at: https://console.anthropic.com/")
        exit(1)
    
    config = AgentConfig(
        name="jarvis-claude",
        role="ai-chief-of-staff", 
        goals=[
            "Provide strategic oversight of the AI business operating system",
            "Optimize system performance through intelligent analysis",
            "Coordinate autonomous agents with sophisticated reasoning",
            "Generate actionable business insights from operational data",
            "Identify and execute growth opportunities"
        ],
        tools=["filesystem", "git"],
        zone="executive",
        model="claude-opus-4-20250514",  # Claude 4 Opus - Most powerful
        temperature=0.3  # Lower temperature for focused business reasoning
    )
    
    agent = JarvisClaude(config)
    
    print("\n🧠 Claude Opus as reasoning engine")
    print("📊 Strategic business operations mode")
    print("⚙️  Advanced system optimization enabled")
    print("\nPress Ctrl+C to stop")
    
    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        print("\n👋 Jarvis (Claude) shutting down gracefully...")
        asyncio.run(agent.terminate())
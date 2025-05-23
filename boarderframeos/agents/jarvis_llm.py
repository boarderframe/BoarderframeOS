import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.base_agent import BaseAgent, AgentConfig
from core.llm_client import LLMClient, OLLAMA_CONFIG
import asyncio
import json
from datetime import datetime

class JarvisLLM(BaseAgent):
    """Jarvis with real LLM reasoning"""
    
    async def think(self, context):
        """Use LLM for actual reasoning"""
        try:
            # Use the built-in LLM client from base agent
            thought = await self.llm.think(
                agent_name=self.config.name,
                role=self.config.role, 
                context=context,
                goals=self.config.goals
            )
            return thought.strip()
            
        except Exception as e:
            # Fallback to simple logic if LLM fails
            self.log(f"LLM error, using fallback: {e}", level="warning")
            if context.get('message_queue_size', 0) > 0:
                return "I should process pending messages from other agents"
            elif context.get('active_tasks', 0) == 0:
                return "System is idle, I should check for new tasks or create a status report"
            else:
                return f"Monitoring {context.get('active_tasks', 0)} active tasks"
    
    async def act(self, thought, context):
        """Execute actions based on LLM thoughts"""
        self.log(f"Acting on thought: {thought[:100]}...")
        
        # Parse the LLM thought for actionable items
        thought_lower = thought.lower()
        
        if any(word in thought_lower for word in ["message", "communicate", "contact"]):
            return {"action": "processed_messages", "status": "no messages found", "thought_summary": thought[:200]}
        
        elif any(word in thought_lower for word in ["status", "report", "monitor", "check"]):
            # Create a detailed status report
            report = {
                "timestamp": datetime.now().isoformat(),
                "system_status": "operational",
                "agent": self.config.name,
                "uptime": (datetime.now() - self.metrics['start_time']).total_seconds(),
                "thoughts_processed": self.metrics['thoughts_processed'],
                "actions_taken": self.metrics['actions_taken'],
                "llm_thought": thought,
                "context_summary": {
                    "recent_memories": len(context.get('recent_memories', [])),
                    "available_tools": context.get('available_tools', []),
                    "active_tasks": context.get('active_tasks', 0)
                }
            }
            
            # Try to write report using filesystem tool
            if "filesystem" in self.tools:
                try:
                    await self.tools['filesystem']('write_file', 
                                                 path=f"data/llm_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                                 content=json.dumps(report, indent=2))
                    return {"action": "llm_status_report_created", "report": report}
                except Exception as e:
                    return {"action": "llm_status_report_failed", "error": str(e), "report": report}
            else:
                return {"action": "llm_status_report_local", "report": report}
        
        elif any(word in thought_lower for word in ["task", "work", "create", "build"]):
            # LLM wants to do some work
            return {
                "action": "llm_task_identified", 
                "task_description": thought,
                "status": "analyzing task requirements",
                "next_steps": "breaking down into subtasks"
            }
        
        else:
            # General monitoring/thinking
            return {
                "action": "llm_reasoning", 
                "thought": thought,
                "status": "continuing analysis",
                "cognitive_load": len(thought.split())
            }

async def test_llm_connection():
    """Test if we can connect to LLM"""
    print("🧠 Testing LLM connection...")
    
    try:
        from core.llm_client import LLMClient, OLLAMA_CONFIG
        llm = LLMClient(OLLAMA_CONFIG)
        
        # Test connection
        if await llm.test_connection():
            print("✅ LLM connection successful!")
            return True
        else:
            print("❌ LLM connection failed")
            return False
            
    except Exception as e:
        print(f"❌ LLM setup error: {e}")
        return False

if __name__ == "__main__":
    # Test LLM first
    if not asyncio.run(test_llm_connection()):
        print("\n⚠️  LLM not available - install Ollama:")
        print("   brew install ollama")
        print("   ollama pull llama3.2")
        print("   ollama serve")
        print("\nRunning in fallback mode...\n")
    
    config = AgentConfig(
        name="jarvis-llm",
        role="chief-of-staff", 
        goals=[
            "Manage overall business operations using AI reasoning",
            "Coordinate between teams with intelligent decision making", 
            "Monitor system health and optimize performance",
            "Generate insights from system data"
        ],
        tools=["filesystem", "git"],
        zone="executive",
        model="llama3.2",
        temperature=0.7
    )
    
    agent = JarvisLLM(config)
    
    print("🤖 Starting Jarvis with LLM reasoning")
    print("📡 Model: llama3.2 via Ollama")
    print("Press Ctrl+C to stop")
    
    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        print("\n👋 Jarvis shutting down gracefully...")
        asyncio.run(agent.terminate())
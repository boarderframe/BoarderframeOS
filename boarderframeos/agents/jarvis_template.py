import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.base_agent import BaseAgent, AgentConfig
import asyncio
import json
from datetime import datetime

class Jarvis(BaseAgent):
    """Your AI Chief of Staff"""
    
    async def think(self, context):
        """Jarvis's reasoning process"""
        # Simple reasoning based on context
        if context.get('message_queue_size', 0) > 0:
            thought = "I should process pending messages from other agents"
        elif context.get('active_tasks', 0) == 0:
            thought = "System is idle, I should check for new tasks or create a status report"
        else:
            thought = f"Monitoring {context.get('active_tasks', 0)} active tasks"
        
        return thought
    
    async def act(self, thought, context):
        """Execute Jarvis's decisions"""
        if "process pending messages" in thought.lower():
            return {"action": "processed_messages", "status": "no messages found"}
        
        elif "check for new tasks" in thought.lower() or "status report" in thought.lower():
            # Create a simple status report
            report = {
                "timestamp": datetime.now().isoformat(),
                "system_status": "operational",
                "agent": self.config.name,
                "uptime": (datetime.now() - self.metrics['start_time']).total_seconds(),
                "thoughts_processed": self.metrics['thoughts_processed'],
                "actions_taken": self.metrics['actions_taken']
            }
            
            # Try to write report using filesystem tool
            if "filesystem" in self.tools:
                try:
                    await self.tools['filesystem']('write_file', 
                                                 path=f"data/status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                                 content=json.dumps(report, indent=2))
                    return {"action": "status_report_created", "report": report}
                except Exception as e:
                    return {"action": "status_report_failed", "error": str(e), "report": report}
            else:
                return {"action": "status_report_local", "report": report}
        
        else:
            return {"action": "monitoring", "status": "watching system", "thought": thought}

if __name__ == "__main__":
    config = AgentConfig(
        name="jarvis",
        role="chief-of-staff", 
        goals=["Manage other agents", "Optimize system performance", "Monitor system health"],
        tools=["filesystem", "git"],
        zone="executive"
    )
    
    agent = Jarvis(config)
    
    print("🤖 Starting Jarvis - Your AI Chief of Staff")
    print("Press Ctrl+C to stop")
    
    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        print("\n👋 Jarvis shutting down gracefully...")
        asyncio.run(agent.terminate())

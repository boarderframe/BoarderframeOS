"""
david Agent - BoarderframeOS
Generated agent implementation
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from boarderframeos.core.base_agent import BaseAgent, AgentConfig
from boarderframeos.core.llm_client import LLMClient
import asyncio
from typing import Dict, Any

class david(BaseAgent):
    """Generated general agent"""
    
    async def think(self, context: Dict[str, Any]) -> str:
        """Agent reasoning process"""
        # Use LLM for reasoning
        prompt = f"""
You are David Agent.

Your goals are:
- {goal}

Current context:
{context}

Based on this context, what should you do next? Provide a clear thought process.
"""
        
        response = await self.llm.chat([{"role": "user", "content": prompt}])
        return response.content
    
    async def act(self, thought: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute actions based on thoughts"""
        # Simple action framework
        if "search" in thought.lower():
            return {"action": "search", "query": thought}
        elif "analyze" in thought.lower():
            return {"action": "analyze", "data": context}
        elif "create" in thought.lower():
            return {"action": "create", "content": thought}
        else:
            return {"action": "wait", "reason": "No clear action identified"}

async def main():
    """Main entry point"""
    config = AgentConfig(
        name="david",
        role="David Agent",
        goals=['Assist with david related tasks'],
        tools=['mcp_filesystem'],
        zone="demo_zone",
        model="claude-3-opus-20240229"
    )
    
    agent = david(config)
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())

"""
Research Agent - BoarderframeOS
An AI agent specialized in research, analysis, and knowledge management
Uses MCP filesystem server for persistent memory and vector search
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.base_agent import BaseAgent, AgentConfig
from core.mcp_client import MCPClient, MCPConfig
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import hashlib
import re

class ResearchAgent(BaseAgent):
    """Advanced research agent with persistent memory and semantic search"""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.mcp_client = MCPClient()
        self.research_cache = {}
        self.active_research_topics = []
        
    async def think(self, context: Dict[str, Any]) -> str:
        """Research agent's reasoning process"""
        
        # Check for new research requests
        if context.get('research_query'):
            query = context['research_query']
            
            # First, search existing memories for related information
            similar_memories = await self._search_related_memories(query)
            
            if similar_memories and len(similar_memories.get('results', [])) > 0:
                thought = f"Found {len(similar_memories['results'])} related memories for '{query}'. I should synthesize this information and identify knowledge gaps."
            else:
                thought = f"New research topic: '{query}'. I need to start fresh research and build a knowledge base."
                
        # Check if we have active research that needs continuation
        elif self.active_research_topics:
            topic = self.active_research_topics[0]
            thought = f"Continuing research on '{topic}'. I should gather more information and update my knowledge base."
            
        # Check for analysis requests
        elif context.get('analysis_request'):
            request = context['analysis_request']
            thought = f"Analysis requested: {request}. I should search my memories and provide comprehensive insights."
            
        # Proactive knowledge management
        elif context.get('memory_count', 0) > 100:
            thought = "I have accumulated many memories. I should organize and cross-reference them to identify patterns and insights."
            
        else:
            thought = "System is idle. I should review recent memories and look for interesting patterns or research opportunities."
            
        return thought
    
    async def act(self, thought: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute research actions based on thoughts"""
        
        try:
            # Handle new research queries
            if "new research topic" in thought.lower() or context.get('research_query'):
                return await self._conduct_research(context.get('research_query'))
                
            # Handle synthesis of existing information
            elif "synthesize this information" in thought.lower():
                return await self._synthesize_memories(context.get('research_query'))
                
            # Handle analysis requests
            elif "analysis requested" in thought.lower():
                return await self._perform_analysis(context.get('analysis_request'))
                
            # Handle knowledge organization
            elif "organize and cross-reference" in thought.lower():
                return await self._organize_knowledge()
                
            # Handle proactive research
            elif "review recent memories" in thought.lower():
                return await self._review_and_discover()
                
            else:
                return {"action": "idle", "status": "no specific action required"}
                
        except Exception as e:
            self.logger.error(f"Error in research action: {e}")
            return {"action": "error", "error": str(e)}
    
    async def _search_related_memories(self, query: str) -> Dict[str, Any]:
        """Search for memories related to a query"""
        try:
            return await self.mcp_client.search_memories(
                query=query,
                agent_name=self.config.name,
                semantic=True
            )
        except Exception as e:
            self.logger.error(f"Memory search failed: {e}")
            return {"results": [], "count": 0}
    
    async def _conduct_research(self, query: str) -> Dict[str, Any]:
        """Conduct research on a new topic"""
        
        # Create a research session
        research_id = hashlib.md5(f"{query}{datetime.now()}".encode()).hexdigest()[:8]
        
        # Save initial research memory
        initial_memory = {
            "type": "research_start",
            "query": query,
            "research_id": research_id,
            "timestamp": datetime.now().isoformat(),
            "status": "initiated"
        }
        
        await self.mcp_client.save_memory(self.config.name, initial_memory)
        
        # Add to active research topics
        if query not in self.active_research_topics:
            self.active_research_topics.append(query)
        
        # Simulate research process (in real implementation, this would connect to external APIs)
        research_findings = await self._simulate_research(query)
        
        # Save research findings
        findings_memory = {
            "type": "research_findings",
            "query": query,
            "research_id": research_id,
            "findings": research_findings,
            "timestamp": datetime.now().isoformat(),
            "confidence": 0.85
        }
        
        await self.mcp_client.save_memory(self.config.name, findings_memory)
        
        return {
            "action": "research_completed",
            "query": query,
            "research_id": research_id,
            "findings_count": len(research_findings),
            "findings": research_findings[:3]  # Return first 3 findings
        }
    
    async def _simulate_research(self, query: str) -> List[Dict[str, Any]]:
        """Simulate research findings (replace with real research APIs)"""
        
        # This is a simulation - in a real implementation, you'd connect to:
        # - Web search APIs
        # - Academic databases
        # - Internal knowledge bases
        # - External APIs
        
        findings = [
            {
                "title": f"Analysis of {query}",
                "content": f"Comprehensive overview of {query} including key concepts, current trends, and implications.",
                "source": "simulated_research",
                "relevance": 0.9,
                "timestamp": datetime.now().isoformat()
            },
            {
                "title": f"Recent developments in {query}",
                "content": f"Latest updates and breakthrough discoveries related to {query}.",
                "source": "simulated_research",
                "relevance": 0.8,
                "timestamp": datetime.now().isoformat()
            },
            {
                "title": f"Future implications of {query}",
                "content": f"Potential future impact and applications of {query} across various domains.",
                "source": "simulated_research",
                "relevance": 0.7,
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        return findings
    
    async def _synthesize_memories(self, query: str) -> Dict[str, Any]:
        """Synthesize information from existing memories"""
        
        # Search for related memories
        memories = await self._search_related_memories(query)
        
        if not memories.get('results'):
            return {"action": "synthesis_failed", "reason": "no_related_memories"}
        
        # Group memories by type and relevance
        grouped_memories = {}
        for memory_result in memories['results']:
            memory = memory_result['memory']
            mem_type = memory.get('type', 'general')
            
            if mem_type not in grouped_memories:
                grouped_memories[mem_type] = []
            grouped_memories[mem_type].append(memory)
        
        # Create synthesis
        synthesis = {
            "type": "knowledge_synthesis",
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "source_memories": len(memories['results']),
            "synthesis": {
                "summary": f"Synthesized knowledge about {query} from {len(memories['results'])} related memories.",
                "key_insights": [],
                "knowledge_gaps": [],
                "grouped_findings": grouped_memories
            }
        }
        
        # Identify key insights (simplified logic)
        for mem_type, mems in grouped_memories.items():
            if len(mems) >= 2:
                synthesis["synthesis"]["key_insights"].append(
                    f"Strong knowledge base in {mem_type} with {len(mems)} related memories"
                )
        
        # Save synthesis
        await self.mcp_client.save_memory(self.config.name, synthesis)
        
        return {
            "action": "synthesis_completed",
            "query": query,
            "memories_analyzed": len(memories['results']),
            "synthesis": synthesis["synthesis"]
        }
    
    async def _perform_analysis(self, analysis_request: str) -> Dict[str, Any]:
        """Perform analysis based on existing knowledge"""
        
        # Search for relevant memories
        relevant_memories = await self._search_related_memories(analysis_request)
        
        # Create analysis
        analysis = {
            "type": "analysis",
            "request": analysis_request,
            "timestamp": datetime.now().isoformat(),
            "data_sources": len(relevant_memories.get('results', [])),
            "analysis_results": {
                "summary": f"Analysis of '{analysis_request}' based on available knowledge.",
                "confidence": 0.8,
                "recommendations": [],
                "supporting_evidence": []
            }
        }
        
        # Add supporting evidence from memories
        for result in relevant_memories.get('results', [])[:5]:  # Top 5 most relevant
            analysis["analysis_results"]["supporting_evidence"].append({
                "content": result['memory'].get('content', 'No content'),
                "relevance_score": result.get('score', 0),
                "source": result['memory'].get('type', 'unknown')
            })
        
        # Generate recommendations (simplified)
        if len(relevant_memories.get('results', [])) > 3:
            analysis["analysis_results"]["recommendations"].append(
                "Sufficient data available for comprehensive analysis"
            )
        else:
            analysis["analysis_results"]["recommendations"].append(
                "Additional research recommended for more robust analysis"
            )
        
        # Save analysis
        await self.mcp_client.save_memory(self.config.name, analysis)
        
        return {
            "action": "analysis_completed",
            "request": analysis_request,
            "data_sources": len(relevant_memories.get('results', [])),
            "analysis": analysis["analysis_results"]
        }
    
    async def _organize_knowledge(self) -> Dict[str, Any]:
        """Organize and cross-reference existing knowledge"""
        
        # Get all memories
        all_memories = await self.mcp_client.list_memories(
            agent_name=self.config.name,
            limit=100
        )
        
        # Organize by type
        organization = {}
        cross_references = []
        
        for memory in all_memories.get('memories', []):
            mem_type = memory.get('type', 'general')
            if mem_type not in organization:
                organization[mem_type] = []
            organization[mem_type].append(memory)
        
        # Create organization summary
        org_summary = {
            "type": "knowledge_organization",
            "timestamp": datetime.now().isoformat(),
            "total_memories": len(all_memories.get('memories', [])),
            "categories": {k: len(v) for k, v in organization.items()},
            "cross_references": cross_references
        }
        
        # Save organization
        await self.mcp_client.save_memory(self.config.name, org_summary)
        
        return {
            "action": "knowledge_organized",
            "total_memories": len(all_memories.get('memories', [])),
            "categories": org_summary["categories"]
        }
    
    async def _review_and_discover(self) -> Dict[str, Any]:
        """Review recent memories and discover patterns"""
        
        # Get recent memories
        recent_memories = await self.mcp_client.list_memories(
            agent_name=self.config.name,
            limit=20
        )
        
        # Look for patterns (simplified pattern detection)
        patterns = []
        memory_types = {}
        
        for memory in recent_memories.get('memories', []):
            mem_type = memory.get('type', 'general')
            memory_types[mem_type] = memory_types.get(mem_type, 0) + 1
        
        # Identify interesting patterns
        for mem_type, count in memory_types.items():
            if count >= 3:
                patterns.append(f"High activity in {mem_type} ({count} recent memories)")
        
        # Create discovery report
        discovery = {
            "type": "pattern_discovery",
            "timestamp": datetime.now().isoformat(),
            "patterns_found": patterns,
            "recent_activity": memory_types,
            "recommendations": []
        }
        
        # Add recommendations based on patterns
        if memory_types.get('research_findings', 0) > memory_types.get('analysis', 0):
            discovery["recommendations"].append(
                "Consider performing more analysis on recent research findings"
            )
        
        # Save discovery
        await self.mcp_client.save_memory(self.config.name, discovery)
        
        return {
            "action": "patterns_discovered",
            "patterns": patterns,
            "recent_activity": memory_types
        }

# Example usage and configuration
async def create_research_agent():
    """Create and configure a research agent"""
    
    config = AgentConfig(
        name="research-agent",
        role="Research and Analysis Specialist",
        goals=[
            "Conduct comprehensive research on assigned topics",
            "Maintain organized knowledge base",
            "Provide insightful analysis and synthesis",
            "Identify patterns and knowledge gaps"
        ],
        tools=["mcp_filesystem", "web_search", "document_analysis"],
        model="claude-3-opus-20240229",
        temperature=0.3,  # Lower temperature for more focused research
        zone="research"
    )
    
    agent = ResearchAgent(config)
    return agent

if __name__ == "__main__":
    async def test_research_agent():
        """Test the research agent"""
        agent = await create_research_agent()
        
        # Test research on AI
        context = {"research_query": "artificial intelligence in healthcare"}
        thought = await agent.think(context)
        print(f"Thought: {thought}")
        
        action_result = await agent.act(thought, context)
        print(f"Action: {action_result}")
        
        # Test analysis
        context = {"analysis_request": "trends in AI adoption"}
        thought = await agent.think(context)
        action_result = await agent.act(thought, context)
        print(f"Analysis: {action_result}")
    
    asyncio.run(test_research_agent())

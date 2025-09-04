"""
title: Advanced Multi-Agent LangGraph System
author: AI Assistant
description: Multi-agent system using LiteLLM with Claude, Gemini, and GPT-5
version: 1.0
licence: MIT
"""

import os
import json
from typing import Annotated, Literal
from typing_extensions import TypedDict

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langgraph.config import get_stream_writer

# Use LiteLLM proxy - no real API keys needed
os.environ["OPENAI_API_KEY"] = "litellm-master-key-2024"

def generate_custom_stream(type: Literal["think","normal"], content: str):
    content = "\n" + content + "\n"
    custom_stream_writer = get_stream_writer()
    return custom_stream_writer({type: content})

class State(TypedDict):
    messages: Annotated[list, add_messages]
    agent_type: str

# Configure multiple specialized LLMs via LiteLLM
reasoning_llm = ChatOpenAI(
    model="claude-sonnet-4-20250514",  # Claude for deep reasoning
    base_url="http://localhost:4001/v1",
    api_key="litellm-master-key-2024",
    temperature=0.3
)

response_llm = ChatOpenAI(
    model="gemini-2-5-flash",  # Gemini for fast, balanced responses
    base_url="http://localhost:4001/v1", 
    api_key="litellm-master-key-2024",
    temperature=0.7
)

critique_llm = ChatOpenAI(
    model="gpt-5",  # GPT-5 for critique and validation
    base_url="http://localhost:4001/v1",
    api_key="litellm-master-key-2024",
    temperature=1.0  # GPT-5 only supports temperature=1
)

def reasoning_agent(state: State):
    """🧠 Deep reasoning and analysis agent (Claude Sonnet 4)"""
    
    agent_type = state.get("agent_type", "general")
    
    # Specialized prompts based on agent type
    if agent_type == "code":
        system_prompt = """You are a code analysis specialist. Your job is to:
1. Analyze code structure, patterns, and architecture deeply
2. Identify potential bugs, security issues, and performance problems
3. Consider best practices, maintainability, and scalability
4. Evaluate code quality, readability, and documentation
5. Plan comprehensive code review and improvement strategies

Be thorough, technical, and precise in your analysis."""
    elif agent_type == "writing":
        system_prompt = """You are a writing and content specialist. Your job is to:
1. Analyze writing style, tone, and structure deeply
2. Identify areas for improvement in clarity, flow, and engagement
3. Consider audience, purpose, and context
4. Evaluate grammar, word choice, and narrative techniques
5. Plan strategies for enhancing content quality and impact

Be creative, insightful, and editorial in your analysis."""
    elif agent_type == "research":
        system_prompt = """You are a research and fact-checking specialist. Your job is to:
1. Analyze information sources and credibility deeply
2. Identify knowledge gaps and verification needs
3. Consider multiple perspectives and potential biases
4. Evaluate evidence quality and reliability
5. Plan comprehensive research and validation strategies

Be thorough, critical, and methodical in your analysis."""
    elif agent_type == "business":
        system_prompt = """You are a business strategy specialist. Your job is to:
1. Analyze market conditions, opportunities, and challenges deeply
2. Identify key stakeholders, risks, and success factors
3. Consider financial implications and resource requirements
4. Evaluate competitive landscape and strategic positioning
5. Plan actionable business strategies and recommendations

Be strategic, analytical, and commercially-focused in your analysis."""
    else:
        system_prompt = """You are a reasoning specialist. Your job is to:
1. Analyze the user's question/request deeply
2. Consider multiple perspectives and approaches
3. Think through potential challenges or edge cases
4. Identify the key information needed for a complete response
5. Plan the best strategy for addressing the user's needs

Be thorough, methodical, and insightful in your analysis."""
    
    reasoning_prompt = [
        {
            "role": "system", 
            "content": system_prompt
        }
    ] + state["messages"]
    
    reasoning_response = reasoning_llm.invoke(reasoning_prompt)
    
    # Stream the reasoning process
    generate_custom_stream("think", f"🧠 REASONING AGENT (Claude): {reasoning_response.content}")
    
    return {"reasoning": reasoning_response.content}

def response_agent(state: State):
    """💬 Response generation agent (Gemini 2.5 Flash)"""
    
    reasoning_context = state.get("reasoning", "")
    agent_type = state.get("agent_type", "general")
    
    # Specialized response prompts based on agent type
    if agent_type == "code":
        system_content = f"""You are a code review and development expert. Based on the analysis below, provide clear, actionable coding guidance.

REASONING ANALYSIS:
{reasoning_context}

Guidelines:
- Provide specific, technical recommendations
- Include code examples and best practices
- Explain technical concepts clearly
- Focus on practical implementation steps
- Address security, performance, and maintainability"""
    elif agent_type == "writing":
        system_content = f"""You are a writing and editing expert. Based on the analysis below, provide creative and practical writing guidance.

REASONING ANALYSIS:
{reasoning_context}

Guidelines:
- Offer specific writing techniques and improvements
- Provide examples of better phrasing or structure
- Focus on clarity, engagement, and impact
- Consider audience and purpose
- Include actionable editing suggestions"""
    elif agent_type == "research":
        system_content = f"""You are a research and information expert. Based on the analysis below, provide thorough, well-sourced information.

REASONING ANALYSIS:
{reasoning_context}

Guidelines:
- Provide comprehensive, factual information
- Include multiple perspectives and sources
- Identify areas for further investigation
- Present information clearly and objectively
- Highlight key findings and implications"""
    elif agent_type == "business":
        system_content = f"""You are a business strategy expert. Based on the analysis below, provide practical business guidance.

REASONING ANALYSIS:
{reasoning_context}

Guidelines:
- Offer actionable business recommendations
- Include financial and strategic considerations
- Focus on practical implementation
- Consider risks, opportunities, and ROI
- Provide clear next steps and timelines"""
    else:
        system_content = f"""You are a helpful assistant. Based on the reasoning analysis below, provide a clear, helpful, and engaging response to the user.

REASONING ANALYSIS:
{reasoning_context}

Guidelines:
- Be helpful, clear, and concise
- Use the reasoning insights to provide a comprehensive answer
- Maintain a friendly and professional tone
- Include specific examples or actionable advice when relevant"""
    
    response_prompt = [
        {
            "role": "system",
            "content": system_content
        }
    ] + state["messages"]
    
    response = response_llm.invoke(response_prompt)
    
    # Stream the response
    generate_custom_stream("normal", f"💬 RESPONSE AGENT (Gemini): {response.content}")
    
    return {
        "messages": [response],
        "draft_response": response.content
    }

def critique_agent(state: State):
    """🔍 Quality assurance and improvement agent (GPT-5)"""
    
    draft_response = state.get("draft_response", "")
    original_messages = state["messages"]
    
    critique_prompt = [
        {
            "role": "system",
            "content": f"""You are a quality assurance specialist. Review this response for:

ORIGINAL USER REQUEST:
{original_messages[-1].content if original_messages else 'No message'}

PROPOSED RESPONSE:
{draft_response}

Evaluate:
1. Accuracy and completeness
2. Clarity and helpfulness  
3. Appropriateness of tone
4. Missing important information
5. Potential improvements

If the response is excellent, simply say "✅ APPROVED - Response is excellent."
If improvements are needed, suggest specific enhancements."""
        }
    ]
    
    critique_response = critique_llm.invoke(critique_prompt)
    
    # Stream the critique
    generate_custom_stream("think", f"🔍 QUALITY ASSURANCE (GPT-5): {critique_response.content}")
    
    return {"critique": critique_response.content}

# Build the multi-agent workflow graph
graph_builder = StateGraph(State)

# Add agent nodes
graph_builder.add_node("reasoning_agent", reasoning_agent)
graph_builder.add_node("response_agent", response_agent) 
graph_builder.add_node("critique_agent", critique_agent)

# Define workflow: reasoning → response → critique
graph_builder.add_edge(START, "reasoning_agent")
graph_builder.add_edge("reasoning_agent", "response_agent")
graph_builder.add_edge("response_agent", "critique_agent")
graph_builder.add_edge("critique_agent", END)

# Compile the graph
graph = graph_builder.compile()

# FastAPI application
app = FastAPI(
    title="Multi-Agent LangGraph API",
    description="Advanced multi-agent system with Claude, Gemini, and GPT-5",
    version="1.0"
)

@app.get("/test")
async def test():
    return {"message": "Multi-Agent System Online! 🤖🧠💬🔍"}

@app.get("/agents")
async def agents_info():
    return {
        "agents": {
            "reasoning": {"model": "claude-sonnet-4-20250514", "role": "Deep analysis and planning"},
            "response": {"model": "gemini-2.5-flash", "role": "Response generation"},
            "critique": {"model": "gpt-5", "role": "Quality assurance"}
        }
    }

@app.post("/stream")  
async def stream(inputs: dict):
    async def event_stream():
        try:
            # Convert pipeline format to State format
            messages_data = inputs.get("messages", [])
            agent_type = inputs.get("agent_type", "general")  # Get requested agent type
            
            print(f"🎯 Agent type requested: {agent_type}")
            
            # Handle both formats: [[role, content], ...] or [{"role": role, "content": content}, ...]
            formatted_messages = []
            for msg in messages_data:
                if isinstance(msg, list) and len(msg) == 2:
                    # Pipeline format: [role, content]
                    formatted_messages.append({"role": msg[0], "content": msg[1]})
                elif isinstance(msg, dict) and "role" in msg and "content" in msg:
                    # Standard format: {"role": role, "content": content}
                    formatted_messages.append(msg)
            
            state_input = {"messages": formatted_messages, "agent_type": agent_type}
            
            # Stream start
            stream_start_msg = {
                'choices': [{
                    'delta': {}, 
                    'finish_reason': None
                }]
            }
            yield f"data: {json.dumps(stream_start_msg)}\n\n"
            
            # Process through multi-agent system
            async for event in graph.astream(input=state_input, stream_mode="custom"):
                print(f"Agent Event: {event}")
                
                think_content = event.get("think", None)
                normal_content = event.get("normal", None)
                
                if think_content:
                    think_msg = {
                        'choices': [{
                            'delta': {
                                'reasoning_content': think_content,
                            },
                            'finish_reason': None
                        }]
                    }
                    yield f"data: {json.dumps(think_msg)}\n\n"
                
                if normal_content:
                    normal_msg = {
                        'choices': [{
                            'delta': {
                                'content': normal_content,
                            },
                            'finish_reason': None
                        }]
                    }
                    yield f"data: {json.dumps(normal_msg)}\n\n"
            
            # Stream end
            stream_end_msg = {
                'choices': [{
                    'delta': {}, 
                    'finish_reason': 'stop'
                }]
            }
            yield f"data: {json.dumps(stream_end_msg)}\n\n"
            
        except Exception as e:
            print(f"Multi-agent system error: {e}")
            error_msg = {
                'choices': [{
                    'delta': {
                        'content': f"⚠️ Agent system error: {str(e)}"
                    },
                    'finish_reason': 'error'
                }]
            }
            yield f"data: {json.dumps(error_msg)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream", 
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Multi-Agent LangGraph System...")
    print("🧠 Reasoning Agent: Claude Sonnet 4")
    print("💬 Response Agent: Gemini 2.5 Flash") 
    print("🔍 Critique Agent: GPT-5")
    print("📡 Running on http://localhost:9000")
    
    uvicorn.run(app, host="0.0.0.0", port=9000)
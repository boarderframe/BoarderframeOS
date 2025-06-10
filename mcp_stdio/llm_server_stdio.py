#!/usr/bin/env python3
"""
MCP LLM Server - stdio transport wrapper
Wraps the HTTP-based LLM server for use with Claude CLI
"""

import asyncio
import json
import sys
import logging
import os
from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime

# Handle MCP import conflicts by temporarily modifying sys.path
import importlib
import importlib.util

# Save original sys.path
original_path = sys.path.copy()

# Remove current and parent directories to avoid local mcp module conflicts
current_dir = str(Path(__file__).parent)
parent_dir = str(Path(__file__).parent.parent)
sys.path = [p for p in sys.path if p not in (current_dir, parent_dir, '')]

# Clear any cached local mcp modules
local_mcp_modules = [name for name in sys.modules.keys() if name.startswith('mcp')]
for module_name in local_mcp_modules:
    del sys.modules[module_name]

try:
    # Import the real MCP package
    from mcp import types
    from mcp.server import Server, NotificationOptions
    from mcp.server.models import InitializationOptions
    import mcp.server.stdio
finally:
    # Restore original sys.path
    sys.path = original_path

# Configure logging to file to avoid interfering with stdio
log_file = Path(__file__).parent / "llm_stdio.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file)]
)
logger = logging.getLogger("llm_stdio")

server = Server("llm")

# Mock data for development
usage_stats = {
    "total_requests": 0,
    "total_tokens": 0,
    "total_cost": 0.0
}

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available LLM tools."""
    return [
        types.Tool(
            name="generate_text",
            description="Generate text using an LLM",
            inputSchema={
                "type": "object",
                "properties": {
                    "provider": {
                        "type": "string",
                        "description": "LLM provider: claude, local, openai",
                        "enum": ["claude", "local", "openai"]
                    },
                    "model": {
                        "type": "string",
                        "description": "Model name"
                    },
                    "messages": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {
                                    "type": "string",
                                    "enum": ["user", "assistant", "system"]
                                },
                                "content": {
                                    "type": "string"
                                }
                            },
                            "required": ["role", "content"]
                        },
                        "description": "Conversation messages"
                    },
                    "temperature": {
                        "type": "number",
                        "description": "Sampling temperature",
                        "default": 0.7,
                        "minimum": 0,
                        "maximum": 2
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "Maximum tokens to generate",
                        "default": 4000,
                        "minimum": 1,
                        "maximum": 8000
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "Requesting agent ID (optional)"
                    },
                    "system_prompt": {
                        "type": "string",
                        "description": "System prompt override (optional)"
                    }
                },
                "required": ["provider", "model", "messages"]
            }
        ),
        types.Tool(
            name="list_models",
            description="List available models across all providers",
            inputSchema={
                "type": "object",
                "properties": {
                    "provider": {
                        "type": "string",
                        "description": "Filter by provider (optional)"
                    }
                }
            }
        ),
        types.Tool(
            name="agent_chat",
            description="Chat endpoint specifically for agent interactions",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Agent identifier"
                    },
                    "provider": {
                        "type": "string",
                        "description": "LLM provider",
                        "default": "claude"
                    },
                    "model": {
                        "type": "string",
                        "description": "Model name",
                        "default": "claude-3-sonnet-20240229"
                    },
                    "messages": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {"type": "string"},
                                "content": {"type": "string"}
                            }
                        },
                        "description": "Conversation messages"
                    },
                    "temperature": {
                        "type": "number",
                        "default": 0.7
                    },
                    "max_tokens": {
                        "type": "integer",
                        "default": 4000
                    }
                },
                "required": ["agent_id", "messages"]
            }
        ),
        types.Tool(
            name="get_llm_stats",
            description="Get LLM usage statistics",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls."""
    try:
        if name == "generate_text":
            return await generate_text(arguments)
        elif name == "list_models":
            return await list_models(arguments)
        elif name == "agent_chat":
            return await agent_chat(arguments)
        elif name == "get_llm_stats":
            return await get_llm_stats()
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

async def generate_text(args: Dict[str, Any]) -> List[types.TextContent]:
    """Generate text using specified LLM provider."""
    try:
        provider = args["provider"]
        model = args["model"]
        messages = args["messages"]
        temperature = args.get("temperature", 0.7)
        max_tokens = args.get("max_tokens", 4000)
        agent_id = args.get("agent_id")
        system_prompt = args.get("system_prompt")
        
        start_time = datetime.now()
        
        # Mock LLM response for development
        # In production, this would call the actual LLM APIs
        mock_content = f"Mock LLM response from {provider}/{model}. Last message was: '{messages[-1]['content'] if messages else 'No messages'}'"
        
        if system_prompt:
            mock_content = f"[System: {system_prompt}] {mock_content}"
        
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        end_time = datetime.now()
        response_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Mock token usage and cost calculation
        estimated_tokens = len(mock_content.split()) * 2  # Rough estimate
        mock_cost = estimated_tokens * 0.000003 if provider == "claude" else 0.0  # Mock cost
        
        # Update usage stats
        usage_stats["total_requests"] += 1
        usage_stats["total_tokens"] += estimated_tokens
        usage_stats["total_cost"] += mock_cost
        
        result = {
            "success": True,
            "content": mock_content,
            "model": model,
            "provider": provider,
            "tokens_used": estimated_tokens,
            "cost_estimate": mock_cost,
            "response_time_ms": response_time_ms,
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # Log the request
        logger.info(f"LLM request: {agent_id or 'unknown'} -> {provider}/{model} "
                   f"({estimated_tokens} tokens, {response_time_ms}ms)")
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error generating text: {str(e)}")]

async def list_models(args: Dict[str, Any]) -> List[types.TextContent]:
    """List available models across all providers."""
    try:
        provider_filter = args.get("provider")
        
        # Mock model configurations
        models = [
            {
                "name": "claude-3-opus-20240229",
                "provider": "claude",
                "context_length": 200000,
                "cost_per_token": 0.000015,
                "available": bool(os.getenv("ANTHROPIC_API_KEY"))
            },
            {
                "name": "claude-3-sonnet-20240229",
                "provider": "claude",
                "context_length": 200000,
                "cost_per_token": 0.000003,
                "available": bool(os.getenv("ANTHROPIC_API_KEY"))
            },
            {
                "name": "claude-3-haiku-20240307",
                "provider": "claude",
                "context_length": 200000,
                "cost_per_token": 0.00000025,
                "available": bool(os.getenv("ANTHROPIC_API_KEY"))
            },
            {
                "name": "llama-maverick-30b",
                "provider": "local",
                "context_length": 8192,
                "cost_per_token": 0.0,
                "available": False  # Assume local server not running
            },
            {
                "name": "mistral-7b",
                "provider": "local",
                "context_length": 8192,
                "cost_per_token": 0.0,
                "available": False  # Assume local server not running
            }
        ]
        
        # Apply provider filter if specified
        if provider_filter:
            models = [m for m in models if m["provider"] == provider_filter]
        
        result = {
            "success": True,
            "models": models,
            "count": len(models),
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error listing models: {str(e)}")]

async def agent_chat(args: Dict[str, Any]) -> List[types.TextContent]:
    """Chat endpoint specifically for agent interactions."""
    try:
        agent_id = args["agent_id"]
        provider = args.get("provider", "claude")
        model = args.get("model", "claude-3-sonnet-20240229")
        messages = args["messages"]
        temperature = args.get("temperature", 0.7)
        max_tokens = args.get("max_tokens", 4000)
        
        # Add agent-specific system prompt if not already present
        system_messages = [m for m in messages if m["role"] == "system"]
        if not system_messages:
            system_prompt = f"You are {agent_id}, an AI agent in the BoarderframeOS system."
        else:
            system_prompt = None
        
        # Create request for generate_text
        request = {
            "provider": provider,
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "agent_id": agent_id,
            "system_prompt": system_prompt
        }
        
        return await generate_text(request)
        
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error in agent chat: {str(e)}")]

async def get_llm_stats() -> List[types.TextContent]:
    """Get LLM usage statistics."""
    try:
        result = {
            "success": True,
            "stats": {
                "total_requests": usage_stats["total_requests"],
                "total_tokens": usage_stats["total_tokens"],
                "total_cost": usage_stats["total_cost"],
                "avg_tokens_per_request": usage_stats["total_tokens"] / max(usage_stats["total_requests"], 1),
                "avg_cost_per_request": usage_stats["total_cost"] / max(usage_stats["total_requests"], 1)
            },
            "providers": {
                "claude": {
                    "available": bool(os.getenv("ANTHROPIC_API_KEY")),
                    "api_key_configured": bool(os.getenv("ANTHROPIC_API_KEY"))
                },
                "local": {
                    "available": False,  # Mock - would check local server
                    "endpoint": "http://localhost:8080"
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error getting LLM stats: {str(e)}")]

async def main():
    """Main entry point."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="llm",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
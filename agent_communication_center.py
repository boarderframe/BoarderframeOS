#!/usr/bin/env python3
"""
BoarderframeOS Agent Communication Center (ACC)
Dedicated service for Claude-powered agent communications
"""

import asyncio
import json
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Import enhanced components
from core.claude_integration import get_claude_integration
from core.message_bus import AgentMessage, MessagePriority, MessageType, message_bus

# Try to import Agent Cortex components (optional)
try:
    from core.agent_cortex import (
        AgentRequest,
        ModelTier,
        SelectionStrategy,
        get_agent_cortex_instance,
    )

    AGENT_CORTEX_AVAILABLE = True
    print("🧠 Agent Cortex components imported successfully")
except ImportError as e:
    print(f"⚠️ Agent Cortex not available: {e}")
    print("   ACC will use direct Claude integration as fallback")
    AGENT_CORTEX_AVAILABLE = False
    # Define dummy classes for compatibility
    get_agent_cortex_instance = None
    AgentRequest = None
    ModelTier = None
    SelectionStrategy = None

# Agent orchestrator is a singleton instance, not importable directly
# from core.agent_orchestrator import agent_orchestrator

# Import metrics if available
try:
    from core.hq_metrics_integration import HQMetricsIntegration

    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False


class ChatMessage(BaseModel):
    agent: str
    message: str
    include_voice: bool = False


class AgentCommunicationCenter:
    """Agent Communication Center (ACC) with Agent Cortex integration"""

    def __init__(self):
        self.app = FastAPI(title="BoarderframeOS Agent Communication Center")
        self.claude = get_claude_integration()
        self.agent_cortex = None  # Will be initialized async
        self.active_connections: List[WebSocket] = []
        self.chat_sessions: Dict[str, List[Dict]] = {}
        self.setup_routes()

        # Track enhanced agents
        self.enhanced_agents = ["solomon", "david", "adam", "eve", "bezalel"]

        # Agent tier mapping for Agent Cortex (if available)
        if AGENT_CORTEX_AVAILABLE and ModelTier:
            self.agent_tiers = {
                "solomon": ModelTier.EXECUTIVE,
                "david": ModelTier.EXECUTIVE,
                "adam": ModelTier.SPECIALIST,
                "eve": ModelTier.SPECIALIST,
                "bezalel": ModelTier.SPECIALIST,
            }
        else:
            # Fallback tier mapping using strings
            self.agent_tiers = {
                "solomon": "executive",
                "david": "executive",
                "adam": "specialist",
                "eve": "specialist",
                "bezalel": "specialist",
            }

    async def initialize(self):
        """Initialize Agent Cortex connection"""
        if AGENT_CORTEX_AVAILABLE and get_agent_cortex_instance:
            try:
                self.agent_cortex = await get_agent_cortex_instance()
                print("🧠 ACC: Agent Cortex integration initialized")
            except Exception as e:
                print(f"⚠️ ACC: Could not initialize Agent Cortex: {e}")
                print("   Falling back to direct Claude integration")
        else:
            print("ℹ️ ACC: Agent Cortex not available, using direct Claude integration")

    def setup_routes(self):
        """Set up FastAPI routes"""

        @self.app.get("/", response_class=HTMLResponse)
        async def home():
            return self.generate_enhanced_ui()

        @self.app.post("/api/chat")
        async def chat(message: ChatMessage):
            """Handle chat with enhanced agents using Agent Cortex"""
            try:
                if message.agent.lower() not in self.enhanced_agents:
                    return JSONResponse(
                        {
                            "success": False,
                            "error": f"Agent {message.agent} not available in enhanced mode",
                        }
                    )

                # Use Agent Cortex for intelligent model selection if available
                if self.agent_cortex:
                    response = await self.get_cortex_response(message)
                else:
                    # Fallback to direct Claude integration
                    response = await self.claude.get_response(
                        message.agent.lower(), message.message
                    )

                # Store in chat history
                session_id = "default"
                if session_id not in self.chat_sessions:
                    self.chat_sessions[session_id] = []

                self.chat_sessions[session_id].append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "agent": message.agent,
                        "message": message.message,
                        "response": response,
                        "used_cortex": bool(self.agent_cortex),
                    }
                )

                return JSONResponse(
                    {
                        "success": True,
                        "agent": message.agent,
                        "response": response,
                        "voice_available": message.include_voice,
                        "cortex_optimized": bool(self.agent_cortex),
                    }
                )

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket for real-time updates"""
            await websocket.accept()
            self.active_connections.append(websocket)

            try:
                while True:
                    data = await websocket.receive_text()
                    # Handle WebSocket messages
                    await self.handle_websocket_message(websocket, data)
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)

        @self.app.get("/api/agents/status")
        async def agents_status():
            """Get enhanced agents status"""
            status = {}

            for agent_name in self.enhanced_agents:
                try:
                    # Check if agent has recent activity
                    agent_info = self.claude.get_agent_info(agent_name)
                    status[agent_name] = {
                        "online": True,
                        "enhanced": True,
                        "memory_size": agent_info.get("memory_size", 0),
                        "role": agent_info.get("role", "Unknown"),
                        "claude_enabled": True,
                        "voice_enabled": True,
                    }
                except:
                    status[agent_name] = {
                        "online": False,
                        "enhanced": True,
                        "error": "Unable to reach agent",
                    }

            return JSONResponse(status)

        @self.app.get("/api/metrics")
        async def get_metrics():
            """Get system metrics"""
            if METRICS_AVAILABLE:
                metrics = HQMetricsIntegration()
                return JSONResponse(await metrics.get_all_metrics())
            else:
                return JSONResponse({"error": "Metrics not available"})

        @self.app.get("/health")
        async def health():
            """Health check endpoint for monitoring"""
            return JSONResponse(
                {
                    "status": "healthy",
                    "service": "agent_communication_center",
                    "port": 8890,
                    "enhanced_agents": len(self.enhanced_agents),
                    "cortex_available": bool(self.agent_cortex),
                    "claude_integration": True,
                    "active_connections": len(self.active_connections),
                    "timestamp": datetime.now().isoformat(),
                }
            )

    async def handle_websocket_message(self, websocket: WebSocket, message: str):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)

            if data.get("type") == "chat":
                # Handle chat through WebSocket
                agent = data.get("agent")
                user_message = data.get("message")

                if agent and user_message:
                    response = await self.claude.get_response(
                        agent.lower(), user_message
                    )

                    await websocket.send_json(
                        {"type": "chat_response", "agent": agent, "response": response}
                    )

            elif data.get("type") == "multi_agent_chat":
                # Handle multi-agent conversation
                agents = data.get("agents", [])
                topic = data.get("topic", "")

                if agents and topic:
                    conversation = await self.claude.multi_agent_conversation(
                        agents=[a.lower() for a in agents], topic=topic, rounds=1
                    )

                    for exchange in conversation:
                        await websocket.send_json(
                            {
                                "type": "multi_agent_response",
                                "agent": exchange["agent"],
                                "message": exchange["message"],
                            }
                        )
                        await asyncio.sleep(0.5)  # Pace the responses

        except Exception as e:
            await websocket.send_json({"type": "error", "message": str(e)})

    async def get_cortex_response(self, message: ChatMessage) -> str:
        """Get response using Agent Cortex for intelligent model selection"""
        try:
            # Create Agent Cortex request
            agent_tier = self.agent_tiers.get(
                message.agent.lower(), ModelTier.SPECIALIST
            )

            # Estimate complexity based on message length and content
            complexity = min(10, max(1, len(message.message) // 50 + 3))
            if any(
                word in message.message.lower()
                for word in ["complex", "analyze", "strategic", "detailed"]
            ):
                complexity = min(10, complexity + 2)

            cortex_request = AgentRequest(
                agent_name=message.agent.lower(),
                task_type="user_chat",
                context={
                    "message": message.message,
                    "interface": "ACC",
                    "session_type": "enhanced_agent_chat",
                },
                complexity=complexity,
                urgency=5,  # Normal priority for chat
                quality_requirements=0.9 if agent_tier == ModelTier.EXECUTIVE else 0.85,
                max_cost=0.05,  # Reasonable limit for chat responses
                conversation_id=f"acc_{uuid.uuid4()}",
            )

            # Get optimal model selection from Agent Cortex
            cortex_response = await self.agent_cortex.process_agent_request(
                cortex_request
            )

            # Use the selected LLM client to get response
            llm_client = cortex_response.llm

            # Get agent personality from Claude integration
            personality = self.claude.personalities.get(message.agent.lower())
            if personality:
                # Use Agent Cortex selected model with personality
                prompt = f"{personality.system_prompt}\n\nUser: {message.message}\n\nAssistant:"
                response_text = await llm_client.generate(
                    prompt, temperature=personality.temperature, max_tokens=4096
                )
            else:
                # Direct response without personality
                response_text = await llm_client.generate(
                    message.message, max_tokens=4096
                )

            # Report performance back to Agent Cortex for learning
            # (This would be done after measuring actual performance)

            print(
                f"🧠 ACC: Used {cortex_response.selection.selected_model} for {message.agent}"
            )
            return response_text

        except Exception as e:
            print(f"❌ ACC Cortex error: {e}")
            # Fallback to direct Claude integration
            return await self.claude.get_response(
                message.agent.lower(), message.message
            )

    def generate_enhanced_ui(self) -> str:
        """Generate the enhanced UI HTML"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BoarderframeOS Agent Communication Center (ACC)</title>
    <style>
        :root {
            --primary: #4fc3f7;
            --secondary: #81c784;
            --accent: #ffb74d;
            --bg-dark: #0f0f23;
            --bg-medium: #1a1a3e;
            --text-light: #ffffff;
            --text-dim: #aaaaaa;
            --border: rgba(255, 255, 255, 0.1);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, var(--bg-dark) 0%, var(--bg-medium) 100%);
            color: var(--text-light);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        .header {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid var(--border);
            padding: 20px;
            text-align: center;
        }

        .header h1 {
            color: var(--primary);
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 0 0 20px rgba(79, 195, 247, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
        }

        .acc-badge {
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.4em;
            font-weight: normal;
        }

        .subtitle {
            color: var(--secondary);
            font-size: 1.2em;
        }

        .main-container {
            flex: 1;
            display: flex;
            gap: 20px;
            padding: 20px;
            max-width: 1400px;
            margin: 0 auto;
            width: 100%;
        }

        .agents-panel {
            width: 300px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
        }

        .agents-panel h2 {
            color: var(--primary);
            margin-bottom: 20px;
            font-size: 1.5em;
        }

        .agent-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .agent-card:hover {
            transform: translateY(-2px);
            border-color: var(--primary);
            box-shadow: 0 5px 20px rgba(79, 195, 247, 0.3);
        }

        .agent-card.selected {
            background: rgba(79, 195, 247, 0.2);
            border-color: var(--primary);
        }

        .agent-name {
            font-size: 1.2em;
            color: var(--primary);
            margin-bottom: 5px;
        }

        .agent-role {
            color: var(--text-dim);
            font-size: 0.9em;
            margin-bottom: 10px;
        }

        .agent-status {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.85em;
        }

        .status-indicator {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--secondary);
            box-shadow: 0 0 10px var(--secondary);
        }

        .chat-container {
            flex: 1;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            backdrop-filter: blur(10px);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .chat-header {
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-bottom: 1px solid var(--border);
        }

        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .message {
            max-width: 70%;
            word-wrap: break-word;
        }

        .message.user {
            align-self: flex-end;
            background: rgba(79, 195, 247, 0.2);
            border: 1px solid var(--primary);
            border-radius: 15px 15px 0 15px;
            padding: 12px 18px;
        }

        .message.agent {
            align-self: flex-start;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border);
            border-radius: 15px 15px 15px 0;
            padding: 12px 18px;
        }

        .message-header {
            font-size: 0.85em;
            color: var(--text-dim);
            margin-bottom: 5px;
        }

        .message-content {
            line-height: 1.5;
        }

        .chat-input {
            padding: 20px;
            border-top: 1px solid var(--border);
            background: rgba(255, 255, 255, 0.05);
        }

        .input-group {
            display: flex;
            gap: 10px;
            align-items: flex-end;
        }

        .chat-textarea {
            flex: 1;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 12px;
            color: var(--text-light);
            resize: none;
            font-family: inherit;
            font-size: 14px;
            min-height: 50px;
            max-height: 150px;
        }

        .chat-textarea:focus {
            outline: none;
            border-color: var(--primary);
        }

        .send-button {
            background: linear-gradient(135deg, var(--primary) 0%, #29b6f6 100%);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 12px 24px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s ease;
        }

        .send-button:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 20px rgba(79, 195, 247, 0.4);
        }

        .send-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }

        .feature-badges {
            display: flex;
            gap: 10px;
            margin-top: 10px;
            flex-wrap: wrap;
        }

        .badge {
            background: rgba(255, 255, 255, 0.1);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75em;
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .badge.claude {
            background: rgba(79, 195, 247, 0.2);
            border: 1px solid var(--primary);
        }

        .badge.voice {
            background: rgba(129, 199, 132, 0.2);
            border: 1px solid var(--secondary);
        }

        .multi-agent-toggle {
            margin-top: 20px;
            padding: 10px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            text-align: center;
        }

        .toggle-button {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid var(--border);
            color: var(--text-light);
            padding: 8px 16px;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .toggle-button:hover {
            background: rgba(255, 255, 255, 0.2);
            border-color: var(--primary);
        }

        .toggle-button.active {
            background: rgba(79, 195, 247, 0.2);
            border-color: var(--primary);
        }

        /* Loading animation */
        .typing-indicator {
            display: flex;
            gap: 4px;
            padding: 12px 18px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border);
            border-radius: 15px;
            width: fit-content;
        }

        .typing-dot {
            width: 8px;
            height: 8px;
            background: var(--text-dim);
            border-radius: 50%;
            animation: typing 1.4s ease-in-out infinite;
        }

        .typing-dot:nth-child(2) {
            animation-delay: 0.2s;
        }

        .typing-dot:nth-child(3) {
            animation-delay: 0.4s;
        }

        @keyframes typing {
            0%, 60%, 100% {
                opacity: 0.3;
                transform: translateY(0);
            }
            30% {
                opacity: 1;
                transform: translateY(-10px);
            }
        }

        /* Voice input button */
        .voice-button {
            background: rgba(129, 199, 132, 0.2);
            border: 1px solid var(--secondary);
            color: var(--secondary);
            border-radius: 10px;
            padding: 12px;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .voice-button:hover {
            background: rgba(129, 199, 132, 0.3);
            transform: scale(1.05);
        }

        .voice-button.recording {
            background: rgba(255, 183, 77, 0.3);
            border-color: var(--accent);
            color: var(--accent);
            animation: pulse 1s ease-in-out infinite;
        }

        @keyframes pulse {
            0% {
                box-shadow: 0 0 0 0 rgba(255, 183, 77, 0.4);
            }
            70% {
                box-shadow: 0 0 0 10px rgba(255, 183, 77, 0);
            }
            100% {
                box-shadow: 0 0 0 0 rgba(255, 183, 77, 0);
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>
            🔗 Agent Communication Center
            <span class="acc-badge">ACC</span>
        </h1>
        <p class="subtitle">Claude-3 Powered Agent Communications Hub</p>
    </div>

    <div class="main-container">
        <div class="agents-panel">
            <h2>Enhanced Agents</h2>

            <div class="agent-card" data-agent="solomon" onclick="selectAgent('solomon')">
                <div class="agent-name">Solomon</div>
                <div class="agent-role">Digital Twin & Chief of Staff</div>
                <div class="agent-status">
                    <span class="status-indicator"></span>
                    <span>Online</span>
                </div>
                <div class="feature-badges">
                    <span class="badge claude">🧠 Claude-3</span>
                    <span class="badge voice">🎤 Voice</span>
                </div>
            </div>

            <div class="agent-card" data-agent="david" onclick="selectAgent('david')">
                <div class="agent-name">David</div>
                <div class="agent-role">Chief Executive Officer</div>
                <div class="agent-status">
                    <span class="status-indicator"></span>
                    <span>Online</span>
                </div>
                <div class="feature-badges">
                    <span class="badge claude">🧠 Claude-3</span>
                    <span class="badge voice">🎤 Voice</span>
                </div>
            </div>

            <div class="agent-card" data-agent="adam" onclick="selectAgent('adam')">
                <div class="agent-name">Adam</div>
                <div class="agent-role">The Creator - Agent Factory</div>
                <div class="agent-status">
                    <span class="status-indicator"></span>
                    <span>Online</span>
                </div>
                <div class="feature-badges">
                    <span class="badge claude">🧠 Claude-3</span>
                    <span class="badge voice">🎤 Voice</span>
                </div>
            </div>

            <div class="agent-card" data-agent="eve" onclick="selectAgent('eve')">
                <div class="agent-name">Eve</div>
                <div class="agent-role">The Evolver</div>
                <div class="agent-status">
                    <span class="status-indicator"></span>
                    <span>Online</span>
                </div>
                <div class="feature-badges">
                    <span class="badge claude">🧠 Claude-3</span>
                    <span class="badge voice">🎤 Voice</span>
                </div>
            </div>

            <div class="agent-card" data-agent="bezalel" onclick="selectAgent('bezalel')">
                <div class="agent-name">Bezalel</div>
                <div class="agent-role">Master Programmer</div>
                <div class="agent-status">
                    <span class="status-indicator"></span>
                    <span>Online</span>
                </div>
                <div class="feature-badges">
                    <span class="badge claude">🧠 Claude-3</span>
                    <span class="badge voice">🎤 Voice</span>
                </div>
            </div>

            <div class="multi-agent-toggle">
                <button class="toggle-button" onclick="toggleMultiAgent()">
                    Multi-Agent Mode
                </button>
            </div>
        </div>

        <div class="chat-container">
            <div class="chat-header">
                <h3 id="chat-title">Select an agent to start chatting</h3>
                <p id="chat-subtitle">Enhanced with Claude-3 Opus intelligence</p>
            </div>

            <div class="chat-messages" id="messages">
                <!-- Messages will appear here -->
            </div>

            <div class="chat-input">
                <div class="input-group">
                    <button class="voice-button" onclick="toggleVoiceInput()" title="Voice Input">
                        🎤
                    </button>
                    <textarea
                        class="chat-textarea"
                        id="messageInput"
                        placeholder="Type your message..."
                        onkeypress="handleKeyPress(event)"
                    ></textarea>
                    <button class="send-button" onclick="sendMessage()" id="sendButton">
                        Send
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let selectedAgent = null;
        let selectedAgents = [];
        let multiAgentMode = false;
        let ws = null;
        let isRecording = false;

        // Initialize WebSocket
        function initWebSocket() {
            const wsUrl = `ws://${window.location.host}/ws`;
            ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                console.log('WebSocket connected');
                updateAgentStatus();
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            ws.onclose = () => {
                console.log('WebSocket disconnected');
                // Attempt to reconnect after 3 seconds
                setTimeout(initWebSocket, 3000);
            };
        }

        function handleWebSocketMessage(data) {
            if (data.type === 'chat_response') {
                addMessage(data.agent, data.response, 'agent');
            } else if (data.type === 'multi_agent_response') {
                addMessage(data.agent, data.message, 'agent');
            } else if (data.type === 'error') {
                console.error('WebSocket error:', data.message);
            }
        }

        function selectAgent(agentName) {
            if (multiAgentMode) {
                // Multi-agent selection
                const card = document.querySelector(`[data-agent="${agentName}"]`);
                if (selectedAgents.includes(agentName)) {
                    selectedAgents = selectedAgents.filter(a => a !== agentName);
                    card.classList.remove('selected');
                } else {
                    selectedAgents.push(agentName);
                    card.classList.add('selected');
                }
                updateChatHeader();
            } else {
                // Single agent selection
                document.querySelectorAll('.agent-card').forEach(card => {
                    card.classList.remove('selected');
                });

                const card = document.querySelector(`[data-agent="${agentName}"]`);
                card.classList.add('selected');

                selectedAgent = agentName;
                selectedAgents = [agentName];
                updateChatHeader();
            }
        }

        function toggleMultiAgent() {
            multiAgentMode = !multiAgentMode;
            const button = document.querySelector('.toggle-button');

            if (multiAgentMode) {
                button.classList.add('active');
                button.textContent = 'Multi-Agent Mode ✓';
            } else {
                button.classList.remove('active');
                button.textContent = 'Multi-Agent Mode';
                // Clear multi-selection
                selectedAgents = selectedAgent ? [selectedAgent] : [];
                updateAgentSelection();
            }
        }

        function updateAgentSelection() {
            document.querySelectorAll('.agent-card').forEach(card => {
                const agentName = card.getAttribute('data-agent');
                if (selectedAgents.includes(agentName)) {
                    card.classList.add('selected');
                } else {
                    card.classList.remove('selected');
                }
            });
        }

        function updateChatHeader() {
            const title = document.getElementById('chat-title');
            const subtitle = document.getElementById('chat-subtitle');

            if (selectedAgents.length === 0) {
                title.textContent = 'Select an agent to start chatting';
                subtitle.textContent = 'Enhanced with Claude-3 Opus intelligence';
            } else if (selectedAgents.length === 1) {
                const agent = selectedAgents[0];
                const agentNames = {
                    solomon: 'Solomon - Digital Twin',
                    david: 'David - CEO',
                    adam: 'Adam - The Creator',
                    eve: 'Eve - The Evolver',
                    bezalel: 'Bezalel - Master Programmer'
                };
                title.textContent = `Chat with ${agentNames[agent] || agent}`;
                subtitle.textContent = 'Powered by Claude-3 Opus';
            } else {
                title.textContent = `Multi-Agent Chat (${selectedAgents.length} agents)`;
                subtitle.textContent = selectedAgents.map(a => a.charAt(0).toUpperCase() + a.slice(1)).join(', ');
            }
        }

        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();

            if (!message || selectedAgents.length === 0) return;

            // Disable input while sending
            input.disabled = true;
            document.getElementById('sendButton').disabled = true;

            // Add user message
            addMessage('You', message, 'user');

            // Clear input
            input.value = '';

            try {
                if (multiAgentMode && selectedAgents.length > 1) {
                    // Multi-agent conversation via WebSocket
                    ws.send(JSON.stringify({
                        type: 'multi_agent_chat',
                        agents: selectedAgents,
                        topic: message
                    }));
                } else {
                    // Single agent chat
                    for (const agent of selectedAgents) {
                        // Show typing indicator
                        showTypingIndicator(agent);

                        const response = await fetch('/api/chat', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                agent: agent,
                                message: message,
                                include_voice: false
                            })
                        });

                        const data = await response.json();

                        // Remove typing indicator
                        hideTypingIndicator();

                        if (data.success) {
                            addMessage(agent, data.response, 'agent');
                        } else {
                            addMessage('System', `Error: ${data.error}`, 'agent');
                        }
                    }
                }
            } catch (error) {
                hideTypingIndicator();
                addMessage('System', `Error: ${error.message}`, 'agent');
            } finally {
                // Re-enable input
                input.disabled = false;
                document.getElementById('sendButton').disabled = false;
                input.focus();
            }
        }

        function addMessage(sender, content, type) {
            const messagesDiv = document.getElementById('messages');

            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;

            const headerDiv = document.createElement('div');
            headerDiv.className = 'message-header';
            headerDiv.textContent = sender.charAt(0).toUpperCase() + sender.slice(1);

            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = content;

            messageDiv.appendChild(headerDiv);
            messageDiv.appendChild(contentDiv);

            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function showTypingIndicator(agent) {
            const messagesDiv = document.getElementById('messages');

            const typingDiv = document.createElement('div');
            typingDiv.className = 'typing-indicator';
            typingDiv.id = 'typing-indicator';

            for (let i = 0; i < 3; i++) {
                const dot = document.createElement('div');
                dot.className = 'typing-dot';
                typingDiv.appendChild(dot);
            }

            messagesDiv.appendChild(typingDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function hideTypingIndicator() {
            const indicator = document.getElementById('typing-indicator');
            if (indicator) {
                indicator.remove();
            }
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }

        function toggleVoiceInput() {
            const button = document.querySelector('.voice-button');

            if (!isRecording) {
                // Start recording
                isRecording = true;
                button.classList.add('recording');
                // TODO: Implement actual voice recording
                addMessage('System', 'Voice input coming soon! Install voice dependencies with: python install_voice_deps.py', 'agent');
            } else {
                // Stop recording
                isRecording = false;
                button.classList.remove('recording');
            }
        }

        async function updateAgentStatus() {
            try {
                const response = await fetch('/api/agents/status');
                const status = await response.json();

                // Update UI based on status
                Object.keys(status).forEach(agent => {
                    const card = document.querySelector(`[data-agent="${agent}"]`);
                    if (card) {
                        const indicator = card.querySelector('.status-indicator');
                        const statusText = card.querySelector('.agent-status span:last-child');

                        if (status[agent].online) {
                            indicator.style.background = '#81c784';
                            indicator.style.boxShadow = '0 0 10px #81c784';
                            statusText.textContent = 'Online';
                        } else {
                            indicator.style.background = '#f44336';
                            indicator.style.boxShadow = '0 0 10px #f44336';
                            statusText.textContent = 'Offline';
                        }
                    }
                });
            } catch (error) {
                console.error('Failed to update agent status:', error);
            }
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            // initWebSocket();
            updateAgentStatus();

            // Auto-select Solomon
            selectAgent('solomon');

            // Update status every 30 seconds
            setInterval(updateAgentStatus, 30000);
        });
    </script>
</body>
</html>
        """


# Create FastAPI app instance (for uvicorn compatibility)
acc = AgentCommunicationCenter()
app = acc.app


def sync_main():
    """Run the Agent Communication Center with Agent Cortex integration"""
    print("=" * 60)
    print("🔗 BoarderframeOS Agent Communication Center (ACC)")
    print("=" * 60)
    print("🧠 Claude-3 API integration active")
    print("🧠 Agent Cortex intelligent model selection")
    print("🎤 Voice capabilities available")
    print("💬 Multi-agent conversations enabled")
    print("🌐 Access at: http://localhost:8890")
    print("\n📌 ACC is a core BoarderframeOS service")
    print("📌 Access from Corporate HQ chat button")
    print("=" * 60)

    # Initialize Agent Cortex integration in background
    async def init_cortex():
        await acc.initialize()

    # Run initialization
    asyncio.run(init_cortex())

    uvicorn.run(app, host="0.0.0.0", port=8890, log_level="info")


if __name__ == "__main__":
    sync_main()

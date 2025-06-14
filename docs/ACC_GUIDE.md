# Agent Communication Center (ACC) Guide

## Overview

The Agent Communication Center (ACC) is a core BoarderframeOS service that provides a dedicated hub for communicating with Claude-3 powered AI agents. It serves as the primary interface for agent interactions, featuring real-time chat, voice capabilities, and multi-agent conversations.

## Access Points

- **Direct URL**: http://localhost:8890
- **From Corporate HQ**: Click the floating chat button (bottom-right corner)
- **Command Line**: `python launch_acc.py`
- **System Startup**: Automatically starts with `python startup.py`

## Key Features

### 1. Claude-3 Integration
- All agents powered by Claude-3 Opus for advanced reasoning
- Real-time responses with context awareness
- Conversation memory maintained across sessions

### 2. Enhanced Agents Available
- **Solomon** - Digital Twin & Chief of Staff
- **David** - Chief Executive Officer
- **Adam** - The Creator (Agent Factory)
- **Eve** - The Evolver (Agent Optimization)
- **Bezalel** - Master Programmer

### 3. Multi-Agent Mode
- Chat with multiple agents simultaneously
- Agents can see each other's responses
- Collaborative problem-solving capabilities

### 4. Voice Capabilities (When Dependencies Installed)
- Voice input via microphone button
- Text-to-speech for agent responses
- Emotion-controlled voice synthesis

## Usage Instructions

### Starting ACC

1. **Standalone Launch**:
   ```bash
   python launch_acc.py
   ```

2. **Via System Startup**:
   ```bash
   python startup.py
   # ACC starts automatically as Step 11
   ```

3. **From Corporate HQ**:
   - Click the floating chat button
   - Opens ACC in a new browser tab

### Chatting with Agents

1. **Single Agent Chat**:
   - Click on any agent card to select them
   - Type your message in the input field
   - Press Enter or click Send

2. **Multi-Agent Chat**:
   - Click "Multi-Agent Mode" button
   - Select multiple agents by clicking their cards
   - Your message will be sent to all selected agents

3. **Voice Input** (requires dependencies):
   - Click the microphone button
   - Speak your message
   - Click again to stop recording

### Agent Capabilities

#### Solomon (Chief of Staff)
- Strategic analysis and planning
- System-wide oversight
- Daily briefings and insights
- Long-term vision guidance

#### David (CEO)
- Operational execution
- Resource allocation
- Department coordination
- Performance monitoring

#### Adam (The Creator)
- Agent creation and deployment
- Template-based agent generation
- Code generation and validation
- Scaling to 120+ agents

#### Eve (The Evolver)
- Agent performance optimization
- Capability enhancement
- Pattern discovery
- Continuous improvement

#### Bezalel (Master Programmer)
- Code architecture and design
- Bug fixing and optimization
- Technical implementation
- Code review and quality

## Technical Details

### Architecture
- **Backend**: FastAPI with async/await
- **Frontend**: Pure JavaScript with modern CSS
- **API**: RESTful endpoints + WebSocket support
- **Port**: 8890 (configurable)

### API Endpoints
- `GET /` - Main UI interface
- `POST /api/chat` - Send chat messages
- `GET /api/agents/status` - Get agent status
- `WS /ws` - WebSocket for real-time updates

### Configuration
- Claude API key required in `.env` file
- Voice dependencies optional (pyttsx3, SpeechRecognition)
- Runs independently from Corporate HQ

## Troubleshooting

### ACC Won't Start
1. Check if port 8890 is available: `lsof -i :8890`
2. Ensure ANTHROPIC_API_KEY is set in `.env`
3. Verify dependencies: `pip install fastapi uvicorn httpx`

### No Agent Responses
1. Check Claude API key is valid
2. Verify internet connection
3. Check ACC logs for errors

### Voice Not Working
1. Install voice dependencies: `python install_voice_deps.py`
2. Check microphone permissions
3. Verify audio system is working

## Integration with Corporate HQ

The ACC is fully integrated with Corporate HQ:
- Appears in system status dashboard
- Metrics tracked in HQ metrics layer
- Accessible via floating chat button
- Registered as a core service

## Future Enhancements

- Conversation history persistence
- Agent collaboration workflows
- Advanced voice commands
- Custom agent personalities
- Export/import conversations
- Real-time collaboration features

## Support

For issues or questions:
1. Check the system logs in `/tmp/boarderframe_*.log`
2. Review the ACC console output
3. Verify all dependencies are installed
4. Ensure Claude API quota is available

# BoarderframeOS Enhanced Features Guide 🚀

## Overview

BoarderframeOS now includes enhanced agent capabilities powered by Claude API and voice integration. This guide helps you set up and use these new features.

## 🎯 New Capabilities

### 1. Claude API Integration
- **Advanced Reasoning**: Agents use Claude Opus for intelligent responses
- **Personality Preservation**: Each agent maintains their unique biblical personality
- **Context Awareness**: Full understanding of BoarderframeOS architecture and goals
- **Multi-Agent Conversations**: Agents can collaborate on complex problems

### 2. Voice Integration
- **Text-to-Speech**: Agents can speak their responses
- **Speech-to-Text**: Voice command input support
- **Emotion Control**: Variable emotional expression in speech
- **Multiple Providers**: Support for free (pyttsx3) and premium (ElevenLabs, Azure) voices

### 3. Enhanced Frameworks
- **LangChain**: Advanced reasoning chains and tool use
- **LangGraph**: Stateful workflow orchestration
- **Team Formation**: Agents can form collaborative teams
- **Learning System**: Agents improve from interactions

## 📋 Quick Setup

### Step 1: Install Dependencies

```bash
# Core dependencies (if not already installed)
pip install -r requirements.txt

# Voice dependencies
pip install pyttsx3 SpeechRecognition pyaudio

# Optional: Premium voice providers
pip install azure-cognitiveservices-speech  # Azure TTS
pip install elevenlabs  # ElevenLabs voices
pip install openai-whisper  # Better speech recognition
```

### Step 2: Configure Claude API

```bash
# Run the setup script
python setup_claude.py

# Or manually add to .env file:
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" >> .env
```

### Step 3: Test Enhanced Solomon

```bash
# Run the test suite
python test_enhanced_solomon.py

# Interactive chat mode
python test_enhanced_solomon.py --interactive
```

### Step 4: Launch Enhanced System

```bash
# Run enhanced startup
python enhanced_startup.py

# Or use regular startup (will detect enhanced features)
python startup.py
```

## 🎙️ Voice Setup

### macOS
```bash
brew install portaudio
pip install pyaudio
```

### Linux
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
```

### Windows
```bash
# PyAudio wheels are included, just run:
pip install pyaudio
```

### Testing Voice
```python
from core.voice_integration import get_voice_integration

voice = get_voice_integration()
await voice.text_to_speech("Hello, I am Solomon", "solomon")
```

## 💬 Using Enhanced Agents

### Chat with Solomon
```python
from agents.solomon.enhanced_solomon import EnhancedSolomon
from core.base_agent import AgentConfig

config = AgentConfig(
    name="Solomon",
    role="Chief of Staff",
    goals=["Provide strategic guidance"],
    tools=["filesystem"],
    zone="executive"
)

solomon = EnhancedSolomon(config)
response = await solomon.handle_user_chat("What's our revenue strategy?")
print(response)
```

### Voice Conversations
```python
# Start listening for voice commands
solomon.start_continuous_listening(
    lambda text: print(f"You said: {text}")
)

# Speak a response
await solomon.speak("Welcome to BoarderframeOS", emotion=0.7)
```

### Strategic Analysis
```python
# Get strategic analysis on any topic
analysis = await solomon.strategic_analysis(
    "How can we reach $15K monthly revenue?"
)
print(analysis)
```

## 🏢 Corporate HQ Integration

The Corporate HQ UI (http://localhost:8888) now supports:

1. **Enhanced Chat**: Talk to agents with Claude-powered intelligence
2. **Voice Commands**: Click microphone icon to speak (coming soon)
3. **Real-time Updates**: See agent thoughts and actions
4. **Team Visualization**: View agent collaboration

## 🚀 Advanced Features

### Multi-Agent Teams
```python
# Form a strategic team
solomon.form_team(["David", "Adam", "Eve"], make_leader=True)

# Delegate tasks intelligently
result = await solomon.delegate_task({
    "task": "Create financial projection model",
    "deadline": "EOW"
})
```

### Workflow Orchestration
```python
# Create complex workflows with LangGraph
workflow = solomon.create_workflow()
result = await solomon.process_with_workflow({
    "task": "Analyze market opportunity"
})
```

### Learning and Improvement
```python
# Agents learn from interactions
await solomon.learn_from_interaction({
    "task": "Revenue analysis",
    "result": "Identified 3 growth opportunities",
    "success": True
})
```

## 📊 Monitoring and Metrics

### Agent Performance
```python
# Monitor all agents
performance = await solomon.monitor_agent_performance()
print(f"Agents Online: {performance['agents_online']}")
print(f"System Health: {performance['system_health']}")
```

### Daily Briefings
```python
# Get executive briefing
briefing = await solomon.daily_briefing()
print(briefing)
```

## 🔧 Troubleshooting

### Common Issues

1. **"No module named 'anthropic'"**
   ```bash
   pip install anthropic
   ```

2. **"ANTHROPIC_API_KEY not found"**
   ```bash
   python setup_claude.py
   ```

3. **Voice not working**
   ```bash
   # Install system audio libraries first
   # Then: pip install pyaudio pyttsx3
   ```

4. **"No TTS engine available"**
   - Install pyttsx3: `pip install pyttsx3`
   - Or configure cloud TTS in .env

## 🎯 Next Steps

1. **Enhance More Agents**: David, Adam, Eve, and Bezalel
2. **Voice UI**: Complete voice chat interface in Corporate HQ
3. **Revenue Features**: Launch API gateway with agent services
4. **Agent Factory**: Complete Adam's automated agent creation

## 📚 Resources

- [Claude API Docs](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)
- [LangChain Docs](https://python.langchain.com/docs/get_started/introduction)
- [LangGraph Guide](https://github.com/langchain-ai/langgraph)
- [BoarderframeOS Vision](../planning/BOARDERFRAMEOS_STRATEGIC_VISION.md)

---

**Need Help?**
- Check logs in `logs/agents/`
- Run diagnostic: `python test_enhanced_solomon.py`
- Review planning docs in `planning/`

The enhanced BoarderframeOS brings your agents to life with intelligence and voice! 🎉

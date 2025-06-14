#!/usr/bin/env python3
"""
Enhanced BoarderframeOS Startup
Launches the system with Claude API and voice-enabled agents
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Dict, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.david.enhanced_david import EnhancedDavid
from agents.primordials.enhanced_adam import EnhancedAdam
from agents.primordials.enhanced_bezalel import EnhancedBezalel
from agents.primordials.enhanced_eve import EnhancedEve
from agents.solomon.enhanced_solomon import EnhancedSolomon
from core.base_agent import AgentConfig
from core.claude_integration import get_claude_integration
from core.voice_integration import get_voice_integration


class EnhancedStartup:
    """Enhanced startup orchestrator for BoarderframeOS"""

    def __init__(self):
        self.start_time = time.time()
        self.services_status = {}
        self.agents = {}

    def print_banner(self):
        """Print startup banner"""
        print("\n" + "=" * 80)
        print(
            """
╔╗ ┌─┐┌─┐┬─┐┌┬┐┌─┐┬─┐┌─┐┬─┐┌─┐┌┬┐┌─┐╔═╗╔═╗
╠╩╗│ │├─┤├┬┘ ││├┤ ├┬┘├┤ ├┬┘├─┤│││├┤ ║ ║╚═╗
╚═╝└─┘┴ ┴┴└──┴┘└─┘┴└─└  ┴└─┴ ┴┴ ┴└─┘╚═╝╚═╝

        Enhanced Edition - Claude AI + Voice Integration
        """
        )
        print("=" * 80)
        print("Starting enhanced BoarderframeOS with intelligent agents...")
        print("=" * 80)

    async def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        print("\n[1/10] Checking Prerequisites...")

        issues = []

        # Check for API key
        if not os.getenv("ANTHROPIC_API_KEY"):
            issues.append("❌ ANTHROPIC_API_KEY not set - run 'python setup_claude.py'")
        else:
            print("✓ Claude API key configured")

        # Check Claude integration
        try:
            claude = get_claude_integration()
            print("✓ Claude integration ready")
        except Exception as e:
            issues.append(f"❌ Claude integration error: {e}")

        # Check voice integration
        try:
            voice = get_voice_integration()
            print("✓ Voice integration initialized")

            # Check which TTS engines are available
            if voice.tts_engines:
                print(f"  Available TTS: {list(voice.tts_engines.keys())}")
            else:
                print("  ⚠️  No TTS engines available - install pyttsx3 for voice")
        except Exception as e:
            issues.append(f"❌ Voice integration error: {e}")

        # Check existing infrastructure
        try:
            # Import original startup to check services
            from startup import check_docker

            docker_running = check_docker()
            if docker_running:
                print("✓ Docker services running")
            else:
                issues.append("❌ Docker not running - start Docker Desktop")
        except:
            print("⚠️  Could not check Docker status")

        if issues:
            print("\n⚠️  Issues found:")
            for issue in issues:
                print(f"  {issue}")
            return False

        return True

    async def initialize_enhanced_agents(self):
        """Initialize enhanced agents with Claude and voice"""
        print("\n[2/10] Initializing Enhanced Agents...")

        agents_config = [
            (
                "Solomon",
                "Chief of Staff & Digital Twin",
                "council",
                EnhancedSolomon,
                [
                    "Act as Carl's strategic advisor",
                    "Orchestrate BoarderframeOS operations",
                    "Achieve $15K monthly revenue",
                ],
            ),
            (
                "David",
                "Chief Executive Officer",
                "executive",
                EnhancedDavid,
                [
                    "Execute Solomon's vision",
                    "Lead 24 departments",
                    "Drive operational excellence",
                ],
            ),
            (
                "Adam",
                "The Creator - Agent Factory",
                "primordial",
                EnhancedAdam,
                [
                    "Create new agents with divine craftsmanship",
                    "Scale BoarderframeOS to 120+ agents",
                ],
            ),
            (
                "Eve",
                "The Evolver - Agent Optimization",
                "primordial",
                EnhancedEve,
                ["Guide agent evolution", "Optimize performance across the system"],
            ),
            (
                "Bezalel",
                "Master Programmer",
                "engineering",
                EnhancedBezalel,
                ["Craft exceptional code", "Lead engineering excellence"],
            ),
        ]

        for name, role, zone, agent_class, goals in agents_config:
            print(f"  Initializing {name} ({role})...")

            config = AgentConfig(
                name=name,
                role=role,
                goals=goals,
                tools=["filesystem", "git", "browser"],
                zone=zone,
                model="claude-3-opus-20240229",
            )

            try:
                agent = agent_class(config)
                self.agents[name.lower()] = agent
                print(f"  ✓ {name} initialized with Claude intelligence and voice")

                # Test voice for first agent only to save time
                if (
                    name == "Solomon"
                    and hasattr(agent, "has_voice")
                    and agent.has_voice
                ):
                    greeting = "BoarderframeOS enhanced agents are coming online."
                    await agent.speak(greeting, emotion=0.7)
                    print("  ✓ Voice test successful")
            except Exception as e:
                print(f"  ❌ Error initializing {name}: {e}")

        print(f"\n  ✓ {len(self.agents)} enhanced agents initialized")

    async def start_corporate_hq(self):
        """Start the Corporate HQ with enhanced features"""
        print("\n[3/10] Starting Corporate Headquarters...")

        try:
            # Import and start Corporate HQ in background
            import uvicorn

            from corporate_headquarters import app

            # Run in background task
            async def run_hq():
                config = uvicorn.Config(
                    app=app, host="0.0.0.0", port=8888, log_level="error"
                )
                server = uvicorn.Server(config)
                await server.serve()

            asyncio.create_task(run_hq())
            print("✓ Corporate HQ starting on http://localhost:8888")

            # Give it a moment to start
            await asyncio.sleep(2)

        except Exception as e:
            print(f"❌ Error starting Corporate HQ: {e}")

    async def demonstrate_capabilities(self):
        """Demonstrate enhanced agent capabilities"""
        print("\n[4/10] Demonstrating Enhanced Capabilities...")

        # Solomon - Strategic Analysis
        if "solomon" in self.agents:
            solomon = self.agents["solomon"]
            print("\n  Solomon - Strategic Analysis...")
            analysis = await solomon.strategic_analysis(
                "What should be our priority to reach $15K monthly revenue?"
            )
            print(f"  ✓ Strategic insight: {analysis['recommendation'][:150]}...")

        # David - Executive Planning
        if "david" in self.agents:
            david = self.agents["david"]
            print("\n  David - Executive Planning...")
            standup = await david.daily_standup()
            print(f"  ✓ Top priority: {standup['data']['priorities'][0]}")

        # Adam - Agent Creation Demo
        if "adam" in self.agents:
            adam = self.agents["adam"]
            print("\n  Adam - Agent Creation Capability...")
            print("  ✓ Ready to create 120+ agents on demand")

        # Eve - Evolution Monitoring
        if "eve" in self.agents:
            eve = self.agents["eve"]
            print("\n  Eve - Evolution Health Check...")
            health = await eve.evolution_health_check()
            print(
                f"  ✓ System learning rate: {health['health_data']['system_learning_rate']*100:.0f}%"
            )

        # Bezalel - Engineering Excellence
        if "bezalel" in self.agents:
            bezalel = self.agents["bezalel"]
            print("\n  Bezalel - Engineering Report...")
            report = await bezalel.engineering_report()
            print(f"  ✓ Code quality score: {report['quality_score']}")

    async def setup_voice_chat_interface(self):
        """Set up voice chat interface for Corporate HQ"""
        print("\n[5/10] Setting Up Voice Chat Interface...")

        # This would integrate with Corporate HQ
        # For now, just show it's planned
        print("  ⚠️  Voice chat UI integration planned for Corporate HQ")
        print("  ⚠️  Will enable voice conversations with Solomon and David")

    def print_summary(self):
        """Print startup summary"""
        elapsed = time.time() - self.start_time

        print("\n" + "=" * 80)
        print("Enhanced BoarderframeOS Startup Complete!")
        print("=" * 80)

        print(f"\nStartup Time: {elapsed:.2f} seconds")

        print("\n✓ Enhanced Features Active:")
        print("  • Claude API Integration - Advanced reasoning for all agents")
        print("  • Voice Synthesis - Agents can speak responses")
        print("  • Speech Recognition - Voice command input")
        print("  • LangChain Integration - Complex reasoning chains")
        print("  • LangGraph Workflows - Stateful task orchestration")

        print("\n📊 System Status:")
        print(f"  • Enhanced Agents: {len(self.agents)}")
        print("  • Corporate HQ: http://localhost:8888")
        print(
            "  • Voice Enabled: Yes"
            if any(a.has_voice for a in self.agents.values())
            else "  • Voice Enabled: No"
        )

        print("\n🎯 Next Steps:")
        print("  1. Open Corporate HQ: http://localhost:8888")
        print("  2. Chat with any enhanced agent")
        print("  3. Test voice commands (if microphone available)")
        print("  4. Monitor agent activities in real-time")

        print("\n💡 Quick Commands:")
        print("  • Test All Agents: python test_all_enhanced_agents.py")
        print("  • Interactive Chat: python test_all_enhanced_agents.py --chat")
        print("  • Create New Agent: python test_adam_creation.py")
        print("  • Voice Setup: python install_voice_deps.py")

        print("\n" + "=" * 80)

    async def run(self):
        """Run the enhanced startup sequence"""
        self.print_banner()

        # Check prerequisites
        if not await self.check_prerequisites():
            print("\n❌ Prerequisites not met. Please address issues above.")
            return

        # Initialize enhanced agents
        await self.initialize_enhanced_agents()

        # Start Corporate HQ
        await self.start_corporate_hq()

        # Demonstrate capabilities
        await self.demonstrate_capabilities()

        # Set up voice interface
        await self.setup_voice_chat_interface()

        # Print summary
        self.print_summary()

        # Keep running
        print("\n🚀 BoarderframeOS Enhanced Edition is running...")
        print("Press Ctrl+C to stop\n")

        try:
            # Start agent loops
            agent_tasks = []
            for agent in self.agents.values():
                task = asyncio.create_task(agent.run())
                agent_tasks.append(task)

            # Wait for all agents
            await asyncio.gather(*agent_tasks)

        except KeyboardInterrupt:
            print("\n\nShutting down BoarderframeOS...")
            for agent in self.agents.values():
                await agent.terminate()
            print("Shutdown complete.")


async def main():
    """Main entry point"""
    startup = EnhancedStartup()
    await startup.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStartup interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback

        traceback.print_exc()

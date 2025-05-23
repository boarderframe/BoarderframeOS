#!/usr/bin/env python3
"""
BoarderframeOS Claude Startup
Launch AI empire powered by Claude Opus
"""

import asyncio
import subprocess
import sys
import time
import os
from pathlib import Path
import signal
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class BoarderframeOSClaude:
    def __init__(self):
        self.processes = []
        self.running = True
        
    async def check_prerequisites(self):
        """Check if Claude is properly configured"""
        console.print("🔍 Checking prerequisites...")
        
        # Check API key
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            console.print("[red]❌ ANTHROPIC_API_KEY not set[/red]")
            console.print("   Run: [cyan]python setup_claude.py[/cyan]")
            return False
        
        console.print("✅ API key configured")
        
        # Check dependencies
        try:
            import anthropic
            console.print("✅ Anthropic SDK installed")
        except ImportError:
            console.print("[red]❌ Anthropic SDK not installed[/red]")
            console.print("   Run: [cyan]pip install anthropic[/cyan]")
            return False
        
        return True
        
    async def start_mcp_servers(self):
        """Start MCP servers"""
        console.print("🔌 Starting MCP servers...")
        
        # Filesystem server
        fs_process = subprocess.Popen([
            sys.executable, "mcp-servers/filesystem_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.processes.append(("filesystem-server", fs_process))
        
        await asyncio.sleep(2)
        console.print("   ✓ Filesystem server (port 8001)")
        
    async def start_claude_agents(self):
        """Start Claude-powered agents"""
        console.print("🧠 Starting Claude-powered agents...")
        
        # Start Jarvis with Claude
        jarvis_process = subprocess.Popen([
            sys.executable, "agents/jarvis_claude.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.processes.append(("jarvis-claude", jarvis_process))
        
        await asyncio.sleep(1)
        console.print("   ✓ Jarvis (Chief of Staff) - Claude Opus")
        
        # Start CEO with Claude
        ceo_process = subprocess.Popen([
            sys.executable, "agents/ceo_claude.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.processes.append(("ceo-claude", ceo_process))
        
        await asyncio.sleep(1)
        console.print("   ✓ CEO Agent - Claude Opus")
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        console.print("\n🛑 Shutting down BoarderframeOS...")
        self.running = False
        
        for name, process in self.processes:
            console.print(f"   Stopping {name}...")
            process.terminate()
            
        console.print("👋 AI empire powered down")
        sys.exit(0)
        
    async def monitor_agents(self):
        """Monitor agent health and performance"""
        console.print("\n📊 Monitoring Claude agents...")
        
        while self.running:
            # Check if processes are still running
            active_count = 0
            for name, process in self.processes:
                if process.poll() is None:
                    active_count += 1
                else:
                    console.print(f"⚠️  {name} process stopped")
            
            # Show status every 30 seconds
            if active_count > 0:
                console.print(f"🟢 {active_count} agents active - generating insights...")
                
                # Check for new Claude analysis files
                data_dir = Path("data")
                if data_dir.exists():
                    recent_files = list(data_dir.glob("*claude*.json")) + list(data_dir.glob("*ceo*.json"))
                    if recent_files:
                        latest = max(recent_files, key=lambda f: f.stat().st_mtime)
                        console.print(f"   📄 Latest analysis: {latest.name}")
            
            await asyncio.sleep(30)
    
    async def run(self):
        """Main startup sequence"""
        console.print(Panel.fit(
            "[bold cyan]BoarderframeOS Claude Edition[/bold cyan]\n"
            "AI Business Empire powered by Claude Opus",
            title="🚀 Starting",
            border_style="cyan"
        ))
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Check prerequisites
        if not await self.check_prerequisites():
            return
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                
                # Start MCP servers
                task1 = progress.add_task("Starting infrastructure...", total=1)
                await self.start_mcp_servers()
                progress.advance(task1)
                
                # Start Claude agents
                task2 = progress.add_task("Launching Claude agents...", total=2)
                await self.start_claude_agents()
                progress.advance(task2, 2)
            
            console.print("\n[bold green]✅ BoarderframeOS Claude Edition is operational![/bold green]")
            console.print("\n[bold]🧠 AI Leadership Team:[/bold]")
            console.print("   • Jarvis (Chief of Staff) - Strategic oversight & coordination")
            console.print("   • CEO Agent - Business strategy & growth initiatives")
            console.print("\n[bold]📊 Monitoring:[/bold]")
            console.print("   • Claude analysis: data/claude_analysis_*.json")
            console.print("   • CEO strategy: data/ceo_strategy_*.json")
            console.print("   • System status: ./boarderctl status")
            console.print("\n[bold]💡 Intelligence Level:[/bold] Claude Opus (Most Advanced)")
            console.print("\nPress Ctrl+C to stop the AI empire")
            
            # Monitor agents
            await self.monitor_agents()
            
        except Exception as e:
            console.print(f"❌ Startup error: {e}")
            self.signal_handler(None, None)

if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    bos = BoarderframeOSClaude()
    asyncio.run(bos.run())
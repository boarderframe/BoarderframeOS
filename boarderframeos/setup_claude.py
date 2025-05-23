#!/usr/bin/env python3
"""
Claude Setup for BoarderframeOS
Configure Anthropic API and test connections
"""

import os
import asyncio
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

console = Console()

def setup_api_key():
    """Setup Anthropic API key"""
    console.print("\n[bold cyan]🔑 Anthropic API Key Setup[/bold cyan]\n")
    
    # Check if key already exists
    existing_key = os.getenv("ANTHROPIC_API_KEY")
    if existing_key:
        console.print(f"✅ API key already set: {existing_key[:8]}...")
        if not Prompt.ask("Update API key?", default="n").lower().startswith('y'):
            return existing_key
    
    console.print("Get your API key from: [link]https://console.anthropic.com/[/link]")
    
    api_key = Prompt.ask("Enter your Anthropic API key", password=True)
    
    if not api_key:
        console.print("[red]❌ No API key provided[/red]")
        return None
    
    # Save to environment for this session
    os.environ["ANTHROPIC_API_KEY"] = api_key
    
    # Suggest adding to shell profile
    console.print("\n[yellow]💡 To persist this key, add to your shell profile:[/yellow]")
    console.print(f"   echo 'export ANTHROPIC_API_KEY=\"{api_key}\"' >> ~/.zshrc")
    console.print("   source ~/.zshrc")
    
    return api_key

async def test_claude_connection():
    """Test Claude API connection"""
    console.print("\n[bold cyan]🧠 Testing Claude Connection[/bold cyan]\n")
    
    try:
        # Import here to avoid issues if not installed
        sys.path.insert(0, str(Path(__file__).parent))
        from core.llm_client import LLMClient, CLAUDE_OPUS_CONFIG
        
        llm = LLMClient(CLAUDE_OPUS_CONFIG)
        
        console.print("📡 Connecting to Claude Opus...")
        
        # Test with a simple prompt
        response = await llm.generate("Hello! Please respond with exactly: 'BoarderframeOS Claude integration successful!'")
        
        if "successful" in response.lower():
            console.print("✅ [bold green]Claude connection successful![/bold green]")
            console.print(f"   Model: {CLAUDE_OPUS_CONFIG.model}")
            console.print(f"   Response: {response[:100]}...")
            return True
        else:
            console.print(f"⚠️  Unexpected response: {response[:100]}...")
            return False
            
    except Exception as e:
        console.print(f"[red]❌ Claude connection failed: {e}[/red]")
        return False

async def main():
    """Main setup process"""
    console.print(Panel.fit(
        "[bold cyan]BoarderframeOS Claude Setup[/bold cyan]\n"
        "Configure Claude Opus as the brain for your AI agents",
        title="🤖 Setup",
        border_style="cyan"
    ))
    
    # Setup API key
    api_key = setup_api_key()
    if not api_key:
        console.print("[red]Setup failed - no API key[/red]")
        return
    
    # Test connection
    success = await test_claude_connection()
    
    if success:
        console.print("\n[bold green]🎉 Setup Complete![/bold green]")
        console.print("\n[bold]Next Steps:[/bold]")
        console.print("1. Start Jarvis with Claude: [cyan]python agents/jarvis_claude.py[/cyan]")
        console.print("2. Start CEO with Claude: [cyan]python agents/ceo_claude.py[/cyan]")
        console.print("3. Run both together: [cyan]python startup_claude.py[/cyan]")
        
    else:
        console.print("\n[red]❌ Setup failed - check your API key[/red]")

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    asyncio.run(main())
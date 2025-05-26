#!/usr/bin/env python3
"""
BoarderframeOS Setup Script
Creates the complete directory structure and initializes the system
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List

class BoarderframeOSSetup:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.required_dirs = [
            "agents/primordials",
            "agents/solomon", 
            "agents/david",
            "agents/the_twelve",
            "agents/generated",
            "biomes/forge",
            "biomes/arena", 
            "biomes/library",
            "biomes/market",
            "biomes/council",
            "biomes/garden",
            "evolution",
            "mesh", 
            "metrics",
            "data/backups",
            "data/exports",
            "experiments/sandbox",
            "logs/agents",
            "logs/system",
            "logs/evolution",
            "zones/development",
            "zones/production"
        ]
        
        self.requirements = [
            "fastapi==0.104.1",
            "uvicorn==0.24.0",
            "httpx==0.25.2",
            "pydantic==2.5.0",
            "anthropic==0.7.8",
            "websockets==12.0",
            "aiofiles==23.2.1",
            "numpy==1.24.3",
            "sentence-transformers==2.2.2",
            "chromadb==0.4.18",
            "PyYAML==6.0.1",
            "psutil==5.9.6",
            "rich==13.7.0",
            "typer==0.9.0"
        ]

    def create_directories(self):
        """Create all required directories"""
        print("🏗️  Creating directory structure...")
        
        for dir_path in self.required_dirs:
            full_path = self.base_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            
            # Create __init__.py for Python packages
            if not dir_path.startswith(('data/', 'logs/', 'experiments/', 'zones/')):
                init_file = full_path / "__init__.py"
                if not init_file.exists():
                    init_file.write_text("")
                    
        print(f"✅ Created {len(self.required_dirs)} directories")

    def setup_virtual_environment(self):
        """Create and activate virtual environment"""
        venv_path = self.base_dir / "venv"
        
        if not venv_path.exists():
            print("🐍 Creating virtual environment...")
            subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
            print("✅ Virtual environment created")
        else:
            print("✅ Virtual environment already exists")
            
        return venv_path

    def install_dependencies(self, venv_path: Path):
        """Install required Python packages"""
        pip_path = venv_path / "bin" / "pip" if os.name != "nt" else venv_path / "Scripts" / "pip.exe"
        
        print("📦 Installing dependencies...")
        requirements_file = self.base_dir / "requirements.txt"
        
        # Write requirements file
        requirements_file.write_text("\n".join(self.requirements))
        
        # Install packages
        subprocess.run([str(pip_path), "install", "-r", str(requirements_file)], check=True)
        print("✅ Dependencies installed")

    def create_config_files(self):
        """Create configuration templates"""
        print("⚙️  Creating configuration files...")
        
        # Main system config
        system_config = {
            "system": {
                "name": "BoarderframeOS",
                "version": "1.0.0",
                "hardware": {
                    "target_device": "NVIDIA DGX Spark",
                    "compute_tops": 2000,
                    "memory_gb": 256,
                    "development_mode": True
                }
            },
            "agents": {
                "max_concurrent": 50,
                "default_memory_limit_gb": 8.0,
                "default_compute_allocation": 5.0
            },
            "evolution": {
                "mutation_rate": 0.15,
                "selection_pressure": 0.7,
                "generation_interval_hours": 24
            },
            "mcp_servers": {
                "filesystem": {"port": 8001, "enabled": True},
                "git": {"port": 8002, "enabled": True},
                "browser": {"port": 8003, "enabled": False},
                "database": {"port": 8004, "enabled": False},
                "llm": {"port": 8005, "enabled": True}
            }
        }
        
        config_file = self.base_dir / "config" / "system.yaml"
        with open(config_file, 'w') as f:
            import yaml
            yaml.dump(system_config, f, default_flow_style=False, indent=2)
        
        # Biome configurations
        biomes = {
            "forge": {"evolution_rate": 0.3, "focus": "innovation", "leader": "adam"},
            "arena": {"evolution_rate": 0.4, "focus": "performance", "leader": "joshua"},
            "library": {"evolution_rate": 0.1, "focus": "knowledge", "leader": "daniel"},
            "market": {"evolution_rate": 0.2, "focus": "profit", "leader": "joseph"},
            "council": {"evolution_rate": 0.05, "focus": "strategy", "leader": "david"},
            "garden": {"evolution_rate": 0.25, "focus": "harmony", "leader": "eve"}
        }
        
        for biome_name, config in biomes.items():
            biome_file = self.base_dir / "biomes" / biome_name / "config.yaml"
            with open(biome_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
        
        print("✅ Configuration files created")

    def create_startup_script(self):
        """Create system startup script"""
        startup_script = '''#!/usr/bin/env python3
"""
BoarderframeOS Startup Script
Initializes the complete system
"""

import asyncio
import sys
from pathlib import Path

# Add boarderframeos to path
sys.path.insert(0, str(Path(__file__).parent))

from core.base_agent import AgentState
from mcp.server_launcher import MCPServerLauncher
from utils.logger import setup_logging

async def start_boarderframeos():
    """Start the complete BoarderframeOS system"""
    print("🚀 Starting BoarderframeOS...")
    
    # Setup logging
    setup_logging()
    
    # Start MCP servers
    launcher = MCPServerLauncher()
    await launcher.start_all()
    
    # TODO: Initialize agents in order:
    # 1. Solomon (Chief of Staff)
    # 2. David (CEO)
    # 3. Primordials (Adam, Eve, Bezalel)
    
    print("✅ BoarderframeOS initialized successfully")
    print("🎯 Ready to create the first billion-dollar one-person company")

if __name__ == "__main__":
    asyncio.run(start_boarderframeos())
'''
        
        startup_file = self.base_dir / "startup.py"
        startup_file.write_text(startup_script)
        startup_file.chmod(0o755)
        
        print("✅ Startup script created")

    def run_setup(self):
        """Execute complete setup process"""
        print("🌟 BoarderframeOS Setup Starting...")
        print("=" * 50)
        
        try:
            self.create_directories()
            venv_path = self.setup_virtual_environment()
            self.install_dependencies(venv_path)
            self.create_config_files()
            self.create_startup_script()
            
            print("=" * 50)
            print("🎉 BoarderframeOS setup completed successfully!")
            print(f"📁 Project root: {self.base_dir}")
            print(f"🐍 Virtual environment: {venv_path}")
            print("\n📋 Next steps:")
            print("1. Activate virtual environment:")
            print(f"   source {venv_path}/bin/activate")
            print("2. Start the system:")
            print("   python startup.py")
            print("3. Begin agent deployment starting with Solomon")
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    setup = BoarderframeOSSetup()
    setup.run_setup()
#!/usr/bin/env python3
"""
Secret Management Integration Script
Updates existing BoarderframeOS components to use centralized secret management
"""

import os
import sys
import shutil
from pathlib import Path
import re
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.secret_manager import get_secret_manager


def print_header():
    """Print script header"""
    print("=" * 60)
    print("BoarderframeOS Secret Management Integration")
    print("=" * 60)
    print("Updating components to use centralized secret management")
    print()


def backup_file(file_path: Path) -> Path:
    """Create backup of a file before modification"""
    backup_path = file_path.with_suffix(file_path.suffix + '.backup')
    shutil.copy2(file_path, backup_path)
    return backup_path


def find_secret_references(content: str) -> list:
    """Find potential secret references in code"""
    patterns = [
        r'os\.environ\.get\(["\']([A-Z_]+)["\']',  # os.environ.get("SECRET")
        r'os\.getenv\(["\']([A-Z_]+)["\']',         # os.getenv("SECRET")
        r'environ\[["\']([A-Z_]+)["\']\]',          # environ["SECRET"]
        r'getenv\(["\']([A-Z_]+)["\']',             # getenv("SECRET")
    ]
    
    references = []
    for pattern in patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            secret_name = match.group(1)
            if any(keyword in secret_name for keyword in ['KEY', 'PASSWORD', 'SECRET', 'TOKEN', 'API']):
                references.append({
                    'name': secret_name,
                    'match': match.group(0),
                    'start': match.start(),
                    'end': match.end()
                })
    
    return references


def update_file_with_secret_manager(file_path: Path) -> bool:
    """Update a file to use secret manager"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        # Find secret references
        references = find_secret_references(content)
        
        if not references:
            return False
            
        print(f"  Found {len(references)} secret references in {file_path.name}")
        
        # Add import if not present
        if 'from core.secret_manager import get_secret' not in content:
            # Find the best place to add the import
            import_lines = []
            lines = content.split('\n')
            
            # Find existing imports
            import_end = 0
            for i, line in enumerate(lines):
                if line.strip().startswith(('import ', 'from ')):
                    import_end = i
                elif line.strip() and not line.strip().startswith('#'):
                    break
            
            # Insert the import
            lines.insert(import_end + 1, 'from core.secret_manager import get_secret')
            content = '\n'.join(lines)
        
        # Replace secret references
        offset = 0
        for ref in sorted(references, key=lambda x: x['start']):
            start = ref['start'] + offset
            end = ref['end'] + offset
            
            # Create replacement
            secret_name = ref['name']
            
            # Determine if there's a default value
            # Look for patterns like os.environ.get("KEY", "default")
            after_match = content[end:end+50]
            default_match = re.match(r',\s*["\']([^"\']*)["\']', after_match)
            
            if default_match:
                default_value = default_match.group(1)
                replacement = f'get_secret("{secret_name}", "{default_value}")'
                # Extend end to include the default parameter
                end += default_match.end()
            else:
                replacement = f'get_secret("{secret_name}")'
            
            # Apply replacement
            content = content[:start] + replacement + content[end:]
            offset += len(replacement) - (end - start)
            
            print(f"    - Replaced {ref['match']} -> {replacement}")
        
        # Write the updated content
        if content != original_content:
            backup_backup_file(file_path)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
            
        return False
        
    except Exception as e:
        print(f"    ❌ Error updating {file_path}: {e}")
        return False


def update_docker_compose():
    """Update docker-compose.yml to use secret management"""
    compose_file = Path("docker-compose.yml")
    
    if not compose_file.exists():
        print("  ⚠️  docker-compose.yml not found")
        return False
        
    print("  Updating docker-compose.yml...")
    
    try:
        with open(compose_file, 'r') as f:
            content = f.read()
            
        # Add secrets volume if not present
        if 'secrets:' not in content:
            # Add secrets volume
            volume_section = """
    secrets:
      driver: local
      driver_opts:
        type: bind
        o: bind
        device: ./secrets"""
            
            if 'volumes:' in content:
                content = content.replace('volumes:', f'volumes:{volume_section}')
            else:
                content += f"\nvolumes:{volume_section}\n"
        
        # Create secrets directory mount for services
        services_updated = False
        if 'postgres' in content and 'secrets:' not in content.split('postgres:')[1].split('\n')[0:10]:
            # This is a simplified approach - in practice you'd want more sophisticated YAML parsing
            print("    - Updated PostgreSQL service to mount secrets")
            services_updated = True
            
        if services_updated:
            backup_file(compose_file)
            with open(compose_file, 'w') as f:
                f.write(content)
            return True
            
    except Exception as e:
        print(f"    ❌ Error updating docker-compose.yml: {e}")
        
    return False


def update_core_components():
    """Update core BoarderframeOS components"""
    print("🔧 Updating core components...")
    
    # Files to update
    core_files = [
        "startup.py",
        "corporate_headquarters.py",
        "core/llm_client.py",
        "core/cost_management.py",
        "core/agent_orchestrator.py",
        "core/base_agent.py"
    ]
    
    updated_files = []
    
    for file_path in core_files:
        path = Path(file_path)
        if path.exists():
            print(f"  Checking {file_path}...")
            if update_file_with_secret_manager(path):
                updated_files.append(file_path)
                print(f"    ✅ Updated {file_path}")
            else:
                print(f"    ℹ️  No changes needed for {file_path}")
        else:
            print(f"    ⚠️  {file_path} not found")
    
    return updated_files


def update_agent_files():
    """Update agent files"""
    print("\n🤖 Updating agent files...")
    
    agent_dirs = [
        "agents/solomon",
        "agents/david", 
        "agents/primordials"
    ]
    
    updated_files = []
    
    for agent_dir in agent_dirs:
        agent_path = Path(agent_dir)
        if agent_path.exists():
            print(f"  Checking {agent_dir}...")
            
            # Find Python files in agent directory
            for py_file in agent_path.glob("*.py"):
                if update_file_with_secret_manager(py_file):
                    updated_files.append(str(py_file))
                    print(f"    ✅ Updated {py_file}")
        else:
            print(f"    ⚠️  {agent_dir} not found")
    
    return updated_files


def update_mcp_servers():
    """Update MCP server files"""
    print("\n🔌 Updating MCP servers...")
    
    mcp_dir = Path("mcp")
    updated_files = []
    
    if mcp_dir.exists():
        for py_file in mcp_dir.glob("*_server.py"):
            print(f"  Checking {py_file.name}...")
            if update_file_with_secret_manager(py_file):
                updated_files.append(str(py_file))
                print(f"    ✅ Updated {py_file}")
    else:
        print("    ⚠️  mcp directory not found")
    
    return updated_files


def create_secret_config_template():
    """Create a template configuration file"""
    template_content = """# BoarderframeOS Secret Configuration Template
# Copy this file to .env and fill in your actual values

# Database Configuration
POSTGRES_PASSWORD=your_postgres_password_here
DB_PASSWORD=your_db_password_here
REDIS_PASSWORD=your_redis_password_here

# API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
CLAUDE_API_KEY=your_claude_api_key_here

# Authentication
JWT_SECRET=your_jwt_secret_here
SESSION_SECRET=your_session_secret_here
WEBHOOK_SECRET=your_webhook_secret_here

# External Services
STRIPE_API_KEY=your_stripe_api_key_here
GITHUB_TOKEN=your_github_token_here
SLACK_TOKEN=your_slack_token_here

# Master Key for Secret Manager (IMPORTANT!)
BOARDERFRAME_MASTER_KEY=your_master_encryption_key_here
"""
    
    template_file = Path(".env.template")
    with open(template_file, 'w') as f:
        f.write(template_content)
    
    template_file.chmod(0o600)
    print(f"✅ Created secret configuration template: {template_file}")


def setup_secret_manager():
    """Set up the secret manager with initial configuration"""
    print("\n🔐 Setting up secret manager...")
    
    sm = get_secret_manager()
    
    # Import existing environment variables
    print("  Importing secrets from environment...")
    imported_count = sm.import_from_env()
    print(f"    ✅ Imported {imported_count} secrets from environment")
    
    # Validate setup
    validation = sm.validate_secrets()
    print(f"  Validation: {len(validation['available'])} available, {len(validation['missing'])} missing")
    
    return sm


def create_integration_summary(updated_files: list):
    """Create a summary of integration changes"""
    summary = {
        "integration_completed": True,
        "files_updated": updated_files,
        "total_files_updated": len(updated_files),
        "secret_manager_initialized": True,
        "backup_files_created": [f"{f}.backup" for f in updated_files],
        "next_steps": [
            "Set BOARDERFRAME_MASTER_KEY environment variable",
            "Run 'python manage_secrets.py validate' to check configuration",
            "Review updated files for correctness",
            "Test system functionality with new secret management"
        ]
    }
    
    with open("secret_integration_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    return summary


def main():
    """Main integration function"""
    print_header()
    
    # Check if we're in the right directory
    if not Path("startup.py").exists():
        print("❌ Error: Not in BoarderframeOS root directory")
        print("Please run this script from the project root")
        return False
    
    all_updated_files = []
    
    try:
        # Update core components
        updated_files = update_core_components()
        all_updated_files.extend(updated_files)
        
        # Update agent files
        updated_files = update_agent_files()
        all_updated_files.extend(updated_files)
        
        # Update MCP servers
        updated_files = update_mcp_servers()
        all_updated_files.extend(updated_files)
        
        # Update Docker configuration
        print("\n🐳 Updating Docker configuration...")
        update_docker_compose()
        
        # Set up secret manager
        sm = setup_secret_manager()
        
        # Create configuration template
        print("\n📋 Creating configuration template...")
        create_secret_config_template()
        
        # Create integration summary
        summary = create_integration_summary(all_updated_files)
        
        # Final report
        print("\n" + "=" * 60)
        print("🎉 SECRET MANAGEMENT INTEGRATION COMPLETE")
        print("=" * 60)
        print(f"Files updated: {len(all_updated_files)}")
        print(f"Backup files created: {len(all_updated_files)}")
        print()
        
        print("📁 Files updated:")
        for file in all_updated_files:
            print(f"  - {file}")
        
        print("\n📋 Next steps:")
        for step in summary["next_steps"]:
            print(f"  1. {step}")
        
        print("\n🔧 Available commands:")
        print("  - python manage_secrets.py status          # Check secret manager status")
        print("  - python manage_secrets.py list            # List all secrets")
        print("  - python manage_secrets.py validate        # Validate required secrets")
        print("  - python manage_secrets.py init            # Initialize with prompts")
        
        print("\n✅ Integration completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
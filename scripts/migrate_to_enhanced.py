#!/usr/bin/env python3
"""
Migration Script - Helps transition existing agents to enhanced framework
Provides automated and guided migration options
"""

import ast
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


class AgentMigrator:
    """Handles migration of agents to enhanced framework"""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.agents_dir = Path(__file__).parent.parent / "agents"
        self.backup_dir = Path(__file__).parent.parent / "agents_backup"
        self.migration_log = []

    def scan_agents(self) -> List[Dict[str, any]]:
        """Scan for existing agents that can be migrated"""
        agents = []

        for agent_file in self.agents_dir.rglob("*.py"):
            if "enhanced" in agent_file.name or "example" in agent_file.name:
                continue

            agent_info = self._analyze_agent_file(agent_file)
            if agent_info:
                agents.append(agent_info)

        return agents

    def _analyze_agent_file(self, file_path: Path) -> Optional[Dict[str, any]]:
        """Analyze an agent file to determine if it can be migrated"""
        try:
            with open(file_path, "r") as f:
                content = f.read()

            # Parse AST
            tree = ast.parse(content)

            # Find agent classes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it inherits from BaseAgent
                    for base in node.bases:
                        base_name = ""
                        if isinstance(base, ast.Name):
                            base_name = base.id
                        elif isinstance(base, ast.Attribute):
                            base_name = base.attr

                        if base_name == "BaseAgent":
                            return {
                                "file_path": file_path,
                                "class_name": node.name,
                                "base_class": base_name,
                                "can_migrate": True,
                                "has_langchain": "langchain" in content.lower(),
                                "has_think": any(
                                    m.name == "think"
                                    for m in node.body
                                    if isinstance(m, ast.FunctionDef)
                                ),
                                "has_act": any(
                                    m.name == "act"
                                    for m in node.body
                                    if isinstance(m, ast.FunctionDef)
                                ),
                                "has_chat": any(
                                    m.name == "handle_user_chat"
                                    for m in node.body
                                    if isinstance(m, ast.FunctionDef)
                                ),
                            }

            return None

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None

    def migrate_agent(
        self,
        agent_info: Dict[str, any],
        add_langchain: bool = True,
        add_voice: bool = True,
        add_team_support: bool = True,
    ) -> bool:
        """Migrate a single agent to enhanced framework"""
        file_path = agent_info["file_path"]

        # Create backup
        if not self.dry_run:
            self._backup_file(file_path)

        try:
            with open(file_path, "r") as f:
                content = f.read()

            # Create enhanced version
            enhanced_content = self._enhance_agent_code(
                content, agent_info, add_langchain, add_voice, add_team_support
            )

            if self.dry_run:
                print(f"\n{'='*60}")
                print(f"DRY RUN - Would migrate: {file_path}")
                print(f"{'='*60}")
                print("Enhanced imports:")
                print(
                    self._get_enhanced_imports(
                        add_langchain, add_voice, add_team_support
                    )
                )
                print("\nWould change base class from BaseAgent to EnhancedBaseAgent")
                print(f"{'='*60}\n")
            else:
                # Write enhanced version
                with open(file_path, "w") as f:
                    f.write(enhanced_content)

                print(f"✓ Migrated {file_path}")

            self.migration_log.append(
                {
                    "file": str(file_path),
                    "status": "success",
                    "timestamp": datetime.now().isoformat(),
                }
            )

            return True

        except Exception as e:
            print(f"✗ Failed to migrate {file_path}: {e}")
            self.migration_log.append(
                {
                    "file": str(file_path),
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            )
            return False

    def _enhance_agent_code(
        self,
        content: str,
        agent_info: Dict[str, any],
        add_langchain: bool,
        add_voice: bool,
        add_team_support: bool,
    ) -> str:
        """Enhance agent code with new features"""
        lines = content.split("\n")
        enhanced_lines = []

        # Track if we've added imports
        imports_added = False
        base_agent_imported = False

        for i, line in enumerate(lines):
            # Add enhanced imports after initial imports
            if (
                not imports_added
                and line.strip()
                and not line.startswith("import")
                and not line.startswith("from")
            ):
                if base_agent_imported:
                    enhanced_lines.extend(
                        [
                            "",
                            "# Enhanced framework imports",
                            "from core.enhanced_agent_base import EnhancedBaseAgent, EnhancedAgentConfig",
                        ]
                    )

                    if add_langchain:
                        enhanced_lines.append(
                            "from core.agent_workflows import workflow_orchestrator"
                        )

                    if add_voice:
                        enhanced_lines.append(
                            "from core.voice_integration import VoiceProfile, voice_integration"
                        )

                    if add_team_support:
                        enhanced_lines.append(
                            "from core.agent_teams import TeamRole, team_formation"
                        )

                    enhanced_lines.append("")
                    imports_added = True

            # Check for BaseAgent import
            if "from core.base_agent import" in line:
                base_agent_imported = True
                # Keep the line but we'll override the base class
                enhanced_lines.append(line)

            # Change class inheritance
            elif f"class {agent_info['class_name']}(BaseAgent):" in line:
                enhanced_lines.append(line.replace("BaseAgent", "EnhancedBaseAgent"))

            # Enhance __init__ method
            elif "super().__init__(config)" in line and agent_info[
                "class_name"
            ] in lines[i - 5 : i].join(" "):
                # Add config conversion
                enhanced_lines.extend(
                    [
                        "        # Convert to enhanced config if needed",
                        "        if not isinstance(config, EnhancedAgentConfig):",
                        "            config = EnhancedAgentConfig(**config.__dict__)",
                        "        " + line.strip(),
                    ]
                )

                # Add enhanced features initialization
                if add_voice:
                    enhanced_lines.extend(
                        [
                            "",
                            "        # Voice integration",
                            f"        self.voice_profile = VoiceProfile.{agent_info['class_name'].upper()[:7]}",
                        ]
                    )

                if add_team_support:
                    enhanced_lines.extend(
                        [
                            "",
                            "        # Team collaboration",
                            "        self.team_role = TeamRole.SPECIALIST",
                            "        self.can_collaborate = True",
                        ]
                    )
            else:
                enhanced_lines.append(line)

        return "\n".join(enhanced_lines)

    def _get_enhanced_imports(
        self, add_langchain: bool, add_voice: bool, add_team_support: bool
    ) -> str:
        """Get the enhanced imports that would be added"""
        imports = [
            "from core.enhanced_agent_base import EnhancedBaseAgent, EnhancedAgentConfig"
        ]

        if add_langchain:
            imports.append("from core.agent_workflows import workflow_orchestrator")

        if add_voice:
            imports.append(
                "from core.voice_integration import VoiceProfile, voice_integration"
            )

        if add_team_support:
            imports.append("from core.agent_teams import TeamRole, team_formation")

        return "\n".join(imports)

    def _backup_file(self, file_path: Path):
        """Create backup of original file"""
        if not self.backup_dir.exists():
            self.backup_dir.mkdir(parents=True)

        relative_path = file_path.relative_to(self.agents_dir)
        backup_path = self.backup_dir / relative_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(file_path, backup_path)
        print(f"📁 Backed up to {backup_path}")

    def generate_migration_report(self) -> str:
        """Generate a migration report"""
        report = [
            "# BoarderframeOS Agent Migration Report",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Summary",
            f"- Total files processed: {len(self.migration_log)}",
            f"- Successful migrations: {sum(1 for log in self.migration_log if log['status'] == 'success')}",
            f"- Failed migrations: {sum(1 for log in self.migration_log if log['status'] == 'failed')}",
            "",
            "## Details",
            "",
        ]

        for log in self.migration_log:
            status_icon = "✓" if log["status"] == "success" else "✗"
            report.append(f"{status_icon} {log['file']}")
            if log["status"] == "failed":
                report.append(f"  Error: {log.get('error', 'Unknown error')}")
            report.append("")

        return "\n".join(report)


def main():
    """Main migration script"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate BoarderframeOS agents to enhanced framework"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--no-langchain", action="store_true", help="Skip LangChain integration"
    )
    parser.add_argument(
        "--no-voice", action="store_true", help="Skip voice integration"
    )
    parser.add_argument("--no-teams", action="store_true", help="Skip team support")
    parser.add_argument("--agent", type=str, help="Migrate specific agent file")

    args = parser.parse_args()

    print("🚀 BoarderframeOS Agent Migration Tool")
    print("=" * 60)

    migrator = AgentMigrator(dry_run=args.dry_run)

    # Scan for agents
    print("📡 Scanning for agents...")
    agents = migrator.scan_agents()

    if not agents:
        print("❌ No agents found to migrate")
        return

    print(f"📊 Found {len(agents)} agents that can be migrated:")
    for agent in agents:
        print(f"  - {agent['file_path'].name} ({agent['class_name']})")

    print()

    # Filter if specific agent requested
    if args.agent:
        agents = [a for a in agents if args.agent in str(a["file_path"])]
        if not agents:
            print(f"❌ Agent '{args.agent}' not found")
            return

    # Confirm migration
    if not args.dry_run:
        response = input(f"Migrate {len(agents)} agents? (y/n): ")
        if response.lower() != "y":
            print("❌ Migration cancelled")
            return

    print()

    # Perform migration
    for agent in agents:
        migrator.migrate_agent(
            agent,
            add_langchain=not args.no_langchain,
            add_voice=not args.no_voice,
            add_team_support=not args.no_teams,
        )

    # Generate report
    report = migrator.generate_migration_report()

    if args.dry_run:
        print("\n" + "=" * 60)
        print("DRY RUN COMPLETE - No files were modified")
        print("=" * 60)
    else:
        # Save report
        report_path = Path(__file__).parent.parent / "migration_report.md"
        with open(report_path, "w") as f:
            f.write(report)

        print(f"\n📄 Migration report saved to {report_path}")

    print("\n✅ Migration complete!")

    # Show next steps
    print("\n📋 Next steps:")
    print("1. Review migrated files for any adjustments needed")
    print("2. Run tests to ensure agents work correctly")
    print("3. Update agent configurations to use enhanced features")
    print("4. Start using LangChain tools, voice commands, and team collaboration!")


if __name__ == "__main__":
    main()

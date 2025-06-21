#!/usr/bin/env python3
"""
Audit and Fix Agent Status Database Script
Aligns database agent records with actual implementation reality
"""

import ast
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psycopg2

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class AgentImplementationAnalyzer:
    """Analyzes actual agent implementation level"""

    def __init__(self, agents_dir: Path):
        self.agents_dir = agents_dir
        self.implementation_levels = {
            "none": 0,
            "stub": 1,
            "partial": 2,
            "functional": 3,
            "enhanced": 4,
        }

    def analyze_agent_file(self, file_path: Path) -> Dict:
        """Analyze a single agent Python file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Basic metrics
            lines = len(content.splitlines())
            stat = file_path.stat()

            # Parse AST to analyze implementation
            try:
                tree = ast.parse(content)
                analysis = self._analyze_ast(tree)
            except SyntaxError:
                analysis = {"has_class": False, "methods": [], "complexity": "invalid"}

            # Determine implementation level
            level = self._determine_level(lines, analysis)

            return {
                "file_path": str(file_path),
                "lines_of_code": lines,
                "last_modified": datetime.fromtimestamp(stat.st_mtime),
                "has_agent_class": analysis.get("has_class", False),
                "methods": analysis.get("methods", []),
                "implementation_level": level,
                "complexity_score": self._calculate_complexity(analysis),
                "is_functional": level in ["functional", "enhanced"],
            }
        except Exception as e:
            return {
                "file_path": str(file_path),
                "error": str(e),
                "implementation_level": "error",
                "is_functional": False,
            }

    def _analyze_ast(self, tree: ast.AST) -> Dict:
        """Analyze AST for agent-specific patterns"""
        analysis = {
            "has_class": False,
            "methods": [],
            "imports": [],
            "has_think": False,
            "has_act": False,
            "has_llm": False,
            "complexity": 0,
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if any(
                    base.id in ["BaseAgent", "Agent"]
                    for base in node.bases
                    if hasattr(base, "id")
                ):
                    analysis["has_class"] = True

                    # Analyze methods in the class
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_name = item.name
                            analysis["methods"].append(method_name)

                            if method_name == "think":
                                analysis["has_think"] = True
                            elif method_name == "act":
                                analysis["has_act"] = True

                            # Count complexity (simple heuristic)
                            analysis["complexity"] += len(item.body)

            elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                if isinstance(node, ast.ImportFrom) and node.module:
                    analysis["imports"].append(node.module)
                    if "llm" in node.module.lower():
                        analysis["has_llm"] = True

        return analysis

    def _determine_level(self, lines: int, analysis: Dict) -> str:
        """Determine implementation level based on analysis"""
        if analysis.get("error"):
            return "error"

        if not analysis.get("has_class"):
            return "none"

        if lines < 100:
            return "stub"

        has_think = analysis.get("has_think", False)
        has_act = analysis.get("has_act", False)
        complexity = analysis.get("complexity", 0)
        methods_count = len(analysis.get("methods", []))

        # More generous classification since these are substantial files
        if has_think and has_act:
            if lines > 600 and complexity > 50:
                return "enhanced"
            elif complexity > 20 or methods_count > 5:
                return "functional"
            else:
                return "partial"
        elif has_think or has_act or methods_count > 3:
            return "partial"
        elif lines > 200:  # Substantial code even without think/act
            return "partial"
        else:
            return "stub"

    def _calculate_complexity(self, analysis: Dict) -> int:
        """Calculate a simple complexity score"""
        score = 0
        score += len(analysis.get("methods", [])) * 2
        score += analysis.get("complexity", 0)
        score += 10 if analysis.get("has_think") else 0
        score += 10 if analysis.get("has_act") else 0
        score += 5 if analysis.get("has_llm") else 0
        return score

    def scan_all_agents(self) -> Dict[str, Dict]:
        """Scan all agent files and return analysis"""
        results = {}

        for py_file in self.agents_dir.rglob("*.py"):
            # Skip __init__.py and other utility files
            if py_file.name.startswith("__"):
                continue

            # Extract agent name from file (remove .py, path info)
            agent_name = py_file.stem

            # Handle enhanced/variant versions
            base_name = (
                agent_name.replace("_enhanced", "")
                .replace("_fresh", "")
                .replace("enhanced_", "")
            )
            base_name = base_name.replace("_", " ").title()

            analysis = self.analyze_agent_file(py_file)
            analysis["agent_name"] = base_name
            analysis["file_variant"] = agent_name

            # Keep the best implementation for each agent
            if (
                base_name not in results
                or analysis["complexity_score"] > results[base_name]["complexity_score"]
            ):
                results[base_name] = analysis

        return results


class AgentStatusUpdater:
    """Updates database agent status based on implementation reality"""

    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.conn = None

    def connect(self):
        """Connect to database"""
        self.conn = psycopg2.connect(**self.db_config)

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def get_current_agent_status(self) -> List[Dict]:
        """Get current agent status from database"""
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT id, name, agent_type, status, development_status,
                   operational_status, created_at, updated_at
            FROM agents
            ORDER BY name
        """
        )

        columns = [desc[0] for desc in cur.description]
        results = []
        for row in cur.fetchall():
            results.append(dict(zip(columns, row)))

        cur.close()
        return results

    def update_agent_status(self, agent_name: str, updates: Dict) -> bool:
        """Update specific agent status"""
        cur = self.conn.cursor()

        # Build UPDATE query dynamically
        set_clauses = []
        values = []

        for field, value in updates.items():
            set_clauses.append(f"{field} = %s")
            values.append(value)

        # Add updated timestamp
        set_clauses.append("updated_at = %s")
        values.append(datetime.now())

        # Add agent name for WHERE clause
        values.append(agent_name)

        query = f"""
            UPDATE agents
            SET {', '.join(set_clauses)}
            WHERE name = %s
        """

        try:
            cur.execute(query, values)
            rows_affected = cur.rowcount
            self.conn.commit()
            cur.close()
            return rows_affected > 0
        except Exception as e:
            print(f"Error updating {agent_name}: {e}")
            self.conn.rollback()
            cur.close()
            return False

    def reset_all_agents_to_planned(self):
        """Reset all agents to realistic 'planned' status"""
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE agents
            SET development_status = 'planned',
                operational_status = 'not_started',
                updated_at = %s
            WHERE development_status != 'planned' OR operational_status != 'not_started'
        """,
            (datetime.now(),),
        )

        rows_affected = cur.rowcount
        self.conn.commit()
        cur.close()

        print(f"✅ Reset {rows_affected} agents to 'planned/not_started' status")
        return rows_affected


def main():
    """Main execution function"""
    print("🔍 Agent Implementation Audit & Database Status Fix")
    print("=" * 60)

    # Setup paths
    project_root = Path(__file__).parent.parent.parent
    agents_dir = project_root / "agents"

    if not agents_dir.exists():
        print(f"❌ Agents directory not found: {agents_dir}")
        return

    # Database configuration
    db_config = {
        "host": "localhost",
        "port": 5434,
        "database": "boarderframeos",
        "user": "boarderframe",
        "password": "boarderframe_secure_2025",
    }

    # Phase 1: Analyze implementation
    print("\n📋 Phase 1: Analyzing Agent Implementations")
    analyzer = AgentImplementationAnalyzer(agents_dir)
    implementations = analyzer.scan_all_agents()

    print(f"Found {len(implementations)} agent implementations:")
    for name, data in implementations.items():
        level = data["implementation_level"]
        lines = data.get("lines_of_code", 0)
        functional = "🟢" if data["is_functional"] else "🔴"
        print(f"  {functional} {name}: {level} ({lines} lines)")

    # Phase 2: Database connection and current status
    print("\n🗄️  Phase 2: Connecting to Database")
    updater = AgentStatusUpdater(db_config)

    try:
        updater.connect()
        current_agents = updater.get_current_agent_status()
        print(f"Found {len(current_agents)} agents in database")

        # Show current status distribution
        status_counts = {}
        for agent in current_agents:
            key = f"{agent['development_status']}/{agent['operational_status']}"
            status_counts[key] = status_counts.get(key, 0) + 1

        print("Current status distribution:")
        for status, count in sorted(
            status_counts.items(), key=lambda x: x[1], reverse=True
        ):
            print(f"  {status}: {count} agents")

        # Phase 3: Reset all to planned
        print("\n🔄 Phase 3: Resetting All Agents to Planned Status")
        reset_count = updater.reset_all_agents_to_planned()

        # Phase 4: Update agents with implementations
        print("\n📝 Phase 4: Updating Agents with Actual Implementations")

        updated_count = 0
        for agent_name, impl_data in implementations.items():
            level = impl_data["implementation_level"]

            # Determine appropriate database status
            if level in ["functional", "enhanced"]:
                dev_status = "in_development"
                op_status = (
                    "not_started"  # Still realistic - none are truly operational
                )
            elif level in ["partial", "stub"]:
                dev_status = "in_development"
                op_status = "not_started"
            else:
                continue  # Keep as planned

            updates = {
                "development_status": dev_status,
                "operational_status": op_status,
            }

            if updater.update_agent_status(agent_name, updates):
                updated_count += 1
                print(f"  ✅ Updated {agent_name}: {dev_status}/{op_status}")
            else:
                print(f"  ❌ Failed to update {agent_name}")

        print(f"\n🎉 Summary:")
        print(f"  - Reset {reset_count} agents to planned status")
        print(f"  - Updated {updated_count} agents with implementations")
        print(f"  - {len(implementations)} agents have Python files")
        print(
            f"  - {sum(1 for impl in implementations.values() if impl['is_functional'])} agents are functional"
        )

        # Show new realistic metrics
        final_agents = updater.get_current_agent_status()
        final_status_counts = {}
        for agent in final_agents:
            key = f"{agent['development_status']}/{agent['operational_status']}"
            final_status_counts[key] = final_status_counts.get(key, 0) + 1

        print(f"\n📊 New Realistic Status Distribution:")
        for status, count in sorted(
            final_status_counts.items(), key=lambda x: x[1], reverse=True
        ):
            print(f"  {status}: {count} agents")

    except Exception as e:
        print(f"❌ Database error: {e}")
    finally:
        updater.close()


if __name__ == "__main__":
    main()

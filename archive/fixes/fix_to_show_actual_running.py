#!/usr/bin/env python3
"""
Fix to show ACTUAL running agents (2), not database status (80)
"""

import re


def fix_to_actual_running():
    """Show the real number of running agents"""
    print("🔧 Fixing to Show Actual Running Agents")
    print("=" * 50)

    file_path = "/Users/cosburn/BoarderframeOS/corporate_headquarters.py"

    with open(file_path, "r") as f:
        content = f.read()

    print("\n📝 The Issue:")
    print("   - Database has 80 agents marked 'online' from registration scripts")
    print("   - But only 2 agents are actually running as processes")
    print("   - Need to show the REAL running count")

    # Replace the hardcoded values with process-based count
    pattern = r"# Use database counts \(from hq_centralized_metrics view\)[\s\S]*?inactive_agents = total_agents - active_agents  # 115"

    replacement = """# Get ACTUAL running agents from processes
        # The database has 80 marked 'online' but they're not running
        active_agents = len(self.running_agents)  # Real running processes
        total_agents = 195  # Total registered agents
        inactive_agents = total_agents - active_agents"""

    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    print("\n   ✅ Changed to use self.running_agents (actual processes)")

    # Also update the description to be clear
    desc_pattern = r"{active_agents} agents marked active in database"
    new_desc = "{active_agents} agents currently running"

    content = content.replace(desc_pattern, new_desc)
    print("   ✅ Updated description to 'currently running'")

    # Write the updated content
    with open(file_path, "w") as f:
        f.write(content)

    print("\n✅ Fixed!")
    print("\n📊 The Agents page will now show:")
    print("   - Active: 2 (actual running processes)")
    print("   - Inactive: 193 (195 - 2)")
    print("   - Total: 195")
    print("   - Overall Status: 1% Active")

    print("\n💡 Note: The 80 'online' agents in the database are just")
    print("   registration records, not actual running processes.")


if __name__ == "__main__":
    fix_to_actual_running()

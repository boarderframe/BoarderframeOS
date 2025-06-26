#!/usr/bin/env python3
"""
Agent Cortex Isolated Launcher - Clean environment startup
Ensures no environment pollution from parent process
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    # Get project root
    project_root = str(Path(__file__).parent.parent)

    # Create a clean environment
    clean_env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "USER": os.environ.get("USER", ""),
        "PYTHONPATH": project_root,
        "FLASK_DEBUG": "0",
        "LANG": os.environ.get("LANG", "en_US.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "en_US.UTF-8"),
    }

    # Find Python executable
    if os.path.exists(os.path.join(project_root, "venv/bin/python")):
        python_exe = os.path.join(project_root, "venv/bin/python")
    elif os.path.exists(os.path.join(project_root, ".venv/bin/python")):
        python_exe = os.path.join(project_root, ".venv/bin/python")
    else:
        python_exe = sys.executable

    # Create the Python code to run inline
    code = """
import sys
sys.path.insert(0, "{project_root}")

from ui.agent_cortex_management import AgentCortexManagementUI

print("🧠 Starting Agent Cortex Management UI (Isolated)")
ui = AgentCortexManagementUI()
print(f"🚀 Agent Cortex UI starting on http://0.0.0.0:{{ui.port}}")
ui.app.run(host="0.0.0.0", port=ui.port, debug=False, use_reloader=False)
""".format(
        project_root=project_root
    )

    # Run Python with clean environment
    subprocess.run([python_exe, "-c", code], env=clean_env, cwd=project_root)


if __name__ == "__main__":
    main()

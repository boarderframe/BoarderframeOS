#!/usr/bin/env python3
"""
BoarderframeOS Log Viewer
Interactive log viewing utility
"""

import os
import sys
import time
from datetime import datetime

def tail_file(filepath, lines=50):
    """Tail a log file"""
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
        
    with open(filepath, 'r') as f:
        # Get last N lines
        file_lines = f.readlines()
        last_lines = file_lines[-lines:]
        
        for line in last_lines:
            print(line.strip())
            
def watch_logs(log_dir):
    """Watch all log files for changes"""
    print(f"Watching logs in {log_dir}...")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            # Clear screen
            os.system('clear' if os.name == 'posix' else 'cls')
            
            print(f"BoarderframeOS Log Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)
            
            # Show recent logs from each category
            log_files = {
                "System": "boarderframeos.log",
                "Errors": "errors/errors.log",
                "Agents": "agents/agents.log",
                "API": "api/api.log"
            }
            
            for category, filename in log_files.items():
                filepath = os.path.join(log_dir, filename)
                if os.path.exists(filepath):
                    print(f"\n[{category}]")
                    tail_file(filepath, 5)
                    
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nStopped watching logs")
        
if __name__ == "__main__":
    log_dir = "logs"
    if len(sys.argv) > 1:
        log_dir = sys.argv[1]
        
    watch_logs(log_dir)

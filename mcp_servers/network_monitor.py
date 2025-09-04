#!/usr/bin/env python3
"""
Network-level monitoring for HTTP requests to port 9004
Captures raw TCP packets for detailed analysis
"""

import subprocess
import threading
import time
import json
import re
from datetime import datetime

class NetworkMonitor:
    def __init__(self, port=9004):
        self.port = port
        self.running = False
        self.log_file = f"/Users/cosburn/MCP Servers/network_monitor_{port}.log"
    
    def start_tcpdump(self):
        """Start tcpdump to capture packets on port 9004"""
        cmd = [
            'tcpdump',
            '-i', 'lo0',  # loopback interface
            '-A',  # ASCII output
            '-s', '0',  # capture full packets
            f'port {self.port}',
            '-l'  # line buffered
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            print(f"🔍 Network monitor started for port {self.port}")
            print(f"📝 Raw packets logged to: {self.log_file}")
            
            with open(self.log_file, 'w') as f:
                f.write(f"Network Monitor Started: {datetime.now().isoformat()}\n")
                f.write(f"Monitoring port: {self.port}\n")
                f.write("="*80 + "\n")
                
                for line in process.stdout:
                    if self.running:
                        timestamp = datetime.now().isoformat()
                        log_line = f"[{timestamp}] {line.strip()}\n"
                        f.write(log_line)
                        f.flush()
                        
                        # Print important packets to console
                        if any(keyword in line for keyword in ['HTTP', 'GET', 'POST', 'Accept:', 'User-Agent:']):
                            print(f"📦 {log_line.strip()}")
        
        except FileNotFoundError:
            print("❌ tcpdump not found. Installing...")
            # Note: tcpdump should be pre-installed on macOS
            print("Please run: sudo tcpdump -i lo0 -A port 9004")
        except Exception as e:
            print(f"❌ Error starting network monitor: {e}")
    
    def start(self):
        """Start monitoring"""
        self.running = True
        monitor_thread = threading.Thread(target=self.start_tcpdump)
        monitor_thread.daemon = True
        monitor_thread.start()
        return monitor_thread
    
    def stop(self):
        """Stop monitoring"""
        self.running = False

def start_simple_packet_monitor():
    """Alternative simple packet monitoring using netstat"""
    print("🔍 Starting simple connection monitor...")
    
    while True:
        try:
            # Monitor connections to port 9004
            result = subprocess.run(['netstat', '-an'], capture_output=True, text=True)
            connections = []
            
            for line in result.stdout.split('\n'):
                if ':9004' in line and 'ESTABLISHED' in line:
                    connections.append(line.strip())
            
            if connections:
                print(f"📡 Active connections to port 9004:")
                for conn in connections:
                    print(f"  {conn}")
                print()
            
            time.sleep(2)
        
        except KeyboardInterrupt:
            print("🛑 Connection monitor stopped")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'simple':
        start_simple_packet_monitor()
    else:
        monitor = NetworkMonitor()
        try:
            thread = monitor.start()
            thread.join()
        except KeyboardInterrupt:
            monitor.stop()
            print("🛑 Network monitor stopped")
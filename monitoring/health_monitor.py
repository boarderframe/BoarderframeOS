#!/usr/bin/env python3
"""
BoarderframeOS Health Monitor
Monitors system and service health
"""

import asyncio
import aiohttp
import psutil
import json
import logging
from datetime import datetime
import socket

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("health_monitor")

class HealthMonitor:
    def __init__(self):
        with open("configs/monitoring/health_config.json", "r") as f:
            self.config = json.load(f)
            
        self.health_status = {
            "system": {},
            "services": {},
            "agents": {},
            "last_check": None
        }
        
    async def check_system_health(self):
        """Check system resource health"""
        try:
            cpu = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            
            self.health_status["system"] = {
                "cpu": {
                    "value": cpu,
                    "healthy": cpu < self.config["checks"]["system"]["cpu_threshold"]
                },
                "memory": {
                    "value": memory,
                    "healthy": memory < self.config["checks"]["system"]["memory_threshold"]
                },
                "disk": {
                    "value": disk,
                    "healthy": disk < self.config["checks"]["system"]["disk_threshold"]
                }
            }
            
            logger.info(f"System health: CPU={cpu}%, Memory={memory}%, Disk={disk}%")
            
        except Exception as e:
            logger.error(f"System health check failed: {e}")
            
    async def check_service_health(self):
        """Check service health"""
        for service in self.config["checks"]["services"]:
            try:
                if service["type"] == "tcp":
                    # TCP port check
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(service["timeout"])
                    result = sock.connect_ex((service["host"], service["port"]))
                    sock.close()
                    
                    self.health_status["services"][service["name"]] = {
                        "healthy": result == 0,
                        "type": "tcp",
                        "port": service["port"]
                    }
                    
                elif service["type"] == "http":
                    # HTTP health check
                    async with aiohttp.ClientSession() as session:
                        try:
                            async with session.get(
                                service["url"],
                                timeout=aiohttp.ClientTimeout(total=service["timeout"])
                            ) as response:
                                self.health_status["services"][service["name"]] = {
                                    "healthy": response.status == 200,
                                    "type": "http",
                                    "status_code": response.status
                                }
                        except Exception:
                            self.health_status["services"][service["name"]] = {
                                "healthy": False,
                                "type": "http",
                                "error": "Connection failed"
                            }
                            
            except Exception as e:
                logger.error(f"Service health check failed for {service['name']}: {e}")
                self.health_status["services"][service["name"]] = {
                    "healthy": False,
                    "error": str(e)
                }
                
    async def check_agent_health(self):
        """Check agent health"""
        # This would check actual agent status via API
        # For now, we'll simulate
        for agent in self.config["checks"]["agents"]:
            self.health_status["agents"][agent] = {
                "healthy": True,  # Would check actual status
                "last_seen": datetime.now().isoformat()
            }
            
    async def run_health_checks(self):
        """Run all health checks"""
        while True:
            # System health
            await self.check_system_health()
            
            # Service health
            await self.check_service_health()
            
            # Agent health
            await self.check_agent_health()
            
            self.health_status["last_check"] = datetime.now().isoformat()
            
            # Save status to file
            with open("monitoring/health/current_status.json", "w") as f:
                json.dump(self.health_status, f, indent=2)
                
            # Wait for next check
            await asyncio.sleep(min(self.config["intervals"].values()))
            
if __name__ == "__main__":
    monitor = HealthMonitor()
    asyncio.run(monitor.run_health_checks())

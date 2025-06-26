#!/usr/bin/env python3
"""
Comprehensive Health Check for BoarderframeOS
Checks all 12 servers and updates system status with accurate health information
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Tuple

import requests

# Complete server list with categories
SERVERS = {
    "Core Infrastructure": {
        "corporate_headquarters": {
            "name": "Corporate Headquarters",
            "port": 8888,
            "url": "http://localhost:8888/health",
            "description": "Main dashboard and control center",
        },
        "agent_cortex": {
            "name": "Agent Cortex Management",
            "port": 8889,
            "url": "http://localhost:8889/health",
            "description": "Model orchestration UI",
        },
        "agent_communication_center": {
            "name": "Agent Communication Center",
            "port": 8890,
            "url": "http://localhost:8890/",
            "description": "Claude-3 powered chat hub",
        },
        "registry": {
            "name": "Registry Server",
            "port": 8000,
            "url": "http://localhost:8000/health",
            "description": "Service discovery and registration",
        },
    },
    "MCP Servers": {
        "filesystem": {
            "name": "Filesystem Server",
            "port": 8001,
            "url": "http://localhost:8001/health",
            "description": "AI-enhanced file operations",
        },
        "database_postgres": {
            "name": "PostgreSQL Database Server",
            "port": 8010,
            "url": "http://localhost:8010/health",
            "description": "Enterprise database operations",
        },
        "analytics": {
            "name": "Analytics Server",
            "port": 8007,
            "url": "http://localhost:8007/health",
            "description": "System metrics and analytics",
        },
        "database_sqlite": {
            "name": "SQLite Database Server",
            "port": 8004,
            "url": "http://localhost:8004/health",
            "description": "Legacy database compatibility",
        },
    },
    "Business Services": {
        "payment": {
            "name": "Payment Server",
            "port": 8006,
            "url": "http://localhost:8006/health",
            "description": "Revenue and billing management",
        },
        "customer": {
            "name": "Customer Server",
            "port": 8008,
            "url": "http://localhost:8008/health",
            "description": "Customer relationship management",
        },
        "screenshot": {
            "name": "Screenshot Server",
            "port": 8011,
            "url": "http://localhost:8011/health",
            "description": "Screenshot capture service",
        },
    },
}


def check_server_health(server_id: str, server_info: dict) -> Dict:
    """Check health of a single server"""
    start_time = time.time()

    try:
        response = requests.get(server_info["url"], timeout=2)
        response_time = int((time.time() - start_time) * 1000)  # in ms

        if response.status_code == 200:
            return {
                "status": "healthy",
                "response_time": response_time,
                "status_code": 200,
                "message": "Server is responding normally",
            }
        else:
            return {
                "status": "degraded",
                "response_time": response_time,
                "status_code": response.status_code,
                "message": f"Server returned status {response.status_code}",
            }
    except requests.exceptions.ConnectionError:
        return {
            "status": "offline",
            "response_time": None,
            "status_code": None,
            "message": "Connection refused - server not running",
        }
    except requests.exceptions.Timeout:
        return {
            "status": "offline",
            "response_time": None,
            "status_code": None,
            "message": "Server timeout - not responding",
        }
    except Exception as e:
        return {
            "status": "offline",
            "response_time": None,
            "status_code": None,
            "message": f"Error: {str(e)}",
        }


def calculate_health_score(results: Dict) -> int:
    """Calculate overall health score with weighted categories"""
    category_weights = {
        "Core Infrastructure": 0.4,  # 40% weight
        "MCP Servers": 0.4,  # 40% weight
        "Business Services": 0.2,  # 20% weight
    }

    weighted_score = 0

    for category, weight in category_weights.items():
        category_servers = results.get(category, {})
        if category_servers:
            healthy_count = sum(
                1 for s in category_servers.values() if s["status"] == "healthy"
            )
            total_count = len(category_servers)
            category_score = (healthy_count / total_count) * 100 * weight
            weighted_score += category_score

    return int(weighted_score)


def main():
    """Run comprehensive health check"""
    print("🏥 BoarderframeOS Comprehensive Health Check\n")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = {}
    total_healthy = 0
    total_servers = 0

    # Check each category
    for category, servers in SERVERS.items():
        print(f"\n📁 {category}:")
        print("─" * 60)

        category_results = {}

        for server_id, server_info in servers.items():
            health = check_server_health(server_id, server_info)
            category_results[server_id] = health

            total_servers += 1
            if health["status"] == "healthy":
                total_healthy += 1
                status_icon = "✅"
                status_color = "\033[92m"  # Green
            elif health["status"] == "degraded":
                status_icon = "⚠️"
                status_color = "\033[93m"  # Yellow
            else:
                status_icon = "❌"
                status_color = "\033[91m"  # Red

            print(
                f"{status_icon} {server_info['name']:30} (port {server_info['port']:<5}) - "
                f"{status_color}{health['status']:>10}\033[0m "
                f"{'(' + str(health['response_time']) + 'ms)' if health['response_time'] else ''}"
            )

            if health["status"] != "healthy":
                print(f"   └─ {health['message']}")

        results[category] = category_results

    # Calculate health score
    health_score = calculate_health_score(results)

    # Summary
    print("\n" + "═" * 60)
    print("📊 SUMMARY")
    print("═" * 60)
    print(f"Total Servers: {total_servers}")
    print(f"Healthy: {total_healthy}")
    print(f"Offline: {total_servers - total_healthy}")
    print(f"Health Score: {health_score}%")

    # Color-coded health assessment
    if health_score >= 90:
        health_status = "\033[92m🟢 EXCELLENT\033[0m"
    elif health_score >= 70:
        health_status = "\033[93m🟡 GOOD\033[0m"
    elif health_score >= 50:
        health_status = "\033[93m🟠 FAIR\033[0m"
    else:
        health_status = "\033[91m🔴 CRITICAL\033[0m"

    print(f"Overall Status: {health_status}")

    # Save results
    output = {
        "timestamp": datetime.now().isoformat(),
        "health_score": health_score,
        "total_servers": total_servers,
        "healthy_servers": total_healthy,
        "offline_servers": total_servers - total_healthy,
        "categories": results,
        "summary": {
            "status": "healthy"
            if health_score >= 70
            else "degraded"
            if health_score >= 50
            else "critical"
        },
    }

    # Update system status
    try:
        with open("/Users/cosburn/BoarderframeOS/data/system_status.json", "r") as f:
            system_status = json.load(f)

        system_status["server_health"] = output
        system_status["last_health_check"] = datetime.now().isoformat()

        with open("/Users/cosburn/BoarderframeOS/data/system_status.json", "w") as f:
            json.dump(system_status, f, indent=2)

        print("\n✅ System status updated")
    except Exception as e:
        print(f"\n⚠️  Failed to update system status: {e}")

    return output


if __name__ == "__main__":
    main()

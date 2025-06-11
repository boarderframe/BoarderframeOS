#!/usr/bin/env python3
"""Test centralized metrics"""
import subprocess

# Test the database view
result = subprocess.run(
    [
        "docker",
        "exec",
        "boarderframeos_postgres",
        "psql",
        "-U",
        "boarderframe",
        "-d",
        "boarderframeos",
        "-t",
        "-c",
        "SELECT total_agents, active_agents, operational_agents, total_departments FROM hq_centralized_metrics;",
    ],
    capture_output=True,
    text=True,
)

if result.returncode == 0:
    parts = result.stdout.strip().split("|")
    print("\n📊 Centralized Metrics Test:")
    print(f"   Total Agents: {parts[0].strip()}")
    print(f"   Active Agents: {parts[1].strip()}")
    print(f"   Operational: {parts[2].strip()}")
    print(f"   Departments: {parts[3].strip()}")
    print("\n✅ Metrics are working!")
else:
    print("❌ Failed to query metrics")

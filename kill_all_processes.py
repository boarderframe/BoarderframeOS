#!/usr/bin/env python3
"""
Kill all BoarderframeOS related processes
"""
import os
import signal
import subprocess
import time

import psutil


def kill_boarderframe_processes():
    """Find and kill all BoarderframeOS related processes"""

    # Keywords to search for in process names/commands
    keywords = [
        "boarderframe",
        "corporate_headquarters",
        "startup.py",
        "solomon",
        "david",
        "mcp",
        "registry_server",
        "filesystem_server",
        "database_server",
        "payment_server",
        "analytics_server",
        "customer_server",
        "agent_cortex",
        "message_bus",
        "boarderframeos",
        "celery",
        "task_queue",
        # "worker",  # Removed - too generic, matches VS Code workers
        "governance",
        "telemetry",
        "health_monitor",
        "hot_reload",
        "blue_green",
        "flower",
        "manage_workers",
    ]
    
    # Process exclusion patterns - don't kill these even if they match keywords
    exclusions = [
        "Visual Studio Code",
        "Code - Insiders",
        "Code Helper",
        "/Applications/Visual Studio",
        # Exclude standalone "claude" (Claude Code CLI) but allow "claude_integration"
        lambda cmd, name: name == "claude" and "boarderframe" not in cmd.lower(),
        "Electron",  # VS Code framework
        "chrome",  # Browser processes
        "chromium",
        "firefox",
        "safari",
        "com.docker",  # Docker processes
        "Docker",  # Docker Desktop
        "docker-proxy",  # Docker proxy
        "containerd",  # Container runtime
    ]

    killed_processes = []

    print("🔍 Searching for BoarderframeOS processes...")

    # First, try to find processes by name
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            # Get process info
            pid = proc.info["pid"]
            name = proc.info["name"]
            cmdline = " ".join(proc.info["cmdline"] or [])

            # Check if process should be excluded
            should_exclude = False
            for exclusion in exclusions:
                if callable(exclusion):
                    # Lambda function exclusion
                    if exclusion(cmdline, name):
                        should_exclude = True
                        break
                else:
                    # String exclusion
                    if exclusion.lower() in name.lower() or exclusion.lower() in cmdline.lower():
                        should_exclude = True
                        break
            
            if should_exclude:
                continue  # Skip this process
            
            # Check if any keyword matches
            for keyword in keywords:
                if (
                    keyword.lower() in name.lower()
                    or keyword.lower() in cmdline.lower()
                ):
                    # Skip this script itself
                    if pid == os.getpid():
                        continue

                    print(f"  Found: PID {pid} - {name} ({cmdline[:50]}...)")

                    try:
                        # Kill the process
                        os.kill(pid, signal.SIGTERM)
                        killed_processes.append((pid, name))
                        print(f"  ✅ Killed PID {pid}")
                    except ProcessLookupError:
                        print(f"  ⚠️  Process {pid} already dead")
                    except PermissionError:
                        print(f"  ❌ Permission denied for PID {pid}")

                    break  # Don't check other keywords for this process

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Also check for processes on specific ports
    ports_to_check = [
        8888,  # Corporate Headquarters
        8889,  # Agent Cortex
        8890,  # Agent Communication Center
        8000,  # Registry
        8001,  # Filesystem
        8004,  # SQLite Database
        8005,  # Agent Cortex API / LLM Server
        8006,  # Payment
        8007,  # Analytics
        8008,  # Customer
        8010,  # PostgreSQL Database
        8011,  # Screenshot
        # 5434,  # PostgreSQL - Don't kill Docker's PostgreSQL
        # 6379,  # Redis - Don't kill Docker's Redis
        5555,  # Celery Flower
    ]

    print(f"\n🔍 Checking processes on BoarderframeOS ports...")

    for port in ports_to_check:
        try:
            # Find process using the port
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"], capture_output=True, text=True
            )

            if result.stdout.strip():
                pids = result.stdout.strip().split("\n")
                for pid in pids:
                    try:
                        pid_int = int(pid)
                        # Get process name
                        proc = psutil.Process(pid_int)
                        name = proc.name()

                        print(f"  Found on port {port}: PID {pid_int} - {name}")

                        # Kill the process
                        os.kill(pid_int, signal.SIGTERM)
                        killed_processes.append((pid_int, f"{name} (port {port})"))
                        print(f"  ✅ Killed PID {pid_int}")

                    except (ProcessLookupError, psutil.NoSuchProcess):
                        print(f"  ⚠️  Process {pid} already dead")
                    except PermissionError:
                        print(f"  ❌ Permission denied for PID {pid}")
                    except ValueError:
                        pass

        except subprocess.CalledProcessError:
            pass
        except FileNotFoundError:
            print("  ⚠️  lsof command not found, skipping port checks")
            break

    # Kill any remaining Python processes that might be BoarderframeOS related
    print(f"\n🔍 Checking for stray Python processes...")

    try:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)

        for line in result.stdout.split("\n"):
            if "python" in line and any(kw in line.lower() for kw in keywords):
                parts = line.split()
                if len(parts) > 1:
                    pid = parts[1]
                    try:
                        pid_int = int(pid)
                        if pid_int != os.getpid():  # Don't kill self
                            print(f"  Found stray process: PID {pid_int}")
                            os.kill(pid_int, signal.SIGTERM)
                            killed_processes.append(
                                (pid_int, "Python BoarderframeOS process")
                            )
                            print(f"  ✅ Killed PID {pid_int}")
                    except (ValueError, ProcessLookupError, PermissionError):
                        pass

    except subprocess.CalledProcessError:
        pass

    # Give processes time to die
    if killed_processes:
        print("\n⏳ Waiting for processes to terminate...")
        time.sleep(2)

        # Force kill any that didn't die gracefully
        for pid, name in killed_processes:
            try:
                os.kill(pid, signal.SIGKILL)
                print(f"  🔨 Force killed PID {pid} - {name}")
            except ProcessLookupError:
                pass  # Already dead
            except PermissionError:
                print(
                    f"  ❌ Could not force kill PID {pid} - {name} (permission denied)"
                )

    # Summary
    print(f"\n{'='*50}")
    if killed_processes:
        print(f"✅ Killed {len(killed_processes)} BoarderframeOS processes")
        print("\nKilled processes:")
        for pid, name in killed_processes:
            print(f"  - PID {pid}: {name}")
    else:
        print("✅ No BoarderframeOS processes found running")

    print(f"\n💡 You can now run: python startup.py")
    print("{'='*50}\n")


if __name__ == "__main__":
    kill_boarderframe_processes()

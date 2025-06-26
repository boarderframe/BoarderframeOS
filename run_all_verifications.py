#!/usr/bin/env python3
"""
BoarderframeOS Master Verification Runner
Executes all verification scripts and generates comprehensive report
"""

import asyncio
import subprocess
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class MasterVerificationRunner:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.verification_scripts = [
            {
                "name": "Docker Services",
                "script": "verify_docker_services.py",
                "description": "PostgreSQL and Redis infrastructure",
                "critical": True,
                "async": False
            },
            {
                "name": "MCP Servers",
                "script": "verify_mcp_servers.py",
                "description": "All 9 MCP server health checks",
                "critical": True,
                "async": True
            },
            {
                "name": "Message Bus",
                "script": "verify_message_bus.py",
                "description": "Inter-agent communication system",
                "critical": True,
                "async": True
            },
            {
                "name": "Corporate HQ",
                "script": "verify_corporate_hq.py",
                "description": "Corporate HQ UI functionality and APIs",
                "critical": True,
                "async": True
            },
            {
                "name": "Agents",
                "script": "verify_agents.py",
                "description": "All 5 implemented agents (Solomon, David, Adam, Eve, Bezalel)",
                "critical": False,
                "async": True
            },
            {
                "name": "UI Components",
                "script": "verify_ui_components.py",
                "description": "All UI systems (Corporate HQ, Agent Cortex, ACC)",
                "critical": False,
                "async": True
            },
            {
                "name": "Integration Tests",
                "script": "verify_integration.py",
                "description": "End-to-end workflows and system integration",
                "critical": False,
                "async": True
            },
            {
                "name": "Performance Analysis",
                "script": "analyze_performance.py",
                "description": "System performance analysis and optimization",
                "critical": False,
                "async": True
            },
            {
                "name": "Monitoring Setup",
                "script": "setup_monitoring.py",
                "description": "Configure logging, metrics, health monitoring, and alerts",
                "critical": False,
                "async": False
            }
        ]
        
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "system": "BoarderframeOS",
            "verifications": {},
            "summary": {},
            "recommendations": []
        }
        
    def log(self, message: str, level: str = "INFO"):
        """Log with timestamp and level"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "ℹ️ ",
            "SUCCESS": "✅",
            "WARNING": "⚠️ ",
            "ERROR": "❌"
        }.get(level, "")
        
        print(f"[{timestamp}] {prefix} {message}")
        
    def run_sync_script(self, script_path: str) -> Tuple[bool, Dict]:
        """Run a synchronous Python script"""
        self.log(f"Running {script_path}...")
        
        try:
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            success = result.returncode == 0
            
            # Try to find and load the JSON report
            report_data = self.load_script_report(script_path)
            
            return success, {
                "success": success,
                "exit_code": result.returncode,
                "stdout": result.stdout if self.verbose else None,
                "stderr": result.stderr if not success else None,
                "report": report_data
            }
            
        except subprocess.TimeoutExpired:
            self.log(f"{script_path} timed out", "ERROR")
            return False, {"success": False, "error": "Script timed out after 120 seconds"}
        except Exception as e:
            self.log(f"Error running {script_path}: {e}", "ERROR")
            return False, {"success": False, "error": str(e)}
            
    async def run_async_script(self, script_path: str) -> Tuple[bool, Dict]:
        """Run an asynchronous Python script"""
        self.log(f"Running async {script_path}...")
        
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=120
            )
            
            success = proc.returncode == 0
            
            # Try to find and load the JSON report
            report_data = self.load_script_report(script_path)
            
            return success, {
                "success": success,
                "exit_code": proc.returncode,
                "stdout": stdout.decode() if self.verbose else None,
                "stderr": stderr.decode() if not success else None,
                "report": report_data
            }
            
        except asyncio.TimeoutError:
            self.log(f"{script_path} timed out", "ERROR")
            return False, {"success": False, "error": "Script timed out after 120 seconds"}
        except Exception as e:
            self.log(f"Error running {script_path}: {e}", "ERROR")
            return False, {"success": False, "error": str(e)}
            
    def load_script_report(self, script_path: str) -> Optional[Dict]:
        """Load JSON report generated by a verification script"""
        # Common report file patterns
        script_name = Path(script_path).stem
        report_patterns = [
            f"{script_name}_report.json",
            script_name.replace("verify_", "") + "_report.json",
            script_name.replace("verify_", "") + "_services_report.json"
        ]
        
        for pattern in report_patterns:
            if os.path.exists(pattern):
                try:
                    with open(pattern, 'r') as f:
                        return json.load(f)
                except Exception as e:
                    self.log(f"Could not load report {pattern}: {e}", "WARNING")
                    
        return None
        
    def analyze_results(self):
        """Analyze all verification results"""
        total_scripts = len(self.verification_scripts)
        successful = sum(
            1 for v in self.results["verifications"].values()
            if v.get("success", False)
        )
        critical_failures = sum(
            1 for script in self.verification_scripts
            if script["critical"] and not self.results["verifications"].get(script["name"], {}).get("success", False)
        )
        
        # Analyze specific components
        docker_healthy = self.results["verifications"].get("Docker Services", {}).get("success", False)
        mcp_report = self.results["verifications"].get("MCP Servers", {}).get("report", {})
        mcp_healthy = mcp_report.get("summary", {}).get("healthy", 0) if mcp_report else 0
        mcp_total = mcp_report.get("summary", {}).get("total_servers", 9) if mcp_report else 9
        
        message_bus_report = self.results["verifications"].get("Message Bus", {}).get("report", {})
        message_bus_healthy = message_bus_report.get("summary", {}).get("success_rate", 0) > 80 if message_bus_report else False
        
        # Generate summary
        self.results["summary"] = {
            "total_verifications": total_scripts,
            "successful": successful,
            "failed": total_scripts - successful,
            "critical_failures": critical_failures,
            "success_rate": round((successful / total_scripts) * 100, 1),
            "infrastructure_status": "healthy" if docker_healthy else "unhealthy",
            "mcp_servers_healthy": f"{mcp_healthy}/{mcp_total}",
            "message_bus_status": "healthy" if message_bus_healthy else "unhealthy",
            "overall_health": self.calculate_overall_health()
        }
        
        # Generate recommendations
        self.generate_recommendations()
        
    def calculate_overall_health(self) -> str:
        """Calculate overall system health"""
        critical_ok = all(
            self.results["verifications"].get(script["name"], {}).get("success", False)
            for script in self.verification_scripts
            if script["critical"]
        )
        
        if not critical_ok:
            return "critical"
            
        success_rate = self.results["summary"]["success_rate"]
        if success_rate >= 90:
            return "healthy"
        elif success_rate >= 70:
            return "warning"
        else:
            return "unhealthy"
            
    def generate_recommendations(self):
        """Generate actionable recommendations based on results"""
        recommendations = []
        
        # Check Docker services
        docker_result = self.results["verifications"].get("Docker Services", {})
        if not docker_result.get("success", False):
            recommendations.append({
                "priority": "HIGH",
                "component": "Docker Services",
                "issue": "Docker services are not running properly",
                "action": "Run 'docker-compose up -d postgresql redis' to start services"
            })
            
        # Check MCP servers
        mcp_report = self.results["verifications"].get("MCP Servers", {}).get("report", {})
        if mcp_report:
            offline_servers = mcp_report.get("summary", {}).get("offline", 0)
            if offline_servers > 0:
                recommendations.append({
                    "priority": "HIGH",
                    "component": "MCP Servers",
                    "issue": f"{offline_servers} MCP servers are offline",
                    "action": "Run './start_offline_mcp_servers.sh' to start them"
                })
                
        # Check message bus
        mb_report = self.results["verifications"].get("Message Bus", {}).get("report", {})
        if mb_report and mb_report.get("performance", {}).get("throughput_per_second", 0) < 1000:
            recommendations.append({
                "priority": "MEDIUM",
                "component": "Message Bus",
                "issue": "Message bus throughput is below target",
                "action": "Check Redis connection and optimize message serialization"
            })
            
        self.results["recommendations"] = recommendations
        
    def generate_html_report(self):
        """Generate an HTML report of results"""
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>BoarderframeOS Verification Report</title>
    <style>
        body {{
            font-family: -apple-system, sans-serif;
            background: #0a0a0a;
            color: #e0e0e0;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            background: linear-gradient(45deg, #00ff88, #0088ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            font-size: 3em;
        }}
        .summary {{
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 20px;
            margin: 20px 0;
        }}
        .health-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
        }}
        .healthy {{ background: #00ff88; color: #000; }}
        .warning {{ background: #ffc107; color: #000; }}
        .critical {{ background: #ff0088; color: #fff; }}
        .verification-item {{
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
        }}
        .success {{ border-color: #00ff88; }}
        .failed {{ border-color: #ff0088; }}
        .recommendation {{
            background: rgba(255,193,7,0.1);
            border: 1px solid #ffc107;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
        }}
        .metric {{
            display: inline-block;
            margin: 0 20px 10px 0;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #00ff88;
        }}
        .metric-label {{
            color: #888;
            font-size: 0.9em;
        }}
        pre {{
            background: #000;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>BoarderframeOS Verification Report</h1>
        <p style="text-align: center; color: #888;">Generated: {self.results['timestamp']}</p>
        
        <div class="summary">
            <h2>System Health: <span class="health-badge {self.results['summary']['overall_health']}">{self.results['summary']['overall_health'].upper()}</span></h2>
            
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value">{self.results['summary']['success_rate']}%</div>
                    <div class="metric-label">Success Rate</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{self.results['summary']['successful']}/{self.results['summary']['total_verifications']}</div>
                    <div class="metric-label">Tests Passed</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{self.results['summary']['mcp_servers_healthy']}</div>
                    <div class="metric-label">MCP Servers</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{self.results['summary']['infrastructure_status']}</div>
                    <div class="metric-label">Infrastructure</div>
                </div>
            </div>
        </div>
        
        <h2>Verification Results</h2>
"""
        
        for script in self.verification_scripts:
            result = self.results["verifications"].get(script["name"], {})
            status_class = "success" if result.get("success", False) else "failed"
            status_text = "✅ PASSED" if result.get("success", False) else "❌ FAILED"
            
            html_content += f"""
        <div class="verification-item {status_class}">
            <h3>{script['name']} - {status_text}</h3>
            <p>{script['description']}</p>
"""
            
            if result.get("report") and result["report"].get("summary"):
                summary = result["report"]["summary"]
                html_content += "<h4>Details:</h4><ul>"
                for key, value in summary.items():
                    if key not in ["success_messages", "warning_messages", "error_messages"]:
                        html_content += f"<li><strong>{key}:</strong> {value}</li>"
                html_content += "</ul>"
                
            if result.get("error"):
                html_content += f"<p style='color: #ff0088;'>Error: {result['error']}</p>"
                
            html_content += "</div>"
            
        if self.results["recommendations"]:
            html_content += "<h2>Recommendations</h2>"
            for rec in self.results["recommendations"]:
                html_content += f"""
        <div class="recommendation">
            <h4>[{rec['priority']}] {rec['component']}</h4>
            <p><strong>Issue:</strong> {rec['issue']}</p>
            <p><strong>Action:</strong> <code>{rec['action']}</code></p>
        </div>
"""
        
        html_content += """
        <h2>Next Steps</h2>
        <ol>
            <li>Address any HIGH priority recommendations first</li>
            <li>Start all offline services using the provided commands</li>
            <li>Re-run failed verifications after fixes</li>
            <li>Check individual JSON reports for detailed information</li>
        </ol>
        
        <p style="text-align: center; margin-top: 40px; color: #666;">
            BoarderframeOS - Building a digital civilization with 120+ AI agents
        </p>
    </div>
</body>
</html>"""
        
        with open("verification_report.html", "w") as f:
            f.write(html_content)
            
        self.log("HTML report generated: verification_report.html", "SUCCESS")
        
    async def run_all_verifications(self):
        """Run all verification scripts"""
        print("="*60)
        print("BoarderframeOS Master Verification Runner")
        print("="*60)
        print(f"Running {len(self.verification_scripts)} verification scripts...\n")
        
        start_time = time.time()
        
        # Run each verification
        for script in self.verification_scripts:
            script_path = script["script"]
            
            if not os.path.exists(script_path):
                self.log(f"Script not found: {script_path}", "ERROR")
                self.results["verifications"][script["name"]] = {
                    "success": False,
                    "error": "Script file not found"
                }
                continue
                
            if script["async"]:
                success, result = await self.run_async_script(script_path)
            else:
                success, result = self.run_sync_script(script_path)
                
            self.results["verifications"][script["name"]] = result
            
            if success:
                self.log(f"{script['name']} completed successfully", "SUCCESS")
            else:
                self.log(f"{script['name']} failed", "ERROR")
                
        # Analyze results
        self.analyze_results()
        
        # Save JSON report
        with open("master_verification_report.json", "w") as f:
            json.dump(self.results, f, indent=2)
            
        # Generate HTML report
        self.generate_html_report()
        
        # Print summary
        duration = time.time() - start_time
        print("\n" + "="*60)
        print("VERIFICATION COMPLETE")
        print("="*60)
        print(f"Duration: {duration:.1f} seconds")
        print(f"Overall Health: {self.results['summary']['overall_health'].upper()}")
        print(f"Success Rate: {self.results['summary']['success_rate']}%")
        print(f"Critical Failures: {self.results['summary']['critical_failures']}")
        
        if self.results["recommendations"]:
            print(f"\n⚠️  {len(self.results['recommendations'])} recommendations generated")
            print("See verification_report.html for details")
            
        print("\nReports generated:")
        print("  - master_verification_report.json")
        print("  - verification_report.html")
        
        # Return success if no critical failures
        return self.results["summary"]["critical_failures"] == 0


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Run all BoarderframeOS verifications")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed output")
    args = parser.parse_args()
    
    runner = MasterVerificationRunner(verbose=args.verbose)
    success = await runner.run_all_verifications()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
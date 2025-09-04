#!/usr/bin/env python3
"""
Comprehensive Bug Detection Script for MCP-UI Ecosystem
Identifies and categorizes all system issues
"""

import asyncio
import json
import os
import psutil
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BugDetector:
    def __init__(self):
        self.base_dir = Path("/Users/cosburn/MCP Servers")
        self.bugs = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }
        self.services = {
            "main_api": "http://localhost:8000",
            "frontend": "http://localhost:3001",
            "kroger_mcp": "http://localhost:9005",
            "playwright": "http://localhost:9001"
        }
        
    def detect_all_bugs(self):
        """Main entry point for bug detection"""
        print("\n" + "="*80)
        print("MCP-UI ECOSYSTEM COMPREHENSIVE BUG DETECTION")
        print("="*80 + "\n")
        
        # 1. Service Health Check
        self.check_service_health()
        
        # 2. Configuration Issues
        self.check_configuration_issues()
        
        # 3. Code Quality Issues
        self.check_code_quality()
        
        # 4. Security Vulnerabilities
        self.check_security_issues()
        
        # 5. Performance Issues
        self.check_performance_issues()
        
        # 6. Integration Issues
        self.check_integration_issues()
        
        # 7. Log Analysis
        self.analyze_logs()
        
        # 8. Resource Leaks
        self.check_resource_leaks()
        
        # 9. Test Coverage
        self.check_test_coverage()
        
        # Generate Report
        self.generate_report()
        
    def check_service_health(self):
        """Check health of all services"""
        print("\n[1/9] Checking Service Health...")
        
        for service_name, url in self.services.items():
            try:
                # Check main endpoint
                response = requests.get(f"{url}/health", timeout=2)
                if response.status_code != 200:
                    self.add_bug("high", f"{service_name}: Health endpoint returns {response.status_code}")
            except requests.exceptions.ConnectionError:
                self.add_bug("critical", f"{service_name}: Service not responding at {url}")
            except requests.exceptions.Timeout:
                self.add_bug("high", f"{service_name}: Service timeout at {url}")
                
        # Check for zombie processes
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'python' in proc.info['name'] and 'mcp' in str(proc.info.get('cmdline', '')):
                    # Check if process is responsive
                    if proc.status() == 'zombie':
                        self.add_bug("high", f"Zombie process detected: PID {proc.info['pid']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
    def check_configuration_issues(self):
        """Check for configuration problems"""
        print("\n[2/9] Checking Configuration Issues...")
        
        # Check environment variables
        required_env_vars = ['DATABASE_URL', 'JWT_SECRET_KEY', 'MCP_CONFIG_PATH']
        env_file = self.base_dir / '.env'
        
        if not env_file.exists():
            self.add_bug("critical", ".env file missing - configuration not loaded")
        else:
            with open(env_file) as f:
                env_content = f.read()
                for var in required_env_vars:
                    if var not in env_content:
                        self.add_bug("high", f"Missing required environment variable: {var}")
                        
        # Check config files
        config_files = [
            'config/mcp.json',
            'frontend/package.json',
            'docker/docker-compose.yml'
        ]
        
        for config_file in config_files:
            file_path = self.base_dir / config_file
            if not file_path.exists():
                self.add_bug("high", f"Missing configuration file: {config_file}")
            else:
                # Check for JSON validity
                if config_file.endswith('.json'):
                    try:
                        with open(file_path) as f:
                            json.load(f)
                    except json.JSONDecodeError as e:
                        self.add_bug("critical", f"Invalid JSON in {config_file}: {e}")
                        
    def check_code_quality(self):
        """Check for code quality issues"""
        print("\n[3/9] Checking Code Quality...")
        
        # Check for import errors
        python_files = list(self.base_dir.glob("**/*.py"))
        for py_file in python_files[:50]:  # Limit for performance
            if 'venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(py_file)],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                if result.returncode != 0:
                    self.add_bug("medium", f"Syntax error in {py_file.name}: {result.stderr[:100]}")
            except subprocess.TimeoutExpired:
                self.add_bug("low", f"Compilation timeout for {py_file.name}")
                
        # Check for deprecated patterns
        deprecated_patterns = [
            (r'@validator\(', "Pydantic V1 validators deprecated"),
            (r'async def .+\(\):', "Missing type hints in async functions"),
            (r'except Exception:', "Broad exception handling")
        ]
        
        for py_file in python_files[:20]:
            if 'venv' in str(py_file):
                continue
            try:
                with open(py_file) as f:
                    content = f.read()
                    for pattern, message in deprecated_patterns:
                        if re.search(pattern, content):
                            self.add_bug("medium", f"{message} in {py_file.name}")
            except Exception:
                pass
                
    def check_security_issues(self):
        """Check for security vulnerabilities"""
        print("\n[4/9] Checking Security Issues...")
        
        # Check for hardcoded secrets
        secret_patterns = [
            (r'(api_key|apikey|api-key)\s*=\s*["\'][^"\']+["\']', "Hardcoded API key"),
            (r'(password|passwd|pwd)\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
            (r'(secret|token)\s*=\s*["\'][^"\']+["\']', "Hardcoded secret/token")
        ]
        
        for py_file in list(self.base_dir.glob("**/*.py"))[:20]:
            if 'venv' in str(py_file) or 'test' in str(py_file):
                continue
            try:
                with open(py_file) as f:
                    content = f.read()
                    for pattern, message in secret_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            self.add_bug("critical", f"{message} found in {py_file.name}")
            except Exception:
                pass
                
        # Check for CORS issues
        main_api_file = self.base_dir / "src/app/main.py"
        if main_api_file.exists():
            with open(main_api_file) as f:
                content = f.read()
                if 'allow_origins=["*"]' in content:
                    self.add_bug("high", "CORS allowing all origins - security risk")
                    
    def check_performance_issues(self):
        """Check for performance problems"""
        print("\n[5/9] Checking Performance Issues...")
        
        # Check memory usage of running processes
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                if 'python' in proc.info['name']:
                    mem_mb = proc.info['memory_info'].rss / 1024 / 1024
                    if mem_mb > 500:
                        self.add_bug("high", f"High memory usage: {proc.info['name']} using {mem_mb:.1f}MB")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
        # Check for N+1 queries in code
        orm_files = list(self.base_dir.glob("**/services/*.py"))
        for orm_file in orm_files[:10]:
            try:
                with open(orm_file) as f:
                    content = f.read()
                    # Simple heuristic for N+1 queries
                    if 'for ' in content and '.query(' in content:
                        if content.count('.query(') > 3:
                            self.add_bug("medium", f"Potential N+1 query pattern in {orm_file.name}")
            except Exception:
                pass
                
    def check_integration_issues(self):
        """Check for integration problems"""
        print("\n[6/9] Checking Integration Issues...")
        
        # Check API endpoint consistency
        try:
            # Test trailing slash redirect issue
            response1 = requests.get("http://localhost:8000/api/v1/health", allow_redirects=False, timeout=1)
            response2 = requests.get("http://localhost:8000/api/v1/health/", allow_redirects=False, timeout=1)
            
            if response1.status_code == 307:
                self.add_bug("medium", "API endpoints redirecting due to trailing slash inconsistency")
                
            # Test missing endpoints
            missing_endpoints = []
            expected_endpoints = ['/api/v1/metrics', '/api/v1/cache/clear', '/api/v1/logs']
            for endpoint in expected_endpoints:
                try:
                    resp = requests.get(f"http://localhost:8000{endpoint}", timeout=1)
                    if resp.status_code == 404:
                        missing_endpoints.append(endpoint)
                except:
                    pass
                    
            if missing_endpoints:
                self.add_bug("high", f"Missing API endpoints: {', '.join(missing_endpoints)}")
                
        except Exception as e:
            self.add_bug("high", f"Cannot test API integration: {str(e)}")
            
    def analyze_logs(self):
        """Analyze application logs for errors"""
        print("\n[7/9] Analyzing Logs...")
        
        log_dir = self.base_dir / "logs"
        if log_dir.exists():
            for log_file in log_dir.glob("*.log"):
                try:
                    with open(log_file) as f:
                        content = f.read()
                        
                        # Count error types
                        error_count = content.count("ERROR")
                        warning_count = content.count("WARNING")
                        traceback_count = content.count("Traceback")
                        
                        if error_count > 10:
                            self.add_bug("high", f"{log_file.name}: {error_count} errors found")
                        if traceback_count > 0:
                            self.add_bug("critical", f"{log_file.name}: {traceback_count} tracebacks found")
                        if warning_count > 50:
                            self.add_bug("medium", f"{log_file.name}: {warning_count} warnings found")
                            
                        # Check for specific error patterns
                        if "Connection refused" in content:
                            self.add_bug("high", f"{log_file.name}: Connection refused errors")
                        if "Timeout" in content:
                            self.add_bug("medium", f"{log_file.name}: Timeout errors")
                        if "DeprecationWarning" in content:
                            self.add_bug("low", f"{log_file.name}: Deprecation warnings")
                            
                except Exception as e:
                    self.add_bug("low", f"Cannot read log file {log_file.name}: {e}")
                    
    def check_resource_leaks(self):
        """Check for resource leaks"""
        print("\n[8/9] Checking Resource Leaks...")
        
        # Check for unclosed files
        open_files = []
        for proc in psutil.process_iter(['pid', 'name', 'open_files']):
            try:
                if 'python' in proc.info['name']:
                    files = proc.open_files()
                    if len(files) > 100:
                        self.add_bug("high", f"Process {proc.info['pid']} has {len(files)} open files")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
        # Check for database connection leaks
        try:
            # Simple check for connection pool exhaustion
            response = requests.get("http://localhost:8000/api/v1/health/", timeout=1)
            if response.status_code == 200:
                # Make multiple concurrent requests
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                    futures = [executor.submit(requests.get, "http://localhost:8000/api/v1/servers/", timeout=1) 
                              for _ in range(10)]
                    results = [f.result() for f in concurrent.futures.as_completed(futures, timeout=5)]
                    
                    failed = sum(1 for r in results if r.status_code != 200)
                    if failed > 2:
                        self.add_bug("high", f"Connection pool exhaustion: {failed}/10 requests failed")
        except Exception:
            pass
            
    def check_test_coverage(self):
        """Check test coverage and test issues"""
        print("\n[9/9] Checking Test Coverage...")
        
        # Check for missing test dependencies
        missing_deps = []
        test_deps = ['testcontainers', 'pytest-benchmark']
        
        for dep in test_deps:
            try:
                __import__(dep.replace('-', '_'))
            except ImportError:
                missing_deps.append(dep)
                
        if missing_deps:
            self.add_bug("medium", f"Missing test dependencies: {', '.join(missing_deps)}")
            
        # Check for test failures
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "--co", "-q"],
                capture_output=True,
                text=True,
                cwd=self.base_dir,
                timeout=5
            )
            
            if "error" in result.stdout.lower() or "error" in result.stderr.lower():
                error_count = result.stdout.count("ERROR") + result.stderr.count("ERROR")
                self.add_bug("high", f"Test collection errors: {error_count} modules cannot be imported")
                
        except subprocess.TimeoutExpired:
            self.add_bug("medium", "Test discovery timeout")
        except Exception as e:
            self.add_bug("low", f"Cannot run test discovery: {e}")
            
    def add_bug(self, severity: str, description: str):
        """Add a bug to the collection"""
        bug = {
            "timestamp": datetime.now().isoformat(),
            "description": description,
            "severity": severity
        }
        self.bugs[severity].append(bug)
        
        # Print immediate feedback
        severity_symbol = {
            "critical": "🔴",
            "high": "🟠", 
            "medium": "🟡",
            "low": "🔵"
        }
        print(f"  {severity_symbol[severity]} [{severity.upper()}] {description}")
        
    def generate_report(self):
        """Generate comprehensive bug report"""
        print("\n" + "="*80)
        print("BUG DETECTION SUMMARY")
        print("="*80)
        
        total_bugs = sum(len(bugs) for bugs in self.bugs.values())
        
        print(f"\nTotal Issues Found: {total_bugs}")
        print(f"  - Critical: {len(self.bugs['critical'])}")
        print(f"  - High:     {len(self.bugs['high'])}")
        print(f"  - Medium:   {len(self.bugs['medium'])}")
        print(f"  - Low:      {len(self.bugs['low'])}")
        
        # Save detailed report
        report = {
            "scan_timestamp": datetime.now().isoformat(),
            "total_issues": total_bugs,
            "issues_by_severity": self.bugs,
            "recommendations": self.generate_recommendations()
        }
        
        report_file = self.base_dir / "bug_detection_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\nDetailed report saved to: {report_file}")
        
        # Print critical issues
        if self.bugs['critical']:
            print("\n🔴 CRITICAL ISSUES REQUIRING IMMEDIATE ATTENTION:")
            for bug in self.bugs['critical']:
                print(f"  - {bug['description']}")
                
    def generate_recommendations(self):
        """Generate fix recommendations based on bugs found"""
        recommendations = []
        
        if any("Missing required environment variable" in bug['description'] for bug in self.bugs['high']):
            recommendations.append("Create proper .env file with all required variables")
            
        if any("Service not responding" in bug['description'] for bug in self.bugs['critical']):
            recommendations.append("Restart failed services and check startup logs")
            
        if any("trailing slash" in bug['description'] for bug in self.bugs['medium']):
            recommendations.append("Standardize API endpoint definitions to avoid trailing slash issues")
            
        if any("Missing test dependencies" in bug['description'] for bug in self.bugs['medium']):
            recommendations.append("Install missing test dependencies: pip install testcontainers pytest-benchmark")
            
        if any("Hardcoded" in bug['description'] for bug in self.bugs['critical']):
            recommendations.append("Move all secrets to environment variables")
            
        if any("High memory usage" in bug['description'] for bug in self.bugs['high']):
            recommendations.append("Investigate memory leaks and optimize resource usage")
            
        return recommendations

if __name__ == "__main__":
    detector = BugDetector()
    detector.detect_all_bugs()
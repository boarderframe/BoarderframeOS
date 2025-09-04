#!/usr/bin/env python3
"""
Comprehensive Test Runner for Kroger MCP Authentication System.

This script provides multiple test execution modes for the Kroger authentication system:
1. Unit tests for token lifecycle and management
2. Integration tests with real server interactions
3. End-to-end tests simulating complete LLM workflows
4. Performance tests under various load conditions
5. Security tests for authentication vulnerabilities

Usage:
    python run_kroger_auth_tests.py [OPTIONS]

Examples:
    # Run all tests
    python run_kroger_auth_tests.py --all

    # Run only unit tests
    python run_kroger_auth_tests.py --unit

    # Run integration tests with real server
    python run_kroger_auth_tests.py --integration --server-url http://localhost:9004

    # Run E2E LLM workflow tests
    python run_kroger_auth_tests.py --e2e --llm-workflows

    # Run performance tests
    python run_kroger_auth_tests.py --performance --concurrent-users 10

    # Run with coverage report
    python run_kroger_auth_tests.py --unit --coverage

    # Run specific test categories
    python run_kroger_auth_tests.py --categories "token_lifecycle,cart_auth,error_handling"
"""

import argparse
import os
import sys
import subprocess
import time
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

import requests


class KrogerAuthTestRunner:
    """Main test runner for Kroger authentication tests."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_dir = self.project_root / "tests"
        self.results_dir = self.project_root / "test-results"
        self.server_url = "http://localhost:9004"
        self.verbose = False
        self.coverage = False
        
        # Create results directory if it doesn't exist
        self.results_dir.mkdir(exist_ok=True)
    
    def check_server_health(self, url: str = None) -> bool:
        """Check if Kroger MCP server is running and healthy."""
        if url is None:
            url = self.server_url
        
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                return health_data.get("status") == "healthy"
            return False
        except Exception as e:
            if self.verbose:
                print(f"Server health check failed: {e}")
            return False
    
    def wait_for_server(self, url: str = None, timeout: int = 30) -> bool:
        """Wait for server to become available."""
        if url is None:
            url = self.server_url
        
        print(f"Waiting for server at {url} to become available...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.check_server_health(url):
                print(f"Server is healthy and ready!")
                return True
            time.sleep(2)
            print(".", end="", flush=True)
        
        print(f"\nServer did not become available within {timeout} seconds")
        return False
    
    def run_pytest_command(self, test_paths: List[str], markers: List[str] = None, 
                          additional_args: List[str] = None) -> Dict[str, Any]:
        """Run pytest with specified parameters."""
        cmd = ["python", "-m", "pytest"]
        
        # Add test paths
        cmd.extend(test_paths)
        
        # Add markers
        if markers:
            for marker in markers:
                cmd.extend(["-m", marker])
        
        # Add verbosity
        if self.verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")
        
        # Add coverage if requested
        if self.coverage:
            cmd.extend([
                "--cov=kroger_mcp_server",
                "--cov=tests",
                "--cov-report=html",
                "--cov-report=term-missing",
                f"--cov-report=json:{self.results_dir}/coverage.json"
            ])
        
        # Add junit XML output
        cmd.extend(["--junit-xml", str(self.results_dir / "test_results.xml")])
        
        # Add additional arguments
        if additional_args:
            cmd.extend(additional_args)
        
        # Set environment variables
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.project_root)
        
        print(f"Running command: {' '.join(cmd)}")
        
        start_time = time.time()
        result = subprocess.run(cmd, cwd=self.project_root, env=env, capture_output=True, text=True)
        execution_time = time.time() - start_time
        
        return {
            "command": " ".join(cmd),
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
    
    def run_unit_tests(self) -> Dict[str, Any]:
        """Run comprehensive unit tests."""
        print("\n" + "="*60)
        print("RUNNING UNIT TESTS")
        print("="*60)
        
        test_files = [
            str(self.test_dir / "unit" / "test_kroger_auth_comprehensive.py")
        ]
        
        markers = ["unit"]
        
        return self.run_pytest_command(test_files, markers)
    
    def run_integration_tests(self, require_server: bool = True) -> Dict[str, Any]:
        """Run integration tests."""
        print("\n" + "="*60)
        print("RUNNING INTEGRATION TESTS")
        print("="*60)
        
        if require_server and not self.check_server_health():
            if not self.wait_for_server():
                return {
                    "error": "Server not available for integration tests",
                    "exit_code": 1,
                    "execution_time": 0,
                    "timestamp": datetime.now().isoformat()
                }
        
        test_files = [
            str(self.test_dir / "integration" / "test_kroger_auth_real_server.py"),
            str(self.test_dir / "integration" / "test_kroger_cart_auth.py")
        ]
        
        markers = ["integration"]
        
        return self.run_pytest_command(test_files, markers)
    
    def run_e2e_tests(self, require_server: bool = True) -> Dict[str, Any]:
        """Run end-to-end LLM workflow tests."""
        print("\n" + "="*60)
        print("RUNNING END-TO-END LLM WORKFLOW TESTS")
        print("="*60)
        
        if require_server and not self.check_server_health():
            if not self.wait_for_server():
                return {
                    "error": "Server not available for E2E tests",
                    "exit_code": 1,
                    "execution_time": 0,
                    "timestamp": datetime.now().isoformat()
                }
        
        test_files = [
            str(self.test_dir / "e2e" / "test_kroger_auth_llm_workflows.py")
        ]
        
        markers = ["e2e", "llm_integration"]
        
        return self.run_pytest_command(test_files, markers)
    
    def run_performance_tests(self, concurrent_users: int = 5) -> Dict[str, Any]:
        """Run performance tests."""
        print("\n" + "="*60)
        print(f"RUNNING PERFORMANCE TESTS (Concurrent Users: {concurrent_users})")
        print("="*60)
        
        if not self.check_server_health():
            if not self.wait_for_server():
                return {
                    "error": "Server not available for performance tests",
                    "exit_code": 1,
                    "execution_time": 0,
                    "timestamp": datetime.now().isoformat()
                }
        
        test_files = [
            str(self.test_dir / "unit" / "test_kroger_auth_comprehensive.py"),
            str(self.test_dir / "integration" / "test_kroger_auth_real_server.py"),
            str(self.test_dir / "e2e" / "test_kroger_auth_llm_workflows.py")
        ]
        
        markers = ["performance"]
        additional_args = [f"--concurrent-users={concurrent_users}"]
        
        return self.run_pytest_command(test_files, markers, additional_args)
    
    def run_security_tests(self) -> Dict[str, Any]:
        """Run security-focused tests."""
        print("\n" + "="*60)
        print("RUNNING SECURITY TESTS")
        print("="*60)
        
        test_files = [
            str(self.test_dir / "unit" / "test_kroger_auth_comprehensive.py"),
            str(self.test_dir / "security" / "test_comprehensive_security.py")
        ]
        
        markers = ["security"]
        
        return self.run_pytest_command(test_files, markers)
    
    def run_category_tests(self, categories: List[str]) -> Dict[str, Any]:
        """Run tests for specific categories."""
        print("\n" + "="*60)
        print(f"RUNNING CATEGORY TESTS: {', '.join(categories)}")
        print("="*60)
        
        # Map categories to markers
        category_markers = {
            "token_lifecycle": "unit and asyncio",
            "persistence": "integration and real_persistence",
            "cart_auth": "cart_auth",
            "error_handling": "integration and real_network",
            "llm_workflows": "e2e and llm_integration",
            "performance": "performance"
        }
        
        markers = []
        for category in categories:
            if category in category_markers:
                markers.append(category_markers[category])
        
        if not markers:
            return {
                "error": f"No valid categories found in: {categories}",
                "exit_code": 1,
                "execution_time": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        # Determine which test files to include based on categories
        test_files = []
        if any("unit" in marker for marker in markers):
            test_files.append(str(self.test_dir / "unit" / "test_kroger_auth_comprehensive.py"))
        if any("integration" in marker or "cart_auth" in marker for marker in markers):
            test_files.extend([
                str(self.test_dir / "integration" / "test_kroger_auth_real_server.py"),
                str(self.test_dir / "integration" / "test_kroger_cart_auth.py")
            ])
        if any("e2e" in marker or "llm" in marker for marker in markers):
            test_files.append(str(self.test_dir / "e2e" / "test_kroger_auth_llm_workflows.py"))
        
        return self.run_pytest_command(test_files, markers)
    
    def generate_test_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate comprehensive test report."""
        report_path = self.results_dir / "kroger_auth_test_report.json"
        
        summary = {
            "test_run_timestamp": datetime.now().isoformat(),
            "total_test_suites": len(results),
            "overall_success": all(r.get("exit_code", 1) == 0 for r in results),
            "total_execution_time": sum(r.get("execution_time", 0) for r in results),
            "results": results
        }
        
        with open(report_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Generate text summary
        print("\n" + "="*60)
        print("TEST EXECUTION SUMMARY")
        print("="*60)
        
        for result in results:
            status = "PASSED" if result.get("exit_code", 1) == 0 else "FAILED"
            print(f"Test Suite: {result.get('command', 'Unknown')}")
            print(f"  Status: {status}")
            print(f"  Duration: {result.get('execution_time', 0):.2f}s")
            if result.get("error"):
                print(f"  Error: {result['error']}")
            print()
        
        print(f"Overall Status: {'PASSED' if summary['overall_success'] else 'FAILED'}")
        print(f"Total Duration: {summary['total_execution_time']:.2f}s")
        print(f"Report saved to: {report_path}")
        
        return str(report_path)
    
    def run_all_tests(self) -> List[Dict[str, Any]]:
        """Run all test suites."""
        print("Starting comprehensive Kroger MCP authentication test suite...")
        
        results = []
        
        # Run unit tests (don't require server)
        results.append(self.run_unit_tests())
        
        # Run integration tests (require server)
        results.append(self.run_integration_tests())
        
        # Run E2E tests (require server)
        results.append(self.run_e2e_tests())
        
        # Run performance tests (require server)
        results.append(self.run_performance_tests())
        
        return results


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive test runner for Kroger MCP authentication system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Test execution modes
    parser.add_argument("--all", action="store_true", help="Run all test suites")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--security", action="store_true", help="Run security tests")
    
    # Specific test categories
    parser.add_argument("--categories", type=str, 
                       help="Comma-separated list of test categories: token_lifecycle,persistence,cart_auth,error_handling,llm_workflows,performance")
    
    # Configuration options
    parser.add_argument("--server-url", type=str, default="http://localhost:9004",
                       help="Kroger MCP server URL (default: http://localhost:9004)")
    parser.add_argument("--no-server-check", action="store_true",
                       help="Skip server health checks")
    parser.add_argument("--concurrent-users", type=int, default=5,
                       help="Number of concurrent users for performance tests (default: 5)")
    parser.add_argument("--coverage", action="store_true",
                       help="Generate code coverage reports")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    
    # LLM-specific options
    parser.add_argument("--llm-workflows", action="store_true",
                       help="Run LLM workflow tests specifically")
    
    args = parser.parse_args()
    
    # Create test runner
    runner = KrogerAuthTestRunner()
    runner.server_url = args.server_url
    runner.verbose = args.verbose
    runner.coverage = args.coverage
    
    # Determine what tests to run
    results = []
    
    if args.all:
        results = runner.run_all_tests()
    else:
        if args.unit:
            results.append(runner.run_unit_tests())
        
        if args.integration:
            results.append(runner.run_integration_tests(not args.no_server_check))
        
        if args.e2e or args.llm_workflows:
            results.append(runner.run_e2e_tests(not args.no_server_check))
        
        if args.performance:
            results.append(runner.run_performance_tests(args.concurrent_users))
        
        if args.security:
            results.append(runner.run_security_tests())
        
        if args.categories:
            categories = [cat.strip() for cat in args.categories.split(",")]
            results.append(runner.run_category_tests(categories))
    
    # If no specific tests specified, run unit tests by default
    if not results:
        print("No test type specified, running unit tests by default...")
        results.append(runner.run_unit_tests())
    
    # Generate report
    report_path = runner.generate_test_report(results)
    
    # Exit with error code if any tests failed
    overall_success = all(r.get("exit_code", 1) == 0 for r in results)
    sys.exit(0 if overall_success else 1)


if __name__ == "__main__":
    main()
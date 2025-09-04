#!/usr/bin/env python3
"""
Comprehensive test runner for Playwright MCP Server
Runs all test suites with proper configuration and reporting
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


class TestRunner:
    """Orchestrates running of all Playwright MCP tests."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_results_dir = self.project_root / "test-results"
        self.test_results_dir.mkdir(exist_ok=True)
        
    def install_dependencies(self, force=False):
        """Install test dependencies including Playwright browsers."""
        print("📦 Installing test dependencies...")
        
        if force or not self._playwright_installed():
            print("Installing Playwright...")
            subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
            subprocess.run([sys.executable, "-m", "playwright", "install-deps"], check=True)
        
        # Install dev requirements
        requirements_dev = self.project_root / "requirements-dev.txt"
        if requirements_dev.exists():
            print("Installing development requirements...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_dev)], check=True)
    
    def _playwright_installed(self):
        """Check if Playwright is properly installed."""
        try:
            import playwright
            return True
        except ImportError:
            return False
    
    def run_unit_tests(self):
        """Run unit tests (fast, isolated)."""
        print("\n🔧 Running Unit Tests...")
        cmd = [
            "python", "-m", "pytest",
            "tests/unit/test_playwright_mcp_unit.py",
            "test_playwright_mcp.py::TestPlaywrightMCPServer::test_server_startup",
            "test_playwright_mcp.py::TestPlaywrightMCPServer::test_root_endpoint",
            "-m", "unit or not (integration or e2e)",
            "--junit-xml=test-results/unit-results.xml",
            "--html=test-results/unit-report.html",
            "--self-contained-html",
            "-v"
        ]
        return self._run_command(cmd)
    
    def run_integration_tests(self):
        """Run integration tests (with real browser)."""
        print("\n🌐 Running Integration Tests...")
        cmd = [
            "python", "-m", "pytest",
            "tests/integration/test_playwright_mcp_integration.py",
            "test_playwright_mcp.py::TestPlaywrightErrorHandling",
            "test_playwright_mcp.py::TestPlaywrightPerformance",
            "-m", "integration",
            "--junit-xml=test-results/integration-results.xml",
            "--html=test-results/integration-report.html",
            "--self-contained-html",
            "-v"
        ]
        return self._run_command(cmd)
    
    def run_e2e_tests(self):
        """Run end-to-end tests (full workflows)."""
        print("\n🎭 Running E2E Tests...")
        cmd = [
            "python", "-m", "pytest",
            "tests/e2e/test_playwright_mcp_e2e.py",
            "-m", "e2e",
            "--junit-xml=test-results/e2e-results.xml",
            "--html=test-results/e2e-report.html",
            "--self-contained-html",
            "-v",
            "-x"  # Stop on first failure for E2E
        ]
        return self._run_command(cmd)
    
    def run_performance_tests(self):
        """Run performance and load tests."""
        print("\n⚡ Running Performance Tests...")
        cmd = [
            "python", "-m", "pytest",
            "test_playwright_mcp.py",
            "-m", "performance",
            "--junit-xml=test-results/performance-results.xml",
            "--html=test-results/performance-report.html",
            "--self-contained-html",
            "-v"
        ]
        return self._run_command(cmd)
    
    def run_security_tests(self):
        """Run security-related tests."""
        print("\n🔒 Running Security Tests...")
        cmd = [
            "python", "-m", "pytest",
            "test_playwright_mcp.py::TestPlaywrightErrorHandling",
            "-m", "security or not (performance or slow)",
            "--junit-xml=test-results/security-results.xml",
            "--html=test-results/security-report.html",
            "--self-contained-html",
            "-v"
        ]
        return self._run_command(cmd)
    
    def run_smoke_tests(self):
        """Run smoke tests (basic functionality)."""
        print("\n💨 Running Smoke Tests...")
        cmd = [
            "python", "-m", "pytest",
            "test_playwright_mcp.py::TestPlaywrightMCPServer::test_server_startup",
            "test_playwright_mcp.py::TestPlaywrightMCPServer::test_root_endpoint",
            "test_playwright_mcp.py::TestPlaywrightMCPServer::test_navigation_api_endpoint",
            "tests/unit/test_playwright_mcp_unit.py::TestMockServerEndpoints::test_health_endpoint",
            "-v"
        ]
        return self._run_command(cmd)
    
    def run_comprehensive_tests(self):
        """Run the comprehensive test file."""
        print("\n📋 Running Comprehensive Test Suite...")
        cmd = [
            "python", "-m", "pytest",
            "test_playwright_mcp.py",
            "--junit-xml=test-results/comprehensive-results.xml",
            "--html=test-results/comprehensive-report.html",
            "--self-contained-html",
            "-v",
            "--tb=short"
        ]
        return self._run_command(cmd)
    
    def run_all_tests(self):
        """Run all test suites in sequence."""
        print("🚀 Running All Test Suites...")
        
        results = {}
        
        # Run tests in order of increasing complexity
        test_suites = [
            ("smoke", self.run_smoke_tests),
            ("unit", self.run_unit_tests),
            ("security", self.run_security_tests),
            ("integration", self.run_integration_tests),
            ("performance", self.run_performance_tests),
            ("comprehensive", self.run_comprehensive_tests),
            ("e2e", self.run_e2e_tests)
        ]
        
        for suite_name, test_func in test_suites:
            print(f"\n{'='*60}")
            print(f"Running {suite_name.upper()} tests...")
            print(f"{'='*60}")
            
            start_time = time.time()
            success = test_func()
            end_time = time.time()
            
            results[suite_name] = {
                "success": success,
                "duration": end_time - start_time
            }
            
            if not success:
                print(f"❌ {suite_name.upper()} tests FAILED")
                if suite_name in ["smoke", "unit"]:
                    print("💥 Critical tests failed, stopping execution")
                    break
            else:
                print(f"✅ {suite_name.upper()} tests PASSED ({results[suite_name]['duration']:.1f}s)")
        
        # Print summary
        self._print_summary(results)
        
        # Return overall success
        return all(result["success"] for result in results.values())
    
    def run_coverage_analysis(self):
        """Run tests with coverage analysis."""
        print("\n📊 Running Coverage Analysis...")
        cmd = [
            "python", "-m", "pytest",
            "test_playwright_mcp.py",
            "tests/unit/",
            "--cov=playwright_server",
            "--cov=playwright_mcp_server_real",
            "--cov-report=html:test-results/coverage-html",
            "--cov-report=xml:test-results/coverage.xml",
            "--cov-report=term-missing",
            "--cov-fail-under=60",  # Require at least 60% coverage
            "-v"
        ]
        return self._run_command(cmd)
    
    def _run_command(self, cmd):
        """Run a command and return success status."""
        try:
            result = subprocess.run(cmd, cwd=self.project_root, check=True, capture_output=False)
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed with exit code {e.returncode}")
            return False
        except Exception as e:
            print(f"❌ Error running command: {e}")
            return False
    
    def _print_summary(self, results):
        """Print test execution summary."""
        print(f"\n{'='*60}")
        print("TEST EXECUTION SUMMARY")
        print(f"{'='*60}")
        
        total_duration = sum(r["duration"] for r in results.values())
        passed_count = sum(1 for r in results.values() if r["success"])
        total_count = len(results)
        
        for suite_name, result in results.items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            duration = result["duration"]
            print(f"{suite_name.upper():15} {status:8} ({duration:5.1f}s)")
        
        print(f"{'='*60}")
        print(f"TOTAL: {passed_count}/{total_count} suites passed in {total_duration:.1f}s")
        
        if passed_count == total_count:
            print("🎉 ALL TESTS PASSED!")
        else:
            print("💥 SOME TESTS FAILED")
        
        print(f"\n📁 Test reports available in: {self.test_results_dir}")


def main():
    """Main test runner entry point."""
    parser = argparse.ArgumentParser(description="Playwright MCP Server Test Runner")
    parser.add_argument("--suite", choices=[
        "all", "smoke", "unit", "integration", "e2e", 
        "performance", "security", "comprehensive", "coverage"
    ], default="all", help="Test suite to run")
    parser.add_argument("--install-deps", action="store_true", 
                       help="Install dependencies before running tests")
    parser.add_argument("--force-install", action="store_true",
                       help="Force reinstall of dependencies")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # Install dependencies if requested
    if args.install_deps or args.force_install:
        try:
            runner.install_dependencies(force=args.force_install)
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return 1
    
    # Run selected test suite
    suite_map = {
        "all": runner.run_all_tests,
        "smoke": runner.run_smoke_tests,
        "unit": runner.run_unit_tests,
        "integration": runner.run_integration_tests,
        "e2e": runner.run_e2e_tests,
        "performance": runner.run_performance_tests,
        "security": runner.run_security_tests,
        "comprehensive": runner.run_comprehensive_tests,
        "coverage": runner.run_coverage_analysis
    }
    
    print(f"🧪 Starting {args.suite} test suite...")
    success = suite_map[args.suite]()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Comprehensive Test Runner for BoarderframeOS
Runs all test suites with proper configuration and reporting
"""

import sys
import os
import subprocess
import argparse
import time
from pathlib import Path
from datetime import datetime


class TestRunner:
    """Manages test execution and reporting"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.test_dir = self.root_dir / "tests"
        self.results = []
        
    def run_command(self, cmd, description):
        """Run a command and capture output"""
        print(f"\n{'='*60}")
        print(f"🧪 {description}")
        print(f"{'='*60}")
        
        start_time = time.time()
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        
        duration = time.time() - start_time
        
        self.results.append({
            "description": description,
            "command": cmd,
            "success": result.returncode == 0,
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr
        })
        
        if result.returncode == 0:
            print(f"✅ PASSED in {duration:.2f}s")
        else:
            print(f"❌ FAILED in {duration:.2f}s")
            print(f"Error: {result.stderr}")
            
        return result.returncode == 0
    
    def run_unit_tests(self):
        """Run unit tests only"""
        return self.run_command(
            "pytest tests/test_core_components.py -v",
            "Unit Tests: Core Components"
        )
    
    def run_agent_tests(self):
        """Run agent-specific tests"""
        return self.run_command(
            "pytest tests/test_agents.py -v",
            "Agent Tests: Solomon, David, Adam, Eve, Bezalel, Governor"
        )
    
    def run_integration_tests(self):
        """Run integration tests"""
        return self.run_command(
            "pytest tests/test_integrations.py -v -m integration",
            "Integration Tests: Cross-component functionality"
        )
    
    def run_governance_tests(self):
        """Run governance tests"""
        return self.run_command(
            "pytest tests/test_governance.py -v",
            "Governance Tests: Policy enforcement and compliance"
        )
    
    def run_task_queue_tests(self):
        """Run task queue tests"""
        return self.run_command(
            "pytest tests/test_task_queue.py -v",
            "Task Queue Tests: Celery and distributed processing"
        )
    
    def run_health_tests(self):
        """Run health monitoring tests"""
        return self.run_command(
            "pytest tests/test_health_monitoring.py -v",
            "Health Monitoring Tests: Agent health and alerting"
        )
    
    def run_all_tests(self):
        """Run all tests with coverage"""
        return self.run_command(
            "pytest -v --cov --cov-report=term-missing --cov-report=html",
            "All Tests with Coverage Report"
        )
    
    def run_fast_tests(self):
        """Run fast tests only (no integration)"""
        return self.run_command(
            'pytest -v -m "not slow and not integration"',
            "Fast Tests Only"
        )
    
    def run_specific_test(self, test_path):
        """Run a specific test file or test"""
        return self.run_command(
            f"pytest {test_path} -v",
            f"Specific Test: {test_path}"
        )
    
    def generate_report(self):
        """Generate test report"""
        print(f"\n{'='*60}")
        print(f"📊 TEST SUMMARY REPORT")
        print(f"{'='*60}")
        print(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\nResults:")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - passed_tests
        total_duration = sum(r["duration"] for r in self.results)
        
        print(f"  Total Tests Run: {total_tests}")
        print(f"  Passed: {passed_tests} ✅")
        print(f"  Failed: {failed_tests} ❌")
        print(f"  Total Duration: {total_duration:.2f}s")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.results:
                if not result["success"]:
                    print(f"  - {result['description']}")
        
        # Save detailed report
        report_path = self.root_dir / "test_report.txt"
        with open(report_path, "w") as f:
            f.write(f"BoarderframeOS Test Report\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write(f"{'='*60}\n\n")
            
            for result in self.results:
                f.write(f"\nTest: {result['description']}\n")
                f.write(f"Command: {result['command']}\n")
                f.write(f"Status: {'PASSED' if result['success'] else 'FAILED'}\n")
                f.write(f"Duration: {result['duration']:.2f}s\n")
                if not result['success']:
                    f.write(f"Error Output:\n{result['stderr']}\n")
                f.write(f"{'-'*40}\n")
        
        print(f"\n📄 Detailed report saved to: {report_path}")
        
        # Open coverage report if generated
        coverage_report = self.root_dir / "htmlcov" / "index.html"
        if coverage_report.exists():
            print(f"\n📈 Coverage report available at: {coverage_report}")
            print(f"   Open with: open {coverage_report}")
        
        return passed_tests == total_tests


def main():
    """Main test runner entry point"""
    parser = argparse.ArgumentParser(
        description="BoarderframeOS Test Runner"
    )
    
    parser.add_argument(
        "--suite",
        choices=[
            "all", "unit", "agents", "integration", 
            "governance", "task-queue", "health", "fast"
        ],
        default="all",
        help="Test suite to run"
    )
    
    parser.add_argument(
        "--test",
        type=str,
        help="Run specific test file or test function"
    )
    
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Skip coverage report generation"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Ensure we're in the right directory
    os.chdir(Path(__file__).parent)
    
    # Create test runner
    runner = TestRunner()
    
    print(f"🚀 BoarderframeOS Test Runner")
    print(f"   Python: {sys.version.split()[0]}")
    print(f"   Directory: {os.getcwd()}")
    
    # Run appropriate test suite
    if args.test:
        runner.run_specific_test(args.test)
    elif args.suite == "all":
        runner.run_all_tests()
    elif args.suite == "unit":
        runner.run_unit_tests()
    elif args.suite == "agents":
        runner.run_agent_tests()
    elif args.suite == "integration":
        runner.run_integration_tests()
    elif args.suite == "governance":
        runner.run_governance_tests()
    elif args.suite == "task-queue":
        runner.run_task_queue_tests()
    elif args.suite == "health":
        runner.run_health_tests()
    elif args.suite == "fast":
        runner.run_fast_tests()
    
    # Generate report
    success = runner.generate_report()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
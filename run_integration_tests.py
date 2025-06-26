#!/usr/bin/env python3
"""
Integration Test Runner for BoarderframeOS
Runs comprehensive integration tests with proper setup and teardown
"""

import sys
import os
import subprocess
import asyncio
import argparse
import time
from pathlib import Path
from datetime import datetime
import json


class IntegrationTestRunner:
    """Manages integration test execution"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.test_dir = self.root_dir / "tests" / "integration"
        self.results = []
        self.services_started = False
        
    def start_test_services(self):
        """Start required services for integration tests"""
        print("\n🚀 Starting test services...")
        
        # Check Docker
        docker_check = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True
        )
        
        if docker_check.returncode != 0:
            print("❌ Docker is not running. Please start Docker Desktop.")
            return False
        
        # Start test database and Redis
        print("Starting test PostgreSQL and Redis...")
        docker_compose = subprocess.run(
            ["docker-compose", "-f", "docker-compose.test.yml", "up", "-d"],
            capture_output=True,
            text=True
        )
        
        if docker_compose.returncode == 0:
            print("✅ Test services started")
            self.services_started = True
            # Wait for services to be ready
            time.sleep(5)
            return True
        else:
            print("❌ Failed to start test services")
            print(docker_compose.stderr)
            return False
    
    def stop_test_services(self):
        """Stop test services"""
        if self.services_started:
            print("\n🛑 Stopping test services...")
            subprocess.run(
                ["docker-compose", "-f", "docker-compose.test.yml", "down"],
                capture_output=True
            )
            print("✅ Test services stopped")
    
    def run_test_suite(self, suite_name, test_file=None):
        """Run a specific integration test suite"""
        print(f"\n{'='*60}")
        print(f"🧪 Running Integration Test Suite: {suite_name}")
        print(f"{'='*60}")
        
        if test_file:
            cmd = f"pytest {test_file} -v -m integration"
        else:
            cmd = f"pytest tests/integration/ -v -m integration"
        
        start_time = time.time()
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        
        duration = time.time() - start_time
        
        self.results.append({
            "suite": suite_name,
            "success": result.returncode == 0,
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr
        })
        
        if result.returncode == 0:
            print(f"✅ {suite_name} PASSED in {duration:.2f}s")
        else:
            print(f"❌ {suite_name} FAILED in {duration:.2f}s")
            print(f"Error output:\n{result.stderr}")
        
        return result.returncode == 0
    
    def run_system_startup_tests(self):
        """Run system startup integration tests"""
        return self.run_test_suite(
            "System Startup",
            "tests/integration/test_system_startup.py"
        )
    
    def run_ui_integration_tests(self):
        """Run UI integration tests"""
        return self.run_test_suite(
            "UI Integration",
            "tests/integration/test_ui_integration.py"
        )
    
    def run_data_flow_tests(self):
        """Run data flow integration tests"""
        return self.run_test_suite(
            "Data Flow",
            "tests/integration/test_data_flow.py"
        )
    
    def run_all_integration_tests(self):
        """Run all integration tests"""
        print("\n🎯 Running ALL Integration Tests")
        
        # Run each test suite
        self.run_system_startup_tests()
        self.run_ui_integration_tests()
        self.run_data_flow_tests()
        
        # Run any additional integration tests
        self.run_test_suite("Additional Integration Tests")
    
    def run_smoke_tests(self):
        """Run quick smoke tests"""
        print("\n💨 Running Smoke Tests (Quick Integration Tests)")
        
        cmd = 'pytest tests/integration/ -v -m "integration and not slow" --maxfail=3'
        
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Smoke tests PASSED")
        else:
            print("❌ Smoke tests FAILED")
            print(result.stderr)
        
        return result.returncode == 0
    
    def generate_report(self):
        """Generate integration test report"""
        print(f"\n{'='*60}")
        print("📊 INTEGRATION TEST REPORT")
        print(f"{'='*60}")
        print(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        total_suites = len(self.results)
        passed_suites = sum(1 for r in self.results if r["success"])
        failed_suites = total_suites - passed_suites
        total_duration = sum(r["duration"] for r in self.results)
        
        print(f"\nSummary:")
        print(f"  Total Test Suites: {total_suites}")
        print(f"  Passed: {passed_suites} ✅")
        print(f"  Failed: {failed_suites} ❌")
        print(f"  Total Duration: {total_duration:.2f}s")
        
        if failed_suites > 0:
            print(f"\n❌ Failed Suites:")
            for result in self.results:
                if not result["success"]:
                    print(f"  - {result['suite']}")
        
        # Save detailed report
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_suites": total_suites,
                "passed": passed_suites,
                "failed": failed_suites,
                "duration": total_duration
            },
            "results": self.results
        }
        
        report_path = self.root_dir / "integration_test_report.json"
        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_path}")
        
        # Generate HTML report if coverage data exists
        coverage_path = self.root_dir / "htmlcov" / "index.html"
        if coverage_path.exists():
            print(f"📈 Coverage report available at: {coverage_path}")
        
        return passed_suites == total_suites
    
    def setup_test_environment(self):
        """Set up test environment"""
        print("\n🔧 Setting up test environment...")
        
        # Create test directories if needed
        test_dirs = [
            self.root_dir / "test_data",
            self.root_dir / "test_logs",
            self.root_dir / "test_configs"
        ]
        
        for dir_path in test_dirs:
            dir_path.mkdir(exist_ok=True)
        
        # Set environment variables
        os.environ["BOARDERFRAME_ENV"] = "test"
        os.environ["BOARDERFRAME_TEST_MODE"] = "1"
        
        print("✅ Test environment ready")
    
    def cleanup_test_environment(self):
        """Clean up test environment"""
        print("\n🧹 Cleaning up test environment...")
        
        # Remove test data
        test_dirs = [
            self.root_dir / "test_data",
            self.root_dir / "test_logs"
        ]
        
        for dir_path in test_dirs:
            if dir_path.exists():
                subprocess.run(["rm", "-rf", str(dir_path)], capture_output=True)
        
        print("✅ Test environment cleaned")


def create_docker_compose_test():
    """Create docker-compose.test.yml for test services"""
    content = """version: '3.8'

services:
  test-postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: test_boarderframe
      POSTGRES_PASSWORD: test_pass
      POSTGRES_DB: test_boarderframeos
    ports:
      - "5435:5432"
    volumes:
      - test_postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test_boarderframe"]
      interval: 5s
      timeout: 5s
      retries: 5

  test-redis:
    image: redis:7-alpine
    ports:
      - "6380:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  test_postgres_data:
"""
    
    with open("docker-compose.test.yml", "w") as f:
        f.write(content)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="BoarderframeOS Integration Test Runner"
    )
    
    parser.add_argument(
        "--suite",
        choices=["all", "startup", "ui", "data-flow", "smoke"],
        default="all",
        help="Test suite to run"
    )
    
    parser.add_argument(
        "--no-services",
        action="store_true",
        help="Skip starting test services (assumes they're already running)"
    )
    
    parser.add_argument(
        "--keep-services",
        action="store_true",
        help="Keep test services running after tests"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Create test docker-compose if needed
    if not Path("docker-compose.test.yml").exists():
        create_docker_compose_test()
    
    # Create runner
    runner = IntegrationTestRunner()
    
    print("🚀 BoarderframeOS Integration Test Runner")
    print(f"   Python: {sys.version.split()[0]}")
    print(f"   Directory: {os.getcwd()}")
    
    try:
        # Setup environment
        runner.setup_test_environment()
        
        # Start services if needed
        if not args.no_services:
            if not runner.start_test_services():
                print("❌ Failed to start test services")
                sys.exit(1)
        
        # Run tests
        if args.suite == "all":
            runner.run_all_integration_tests()
        elif args.suite == "startup":
            runner.run_system_startup_tests()
        elif args.suite == "ui":
            runner.run_ui_integration_tests()
        elif args.suite == "data-flow":
            runner.run_data_flow_tests()
        elif args.suite == "smoke":
            runner.run_smoke_tests()
        
        # Generate report
        success = runner.generate_report()
        
        # Cleanup
        if not args.keep_services and not args.no_services:
            runner.stop_test_services()
        
        runner.cleanup_test_environment()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        if not args.keep_services and not args.no_services:
            runner.stop_test_services()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if not args.keep_services and not args.no_services:
            runner.stop_test_services()
        sys.exit(1)


if __name__ == "__main__":
    main()
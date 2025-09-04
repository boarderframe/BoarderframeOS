#!/usr/bin/env python3
"""
Comprehensive test runner for Kroger MCP Server tests.
Provides organized test execution with reporting and coverage analysis.
"""
import subprocess
import sys
import os
import argparse
from pathlib import Path
from typing import List, Dict, Any
import json
from datetime import datetime


class KrogerTestRunner:
    """Test runner for Kroger MCP Server test suite."""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent
        self.test_file = self.project_root / "tests" / "unit" / "test_kroger_mcp.py"
        self.config_file = self.project_root / "pytest-kroger.ini"
        
    def run_tests(self, 
                  test_type: str = "all",
                  verbose: bool = True,
                  coverage: bool = True,
                  parallel: bool = False,
                  markers: List[str] = None,
                  keywords: str = None) -> Dict[str, Any]:
        """
        Run Kroger MCP tests with specified options.
        
        Args:
            test_type: Type of tests to run (unit, integration, e2e, security, performance, all)
            verbose: Enable verbose output
            coverage: Generate coverage report
            parallel: Run tests in parallel (requires pytest-xdist)
            markers: Additional pytest markers to apply
            keywords: Test name keywords to filter by
            
        Returns:
            Dict with test results and metadata
        """
        cmd = ["python", "-m", "pytest"]
        
        # Add configuration file
        if self.config_file.exists():
            cmd.extend(["-c", str(self.config_file)])
        
        # Add test file
        cmd.append(str(self.test_file))
        
        # Test type markers
        test_markers = {
            "unit": "unit",
            "integration": "integration", 
            "e2e": "e2e",
            "security": "security",
            "performance": "performance",
            "schema": "schema",
            "oauth": "oauth",
            "api": "api",
            "cart": "cart",
            "product": "product",
            "location": "location"
        }
        
        # Apply test type filter
        if test_type != "all" and test_type in test_markers:
            cmd.extend(["-m", test_markers[test_type]])
        elif test_type == "fast":
            cmd.extend(["-m", "not slow"])
        elif test_type == "slow":
            cmd.extend(["-m", "slow"])
        
        # Additional markers
        if markers:
            for marker in markers:
                cmd.extend(["-m", marker])
        
        # Keyword filtering
        if keywords:
            cmd.extend(["-k", keywords])
        
        # Verbose output
        if verbose:
            cmd.append("-v")
        
        # Coverage
        if coverage:
            cmd.extend([
                "--cov=mcp_servers/kroger",
                "--cov-report=html:htmlcov/kroger",
                "--cov-report=term-missing",
                "--cov-report=json:coverage-kroger.json"
            ])
        
        # Parallel execution
        if parallel:
            try:
                import pytest_xdist
                cmd.extend(["-n", "auto"])
            except ImportError:
                print("Warning: pytest-xdist not installed, running sequentially")
        
        # Output formatting
        cmd.extend([
            "--tb=short",
            "--color=yes",
            "--durations=10"
        ])
        
        print(f"Running Kroger MCP tests with command: {' '.join(cmd)}")
        print("-" * 80)
        
        # Execute tests
        start_time = datetime.now()
        result = subprocess.run(cmd, capture_output=False, text=True)
        end_time = datetime.now()
        
        # Parse results
        test_results = {
            "command": " ".join(cmd),
            "exit_code": result.returncode,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration": (end_time - start_time).total_seconds(),
            "success": result.returncode == 0
        }
        
        # Load coverage data if available
        coverage_file = self.project_root / "coverage-kroger.json"
        if coverage and coverage_file.exists():
            try:
                with open(coverage_file) as f:
                    coverage_data = json.load(f)
                    test_results["coverage"] = {
                        "total_coverage": coverage_data.get("totals", {}).get("percent_covered", 0),
                        "lines_covered": coverage_data.get("totals", {}).get("covered_lines", 0),
                        "lines_total": coverage_data.get("totals", {}).get("num_statements", 0)
                    }
            except Exception as e:
                print(f"Warning: Could not parse coverage data: {e}")
        
        return test_results
    
    def run_test_suite(self) -> Dict[str, Any]:
        """Run the complete Kroger MCP test suite with comprehensive reporting."""
        print("🚀 Starting Kroger MCP Server Test Suite")
        print("=" * 80)
        
        suite_results = {
            "suite_start": datetime.now().isoformat(),
            "test_runs": {}
        }
        
        # Test configurations to run
        test_configs = [
            ("Unit Tests", {"test_type": "unit", "coverage": True}),
            ("Integration Tests", {"test_type": "integration", "coverage": False}),
            ("Security Tests", {"test_type": "security", "coverage": False}),
            ("Schema Validation", {"test_type": "schema", "coverage": False}),
            ("OAuth2 Tests", {"test_type": "oauth", "coverage": False}),
            ("Performance Tests", {"test_type": "performance", "coverage": False}),
        ]
        
        for test_name, config in test_configs:
            print(f"\n📋 Running {test_name}")
            print("-" * 40)
            
            try:
                results = self.run_tests(**config)
                suite_results["test_runs"][test_name] = results
                
                if results["success"]:
                    print(f"✅ {test_name} completed successfully")
                else:
                    print(f"❌ {test_name} failed with exit code {results['exit_code']}")
                    
            except Exception as e:
                print(f"💥 {test_name} crashed: {e}")
                suite_results["test_runs"][test_name] = {
                    "error": str(e),
                    "success": False
                }
        
        # Summary
        suite_results["suite_end"] = datetime.now().isoformat()
        successful_runs = sum(1 for run in suite_results["test_runs"].values() 
                             if run.get("success", False))
        total_runs = len(suite_results["test_runs"])
        
        print("\n" + "=" * 80)
        print("📊 TEST SUITE SUMMARY")
        print("=" * 80)
        print(f"Total test categories: {total_runs}")
        print(f"Successful runs: {successful_runs}")
        print(f"Failed runs: {total_runs - successful_runs}")
        print(f"Success rate: {(successful_runs/total_runs)*100:.1f}%")
        
        # Coverage summary
        unit_test_results = suite_results["test_runs"].get("Unit Tests", {})
        if "coverage" in unit_test_results:
            cov = unit_test_results["coverage"]
            print(f"Code coverage: {cov['total_coverage']:.1f}% "
                  f"({cov['lines_covered']}/{cov['lines_total']} lines)")
        
        # Save results
        results_file = self.project_root / "kroger_test_results.json"
        with open(results_file, "w") as f:
            json.dump(suite_results, f, indent=2)
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        if successful_runs == total_runs:
            print("🎉 All test categories passed!")
            return suite_results
        else:
            print("⚠️  Some test categories failed. Check logs above.")
            return suite_results
    
    def install_dependencies(self):
        """Install required test dependencies."""
        dependencies = [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "pytest-xdist>=3.0.0",  # For parallel execution
            "httpx>=0.24.0",
            "jsonschema>=4.17.0",
            "freezegun>=1.2.0",
            "faker>=18.0.0",
            "pyjwt>=2.6.0"
        ]
        
        print("📦 Installing test dependencies...")
        for dep in dependencies:
            print(f"Installing {dep}")
            subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                          capture_output=True)
        print("✅ Dependencies installed")


def main():
    """Main CLI interface for Kroger MCP test runner."""
    parser = argparse.ArgumentParser(description="Kroger MCP Server Test Runner")
    parser.add_argument("--type", choices=["all", "unit", "integration", "e2e", 
                                          "security", "performance", "schema", 
                                          "oauth", "fast", "slow"], 
                       default="all", help="Type of tests to run")
    parser.add_argument("--markers", nargs="+", help="Additional pytest markers")
    parser.add_argument("--keywords", "-k", help="Test name keywords to filter")
    parser.add_argument("--no-coverage", action="store_true", 
                       help="Disable coverage reporting")
    parser.add_argument("--parallel", action="store_true", 
                       help="Run tests in parallel")
    parser.add_argument("--suite", action="store_true", 
                       help="Run complete test suite")
    parser.add_argument("--install-deps", action="store_true", 
                       help="Install required dependencies")
    parser.add_argument("--quiet", action="store_true", 
                       help="Reduce verbosity")
    
    args = parser.parse_args()
    
    runner = KrogerTestRunner()
    
    if args.install_deps:
        runner.install_dependencies()
        return
    
    if args.suite:
        results = runner.run_test_suite()
        # Exit with error code if any tests failed
        if not all(run.get("success", False) for run in results["test_runs"].values()):
            sys.exit(1)
    else:
        results = runner.run_tests(
            test_type=args.type,
            verbose=not args.quiet,
            coverage=not args.no_coverage,
            parallel=args.parallel,
            markers=args.markers,
            keywords=args.keywords
        )
        if not results["success"]:
            sys.exit(results["exit_code"])


if __name__ == "__main__":
    main()
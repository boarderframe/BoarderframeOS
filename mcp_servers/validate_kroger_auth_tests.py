#!/usr/bin/env python3
"""
Validation Script for Kroger MCP Authentication Test Suite.

This script validates the test environment and runs a quick smoke test
to ensure all test components are properly configured.

Usage:
    python validate_kroger_auth_tests.py
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path
from typing import List, Dict, Any


class TestEnvironmentValidator:
    """Validates the test environment setup."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_dir = self.project_root / "tests"
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def validate_python_version(self) -> bool:
        """Check Python version compatibility."""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            self.errors.append(f"Python 3.8+ required, found {version.major}.{version.minor}")
            return False
        print(f"✓ Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    
    def validate_dependencies(self) -> bool:
        """Check required dependencies."""
        required_packages = [
            'pytest', 'httpx', 'fastapi', 'asyncio', 'json', 'time', 
            'datetime', 'typing'
        ]
        
        # Special cases for imports that need different handling
        special_imports = {
            'mock': 'unittest.mock'
        }
        
        missing_packages = []
        for package in required_packages:
            try:
                importlib.import_module(package)
                print(f"✓ {package}")
            except ImportError:
                missing_packages.append(package)
                print(f"✗ {package}")
        
        # Check special imports
        for short_name, full_import in special_imports.items():
            try:
                from unittest import mock
                print(f"✓ {full_import}")
            except ImportError:
                missing_packages.append(full_import)
                print(f"✗ {full_import}")
        
        if missing_packages:
            self.errors.append(f"Missing packages: {', '.join(missing_packages)}")
            return False
        
        return True
    
    def validate_test_files(self) -> bool:
        """Check test file structure."""
        expected_files = [
            "tests/unit/test_kroger_auth_comprehensive.py",
            "tests/integration/test_kroger_auth_real_server.py", 
            "tests/integration/test_kroger_cart_auth.py",
            "tests/e2e/test_kroger_auth_llm_workflows.py",
            "tests/utils/test_helpers.py",
            "tests/factories/test_data_factory.py"
        ]
        
        missing_files = []
        for file_path in expected_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                print(f"✓ {file_path}")
            else:
                missing_files.append(file_path)
                print(f"✗ {file_path}")
        
        if missing_files:
            self.errors.append(f"Missing test files: {', '.join(missing_files)}")
            return False
        
        return True
    
    def validate_test_runner(self) -> bool:
        """Check test runner script."""
        runner_path = self.project_root / "run_kroger_auth_tests.py"
        if not runner_path.exists():
            self.errors.append("Test runner script not found: run_kroger_auth_tests.py")
            return False
        
        # Check if executable
        if not os.access(runner_path, os.X_OK):
            self.warnings.append("Test runner script is not executable")
        
        print(f"✓ Test runner: {runner_path}")
        return True
    
    def validate_configuration(self) -> bool:
        """Check configuration and environment variables."""
        # Check for environment variables
        env_vars = {
            'KROGER_CLIENT_ID': False,
            'KROGER_CLIENT_SECRET': False,
            'KROGER_DEV_MODE': False,
            'KROGER_SERVER_URL': False
        }
        
        for var, required in env_vars.items():
            value = os.getenv(var)
            if value:
                print(f"✓ {var}: {'*' * len(value[:4])}...")
            elif required:
                self.errors.append(f"Required environment variable missing: {var}")
            else:
                print(f"- {var}: Not set (optional)")
        
        return True
    
    def run_smoke_test(self) -> bool:
        """Run basic smoke test."""
        print("\nRunning smoke test...")
        
        try:
            # Try to import test modules
            sys.path.insert(0, str(self.project_root))
            
            # Test basic test helper imports
            from tests.factories.test_data_factory import TestDataFactory
            
            # Test factory functionality
            server_data = TestDataFactory.create_server_data()
            assert 'name' in server_data
            assert 'port' in server_data
            print("✓ Test data factory working")
            
            # Test that we can create random strings
            random_string = TestDataFactory.random_string(10)
            assert len(random_string) == 10
            print("✓ Random string generation working")
            
            # Test email generation
            email = TestDataFactory.random_email()
            assert '@' in email
            print("✓ Email generation working")
            
            return True
            
        except Exception as e:
            self.errors.append(f"Smoke test failed: {str(e)}")
            return False
    
    def check_server_availability(self) -> bool:
        """Check if Kroger MCP server is available."""
        try:
            import requests
            response = requests.get("http://localhost:9004/health", timeout=5)
            if response.status_code == 200:
                print("✓ Kroger MCP server is running and healthy")
                return True
            else:
                self.warnings.append(f"Server responded with status {response.status_code}")
                return False
        except Exception as e:
            self.warnings.append(f"Server not available: {str(e)}")
            return False
    
    def run_basic_pytest(self) -> bool:
        """Run basic pytest to verify functionality."""
        print("\nRunning basic pytest validation...")
        
        try:
            # Run a simple pytest command to check if it works
            result = subprocess.run([
                sys.executable, "-m", "pytest", "--version"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                print(f"✓ Pytest version: {result.stdout.strip()}")
                return True
            else:
                self.errors.append(f"Pytest not working: {result.stderr}")
                return False
                
        except Exception as e:
            self.errors.append(f"Failed to run pytest: {str(e)}")
            return False
    
    def validate_all(self) -> bool:
        """Run all validations."""
        print("Validating Kroger MCP Authentication Test Environment")
        print("=" * 60)
        
        validations = [
            ("Python Version", self.validate_python_version),
            ("Dependencies", self.validate_dependencies),
            ("Test Files", self.validate_test_files),
            ("Test Runner", self.validate_test_runner),
            ("Configuration", self.validate_configuration),
            ("Smoke Test", self.run_smoke_test),
            ("Pytest", self.run_basic_pytest),
            ("Server Availability", self.check_server_availability)
        ]
        
        success_count = 0
        for name, validation_func in validations:
            print(f"\n{name}:")
            print("-" * 20)
            if validation_func():
                success_count += 1
            print()
        
        # Print summary
        print("=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        
        print(f"Validations passed: {success_count}/{len(validations)}")
        
        if self.errors:
            print("\nERRORS:")
            for error in self.errors:
                print(f"  ✗ {error}")
        
        if self.warnings:
            print("\nWARNINGS:")
            for warning in self.warnings:
                print(f"  ⚠ {warning}")
        
        if not self.errors:
            print("\n✓ Test environment is properly configured!")
            print("\nNext steps:")
            print("  1. Run unit tests: python run_kroger_auth_tests.py --unit")
            if not any("Server not available" in w for w in self.warnings):
                print("  2. Run integration tests: python run_kroger_auth_tests.py --integration")
                print("  3. Run E2E tests: python run_kroger_auth_tests.py --e2e")
            else:
                print("  2. Start Kroger MCP server: python kroger_mcp_server.py")
                print("  3. Then run integration tests: python run_kroger_auth_tests.py --integration")
            print("  4. Run all tests: python run_kroger_auth_tests.py --all")
            return True
        else:
            print("\n✗ Test environment has issues that need to be resolved.")
            return False


def main():
    """Main validation function."""
    validator = TestEnvironmentValidator()
    success = validator.validate_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
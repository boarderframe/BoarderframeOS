#!/usr/bin/env python3
"""
Quick UI Component Test Runner
Simple script to run UI component tests and display results
"""

import asyncio
import subprocess
import sys
import os


def print_header():
    """Print header"""
    print("=" * 60)
    print("UI Component Test Runner")
    print("=" * 60)
    print("Testing Corporate HQ, Agent Cortex, and Agent Communication Center")
    print()


def check_dependencies():
    """Check if required dependencies are installed"""
    missing_deps = []
    
    try:
        import httpx
    except ImportError:
        missing_deps.append("httpx")
        
    try:
        import bs4
    except ImportError:
        missing_deps.append("beautifulsoup4")
        
    if missing_deps:
        print("❌ Missing dependencies:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\nInstall with: pip install " + " ".join(missing_deps))
        return False
        
    return True


async def main():
    """Main function"""
    print_header()
    
    # Check if we're in the right directory
    if not os.path.exists("test_ui_components.py"):
        print("❌ Error: test_ui_components.py not found")
        print("Please run this script from the BoarderframeOS root directory")
        return False
        
    # Check dependencies
    if not check_dependencies():
        return False
        
    print("🚀 Starting UI component tests...")
    print()
    
    try:
        # Run the comprehensive test script
        result = subprocess.run([
            sys.executable, "test_ui_components.py"
        ], capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n✅ UI component tests completed successfully!")
        else:
            print("\n⚠️  UI component tests completed with issues")
            
    except FileNotFoundError:
        print("❌ Error: Python executable not found")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False
        
    # Show available resources
    print("\n📊 Available Resources:")
    print("- Test script: test_ui_components.py")
    print("- Visual dashboard: ui_component_test_dashboard.html")
    print("- Quick runner: run_ui_tests.py (this script)")
    
    print("\n🔗 Quick Links:")
    print("- Corporate HQ: http://localhost:8888")
    print("- Agent Cortex: http://localhost:8889") 
    print("- Agent Communication Center: http://localhost:8890")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
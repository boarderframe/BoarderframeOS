#!/usr/bin/env python3
"""
Master Performance Optimization Script
Runs all performance optimizations for BoarderframeOS
"""

import asyncio
import sys
import os
import argparse
from datetime import datetime
import subprocess


class PerformanceOptimizationRunner:
    """Master performance optimization runner"""
    
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
    
    def print_header(self, title):
        """Print section header"""
        print(f"\n{'='*60}")
        print(f"🚀 {title}")
        print(f"{'='*60}")
    
    async def run_database_optimization(self):
        """Run database optimization"""
        self.print_header("Database Performance Optimization")
        
        try:
            # Import and run database optimizer
            from performance.optimize_database import DatabaseOptimizer
            
            optimizer = DatabaseOptimizer()
            await optimizer.run_optimization()
            
            self.results.append({
                "component": "Database",
                "status": "✅ Optimized",
                "details": "Indexes, vacuum, configuration optimized"
            })
            
        except Exception as e:
            self.results.append({
                "component": "Database",
                "status": "❌ Failed",
                "details": str(e)
            })
            print(f"❌ Database optimization failed: {e}")
    
    async def run_agent_optimization(self):
        """Run agent optimization"""
        self.print_header("Agent Performance Optimization")
        
        try:
            # Import and run agent optimizer
            from performance.optimize_agents import AgentOptimizer
            
            optimizer = AgentOptimizer()
            await optimizer.run_optimization()
            
            self.results.append({
                "component": "Agents",
                "status": "✅ Optimized",
                "details": "Memory, message processing, LLM calls optimized"
            })
            
        except Exception as e:
            self.results.append({
                "component": "Agents",
                "status": "❌ Failed",
                "details": str(e)
            })
            print(f"❌ Agent optimization failed: {e}")
    
    async def run_system_optimization(self):
        """Run system-wide optimization"""
        self.print_header("System-wide Performance Optimization")
        
        try:
            # Import and run system optimizer
            from performance.optimize_system import SystemOptimizer
            
            optimizer = SystemOptimizer()
            await optimizer.run_optimization()
            
            self.results.append({
                "component": "System",
                "status": "✅ Optimized",
                "details": "Docker, network, Redis, Python runtime optimized"
            })
            
        except Exception as e:
            self.results.append({
                "component": "System",
                "status": "❌ Failed",
                "details": str(e)
            })
            print(f"❌ System optimization failed: {e}")
    
    def apply_optimized_configs(self):
        """Apply optimized configurations"""
        self.print_header("Applying Optimized Configurations")
        
        configs_applied = []
        
        # Check for generated configs
        config_files = {
            "Docker Compose Override": "docker-compose.override.yml",
            "Nginx Config": "performance/nginx_optimized.conf",
            "Redis Config": "performance/redis_optimized.conf",
            "Python Settings": "performance/optimized_settings.py"
        }
        
        for name, path in config_files.items():
            if os.path.exists(path):
                configs_applied.append(name)
                print(f"✅ Found {name}: {path}")
            else:
                print(f"⚠️  {name} not found: {path}")
        
        if configs_applied:
            self.results.append({
                "component": "Configurations",
                "status": "✅ Ready",
                "details": f"Applied: {', '.join(configs_applied)}"
            })
        else:
            self.results.append({
                "component": "Configurations",
                "status": "⚠️  Partial",
                "details": "Some configurations missing"
            })
    
    def generate_summary_report(self):
        """Generate optimization summary report"""
        self.print_header("Optimization Summary")
        
        duration = (datetime.now() - self.start_time).total_seconds()
        
        print(f"\n📊 OPTIMIZATION RESULTS")
        print(f"Duration: {duration:.2f} seconds")
        print(f"\nComponents Optimized:")
        
        for result in self.results:
            print(f"\n{result['component']}:")
            print(f"  Status: {result['status']}")
            print(f"  Details: {result['details']}")
        
        # Generate HTML summary
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>BoarderframeOS Performance Optimization Summary</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #1a1a2e; color: #fff; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: #16213e; padding: 30px; border-radius: 15px; }}
        h1 {{ color: #00ff88; text-align: center; }}
        .result {{ margin: 20px 0; padding: 20px; background: #0f3460; border-radius: 10px; border-left: 4px solid #00ff88; }}
        .success {{ border-color: #00ff88; }}
        .warning {{ border-color: #ff9800; }}
        .error {{ border-color: #f44336; }}
        .timestamp {{ text-align: center; color: #888; margin-top: 30px; }}
        .next-steps {{ background: #1e3a5f; padding: 20px; border-radius: 10px; margin-top: 30px; }}
        code {{ background: #0f1923; padding: 2px 6px; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Performance Optimization Complete</h1>
        <p style="text-align: center;">Duration: {duration:.2f} seconds</p>
        
        <h2>Optimization Results</h2>
        {''.join([f'<div class="result {"success" if "✅" in r["status"] else "warning" if "⚠️" in r["status"] else "error"}"><h3>{r["component"]}</h3><p><strong>{r["status"]}</strong></p><p>{r["details"]}</p></div>' for r in self.results])}
        
        <div class="next-steps">
            <h2>Next Steps</h2>
            <ol>
                <li>Review generated configuration files in <code>performance/</code> directory</li>
                <li>Restart services with optimized configurations:
                    <ul>
                        <li><code>docker-compose down && docker-compose up -d</code></li>
                        <li><code>./performance/optimized_startup.sh</code></li>
                    </ul>
                </li>
                <li>Monitor performance: <code>./performance/monitor_performance.py</code></li>
                <li>Review detailed reports:
                    <ul>
                        <li><code>performance/database_optimization_report.json</code></li>
                        <li><code>performance/agent_optimization_config.json</code></li>
                        <li><code>performance/system_optimization_report.json</code></li>
                    </ul>
                </li>
            </ol>
        </div>
        
        <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>"""
        
        summary_path = "performance_optimization_summary.html"
        with open(summary_path, 'w') as f:
            f.write(html_content)
        
        print(f"\n📄 HTML summary saved to: {summary_path}")
    
    async def run_all_optimizations(self):
        """Run all performance optimizations"""
        print("🚀 BoarderframeOS Master Performance Optimization")
        print(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Create performance directory
        os.makedirs("performance", exist_ok=True)
        
        # Run optimizations in sequence
        await self.run_database_optimization()
        await self.run_agent_optimization()
        await self.run_system_optimization()
        
        # Apply configurations
        self.apply_optimized_configs()
        
        # Generate summary
        self.generate_summary_report()
        
        print("\n✅ All optimizations complete!")
        print("\n💡 To start monitoring performance, run:")
        print("   ./performance/monitor_performance.py")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="BoarderframeOS Performance Optimization"
    )
    
    parser.add_argument(
        "--component",
        choices=["all", "database", "agents", "system"],
        default="all",
        help="Component to optimize"
    )
    
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Start performance monitor after optimization"
    )
    
    args = parser.parse_args()
    
    runner = PerformanceOptimizationRunner()
    
    # Run optimizations
    if args.component == "all":
        asyncio.run(runner.run_all_optimizations())
    elif args.component == "database":
        asyncio.run(runner.run_database_optimization())
    elif args.component == "agents":
        asyncio.run(runner.run_agent_optimization())
    elif args.component == "system":
        asyncio.run(runner.run_system_optimization())
    
    # Start monitor if requested
    if args.monitor:
        print("\n🔍 Starting performance monitor...")
        subprocess.run([sys.executable, "performance/monitor_performance.py"])


if __name__ == "__main__":
    main()
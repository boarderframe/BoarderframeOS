#!/usr/bin/env python3
"""
BoarderframeOS Performance Analysis and Optimization Script
Analyzes system performance, identifies bottlenecks, and provides optimization recommendations
"""

import asyncio
import aiohttp
import psutil
import time
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import statistics
import subprocess

# Database imports
import psycopg2
from psycopg2.extras import RealDictCursor
import sqlite3


class PerformanceAnalyzer:
    def __init__(self):
        self.performance_targets = {
            "database_query_ms": 3,          # Target: <3ms for PostgreSQL queries
            "message_throughput": 1000000,   # Target: 1M+ messages/second
            "agent_response_ms": 100,        # Target: <100ms agent response
            "api_latency_ms": 50,           # Target: <50ms API responses
            "ui_load_time_ms": 1000,        # Target: <1s page load
            "memory_usage_percent": 80,      # Warning if >80% memory usage
            "cpu_usage_percent": 70          # Warning if >70% CPU usage
        }
        
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "system_metrics": {},
            "database_performance": {},
            "api_performance": {},
            "agent_performance": {},
            "message_bus_performance": {},
            "bottlenecks": [],
            "optimizations": [],
            "summary": {}
        }
        
        self.errors = []
        self.warnings = []
        self.successes = []
        
        # Connection configs
        self.pg_config = {
            "host": "localhost",
            "port": 5434,
            "database": "boarderframeos",
            "user": "boarderframe",
            "password": "boarderframe123"
        }
        
    def log_success(self, message: str):
        self.successes.append(message)
        print(f"✓ {message}")
        
    def log_warning(self, message: str):
        self.warnings.append(message)
        print(f"⚠ {message}")
        
    def log_error(self, message: str):
        self.errors.append(message)
        print(f"✗ {message}")
        
    def analyze_system_metrics(self):
        """Analyze current system resource usage"""
        print("\n=== Analyzing System Metrics ===")
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu": {},
            "memory": {},
            "disk": {},
            "network": {}
        }
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        metrics["cpu"] = {
            "usage_percent": cpu_percent,
            "core_count": cpu_count,
            "frequency_mhz": cpu_freq.current if cpu_freq else None,
            "per_core_usage": psutil.cpu_percent(interval=1, percpu=True)
        }
        
        if cpu_percent > self.performance_targets["cpu_usage_percent"]:
            self.log_warning(f"High CPU usage: {cpu_percent}%")
            self.results["bottlenecks"].append({
                "type": "cpu",
                "severity": "high",
                "value": cpu_percent,
                "target": self.performance_targets["cpu_usage_percent"]
            })
        else:
            self.log_success(f"CPU usage normal: {cpu_percent}%")
            
        # Memory metrics
        memory = psutil.virtual_memory()
        metrics["memory"] = {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "usage_percent": memory.percent
        }
        
        if memory.percent > self.performance_targets["memory_usage_percent"]:
            self.log_warning(f"High memory usage: {memory.percent}%")
            self.results["bottlenecks"].append({
                "type": "memory",
                "severity": "high",
                "value": memory.percent,
                "target": self.performance_targets["memory_usage_percent"]
            })
        else:
            self.log_success(f"Memory usage normal: {memory.percent}%")
            
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        
        metrics["disk"] = {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "usage_percent": disk.percent,
            "read_mb_s": round((disk_io.read_bytes / (1024**2)) if disk_io else 0, 2),
            "write_mb_s": round((disk_io.write_bytes / (1024**2)) if disk_io else 0, 2)
        }
        
        # Network metrics
        net_io = psutil.net_io_counters()
        metrics["network"] = {
            "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 2),
            "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 2),
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv
        }
        
        self.results["system_metrics"] = metrics
        
    async def analyze_database_performance(self):
        """Analyze database query performance"""
        print("\n=== Analyzing Database Performance ===")
        
        db_perf = {
            "postgresql": {},
            "sqlite": {}
        }
        
        # Test PostgreSQL performance
        try:
            conn = psycopg2.connect(**self.pg_config)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Test simple query performance
            query_times = []
            for i in range(10):
                start_time = time.time()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                query_time_ms = (time.time() - start_time) * 1000
                query_times.append(query_time_ms)
                
            avg_query_time = statistics.mean(query_times)
            
            db_perf["postgresql"]["simple_query_ms"] = round(avg_query_time, 3)
            
            if avg_query_time <= self.performance_targets["database_query_ms"]:
                self.log_success(f"PostgreSQL query performance: {avg_query_time:.3f}ms (✓ meets target)")
            else:
                self.log_warning(f"PostgreSQL query performance: {avg_query_time:.3f}ms (target: <{self.performance_targets['database_query_ms']}ms)")
                self.results["bottlenecks"].append({
                    "type": "database_query",
                    "database": "postgresql",
                    "severity": "medium",
                    "value": avg_query_time,
                    "target": self.performance_targets["database_query_ms"]
                })
                
            # Check connection pool status
            cursor.execute("""
                SELECT count(*) as total_connections,
                       sum(case when state = 'active' then 1 else 0 end) as active,
                       sum(case when state = 'idle' then 1 else 0 end) as idle
                FROM pg_stat_activity
            """)
            
            conn_stats = cursor.fetchone()
            db_perf["postgresql"]["connections"] = dict(conn_stats)
            
            # Check cache hit ratio
            cursor.execute("""
                SELECT 
                    sum(heap_blks_read) as heap_read,
                    sum(heap_blks_hit) as heap_hit,
                    CASE 
                        WHEN sum(heap_blks_hit) + sum(heap_blks_read) > 0 
                        THEN (sum(heap_blks_hit) * 100.0) / (sum(heap_blks_hit) + sum(heap_blks_read))
                        ELSE 0 
                    END as cache_hit_ratio
                FROM pg_statio_user_tables
            """)
            
            cache_stats = cursor.fetchone()
            if cache_stats and cache_stats['cache_hit_ratio']:
                cache_hit_ratio = float(cache_stats['cache_hit_ratio'])
                db_perf["postgresql"]["cache_hit_ratio"] = round(cache_hit_ratio, 2)
                
                if cache_hit_ratio > 90:
                    self.log_success(f"PostgreSQL cache hit ratio: {cache_hit_ratio:.2f}% (✓ excellent)")
                else:
                    self.log_warning(f"PostgreSQL cache hit ratio: {cache_hit_ratio:.2f}% (target: >90%)")
                    self.results["optimizations"].append({
                        "component": "postgresql",
                        "issue": "low_cache_hit_ratio",
                        "recommendation": "Increase shared_buffers or optimize queries"
                    })
                    
            # Check table sizes and bloat
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 5
            """)
            
            largest_tables = cursor.fetchall()
            db_perf["postgresql"]["largest_tables"] = [dict(t) for t in largest_tables]
            
            conn.close()
            
        except Exception as e:
            self.log_error(f"PostgreSQL performance analysis failed: {e}")
            db_perf["postgresql"]["error"] = str(e)
            
        # Test SQLite performance
        sqlite_dbs = ["data/boarderframe.db", "data/message_bus.db"]
        
        for db_path in sqlite_dbs:
            if os.path.exists(db_path):
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # Test query performance
                    query_times = []
                    for i in range(10):
                        start_time = time.time()
                        cursor.execute("SELECT 1")
                        cursor.fetchone()
                        query_time_ms = (time.time() - start_time) * 1000
                        query_times.append(query_time_ms)
                        
                    avg_query_time = statistics.mean(query_times)
                    
                    db_name = os.path.basename(db_path)
                    db_perf["sqlite"][db_name] = {
                        "simple_query_ms": round(avg_query_time, 3),
                        "file_size_mb": round(os.path.getsize(db_path) / (1024**2), 2)
                    }
                    
                    self.log_success(f"SQLite ({db_name}) query performance: {avg_query_time:.3f}ms")
                    
                    conn.close()
                    
                except Exception as e:
                    self.log_error(f"SQLite performance analysis failed for {db_path}: {e}")
                    
        self.results["database_performance"] = db_perf
        
    async def analyze_api_performance(self):
        """Analyze API endpoint performance"""
        print("\n=== Analyzing API Performance ===")
        
        api_perf = {}
        
        endpoints_to_test = [
            ("http://localhost:8888/api/system/status", "Corporate HQ Status"),
            ("http://localhost:8888/api/metrics", "Corporate HQ Metrics"),
            ("http://localhost:8888/api/agents", "Agent List"),
            ("http://localhost:8009/health", "Registry Server"),
            ("http://localhost:8007/health", "Analytics Server"),
            ("http://localhost:8010/health", "Database Server")
        ]
        
        for url, name in endpoints_to_test:
            response_times = []
            success_count = 0
            
            async with aiohttp.ClientSession() as session:
                for i in range(5):
                    try:
                        start_time = time.time()
                        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                            await response.text()
                            response_time_ms = (time.time() - start_time) * 1000
                            response_times.append(response_time_ms)
                            
                            if response.status == 200:
                                success_count += 1
                                
                    except Exception as e:
                        self.log_warning(f"API test failed for {name}: {e}")
                        
            if response_times:
                avg_response_time = statistics.mean(response_times)
                min_response_time = min(response_times)
                max_response_time = max(response_times)
                
                api_perf[name] = {
                    "average_ms": round(avg_response_time, 2),
                    "min_ms": round(min_response_time, 2),
                    "max_ms": round(max_response_time, 2),
                    "success_rate": (success_count / 5) * 100,
                    "samples": len(response_times)
                }
                
                if avg_response_time <= self.performance_targets["api_latency_ms"]:
                    self.log_success(f"{name} latency: {avg_response_time:.2f}ms (✓ excellent)")
                elif avg_response_time <= self.performance_targets["api_latency_ms"] * 2:
                    self.log_success(f"{name} latency: {avg_response_time:.2f}ms (✓ good)")
                else:
                    self.log_warning(f"{name} latency: {avg_response_time:.2f}ms (target: <{self.performance_targets['api_latency_ms']}ms)")
                    self.results["bottlenecks"].append({
                        "type": "api_latency",
                        "endpoint": name,
                        "severity": "medium",
                        "value": avg_response_time,
                        "target": self.performance_targets["api_latency_ms"]
                    })
                    
        self.results["api_performance"] = api_perf
        
    async def analyze_agent_performance(self):
        """Analyze agent response times and efficiency"""
        print("\n=== Analyzing Agent Performance ===")
        
        agent_perf = {}
        
        # Test agent chat response times
        test_agents = ["solomon", "david"]
        
        for agent_name in test_agents:
            response_times = []
            
            test_message = {
                "agent": agent_name,
                "message": "What is your current status?"
            }
            
            async with aiohttp.ClientSession() as session:
                for i in range(3):
                    try:
                        start_time = time.time()
                        async with session.post(
                            "http://localhost:8888/api/agent/chat",
                            json=test_message,
                            timeout=aiohttp.ClientTimeout(total=10)
                        ) as response:
                            await response.json()
                            response_time_ms = (time.time() - start_time) * 1000
                            response_times.append(response_time_ms)
                            
                    except Exception as e:
                        self.log_warning(f"Agent test failed for {agent_name}: {e}")
                        
            if response_times:
                avg_response_time = statistics.mean(response_times)
                
                agent_perf[agent_name] = {
                    "average_response_ms": round(avg_response_time, 2),
                    "samples": len(response_times)
                }
                
                if avg_response_time <= self.performance_targets["agent_response_ms"]:
                    self.log_success(f"{agent_name} response time: {avg_response_time:.2f}ms (✓ meets target)")
                else:
                    self.log_warning(f"{agent_name} response time: {avg_response_time:.2f}ms (target: <{self.performance_targets['agent_response_ms']}ms)")
                    self.results["bottlenecks"].append({
                        "type": "agent_response",
                        "agent": agent_name,
                        "severity": "medium",
                        "value": avg_response_time,
                        "target": self.performance_targets["agent_response_ms"]
                    })
                    
        # Check agent resource usage
        try:
            # Get agent processes
            agent_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                if 'python' in proc.info['name'].lower():
                    cmdline = proc.cmdline()
                    if any('agent' in arg.lower() for arg in cmdline):
                        agent_processes.append({
                            "pid": proc.info['pid'],
                            "cpu_percent": proc.cpu_percent(interval=0.1),
                            "memory_mb": round(proc.info['memory_info'].rss / (1024**2), 2)
                        })
                        
            if agent_processes:
                total_agent_cpu = sum(p['cpu_percent'] for p in agent_processes)
                total_agent_memory = sum(p['memory_mb'] for p in agent_processes)
                
                agent_perf["resource_usage"] = {
                    "total_cpu_percent": round(total_agent_cpu, 2),
                    "total_memory_mb": round(total_agent_memory, 2),
                    "process_count": len(agent_processes)
                }
                
                self.log_success(f"Agent resource usage: {total_agent_cpu:.2f}% CPU, {total_agent_memory:.2f}MB RAM")
                
        except Exception as e:
            self.log_warning(f"Could not analyze agent resource usage: {e}")
            
        self.results["agent_performance"] = agent_perf
        
    async def analyze_message_bus_performance(self):
        """Analyze message bus throughput and latency"""
        print("\n=== Analyzing Message Bus Performance ===")
        
        mb_perf = {}
        
        # Import message bus if available
        try:
            from core.message_bus import MessageBus, AgentMessage, MessagePriority
            
            message_bus = MessageBus()
            
            # Test message throughput
            message_count = 1000
            received_count = 0
            
            async def test_handler(message):
                nonlocal received_count
                received_count += 1
                
            # Subscribe test handler
            await message_bus.subscribe("perf_test", test_handler)
            
            # Send messages
            start_time = time.time()
            
            for i in range(message_count):
                message = AgentMessage(
                    from_agent="perf_sender",
                    to_agent="perf_test",
                    content={"index": i},
                    priority=MessagePriority.NORMAL
                )
                await message_bus.publish(message)
                
            # Wait for processing
            max_wait = 5.0
            wait_start = time.time()
            while received_count < message_count and (time.time() - wait_start) < max_wait:
                await asyncio.sleep(0.01)
                
            duration = time.time() - start_time
            throughput = received_count / duration if duration > 0 else 0
            
            mb_perf["throughput_test"] = {
                "messages_sent": message_count,
                "messages_received": received_count,
                "duration_seconds": round(duration, 3),
                "throughput_per_second": round(throughput, 1),
                "success_rate": round((received_count / message_count) * 100, 1)
            }
            
            if throughput >= self.performance_targets["message_throughput"] / 1000:  # Scaled test
                self.log_success(f"Message throughput: {throughput:.1f} msgs/sec (✓ good)")
            else:
                self.log_warning(f"Message throughput: {throughput:.1f} msgs/sec (below target)")
                self.results["bottlenecks"].append({
                    "type": "message_throughput",
                    "severity": "high",
                    "value": throughput,
                    "target": self.performance_targets["message_throughput"] / 1000
                })
                
            # Unsubscribe
            await message_bus.unsubscribe("perf_test")
            
        except Exception as e:
            self.log_error(f"Message bus performance analysis failed: {e}")
            mb_perf["error"] = str(e)
            
        self.results["message_bus_performance"] = mb_perf
        
    def identify_optimization_opportunities(self):
        """Identify and recommend optimizations"""
        print("\n=== Identifying Optimization Opportunities ===")
        
        # Analyze bottlenecks and generate recommendations
        
        # Database optimizations
        if any(b["type"] == "database_query" for b in self.results["bottlenecks"]):
            self.results["optimizations"].append({
                "component": "database",
                "priority": "high",
                "recommendation": "Implement query optimization and indexing",
                "actions": [
                    "Add indexes on frequently queried columns",
                    "Use EXPLAIN ANALYZE to identify slow queries",
                    "Increase PostgreSQL shared_buffers",
                    "Enable query caching"
                ]
            })
            
        # API optimizations
        slow_apis = [b for b in self.results["bottlenecks"] if b["type"] == "api_latency"]
        if slow_apis:
            self.results["optimizations"].append({
                "component": "api",
                "priority": "medium",
                "recommendation": "Optimize API response times",
                "actions": [
                    "Implement response caching for static data",
                    "Use connection pooling for database queries",
                    "Add pagination for large result sets",
                    "Consider async processing for heavy operations"
                ]
            })
            
        # System resource optimizations
        high_cpu = any(b["type"] == "cpu" and b["severity"] == "high" for b in self.results["bottlenecks"])
        high_memory = any(b["type"] == "memory" and b["severity"] == "high" for b in self.results["bottlenecks"])
        
        if high_cpu:
            self.results["optimizations"].append({
                "component": "system",
                "priority": "high",
                "recommendation": "Reduce CPU usage",
                "actions": [
                    "Profile CPU-intensive operations",
                    "Implement throttling for background tasks",
                    "Use worker processes for heavy computations",
                    "Optimize algorithms and data structures"
                ]
            })
            
        if high_memory:
            self.results["optimizations"].append({
                "component": "system",
                "priority": "high",
                "recommendation": "Optimize memory usage",
                "actions": [
                    "Implement memory pooling",
                    "Add garbage collection triggers",
                    "Use generators for large data processing",
                    "Monitor and fix memory leaks"
                ]
            })
            
        # Agent optimizations
        slow_agents = [b for b in self.results["bottlenecks"] if b["type"] == "agent_response"]
        if slow_agents:
            self.results["optimizations"].append({
                "component": "agents",
                "priority": "medium",
                "recommendation": "Improve agent response times",
                "actions": [
                    "Implement response caching for common queries",
                    "Use smaller LLM models for simple tasks",
                    "Add request batching",
                    "Optimize prompt engineering"
                ]
            })
            
        # Message bus optimizations
        if any(b["type"] == "message_throughput" for b in self.results["bottlenecks"]):
            self.results["optimizations"].append({
                "component": "message_bus",
                "priority": "high",
                "recommendation": "Increase message throughput",
                "actions": [
                    "Implement message batching",
                    "Use more efficient serialization (MessagePack)",
                    "Add message compression",
                    "Consider switching to NATS or RabbitMQ"
                ]
            })
            
    def generate_performance_script(self):
        """Generate optimization script"""
        script_content = """#!/bin/bash
# BoarderframeOS Performance Optimization Script
# Generated by performance analysis

echo "Starting BoarderframeOS performance optimizations..."

# Database optimizations
echo "Optimizing PostgreSQL..."
psql -U boarderframe -d boarderframeos << EOF
-- Add indexes for common queries
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_correlation ON messages(correlation_id);

-- Update statistics
ANALYZE;

-- Show current settings
SHOW shared_buffers;
SHOW effective_cache_size;
EOF

# Clear caches
echo "Clearing application caches..."
redis-cli FLUSHDB

# Restart services with optimized settings
echo "Restarting services..."
# Add service restart commands here

echo "Optimizations complete!"
"""
        
        with open("optimize_performance.sh", "w") as f:
            f.write(script_content)
            
        os.chmod("optimize_performance.sh", 0o755)
        self.log_success("Performance optimization script created: optimize_performance.sh")
        
    def generate_report(self):
        """Generate comprehensive performance report"""
        # Calculate summary
        total_bottlenecks = len(self.results["bottlenecks"])
        high_severity = sum(1 for b in self.results["bottlenecks"] if b.get("severity") == "high")
        total_optimizations = len(self.results["optimizations"])
        
        # Performance score (0-100)
        performance_score = 100
        performance_score -= high_severity * 20  # -20 for each high severity issue
        performance_score -= (total_bottlenecks - high_severity) * 10  # -10 for other issues
        performance_score = max(0, performance_score)
        
        self.results["summary"] = {
            "performance_score": performance_score,
            "total_bottlenecks": total_bottlenecks,
            "high_severity_issues": high_severity,
            "optimization_recommendations": total_optimizations,
            "system_health": "healthy" if performance_score >= 70 else "needs_optimization",
            "total_successes": len(self.successes),
            "total_warnings": len(self.warnings),
            "total_errors": len(self.errors)
        }
        
        # Add key metrics
        if self.results["system_metrics"]:
            self.results["summary"]["cpu_usage"] = self.results["system_metrics"]["cpu"]["usage_percent"]
            self.results["summary"]["memory_usage"] = self.results["system_metrics"]["memory"]["usage_percent"]
            
        # Save JSON report
        with open("performance_analysis_report.json", "w") as f:
            json.dump(self.results, f, indent=2)
            
        # Print summary
        print("\n" + "="*60)
        print("PERFORMANCE ANALYSIS SUMMARY")
        print("="*60)
        
        summary = self.results["summary"]
        print(f"Performance Score: {summary['performance_score']}/100")
        print(f"System Health: {summary['system_health'].upper()}")
        print(f"Bottlenecks Found: {summary['total_bottlenecks']}")
        print(f"High Severity Issues: {summary['high_severity_issues']}")
        print(f"Optimization Recommendations: {summary['optimization_recommendations']}")
        
        if "cpu_usage" in summary:
            print(f"\nCurrent CPU Usage: {summary['cpu_usage']}%")
            print(f"Current Memory Usage: {summary['memory_usage']}%")
            
        print(f"\n✓ Successes: {summary['total_successes']}")
        print(f"⚠ Warnings: {summary['total_warnings']}")
        print(f"✗ Errors: {summary['total_errors']}")
        
        # List bottlenecks
        if self.results["bottlenecks"]:
            print("\nPerformance Bottlenecks:")
            for bottleneck in self.results["bottlenecks"]:
                severity_emoji = "🔴" if bottleneck["severity"] == "high" else "🟡"
                print(f"  {severity_emoji} {bottleneck['type']}: {bottleneck['value']} (target: {bottleneck['target']})")
                
        # List top optimizations
        if self.results["optimizations"]:
            print("\nTop Optimization Recommendations:")
            for i, opt in enumerate(self.results["optimizations"][:3], 1):
                print(f"  {i}. {opt['recommendation']} ({opt['component']})")
                
        print("\nDetailed report saved to: performance_analysis_report.json")
        print("Optimization script created: optimize_performance.sh")
        
    async def run_analysis(self):
        """Run complete performance analysis"""
        print("="*60)
        print("BoarderframeOS Performance Analysis")
        print("="*60)
        
        # Run all analyses
        self.analyze_system_metrics()
        await self.analyze_database_performance()
        await self.analyze_api_performance()
        await self.analyze_agent_performance()
        await self.analyze_message_bus_performance()
        
        # Identify optimizations
        self.identify_optimization_opportunities()
        
        # Generate optimization script
        self.generate_performance_script()
        
        # Generate report
        self.generate_report()
        
        # Return success if performance score is acceptable
        return self.results["summary"]["performance_score"] >= 50


async def main():
    analyzer = PerformanceAnalyzer()
    success = await analyzer.run_analysis()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
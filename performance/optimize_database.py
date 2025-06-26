#!/usr/bin/env python3
"""
Database Performance Optimization Script
Optimizes PostgreSQL and SQLite database performance
"""

import asyncio
import asyncpg
import aiosqlite
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json
import os


class DatabaseOptimizer:
    """Database performance optimization tool"""
    
    def __init__(self):
        self.pg_conn = None
        self.sqlite_conn = None
        self.metrics = {
            "before": {},
            "after": {},
            "improvements": {}
        }
    
    async def connect_postgres(self):
        """Connect to PostgreSQL"""
        try:
            self.pg_conn = await asyncpg.connect(
                host='localhost',
                port=5434,
                user='boarderframe',
                password='securepass123',
                database='boarderframeos'
            )
            print("✅ Connected to PostgreSQL")
        except Exception as e:
            print(f"❌ PostgreSQL connection failed: {e}")
            return False
        return True
    
    async def connect_sqlite(self):
        """Connect to SQLite"""
        try:
            self.sqlite_conn = await aiosqlite.connect('data/boarderframe.db')
            print("✅ Connected to SQLite")
        except Exception as e:
            print(f"❌ SQLite connection failed: {e}")
            return False
        return True
    
    async def analyze_postgres_performance(self) -> Dict:
        """Analyze PostgreSQL performance metrics"""
        if not self.pg_conn:
            return {}
        
        metrics = {}
        
        # Database size
        size_query = """
        SELECT pg_database_size(current_database()) as size,
               pg_size_pretty(pg_database_size(current_database())) as size_pretty
        """
        result = await self.pg_conn.fetchrow(size_query)
        metrics['database_size'] = result['size']
        metrics['database_size_pretty'] = result['size_pretty']
        
        # Table sizes
        table_sizes_query = """
        SELECT schemaname, tablename, 
               pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
               pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
        FROM pg_tables 
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        LIMIT 10
        """
        metrics['table_sizes'] = await self.pg_conn.fetch(table_sizes_query)
        
        # Index usage
        index_usage_query = """
        SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
        FROM pg_stat_user_indexes
        ORDER BY idx_scan DESC
        LIMIT 10
        """
        metrics['index_usage'] = await self.pg_conn.fetch(index_usage_query)
        
        # Slow queries (if pg_stat_statements is available)
        try:
            slow_queries = """
            SELECT query, calls, mean_exec_time, total_exec_time
            FROM pg_stat_statements
            WHERE query NOT LIKE '%pg_stat_statements%'
            ORDER BY mean_exec_time DESC
            LIMIT 10
            """
            metrics['slow_queries'] = await self.pg_conn.fetch(slow_queries)
        except:
            metrics['slow_queries'] = []
        
        # Cache hit ratio
        cache_hit_query = """
        SELECT 
            sum(heap_blks_read) as heap_read,
            sum(heap_blks_hit) as heap_hit,
            sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as ratio
        FROM pg_statio_user_tables
        """
        cache_result = await self.pg_conn.fetchrow(cache_hit_query)
        metrics['cache_hit_ratio'] = float(cache_result['ratio']) if cache_result['ratio'] else 0
        
        return metrics
    
    async def optimize_postgres_indexes(self):
        """Optimize PostgreSQL indexes"""
        print("\n🔧 Optimizing PostgreSQL indexes...")
        
        # Find missing indexes
        missing_indexes_query = """
        SELECT schemaname, tablename, attname, n_tup_ins + n_tup_upd + n_tup_del as total_writes,
               pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size
        FROM pg_stat_user_tables
        JOIN pg_attribute ON attrelid = (schemaname||'.'||tablename)::regclass
        WHERE attnum > 0 AND NOT attisdropped
        AND schemaname NOT IN ('pg_catalog', 'information_schema')
        AND n_tup_ins + n_tup_upd + n_tup_del > 1000
        AND NOT EXISTS (
            SELECT 1 FROM pg_index 
            WHERE pg_index.indrelid = (schemaname||'.'||tablename)::regclass
            AND attnum = ANY(indkey)
        )
        LIMIT 10
        """
        
        try:
            missing = await self.pg_conn.fetch(missing_indexes_query)
            
            if missing:
                print(f"Found {len(missing)} columns that might benefit from indexes")
                
                # Create indexes for high-write columns
                for row in missing[:5]:  # Limit to 5 to avoid over-indexing
                    index_name = f"idx_{row['tablename']}_{row['attname']}"
                    create_index = f"""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS {index_name}
                    ON {row['schemaname']}.{row['tablename']} ({row['attname']})
                    """
                    
                    try:
                        print(f"Creating index: {index_name}")
                        await self.pg_conn.execute(create_index)
                        print(f"✅ Created index: {index_name}")
                    except Exception as e:
                        print(f"⚠️  Could not create index {index_name}: {e}")
        except Exception as e:
            print(f"⚠️  Could not analyze missing indexes: {e}")
        
        # Remove unused indexes
        unused_indexes_query = """
        SELECT schemaname, tablename, indexname, idx_scan
        FROM pg_stat_user_indexes
        WHERE idx_scan = 0
        AND indexname NOT LIKE 'pg_%'
        AND schemaname NOT IN ('pg_catalog', 'information_schema')
        """
        
        unused = await self.pg_conn.fetch(unused_indexes_query)
        if unused:
            print(f"\nFound {len(unused)} unused indexes")
            for idx in unused:
                print(f"⚠️  Unused index: {idx['indexname']} on {idx['tablename']}")
    
    async def vacuum_postgres(self):
        """Run VACUUM and ANALYZE on PostgreSQL"""
        print("\n🧹 Running VACUUM ANALYZE...")
        
        tables_query = """
        SELECT schemaname, tablename 
        FROM pg_tables 
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        """
        
        tables = await self.pg_conn.fetch(tables_query)
        
        for table in tables:
            try:
                vacuum_sql = f"VACUUM ANALYZE {table['schemaname']}.{table['tablename']}"
                await self.pg_conn.execute(vacuum_sql)
                print(f"✅ Vacuumed {table['tablename']}")
            except Exception as e:
                print(f"⚠️  Could not vacuum {table['tablename']}: {e}")
    
    async def optimize_postgres_config(self):
        """Suggest PostgreSQL configuration optimizations"""
        print("\n📋 PostgreSQL Configuration Recommendations:")
        
        # Get current settings
        settings_query = """
        SELECT name, setting, unit, source
        FROM pg_settings
        WHERE name IN (
            'shared_buffers', 'effective_cache_size', 'work_mem',
            'maintenance_work_mem', 'max_connections', 'checkpoint_segments',
            'checkpoint_completion_target', 'wal_buffers'
        )
        """
        
        settings = await self.pg_conn.fetch(settings_query)
        
        # Get system memory
        total_mem = psutil.virtual_memory().total
        total_mem_mb = total_mem / (1024 * 1024)
        
        recommendations = []
        
        for setting in settings:
            if setting['name'] == 'shared_buffers':
                current_mb = self._parse_memory_setting(setting['setting'], setting['unit'])
                recommended_mb = min(total_mem_mb * 0.25, 8192)  # 25% of RAM, max 8GB
                
                if current_mb < recommended_mb * 0.8:
                    recommendations.append({
                        'setting': 'shared_buffers',
                        'current': f"{current_mb}MB",
                        'recommended': f"{int(recommended_mb)}MB",
                        'reason': 'Increase for better caching'
                    })
            
            elif setting['name'] == 'effective_cache_size':
                current_mb = self._parse_memory_setting(setting['setting'], setting['unit'])
                recommended_mb = total_mem_mb * 0.75  # 75% of RAM
                
                if current_mb < recommended_mb * 0.8:
                    recommendations.append({
                        'setting': 'effective_cache_size',
                        'current': f"{current_mb}MB",
                        'recommended': f"{int(recommended_mb)}MB",
                        'reason': 'Help query planner make better decisions'
                    })
        
        if recommendations:
            print("\nRecommended configuration changes:")
            for rec in recommendations:
                print(f"\n{rec['setting']}:")
                print(f"  Current: {rec['current']}")
                print(f"  Recommended: {rec['recommended']}")
                print(f"  Reason: {rec['reason']}")
        else:
            print("✅ Configuration looks good!")
    
    def _parse_memory_setting(self, value: str, unit: str) -> float:
        """Parse PostgreSQL memory settings to MB"""
        value = float(value)
        
        if unit == 'kB':
            return value / 1024
        elif unit == '8kB':  # PostgreSQL blocks
            return (value * 8) / 1024
        elif unit == 'MB':
            return value
        elif unit == 'GB':
            return value * 1024
        
        return value
    
    async def optimize_sqlite(self):
        """Optimize SQLite database"""
        if not self.sqlite_conn:
            return
        
        print("\n🔧 Optimizing SQLite database...")
        
        # Run VACUUM
        await self.sqlite_conn.execute("VACUUM")
        print("✅ Vacuumed SQLite database")
        
        # Analyze tables
        await self.sqlite_conn.execute("ANALYZE")
        print("✅ Analyzed SQLite tables")
        
        # Optimize settings
        optimizations = [
            ("PRAGMA journal_mode = WAL", "Write-Ahead Logging for better concurrency"),
            ("PRAGMA synchronous = NORMAL", "Balanced durability and performance"),
            ("PRAGMA cache_size = -64000", "64MB cache size"),
            ("PRAGMA temp_store = MEMORY", "Use memory for temporary tables"),
            ("PRAGMA mmap_size = 268435456", "256MB memory-mapped I/O")
        ]
        
        for pragma, description in optimizations:
            try:
                await self.sqlite_conn.execute(pragma)
                print(f"✅ Set {description}")
            except Exception as e:
                print(f"⚠️  Could not set {pragma}: {e}")
        
        await self.sqlite_conn.commit()
    
    async def analyze_query_performance(self):
        """Analyze and optimize slow queries"""
        print("\n🔍 Analyzing query performance...")
        
        # Test queries for agents table
        test_queries = [
            ("SELECT * FROM agents WHERE status = 'active'", "Active agents query"),
            ("SELECT COUNT(*) FROM messages WHERE timestamp > NOW() - INTERVAL '1 hour'", "Recent messages count"),
            ("SELECT * FROM agents JOIN departments ON agents.department_id = departments.id", "Agent department join")
        ]
        
        for query, description in test_queries:
            try:
                # Explain analyze
                explain_query = f"EXPLAIN ANALYZE {query}"
                start = time.time()
                result = await self.pg_conn.fetch(explain_query)
                duration = time.time() - start
                
                print(f"\n{description}:")
                print(f"  Execution time: {duration*1000:.2f}ms")
                
                # Check for sequential scans
                plan_text = '\n'.join([row['QUERY PLAN'] for row in result])
                if 'Seq Scan' in plan_text:
                    print("  ⚠️  Warning: Sequential scan detected - consider adding index")
                
            except Exception as e:
                print(f"  ❌ Could not analyze: {e}")
    
    async def generate_report(self):
        """Generate optimization report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "optimizations_performed": [],
            "recommendations": [],
            "metrics": self.metrics
        }
        
        # Save report
        report_path = "performance/database_optimization_report.json"
        os.makedirs("performance", exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Report saved to: {report_path}")
    
    async def run_optimization(self):
        """Run complete database optimization"""
        print("🚀 Starting Database Performance Optimization")
        print("=" * 60)
        
        # Connect to databases
        if not await self.connect_postgres():
            return
        
        await self.connect_sqlite()
        
        # Analyze before optimization
        print("\n📊 Analyzing current performance...")
        self.metrics['before'] = await self.analyze_postgres_performance()
        
        # Run optimizations
        await self.optimize_postgres_indexes()
        await self.vacuum_postgres()
        await self.optimize_postgres_config()
        
        if self.sqlite_conn:
            await self.optimize_sqlite()
        
        await self.analyze_query_performance()
        
        # Analyze after optimization
        print("\n📊 Analyzing performance after optimization...")
        self.metrics['after'] = await self.analyze_postgres_performance()
        
        # Calculate improvements
        if self.metrics['before'].get('cache_hit_ratio') and self.metrics['after'].get('cache_hit_ratio'):
            before_ratio = self.metrics['before']['cache_hit_ratio']
            after_ratio = self.metrics['after']['cache_hit_ratio']
            improvement = ((after_ratio - before_ratio) / before_ratio) * 100
            
            print(f"\n✨ Cache hit ratio improved by {improvement:.2f}%")
        
        # Generate report
        await self.generate_report()
        
        # Cleanup
        if self.pg_conn:
            await self.pg_conn.close()
        if self.sqlite_conn:
            await self.sqlite_conn.close()
        
        print("\n✅ Database optimization complete!")


async def main():
    """Main entry point"""
    optimizer = DatabaseOptimizer()
    await optimizer.run_optimization()


if __name__ == "__main__":
    asyncio.run(main())
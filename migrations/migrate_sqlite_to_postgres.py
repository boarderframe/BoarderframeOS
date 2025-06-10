#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script for BoarderframeOS
Migrates existing SQLite data to the new PostgreSQL + pgvector setup
"""

import asyncio
import asyncpg
import aiosqlite
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import uuid
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("migration")

@dataclass
class MigrationStats:
    """Track migration statistics"""
    table_name: str
    sqlite_count: int = 0
    postgres_count: int = 0
    migrated_count: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class DatabaseMigrator:
    """Handles the migration from SQLite to PostgreSQL"""
    
    def __init__(self, sqlite_path: Path, postgres_dsn: str):
        self.sqlite_path = sqlite_path
        self.postgres_dsn = postgres_dsn
        self.stats: Dict[str, MigrationStats] = {}
    
    async def migrate_all(self) -> Dict[str, MigrationStats]:
        """Execute complete migration from SQLite to PostgreSQL"""
        logger.info("Starting SQLite to PostgreSQL migration")
        
        # Table migration order (respecting foreign key dependencies)
        migration_order = [
            'agents',
            'departments', 
            'agent_roles',
            'agent_memories',
            'agent_interactions',
            'tasks',
            'workflows',
            'metrics',
            'system_metrics',
            'evolution_log',
            'learning_experiences',
            'customers',
            'revenue_transactions',
            'api_usage',
            'message_bus'
        ]
        
        try:
            # Connect to databases
            sqlite_conn = await aiosqlite.connect(self.sqlite_path)
            postgres_conn = await asyncpg.connect(self.postgres_dsn)
            
            # Migrate each table
            for table_name in migration_order:
                await self._migrate_table(sqlite_conn, postgres_conn, table_name)
            
            # Verify migration
            await self._verify_migration(sqlite_conn, postgres_conn)
            
            # Close connections
            await sqlite_conn.close()
            await postgres_conn.close()
            
            logger.info("Migration completed successfully")
            return self.stats
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
    
    async def _migrate_table(self, sqlite_conn, postgres_conn, table_name: str):
        """Migrate a specific table from SQLite to PostgreSQL"""
        logger.info(f"Migrating table: {table_name}")
        stats = MigrationStats(table_name)
        
        try:
            # Check if table exists in SQLite
            cursor = await sqlite_conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            table_exists = await cursor.fetchone()
            
            if not table_exists:
                logger.warning(f"Table {table_name} does not exist in SQLite, skipping")
                stats.sqlite_count = 0
                stats.migrated_count = 0
                self.stats[table_name] = stats
                return
            
            # Get SQLite data count
            cursor = await sqlite_conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            stats.sqlite_count = (await cursor.fetchone())[0]
            
            if stats.sqlite_count == 0:
                logger.info(f"Table {table_name} is empty, skipping migration")
                stats.migrated_count = 0
                self.stats[table_name] = stats
                return
            
            # Fetch all data from SQLite
            cursor = await sqlite_conn.execute(f"SELECT * FROM {table_name}")
            rows = await cursor.fetchall()
            
            # Get column names
            column_names = [description[0] for description in cursor.description]
            
            # Transform and insert data based on table type
            if table_name == 'agents':
                await self._migrate_agents(postgres_conn, rows, column_names, stats)
            elif table_name == 'agent_memories':
                await self._migrate_agent_memories(postgres_conn, rows, column_names, stats)
            elif table_name == 'agent_interactions':
                await self._migrate_agent_interactions(postgres_conn, rows, column_names, stats)
            elif table_name == 'tasks':
                await self._migrate_tasks(postgres_conn, rows, column_names, stats)
            elif table_name == 'metrics':
                await self._migrate_metrics(postgres_conn, rows, column_names, stats)
            elif table_name == 'customers':
                await self._migrate_customers(postgres_conn, rows, column_names, stats)
            elif table_name == 'revenue_transactions':
                await self._migrate_revenue_transactions(postgres_conn, rows, column_names, stats)
            elif table_name == 'api_usage':
                await self._migrate_api_usage(postgres_conn, rows, column_names, stats)
            else:
                # Generic migration for other tables
                await self._migrate_generic(postgres_conn, table_name, rows, column_names, stats)
            
            logger.info(f"Migrated {stats.migrated_count}/{stats.sqlite_count} rows for {table_name}")
            
        except Exception as e:
            error_msg = f"Error migrating {table_name}: {e}"
            logger.error(error_msg)
            stats.errors.append(error_msg)
        
        self.stats[table_name] = stats
    
    async def _migrate_agents(self, pg_conn, rows, columns, stats: MigrationStats):
        """Migrate agents table with UUID conversion"""
        for row in rows:
            try:
                data = dict(zip(columns, row))
                
                # Convert string ID to UUID, generate new if invalid
                try:
                    agent_uuid = uuid.UUID(data['id']) if data.get('id') else uuid.uuid4()
                except (ValueError, TypeError):
                    agent_uuid = uuid.uuid4()
                
                # Handle parent_id
                parent_uuid = None
                if data.get('parent_id'):
                    try:
                        parent_uuid = uuid.UUID(data['parent_id'])
                    except (ValueError, TypeError):
                        parent_uuid = None
                
                # Parse JSON fields
                config = json.loads(data.get('config', '{}')) if data.get('config') else {}
                
                await pg_conn.execute("""
                    INSERT INTO agents (
                        id, name, department, agent_type, status, configuration, 
                        code, parent_id, generation, fitness_score, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    ON CONFLICT (id) DO NOTHING
                """, 
                    agent_uuid,
                    data.get('name'),
                    data.get('biome'),  # Map biome to department
                    data.get('agent_type', 'general'),
                    data.get('status', 'active'),
                    config,
                    data.get('code'),
                    parent_uuid,
                    data.get('generation', 1),
                    data.get('fitness_score', 0.0),
                    self._parse_timestamp(data.get('created_at')),
                    self._parse_timestamp(data.get('updated_at'))
                )
                
                stats.migrated_count += 1
                
            except Exception as e:
                stats.errors.append(f"Row error: {e}")
    
    async def _migrate_agent_memories(self, pg_conn, rows, columns, stats: MigrationStats):
        """Migrate agent memories with vector embedding generation"""
        for row in rows:
            try:
                data = dict(zip(columns, row))
                
                # Generate UUIDs
                memory_uuid = uuid.uuid4()
                try:
                    agent_uuid = uuid.UUID(data['agent_id'])
                except (ValueError, TypeError):
                    # Skip if agent_id is invalid
                    stats.errors.append(f"Invalid agent_id: {data.get('agent_id')}")
                    continue
                
                # Generate dummy embedding for now (replace with actual embedding later)
                embedding = np.random.random(1536).tolist()
                
                await pg_conn.execute("""
                    INSERT INTO agent_memories (
                        id, agent_id, content, memory_type, importance, embedding,
                        metadata, created_at, accessed_at, access_count
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (id) DO NOTHING
                """,
                    memory_uuid,
                    agent_uuid,
                    data.get('content'),
                    data.get('memory_type', 'short_term'),
                    data.get('importance', 0.5),
                    embedding,
                    {},  # metadata
                    self._parse_timestamp(data.get('created_at')),
                    self._parse_timestamp(data.get('accessed_at')),
                    0  # access_count
                )
                
                stats.migrated_count += 1
                
            except Exception as e:
                stats.errors.append(f"Row error: {e}")
    
    async def _migrate_agent_interactions(self, pg_conn, rows, columns, stats: MigrationStats):
        """Migrate agent interactions"""
        for row in rows:
            try:
                data = dict(zip(columns, row))
                
                # Generate UUID for interaction
                interaction_uuid = uuid.uuid4()
                
                # Convert agent IDs to UUIDs
                try:
                    source_uuid = uuid.UUID(data['source_agent'])
                except (ValueError, TypeError):
                    stats.errors.append(f"Invalid source_agent: {data.get('source_agent')}")
                    continue
                
                target_uuid = None
                if data.get('target_agent'):
                    try:
                        target_uuid = uuid.UUID(data['target_agent'])
                    except (ValueError, TypeError):
                        pass
                
                # Parse JSON data
                interaction_data = json.loads(data.get('data', '{}')) if data.get('data') else {}
                
                await pg_conn.execute("""
                    INSERT INTO agent_interactions (
                        id, source_agent_id, target_agent_id, interaction_type,
                        data, status, started_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (id) DO NOTHING
                """,
                    interaction_uuid,
                    source_uuid,
                    target_uuid,
                    data.get('interaction_type', 'message'),
                    interaction_data,
                    'completed',  # Default status
                    self._parse_timestamp(data.get('created_at'))
                )
                
                stats.migrated_count += 1
                
            except Exception as e:
                stats.errors.append(f"Row error: {e}")
    
    async def _migrate_tasks(self, pg_conn, rows, columns, stats: MigrationStats):
        """Migrate tasks table"""
        for row in rows:
            try:
                data = dict(zip(columns, row))
                
                # Generate UUID for task
                task_uuid = uuid.uuid4()
                
                # Convert agent_id to UUID
                agent_uuid = None
                if data.get('agent_id'):
                    try:
                        agent_uuid = uuid.UUID(data['agent_id'])
                    except (ValueError, TypeError):
                        pass
                
                # Parse JSON data
                task_data = json.loads(data.get('data', '{}')) if data.get('data') else {}
                
                await pg_conn.execute("""
                    INSERT INTO tasks (
                        id, agent_id, task_type, description, data, status,
                        priority, created_at, started_at, completed_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT (id) DO NOTHING
                """,
                    task_uuid,
                    agent_uuid,
                    data.get('task_type', 'general'),
                    data.get('description'),
                    task_data,
                    data.get('status', 'pending'),
                    data.get('priority', 5),
                    self._parse_timestamp(data.get('created_at')),
                    self._parse_timestamp(data.get('started_at')),
                    self._parse_timestamp(data.get('completed_at'))
                )
                
                stats.migrated_count += 1
                
            except Exception as e:
                stats.errors.append(f"Row error: {e}")
    
    async def _migrate_metrics(self, pg_conn, rows, columns, stats: MigrationStats):
        """Migrate metrics table"""
        for row in rows:
            try:
                data = dict(zip(columns, row))
                
                # Generate UUID for metric
                metric_uuid = uuid.uuid4()
                
                # Convert agent_id to UUID
                agent_uuid = None
                if data.get('agent_id'):
                    try:
                        agent_uuid = uuid.UUID(data['agent_id'])
                    except (ValueError, TypeError):
                        pass
                
                # Parse metadata
                metadata = json.loads(data.get('metadata', '{}')) if data.get('metadata') else {}
                
                await pg_conn.execute("""
                    INSERT INTO metrics (
                        id, agent_id, metric_name, metric_value, metadata, recorded_at
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (id) DO NOTHING
                """,
                    metric_uuid,
                    agent_uuid,
                    data.get('metric_name'),
                    data.get('metric_value', 0.0),
                    metadata,
                    self._parse_timestamp(data.get('recorded_at'))
                )
                
                stats.migrated_count += 1
                
            except Exception as e:
                stats.errors.append(f"Row error: {e}")
    
    async def _migrate_customers(self, pg_conn, rows, columns, stats: MigrationStats):
        """Migrate customers table"""
        for row in rows:
            try:
                data = dict(zip(columns, row))
                
                # Generate UUID for customer
                customer_uuid = uuid.uuid4()
                
                # Convert created_by_agent to UUID
                created_by_uuid = None
                if data.get('created_by_agent'):
                    try:
                        created_by_uuid = uuid.UUID(data['created_by_agent'])
                    except (ValueError, TypeError):
                        pass
                
                await pg_conn.execute("""
                    INSERT INTO customers (
                        id, email, stripe_customer_id, subscription_status,
                        monthly_value, created_by_agent_id
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (email) DO NOTHING
                """,
                    customer_uuid,
                    data.get('email'),
                    data.get('stripe_customer_id'),
                    data.get('subscription_status', 'trial'),
                    data.get('monthly_value', 0.0),
                    created_by_uuid
                )
                
                stats.migrated_count += 1
                
            except Exception as e:
                stats.errors.append(f"Row error: {e}")
    
    async def _migrate_revenue_transactions(self, pg_conn, rows, columns, stats: MigrationStats):
        """Migrate revenue transactions"""
        for row in rows:
            try:
                data = dict(zip(columns, row))
                
                # Generate UUID for transaction
                transaction_uuid = uuid.uuid4()
                
                # Convert customer_id and agent_id to UUIDs
                customer_uuid = None
                if data.get('customer_id'):
                    try:
                        customer_uuid = uuid.UUID(data['customer_id'])
                    except (ValueError, TypeError):
                        # Skip if customer_id is invalid
                        continue
                
                agent_uuid = None
                if data.get('agent_id'):
                    try:
                        agent_uuid = uuid.UUID(data['agent_id'])
                    except (ValueError, TypeError):
                        pass
                
                await pg_conn.execute("""
                    INSERT INTO revenue_transactions (
                        id, customer_id, agent_id, transaction_type, amount,
                        currency, product, processed_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (id) DO NOTHING
                """,
                    transaction_uuid,
                    customer_uuid,
                    agent_uuid,
                    'subscription',  # Default type
                    data.get('amount', 0.0),
                    data.get('currency', 'USD'),
                    data.get('product'),
                    self._parse_timestamp(data.get('created_at'))
                )
                
                stats.migrated_count += 1
                
            except Exception as e:
                stats.errors.append(f"Row error: {e}")
    
    async def _migrate_api_usage(self, pg_conn, rows, columns, stats: MigrationStats):
        """Migrate API usage data"""
        for row in rows:
            try:
                data = dict(zip(columns, row))
                
                # Generate UUID for usage record
                usage_uuid = uuid.uuid4()
                
                # Convert customer_id to UUID
                customer_uuid = None
                if data.get('customer_id'):
                    try:
                        customer_uuid = uuid.UUID(data['customer_id'])
                    except (ValueError, TypeError):
                        # Skip if customer_id is invalid
                        continue
                
                await pg_conn.execute("""
                    INSERT INTO api_usage (
                        id, customer_id, endpoint, method, tokens_used,
                        cost_usd, timestamp
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (id) DO NOTHING
                """,
                    usage_uuid,
                    customer_uuid,
                    data.get('endpoint', '/unknown'),
                    'GET',  # Default method
                    data.get('tokens_used', 0),
                    data.get('cost', 0.0),
                    self._parse_timestamp(data.get('timestamp'))
                )
                
                stats.migrated_count += 1
                
            except Exception as e:
                stats.errors.append(f"Row error: {e}")
    
    async def _migrate_generic(self, pg_conn, table_name: str, rows, columns, stats: MigrationStats):
        """Generic migration for simple tables"""
        logger.info(f"Using generic migration for {table_name}")
        # For now, just count the rows but don't migrate
        stats.migrated_count = 0
        stats.errors.append(f"Generic migration not implemented for {table_name}")
    
    def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """Parse timestamp string to datetime object"""
        if not timestamp_str:
            return None
        
        try:
            # Try multiple timestamp formats
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%dT%H:%M:%S.%fZ'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(timestamp_str, fmt)
                except ValueError:
                    continue
            
            # If all formats fail, return current time
            logger.warning(f"Could not parse timestamp: {timestamp_str}")
            return datetime.utcnow()
            
        except Exception as e:
            logger.warning(f"Timestamp parsing error: {e}")
            return datetime.utcnow()
    
    async def _verify_migration(self, sqlite_conn, postgres_conn):
        """Verify migration by comparing row counts"""
        logger.info("Verifying migration...")
        
        verification_tables = ['agents', 'agent_memories', 'agent_interactions', 'tasks', 'metrics']
        
        for table in verification_tables:
            if table in self.stats:
                try:
                    # Get PostgreSQL count
                    pg_count = await postgres_conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                    self.stats[table].postgres_count = pg_count
                    
                    logger.info(f"{table}: SQLite={self.stats[table].sqlite_count}, "
                              f"PostgreSQL={pg_count}, "
                              f"Migrated={self.stats[table].migrated_count}")
                              
                except Exception as e:
                    logger.error(f"Verification error for {table}: {e}")

async def main():
    """Main migration function"""
    # Configuration
    sqlite_path = Path(__file__).parent.parent / "data" / "boarderframe.db"
    postgres_dsn = "postgresql://boarderframe:boarderframe_secure_2025@localhost:5432/boarderframeos"
    
    # Check if SQLite database exists
    if not sqlite_path.exists():
        logger.error(f"SQLite database not found at {sqlite_path}")
        sys.exit(1)
    
    # Run migration
    migrator = DatabaseMigrator(sqlite_path, postgres_dsn)
    
    try:
        stats = await migrator.migrate_all()
        
        # Print summary
        print("\n" + "="*60)
        print("MIGRATION SUMMARY")
        print("="*60)
        
        total_sqlite = 0
        total_migrated = 0
        total_errors = 0
        
        for table_name, stat in stats.items():
            total_sqlite += stat.sqlite_count
            total_migrated += stat.migrated_count
            total_errors += len(stat.errors)
            
            print(f"{table_name:20} | SQLite: {stat.sqlite_count:6} | "
                  f"Migrated: {stat.migrated_count:6} | "
                  f"Errors: {len(stat.errors):3}")
            
            if stat.errors:
                for error in stat.errors[:3]:  # Show first 3 errors
                    print(f"  ↳ {error}")
                if len(stat.errors) > 3:
                    print(f"  ↳ ... and {len(stat.errors) - 3} more errors")
        
        print("-"*60)
        print(f"{'TOTAL':20} | SQLite: {total_sqlite:6} | "
              f"Migrated: {total_migrated:6} | "
              f"Errors: {total_errors:3}")
        
        if total_errors == 0:
            print("\n✅ Migration completed successfully!")
        else:
            print(f"\n⚠️  Migration completed with {total_errors} errors")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
Department Migration Script
Migrates department data from JSON to PostgreSQL, removing phases layer
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import asyncpg

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DepartmentMigrator:
    def __init__(self, db_url: str = "postgresql://boarderframe:boarderframe_secure_2025@localhost:5434/boarderframeos"):
        self.db_url = db_url
        self.conn = None

    async def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = await asyncpg.connect(self.db_url)
            logger.info("Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    async def close(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()
            logger.info("Database connection closed")

    async def load_json_data(self, json_path: str) -> Dict[str, Any]:
        """Load department data from JSON file"""
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            logger.info(f"Loaded JSON data from {json_path}")
            return data
        except Exception as e:
            logger.error(f"Failed to load JSON data: {e}")
            raise

    async def clear_existing_data(self):
        """Clear existing department data (for clean migration)"""
        logger.info("Clearing existing department data...")

        # Delete in correct order due to foreign key constraints
        tables = [
            'department_assignment_history',
            'department_hierarchy',
            'agent_department_assignments',
            'department_status',
            'department_native_agents',
            'department_leaders',
            'departments'
        ]

        for table in tables:
            await self.conn.execute(f"DELETE FROM {table}")
            logger.info(f"Cleared {table}")

        # Reset sequences
        await self.conn.execute("ALTER SEQUENCE departments_id_seq RESTART WITH 1")
        await self.conn.execute("ALTER SEQUENCE department_leaders_id_seq RESTART WITH 1")
        await self.conn.execute("ALTER SEQUENCE department_native_agents_id_seq RESTART WITH 1")

        logger.info("All department data cleared")

    async def migrate_departments(self, data: Dict[str, Any]):
        """Migrate departments from JSON to PostgreSQL"""
        logger.info("Starting department migration...")

        departments_data = data.get('boarderframeos_departments', {})
        department_id_map = {}  # Maps department_key to database UUID

        # Process each phase and its departments
        for phase_key, phase_data in departments_data.items():
            if phase_key == 'metadata':  # Skip metadata
                continue

            phase_name = phase_data.get('phase_name', phase_key)
            phase_priority = phase_data.get('priority', 1)
            departments = phase_data.get('departments', {})

            logger.info(f"Processing phase: {phase_name} (priority {phase_priority})")

            # Process each department in the phase
            for dept_key, dept_data in departments.items():
                dept_name = dept_data.get('department_name', dept_key)
                category = dept_data.get('category', phase_name)
                description = dept_data.get('description', '')
                purpose = dept_data.get('department_purpose', '')

                # Check if department already exists (by name or department_key)
                existing_dept = await self.conn.fetchval(
                    "SELECT id FROM departments WHERE name = $1 OR department_key = $2",
                    dept_name, dept_key
                )

                if existing_dept:
                    # Update existing department
                    await self.conn.execute("""
                        UPDATE departments SET
                            name = $1, category = $2, description = $3,
                            department_name = $4, department_purpose = $5,
                            legacy_phase = $6, legacy_phase_priority = $7,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = $8
                    """, dept_name, category, description, dept_name, purpose,
                        phase_name, phase_priority, existing_dept)
                    dept_id = existing_dept
                    logger.info(f"  Updated department: {dept_name} (ID: {dept_id})")
                else:
                    # Insert new department
                    dept_id = await self.conn.fetchval("""
                        INSERT INTO departments (
                            name, category, description, phase, priority,
                            department_key, department_name, department_purpose,
                            legacy_phase, legacy_phase_priority, is_active
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                        RETURNING id
                    """, dept_name, category, description, phase_priority, phase_priority,
                        dept_key, dept_name, purpose, phase_name, phase_priority, True)
                    logger.info(f"  Created department: {dept_name} (ID: {dept_id})")

                department_id_map[dept_key] = dept_id

                # Clear existing leaders and native agents for this department
                await self.conn.execute("DELETE FROM department_leaders WHERE department_id = $1", dept_id)
                await self.conn.execute("DELETE FROM department_native_agents WHERE department_id = $1", dept_id)

                # Insert department leaders
                leaders = dept_data.get('leaders', [])
                for i, leader in enumerate(leaders):
                    await self.conn.execute("""
                        INSERT INTO department_leaders (
                            department_id, name, title, description, is_primary
                        ) VALUES ($1, $2, $3, $4, $5)
                    """, dept_id, leader.get('name', ''), leader.get('title', ''),
                        leader.get('description', ''), i == 0)  # First leader is primary

                    logger.info(f"    Added leader: {leader.get('name', '')} - {leader.get('title', '')}")

                # Insert native agents
                native_agents = dept_data.get('native_agents', [])
                for agent in native_agents:
                    await self.conn.execute("""
                        INSERT INTO department_native_agents (
                            department_id, agent_type_name, agent_description
                        ) VALUES ($1, $2, $3)
                    """, dept_id, agent.get('name', ''), agent.get('description', ''))

                    logger.info(f"    Added native agent type: {agent.get('name', '')}")

                # Initialize or update department status
                await self.conn.execute("""
                    INSERT INTO department_status (
                        department_id, assigned_agents_count, active_agents_count,
                        productivity_score, health_score, status
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (department_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        updated_at = CURRENT_TIMESTAMP
                """, dept_id, 0, 0, 0.0, 0.0, 'inactive')

        logger.info(f"Migration completed! Created/Updated {len(department_id_map)} departments")
        return department_id_map

    async def create_department_hierarchies(self, department_id_map: Dict[str, int]):
        """Create logical department hierarchies (optional)"""
        logger.info("Creating department hierarchies...")

        # Define logical hierarchies (based on the phase structure and business logic)
        hierarchies = [
            # Executive Leadership oversees Coordination & Orchestration
            ('executive_leadership', 'coordination_orchestration'),

            # Coordination & Orchestration oversees technical departments
            ('coordination_orchestration', 'engineering'),
            ('coordination_orchestration', 'infrastructure'),
            ('coordination_orchestration', 'operations'),
            ('coordination_orchestration', 'security'),
            ('coordination_orchestration', 'data_management'),

            # Sales oversees marketing and production
            ('sales', 'marketing'),
            ('sales', 'production'),

            # Executive leadership oversees major functions
            ('executive_leadership', 'sales'),
            ('executive_leadership', 'finance'),
            ('executive_leadership', 'legal'),

            # Support functions
            ('finance', 'procurement'),
            ('executive_leadership', 'customer_support'),

            # Strategic functions
            ('executive_leadership', 'analytics'),
            ('executive_leadership', 'strategic_planning'),
            ('executive_leadership', 'change_management'),

            # Advanced capabilities
            ('strategic_planning', 'research_development'),
            ('strategic_planning', 'innovation'),
            ('strategic_planning', 'learning_development'),
            ('strategic_planning', 'creative_services'),

            # HR and Data Generation under executive
            ('executive_leadership', 'human_resources'),
            ('data_management', 'data_generation'),
        ]

        for parent_key, child_key in hierarchies:
            if parent_key in department_id_map and child_key in department_id_map:
                try:
                    await self.conn.execute("""
                        INSERT INTO department_hierarchy (parent_department_id, child_department_id, relationship_type)
                        VALUES ($1, $2, 'reports_to')
                        ON CONFLICT (parent_department_id, child_department_id) DO NOTHING
                    """, department_id_map[parent_key], department_id_map[child_key])

                    logger.info(f"  Created hierarchy: {parent_key} -> {child_key}")
                except Exception as e:
                    logger.warning(f"Failed to create hierarchy {parent_key} -> {child_key}: {e}")

        logger.info("Department hierarchies created")

    async def verify_migration(self) -> Dict[str, Any]:
        """Verify the migration was successful"""
        logger.info("Verifying migration...")

        # Count records
        dept_count = await self.conn.fetchval("SELECT COUNT(*) FROM departments")
        leaders_count = await self.conn.fetchval("SELECT COUNT(*) FROM department_leaders")
        agents_count = await self.conn.fetchval("SELECT COUNT(*) FROM department_native_agents")
        status_count = await self.conn.fetchval("SELECT COUNT(*) FROM department_status")
        hierarchy_count = await self.conn.fetchval("SELECT COUNT(*) FROM department_hierarchy")

        # Get department breakdown by category
        categories = await self.conn.fetch("""
            SELECT category, COUNT(*) as count
            FROM departments
            GROUP BY category
            ORDER BY count DESC
        """)

        # Get sample data
        sample_depts = await self.conn.fetch("""
            SELECT department_key, department_name, category
            FROM departments
            ORDER BY priority, department_name
            LIMIT 5
        """)

        verification = {
            'counts': {
                'departments': dept_count,
                'leaders': leaders_count,
                'native_agent_types': agents_count,
                'department_status': status_count,
                'hierarchies': hierarchy_count
            },
            'categories': [dict(row) for row in categories],
            'sample_departments': [dict(row) for row in sample_depts]
        }

        logger.info(f"Migration verification complete:")
        logger.info(f"  Departments: {dept_count}")
        logger.info(f"  Leaders: {leaders_count}")
        logger.info(f"  Native agent types: {agents_count}")
        logger.info(f"  Department status records: {status_count}")
        logger.info(f"  Hierarchies: {hierarchy_count}")

        return verification

    async def run_migration(self, json_path: str, clear_existing: bool = False):
        """Run the complete migration process"""
        try:
            await self.connect()

            # Load JSON data
            data = await self.load_json_data(json_path)

            # Clear existing data if requested
            if clear_existing:
                await self.clear_existing_data()

            # Migrate departments
            department_id_map = await self.migrate_departments(data)

            # Create hierarchies
            await self.create_department_hierarchies(department_id_map)

            # Verify migration
            verification = await self.verify_migration()

            logger.info("✅ Department migration completed successfully!")
            return verification

        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise
        finally:
            await self.close()

async def main():
    """Main migration function"""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate department data from JSON to PostgreSQL")
    parser.add_argument("--json-path",
                       default="/Users/cosburn/BoarderframeOS/departments/boarderframeos-departments.json",
                       help="Path to the JSON department data file")
    parser.add_argument("--db-url",
                       default="postgresql://boarderframe:boarderframe_secure_2025@localhost:5434/boarderframeos",
                       help="PostgreSQL database URL")
    parser.add_argument("--clear", action="store_true",
                       help="Clear existing department data before migration")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be migrated without making changes")

    args = parser.parse_args()

    if args.dry_run:
        logger.info("DRY RUN: Showing what would be migrated...")
        # Load and analyze JSON without making database changes
        try:
            with open(args.json_path, 'r') as f:
                data = json.load(f)

            departments_data = data.get('boarderframeos_departments', {})
            total_depts = 0
            total_leaders = 0
            total_agents = 0

            for phase_key, phase_data in departments_data.items():
                if phase_key == 'metadata':
                    continue

                departments = phase_data.get('departments', {})
                phase_depts = len(departments)
                total_depts += phase_depts

                phase_leaders = sum(len(dept.get('leaders', [])) for dept in departments.values())
                phase_agents = sum(len(dept.get('native_agents', [])) for dept in departments.values())
                total_leaders += phase_leaders
                total_agents += phase_agents

                logger.info(f"Phase: {phase_data.get('phase_name')} - {phase_depts} departments, {phase_leaders} leaders, {phase_agents} agent types")

            logger.info(f"TOTAL: {total_depts} departments, {total_leaders} leaders, {total_agents} native agent types")

        except Exception as e:
            logger.error(f"Failed to analyze JSON: {e}")
        return

    # Run actual migration
    migrator = DepartmentMigrator(args.db_url)
    verification = await migrator.run_migration(args.json_path, args.clear)

    # Print verification results
    print("\n" + "="*50)
    print("MIGRATION VERIFICATION")
    print("="*50)
    print(json.dumps(verification, indent=2))

if __name__ == "__main__":
    asyncio.run(main())

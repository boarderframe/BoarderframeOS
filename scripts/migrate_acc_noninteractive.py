#!/usr/bin/env python3
"""
Non-interactive migration script for Enhanced ACC
Keeps existing tables and only creates missing ones
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg


async def setup_database_schema():
    """Create enhanced ACC database schema (non-interactive)"""
    print("📊 Setting up Enhanced ACC database schema...")
    
    try:
        conn = await asyncpg.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5434")),
            user=os.getenv("POSTGRES_USER", "boarderframe"),
            password=os.getenv("POSTGRES_PASSWORD", "boarderframe_secure_2025"),
            database=os.getenv("POSTGRES_DB", "boarderframeos")
        )
        
        # Check existing tables
        existing_tables = await conn.fetch("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename LIKE 'acc_%'
        """)
        
        if existing_tables:
            print("ℹ️  Found existing ACC tables - keeping them:")
            for table in existing_tables:
                print(f"   - {table['tablename']}")
        
        # Create tables if they don't exist (using IF NOT EXISTS)
        print("🔨 Creating/verifying ACC tables...")
        
        # All CREATE TABLE statements already have IF NOT EXISTS
        tables_sql = [
            """CREATE TABLE IF NOT EXISTS acc_channels (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                channel_type VARCHAR(50) NOT NULL,
                members JSONB DEFAULT '[]'::jsonb,
                created_by VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_archived BOOLEAN DEFAULT false,
                metadata JSONB DEFAULT '{}'::jsonb
            )""",
            
            """CREATE TABLE IF NOT EXISTS acc_messages (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                channel_id UUID REFERENCES acc_channels(id) ON DELETE CASCADE,
                from_agent VARCHAR(100) NOT NULL,
                to_agent VARCHAR(100),
                message_type VARCHAR(50) DEFAULT 'chat',
                content TEXT NOT NULL,
                format VARCHAR(50) DEFAULT 'text',
                thread_id UUID,
                mentions JSONB DEFAULT '[]'::jsonb,
                attachments JSONB DEFAULT '[]'::jsonb,
                reactions JSONB DEFAULT '{}'::jsonb,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_edited BOOLEAN DEFAULT false,
                is_deleted BOOLEAN DEFAULT false,
                metadata JSONB DEFAULT '{}'::jsonb
            )""",
            
            """CREATE TABLE IF NOT EXISTS acc_presence (
                agent_name VARCHAR(100) PRIMARY KEY,
                status VARCHAR(50) NOT NULL,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                current_channel UUID REFERENCES acc_channels(id),
                metadata JSONB DEFAULT '{}'::jsonb
            )""",
            
            """CREATE TABLE IF NOT EXISTS acc_threads (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                channel_id UUID REFERENCES acc_channels(id) ON DELETE CASCADE,
                started_by VARCHAR(100) NOT NULL,
                title VARCHAR(200),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB DEFAULT '{}'::jsonb
            )""",
            
            """CREATE TABLE IF NOT EXISTS acc_channel_members (
                channel_id UUID REFERENCES acc_channels(id) ON DELETE CASCADE,
                agent_name VARCHAR(100) NOT NULL,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                role VARCHAR(50) DEFAULT 'member',
                PRIMARY KEY (channel_id, agent_name)
            )"""
        ]
        
        for sql in tables_sql:
            await conn.execute(sql)
        
        # Create indexes
        print("📍 Creating indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_messages_channel ON acc_messages(channel_id, timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_messages_thread ON acc_messages(thread_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_presence_status ON acc_presence(status)"
        ]
        
        for idx in indexes:
            await conn.execute(idx)
        
        print("✅ Database schema ready")
        
        # Create default channels if they don't exist
        print("\n📢 Creating default channels...")
        default_channels = [
            ("general", "General discussion for all agents", "topic"),
            ("announcements", "System-wide announcements", "broadcast"),
            ("executive", "Executive team discussions", "department"),
            ("engineering", "Engineering department", "department"),
            ("operations", "Operations and logistics", "department"),
            ("random", "Off-topic discussions", "topic")
        ]
        
        for name, desc, ch_type in default_channels:
            try:
                await conn.execute("""
                    INSERT INTO acc_channels (name, description, channel_type, created_by)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (name) DO NOTHING
                """, name, desc, ch_type, "system")
                print(f"   ✅ Channel ready: #{name}")
            except Exception as e:
                print(f"   ⚠️  Error with channel {name}: {e}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database setup error: {e}")
        return False


async def create_launch_script():
    """Create launch script for enhanced ACC"""
    print("\n🚀 Creating launch script...")
    
    script_content = """#!/bin/bash
# Launch Enhanced Agent Communication Center

echo "🚀 Starting Enhanced Agent Communication Center..."

# Check if PostgreSQL is running
if ! nc -z localhost 5434 2>/dev/null; then
    echo "❌ PostgreSQL is not running on port 5434"
    echo "   Please start PostgreSQL first: docker-compose up -d postgresql"
    exit 1
fi

echo "✅ PostgreSQL is running"
echo "🌟 Launching Enhanced ACC on port 8890..."
python agent_communication_center_enhanced.py
"""
    
    script_path = Path("launch_enhanced_acc.sh")
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    os.chmod(script_path, 0o755)
    print(f"✅ Created launch script: {script_path}")


async def main():
    """Main migration process"""
    print("🎯 Enhanced Agent Communication Center Migration (Non-interactive)")
    print("=" * 65)
    
    # Setup database
    if not await setup_database_schema():
        print("\n❌ Migration failed")
        return
    
    # Create launch script
    await create_launch_script()
    
    print("\n✨ Migration completed successfully!")
    print("\n📝 Next Steps:")
    print("   1. Update startup.py to use enhanced ACC:")
    print("      python scripts/update_startup_for_enhanced_acc.py")
    print("   2. Test the enhanced ACC:")
    print("      python test_acc_enhanced.py")
    print("   3. Launch enhanced ACC:")
    print("      ./launch_enhanced_acc.sh")
    print("\n🔗 Access at: http://localhost:8890")


if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
Migration script for transitioning to Enhanced Agent Communication Center
Handles database setup, configuration migration, and startup transition
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncpg


async def check_current_acc_status():
    """Check if current ACC is running"""
    print("🔍 Checking current ACC status...")
    
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8890/health")
            if response.status_code == 200:
                print("⚠️  Current ACC is running on port 8890")
                print("   Please stop it before running the enhanced version")
                return False
    except:
        print("✅ Current ACC is not running")
    
    return True


async def setup_database_schema():
    """Create enhanced ACC database schema"""
    print("\n📊 Setting up Enhanced ACC database schema...")
    
    try:
        # Connect to PostgreSQL
        conn = await asyncpg.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5434")),
            user=os.getenv("POSTGRES_USER", "boarderframe"),
            password=os.getenv("POSTGRES_PASSWORD", "boarderframe_secure_2025"),
            database=os.getenv("POSTGRES_DB", "boarderframeos")
        )
        
        # Check if tables already exist
        existing_tables = await conn.fetch("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename LIKE 'acc_%'
        """)
        
        if existing_tables:
            print("⚠️  ACC tables already exist:")
            for table in existing_tables:
                print(f"   - {table['tablename']}")
            
            response = input("\nDo you want to drop and recreate them? (y/N): ")
            if response.lower() == 'y':
                print("🗑️  Dropping existing ACC tables...")
                await conn.execute("DROP TABLE IF EXISTS acc_messages CASCADE")
                await conn.execute("DROP TABLE IF EXISTS acc_channels CASCADE")
                await conn.execute("DROP TABLE IF EXISTS acc_presence CASCADE")
                await conn.execute("DROP TABLE IF EXISTS acc_threads CASCADE")
                await conn.execute("DROP TABLE IF EXISTS acc_channel_members CASCADE")
            else:
                print("ℹ️  Keeping existing tables")
                await conn.close()
                return True
        
        # Create tables
        print("🔨 Creating ACC tables...")
        
        # Channels table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS acc_channels (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                channel_type VARCHAR(50) NOT NULL,
                created_by VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB DEFAULT '{}'::jsonb
            )
        """)
        
        # Messages table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS acc_messages (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                channel_id UUID REFERENCES acc_channels(id) ON DELETE CASCADE,
                from_agent VARCHAR(100) NOT NULL,
                to_agent VARCHAR(100),
                content TEXT NOT NULL,
                format VARCHAR(50) DEFAULT 'text',
                thread_id UUID,
                mentions TEXT[],
                attachments JSONB DEFAULT '[]'::jsonb,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                edited_at TIMESTAMP,
                metadata JSONB DEFAULT '{}'::jsonb
            )
        """)
        
        # Agent presence table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS acc_presence (
                agent_name VARCHAR(100) PRIMARY KEY,
                status VARCHAR(50) NOT NULL,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                current_channel UUID REFERENCES acc_channels(id),
                metadata JSONB DEFAULT '{}'::jsonb
            )
        """)
        
        # Threads table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS acc_threads (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                channel_id UUID REFERENCES acc_channels(id) ON DELETE CASCADE,
                started_by VARCHAR(100) NOT NULL,
                title VARCHAR(200),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB DEFAULT '{}'::jsonb
            )
        """)
        
        # Channel members table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS acc_channel_members (
                channel_id UUID REFERENCES acc_channels(id) ON DELETE CASCADE,
                agent_name VARCHAR(100) NOT NULL,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                role VARCHAR(50) DEFAULT 'member',
                PRIMARY KEY (channel_id, agent_name)
            )
        """)
        
        # Create indexes for performance
        print("📍 Creating indexes...")
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_channel 
            ON acc_messages(channel_id, timestamp DESC)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_thread 
            ON acc_messages(thread_id, timestamp)
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_presence_status 
            ON acc_presence(status)
        """)
        
        print("✅ Database schema created successfully")
        
        # Create default channels
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
                print(f"   ✅ Created channel: #{name}")
            except Exception as e:
                print(f"   ⚠️  Error creating channel {name}: {e}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database setup error: {e}")
        return False


async def migrate_existing_data():
    """Migrate any existing chat data from the old ACC"""
    print("\n📦 Checking for existing ACC data to migrate...")
    
    # Check if there's a SQLite database or logs to migrate
    old_data_path = Path("data/acc_chat_history.json")
    if old_data_path.exists():
        print("📄 Found old chat history file")
        try:
            with open(old_data_path, 'r') as f:
                old_data = json.load(f)
            
            print(f"   Found {len(old_data.get('messages', []))} messages to migrate")
            # TODO: Implement actual migration logic if needed
            print("   ℹ️  Migration of old data not implemented yet")
        except Exception as e:
            print(f"   ⚠️  Error reading old data: {e}")
    else:
        print("✅ No old data found to migrate")


async def update_startup_configuration():
    """Update startup.py to use enhanced ACC"""
    print("\n⚙️  Updating startup configuration...")
    
    startup_path = Path("startup.py")
    if startup_path.exists():
        print("📝 Checking startup.py for ACC references...")
        
        try:
            with open(startup_path, 'r') as f:
                content = f.read()
            
            if "agent_communication_center.py" in content:
                print("   Found reference to old ACC")
                print("   ℹ️  To use enhanced ACC, update startup.py to launch:")
                print("      agent_communication_center_enhanced.py")
            else:
                print("✅ Startup configuration looks good")
                
        except Exception as e:
            print(f"   ⚠️  Error checking startup.py: {e}")
    else:
        print("⚠️  startup.py not found")


async def create_launch_script():
    """Create a convenient launch script for enhanced ACC"""
    print("\n🚀 Creating launch script...")
    
    script_content = """#!/bin/bash
# Launch Enhanced Agent Communication Center

echo "🚀 Starting Enhanced Agent Communication Center..."

# Set environment variables if needed
export POSTGRES_HOST=${POSTGRES_HOST:-localhost}
export POSTGRES_PORT=${POSTGRES_PORT:-5434}
export POSTGRES_USER=${POSTGRES_USER:-boarderframe}
export POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-boarderframe}
export POSTGRES_DB=${POSTGRES_DB:-boarderframeos}

# Check if PostgreSQL is running
echo "🔍 Checking PostgreSQL connection..."
if ! nc -z localhost 5434; then
    echo "❌ PostgreSQL is not running on port 5434"
    echo "   Please start PostgreSQL first: docker-compose up -d postgresql"
    exit 1
fi

echo "✅ PostgreSQL is running"

# Launch enhanced ACC
echo "🌟 Launching Enhanced ACC on port 8890..."
python agent_communication_center_enhanced.py
"""
    
    script_path = Path("launch_enhanced_acc.sh")
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    # Make executable
    os.chmod(script_path, 0o755)
    print(f"✅ Created launch script: {script_path}")


async def print_migration_summary():
    """Print migration summary and next steps"""
    print("\n" + "=" * 50)
    print("📋 Enhanced ACC Migration Summary")
    print("=" * 50)
    
    print("\n✅ Completed:")
    print("   - Database schema created")
    print("   - Default channels created")
    print("   - Launch script created")
    
    print("\n📝 Next Steps:")
    print("   1. Stop the current ACC if running:")
    print("      pkill -f 'agent_communication_center.py'")
    print("   2. Update startup.py to use enhanced ACC:")
    print("      Replace 'agent_communication_center.py' with 'agent_communication_center_enhanced.py'")
    print("   3. Launch enhanced ACC:")
    print("      ./launch_enhanced_acc.sh")
    print("   4. Test the enhanced features:")
    print("      python test_acc_enhanced.py")
    
    print("\n🌟 Enhanced ACC Features:")
    print("   - Persistent message storage in PostgreSQL")
    print("   - Channel-based communication (like Slack)")
    print("   - Real-time WebSocket updates")
    print("   - Message bus integration for agent-to-agent messaging")
    print("   - Thread support for conversations")
    print("   - Agent presence tracking")
    print("   - File attachments and mentions")
    
    print("\n🔗 Access the enhanced ACC at: http://localhost:8890")


async def main():
    """Main migration process"""
    print("🎯 Enhanced Agent Communication Center Migration")
    print("=" * 50)
    
    # Check current ACC status
    if not await check_current_acc_status():
        return
    
    # Setup database
    if not await setup_database_schema():
        print("\n❌ Migration failed at database setup")
        return
    
    # Migrate existing data
    await migrate_existing_data()
    
    # Update configuration
    await update_startup_configuration()
    
    # Create launch script
    await create_launch_script()
    
    # Print summary
    await print_migration_summary()


if __name__ == "__main__":
    asyncio.run(main())
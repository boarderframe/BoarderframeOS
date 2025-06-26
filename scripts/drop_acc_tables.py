#!/usr/bin/env python3
"""
Drop existing ACC tables to prepare for enhanced ACC
"""

import asyncio
import asyncpg
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


async def drop_acc_tables():
    """Drop all ACC tables"""
    print("🗑️  Dropping existing ACC tables...")
    
    try:
        conn = await asyncpg.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5434")),
            user=os.getenv("POSTGRES_USER", "boarderframe"),
            password=os.getenv("POSTGRES_PASSWORD", "boarderframe_secure_2025"),
            database=os.getenv("POSTGRES_DB", "boarderframeos")
        )
        
        # Get all ACC tables
        tables = await conn.fetch("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename LIKE 'acc_%'
        """)
        
        if not tables:
            print("✅ No ACC tables found to drop")
            await conn.close()
            return
        
        print(f"Found {len(tables)} ACC tables:")
        for table in tables:
            print(f"   - {table['tablename']}")
        
        # Drop each table
        for table in tables:
            table_name = table['tablename']
            try:
                await conn.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
                print(f"   ✅ Dropped {table_name}")
            except Exception as e:
                print(f"   ❌ Error dropping {table_name}: {e}")
        
        await conn.close()
        print("\n✅ All ACC tables dropped successfully")
        print("\n📝 Next step: Run the migration script")
        print("   python scripts/migrate_acc_noninteractive.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("⚠️  WARNING: This will drop all ACC tables and data!")
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() == "yes":
        asyncio.run(drop_acc_tables())
    else:
        print("❌ Operation cancelled")
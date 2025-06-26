#!/usr/bin/env python3
"""
Refresh the database tables view in Corporate HQ to show all PostgreSQL tables
"""

import asyncio
import json
from datetime import datetime

import aiohttp


async def refresh_database_metrics():
    """Trigger a refresh of database metrics in Corporate HQ"""
    try:
        print("🔄 Refreshing database metrics in Corporate HQ...")

        # Call the database refresh endpoint
        async with aiohttp.ClientSession() as session:
            # First, check if Corporate HQ is running
            try:
                async with session.get("http://localhost:8888/") as resp:
                    if resp.status != 200:
                        print("❌ Corporate HQ is not running. Please start it first.")
                        return False
            except:
                print("❌ Cannot connect to Corporate HQ at http://localhost:8888")
                print("   Please run: python corporate_headquarters.py")
                return False

            # Trigger database refresh
            async with session.post(
                "http://localhost:8888/api/database/refresh"
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print("✅ Database metrics refreshed successfully!")
                    print(f"   Total tables: {data.get('total_tables', 'Unknown')}")
                    print(f"   Database size: {data.get('database_size', 'Unknown')}")
                    print(
                        f"   Active connections: {data.get('active_connections', 'Unknown')}"
                    )

                    # Show table categories
                    tables = data.get("tables", [])
                    if tables:
                        print("\n📊 Table Categories:")
                        categories = {}
                        for table in tables:
                            # Categorize based on name
                            name = table.get("name", "").lower()
                            if (
                                "llm_cost" in name
                                or "llm_budget" in name
                                or "llm_model_performance" in name
                            ):
                                category = "LLM Cost Tracking"
                            elif any(
                                k in name
                                for k in ["agent", "solomon", "david", "adam", "eve"]
                            ):
                                category = "Agents"
                            elif any(
                                k in name
                                for k in ["department", "finance", "legal", "sales"]
                            ):
                                category = "Departments"
                            elif any(
                                k in name
                                for k in ["division", "leadership", "executive"]
                            ):
                                category = "Divisions"
                            elif any(
                                k in name
                                for k in ["registry", "server", "service", "mcp"]
                            ):
                                category = "Registry"
                            elif any(
                                k in name
                                for k in ["message", "chat", "communication", "log"]
                            ):
                                category = "Messaging"
                            elif any(
                                k in name for k in ["migration", "schema", "version"]
                            ):
                                category = "Migrations"
                            elif any(
                                k in name
                                for k in ["pg_", "information_schema", "sql_", "sys_"]
                            ):
                                category = "System"
                            else:
                                category = "Other"

                            if category not in categories:
                                categories[category] = []
                            categories[category].append(table.get("name"))

                        # Display categorized tables
                        category_order = [
                            "Agents",
                            "Divisions",
                            "Departments",
                            "LLM Cost Tracking",
                            "Registry",
                            "Messaging",
                            "Migrations",
                            "System",
                            "Other",
                        ]

                        for cat in category_order:
                            if cat in categories:
                                print(f"\n   {cat}: {len(categories[cat])} tables")
                                for table in sorted(categories[cat])[
                                    :5
                                ]:  # Show first 5
                                    print(f"     - {table}")
                                if len(categories[cat]) > 5:
                                    print(
                                        f"     ... and {len(categories[cat]) - 5} more"
                                    )

                    return True
                else:
                    print(f"❌ Failed to refresh database metrics: {resp.status}")
                    return False

    except Exception as e:
        print(f"❌ Error refreshing database metrics: {e}")
        return False


async def check_llm_tables():
    """Check if LLM cost tracking tables exist in the database"""
    try:
        import asyncpg

        print("\n🔍 Checking for LLM cost tracking tables directly in PostgreSQL...")

        # Connect to database
        conn = await asyncpg.connect(
            "postgresql://boarderframe:boarderframe_secure_2025@localhost:5434/boarderframeos"
        )

        # Query for LLM tables
        query = """
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
              AND tablename LIKE 'llm_%'
            ORDER BY tablename
        """

        results = await conn.fetch(query)

        if results:
            print(f"\n✅ Found {len(results)} LLM cost tracking tables:")
            for row in results:
                print(f"   - {row['tablename']}")
        else:
            print("\n⚠️  No LLM cost tracking tables found.")
            print("   The migration may not have been run yet.")

        # Get total table count
        total_query = """
            SELECT COUNT(*) as count
            FROM pg_tables
            WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
        """
        total_result = await conn.fetchrow(total_query)
        print(f"\n📊 Total tables in database: {total_result['count']}")

        await conn.close()

    except Exception as e:
        print(f"❌ Error checking database: {e}")


async def main():
    """Main function"""
    print("🗄️  BoarderframeOS Database Table Refresh")
    print("=" * 50)

    # Check database directly
    await check_llm_tables()

    # Refresh Corporate HQ
    print("\n" + "=" * 50)
    success = await refresh_database_metrics()

    if success:
        print("\n✅ Database refresh complete!")
        print("   Visit http://localhost:8888 and click on the Database tab")
        print("   to see all tables including LLM Cost Tracking category.")
    else:
        print("\n❌ Database refresh failed.")
        print("   Please ensure Corporate HQ is running.")


if __name__ == "__main__":
    asyncio.run(main())

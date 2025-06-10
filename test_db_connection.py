#!/usr/bin/env python3
import asyncpg
import asyncio

async def test_connection():
    try:
        # Test with new port 5434
        conn = await asyncpg.connect('postgresql://boarderframe:boarderframe_secure_2025@localhost:5434/boarderframeos')
        result = await conn.fetchval('SELECT current_user')
        print(f"Connection successful! Current user: {result}")
        await conn.close()
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())
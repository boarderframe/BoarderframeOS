#!/usr/bin/env python3
"""
MCP Database Server - stdio transport wrapper
Wraps the HTTP-based database server for use with Claude CLI
"""

import asyncio

# Handle MCP import conflicts by temporarily modifying sys.path
import importlib
import importlib.util
import json
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiosqlite

# Save original sys.path
original_path = sys.path.copy()

# Remove current and parent directories to avoid local mcp module conflicts
current_dir = str(Path(__file__).parent)
parent_dir = str(Path(__file__).parent.parent)
sys.path = [p for p in sys.path if p not in (current_dir, parent_dir, "")]

# Clear any cached local mcp modules
local_mcp_modules = [name for name in sys.modules.keys() if name.startswith("mcp")]
for module_name in local_mcp_modules:
    del sys.modules[module_name]

try:
    # Import the real MCP package
    import mcp.server.stdio
    from mcp import types
    from mcp.server import NotificationOptions, Server
    from mcp.server.models import InitializationOptions
finally:
    # Restore original sys.path
    sys.path = original_path

# Configure logging to file to avoid interfering with stdio
log_file = Path(__file__).parent / "database_stdio.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file)],
)
logger = logging.getLogger("database_stdio")

# Database path
BASE_PATH = Path(__file__).parent.parent
DB_PATH = BASE_PATH / "data" / "boarderframe.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

server = Server("database")


@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available database tools."""
    return [
        types.Tool(
            name="execute_query",
            description="Execute raw SQL query",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "SQL query to execute"},
                    "params": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Query parameters (optional)",
                    },
                    "fetch_all": {
                        "type": "boolean",
                        "description": "Fetch all results or just one",
                        "default": True,
                    },
                },
                "required": ["sql"],
            },
        ),
        types.Tool(
            name="insert_data",
            description="Insert data into a table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table": {"type": "string", "description": "Table name"},
                    "data": {
                        "type": "object",
                        "description": "Data to insert as key-value pairs",
                    },
                    "on_conflict": {
                        "type": "string",
                        "description": "Conflict resolution: IGNORE, REPLACE",
                        "default": "IGNORE",
                    },
                },
                "required": ["table", "data"],
            },
        ),
        types.Tool(
            name="update_data",
            description="Update data in a table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table": {"type": "string", "description": "Table name"},
                    "data": {
                        "type": "object",
                        "description": "Data to update as key-value pairs",
                    },
                    "where": {
                        "type": "object",
                        "description": "WHERE conditions as key-value pairs",
                    },
                },
                "required": ["table", "data", "where"],
            },
        ),
        types.Tool(
            name="delete_data",
            description="Delete data from a table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table": {"type": "string", "description": "Table name"},
                    "where": {
                        "type": "object",
                        "description": "WHERE conditions as key-value pairs",
                    },
                },
                "required": ["table", "where"],
            },
        ),
        types.Tool(
            name="list_tables",
            description="List all tables in the database",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="get_table_schema",
            description="Get schema for a specific table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table": {"type": "string", "description": "Table name"}
                },
                "required": ["table"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: Dict[str, Any]
) -> List[types.TextContent]:
    """Handle tool calls."""
    try:
        if name == "execute_query":
            return await execute_query(arguments)
        elif name == "insert_data":
            return await insert_data(arguments)
        elif name == "update_data":
            return await update_data(arguments)
        elif name == "delete_data":
            return await delete_data(arguments)
        elif name == "list_tables":
            return await list_tables()
        elif name == "get_table_schema":
            return await get_table_schema(arguments["table"])
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def execute_query(args: Dict[str, Any]) -> List[types.TextContent]:
    """Execute raw SQL query."""
    try:
        sql = args["sql"]
        params = args.get("params", [])
        fetch_all = args.get("fetch_all", True)

        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(sql, params)

            if sql.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
                rows_affected = cursor.rowcount
                await db.commit()
                result = {
                    "success": True,
                    "rows_affected": rows_affected,
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                if fetch_all:
                    rows = await cursor.fetchall()
                    data = [dict(row) for row in rows]
                else:
                    row = await cursor.fetchone()
                    data = dict(row) if row else None

                result = {
                    "success": True,
                    "data": data,
                    "count": (
                        len(data) if isinstance(data, list) else (1 if data else 0)
                    ),
                    "timestamp": datetime.now().isoformat(),
                }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error executing query: {str(e)}")]


async def insert_data(args: Dict[str, Any]) -> List[types.TextContent]:
    """Insert data into table."""
    try:
        table = args["table"]
        data = args["data"]
        on_conflict = args.get("on_conflict", "IGNORE")

        columns = list(data.keys())
        placeholders = ["?" for _ in columns]
        values = [data[col] for col in columns]

        sql = f"""
            INSERT OR {on_conflict} INTO {table}
            ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """

        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(sql, values)
            await db.commit()

            result = {
                "success": True,
                "table": table,
                "rows_affected": cursor.rowcount,
                "timestamp": datetime.now().isoformat(),
            }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error inserting data: {str(e)}")]


async def update_data(args: Dict[str, Any]) -> List[types.TextContent]:
    """Update data in table."""
    try:
        table = args["table"]
        data = args["data"]
        where = args["where"]

        set_clauses = [f"{col} = ?" for col in data.keys()]
        where_clauses = [f"{col} = ?" for col in where.keys()]

        set_values = list(data.values())
        where_values = list(where.values())

        sql = f"""
            UPDATE {table}
            SET {', '.join(set_clauses)}
            WHERE {' AND '.join(where_clauses)}
        """

        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(sql, set_values + where_values)
            await db.commit()

            result = {
                "success": True,
                "table": table,
                "rows_affected": cursor.rowcount,
                "timestamp": datetime.now().isoformat(),
            }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error updating data: {str(e)}")]


async def delete_data(args: Dict[str, Any]) -> List[types.TextContent]:
    """Delete data from table."""
    try:
        table = args["table"]
        where = args["where"]

        where_clauses = [f"{col} = ?" for col in where.keys()]
        where_values = list(where.values())

        sql = f"""
            DELETE FROM {table}
            WHERE {' AND '.join(where_clauses)}
        """

        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(sql, where_values)
            await db.commit()

            result = {
                "success": True,
                "table": table,
                "rows_affected": cursor.rowcount,
                "timestamp": datetime.now().isoformat(),
            }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error deleting data: {str(e)}")]


async def list_tables() -> List[types.TextContent]:
    """List all tables in database."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            rows = await cursor.fetchall()
            tables = [row[0] for row in rows]

            result = {
                "success": True,
                "tables": tables,
                "count": len(tables),
                "timestamp": datetime.now().isoformat(),
            }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error listing tables: {str(e)}")]


async def get_table_schema(table: str) -> List[types.TextContent]:
    """Get schema for specific table."""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(f"PRAGMA table_info({table})")
            rows = await cursor.fetchall()

            schema = []
            for row in rows:
                schema.append(
                    {
                        "column": row[1],
                        "type": row[2],
                        "not_null": bool(row[3]),
                        "default_value": row[4],
                        "primary_key": bool(row[5]),
                    }
                )

            result = {
                "success": True,
                "table": table,
                "schema": schema,
                "timestamp": datetime.now().isoformat(),
            }

        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        return [
            types.TextContent(type="text", text=f"Error getting table schema: {str(e)}")
        ]


async def main():
    """Main entry point."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="database",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())

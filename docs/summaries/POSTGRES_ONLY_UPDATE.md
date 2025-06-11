# PostgreSQL-Only Database Configuration Update

## Summary
Modified BoarderframeOS startup configuration to use only PostgreSQL database server (port 8010) instead of SQLite database server (port 8004).

## Changes Made

### 1. startup.py
- **Line 774**: Changed database server configuration in `start_mcp_servers()` method
  - From: `{"name": "database", "port": 8004, "script": "database_server.py", "category": "Core"}`
  - To: `{"name": "database_postgres", "port": 8010, "script": "database_server_postgres.py", "category": "Core"}`

### 2. corporate_headquarters.py
Updated all references from SQLite database server (port 8004) to PostgreSQL database server (port 8010):
- Line 134: Changed MCP server refresh call
- Line 1060: Updated dashboard configuration
- Line 1477: Updated server status configuration
- Line 1534: Updated server list
- Line 4026: Updated startup check description
- Line 8175: Updated server registry configuration
- Line 8463: Updated detailed server configuration

### 3. core/hq_metrics_layer.py
- Line 391: Updated mock server data fallback from port 8004 to port 8010

### 4. system_status.py
- Line 18: Updated server list from "Database" on port 8004 to "PostgreSQL Database" on port 8010

## Benefits
1. **Single Database System**: Eliminates confusion between SQLite and PostgreSQL
2. **Better Performance**: PostgreSQL offers superior performance for BoarderframeOS's needs
3. **Advanced Features**: Access to pgvector for AI embeddings and JSONB for flexible data storage
4. **Enterprise-Ready**: PostgreSQL is production-grade with better concurrency and reliability

## Next Steps
To apply these changes:
1. Stop the current BoarderframeOS system if running
2. Restart using `python startup.py`
3. The system will now use only PostgreSQL database server on port 8010

## Verification
After restarting, verify the change by:
1. Checking the startup logs for "database_postgres" on port 8010
2. Visiting Corporate Headquarters at http://localhost:8888 and checking the server status
3. Confirming no SQLite database server is running on port 8004

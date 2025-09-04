# Server Configuration Modal Usage Guide

## Overview
The Server Configuration Modal provides a comprehensive interface for configuring MCP servers with different types, protocols, and security settings.

## Features

### 1. General Settings Tab
- **Server Name**: Required field for identifying the server
- **Description**: Optional description of server purpose
- **Server Type**: Choose from filesystem, database, HTTP, Python, Node.js, or custom
- **Protocol**: Select communication protocol (stdio, HTTP, WebSocket, gRPC)
- **Enabled**: Toggle to enable/disable the server
- **Auto-start**: Option to start server automatically on launch

### 2. Command Tab
- **Command**: The executable command to run the server
- **Arguments**: Command-line arguments passed to the server
- **Working Directory**: Directory where the server process runs

### 3. Environment Variables Tab
- Add/remove environment variables with key-value pairs
- Support for encrypted values (passwords, API keys)
- Visual toggle to show/hide encrypted values

### 4. File System Tab (for filesystem type)
- **Allowed Directories**: List of directories the server can access
- **Permissions**: Read, write, and delete permissions
- **Max File Size**: Limit for file operations
- **Blocked Paths**: Directories to explicitly block access

### 5. Database Tab (for database type)
- **Connection String**: Database connection URL
- **Database Name**: Target database
- **Schema**: Optional schema selection
- **Max Connections**: Connection pool size
- **Timeout**: Query timeout settings
- **Read-only Mode**: Restrict to read operations only

### 6. Security Tab
- **Token Budget**: Maximum tokens per session
- **Rate Limiting**: Requests per minute and concurrent limits
- **Blocked Commands**: List of restricted commands
- **Authentication**: Require auth for access

### 7. Advanced Tab
- **Port**: Network port for HTTP/WebSocket protocols
- **Host**: Bind address for the server
- **Timeout**: General operation timeout
- **Max Retries**: Auto-retry on failure
- **Log Level**: Debug, info, warn, or error
- **Restart on Failure**: Automatic restart behavior

## Usage

### Adding a New Server
1. Click the "Add Server" button in the main interface
2. Fill in required fields (name, type, protocol, command)
3. Configure type-specific settings in relevant tabs
4. Set security restrictions as needed
5. Click "Save Configuration"

### Editing an Existing Server
1. Click the gear icon on any server card
2. Modal opens with current configuration loaded
3. Make desired changes across tabs
4. Unsaved changes indicator appears
5. Click "Save Configuration" to apply changes

### Validation
- Required fields are marked with red asterisks
- Validation errors appear below fields
- Tab headers show error count if validation fails
- Save button is disabled when errors exist

### Reset and Cancel
- **Reset**: Reverts all changes to original values
- **Cancel**: Closes modal (prompts if unsaved changes)

## Configuration Examples

### File System Server
```javascript
{
  name: "File System Server",
  type: "filesystem",
  protocol: "stdio",
  command: "mcp-server-filesystem",
  fileSystemConfig: {
    allowedDirectories: ["/Users/workspace"],
    readPermissions: true,
    writePermissions: false
  }
}
```

### Database Server
```javascript
{
  name: "PostgreSQL Server",
  type: "database",
  protocol: "stdio",
  command: "mcp-server-postgres",
  databaseConfig: {
    connectionString: "postgresql://user:pass@localhost:5432/db",
    database: "mydb",
    readOnly: false
  }
}
```

## Integration with Backend

The modal integrates with the FastAPI backend through:
- `POST /api/v1/servers/` - Create new server
- `PUT /api/v1/servers/{id}` - Update existing server

Configuration is validated both client-side and server-side for security.

## Keyboard Shortcuts
- `Escape` - Close modal (if no unsaved changes)
- `Tab` - Navigate between fields
- `Enter` - Submit form (when valid)

## Testing
Run the test suite:
```bash
npm run test -- ServerConfigModal
```

## Future Enhancements
- Import/export configuration files
- Configuration templates
- Bulk configuration updates
- Configuration history/versioning
- Live validation against running servers
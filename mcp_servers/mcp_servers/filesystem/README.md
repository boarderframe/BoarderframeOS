# File System MCP Server

A Model Context Protocol (MCP) server that provides file system operations for AI assistants.

## Features

- **Read Files**: Read the contents of text files
- **Write Files**: Create or modify files with new content
- **List Directories**: Browse directory contents with file information
- **Search Files**: Find files using glob patterns (recursive or non-recursive)
- **File Information**: Get detailed metadata about files and directories
- **Create Directories**: Create new directories with proper path handling

## Tools Available

### `read_file`
Read the contents of a file.
- **Parameter**: `path` (string) - The path to the file to read

### `write_file`
Write content to a file (creates parent directories if needed).
- **Parameters**: 
  - `path` (string) - The path to the file to write
  - `content` (string) - The content to write to the file

### `list_directory`
List the contents of a directory.
- **Parameter**: `path` (string) - The path to the directory to list

### `search_files`
Search for files matching a pattern.
- **Parameters**:
  - `directory` (string) - The directory to search in
  - `pattern` (string) - The search pattern (supports glob patterns like `*.py`, `test_*`, etc.)
  - `recursive` (boolean, optional) - Whether to search recursively (default: true)

### `get_file_info`
Get information about a file or directory.
- **Parameter**: `path` (string) - The path to get information about

### `create_directory`
Create a new directory.
- **Parameter**: `path` (string) - The path of the directory to create

## Installation & Usage

1. **Prerequisites**: Python 3.10+ and the MCP Python SDK
2. **Virtual Environment**: Ensure you're in the project's virtual environment
3. **Start the Server**: Run `./start.sh` or `python main.py`

## Configuration

The server can be configured to work with various MCP clients:

### Claude Desktop
Add to your MCP configuration:
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "python",
      "args": ["/path/to/mcp_servers/filesystem/main.py"]
    }
  }
}
```

### VS Code
Configure in your VS Code settings for MCP integration.

## Security Features

- Path validation to prevent directory traversal attacks
- Safe file operations with error handling
- Logging to stderr (not stdout) to maintain MCP protocol compatibility
- Graceful error handling for all operations

## Example Usage

Once connected through an MCP client, you can:

```
# Read a configuration file
read_file("config/settings.json")

# List project files
list_directory("src/")

# Find all Python test files
search_files("tests/", "test_*.py", true)

# Create a new directory
create_directory("new_feature/")

# Write a new file
write_file("new_feature/feature.py", "# New feature implementation\n")
```

## Logging

The server logs to stderr and includes:
- Server startup/shutdown events
- Tool execution information
- Error details for debugging
- Path validation warnings

## Error Handling

The server provides user-friendly error messages for common issues:
- File not found errors
- Permission denied errors
- Invalid path specifications
- Directory traversal attempts

All errors are returned as MCP TextContent responses rather than throwing exceptions.
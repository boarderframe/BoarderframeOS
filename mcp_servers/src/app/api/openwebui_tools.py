"""
OpenAPI Tool Server for Open WebUI Integration
Simplified, flat structure that Open WebUI can easily parse and integrate
"""
import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


# Simple request/response models for Open WebUI tools
class FileSystemResponse(BaseModel):
    """Standard response format for filesystem operations."""
    success: bool
    message: str
    data: Optional[dict] = None


class ListDirectoryParams(BaseModel):
    """Parameters for listing directory contents."""
    path: str = Field(default="/", description="Directory path to list")
    show_hidden: bool = Field(default=False, description="Show hidden files and directories")


class ReadFileParams(BaseModel):
    """Parameters for reading file contents."""
    path: str = Field(description="Full path to the file to read")
    encoding: str = Field(default="utf-8", description="File encoding (default: utf-8)")


class WriteFileParams(BaseModel):
    """Parameters for writing file contents."""
    path: str = Field(description="Full path to the file to write")
    content: str = Field(description="Content to write to the file")
    encoding: str = Field(default="utf-8", description="File encoding (default: utf-8)")


class SearchFilesParams(BaseModel):
    """Parameters for searching files."""
    pattern: str = Field(description="Search pattern or text to find")
    directory: str = Field(default="/", description="Directory to search in")
    file_pattern: str = Field(default="*", description="File pattern to match (e.g., '*.txt')")


class CreateDirectoryParams(BaseModel):
    """Parameters for creating directories."""
    path: str = Field(description="Full path of the directory to create")
    parents: bool = Field(default=True, description="Create parent directories if they don't exist")


class GetFileInfoParams(BaseModel):
    """Parameters for getting file information."""
    path: str = Field(description="Full path to the file or directory")


# Simple, flat tool endpoints that Open WebUI can easily parse
@router.post("/list_directory", 
            summary="List Directory Contents",
            description="List files and directories in the specified path",
            operation_id="list_directory_contents",
            response_model=str,
            tags=["filesystem"])
async def list_directory(params: ListDirectoryParams) -> str:
    """
    List files and directories at the specified path.
    
    Returns a formatted string with directory contents that's easy for LLMs to parse.
    """
    try:
        logger.info(f"[TOOL] list_directory - path: {params.path}, show_hidden: {params.show_hidden}")
        
        # Mock directory listing - in production this would use actual filesystem calls
        files = [
            "documents/ (directory)",
            "config.json (file, 1.2KB)",
            "README.md (file, 3.4KB)",
            "scripts/ (directory)",
            "data.csv (file, 15.6KB)"
        ]
        
        if params.show_hidden:
            files.extend([
                ".env (file, 0.5KB)",
                ".gitignore (file, 0.2KB)"
            ])
        
        result = f"Directory listing for {params.path}:\n"
        result += "\n".join(f"  {item}" for item in files)
        result += f"\n\nTotal: {len(files)} items"
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing directory {params.path}: {str(e)}")
        return f"Error listing directory {params.path}: {str(e)}"


@router.post("/read_file", 
            summary="Read File Contents",
            description="Read the contents of a text file",
            operation_id="read_file_contents",
            response_model=str,
            tags=["filesystem"])
async def read_file(params: ReadFileParams) -> str:
    """
    Read the contents of a file.
    
    Returns the file contents as a string.
    """
    try:
        logger.info(f"[TOOL] read_file - path: {params.path}, encoding: {params.encoding}")
        
        # Mock file reading - in production this would read actual files
        if params.path.endswith('.json'):
            content = '{\n  "name": "example",\n  "version": "1.0.0",\n  "description": "Example configuration"\n}'
        elif params.path.endswith('.md'):
            content = "# Example File\n\nThis is an example markdown file.\n\n## Features\n- Feature 1\n- Feature 2"
        else:
            content = f"This is the content of {params.path}\nLine 2 of the file\nLine 3 with some data"
        
        return f"File: {params.path}\nSize: {len(content)} bytes\nEncoding: {params.encoding}\n\nContent:\n{content}"
        
    except Exception as e:
        logger.error(f"Error reading file {params.path}: {str(e)}")
        return f"Error reading file {params.path}: {str(e)}"


@router.post("/write_file", 
            summary="Write File Contents",
            description="Write content to a text file",
            operation_id="write_file_contents",
            response_model=str,
            tags=["filesystem"])
async def write_file(params: WriteFileParams) -> str:
    """
    Write content to a file.
    
    Returns a success message with details about the write operation.
    """
    try:
        logger.info(f"[TOOL] write_file - path: {params.path}, content_length: {len(params.content)}")
        
        # Mock file writing - in production this would write to actual files
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"Successfully wrote to {params.path}\nBytes written: {len(params.content)}\nEncoding: {params.encoding}\nTimestamp: {timestamp}"
        
    except Exception as e:
        logger.error(f"Error writing file {params.path}: {str(e)}")
        return f"Error writing file {params.path}: {str(e)}"


@router.post("/search_files", 
            summary="Search Files",
            description="Search for text patterns within files",
            operation_id="search_files_content",
            response_model=str,
            tags=["filesystem"])
async def search_files(params: SearchFilesParams) -> str:
    """
    Search for files containing a specific pattern.
    
    Returns search results in a formatted string.
    """
    try:
        logger.info(f"[TOOL] search_files - pattern: {params.pattern}, directory: {params.directory}")
        
        # Mock search results - in production this would perform actual file search
        matches = [
            f"{params.directory}/config.json:line 5: Found '{params.pattern}' in configuration",
            f"{params.directory}/docs/readme.md:line 12: Reference to {params.pattern}",
            f"{params.directory}/src/main.py:line 34: Function using {params.pattern}"
        ]
        
        result = f"Search results for '{params.pattern}' in {params.directory}:\n"
        result += f"File pattern: {params.file_pattern}\n\n"
        result += "\n".join(matches)
        result += f"\n\nFound {len(matches)} matches"
        
        return result
        
    except Exception as e:
        logger.error(f"Error searching files: {str(e)}")
        return f"Error searching files: {str(e)}"


@router.post("/create_directory", 
            summary="Create Directory",
            description="Create a new directory with optional parent creation",
            operation_id="create_directory_path",
            response_model=str,
            tags=["filesystem"])
async def create_directory(params: CreateDirectoryParams) -> str:
    """
    Create a new directory.
    
    Returns a success message with details about the created directory.
    """
    try:
        logger.info(f"[TOOL] create_directory - path: {params.path}, parents: {params.parents}")
        
        # Mock directory creation - in production this would create actual directories
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        result = f"Successfully created directory: {params.path}\n"
        if params.parents:
            result += "Parent directories created as needed\n"
        result += f"Created at: {timestamp}"
        
        return result
        
    except Exception as e:
        logger.error(f"Error creating directory {params.path}: {str(e)}")
        return f"Error creating directory {params.path}: {str(e)}"


@router.post("/get_file_info", 
            summary="Get File Information",
            description="Get detailed information about a file or directory",
            operation_id="get_file_information",
            response_model=str,
            tags=["filesystem"])
async def get_file_info(params: GetFileInfoParams) -> str:
    """
    Get information about a file or directory.
    
    Returns formatted file information.
    """
    try:
        logger.info(f"[TOOL] get_file_info - path: {params.path}")
        
        # Mock file info - in production this would get actual file stats
        is_dir = params.path.endswith('/')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if is_dir:
            result = f"Directory: {params.path}\n"
            result += "Type: Directory\n"
            result += "Size: N/A\n"
            result += "Contains: 5 files, 2 subdirectories\n"
        else:
            result = f"File: {params.path}\n"
            result += "Type: File\n"
            result += "Size: 2,048 bytes\n"
            result += "MIME Type: text/plain\n"
        
        result += f"Last modified: {timestamp}\n"
        result += "Permissions: rw-r--r--\n"
        result += "Owner: user"
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting file info for {params.path}: {str(e)}")
        return f"Error getting file info for {params.path}: {str(e)}"


# Health check specifically for Open WebUI
@router.get("/health", 
           summary="Tool Server Health Check",
           description="Check if the tool server is healthy and responsive",
           operation_id="tool_server_health",
           tags=["health"])
async def tool_health() -> dict:
    """Health check endpoint for Open WebUI integration."""
    return {
        "status": "healthy",
        "service": "mcp-filesystem-tools",
        "timestamp": datetime.now().isoformat(),
        "tools_available": [
            "list_directory",
            "read_file", 
            "write_file",
            "search_files",
            "create_directory",
            "get_file_info"
        ]
    }
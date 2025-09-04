#!/usr/bin/env python3
"""
Advanced Filesystem Server for Open WebUI - Enhanced Features
Based on the best MCP filesystem servers with OpenAPI compatibility
Provides comprehensive file operations optimized for LLM interaction
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import glob
import json
import shutil
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
import re
import mimetypes
import base64
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Advanced Filesystem Tools", 
    description="Comprehensive file operations for Open WebUI with enhanced features",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security: Define allowed base directories
ALLOWED_DIRECTORIES = [
    "/Users/cosburn"  # Full access to cosburn user directory
]

# Advanced request models without enums (OpenAPI compatible)
class ListDirectoryRequest(BaseModel):
    path: str = "/Users/cosburn"
    show_hidden: bool = False
    recursive: bool = False

class ReadFileRequest(BaseModel):
    path: str
    encoding: str = "utf-8"
    max_size: int = 1000000  # 1MB limit

class ReadFileLinesRequest(BaseModel):
    path: str
    offset: int = 0
    limit: int = 100
    encoding: str = "utf-8"

class WriteFileRequest(BaseModel):
    path: str
    content: str
    encoding: str = "utf-8"
    create_dirs: bool = True

class MoveFileRequest(BaseModel):
    source: str
    destination: str

class CopyFileRequest(BaseModel):
    source: str
    destination: str

class DeleteRequest(BaseModel):
    path: str
    recursive: bool = False

class SearchFilesRequest(BaseModel):
    path: str = "/Users/cosburn"
    pattern: str = "*"
    content_pattern: Optional[str] = None
    recursive: bool = True
    case_sensitive: bool = False
    max_results: int = 100

class CreateDirectoryRequest(BaseModel):
    path: str
    create_parents: bool = True

def is_path_allowed(path: str) -> bool:
    """Check if path is within allowed directories"""
    try:
        abs_path = os.path.abspath(path)
        for allowed_dir in ALLOWED_DIRECTORIES:
            if abs_path.startswith(os.path.abspath(allowed_dir)):
                return True
        return False
    except:
        return False

def safe_path_resolve(path: str) -> str:
    """Safely resolve path and validate"""
    try:
        # Replace "." with home directory
        if path == ".":
            path = "/Users/cosburn"
        
        result = os.path.abspath(path)
        if is_path_allowed(result):
            return result
        raise ValueError("Path not allowed")
    except Exception as e:
        raise HTTPException(status_code=403, detail=f"Invalid path: {str(e)}")

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 bytes"
    
    size_names = ["bytes", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    if i == 0:
        return f"{int(size_bytes)} {size_names[i]}"
    else:
        return f"{size_bytes:.1f} {size_names[i]}"

@app.post("/list_directory")
async def list_directory(request: ListDirectoryRequest) -> str:
    """List directory contents with enhanced information"""
    try:
        path = safe_path_resolve(request.path)
        
        if not os.path.exists(path):
            return f"Error: Directory '{path}' does not exist"
        
        if not os.path.isdir(path):
            return f"Error: '{path}' is not a directory"
        
        items = []
        total_size = 0
        file_count = 0
        dir_count = 0
        
        try:
            entries = os.listdir(path)
            if not request.show_hidden:
                entries = [e for e in entries if not e.startswith('.')]
            
            entries.sort()
            
            for item in entries:
                item_path = os.path.join(path, item)
                try:
                    stat = os.stat(item_path)
                    size = stat.st_size
                    modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                    
                    if os.path.isdir(item_path):
                        items.append(f"📁 {item}/ (modified: {modified})")
                        dir_count += 1
                        if request.recursive:
                            # Count items in subdirectory
                            try:
                                sub_items = len(os.listdir(item_path))
                                items[-1] = f"📁 {item}/ ({sub_items} items, modified: {modified})"
                            except:
                                pass
                    else:
                        size_str = format_file_size(size)
                        items.append(f"📄 {item} ({size_str}, modified: {modified})")
                        total_size += size
                        file_count += 1
                except (OSError, PermissionError):
                    items.append(f"❌ {item} (access denied)")
            
            result = f"Directory listing for '{path}':\n\n"
            result += f"Summary: {dir_count} directories, {file_count} files, total size: {format_file_size(total_size)}\n\n"
            
            if items:
                result += "\n".join(items)
            else:
                result += "(empty directory)"
            
            logger.info(f"Listed directory: {path} ({len(items)} items)")
            return result
            
        except PermissionError:
            return f"Error: Permission denied accessing directory '{path}'"
            
    except Exception as e:
        logger.error(f"List directory failed: {e}")
        return f"Error listing directory: {str(e)}"

@app.post("/read_file")
async def read_file(request: ReadFileRequest) -> str:
    """Read complete file contents"""
    try:
        file_path = safe_path_resolve(request.path)
        
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' does not exist"
        
        if not os.path.isfile(file_path):
            return f"Error: '{file_path}' is not a file"
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > request.max_size:
            return f"Error: File too large ({format_file_size(file_size)}). Maximum allowed: {format_file_size(request.max_size)}"
        
        try:
            with open(file_path, 'r', encoding=request.encoding) as f:
                content = f.read()
            
            logger.info(f"Read file: {file_path} ({len(content)} characters)")
            return f"File contents of '{file_path}' ({format_file_size(file_size)}):\n\n{content}"
            
        except UnicodeDecodeError:
            # Try to detect if it's a binary file
            with open(file_path, 'rb') as f:
                binary_content = f.read(1024)  # Read first 1KB
            
            # Check if it looks like a binary file
            if b'\x00' in binary_content:
                return f"Binary file '{file_path}' ({format_file_size(file_size)}). Cannot display as text."
            else:
                # Try with different encoding
                try:
                    with open(file_path, 'r', encoding='latin1') as f:
                        content = f.read()
                    return f"File contents of '{file_path}' (read with latin1 encoding):\n\n{content}"
                except:
                    return f"Error: Could not read file '{file_path}' with any encoding"
            
        except PermissionError:
            return f"Error: Permission denied reading file '{file_path}'"
            
    except Exception as e:
        logger.error(f"Read file failed: {e}")
        return f"Error reading file: {str(e)}"

@app.post("/read_file_lines")
async def read_file_lines(request: ReadFileLinesRequest) -> str:
    """Read specific lines from a file for efficient large file handling"""
    try:
        file_path = safe_path_resolve(request.path)
        
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' does not exist"
        
        if not os.path.isfile(file_path):
            return f"Error: '{file_path}' is not a file"
        
        try:
            with open(file_path, 'r', encoding=request.encoding) as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            start_line = max(0, request.offset)
            end_line = min(total_lines, start_line + request.limit)
            
            if start_line >= total_lines:
                return f"Error: Offset {request.offset} exceeds file length ({total_lines} lines)"
            
            selected_lines = lines[start_line:end_line]
            content = ''.join(selected_lines)
            
            result = f"Lines {start_line + 1}-{end_line} of '{file_path}' (total: {total_lines} lines):\n\n"
            
            # Add line numbers
            for i, line in enumerate(selected_lines, start_line + 1):
                result += f"{i:4d}: {line}"
            
            logger.info(f"Read lines {start_line}-{end_line} from {file_path}")
            return result
            
        except UnicodeDecodeError:
            return f"Error: Cannot read '{file_path}' as text with {request.encoding} encoding"
        except PermissionError:
            return f"Error: Permission denied reading file '{file_path}'"
            
    except Exception as e:
        logger.error(f"Read file lines failed: {e}")
        return f"Error reading file lines: {str(e)}"

@app.post("/write_file")
async def write_file(request: WriteFileRequest) -> str:
    """Write content to file with directory creation"""
    try:
        file_path = safe_path_resolve(request.path)
        
        # Create directories if requested
        if request.create_dirs:
            parent_dir = os.path.dirname(file_path)
            os.makedirs(parent_dir, exist_ok=True)
        
        try:
            with open(file_path, 'w', encoding=request.encoding) as f:
                f.write(request.content)
            
            file_size = len(request.content.encode(request.encoding))
            logger.info(f"Wrote file: {file_path} ({format_file_size(file_size)})")
            return f"Successfully wrote {format_file_size(file_size)} to '{file_path}'"
            
        except PermissionError:
            return f"Error: Permission denied writing to '{file_path}'"
            
    except Exception as e:
        logger.error(f"Write file failed: {e}")
        return f"Error writing file: {str(e)}"

@app.post("/move_file")
async def move_file(request: MoveFileRequest) -> str:
    """Move or rename files and directories"""
    try:
        source_path = safe_path_resolve(request.source)
        dest_path = safe_path_resolve(request.destination)
        
        if not os.path.exists(source_path):
            return f"Error: Source '{source_path}' does not exist"
        
        if os.path.exists(dest_path):
            return f"Error: Destination '{dest_path}' already exists"
        
        try:
            shutil.move(source_path, dest_path)
            logger.info(f"Moved: {source_path} -> {dest_path}")
            return f"Successfully moved '{request.source}' to '{request.destination}'"
            
        except PermissionError:
            return f"Error: Permission denied moving '{source_path}'"
            
    except Exception as e:
        logger.error(f"Move file failed: {e}")
        return f"Error moving file: {str(e)}"

@app.post("/copy_file")
async def copy_file(request: CopyFileRequest) -> str:
    """Copy files or directories"""
    try:
        source_path = safe_path_resolve(request.source)
        dest_path = safe_path_resolve(request.destination)
        
        if not os.path.exists(source_path):
            return f"Error: Source '{source_path}' does not exist"
        
        if os.path.exists(dest_path):
            return f"Error: Destination '{dest_path}' already exists"
        
        try:
            if os.path.isfile(source_path):
                shutil.copy2(source_path, dest_path)
                size = os.path.getsize(dest_path)
                logger.info(f"Copied file: {source_path} -> {dest_path} ({format_file_size(size)})")
                return f"Successfully copied file '{request.source}' to '{request.destination}' ({format_file_size(size)})"
            elif os.path.isdir(source_path):
                shutil.copytree(source_path, dest_path)
                logger.info(f"Copied directory: {source_path} -> {dest_path}")
                return f"Successfully copied directory '{request.source}' to '{request.destination}'"
            else:
                return f"Error: '{source_path}' is neither a file nor a directory"
            
        except PermissionError:
            return f"Error: Permission denied copying '{source_path}'"
            
    except Exception as e:
        logger.error(f"Copy file failed: {e}")
        return f"Error copying file: {str(e)}"

@app.post("/delete_file")
async def delete_file(request: DeleteRequest) -> str:
    """Delete files or directories"""
    try:
        target_path = safe_path_resolve(request.path)
        
        if not os.path.exists(target_path):
            return f"Error: Path '{target_path}' does not exist"
        
        try:
            if os.path.isfile(target_path):
                size = os.path.getsize(target_path)
                os.remove(target_path)
                logger.info(f"Deleted file: {target_path} ({format_file_size(size)})")
                return f"Successfully deleted file '{request.path}' ({format_file_size(size)})"
            elif os.path.isdir(target_path):
                if request.recursive:
                    shutil.rmtree(target_path)
                    logger.info(f"Deleted directory recursively: {target_path}")
                    return f"Successfully deleted directory '{request.path}' and all contents"
                else:
                    os.rmdir(target_path)
                    logger.info(f"Deleted empty directory: {target_path}")
                    return f"Successfully deleted empty directory '{request.path}'"
            else:
                return f"Error: '{target_path}' is neither a file nor a directory"
            
        except OSError as e:
            if "Directory not empty" in str(e):
                return f"Error: Directory '{request.path}' is not empty. Use recursive=true to delete with contents."
            return f"Error: {str(e)}"
        except PermissionError:
            return f"Error: Permission denied deleting '{target_path}'"
            
    except Exception as e:
        logger.error(f"Delete file failed: {e}")
        return f"Error deleting file: {str(e)}"

@app.post("/search_files")
async def search_files(request: SearchFilesRequest) -> str:
    """Advanced file search with content searching"""
    try:
        search_dir = safe_path_resolve(request.path)
        
        if not os.path.exists(search_dir):
            return f"Error: Directory '{search_dir}' does not exist"
        
        if not os.path.isdir(search_dir):
            return f"Error: '{search_dir}' is not a directory"
        
        matches = []
        content_matches = []
        
        # Build search pattern
        if request.recursive:
            pattern = os.path.join(search_dir, "**", request.pattern)
            file_matches = glob.glob(pattern, recursive=True)
        else:
            pattern = os.path.join(search_dir, request.pattern)
            file_matches = glob.glob(pattern)
        
        # Filter and format file matches
        for match in file_matches[:request.max_results]:
            if os.path.isfile(match):
                try:
                    rel_path = os.path.relpath(match, search_dir)
                    size = os.path.getsize(match)
                    size_str = format_file_size(size)
                    matches.append(f"📄 {rel_path} ({size_str})")
                except:
                    matches.append(f"📄 {match}")
        
        # Content search if requested
        if request.content_pattern:
            pattern_flags = 0 if request.case_sensitive else re.IGNORECASE
            try:
                content_regex = re.compile(request.content_pattern, pattern_flags)
            except re.error:
                return f"Error: Invalid regex pattern '{request.content_pattern}'"
            
            for match in file_matches:
                if os.path.isfile(match) and len(content_matches) < request.max_results:
                    try:
                        with open(match, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        if content_regex.search(content):
                            rel_path = os.path.relpath(match, search_dir)
                            # Find line numbers with matches
                            lines = content.split('\n')
                            matching_lines = []
                            for i, line in enumerate(lines, 1):
                                if content_regex.search(line):
                                    matching_lines.append(f"  Line {i}: {line.strip()[:100]}")
                                    if len(matching_lines) >= 3:  # Limit to 3 lines per file
                                        break
                            
                            if matching_lines:
                                content_matches.append(f"📄 {rel_path}:\n" + "\n".join(matching_lines))
                    except:
                        continue
        
        # Build result
        result = f"Search results in '{search_dir}':\n"
        result += f"Pattern: '{request.pattern}'"
        if request.content_pattern:
            result += f", Content: '{request.content_pattern}'"
        result += f", Recursive: {request.recursive}\n\n"
        
        if matches:
            result += f"File matches ({len(matches)}):\n" + "\n".join(matches)
        
        if content_matches:
            if matches:
                result += "\n\n"
            result += f"Content matches ({len(content_matches)}):\n" + "\n".join(content_matches)
        
        if not matches and not content_matches:
            result += "No matches found"
        
        logger.info(f"Search files: {search_dir} pattern={request.pattern} found={len(matches)} content_matches={len(content_matches)}")
        return result
        
    except Exception as e:
        logger.error(f"Search files failed: {e}")
        return f"Error searching files: {str(e)}"

@app.post("/create_directory")
async def create_directory(request: CreateDirectoryRequest) -> str:
    """Create directory with parent creation option"""
    try:
        dir_path = safe_path_resolve(request.path)
        
        if os.path.exists(dir_path):
            if os.path.isdir(dir_path):
                return f"Directory '{request.path}' already exists"
            else:
                return f"Error: '{request.path}' exists but is not a directory"
        
        try:
            if request.create_parents:
                os.makedirs(dir_path, exist_ok=True)
                logger.info(f"Created directory with parents: {dir_path}")
                return f"Successfully created directory '{request.path}' (with parent directories)"
            else:
                os.mkdir(dir_path)
                logger.info(f"Created directory: {dir_path}")
                return f"Successfully created directory '{request.path}'"
            
        except PermissionError:
            return f"Error: Permission denied creating directory '{dir_path}'"
            
    except Exception as e:
        logger.error(f"Create directory failed: {e}")
        return f"Error creating directory: {str(e)}"

@app.post("/get_file_info")
async def get_file_info(request: ReadFileRequest) -> str:
    """Get detailed file or directory metadata"""
    try:
        target_path = safe_path_resolve(request.path)
        
        if not os.path.exists(target_path):
            return f"Error: Path '{target_path}' does not exist"
        
        try:
            stat = os.stat(target_path)
            
            info = {
                "path": request.path,
                "absolute_path": target_path,
                "type": "directory" if os.path.isdir(target_path) else "file",
                "size": stat.st_size,
                "size_formatted": format_file_size(stat.st_size),
                "created": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "accessed": datetime.fromtimestamp(stat.st_atime).strftime("%Y-%m-%d %H:%M:%S"),
                "permissions": oct(stat.st_mode)[-3:],
                "owner_readable": bool(stat.st_mode & 0o400),
                "owner_writable": bool(stat.st_mode & 0o200),
                "owner_executable": bool(stat.st_mode & 0o100),
            }
            
            if os.path.isfile(target_path):
                # Add file-specific info
                info["mime_type"] = mimetypes.guess_type(target_path)[0] or "unknown"
                info["extension"] = os.path.splitext(target_path)[1]
            
            # Format result
            result = f"File information for '{request.path}':\n\n"
            for key, value in info.items():
                formatted_key = key.replace("_", " ").title()
                result += f"{formatted_key}: {value}\n"
            
            logger.info(f"Got file info: {target_path}")
            return result
            
        except PermissionError:
            return f"Error: Permission denied accessing '{target_path}'"
            
    except Exception as e:
        logger.error(f"Get file info failed: {e}")
        return f"Error getting file info: {str(e)}"

@app.get("/")
async def root():
    return {"message": "Advanced Filesystem Tools API for Open WebUI", "status": "running"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "tools": [
            "list_directory", "read_file", "read_file_lines", "write_file", 
            "move_file", "copy_file", "delete_file", "search_files", 
            "create_directory", "get_file_info"
        ],
        "allowed_directories": len(ALLOWED_DIRECTORIES),
        "features": [
            "Enhanced directory listings", "Line-based file reading", 
            "Content search", "File operations", "Metadata access"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9003)
#!/usr/bin/env python3
"""
Simple Filesystem Server for Open WebUI - No Enums
Provides basic file operations without complex enums to avoid LLM compatibility issues
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import glob
import json
from pathlib import Path
from typing import List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Simple Filesystem Tools", 
    description="Basic file operations for Open WebUI integration",
    version="1.0.0"
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

# Simple request models without enums
class ListDirectoryRequest(BaseModel):
    path: str = "/Users/cosburn"
    show_hidden: bool = False

class ReadFileRequest(BaseModel):
    file_path: str
    max_size: int = 100000  # 100KB limit

class WriteFileRequest(BaseModel):
    file_path: str
    content: str
    create_dirs: bool = False

class SearchFilesRequest(BaseModel):
    directory: str = "."
    pattern: str = "*.txt"
    recursive: bool = False

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

def safe_path_join(base: str, *paths) -> str:
    """Safely join paths and validate"""
    try:
        result = os.path.join(base, *paths)
        result = os.path.abspath(result)
        if is_path_allowed(result):
            return result
        raise ValueError("Path not allowed")
    except Exception as e:
        raise HTTPException(status_code=403, detail=f"Invalid path: {str(e)}")

@app.post("/list_directory")
async def list_directory(request: ListDirectoryRequest) -> str:
    """List directory contents"""
    try:
        # Replace "." with home directory
        actual_path = "/Users/cosburn" if request.path == "." else request.path
        
        if not is_path_allowed(actual_path):
            return "Error: Directory access not allowed for security reasons"
        
        path = os.path.abspath(actual_path)
        if not os.path.exists(path):
            return f"Error: Directory '{path}' does not exist"
        
        if not os.path.isdir(path):
            return f"Error: '{path}' is not a directory"
        
        items = []
        try:
            for item in os.listdir(path):
                if item.startswith('.') and not request.show_hidden:
                    continue
                
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    items.append(f"📁 {item}/")
                else:
                    # Get file size
                    try:
                        size = os.path.getsize(item_path)
                        size_str = f" ({size} bytes)" if size < 1024 else f" ({size//1024}KB)"
                    except:
                        size_str = ""
                    items.append(f"📄 {item}{size_str}")
            
            result = f"Directory listing for '{path}':\n\n"
            if items:
                result += "\n".join(sorted(items))
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
    """Read file contents"""
    try:
        if not is_path_allowed(request.file_path):
            return "Error: File access not allowed for security reasons"
        
        file_path = os.path.abspath(request.file_path)
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' does not exist"
        
        if not os.path.isfile(file_path):
            return f"Error: '{file_path}' is not a file"
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > request.max_size:
            return f"Error: File too large ({file_size} bytes). Maximum allowed: {request.max_size} bytes"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.info(f"Read file: {file_path} ({len(content)} characters)")
            return f"File contents of '{file_path}':\n\n{content}"
            
        except UnicodeDecodeError:
            # Try binary read for non-text files
            with open(file_path, 'rb') as f:
                binary_content = f.read()
            return f"Binary file '{file_path}' ({len(binary_content)} bytes). Cannot display as text."
            
        except PermissionError:
            return f"Error: Permission denied reading file '{file_path}'"
            
    except Exception as e:
        logger.error(f"Read file failed: {e}")
        return f"Error reading file: {str(e)}"

@app.post("/write_file")
async def write_file(request: WriteFileRequest) -> str:
    """Write content to file"""
    try:
        if not is_path_allowed(request.file_path):
            return "Error: File write not allowed for security reasons"
        
        file_path = os.path.abspath(request.file_path)
        
        # Create directories if requested
        if request.create_dirs:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(request.content)
            
            logger.info(f"Wrote file: {file_path} ({len(request.content)} characters)")
            return f"Successfully wrote {len(request.content)} characters to '{file_path}'"
            
        except PermissionError:
            return f"Error: Permission denied writing to '{file_path}'"
            
    except Exception as e:
        logger.error(f"Write file failed: {e}")
        return f"Error writing file: {str(e)}"

@app.post("/search_files")
async def search_files(request: SearchFilesRequest) -> str:
    """Search for files by pattern"""
    try:
        if not is_path_allowed(request.directory):
            return "Error: Directory search not allowed for security reasons"
        
        search_dir = os.path.abspath(request.directory)
        if not os.path.exists(search_dir):
            return f"Error: Directory '{search_dir}' does not exist"
        
        if not os.path.isdir(search_dir):
            return f"Error: '{search_dir}' is not a directory"
        
        # Build search pattern
        if request.recursive:
            pattern = os.path.join(search_dir, "**", request.pattern)
            matches = glob.glob(pattern, recursive=True)
        else:
            pattern = os.path.join(search_dir, request.pattern)
            matches = glob.glob(pattern)
        
        # Filter out directories and format results
        files = []
        for match in matches:
            if os.path.isfile(match):
                # Get relative path for cleaner display
                try:
                    rel_path = os.path.relpath(match, search_dir)
                    size = os.path.getsize(match)
                    size_str = f" ({size} bytes)" if size < 1024 else f" ({size//1024}KB)"
                    files.append(f"📄 {rel_path}{size_str}")
                except:
                    files.append(f"📄 {match}")
        
        result = f"Search results for '{request.pattern}' in '{search_dir}':\n"
        result += f"Recursive: {request.recursive}\n\n"
        
        if files:
            result += f"Found {len(files)} files:\n" + "\n".join(sorted(files))
        else:
            result += "No files found matching the pattern"
        
        logger.info(f"Search files: {search_dir} pattern={request.pattern} found={len(files)}")
        return result
        
    except Exception as e:
        logger.error(f"Search files failed: {e}")
        return f"Error searching files: {str(e)}"

@app.get("/")
async def root():
    return {"message": "Simple Filesystem Tools API for Open WebUI", "status": "running"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "tools": ["list_directory", "read_file", "write_file", "search_files"],
        "allowed_directories": len(ALLOWED_DIRECTORIES)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9001)
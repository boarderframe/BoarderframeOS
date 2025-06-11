"""
Unified MCP Filesystem Server - BoarderframeOS Agent Storage
Consolidation of three implementations:
- Original: Basic file operations with MCP protocol support
- Enhanced: Async I/O, streaming, integrity checking, performance monitoring
- AI-Enhanced: Semantic search, content analysis, embeddings, similarity matching

Features:
- Complete MCP filesystem protocol support
- Async file I/O with aiofiles
- Chunked streaming for large files
- xxHash-64/BLAKE3/SHA256/MD5 integrity checking
- Enhanced error handling and retry logic
- Progress tracking for long operations
- Performance monitoring
- AI content analysis and semantic search
- Vector embeddings and similarity matching
- Real-time file system event notifications via SSE and WebSockets
- Adaptive chunk sizing for optimal performance
- Pluggable hashing algorithms
"""

import asyncio
import difflib
import fnmatch
import gzip
import hashlib
import json
import logging
import mimetypes
import os
import re
import shutil
import stat
import time
import uuid
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import (
    Any,
    AsyncGenerator,
    BinaryIO,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)

import uvicorn
import yaml
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    Header,
    HTTPException,
    Request,
    Security,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Enhanced imports for async I/O and integrity - optional
try:
    import aiofiles
    HAS_AIOFILES = True
except ImportError:
    HAS_AIOFILES = False
    logger.warning("aiofiles not available - using synchronous file I/O")

try:
    import xxhash
    HAS_XXHASH = True
except ImportError:
    HAS_XXHASH = False
    logger.warning("xxhash not available - using SHA256 for checksums")

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False
    logger.warning("watchdog not available - file system monitoring disabled")

# Optional AI/ML imports
try:
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    logger.warning("numpy/sklearn not available - advanced similarity calculations disabled")

try:
    from sentence_transformers import SentenceTransformer
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    logger.warning("sentence-transformers not available - AI features disabled")

try:
    import aiosqlite
    HAS_SQLITE = True
except ImportError:
    HAS_SQLITE = False
    logger.warning("aiosqlite not available - version control and embeddings disabled")

try:
    import tiktoken
    HAS_TIKTOKEN = True
except ImportError:
    HAS_TIKTOKEN = False
    logger.warning("tiktoken not available - token counting disabled")

try:
    from pygments import highlight
    from pygments.formatters import TerminalFormatter
    from pygments.lexers import get_lexer_by_name, guess_lexer
    HAS_PYGMENTS = True
except ImportError:
    HAS_PYGMENTS = False
    logger.warning("pygments not available - syntax highlighting disabled")

try:
    import blake3
    HAS_BLAKE3 = True
except ImportError:
    HAS_BLAKE3 = False
    logger.warning("blake3 not available - using alternative hash algorithms")

try:
    import gzip
    HAS_GZIP = True
except ImportError:
    HAS_GZIP = False
    logger.warning("gzip not available - compression disabled")

# Constants
DEFAULT_CHUNK_SIZE = 64 * 1024  # 64KB chunks (will be adaptive)
LARGE_FILE_CHUNK_SIZE = 8 * 1024 * 1024  # 8MB chunks for large files
MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1GB limit (increased)
LARGE_FILE_THRESHOLD = 100 * 1024 * 1024  # 100MB threshold for large file handling
MAX_OPERATION_TIME = 600  # 10 minutes (increased)
DEFAULT_EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
MAX_VERSIONS_PER_FILE = 10  # Maximum versions to keep per file
CHUNK_TARGET_TIME = 0.2  # seconds – target per-chunk duration when AUTO_CHUNK is on

# Rate limiting configuration
RATE_LIMIT_GENERAL = 100  # requests per minute for general operations
RATE_LIMIT_FILES = 20     # requests per minute for file upload/download
RATE_LIMIT_BATCH = 10     # requests per minute for batch operations
RATE_LIMIT_AI = 5         # requests per minute for AI operations
RATE_LIMIT_WINDOW = 60    # time window in seconds

# --------------------------------------------------------------------------
# Feature toggles (env‑driven; default safe values)
# --------------------------------------------------------------------------
AUTO_CHUNK   = os.getenv("AUTO_CHUNK", "false").lower() in ("1", "true", "yes")
HASH_ALGO    = os.getenv("HASH_ALGO", "xxhash").lower()          # xxhash | blake3 | sha256
GZIP_CHUNK   = os.getenv("GZIP_CHUNK", "false").lower() in ("1", "true", "yes")

# Data Models
class FileMetadata(BaseModel):
    path: str
    size: int
    modified: float
    created: float
    checksum: Optional[str] = None
    content_type: Optional[str] = None
    encoding: Optional[str] = None
    permissions: Optional[str] = None

class StreamProgress(BaseModel):
    operation_id: str
    bytes_processed: int
    total_bytes: int
    percentage: float
    status: str = "in_progress"
    speed_mbps: Optional[float] = None
    eta_seconds: Optional[float] = None

class BatchOperation(BaseModel):
    operations: List[Dict[str, Any]]
    parallel: bool = False
    stop_on_error: bool = True

class ContentAnalysis(BaseModel):
    file_path: str
    content_type: str
    encoding: str
    size: int
    line_count: Optional[int] = None
    word_count: Optional[int] = None
    char_count: Optional[int] = None
    language: Optional[str] = None
    syntax_highlighted: Optional[str] = None
    summary: Optional[str] = None
    key_terms: Optional[List[str]] = None
    complexity_score: Optional[float] = None

class SearchResult(BaseModel):
    path: str
    score: float
    snippet: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class EmbeddingResult(BaseModel):
    file_path: str
    embeddings: List[float]
    model: str
    chunk_count: int
    processing_time: float

# Rate Limiting Implementation
class RateLimiter:
    """Advanced rate limiter with different limits for different operation types"""

    def __init__(self):
        self.requests = defaultdict(list)  # client_id -> [(timestamp, operation_type), ...]

    def is_allowed(self, client_id: str, operation_type: str) -> bool:
        """Check if request is allowed based on rate limits"""
        now = time.time()

        # Get rate limit for operation type
        if operation_type == "ai":
            limit = RATE_LIMIT_AI
        elif operation_type == "files":
            limit = RATE_LIMIT_FILES
        elif operation_type == "batch":
            limit = RATE_LIMIT_BATCH
        else:
            limit = RATE_LIMIT_GENERAL

        # Clean old requests outside the time window
        self.requests[client_id] = [
            (timestamp, op_type) for timestamp, op_type in self.requests[client_id]
            if now - timestamp < RATE_LIMIT_WINDOW
        ]

        # Count requests of this type in the current window
        current_count = sum(
            1 for timestamp, op_type in self.requests[client_id]
            if op_type == operation_type or operation_type == "general"
        )

        if current_count < limit:
            self.requests[client_id].append((now, operation_type))
            return True

        return False

    def get_stats(self, client_id: str) -> Dict[str, Any]:
        """Get rate limiting stats for a client"""
        now = time.time()

        # Clean old requests
        self.requests[client_id] = [
            (timestamp, op_type) for timestamp, op_type in self.requests[client_id]
            if now - timestamp < RATE_LIMIT_WINDOW
        ]

        # Count by operation type
        counts = defaultdict(int)
        for timestamp, op_type in self.requests[client_id]:
            counts[op_type] += 1

        return {
            "current_window_requests": dict(counts),
            "window_seconds": RATE_LIMIT_WINDOW,
            "limits": {
                "general": RATE_LIMIT_GENERAL,
                "files": RATE_LIMIT_FILES,
                "batch": RATE_LIMIT_BATCH,
                "ai": RATE_LIMIT_AI
            }
        }

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for filesystem server"""

    def __init__(self, app, rate_limiter: RateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter

    async def dispatch(self, request: Request, call_next):
        # Get client identifier (IP address)
        client_id = request.client.host if request.client else "unknown"

        # Determine operation type based on request
        operation_type = self._get_operation_type(request)

        # Check rate limit
        if not self.rate_limiter.is_allowed(client_id, operation_type):
            stats = self.rate_limiter.get_stats(client_id)
            return Response(
                content=json.dumps({
                    "error": "Rate limit exceeded",
                    "operation_type": operation_type,
                    "client_stats": stats
                }),
                status_code=429,
                headers={"Content-Type": "application/json"}
            )

        # Process request
        response = await call_next(request)
        return response

    def _get_operation_type(self, request: Request) -> str:
        """Determine operation type from request"""
        path = request.url.path
        method = request.method

        # File operations
        if path.startswith(("/upload", "/download")):
            return "files"

        # Batch operations
        if path.startswith("/batch"):
            return "batch"

        # RPC operations - need to check if it's AI-related
        if path.startswith("/rpc"):
            return "ai"  # Assume RPC calls might be AI operations

        # General operations
        return "general"

class FileVersion(BaseModel):
    version_id: str
    file_path: str
    description: Optional[str] = None
    content_hash: str
    size: int
    created_at: datetime
    created_by: str = "system"

class VersionDiff(BaseModel):
    version1: str
    version2: str
    file_path: str
    diff_text: str
    changed_lines: int
    diff_type: str  # 'text' or 'binary'

class VersionControlResult(BaseModel):
    success: bool
    version_id: Optional[str] = None
    versions: Optional[List[FileVersion]] = None
    diff: Optional[VersionDiff] = None
    error: Optional[str] = None
    message: Optional[str] = None

class MCPFileEventHandler(FileSystemEventHandler):
    """Bridges watchdog events to UnifiedFilesystemServer broadcasts."""
    def __init__(self, server: 'UnifiedFilesystemServer'):
        super().__init__()
        self.server = server

    def on_any_event(self, event):
        data = {
            "event_type": event.event_type,
            "is_directory": event.is_directory,
            "src_path": os.path.relpath(event.src_path, self.server.base_path)
                       if hasattr(event, "src_path") else None,
            "dest_path": os.path.relpath(event.dest_path, self.server.base_path)
                        if hasattr(event, "dest_path") else None,
            "timestamp": time.time()
        }
        try:
            asyncio.get_running_loop().create_task(self.server.broadcast_fs_event(data))
        except RuntimeError:
            # Called before loop starts—ignore
            pass

class UnifiedFilesystemServer:
    """Unified MCP Filesystem Server with full feature set"""

    def __init__(self, base_path: str = None, temp_path: str = None):
        self.base_path = Path(base_path or os.getcwd()).resolve()
        self.temp_path = Path(temp_path or (self.base_path / "temp")).resolve()
        self.temp_path.mkdir(exist_ok=True)

        # FastAPI app
        self.app = FastAPI(title="Unified MCP Filesystem Server", version="1.0.0")
        # --- API prefix for v1 (non‑breaking migration) ---
        self.v1_prefix = "/v1"

        # Rate limiting
        self.rate_limiter = RateLimiter()

        self._setup_middleware()
        self._setup_routes()

        # Performance tracking
        self.stats = {
            "operations": {},
            "total_bytes_processed": 0,
            "total_operations": 0,
            "average_speed_mbps": 0.0,
            "uptime_start": time.time()
        }

        # Operation tracking
        self.active_operations = {}
        self.connected_clients = {"progress": [], "notifications": []}

        # SSE queues listening for FS events
        self.fs_watchers: Set[asyncio.Queue] = set()

        # AI components
        self.embedding_model = None
        self.vector_db_path = self.base_path / "vectors.db"
        self.content_cache = {}

        # File system monitoring
        self.file_observer = None
        self.event_handler = None

        # Initialize AI components
        self._initialize_ai_components()

        logger.info(f"Unified Filesystem Server initialized with base path: {self.base_path}")

    def _setup_middleware(self):
        """Setup FastAPI middleware"""
        # Add rate limiting middleware first (processes requests before other middleware)
        self.app.add_middleware(RateLimitMiddleware, rate_limiter=self.rate_limiter)

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self):
        """Setup FastAPI routes"""
        # Health and status endpoints
        self.app.get("/health")(self.health_check)
        self.app.get("/stats")(self.get_stats)
        self.app.get("/rate-limit-stats")(self.get_rate_limit_stats)

        # File operation endpoints
        self.app.post("/upload")(self.upload_stream)
        self.app.get("/download/{path:path}")(self.download_stream)
        self.app.get("/metadata/{path:path}")(self.get_file_metadata)
        self.app.post("/batch")(self.batch_operations)

        # Version control endpoints
        self.app.post("/version/snapshot")(self.create_snapshot_endpoint)
        self.app.get("/version/list/{path:path}")(self.list_versions_endpoint)
        self.app.get("/version/diff/{path:path}")(self.get_diff_endpoint)
        self.app.post("/version/restore")(self.restore_version_endpoint)
        self.app.delete("/version/cleanup/{path:path}")(self.cleanup_versions_endpoint)

        # MCP JSON-RPC endpoint
        self.app.post("/rpc")(self.rpc_handler)

        # WebSocket endpoints
        self.app.websocket("/ws/progress/{operation_id}")(self.progress_websocket)
        self.app.websocket("/ws/events")(self.events_websocket)

        # SSE for FS events
        self.app.get("/fs/watch")(self.fs_watch_sse)

        # ------------------------------------------------------------------
        #  DUPLICATE ROUTES WITH /v1 PREFIX  (legacy paths remain available
        #  until OLD_PATHS is set to "false")
        # ------------------------------------------------------------------
        if os.getenv("OLD_PATHS", "true").lower() in ("1", "true", "yes"):
            # Leave legacy routes exactly as defined above
            pass

        # Register v1‑prefixed clones
        for route in list(self.app.routes):
            # Skip FastAPI internals & already‑prefixed paths
            if not getattr(route, "path", "").startswith("/") or route.path.startswith(self.v1_prefix):
                continue

            # FastAPI differentiates between websocket & http routes
            if "websocket" in route.__class__.__name__.lower():
                self.app.websocket(f"{self.v1_prefix}{route.path}")(route.endpoint)
            else:
                # Use same methods & endpoint
                for m in route.methods:
                    self.app.add_api_route(
                        f"{self.v1_prefix}{route.path}",
                        route.endpoint,
                        methods=[m],
                        name=f"{route.name}_v1" if route.name else None,
                    )

    def _initialize_ai_components(self):
        """Initialize AI components if available"""
        if HAS_TRANSFORMERS:
            try:
                self.embedding_model = SentenceTransformer(DEFAULT_EMBEDDING_MODEL)
                logger.info(f"Loaded embedding model: {DEFAULT_EMBEDDING_MODEL}")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                self.embedding_model = None

        # Note: Vector DB initialization will happen when server starts
        if HAS_SQLITE:
            logger.info("SQLite available, vector DB will be initialized on server start")

    async def _initialize_vector_db(self):
        """Initialize vector database for embeddings and version control"""
        try:
            async with aiosqlite.connect(self.vector_db_path) as db:
                # Vector embeddings tables
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS file_embeddings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_path TEXT UNIQUE,
                        content_hash TEXT,
                        embedding BLOB,
                        model TEXT,
                        chunk_size INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                await db.execute("""
                    CREATE TABLE IF NOT EXISTS content_chunks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_id INTEGER,
                        chunk_index INTEGER,
                        content TEXT,
                        embedding BLOB,
                        FOREIGN KEY(file_id) REFERENCES file_embeddings(id)
                    )
                """)

                # Version control tables
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS file_versions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_path TEXT NOT NULL,
                        version_id TEXT UNIQUE NOT NULL,
                        description TEXT,
                        content BLOB,
                        content_hash TEXT,
                        metadata TEXT,
                        size INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_by TEXT DEFAULT 'system'
                    )
                """)

                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_file_versions_path
                    ON file_versions(file_path)
                """)

                await db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_file_versions_created
                    ON file_versions(created_at)
                """)

                await db.commit()
                logger.info("Vector database and version control initialized")
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {e}")

    async def start(self, port: int = 8001):
        """Start the server"""
        # Initialize vector DB if available
        if HAS_SQLITE:
            await self._initialize_vector_db()

        self._start_file_monitoring()

        config = uvicorn.Config(
            app=self.app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()

    async def stop(self):
        """Stop the server and cleanup"""
        if self.file_observer:
            self.file_observer.stop()
            self.file_observer.join()

        # Close all WebSocket connections
        for client_list in self.connected_clients.values():
            for client in client_list:
                try:
                    await client.close()
                except:
                    pass

    def _start_file_monitoring(self):
        """Start file system monitoring"""
        if not HAS_WATCHDOG:
            logger.info("Watchdog not available, file monitoring disabled")
            return

        try:
            self.event_handler = MCPFileEventHandler(self)
            self.file_observer = Observer()
            self.file_observer.schedule(self.event_handler, str(self.base_path), recursive=True)
            self.file_observer.start()
            logger.info("File system monitoring started")
        except Exception as e:
            logger.error(f"Failed to start file monitoring: {e}")

    async def health_check(self):
        """Health check endpoint"""
        return {
            "status": "healthy",
            "uptime": time.time() - self.stats["uptime_start"],
            "base_path": str(self.base_path),
            "ai_available": self.embedding_model is not None,
            "active_operations": len(self.active_operations),
            "connected_clients": sum(len(clients) for clients in self.connected_clients.values()),
            "fs_watchers": len(self.fs_watchers),
            "features": {
                "aiofiles": HAS_AIOFILES,
                "xxhash": HAS_XXHASH,
                "watchdog": HAS_WATCHDOG,
                "numpy": HAS_NUMPY,
                "transformers": HAS_TRANSFORMERS,
                "sqlite": HAS_SQLITE,
                "tiktoken": HAS_TIKTOKEN,
                "pygments": HAS_PYGMENTS,
                "blake3": HAS_BLAKE3
            }
        }

    async def get_stats(self):
        """Get server statistics"""
        return {
            "stats": self.stats,
            "active_operations": len(self.active_operations),
            "connected_clients": {
                name: len(clients) for name, clients in self.connected_clients.items()
            },
            "fs_watchers": len(self.fs_watchers)
        }

    async def get_rate_limit_stats(self, request: Request):
        """Get rate limiting statistics for the requesting client"""
        # Get client identifier (IP address)
        client_id = request.client.host if request.client else "unknown"

        # Get rate limiting stats for this client
        client_stats = self.rate_limiter.get_stats(client_id)

        # Add global rate limiting information
        total_clients = len(self.rate_limiter.requests)

        return {
            "client_id": client_id,
            "client_stats": client_stats,
            "global_stats": {
                "total_tracked_clients": total_clients,
                "rate_limits": {
                    "general": RATE_LIMIT_GENERAL,
                    "files": RATE_LIMIT_FILES,
                    "batch": RATE_LIMIT_BATCH,
                    "ai": RATE_LIMIT_AI
                },
                "window_seconds": RATE_LIMIT_WINDOW
            }
        }

    # =============================================================================
    # Core File Operations (Original + Enhanced)
    # =============================================================================

    async def read_file_async(self, path: str, chunk_size: int = DEFAULT_CHUNK_SIZE) -> Dict[str, Any]:
        """Read file with async I/O and progress tracking"""
        operation_id = str(uuid.uuid4())

        try:
            file_path = self.validate_path(path)
            if not file_path.exists():
                return {"error": "File not found", "path": path}

            if not file_path.is_file():
                return {"error": "Path is not a file", "path": path}

            file_size = file_path.stat().st_size
            if file_size > MAX_FILE_SIZE:
                return {"error": f"File too large (max {MAX_FILE_SIZE} bytes)", "path": path}

            await self.register_operation(operation_id, "read", file_path)

            start_time = time.time()
            bytes_read = 0

            # Use async I/O if available, otherwise fall back to sync
            if HAS_AIOFILES:
                content_parts = []
                hasher = self._create_hasher()

                async with aiofiles.open(file_path, 'rb') as f:
                    while True:
                        chunk = await f.read(chunk_size)
                        if not chunk:
                            break

                        content_parts.append(chunk)
                        bytes_read += len(chunk)
                        if hasher:
                            hasher.update(chunk)

                        # Update progress
                        await self.update_operation_progress(operation_id, bytes_read, file_size,
                                                           (bytes_read / file_size) * 100)

                        if AUTO_CHUNK:
                            elapsed = time.time() - self.active_operations[operation_id]["start_time"]
                            chunk_size = self._auto_tune_chunk_size(bytes_read, elapsed, chunk_size)

                full_content = b''.join(content_parts)
            else:
                # Fallback to sync reading
                with open(file_path, 'rb') as f:
                    full_content = f.read()
                    bytes_read = len(full_content)
                hasher = None

            # Try to decode as text
            try:
                text_content = full_content.decode('utf-8')
                is_binary = False
            except UnicodeDecodeError:
                try:
                    text_content = full_content.decode('latin1')
                    is_binary = True
                except:
                    text_content = str(full_content)
                    is_binary = True

            elapsed_time = time.time() - start_time
            await self.complete_operation(operation_id)
            await self.update_stats("read", bytes_read, elapsed_time)

            result = {
                "content": text_content,
                "path": path,
                "size": bytes_read,
                "is_binary": is_binary,
                "operation_id": operation_id,
                "elapsed_time": elapsed_time
            }

            if hasher and HAS_XXHASH:
                result["checksum"] = hasher.hexdigest()

            return result

        except Exception as e:
            await self.fail_operation(operation_id, str(e))
            logger.error(f"Error reading file {path}: {e}")
            return {"error": str(e), "path": path}

    async def write_file_async(self, path: str, content: Union[str, bytes],
                             chunk_size: int = DEFAULT_CHUNK_SIZE,
                             verify_checksum: bool = True) -> Dict[str, Any]:
        """Write file with async I/O and integrity checking"""
        operation_id = str(uuid.uuid4())

        try:
            file_path = self.validate_path(path)

            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert content to bytes if needed
            if isinstance(content, str):
                content_bytes = content.encode('utf-8')
            else:
                content_bytes = content

            total_size = len(content_bytes)
            if total_size > MAX_FILE_SIZE:
                return {"error": f"Content too large (max {MAX_FILE_SIZE} bytes)", "path": path}

            await self.register_operation(operation_id, "write", file_path)

            start_time = time.time()
            bytes_written = 0
            hasher = self._create_hasher()

            # Use async I/O if available
            if HAS_AIOFILES:
                async with aiofiles.open(file_path, 'wb') as f:
                    for i in range(0, total_size, chunk_size):
                        chunk = content_bytes[i:i + chunk_size]
                        await f.write(chunk)
                        bytes_written += len(chunk)
                        if hasher:
                            hasher.update(chunk)

                        # Update progress
                        await self.update_operation_progress(operation_id, bytes_written, total_size,
                                                           (bytes_written / total_size) * 100)

                        if AUTO_CHUNK:
                            elapsed = time.time() - self.active_operations[operation_id]["start_time"]
                            chunk_size = self._auto_tune_chunk_size(bytes_written, elapsed, chunk_size)
            else:
                # Fallback to sync writing
                with open(file_path, 'wb') as f:
                    f.write(content_bytes)
                    bytes_written = total_size
                    if hasher:
                        hasher.update(content_bytes)

            checksum = hasher.hexdigest() if hasher else None
            elapsed_time = time.time() - start_time

            # Verify integrity if requested
            verification_result = None
            if verify_checksum and checksum:
                verification_result = await self.verify_file_integrity(file_path, checksum)

            await self.complete_operation(operation_id)
            await self.update_stats("write", bytes_written, elapsed_time)

            result = {
                "success": True,
                "path": path,
                "size": bytes_written,
                "operation_id": operation_id,
                "elapsed_time": elapsed_time
            }

            if checksum:
                result["checksum"] = checksum
            if verification_result:
                result["verification"] = verification_result

            return result

        except Exception as e:
            await self.fail_operation(operation_id, str(e))
            logger.error(f"Error writing file {path}: {e}")
            return {"error": str(e), "path": path}

    async def delete_file_async(self, path: str) -> Dict[str, Any]:
        """Delete file or directory"""
        try:
            file_path = self.validate_path(path)

            if not file_path.exists():
                return {"error": "File or directory not found", "path": path}

            if file_path.is_file():
                file_path.unlink()
                return {"success": True, "path": path, "type": "file"}
            elif file_path.is_dir():
                shutil.rmtree(file_path)
                return {"success": True, "path": path, "type": "directory"}
            else:
                return {"error": "Path is neither file nor directory", "path": path}

        except Exception as e:
            logger.error(f"Error deleting {path}: {e}")
            return {"error": str(e), "path": path}

    async def list_directory_async(self, path: str = "", pattern: str = None) -> Dict[str, Any]:
        """List directory contents with optional pattern matching"""
        try:
            dir_path = self.validate_path(path) if path else self.base_path

            if not dir_path.exists():
                return {"error": "Directory not found", "path": path}

            if not dir_path.is_dir():
                return {"error": "Path is not a directory", "path": path}

            items = []

            for item in dir_path.iterdir():
                try:
                    stat_info = item.stat()
                    item_info = {
                        "name": item.name,
                        "path": str(item.relative_to(self.base_path)),
                        "type": "directory" if item.is_dir() else "file",
                        "size": stat_info.st_size if item.is_file() else 0,
                        "modified": stat_info.st_mtime,
                        "created": stat_info.st_ctime,
                        "permissions": oct(stat_info.st_mode)[-3:]
                    }

                    # Apply pattern filter if specified
                    if pattern is None or fnmatch.fnmatch(item.name, pattern):
                        items.append(item_info)

                except (OSError, PermissionError) as e:
                    logger.warning(f"Could not access {item}: {e}")
                    continue

            # Sort by name
            items.sort(key=lambda x: (x["type"] == "file", x["name"].lower()))

            return {
                "entries": items,
                "path": path,
                "total": len(items)
            }

        except Exception as e:
            logger.error(f"Error listing directory {path}: {e}")
            return {"error": str(e), "path": path}

    async def create_directory_async(self, path: str) -> Dict[str, Any]:
        """Create directory with parent directories"""
        try:
            dir_path = self.validate_path(path)
            dir_path.mkdir(parents=True, exist_ok=True)

            return {"success": True, "path": path, "created": True}

        except Exception as e:
            logger.error(f"Error creating directory {path}: {e}")
            return {"error": str(e), "path": path}

    async def search_files_async(self, query: str, path: str = "",
                               file_pattern: str = "*", content_search: bool = False) -> Dict[str, Any]:
        """Search for files by name and optionally content"""
        try:
            search_path = self.validate_path(path) if path else self.base_path

            if not search_path.exists() or not search_path.is_dir():
                return {"error": "Search path not found or not a directory", "path": path}

            results = []
            query_lower = query.lower()

            # Search by filename
            for file_path in search_path.rglob(file_pattern):
                if file_path.is_file():
                    relative_path = str(file_path.relative_to(self.base_path))

                    # Check filename match
                    if query_lower in file_path.name.lower():
                        score = 1.0 if query_lower == file_path.name.lower() else 0.8
                        results.append({
                            "path": relative_path,
                            "name": file_path.name,
                            "score": score,
                            "match_type": "filename",
                            "size": file_path.stat().st_size,
                            "modified": file_path.stat().st_mtime
                        })

                    # Content search if requested
                    elif content_search and file_path.stat().st_size < 10 * 1024 * 1024:  # 10MB limit
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if query_lower in content.lower():
                                    # Calculate basic relevance score
                                    matches = content.lower().count(query_lower)
                                    score = min(0.7, matches / 10)  # Cap at 0.7 for content matches

                                    # Find snippet around first match
                                    match_pos = content.lower().find(query_lower)
                                    start = max(0, match_pos - 50)
                                    end = min(len(content), match_pos + len(query) + 50)
                                    snippet = content[start:end].strip()

                                    results.append({
                                        "path": relative_path,
                                        "name": file_path.name,
                                        "score": score,
                                        "match_type": "content",
                                        "snippet": snippet,
                                        "matches": matches,
                                        "size": file_path.stat().st_size,
                                        "modified": file_path.stat().st_mtime
                                    })
                        except (UnicodeDecodeError, PermissionError):
                            continue

            # Sort by score descending
            results.sort(key=lambda x: x["score"], reverse=True)

            return {
                "results": results[:50],  # Limit to top 50 results
                "query": query,
                "total_found": len(results),
                "search_path": str(search_path.relative_to(self.base_path)),
                "content_search": content_search
            }

        except Exception as e:
            logger.error(f"Error searching files: {e}")
            return {"error": str(e), "query": query}

    # =============================================================================
    # AI Features (Enhanced with fallbacks)
    # =============================================================================

    async def analyze_content_async(self, path: str, include_highlighting: bool = True) -> Dict[str, Any]:
        """Analyze file content with AI features"""
        try:
            file_path = self.validate_path(path)

            if not file_path.exists() or not file_path.is_file():
                return {"error": "File not found", "path": path}

            # Read file content
            read_result = await self.read_file_async(path)
            if "error" in read_result:
                return read_result

            content = read_result["content"]
            is_binary = read_result.get("is_binary", False)

            if is_binary:
                return {"error": "Cannot analyze binary file content", "path": path}

            # Basic analysis
            analysis = ContentAnalysis(
                file_path=path,
                content_type=mimetypes.guess_type(str(file_path))[0] or "text/plain",
                encoding="utf-8",
                size=len(content),
                line_count=content.count('\n') + 1,
                word_count=len(content.split()),
                char_count=len(content)
            )

            # Language detection and syntax highlighting
            if HAS_PYGMENTS and include_highlighting:
                try:
                    if file_path.suffix:
                        lexer = get_lexer_by_name(file_path.suffix[1:])
                    else:
                        lexer = guess_lexer(content)

                    analysis.language = lexer.name
                    analysis.syntax_highlighted = highlight(content, lexer, TerminalFormatter())
                except Exception as e:
                    logger.debug(f"Could not highlight {path}: {e}")

            # Calculate complexity score (simple heuristic)
            if analysis.language and analysis.language.lower() in ['python', 'javascript', 'java', 'c', 'cpp']:
                complexity_indicators = [
                    len(re.findall(r'\bif\b|\bfor\b|\bwhile\b|\btry\b|\bcatch\b', content, re.IGNORECASE)),
                    len(re.findall(r'\bclass\b|\bfunction\b|\bdef\b', content, re.IGNORECASE)),
                    content.count('{') + content.count('('),
                    len(re.findall(r'\band\b|\bor\b|\bnot\b|\&&|\|\|', content, re.IGNORECASE))
                ]
                analysis.complexity_score = sum(complexity_indicators) / max(analysis.line_count, 1)

            # Extract key terms (simple approach)
            words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', content)
            word_freq = {}
            for word in words:
                if len(word) > 3:  # Filter short words
                    word_freq[word.lower()] = word_freq.get(word.lower(), 0) + 1

            analysis.key_terms = sorted(word_freq.keys(), key=lambda x: word_freq[x], reverse=True)[:20]

            # Generate summary (basic approach)
            lines = content.split('\n')
            non_empty_lines = [line.strip() for line in lines if line.strip()]
            if non_empty_lines:
                analysis.summary = f"File with {len(non_empty_lines)} non-empty lines"
                if analysis.language:
                    analysis.summary += f" of {analysis.language} code"

            return analysis.dict()

        except Exception as e:
            logger.error(f"Error analyzing content for {path}: {e}")
            return {"error": str(e), "path": path}

    async def generate_embeddings_async(self, path: str, chunk_size: int = 1000) -> Dict[str, Any]:
        """Generate embeddings for file content"""
        if not self.embedding_model:
            return {"error": "Embedding model not available", "path": path}

        try:
            # Read file content
            read_result = await self.read_file_async(path)
            if "error" in read_result:
                return read_result

            content = read_result["content"]
            is_binary = read_result.get("is_binary", False)

            if is_binary:
                return {"error": "Cannot generate embeddings for binary file", "path": path}

            start_time = time.time()

            # Split content into chunks
            chunks = []
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size].strip()
                if chunk:
                    chunks.append(chunk)

            if not chunks:
                return {"error": "No content to embed", "path": path}

            # Generate embeddings
            embeddings = self.embedding_model.encode(chunks)

            # Average embeddings for the entire file
            if HAS_NUMPY:
                file_embedding = np.mean(embeddings, axis=0).tolist()
            else:
                # Fallback without numpy
                file_embedding = [sum(col)/len(col) for col in zip(*embeddings)]

            processing_time = time.time() - start_time

            # Store in vector database if available
            if HAS_SQLITE:
                await self._store_embeddings(path, file_embedding, chunks, embeddings.tolist())

            return EmbeddingResult(
                file_path=path,
                embeddings=file_embedding,
                model=DEFAULT_EMBEDDING_MODEL,
                chunk_count=len(chunks),
                processing_time=processing_time
            ).dict()

        except Exception as e:
            logger.error(f"Error generating embeddings for {path}: {e}")
            return {"error": str(e), "path": path}

    async def semantic_search_async(self, query: str, top_k: int = 10,
                                  similarity_threshold: float = 0.5) -> Dict[str, Any]:
        """Perform semantic search across indexed files"""
        if not self.embedding_model:
            return {"error": "Embedding model not available", "query": query}

        if not HAS_SQLITE:
            return {"error": "SQLite not available for vector search", "query": query}

        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])[0]

            # Search vector database
            results = []
            async with aiosqlite.connect(self.vector_db_path) as db:
                async with db.execute("""
                    SELECT file_path, embedding, content_hash FROM file_embeddings
                    ORDER BY created_at DESC
                """) as cursor:
                    async for row in cursor:
                        file_path, embedding_blob, content_hash = row

                        if embedding_blob:
                            try:
                                # Deserialize embedding
                                if HAS_NUMPY:
                                    file_embedding = np.frombuffer(embedding_blob, dtype=np.float32)
                                    similarity = cosine_similarity([query_embedding], [file_embedding])[0][0]
                                else:
                                    # Fallback similarity calculation for JSON-encoded embeddings
                                    file_embedding = json.loads(embedding_blob.decode())
                                    similarity = self._calculate_similarity(query_embedding, file_embedding)

                                if similarity >= similarity_threshold:
                                    results.append(SearchResult(
                                        path=file_path,
                                        score=float(similarity),
                                        metadata={"content_hash": content_hash}
                                    ))
                            except Exception as e:
                                logger.debug(f"Error processing embedding for {file_path}: {e}")
                                continue

            # Sort by similarity score and limit results
            results.sort(key=lambda x: x.score, reverse=True)
            results = results[:top_k]

            return {
                "results": [result.dict() for result in results],
                "total": len(results),
                "query": query,
                "top_k": top_k,
                "similarity_threshold": similarity_threshold
            }

        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return {"error": str(e), "query": query}

    async def find_similar_files_async(self, path: str, top_k: int = 5,
                                     similarity_threshold: float = 0.7) -> Dict[str, Any]:
        """Find files similar to the given file"""
        if not self.embedding_model:
            return {"error": "Embedding model not available", "path": path}

        try:
            # Generate embeddings for the target file if not exists
            embedding_result = await self.generate_embeddings_async(path)
            if "error" in embedding_result:
                return embedding_result

            target_embedding = embedding_result["embeddings"]
            if HAS_NUMPY:
                target_embedding = np.array(target_embedding)

            # Find similar files
            results = []
            if HAS_SQLITE:
                async with aiosqlite.connect(self.vector_db_path) as db:
                    async with db.execute("""
                        SELECT file_path, embedding FROM file_embeddings
                        WHERE file_path != ?
                    """, (path,)) as cursor:
                        async for row in cursor:
                            file_path, embedding_blob = row

                            if embedding_blob:
                                try:
                                    if HAS_NUMPY:
                                        file_embedding = np.frombuffer(embedding_blob, dtype=np.float32)
                                        similarity = cosine_similarity([target_embedding], [file_embedding])[0][0]
                                    else:
                                        file_embedding = list(embedding_blob)
                                        similarity = self._calculate_similarity(target_embedding, file_embedding)

                                    if similarity >= similarity_threshold:
                                        results.append(SearchResult(
                                            path=file_path,
                                            score=float(similarity)
                                        ))
                                except Exception as e:
                                    logger.debug(f"Error processing embedding for {file_path}: {e}")
                                    continue

            # Sort by similarity and limit results
            results.sort(key=lambda x: x.score, reverse=True)
            results = results[:top_k]

            return {
                "target_file": path,
                "similar_files": [result.dict() for result in results],
                "total": len(results),
                "similarity_threshold": similarity_threshold
            }

        except Exception as e:
            logger.error(f"Error finding similar files for {path}: {e}")
            return {"error": str(e), "path": path}

    def _calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity without numpy"""
        try:
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            magnitude1 = sum(a * a for a in vec1) ** 0.5
            magnitude2 = sum(b * b for b in vec2) ** 0.5

            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0

            return dot_product / (magnitude1 * magnitude2)
        except Exception:
            return 0.0

    async def _store_embeddings(self, file_path: str, file_embedding: List[float],
                              chunks: List[str], chunk_embeddings: List[List[float]]):
        """Store embeddings in vector database"""
        try:
            # Calculate content hash
            hasher = self._create_hasher()
            if hasher:
                hasher.update(''.join(chunks).encode())
                content_hash = hasher.hexdigest()
            else:
                content_hash = "unknown"

            async with aiosqlite.connect(self.vector_db_path) as db:
                # Store file embedding
                if HAS_NUMPY:
                    embedding_blob = np.array(file_embedding, dtype=np.float32).tobytes()
                else:
                    # Simple serialization for non-numpy case
                    embedding_blob = json.dumps(file_embedding).encode()

                await db.execute("""
                    INSERT OR REPLACE INTO file_embeddings
                    (file_path, content_hash, embedding, model, chunk_size, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    file_path,
                    content_hash,
                    embedding_blob,
                    DEFAULT_EMBEDDING_MODEL,
                    len(chunks)
                ))

                # Get file ID
                cursor = await db.execute("SELECT last_insert_rowid()")
                file_id = (await cursor.fetchone())[0]

                # Store chunk embeddings
                for i, (chunk, embedding) in enumerate(zip(chunks, chunk_embeddings)):
                    if HAS_NUMPY:
                        chunk_blob = np.array(embedding, dtype=np.float32).tobytes()
                    else:
                        chunk_blob = json.dumps(embedding).encode()

                    await db.execute("""
                        INSERT INTO content_chunks (file_id, chunk_index, content, embedding)
                        VALUES (?, ?, ?, ?)
                    """, (
                        file_id,
                        i,
                        chunk,
                        chunk_blob
                    ))

                await db.commit()

        except Exception as e:
            logger.error(f"Error storing embeddings for {file_path}: {e}")

    # =============================================================================
    # Progress and Operation Tracking
    # =============================================================================

    async def register_operation(self, operation_id: str, operation_type: str, file_path: Path):
        """Register a new operation for tracking"""
        self.active_operations[operation_id] = {
            "type": operation_type,
            "file_path": str(file_path),
            "start_time": time.time(),
            "status": "starting",
            "bytes_processed": 0,
            "total_bytes": 0,
            "percentage": 0.0
        }

    async def update_operation_progress(self, operation_id: str, bytes_processed: int,
                                      total_bytes: int, percentage: float):
        """Update operation progress"""
        if operation_id not in self.active_operations:
            return

        operation = self.active_operations[operation_id]
        operation.update({
            "bytes_processed": bytes_processed,
            "total_bytes": total_bytes,
            "percentage": percentage,
            "status": "in_progress"
        })

        # Calculate speed
        elapsed = time.time() - operation["start_time"]
        if elapsed > 0:
            speed_mbps = (bytes_processed / elapsed) / (1024 * 1024)
            eta_seconds = (total_bytes - bytes_processed) / (bytes_processed / elapsed) if bytes_processed > 0 else None
        else:
            speed_mbps = 0
            eta_seconds = None

        progress = StreamProgress(
            operation_id=operation_id,
            bytes_processed=bytes_processed,
            total_bytes=total_bytes,
            percentage=percentage,
            speed_mbps=speed_mbps,
            eta_seconds=eta_seconds
        )

        # Broadcast to WebSocket clients
        await self.broadcast_progress(operation_id, progress)

    async def complete_operation(self, operation_id: str):
        """Mark operation as completed"""
        if operation_id in self.active_operations:
            self.active_operations[operation_id]["status"] = "completed"
            asyncio.create_task(self.cleanup_operation(operation_id, delay=30.0))

    async def fail_operation(self, operation_id: str, error: str):
        """Mark operation as failed"""
        if operation_id in self.active_operations:
            self.active_operations[operation_id]["status"] = "failed"
            self.active_operations[operation_id]["error"] = error
            asyncio.create_task(self.cleanup_operation(operation_id, delay=60.0))

    async def cleanup_operation(self, operation_id: str, delay: float = 0.0):
        """Remove operation from tracking after delay"""
        if delay > 0:
            await asyncio.sleep(delay)

        if operation_id in self.active_operations:
            del self.active_operations[operation_id]

    async def update_stats(self, operation_type: str, bytes_processed: int, elapsed_time: float):
        """Update server statistics"""
        if operation_type not in self.stats["operations"]:
            self.stats["operations"][operation_type] = {
                "count": 0,
                "total_bytes": 0,
                "total_time": 0.0,
                "average_speed_mbps": 0.0
            }

        op_stats = self.stats["operations"][operation_type]
        op_stats["count"] += 1
        op_stats["total_bytes"] += bytes_processed
        op_stats["total_time"] += elapsed_time

        if elapsed_time > 0:
            op_stats["average_speed_mbps"] = (op_stats["total_bytes"] / op_stats["total_time"]) / (1024 * 1024)

        self.stats["total_bytes_processed"] += bytes_processed
        self.stats["total_operations"] += 1

    # =============================================================================
    # WebSocket Support
    # =============================================================================

    async def progress_websocket(self, websocket: WebSocket, operation_id: str):
        """WebSocket endpoint for operation progress updates"""
        await websocket.accept()

        if "progress" not in self.connected_clients:
            self.connected_clients["progress"] = []

        self.connected_clients["progress"].append(websocket)

        try:
            while True:
                # Send current operation status if exists
                if operation_id in self.active_operations:
                    operation = self.active_operations[operation_id]
                    await websocket.send_json({
                        "operation_id": operation_id,
                        "status": operation["status"],
                        "bytes_processed": operation["bytes_processed"],
                        "total_bytes": operation["total_bytes"],
                        "percentage": operation["percentage"]
                    })

                await asyncio.sleep(1)  # Update every second

        except WebSocketDisconnect:
            pass
        finally:
            if websocket in self.connected_clients["progress"]:
                self.connected_clients["progress"].remove(websocket)

    async def broadcast_progress(self, operation_id: str, progress_data: StreamProgress):
        """Broadcast progress to interested WebSocket clients"""
        if "progress" in self.connected_clients:
            disconnected_clients = []

            for client in self.connected_clients["progress"]:
                try:
                    await client.send_json(progress_data.dict())
                except Exception as e:
                    logger.error(f"Error sending progress to client: {e}")
                    disconnected_clients.append(client)

            # Remove disconnected clients
            for client in disconnected_clients:
                self.connected_clients["progress"].remove(client)

    async def broadcast_fs_event(self, event: dict):
        """Fan-out FS events to SSE queues and WS notification clients."""
        # SSE queues
        for q in list(self.fs_watchers):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass

        # WebSocket notifications
        if "notifications" in self.connected_clients:
            dead = []
            for ws in self.connected_clients["notifications"]:
                try:
                    await ws.send_json({"type": "fs_event", "data": event})
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.connected_clients["notifications"].remove(ws)

    async def fs_watch_sse(self):
        """`/fs/watch` – Event-Stream of file changes."""
        q: asyncio.Queue = asyncio.Queue(maxsize=500)
        self.fs_watchers.add(q)

        async def gen():
            try:
                while True:
                    data = await q.get()
                    yield f"data: {json.dumps(data)}\\n\\n"
            finally:
                self.fs_watchers.discard(q)

        return StreamingResponse(gen(), media_type="text/event-stream")

    async def events_websocket(self, websocket: WebSocket):
        """WebSocket endpoint for file system events"""
        await websocket.accept()

        if "notifications" not in self.connected_clients:
            self.connected_clients["notifications"] = []

        self.connected_clients["notifications"].append(websocket)

        try:
            # Send initial status
            await websocket.send_json({
                "type": "connection",
                "status": "connected",
                "timestamp": datetime.now().isoformat()
            })

            # Keep connection alive
            while True:
                await asyncio.sleep(30)  # Ping every 30 seconds
                await websocket.send_json({
                    "type": "ping",
                    "timestamp": datetime.now().isoformat()
                })

        except WebSocketDisconnect:
            pass
        finally:
            if websocket in self.connected_clients["notifications"]:
                self.connected_clients["notifications"].remove(websocket)

    # =============================================================================
    # MCP JSON-RPC Handler
    # =============================================================================

    async def rpc_handler(self, request: Request):
        """Main JSON-RPC endpoint handler"""
        try:
            body = await request.json()
            response = await self.handle_rpc(body)
            return response
        except Exception as e:
            logger.error(f"RPC handler error: {e}")
            return {
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
                "id": body.get("id", 0) if 'body' in locals() else 0
            }

    async def handle_rpc(self, request_body: dict):
        """Enhanced JSON-RPC handler with all methods"""
        method = request_body.get("method")
        params = request_body.get("params", {})
        request_id = request_body.get("id", 0)

        try:
            # Basic file operations
            if method == "fs.read":
                result = await self.read_file_async(
                    params.get("path"),
                    params.get("chunk_size", DEFAULT_CHUNK_SIZE)
                )
            elif method == "fs.write":
                result = await self.write_file_async(
                    params.get("path"),
                    params.get("content"),
                    params.get("chunk_size", DEFAULT_CHUNK_SIZE),
                    params.get("verify_checksum", True)
                )
            elif method == "fs.delete":
                result = await self.delete_file_async(params.get("path"))
            elif method == "fs.list":
                result = await self.list_directory_async(
                    params.get("path", ""),
                    params.get("pattern")
                )
            elif method == "fs.mkdir":
                result = await self.create_directory_async(params.get("path"))
            elif method == "fs.search":
                result = await self.search_files_async(
                    params.get("query"),
                    params.get("path", ""),
                    params.get("file_pattern", "*"),
                    params.get("content_search", False)
                )

            # Enhanced operations
            elif method == "fs.metadata":
                result = await self.get_file_metadata_async(params.get("path"))
            elif method == "fs.verify":
                file_path = self.validate_path(params.get("path"))
                result = await self.verify_file_integrity(file_path, params.get("checksum"))
            elif method == "fs.stats":
                result = await self.get_stats()

            # AI operations
            elif method == "fs.analyze":
                result = await self.analyze_content_async(
                    params.get("path"),
                    params.get("include_highlighting", True)
                )
            elif method == "fs.embed":
                result = await self.generate_embeddings_async(
                    params.get("path"),
                    params.get("chunk_size", 1000)
                )
            elif method == "fs.search.semantic":
                result = await self.semantic_search_async(
                    params.get("query"),
                    params.get("top_k", 10),
                    params.get("similarity_threshold", 0.5)
                )
            elif method == "fs.search.similar":
                result = await self.find_similar_files_async(
                    params.get("path"),
                    params.get("top_k", 5),
                    params.get("similarity_threshold", 0.7)
                )

            # Version control operations
            elif method == "fs.version.snapshot":
                result = await self.create_snapshot_async(
                    params.get("path"),
                    params.get("description")
                )
            elif method == "fs.version.list":
                result = await self.list_versions_async(
                    params.get("path"),
                    params.get("limit", 10)
                )
            elif method == "fs.version.diff":
                result = await self.get_diff_async(
                    params.get("path"),
                    params.get("version1"),
                    params.get("version2", "current")
                )
            elif method == "fs.version.restore":
                result = await self.restore_version_async(
                    params.get("path"),
                    params.get("version_id")
                )
            elif method == "fs.version.cleanup":
                result = await self.cleanup_old_versions_async(
                    params.get("path"),
                    params.get("keep_count", 5)
                )
            elif method == "fs.batch":
                # Execute JSON‑RPC batch operations
                batch_ops    = params.get("operations", [])
                parallel     = params.get("parallel", False)
                stop_on_err  = params.get("stop_on_error", True)
                batch_model  = BatchOperation(
                    operations=batch_ops,
                    parallel=parallel,
                    stop_on_error=stop_on_err,
                )
                result = await self.batch_operations(batch_model)

            else:
                result = {"error": f"Unknown method: {method}"}

            return {"result": result, "id": request_id}

        except Exception as e:
            logger.error(f"RPC error for method {method}: {e}")
            return {
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
                "id": request_id
            }

    # =============================================================================
    # Helper Methods
    # =============================================================================

    def _create_hasher(self):
        """Create a hasher instance based on configuration"""
        if HASH_ALGO == "xxhash" and HAS_XXHASH:
            return xxhash.xxh64()
        elif HASH_ALGO == "blake3" and HAS_BLAKE3:
            return blake3.blake3()
        elif HASH_ALGO == "sha256":
            return hashlib.sha256()
        else:
            # Fallback to MD5 for compatibility
            return hashlib.md5()

    def _auto_tune_chunk_size(self, bytes_processed: int, elapsed: float, current_size: int) -> int:
        """Auto-tune chunk size based on performance"""
        if not AUTO_CHUNK or elapsed <= 0:
            return current_size

        # Calculate current throughput
        throughput = bytes_processed / elapsed  # bytes per second

        # Target chunk size for optimal performance
        target = int(throughput * CHUNK_TARGET_TIME)

        # Keep within reasonable bounds
        return max(64 * 1024, min(target, LARGE_FILE_CHUNK_SIZE))

    def validate_path(self, path_str: str) -> Path:
        """Enhanced path validation with security"""
        try:
            if not path_str:
                return self.base_path

            # Convert to Path object
            if path_str.startswith('/'):
                # Absolute path - make it relative to base_path
                path_str = path_str.lstrip('/')

            path = self.base_path / path_str

            # Resolve and check it's within base_path
            resolved_path = path.resolve()

            # Security check: ensure path is within base_path
            try:
                resolved_path.relative_to(self.base_path.resolve())
            except ValueError:
                raise ValueError(f"Path outside allowed directory: {path_str}")

            return resolved_path

        except Exception as e:
            logger.error(f"Path validation failed for '{path_str}': {e}")
            raise ValueError(f"Invalid path: {path_str}")

    async def get_file_metadata_async(self, path: str) -> Dict[str, Any]:
        """Get comprehensive file metadata"""
        try:
            file_path = self.validate_path(path)
            if not file_path.exists():
                return {"error": "File not found", "path": path}

            stat = file_path.stat()

            # Calculate checksum for small files only
            checksum = None
            if file_path.is_file() and stat.st_size < 10 * 1024 * 1024:  # 10MB limit
                hasher = self._create_hasher()
                if hasher:
                    if HAS_AIOFILES:
                        async with aiofiles.open(file_path, 'rb') as f:
                            while True:
                                chunk = await f.read(DEFAULT_CHUNK_SIZE)
                                if not chunk:
                                    break
                                hasher.update(chunk)
                    else:
                        with open(file_path, 'rb') as f:
                            while True:
                                chunk = f.read(DEFAULT_CHUNK_SIZE)
                                if not chunk:
                                    break
                                hasher.update(chunk)
                    checksum = hasher.hexdigest()

            # Detect content type
            content_type, encoding = mimetypes.guess_type(str(file_path))

            return FileMetadata(
                path=path,
                size=stat.st_size,
                modified=stat.st_mtime,
                created=stat.st_ctime,
                checksum=checksum,
                content_type=content_type,
                encoding=encoding,
                permissions=oct(stat.st_mode)[-3:]
            ).dict()

        except Exception as e:
            logger.error(f"Error getting metadata for {path}: {e}")
            return {"error": str(e), "path": path}

    async def verify_file_integrity(self, file_path: Path, expected_checksum: str) -> Dict[str, Any]:
        """Verify file integrity using checksum"""
        try:
            if not file_path.exists():
                return {"error": "File not found", "path": str(file_path)}

            hasher = self._create_hasher()
            if not hasher:
                return {"error": "Checksum verification not available", "path": str(file_path)}

            if HAS_AIOFILES:
                async with aiofiles.open(file_path, 'rb') as f:
                    while True:
                        chunk = await f.read(DEFAULT_CHUNK_SIZE)
                        if not chunk:
                            break
                        hasher.update(chunk)
            else:
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(DEFAULT_CHUNK_SIZE)
                        if not chunk:
                            break
                        hasher.update(chunk)

            actual_checksum = hasher.hexdigest()
            is_valid = actual_checksum == expected_checksum

            return {
                "file_path": str(file_path),
                "expected_checksum": expected_checksum,
                "actual_checksum": actual_checksum,
                "is_valid": is_valid
            }

        except Exception as e:
            logger.error(f"Error verifying integrity for {file_path}: {e}")
            return {"error": str(e), "path": str(file_path)}
    # =============================================================================
    # Streaming Endpoints
    # =============================================================================

    async def upload_stream(self, file: UploadFile = File(...),
                           chunk_size: int = DEFAULT_CHUNK_SIZE,
                           verify_checksum: bool = True):
        """Streaming file upload endpoint"""
        operation_id = str(uuid.uuid4())

        try:
            # Generate safe filename
            safe_filename = file.filename.replace('/', '_').replace('\\', '_')
            file_path = self.temp_path / safe_filename

            await self.register_operation(operation_id, "upload", file_path)

            bytes_written = 0
            hasher = self._create_hasher()

            if HAS_AIOFILES:
                async with aiofiles.open(file_path, 'wb') as f:
                    while True:
                        chunk = await file.read(chunk_size)
                        if not chunk:
                            break

                        await f.write(chunk)
                        bytes_written += len(chunk)
                        if hasher:
                            hasher.update(chunk)

                        # Update progress (we don't know total size for uploads)
                        await self.update_operation_progress(operation_id, bytes_written, bytes_written, 100)
            else:
                # Fallback to sync writing
                with open(file_path, 'wb') as f:
                    while True:
                        chunk = await file.read(chunk_size)
                        if not chunk:
                            break

                        f.write(chunk)
                        bytes_written += len(chunk)
                        if hasher:
                            hasher.update(chunk)

            checksum = hasher.hexdigest() if hasher else None
            await self.complete_operation(operation_id)

            result = {
                "success": True,
                "operation_id": operation_id,
                "filename": safe_filename,
                "path": str(file_path.relative_to(self.base_path)),
                "size": bytes_written
            }

            if checksum:
                result["checksum"] = checksum

            return result

        except Exception as e:
            await self.fail_operation(operation_id, str(e))
            raise HTTPException(status_code=500, detail=str(e))

    async def download_stream(self, path: str, chunk_size: int = DEFAULT_CHUNK_SIZE):
        """Streaming file download endpoint"""
        try:
            file_path = self.validate_path(path)
            if not file_path.exists() or not file_path.is_file():
                raise HTTPException(status_code=404, detail="File not found")

            if HAS_AIOFILES:
                async def stream_file():
                    async with aiofiles.open(file_path, 'rb') as f:
                        while True:
                            chunk = await f.read(chunk_size)
                            if not chunk:
                                break
                            yield chunk
            else:
                def stream_file():
                    with open(file_path, 'rb') as f:
                        while True:
                            chunk = f.read(chunk_size)
                            if not chunk:
                                break
                            yield chunk

            return StreamingResponse(
                stream_file(),
                media_type='application/octet-stream',
                headers={
                    "Content-Disposition": f"attachment; filename={file_path.name}",
                    "Content-Length": str(file_path.stat().st_size)
                }
            )

        except Exception as e:
            logger.error(f"Error streaming download for {path}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_file_metadata(self, path: str):
        """HTTP endpoint for file metadata"""
        return await self.get_file_metadata_async(path)

    async def batch_operations(self, batch: BatchOperation):
        """Execute batch file operations"""
        results = []

        for operation in batch.operations:
            try:
                method = operation.get("method")
                params = operation.get("params", {})

                if method == "fs.read":
                    result = await self.read_file_async(params.get("path"))
                elif method == "fs.write":
                    result = await self.write_file_async(params.get("path"), params.get("content"))
                elif method == "fs.delete":
                    result = await self.delete_file_async(params.get("path"))
                elif method == "fs.mkdir":
                    result = await self.create_directory_async(params.get("path"))
                else:
                    result = {"error": f"Unknown batch method: {method}"}

                results.append({"operation": operation, "result": result})

                # Stop on error if configured
                if batch.stop_on_error and "error" in result:
                    break

            except Exception as e:
                error_result = {"error": str(e)}
                results.append({"operation": operation, "result": error_result})

                if batch.stop_on_error:
                    break

        return {"results": results, "total": len(results)}

    # ========================================
    # VERSION CONTROL SYSTEM
    # ========================================

    async def create_snapshot_async(self, path: str, description: str = None) -> Dict[str, Any]:
        """Create a snapshot/version of a file"""
        try:
            file_path = self.validate_path(path)

            if not file_path.exists() or not file_path.is_file():
                return {"error": "File not found or is not a regular file", "path": path}

            # Generate unique version ID
            version_id = f"{uuid.uuid4().hex[:12]}_{int(time.time())}"

            # Read file content
            if HAS_AIOFILES:
                async with aiofiles.open(file_path, 'rb') as f:
                    content = await f.read()
            else:
                with open(file_path, 'rb') as f:
                    content = f.read()

            # Calculate hash
            content_hash = None
            hasher = self._create_hasher()
            if hasher:
                hasher.update(content)
                content_hash = hasher.hexdigest()

            # Get file metadata
            stat = file_path.stat()
            metadata = {
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "created": stat.st_ctime,
                "permissions": oct(stat.st_mode)[-3:]
            }

            # Store version in database
            async with aiosqlite.connect(self.vector_db_path) as db:
                await db.execute("""
                    INSERT INTO file_versions
                    (file_path, version_id, description, content, content_hash, metadata, size)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(file_path.relative_to(self.base_path)),
                    version_id,
                    description or f"Snapshot created at {datetime.now().isoformat()}",
                    content,
                    content_hash,
                    json.dumps(metadata),
                    stat.st_size
                ))

                await db.commit()

            # Cleanup old versions if needed
            await self._cleanup_old_versions(path, MAX_VERSIONS_PER_FILE)

            logger.info(f"Created snapshot {version_id} for {path}")
            return {
                "success": True,
                "version_id": version_id,
                "path": path,
                "content_hash": content_hash,
                "size": stat.st_size,
                "description": description
            }

        except Exception as e:
            logger.error(f"Error creating snapshot for {path}: {e}")
            return {"error": str(e), "path": path}

    async def list_versions_async(self, path: str, limit: int = 10) -> Dict[str, Any]:
        """List all versions of a file"""
        try:
            file_path = self.validate_path(path)
            relative_path = str(file_path.relative_to(self.base_path))

            async with aiosqlite.connect(self.vector_db_path) as db:
                cursor = await db.execute("""
                    SELECT version_id, description, content_hash, size, created_at, created_by
                    FROM file_versions
                    WHERE file_path = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (relative_path, limit))

                rows = await cursor.fetchall()

            versions = []
            for row in rows:
                versions.append({
                    "version_id": row[0],
                    "description": row[1],
                    "content_hash": row[2],
                    "size": row[3],
                    "created_at": row[4],
                    "created_by": row[5]
                })

            return {
                "success": True,
                "path": path,
                "versions": versions,
                "total": len(versions)
            }

        except Exception as e:
            logger.error(f"Error listing versions for {path}: {e}")
            return {"error": str(e), "path": path}

    async def get_diff_async(self, path: str, version1: str, version2: str = "current") -> Dict[str, Any]:
        """Get diff between two versions of a file"""
        try:
            file_path = self.validate_path(path)
            relative_path = str(file_path.relative_to(self.base_path))

            # Get version1 content
            async with aiosqlite.connect(self.vector_db_path) as db:
                cursor = await db.execute("""
                    SELECT content FROM file_versions
                    WHERE file_path = ? AND version_id = ?
                """, (relative_path, version1))

                row = await cursor.fetchone()
                if not row:
                    return {"error": f"Version {version1} not found", "path": path}

                content1 = row[0]

            # Get version2 content (current file or another version)
            if version2 == "current":
                if not file_path.exists():
                    return {"error": "Current file not found", "path": path}

                if HAS_AIOFILES:
                    async with aiofiles.open(file_path, 'rb') as f:
                        content2 = await f.read()
                else:
                    with open(file_path, 'rb') as f:
                        content2 = f.read()
            else:
                async with aiosqlite.connect(self.vector_db_path) as db:
                    cursor = await db.execute("""
                        SELECT content FROM file_versions
                        WHERE file_path = ? AND version_id = ?
                    """, (relative_path, version2))

                    row = await cursor.fetchone()
                    if not row:
                        return {"error": f"Version {version2} not found", "path": path}

                    content2 = row[0]

            # Check if files are binary
            def is_binary(content):
                return b'\x00' in content[:8192]  # Check first 8KB for null bytes

            if is_binary(content1) or is_binary(content2):
                # Binary diff - just compare hashes
                hasher1 = self._create_hasher()
                hasher2 = self._create_hasher()

                if hasher1 and hasher2:
                    hasher1.update(content1)
                    hasher2.update(content2)
                    hash1 = hasher1.hexdigest()
                    hash2 = hasher2.hexdigest()
                else:
                    import hashlib
                    hash1 = hashlib.md5(content1).hexdigest()
                    hash2 = hashlib.md5(content2).hexdigest()

                return {
                    "success": True,
                    "path": path,
                    "version1": version1,
                    "version2": version2,
                    "diff_type": "binary",
                    "different": hash1 != hash2,
                    "size1": len(content1),
                    "size2": len(content2),
                    "hash1": hash1,
                    "hash2": hash2
                }

            # Text diff
            try:
                text1 = content1.decode('utf-8')
                text2 = content2.decode('utf-8')
            except UnicodeDecodeError:
                return {"error": "Unable to decode file content as text", "path": path}

            # Simple line-by-line diff
            lines1 = text1.splitlines(keepends=True)
            lines2 = text2.splitlines(keepends=True)

            import difflib
            diff_lines = list(difflib.unified_diff(
                lines1, lines2,
                fromfile=f"{path}@{version1}",
                tofile=f"{path}@{version2}",
                lineterm=""
            ))

            diff_text = ''.join(diff_lines)
            changed_lines = len([line for line in diff_lines if line.startswith(('+', '-')) and not line.startswith(('+++', '---'))])

            return {
                "success": True,
                "path": path,
                "version1": version1,
                "version2": version2,
                "diff_type": "text",
                "diff_text": diff_text,
                "changed_lines": changed_lines,
                "total_lines1": len(lines1),
                "total_lines2": len(lines2)
            }

        except Exception as e:
            logger.error(f"Error getting diff for {path}: {e}")
            return {"error": str(e), "path": path}

    async def restore_version_async(self, path: str, version_id: str) -> Dict[str, Any]:
        """Restore a file to a specific version"""
        try:
            file_path = self.validate_path(path)
            relative_path = str(file_path.relative_to(self.base_path))

            # Get version content
            async with aiosqlite.connect(self.vector_db_path) as db:
                cursor = await db.execute("""
                    SELECT content, content_hash, size, description FROM file_versions
                    WHERE file_path = ? AND version_id = ?
                """, (relative_path, version_id))

                row = await cursor.fetchone()
                if not row:
                    return {"error": f"Version {version_id} not found", "path": path}

                content, content_hash, size, description = row

            # Create current file backup before restore
            if file_path.exists():
                backup_result = await self.create_snapshot_async(path, f"Backup before restoring to {version_id}")
                if "error" in backup_result:
                    logger.warning(f"Failed to create backup before restore: {backup_result['error']}")

            # Write restored content
            file_path.parent.mkdir(parents=True, exist_ok=True)

            if HAS_AIOFILES:
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(content)
            else:
                with open(file_path, 'wb') as f:
                    f.write(content)

            # Verify restoration
            verification_result = await self._verify_file_integrity(content, file_path)

            logger.info(f"Restored {path} to version {version_id}")
            return {
                "success": True,
                "path": path,
                "version_id": version_id,
                "size": size,
                "description": description,
                "verification": verification_result
            }

        except Exception as e:
            logger.error(f"Error restoring {path} to version {version_id}: {e}")
            return {"error": str(e), "path": path}

    async def cleanup_old_versions_async(self, path: str, keep_count: int = 5) -> Dict[str, Any]:
        """Clean up old versions of a file, keeping only the most recent ones"""
        try:
            file_path = self.validate_path(path)
            relative_path = str(file_path.relative_to(self.base_path))

            return await self._cleanup_old_versions(relative_path, keep_count)

        except Exception as e:
            logger.error(f"Error cleaning up versions for {path}: {e}")
            return {"error": str(e), "path": path}

    async def _cleanup_old_versions(self, relative_path: str, keep_count: int) -> Dict[str, Any]:
        """Internal method to cleanup old versions"""
        try:
            async with aiosqlite.connect(self.vector_db_path) as db:
                # Get count of existing versions
                cursor = await db.execute("""
                    SELECT COUNT(*) FROM file_versions WHERE file_path = ?
                """, (relative_path,))

                total_count = (await cursor.fetchone())[0]

                if total_count <= keep_count:
                    return {
                        "success": True,
                        "path": relative_path,
                        "total_versions": total_count,
                        "deleted_count": 0,
                        "message": "No cleanup needed"
                    }

                # Delete old versions
                delete_count = total_count - keep_count
                await db.execute("""
                    DELETE FROM file_versions
                    WHERE file_path = ? AND id NOT IN (
                        SELECT id FROM file_versions
                        WHERE file_path = ?
                        ORDER BY created_at DESC
                        LIMIT ?
                    )
                """, (relative_path, relative_path, keep_count))

                await db.commit()

                logger.info(f"Cleaned up {delete_count} old versions for {relative_path}")
                return {
                    "success": True,
                    "path": relative_path,
                    "total_versions": total_count,
                    "deleted_count": delete_count,
                    "remaining_count": keep_count
                }

        except Exception as e:
            logger.error(f"Error in cleanup for {relative_path}: {e}")
            return {"error": str(e), "path": relative_path}

    async def _verify_file_integrity(self, content: bytes, file_path: Path) -> Dict[str, Any]:
        """Verify file integrity by comparing content"""
        try:
            if HAS_AIOFILES:
                async with aiofiles.open(file_path, 'rb') as f:
                    file_content = await f.read()
            else:
                with open(file_path, 'rb') as f:
                    file_content = f.read()

            return {
                "verified": content == file_content,
                "expected_size": len(content),
                "actual_size": len(file_content)
            }

        except Exception as e:
            return {"verified": False, "error": str(e)}

    # Version Control HTTP Endpoints
    async def create_snapshot_endpoint(self, request: Request):
        """HTTP endpoint for creating snapshots"""
        data = await request.json()
        path = data.get("path")
        description = data.get("description")

        if not path:
            raise HTTPException(status_code=400, detail="Path is required")

        result = await self.create_snapshot_async(path, description)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    async def list_versions_endpoint(self, path: str, limit: int = 10):
        """HTTP endpoint for listing versions"""
        result = await self.list_versions_async(path, limit)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result

    async def get_diff_endpoint(self, path: str, version1: str, version2: str = "current"):
        """HTTP endpoint for getting diffs"""
        result = await self.get_diff_async(path, version1, version2)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result

    async def restore_version_endpoint(self, request: Request):
        """HTTP endpoint for restoring versions"""
        data = await request.json()
        path = data.get("path")
        version_id = data.get("version_id")

        if not path or not version_id:
            raise HTTPException(status_code=400, detail="Path and version_id are required")

        result = await self.restore_version_async(path, version_id)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    async def cleanup_versions_endpoint(self, path: str, keep_count: int = 5):
        """HTTP endpoint for cleaning up versions"""
        result = await self.cleanup_old_versions_async(path, keep_count)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result


class FilesystemEventHandler(FileSystemEventHandler):
    """File system event handler for real-time notifications"""

    def __init__(self, server: UnifiedFilesystemServer):
        self.server = server
        super().__init__()

    async def notify_clients(self, event_type: str, file_path: str, extra_data: dict = None):
        """Send event notification to WebSocket clients"""
        event_data = {
            "type": event_type,
            "path": file_path,
            "timestamp": datetime.now().isoformat()
        }

        if extra_data:
            event_data.update(extra_data)

        # Send to all connected event clients
        if "notifications" in self.server.connected_clients:
            disconnected_clients = []

            for client in self.server.connected_clients["notifications"]:
                try:
                    await client.send_json(event_data)
                except Exception as e:
                    logger.error(f"Error sending event to client: {e}")
                    disconnected_clients.append(client)

            # Remove disconnected clients
            for client in disconnected_clients:
                self.server.connected_clients["notifications"].remove(client)

    def on_created(self, event):
        if not event.is_directory:
            asyncio.create_task(
                self.notify_clients("file_created", event.src_path)
            )

    def on_modified(self, event):
        if not event.is_directory:
            asyncio.create_task(
                self.notify_clients("file_modified", event.src_path)
            )

    def on_deleted(self, event):
        if not event.is_directory:
            asyncio.create_task(
                self.notify_clients("file_deleted", event.src_path)
            )

    def on_moved(self, event):
        if not event.is_directory:
            asyncio.create_task(
                self.notify_clients("file_moved", event.dest_path, {
                    "old_path": event.src_path
                })
            )


# Legacy compatibility class
class MCPFilesystemServer(UnifiedFilesystemServer):
    """Legacy compatibility class - redirects to UnifiedFilesystemServer"""
    pass


# Standalone entry point
async def main():
    """Run the unified server directly"""
    logger.info("Starting Unified MCP Filesystem Server...")
    server = UnifiedFilesystemServer()

    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal...")
        await server.stop()
        logger.info("Server stopped successfully")

if __name__ == "__main__":
    asyncio.run(main())

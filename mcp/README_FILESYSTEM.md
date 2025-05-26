# Unified MCP Filesystem Server

A comprehensive, production-ready filesystem server implementing the Model Context Protocol (MCP) with advanced features including AI-powered content analysis, semantic search, version control, and real-time file monitoring.

## 🌟 Features

### Core Functionality
- **Complete MCP Protocol Support**: Full JSON-RPC implementation for filesystem operations
- **Async I/O**: High-performance async file operations with `aiofiles`
- **Chunked Streaming**: Efficient handling of large files with adaptive chunk sizing
- **Multiple Integrity Checking**: Support for xxHash, BLAKE3, SHA256, and MD5 checksums
- **Progress Tracking**: Real-time progress updates for long-running operations
- **Error Handling**: Comprehensive error handling with graceful fallbacks

### Advanced Features
- **AI Content Analysis**: Automatic language detection, syntax highlighting, complexity scoring
- **Semantic Search**: Vector-based content search using sentence transformers
- **File Similarity**: Find files with similar content using embeddings
- **Version Control**: Built-in file versioning with diff support
- **Real-time Monitoring**: File system event notifications via WebSockets/SSE
- **Batch Operations**: Execute multiple file operations in parallel or sequence

### API Endpoints
- **REST API**: Standard HTTP endpoints for all operations
- **JSON-RPC**: MCP-compliant RPC interface at `/rpc`
- **WebSocket**: Real-time event streaming at `/ws/events`
- **Server-Sent Events**: File system monitoring at `/fs/watch`

## 🚀 Quick Start

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the server:
```bash
python start_filesystem_server.py
```

3. Or run with custom options:
```bash
python start_filesystem_server.py --port 8080 --base-path /path/to/files --verbose
```

### Testing

Run the comprehensive test suite:
```bash
python test_filesystem_server.py
```

## 📡 API Reference

### Health Check
```bash
curl http://localhost:8001/health
```

### File Operations (JSON-RPC)

#### Read File
```bash
curl -X POST http://localhost:8001/rpc \\
  -H "Content-Type: application/json" \\
  -d '{
    "method": "fs.read",
    "params": {"path": "example.txt"},
    "id": 1
  }'
```

#### Write File
```bash
curl -X POST http://localhost:8001/rpc \\
  -H "Content-Type: application/json" \\
  -d '{
    "method": "fs.write",
    "params": {
      "path": "example.txt",
      "content": "Hello, World!"
    },
    "id": 2
  }'
```

#### Search Files
```bash
curl -X POST http://localhost:8001/rpc \\
  -H "Content-Type: application/json" \\
  -d '{
    "method": "fs.search",
    "params": {
      "query": "hello",
      "content_search": true
    },
    "id": 3
  }'
```

### AI Features

#### Content Analysis
```bash
curl -X POST http://localhost:8001/rpc \\
  -H "Content-Type: application/json" \\
  -d '{
    "method": "fs.analyze",
    "params": {"path": "script.py"},
    "id": 4
  }'
```

#### Generate Embeddings
```bash
curl -X POST http://localhost:8001/rpc \\
  -H "Content-Type: application/json" \\
  -d '{
    "method": "fs.embed",
    "params": {"path": "document.txt"},
    "id": 5
  }'
```

#### Semantic Search
```bash
curl -X POST http://localhost:8001/rpc \\
  -H "Content-Type: application/json" \\
  -d '{
    "method": "fs.search.semantic",
    "params": {
      "query": "machine learning algorithms",
      "top_k": 5
    },
    "id": 6
  }'
```

### Version Control

#### Create Snapshot
```bash
curl -X POST http://localhost:8001/rpc \\
  -H "Content-Type: application/json" \\
  -d '{
    "method": "fs.version.snapshot",
    "params": {
      "path": "important.txt",
      "description": "Before major changes"
    },
    "id": 7
  }'
```

#### List Versions
```bash
curl -X POST http://localhost:8001/rpc \\
  -H "Content-Type: application/json" \\
  -d '{
    "method": "fs.version.list",
    "params": {"path": "important.txt"},
    "id": 8
  }'
```

## 🔧 Configuration

### Environment Variables

- `AUTO_CHUNK=true`: Enable adaptive chunk sizing for optimal performance
- `HASH_ALGO=xxhash`: Set hashing algorithm (xxhash|blake3|sha256|md5)
- `GZIP_CHUNK=true`: Enable gzip compression for chunks
- `OLD_PATHS=false`: Disable legacy API paths

### Feature Toggles

The server automatically detects available dependencies and enables features accordingly:

- **aiofiles**: Async file I/O (fallback to sync if unavailable)
- **xxhash**: Fast hashing (fallback to SHA256)
- **watchdog**: File system monitoring
- **sentence-transformers**: AI content analysis and embeddings
- **numpy/sklearn**: Advanced similarity calculations
- **pygments**: Syntax highlighting

## 🏗️ Architecture

### Core Components

1. **UnifiedFilesystemServer**: Main server class handling all operations
2. **FastAPI Application**: HTTP server with automatic OpenAPI documentation
3. **Vector Database**: SQLite-based storage for embeddings and versions
4. **Event System**: Real-time file system monitoring and notifications
5. **Progress Tracking**: WebSocket-based progress updates

### Data Models

- **FileMetadata**: Comprehensive file information
- **ContentAnalysis**: AI-powered content insights
- **EmbeddingResult**: Vector embeddings for semantic search
- **FileVersion**: Version control metadata
- **SearchResult**: Search results with relevance scoring

## 🔒 Security

- **Path Validation**: Prevents directory traversal attacks
- **Sandboxing**: All operations confined to specified base directory
- **Size Limits**: Configurable limits for file sizes and operation timeouts
- **Error Handling**: Secure error messages without information leakage

## 📊 Performance

### Optimizations

- **Adaptive Chunking**: Automatically adjusts chunk sizes for optimal throughput
- **Async Operations**: Non-blocking I/O for concurrent requests
- **Streaming**: Efficient handling of large files
- **Caching**: Content analysis and embedding caching
- **Connection Pooling**: Efficient database connection management

### Monitoring

- Real-time statistics at `/stats`
- Performance metrics for all operations
- Progress tracking for long-running tasks
- Connection and resource monitoring

## 🧪 Testing

The test suite covers:

- Basic file operations (read, write, delete, list)
- Directory operations
- Search functionality
- Content analysis (when AI features available)
- Error handling and edge cases
- Performance characteristics

## 🤝 Contributing

1. Install development dependencies: `pip install -r requirements.txt`
2. Run tests: `python test_filesystem_server.py`
3. Check code style: `python -m py_compile filesystem_server.py`
4. Submit pull requests with comprehensive tests

## 📄 License

MIT License - see LICENSE file for details.

## 🙋 Support

For issues, questions, or contributions:
1. Check the test output: `python test_filesystem_server.py`
2. Review server logs for error details
3. Ensure all dependencies are properly installed
4. Check the `/health` endpoint for system status

---

**Built with ❤️ for the Model Context Protocol ecosystem**

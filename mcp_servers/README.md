# MCP Server Management System

A comprehensive management system for organizing and controlling Model Context Protocol (MCP) servers within the Open WebUI project.

## 📁 Project Structure

```
mcp_servers/
├── servers/                    # Organized MCP servers
│   ├── active/                # Currently used servers
│   ├── archive/               # Old/superseded servers  
│   └── development/           # Development servers
├── utils/                     # Utility files
├── management/                # Management interface
│   ├── mcp_manager.py        # Python management backend
│   ├── api_server.py         # FastAPI REST server
│   ├── dashboard.html        # Web management interface
│   └── start_management.sh   # Startup script
├── logs/                      # Server logs
└── README.md                  # This file
```

## 🚀 Quick Start

### Start the Management Interface

```bash
cd /Users/cosburn/open_webui/mcp_servers/management
./start_management.sh
```

The management dashboard will be available at: **http://localhost:8090**

## 🖥️ Features

- **Web Dashboard**: Modern responsive interface for server management
- **Real-time Status**: Live monitoring of server states and ports
- **Server Control**: Start/stop servers with one click
- **Organized Structure**: Servers categorized as active, archive, or development
- **REST API**: Programmatic control via HTTP endpoints
- **Command Line**: Terminal interface for quick operations

## 📊 Server Categories

### Active Servers (Production Ready)
- **Kroger MCP Enhanced UI** (Port 9006): Main product search with MCP-UI protocol
- **Simple Filesystem Server** (Port 9001): Basic filesystem operations
- **Playwright Server** (Port 9002): Browser automation

### Archive Servers (Historical/Superseded)
- Various versions of Kroger MCP servers
- Alternative implementations kept for reference

### Development Servers (Work in Progress)
- New servers under development
- Testing implementations

## 🔧 API Endpoints

```
GET  /api/status                    # System status
GET  /api/servers                   # All servers by category
POST /api/servers/{name}/start      # Start server
POST /api/servers/{name}/stop       # Stop server
GET  /api/health                    # Health check
```

## 💻 Command Line Usage

```bash
# View all servers and status
python3 mcp_manager.py

# Example output:
# 🔧 MCP Server Manager
# 📊 Total Servers: 12
# 🟢 Active: 3
# 
# 📁 ACTIVE (3/3 running)
#    🟢 Kroger MCP Enhanced UI:9006
#    🟢 Simple Filesystem Server:9001
#    🟢 Playwright Server:9002
```

## Development

### Code Quality

This project uses several tools to maintain code quality:

- **Black**: Code formatting
- **Ruff**: Linting and import sorting
- **MyPy**: Static type checking
- **Pytest**: Testing framework

Run code quality checks:
```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/

# Run tests
pytest
```

### Database Migrations

Database schema changes are managed with Alembic:

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migrations
alembic downgrade -1
```

## Docker Deployment

The application can be deployed using Docker Compose:

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login and get access token
- `POST /api/v1/auth/test-token` - Test token validity

### MCP Servers
- `GET /api/v1/mcp-servers/` - List all MCP servers
- `POST /api/v1/mcp-servers/` - Create a new MCP server
- `GET /api/v1/mcp-servers/{id}` - Get MCP server details
- `PUT /api/v1/mcp-servers/{id}` - Update MCP server
- `DELETE /api/v1/mcp-servers/{id}` - Delete MCP server

### Health Checks
- `GET /health` - Basic health check
- `GET /api/v1/health/detailed` - Detailed health check

## Configuration

The application can be configured using environment variables or a `.env` file. See `.env.example` for all available options.

### Key Configuration Options

- `POSTGRES_*`: Database connection settings
- `REDIS_URL`: Redis connection URL
- `SECRET_KEY`: JWT signing secret
- `BACKEND_CORS_ORIGINS`: Allowed CORS origins
- `MCP_SERVERS_CONFIG_PATH`: Path to MCP servers configuration file

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run code quality checks: `black`, `ruff`, `mypy`
5. Run tests: `pytest`
6. Commit your changes: `git commit -am 'Add feature'`
7. Push to the branch: `git push origin feature-name`
8. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
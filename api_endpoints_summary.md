# Corporate Headquarters API Endpoints Summary

## Overview
The Corporate Headquarters (`corporate_headquarters.py`) implements API endpoints using two different approaches:
1. **SimpleHTTPRequestHandler** - Main implementation using `do_GET()` and `do_POST()` methods
2. **Flask routes** - Alternative Flask-based endpoints (appears to be a secondary implementation)

## Main API Endpoints (SimpleHTTPRequestHandler)

### GET Endpoints

#### Core Pages
- `/` or `/index.html` - Main dashboard page
- `/servers` - Dedicated servers monitoring page
- `/metrics` - Metrics endpoint for real-time updates

#### Health & Status
- `/health` - Corporate HQ health check endpoint
- `/api/test` - Simple test endpoint to verify API routing
- `/api/refresh/status` - Get current refresh status
- `/api/refresh/progress` - Server-Sent Events (SSE) endpoint for real-time refresh progress

#### Screenshot API
- `/api/screenshot` - Capture screenshot of the UI
- `/api/screenshot/display/{display_num}` - Capture specific display screenshot

#### Data Retrieval
- `/api/agents` - Get agent status data
- `/api/servers` - Get server status data
- `/api/departments` - Get departments data
- `/api/services` - Alias for servers endpoint
- `/api/department/hierarchy` - Get department hierarchy structure

### POST Endpoints

#### Refresh Operations
- `/api/enhanced/refresh` - Enhanced global refresh with component selection and real-time progress
- `/api/refresh/{component}` - Refresh specific component
- `/api/global/refresh` - Legacy global refresh endpoint
- `/api/servers/refresh` - Refresh server status
- `/api/database/refresh` - Refresh database metrics
- `/api/metrics/refresh` - Force refresh of metrics data

#### System Operations
- `/api/chat` - Send chat message to agents
- `/api/reload/status` - Handle reload status updates
- `/api/metrics/data` - Get metrics data with caching support

## Flask-based Endpoints (Alternative Implementation)

### GET Endpoints
- `/` - Root endpoint
- `/health` - Health check
- `/api/health-summary` - Get health summary
- `/api/health-history/<component>` - Get health history for specific component
- `/api/monitoring-config` - Get monitoring configuration
- `/api/screenshot` - Screenshot capture
- `/api/test` - Test endpoint
- `/api/agent-cortex/status` - Agent Cortex status
- `/api/ui/diagnostics` - UI diagnostics information
- `/api/ui/component/<component>` - Get specific UI component data
- `/api/header-status-dropdown` - Header status dropdown data
- `/api/registry/events` - Registry events
- `/metrics` - Metrics endpoint
- `/api/metrics` - Alternative metrics endpoint
- `/api/metrics/page` - Metrics page data
- `/api/metrics/summary` - Metrics summary
- `/api/servers/realtime-health` - Real-time server health status

### POST Endpoints
- `/api/chat` - Chat endpoint
- `/api/database/refresh` - Database refresh
- `/api/ui/preview` - UI preview
- `/api/global/refresh` - Global refresh
- `/api/systems/refresh` - Systems refresh
- `/api/enhanced/refresh` - Enhanced refresh
- `/api/refresh/<component>` - Component-specific refresh

## Key Features

### Server-Sent Events (SSE)
- `/api/refresh/progress` - Provides real-time progress updates during refresh operations
- Uses `text/event-stream` content type
- Sends heartbeat messages every 500ms to keep connection alive

### Enhanced Refresh System
- Supports component selection for targeted refreshes
- Real-time progress callbacks
- Comprehensive error handling and status reporting

### Metrics System
- Optimized metrics with caching support (30-second cache)
- Force refresh capability
- Integration with HQ Metrics Layer

### Chat Integration
- Direct messaging to agents via message bus
- Support for Cortex + LangGraph integration

### Screenshot Capabilities
- macOS screenshot capture using screencapture command
- Base64 encoding of screenshots
- Support for specific display capture

## Response Formats

All API endpoints return JSON responses with consistent structure:
```json
{
    "status": "success|error",
    "message": "Description of the result",
    "timestamp": "ISO format timestamp",
    "data": {} // Optional: endpoint-specific data
}
```

## Error Handling
- HTTP 200 for successful operations
- HTTP 500 for server errors
- Detailed error messages in JSON response
- Comprehensive exception handling with traceback logging
# Integration Testing Guide

## Overview

BoarderframeOS integration tests ensure that all components work together correctly. These tests verify end-to-end workflows, data flow between systems, and multi-component interactions.

## Test Structure

```
tests/integration/
├── __init__.py
├── test_system_startup.py      # System startup sequence tests
├── test_ui_integration.py      # UI component integration tests
└── test_data_flow.py          # Data flow and pipeline tests
```

## Running Integration Tests

### Quick Start

```bash
# Run all integration tests
./run_integration_tests.py

# Run specific test suite
./run_integration_tests.py --suite startup
./run_integration_tests.py --suite ui
./run_integration_tests.py --suite data-flow

# Run smoke tests (quick integration tests)
./run_integration_tests.py --suite smoke

# Run without starting services (if already running)
./run_integration_tests.py --no-services

# Keep services running after tests
./run_integration_tests.py --keep-services
```

### Test Services

Integration tests require:
- PostgreSQL (test instance on port 5435)
- Redis (test instance on port 6380)

These are automatically started via `docker-compose.test.yml`.

## Test Categories

### 1. System Startup Tests (`test_system_startup.py`)

Tests the complete system initialization sequence:

- **Docker Services Startup**: Verifies PostgreSQL and Redis start correctly
- **Database Initialization**: Tests migrations and connection pooling
- **MCP Servers Startup**: Validates all 9 MCP servers initialize
- **Agent Orchestrator**: Tests orchestrator initialization
- **Core Agents Startup**: Verifies Solomon, David, and Governor start
- **Full System Startup**: End-to-end startup sequence validation

### 2. UI Integration Tests (`test_ui_integration.py`)

Tests UI components and their backend integration:

- **Corporate HQ Integration**: API endpoints, metrics flow, WebSocket updates
- **Agent Cortex Integration**: Startup, API endpoints, chat functionality
- **Agent Communication Center**: WebSocket connections, message routing
- **Cross-UI Data Sync**: Data consistency across UI components
- **UI Performance**: Response times, concurrent request handling

### 3. Data Flow Tests (`test_data_flow.py`)

Tests data movement through the system:

- **Database Data Flow**: Agent registry, message persistence, analytics pipeline
- **Redis Data Flow**: Caching, pub/sub messaging, session management
- **Message Bus Flow**: Routing, priority handling, filtering
- **Vector Database**: Embedding storage and similarity search
- **Multi-Component Flow**: Complete request processing, distributed tasks

## Integration Test Patterns

### Testing Service Interactions

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_database_integration(self):
    """Test agents can interact with database"""
    # Mock database connection
    with patch('asyncpg.create_pool') as mock_pool:
        mock_conn = AsyncMock()
        mock_pool.return_value = mock_conn
        
        # Test agent operations
        agent = TestAgent(name="DBTest")
        result = await agent.query_database()
        
        # Verify interaction
        assert mock_conn.execute.called
```

### Testing Message Flow

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_message_routing(self):
    """Test message routing between components"""
    bus = MessageBus()
    await bus.initialize()
    
    # Track messages
    received = []
    
    async def handler(msg):
        received.append(msg)
    
    await bus.subscribe("test_topic", handler)
    
    # Send message
    await bus.publish(Message(
        topic="test_topic",
        content={"test": "data"}
    ))
    
    # Verify delivery
    assert len(received) == 1
```

### Testing End-to-End Workflows

```python
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_complete_workflow(self):
    """Test complete user request workflow"""
    # 1. User request
    request = create_user_request()
    
    # 2. API processing
    response = await api.process(request)
    
    # 3. Agent handling
    result = await agent.handle(response)
    
    # 4. Database storage
    await db.store(result)
    
    # 5. Cache update
    await cache.set(result.id, result)
    
    # Verify complete flow
    assert result.status == "completed"
```

## Test Environment

### Configuration

Integration tests use a separate test environment:

```python
# Environment variables
BOARDERFRAME_ENV=test
BOARDERFRAME_TEST_MODE=1

# Test database
DATABASE_URL=postgresql://test_boarderframe:test_pass@localhost:5435/test_boarderframeos

# Test Redis
REDIS_URL=redis://localhost:6380
```

### Test Data

Test data is stored in:
- `test_data/` - Test fixtures and datasets
- `test_logs/` - Test execution logs
- `test_configs/` - Test configuration files

### Cleanup

Test environment is automatically cleaned after test runs.

## Best Practices

### 1. Test Isolation

- Each test should be independent
- Use fresh test data for each test
- Clean up resources after tests
- Mock external dependencies

### 2. Realistic Testing

- Test with realistic data volumes
- Include error scenarios
- Test timeout and retry logic
- Verify resource cleanup

### 3. Performance Considerations

- Mark slow tests with `@pytest.mark.slow`
- Set appropriate timeouts
- Test concurrent operations
- Monitor resource usage

### 4. Debugging Integration Tests

```bash
# Run with verbose output
./run_integration_tests.py -v

# Run specific test
pytest tests/integration/test_system_startup.py::TestSystemStartup::test_database_initialization -vv

# Run with debugging
pytest tests/integration/ -vv -s --pdb
```

## Common Integration Scenarios

### 1. Multi-Agent Collaboration

Tests agents working together on complex tasks.

### 2. System Recovery

Tests system behavior during failures and recovery.

### 3. Data Consistency

Verifies data remains consistent across components.

### 4. Performance Under Load

Tests system performance with concurrent operations.

### 5. Security Integration

Validates security measures across components.

## Troubleshooting

### Docker Services Won't Start

```bash
# Check Docker status
docker info

# Check for port conflicts
lsof -i :5435  # Test PostgreSQL
lsof -i :6380  # Test Redis

# Manually start services
docker-compose -f docker-compose.test.yml up -d
```

### Test Timeouts

- Increase timeout values for slow operations
- Check for deadlocks or infinite loops
- Verify service health before tests

### Flaky Tests

- Add retry logic for network operations
- Increase wait times for async operations
- Mock unreliable external services

## CI/CD Integration

Integration tests should run:
- On pull requests (smoke tests)
- Before merging (full suite)
- In staging environment
- Before production deployment

## Reporting

Test results are saved to:
- `integration_test_report.json` - Detailed test results
- `htmlcov/` - Coverage report (if enabled)

View reports:
```bash
# View test report
cat integration_test_report.json | jq .

# Open coverage report
open htmlcov/index.html
```
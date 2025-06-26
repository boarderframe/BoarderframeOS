# Testing Guide for BoarderframeOS

## Overview

BoarderframeOS includes a comprehensive test suite covering unit tests, integration tests, and system tests. The test suite ensures reliability and maintainability across all components.

## Test Structure

```
tests/
├── test_core_components.py    # Core framework tests
├── test_agents.py              # Individual agent tests
├── test_integrations.py        # Cross-component integration tests
├── test_governance.py          # Governance system tests
├── test_task_queue.py          # Distributed task processing tests
└── test_health_monitoring.py   # Health monitoring tests
```

## Running Tests

### Quick Start

```bash
# Run all tests with coverage
./run_tests.py

# Run specific test suite
./run_tests.py --suite unit
./run_tests.py --suite agents
./run_tests.py --suite integration

# Run specific test file
./run_tests.py --test tests/test_core_components.py

# Run fast tests only (no integration)
./run_tests.py --suite fast
```

### Using pytest directly

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov --cov-report=html

# Run specific test file
pytest tests/test_agents.py -v

# Run tests matching pattern
pytest -k "test_solomon" -v

# Run tests with specific marker
pytest -m "not slow" -v
```

## Test Categories

### Unit Tests
- Test individual components in isolation
- Mock external dependencies
- Fast execution
- Located in: `test_core_components.py`

### Agent Tests
- Test each agent's functionality
- Verify agent lifecycle and behaviors
- Test inter-agent communication
- Located in: `test_agents.py`

### Integration Tests
- Test component interactions
- Verify system integrations
- Test with real dependencies where possible
- Located in: `test_integrations.py`

### Governance Tests
- Test policy enforcement
- Verify compliance monitoring
- Test violation handling
- Located in: `test_governance.py`

### Task Queue Tests
- Test distributed task processing
- Verify Celery integration
- Test worker management
- Located in: `test_task_queue.py`

### Health Monitoring Tests
- Test health metric collection
- Verify alerting system
- Test threshold management
- Located in: `test_health_monitoring.py`

## Coverage Requirements

- Minimum coverage: 70%
- Target coverage: 85%+
- Critical paths must have 95%+ coverage

View coverage report:
```bash
# Generate HTML coverage report
pytest --cov --cov-report=html

# Open report
open htmlcov/index.html
```

## Writing Tests

### Test Structure

```python
import pytest
from unittest.mock import Mock, AsyncMock

class TestComponent:
    """Test suite for specific component"""
    
    @pytest.fixture
    async def component(self):
        """Create component instance"""
        # Setup
        comp = Component()
        await comp.initialize()
        yield comp
        # Teardown
        await comp.shutdown()
    
    @pytest.mark.asyncio
    async def test_feature(self, component):
        """Test specific feature"""
        result = await component.do_something()
        assert result == expected_value
```

### Mocking Guidelines

1. Mock external services (databases, APIs)
2. Use AsyncMock for async methods
3. Patch at the lowest level possible
4. Verify mock calls when appropriate

### Async Testing

All async tests must:
1. Use `@pytest.mark.asyncio` decorator
2. Define test methods as `async def`
3. Use `await` for async operations
4. Handle async fixtures properly

## Test Markers

- `@pytest.mark.slow` - Long-running tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.asyncio` - Async tests

## CI/CD Integration

Tests are automatically run on:
- Every commit
- Pull requests
- Before deployment

Failed tests block merging and deployment.

## Debugging Tests

```bash
# Run with debugging output
pytest -vv -s

# Run with pdb on failure
pytest --pdb

# Run specific test with full traceback
pytest tests/test_agents.py::TestSolomonAgent::test_solomon_initialization -vv --tb=long
```

## Performance Testing

For performance-critical paths:
1. Add timing assertions
2. Test with realistic data volumes
3. Monitor resource usage
4. Set performance benchmarks

## Best Practices

1. **Keep tests fast** - Mock slow operations
2. **Test one thing** - Each test should verify one behavior
3. **Use descriptive names** - Test names should explain what they test
4. **Clean up resources** - Always cleanup in fixtures
5. **Avoid test interdependence** - Tests should run in any order
6. **Mock at boundaries** - Mock external services, not internal components
7. **Test edge cases** - Include error conditions and boundary values

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure PYTHONPATH includes project root
2. **Async warnings**: Use pytest-asyncio and proper markers
3. **Database errors**: Mock database connections in unit tests
4. **Timeout errors**: Increase timeout for slow tests
5. **Coverage gaps**: Add tests for uncovered code paths

### Getting Help

- Check test output for specific errors
- Review test implementation examples
- Ensure all dependencies are installed
- Verify test environment configuration
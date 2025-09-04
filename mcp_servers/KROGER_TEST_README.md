# Kroger MCP Server Test Suite

Comprehensive testing framework for the Kroger MCP (Model Context Protocol) Server implementation, covering OAuth2 authentication, API endpoints, error handling, and OpenAPI schema validation.

## 📋 Overview

This test suite provides comprehensive coverage for the Kroger MCP Server with over 80 test cases across multiple categories:

- **Unit Tests**: Individual component testing with mocks
- **Integration Tests**: Component interaction and workflow testing  
- **End-to-End Tests**: Complete MCP tool execution workflows
- **Security Tests**: Authentication, authorization, and input validation
- **Performance Tests**: Load testing and response time validation
- **Schema Tests**: OpenAPI specification compliance validation

## 🏗️ Test Architecture

### Test Categories

| Category | Tests | Coverage |
|----------|-------|----------|
| OAuth2 Authentication | 8 tests | Token lifecycle, refresh, validation |
| Product API | 12 tests | Search, details, filtering, pagination |
| Location API | 8 tests | Search by ZIP, coordinates, details |
| Cart Management | 10 tests | CRUD operations, item management |
| User Profile | 4 tests | Profile retrieval and validation |
| Error Handling | 15 tests | All HTTP status codes, rate limiting |
| Schema Validation | 20+ tests | Request/response validation |
| Security | 8 tests | Input sanitization, XSS, injection |
| Performance | 6 tests | Response times, concurrent load |

### Test Structure

```
tests/unit/test_kroger_mcp.py
├── TestKrogerMCPServerUnit           # Core unit tests
├── TestKrogerMCPServerIntegration    # Integration workflows  
├── TestKrogerMCPServerE2E           # End-to-end MCP testing
├── TestKrogerMCPServerSecurity      # Security validation
├── TestKrogerMCPServerPerformance   # Performance benchmarks
└── TestKrogerMCPServerSchemaValidation # OpenAPI compliance
```

## 🚀 Quick Start

### Prerequisites

Install required dependencies:

```bash
python run_kroger_tests.py --install-deps
```

### Running Tests

#### Complete Test Suite
```bash
# Run all test categories with reporting
python run_kroger_tests.py --suite

# Or using pytest directly
pytest tests/unit/test_kroger_mcp.py -v --cov=mcp_servers/kroger
```

#### Specific Test Categories
```bash
# Unit tests only
python run_kroger_tests.py --type unit

# Integration tests  
python run_kroger_tests.py --type integration

# Security tests
python run_kroger_tests.py --type security

# Performance tests
python run_kroger_tests.py --type performance

# Schema validation tests
python run_kroger_tests.py --type schema
```

#### Filtered Testing
```bash
# OAuth-related tests only
python run_kroger_tests.py --markers oauth

# Product search tests
python run_kroger_tests.py --keywords "product_search"

# Fast tests (exclude slow performance tests)
python run_kroger_tests.py --type fast
```

## 🧪 Test Details

### OAuth2 Authentication Tests

Tests comprehensive OAuth2 flow implementation:

```python
async def test_oauth_token_request_success()
async def test_oauth_token_request_failure() 
async def test_token_refresh_success()
async def test_token_validation()
```

**Coverage:**
- Client credentials flow
- Authorization code flow  
- Token refresh mechanism
- Token expiration handling
- Invalid credential scenarios

### API Endpoint Tests

#### Product API Tests
```python
async def test_product_search_success()
async def test_product_search_no_results()
async def test_product_details_success()
async def test_product_details_not_found()
```

#### Location API Tests  
```python
async def test_location_search_success()
async def test_location_search_by_coordinates()
async def test_location_details_success()
```

#### Cart Management Tests
```python
async def test_create_cart_success()
async def test_add_to_cart_success()
async def test_update_cart_item_success()
async def test_remove_from_cart_success()
```

### Error Handling Tests

Comprehensive error scenario coverage:

- **401 Unauthorized**: Invalid/expired tokens
- **403 Forbidden**: Insufficient permissions  
- **404 Not Found**: Non-existent resources
- **429 Rate Limited**: Request throttling
- **500 Server Error**: Internal failures

### Security Tests

Input validation and security measures:

```python
async def test_input_validation()
async def test_xss_prevention()
async def test_oauth_token_security()
```

**Validates protection against:**
- SQL injection attempts
- XSS attacks
- Path traversal
- Token exposure in logs
- Malicious input sanitization

### Schema Validation Tests

OpenAPI specification compliance:

```python
def test_oauth_token_schema_validation()
def test_product_schema_validation()
def test_location_schema_validation()  
def test_cart_schema_validation()
def test_error_response_schema_validation()
```

**Validates:**
- Request parameter schemas
- Response data structures
- Required field enforcement
- Data type validation
- Enum value constraints

### Performance Tests

Response time and load testing:

```python
async def test_token_refresh_performance()
async def test_product_search_performance()
async def test_concurrent_requests_performance()
```

**Benchmarks:**
- Token operations < 1 second
- API searches < 2 seconds  
- 10 concurrent requests < 5 seconds
- Rate limit compliance

## 🏭 Mock Data Factories

### KrogerDataFactory

Generates realistic test data for all Kroger API entities:

```python
# OAuth2 tokens
token = KrogerDataFactory.create_oauth_token_response()

# Product data with pricing, inventory, fulfillment
product = KrogerDataFactory.create_product_data()

# Store locations with address, hours, departments  
location = KrogerDataFactory.create_location_data()

# Shopping carts with items and totals
cart = KrogerDataFactory.create_cart_data()

# User profiles with loyalty info
profile = KrogerDataFactory.create_user_profile()
```

### Data Characteristics

- **Realistic**: Uses Faker library for authentic data
- **Configurable**: Override any field with custom values
- **Consistent**: Maintains referential integrity
- **Varied**: Random but deterministic generation

## ⚙️ Configuration

### pytest-kroger.ini

Comprehensive pytest configuration:

```ini
[tool:pytest]
testpaths = tests/unit/test_kroger_mcp.py
markers = 
    unit: Unit tests
    integration: Integration tests
    security: Security tests
    performance: Performance tests
    oauth: OAuth2 tests
    
addopts = --verbose --tb=short --color=yes
asyncio_mode = auto
```

### Environment Variables

Test environment configuration:

```bash
TEST_MODE=true
KROGER_CLIENT_ID=test_client_id
KROGER_CLIENT_SECRET=test_client_secret
KROGER_REDIRECT_URI=http://localhost:8080/callback
KROGER_BASE_URL=https://api.kroger.com/v1
```

## 📊 Coverage Analysis

### Coverage Targets

- **Overall Coverage**: > 90%
- **Critical Paths**: 100% (OAuth, error handling)
- **API Endpoints**: > 95%
- **Security Functions**: 100%

### Coverage Reports

Generated in multiple formats:

```bash
# HTML report
open htmlcov/kroger/index.html

# Terminal summary
pytest --cov=mcp_servers/kroger --cov-report=term-missing

# JSON for CI/CD
pytest --cov-report=json:coverage-kroger.json
```

## 🔧 Advanced Usage

### Parallel Testing

Run tests in parallel for faster execution:

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run with auto-detection of CPU cores
python run_kroger_tests.py --parallel

# Or specify number of workers
pytest -n 4 tests/unit/test_kroger_mcp.py
```

### Custom Test Markers

Add custom markers for specific test scenarios:

```python
@pytest.mark.slow
@pytest.mark.network_required
async def test_real_api_integration():
    """Test requiring actual network access."""
    pass
```

### Debugging Tests

Debug failing tests with enhanced output:

```bash
# Verbose output with local variables
pytest tests/unit/test_kroger_mcp.py::TestKrogerMCPServerUnit::test_oauth_token_request_success -vv -s --tb=long

# Drop into debugger on failure
pytest --pdb tests/unit/test_kroger_mcp.py

# Debug specific test method
pytest --pdb-trace tests/unit/test_kroger_mcp.py -k "test_product_search"
```

## 🤖 CI/CD Integration

### GitHub Actions Example

```yaml
name: Kroger MCP Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies  
        run: python run_kroger_tests.py --install-deps
      - name: Run test suite
        run: python run_kroger_tests.py --suite
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage-kroger.json
```

## 🐛 Troubleshooting

### Common Issues

#### Import Errors
```bash
# Ensure test dependencies installed
python run_kroger_tests.py --install-deps

# Check Python path
export PYTHONPATH="/Users/cosburn/MCP Servers:$PYTHONPATH"
```

#### Async Test Failures
```bash
# Ensure asyncio mode enabled
pytest --asyncio-mode=auto tests/unit/test_kroger_mcp.py
```

#### Mock Issues
```bash
# Run with verbose mocking info
pytest -v -s tests/unit/test_kroger_mcp.py -k "mock"
```

### Performance Issues

If tests run slowly:

1. Use parallel execution: `--parallel`
2. Filter to specific tests: `-k "unit"`
3. Skip slow tests: `-m "not slow"`
4. Reduce coverage overhead: `--no-coverage`

## 📈 Metrics and Reporting

### Test Results Dashboard

The test runner generates comprehensive reports:

```json
{
  "suite_start": "2025-01-15T10:30:00",
  "test_runs": {
    "Unit Tests": {
      "success": true,
      "duration": 12.5,
      "coverage": {"total_coverage": 92.3}
    },
    "Integration Tests": {
      "success": true, 
      "duration": 8.7
    }
  }
}
```

### Key Metrics

- **Test Execution Time**: < 30 seconds for full suite
- **Coverage Percentage**: > 90% target
- **Test Reliability**: > 99% pass rate
- **Performance Benchmarks**: All within SLA limits

## 🤝 Contributing

### Adding New Tests

1. Follow naming convention: `test_<feature>_<scenario>`
2. Use appropriate test markers
3. Include docstrings explaining test purpose
4. Add mock data using KrogerDataFactory
5. Validate both success and failure scenarios

### Test Categories

Choose appropriate test class:

- `TestKrogerMCPServerUnit`: Pure unit tests with mocks
- `TestKrogerMCPServerIntegration`: Multi-component workflows
- `TestKrogerMCPServerSecurity`: Security validation tests
- `TestKrogerMCPServerPerformance`: Load and timing tests

### Code Quality

Ensure tests follow project standards:

```bash
# Run linting
flake8 tests/unit/test_kroger_mcp.py

# Format code  
black tests/unit/test_kroger_mcp.py

# Type checking
mypy tests/unit/test_kroger_mcp.py
```

## 📚 References

- [Kroger API Documentation](https://developer.kroger.com/documentation)
- [OAuth2 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [Pytest Documentation](https://docs.pytest.org/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/docs/)

## 📄 License

This test suite is part of the MCP Server Manager project and follows the same license terms.
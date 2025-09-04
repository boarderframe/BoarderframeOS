# Playwright MCP Server Testing Guide

## Overview

This guide covers the comprehensive test suite for the Playwright MCP Server, including unit tests, integration tests, end-to-end tests, performance testing, and security validation.

## Test Structure

```
/Users/cosburn/MCP Servers/
├── test_playwright_mcp.py                    # Main comprehensive test suite
├── tests/
│   ├── unit/
│   │   └── test_playwright_mcp_unit.py       # Unit tests (fast, isolated)
│   ├── integration/
│   │   └── test_playwright_mcp_integration.py # Integration tests (real browser)
│   └── e2e/
│       └── test_playwright_mcp_e2e.py        # End-to-end workflow tests
├── playwright_server.py                      # Mock server for unit testing
├── playwright_mcp_server_real.py            # Real server with browser automation
├── run_playwright_tests.py                  # Test runner script
└── pytest.ini                               # Pytest configuration
```

## Test Categories

### 1. Unit Tests (`tests/unit/`)
- **Focus**: Individual components, request validation, error handling
- **Speed**: Fast (< 1 second per test)
- **Dependencies**: No external services or browsers
- **Coverage**: API endpoints, data models, validation logic

**Key Test Areas:**
- Pydantic model validation
- API endpoint responses (mocked)
- Error handling scenarios
- Request/response schema validation
- Concurrent API requests

### 2. Integration Tests (`tests/integration/`)
- **Focus**: Real browser automation with actual websites
- **Speed**: Medium (5-30 seconds per test)
- **Dependencies**: Real Playwright browser, internet access
- **Coverage**: Browser interactions, website compatibility

**Key Test Areas:**
- Navigation to real websites (example.com, httpbin.org)
- Text extraction from live pages
- Form filling and interaction
- Screenshot functionality
- JavaScript execution
- Error handling with real scenarios

### 3. End-to-End Tests (`tests/e2e/`)
- **Focus**: Complete workflows and user scenarios
- **Speed**: Slow (30+ seconds per test)
- **Dependencies**: Full server setup, real browser
- **Coverage**: Complete user journeys

**Key Test Areas:**
- Multi-step workflows (navigate → extract → screenshot)
- Form automation workflows
- Multi-page sessions
- Performance under load
- Error recovery scenarios
- Resource management

### 4. Performance Tests
- **Focus**: Response times, memory usage, concurrency
- **Markers**: `@pytest.mark.performance`
- **Coverage**: Load testing, memory leak detection

### 5. Security Tests
- **Focus**: Input validation, error handling, data sanitization
- **Markers**: `@pytest.mark.security`
- **Coverage**: Malicious input handling, timeout scenarios

## Running Tests

### Quick Start
```bash
# Install dependencies and run all tests
python run_playwright_tests.py --install-deps

# Run specific test suites
python run_playwright_tests.py --suite smoke    # Basic functionality
python run_playwright_tests.py --suite unit     # Unit tests only
python run_playwright_tests.py --suite integration  # Integration tests
python run_playwright_tests.py --suite e2e      # End-to-end tests
python run_playwright_tests.py --suite performance  # Performance tests
python run_playwright_tests.py --suite coverage # Coverage analysis
```

### Manual Test Execution
```bash
# Unit tests (fast)
pytest tests/unit/ -m "unit" -v

# Integration tests (requires browser)
pytest tests/integration/ -m "integration" -v

# E2E tests (full workflows)
pytest tests/e2e/ -m "e2e" -v

# Performance tests
pytest -m "performance" -v

# Run comprehensive suite
pytest test_playwright_mcp.py -v

# With coverage
pytest --cov=playwright_server --cov-report=html
```

### Test Markers
Use pytest markers to run specific test categories:

```bash
pytest -m "unit"           # Unit tests only
pytest -m "integration"    # Integration tests only
pytest -m "e2e"           # End-to-end tests only
pytest -m "performance"   # Performance tests only
pytest -m "security"      # Security tests only
pytest -m "slow"          # Slow tests
pytest -m "not slow"      # Skip slow tests
```

## Test Configuration

### Pytest Configuration (`pytest.ini`)
- Test discovery patterns
- Asyncio support
- Custom markers
- Output formatting
- Timeout settings
- Log configuration

### Environment Variables
```bash
export PLAYWRIGHT_BROWSERS_PATH=0  # Use default browser location
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0  # Allow browser downloads
```

## Test Scenarios Covered

### 1. Browser Startup and Shutdown ✅
- Browser initialization
- Context creation
- Resource cleanup
- Memory management

### 2. Navigation to Various Websites ✅
- Valid URLs (google.com, github.com, example.com)
- Invalid URLs and error handling
- Timeout scenarios
- Performance measurement

### 3. Text Extraction ✅
- Single elements
- Multiple elements
- Different page types
- Attribute extraction
- Consistency across calls

### 4. Element Interaction ✅
- Clicking buttons and links
- Form field filling
- Element waiting
- JavaScript-heavy pages

### 5. Screenshot Functionality ✅
- Full page screenshots
- Viewport screenshots
- Different formats (PNG, JPEG)
- Quality settings
- Element-specific screenshots

### 6. Error Handling ✅
- Invalid URLs
- Invalid selectors
- Network timeouts
- Malformed requests
- Browser crashes

### 7. Performance Testing ✅
- Response times
- Navigation speed
- Concurrent requests
- Memory usage tracking
- Load testing

### 8. OpenAPI Validation ✅
- Schema generation
- Endpoint documentation
- Request/response validation
- Interactive docs

### 9. Concurrent Request Handling ✅
- Multiple simultaneous requests
- Thread safety
- Resource isolation
- Performance under load

### 10. Memory Leak Detection ✅
- Memory growth monitoring
- Resource cleanup validation
- Long-running session stability
- Browser process management

## Test Data and Fixtures

### Test URLs
```python
{
    'google': 'https://www.google.com',
    'github': 'https://github.com',
    'example': 'https://example.com',
    'httpbin': 'https://httpbin.org/html',
    'javascript_heavy': 'https://www.wikipedia.org',
    'form_test': 'https://httpbin.org/forms/post',
    'slow_page': 'https://httpbin.org/delay/3',
    'invalid': 'https://nonexistent-domain-12345.com'
}
```

### Fixtures
- `playwright_client`: Real browser client for integration tests
- `mock_playwright_client`: Mock client for unit tests
- `test_urls`: Standard test URLs
- `real_client`: Real server client for E2E tests

## Expected Test Results

### Coverage Targets
- **Unit Tests**: 90%+ coverage of core logic
- **Integration Tests**: 80%+ coverage of browser interactions
- **E2E Tests**: 70%+ coverage of complete workflows

### Performance Benchmarks
- **Navigation**: < 15 seconds per page
- **API Response**: < 1 second per request
- **Screenshot**: < 5 seconds
- **Memory Growth**: < 100MB per test session

### Success Criteria
- All unit tests pass (required)
- 80%+ integration tests pass
- 70%+ E2E tests pass (some may fail due to network)
- No memory leaks detected
- Performance within acceptable limits

## Troubleshooting

### Common Issues

#### Browser Installation
```bash
# If Playwright browsers not installed
python -m playwright install chromium
python -m playwright install-deps
```

#### Permission Issues
```bash
# On Linux/macOS, browsers may need additional setup
sudo apt-get install libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2
```

#### Network Issues
- Some integration tests require internet access
- Use `--no-network` flag for offline testing
- Configure proxy settings if needed

#### Memory Issues
```bash
# Increase available memory for tests
export NODE_OPTIONS="--max-old-space-size=8192"
```

### Test Debugging

#### Verbose Output
```bash
pytest -v -s --tb=long  # Verbose with full tracebacks
```

#### Single Test Debugging
```bash
pytest test_playwright_mcp.py::TestPlaywrightMCPServer::test_browser_startup_shutdown -v -s
```

#### Browser Debugging (Non-headless)
```python
# In test files, modify setup:
await client.setup(headless=False)  # See browser actions
```

## Continuous Integration

### GitHub Actions Integration
The test suite is designed to work with CI/CD pipelines:

```yaml
- name: Install Playwright
  run: |
    pip install playwright
    playwright install chromium
    
- name: Run Tests
  run: |
    python run_playwright_tests.py --suite all
```

### Test Reports
- HTML reports generated in `test-results/`
- JUnit XML for CI integration
- Coverage reports in multiple formats

## Best Practices

### Writing New Tests
1. Use appropriate markers (`@pytest.mark.unit`, `@pytest.mark.integration`)
2. Follow naming convention: `test_feature_scenario`
3. Include docstrings describing test purpose
4. Use fixtures for common setup
5. Assert specific conditions, not just "no error"

### Test Organization
1. Group related tests in classes
2. Use descriptive class and method names
3. Keep unit tests fast (< 1 second)
4. Mark slow tests appropriately
5. Include both positive and negative test cases

### Performance Considerations
1. Use real browser only when necessary
2. Clean up resources in fixtures
3. Monitor memory usage in long tests
4. Use concurrent execution for independent tests
5. Set appropriate timeouts

## Maintenance

### Regular Tasks
- Update test URLs if they become unavailable
- Review and update performance benchmarks
- Add tests for new features
- Update browser versions
- Review test coverage reports

### Monitoring
- Track test execution times
- Monitor flaky test patterns
- Review failure rates in CI
- Update dependencies regularly

## Additional Resources

- [Playwright Documentation](https://playwright.dev/python/)
- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [AsyncIO Testing](https://docs.python.org/3/library/asyncio-dev.html#testing)
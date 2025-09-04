# Kroger MCP Authentication Testing Guide

## Overview

This guide provides comprehensive documentation for testing the Kroger MCP Server authentication system. The test suite is designed to validate all aspects of token lifecycle management, persistence, error handling, and LLM integration workflows.

## Test Architecture

### Test Categories

The test suite is organized into several categories, each focusing on specific aspects of the authentication system:

#### 1. **Token Lifecycle Tests** (`test_kroger_auth_comprehensive.py`)
- **Unit Tests**: Core token management logic
- **Token Creation**: Client credentials and user OAuth tokens
- **Token Refresh**: Automatic refresh before expiry
- **Token Validation**: Validity checking and expiry detection
- **Token Storage**: In-memory and persistent storage mechanisms

#### 2. **Persistence Tests** (`test_kroger_auth_real_server.py`)
- **Server Restart Persistence**: Tokens survive server restarts
- **File Storage**: JSON-based token storage validation
- **Corruption Recovery**: Handling of corrupted storage files
- **Concurrent Access**: Multiple processes accessing token storage

#### 3. **Error Scenario Tests** (Multiple files)
- **Network Failures**: Timeout and connection error handling
- **Invalid Tokens**: Expired and malformed token responses
- **API Errors**: 401, 403, 429, 500 error handling
- **Retry Logic**: Automatic retry for transient failures

#### 4. **Cart Operations Tests** (`test_kroger_cart_auth.py`)
- **Authenticated Cart Operations**: Add, update, remove items
- **Automatic Token Management**: Seamless token refresh during cart operations
- **Concurrent Cart Operations**: Multiple simultaneous cart requests
- **Cart Persistence**: Cart state across authentication events

#### 5. **LLM Integration Tests** (`test_kroger_auth_llm_workflows.py`)
- **Complete Workflows**: End-to-end shopping scenarios
- **Error Recovery**: Graceful handling of authentication failures
- **Performance**: Response times suitable for LLM interactions
- **Session Management**: State persistence across LLM requests

### Test Types

#### Unit Tests
- **Focus**: Individual functions and methods
- **Dependencies**: Mocked external services
- **Execution**: Fast, no external dependencies
- **Coverage**: Token management logic, validation, storage

#### Integration Tests
- **Focus**: Component interactions
- **Dependencies**: Real Kroger MCP server
- **Execution**: Requires running server
- **Coverage**: API endpoints, authentication flows, persistence

#### End-to-End Tests
- **Focus**: Complete user scenarios
- **Dependencies**: Full system deployment
- **Execution**: Simulates real LLM agent workflows
- **Coverage**: Multi-step operations, error recovery, performance

## Running Tests

### Quick Start

```bash
# Run all tests
python run_kroger_auth_tests.py --all

# Run specific test categories
python run_kroger_auth_tests.py --unit
python run_kroger_auth_tests.py --integration
python run_kroger_auth_tests.py --e2e

# Run with coverage report
python run_kroger_auth_tests.py --unit --coverage
```

### Prerequisites

#### Environment Setup
```bash
# Install dependencies
pip install -r requirements-dev.txt

# Optional: Set up Kroger API credentials for real API testing
export KROGER_CLIENT_ID="your_client_id"
export KROGER_CLIENT_SECRET="your_client_secret"
export KROGER_REDIRECT_URI="http://localhost:9004/auth/callback"
```

#### Server Requirements
For integration and E2E tests, the Kroger MCP server must be running:

```bash
# Start the server
python kroger_mcp_server.py

# Verify server health
curl http://localhost:9004/health
```

### Test Execution Options

#### 1. Unit Tests Only
```bash
python run_kroger_auth_tests.py --unit
```
- **Duration**: ~30 seconds
- **Dependencies**: None
- **Coverage**: Token lifecycle, validation, storage logic

#### 2. Integration Tests
```bash
python run_kroger_auth_tests.py --integration --server-url http://localhost:9004
```
- **Duration**: ~2-3 minutes
- **Dependencies**: Running Kroger MCP server
- **Coverage**: Real API interactions, persistence, error handling

#### 3. End-to-End LLM Workflows
```bash
python run_kroger_auth_tests.py --e2e --llm-workflows
```
- **Duration**: ~3-5 minutes
- **Dependencies**: Running server, optional Kroger API credentials
- **Coverage**: Complete shopping workflows, LLM interaction patterns

#### 4. Performance Tests
```bash
python run_kroger_auth_tests.py --performance --concurrent-users 10
```
- **Duration**: ~5-10 minutes
- **Dependencies**: Running server
- **Coverage**: Load testing, concurrent operations, response times

#### 5. Security Tests
```bash
python run_kroger_auth_tests.py --security
```
- **Duration**: ~1-2 minutes
- **Dependencies**: Running server
- **Coverage**: Authentication vulnerabilities, token security

#### 6. Specific Categories
```bash
python run_kroger_auth_tests.py --categories "token_lifecycle,cart_auth,error_handling"
```
- **Duration**: Variable
- **Dependencies**: Based on categories
- **Coverage**: Targeted testing of specific functionality

### Advanced Options

#### Coverage Reports
```bash
python run_kroger_auth_tests.py --unit --coverage
```
Generates:
- HTML report: `htmlcov/index.html`
- JSON report: `test-results/coverage.json`
- Terminal summary with missing lines

#### Verbose Output
```bash
python run_kroger_auth_tests.py --e2e --verbose
```
Provides detailed test execution information and debugging output.

#### Custom Server URL
```bash
python run_kroger_auth_tests.py --integration --server-url http://production-server:9004
```
Test against different server deployments.

## Test Scenarios

### Scenario 1: Token Lifecycle Validation

**Purpose**: Verify complete token management lifecycle

**Test Flow**:
1. Create client credentials token
2. Validate token is properly stored
3. Simulate token near expiry
4. Verify automatic refresh
5. Validate new token functionality
6. Test token persistence across restarts

**Expected Results**:
- All token operations complete successfully
- Automatic refresh occurs before expiry
- Tokens persist across server restarts
- Error handling for invalid tokens

### Scenario 2: LLM Shopping Workflow

**Purpose**: Simulate complete LLM agent shopping experience

**Test Flow**:
1. LLM searches for "milk" products
2. LLM adds milk to cart (triggers authentication)
3. LLM searches for "bread" products
4. LLM adds bread to cart (reuses authentication)
5. LLM retrieves cart contents
6. LLM modifies item quantities

**Expected Results**:
- Seamless authentication handling
- No visible token management to LLM
- Consistent response times < 3 seconds
- Helpful error messages for failures

### Scenario 3: Error Recovery Testing

**Purpose**: Validate graceful error handling

**Test Flow**:
1. Attempt cart operation with expired token
2. Verify automatic token refresh attempt
3. Simulate network failure during refresh
4. Verify helpful error message returned
5. Test recovery after network restoration

**Expected Results**:
- Automatic recovery where possible
- Clear error messages for LLM consumption
- No system crashes or undefined states
- Proper logging of authentication events

### Scenario 4: Concurrent Operations

**Purpose**: Test system behavior under load

**Test Flow**:
1. Simulate 10 concurrent LLM agents
2. Each agent performs shopping workflow
3. Monitor authentication token sharing
4. Verify no race conditions in token refresh
5. Check system performance degradation

**Expected Results**:
- All operations complete successfully
- No token conflicts or race conditions
- Response times remain reasonable
- Proper rate limiting enforcement

## Environment Configurations

### Development Mode
```bash
export KROGER_DEV_MODE=true
```
- Uses mock Kroger API responses
- No real API credentials required
- Faster test execution
- Suitable for unit and basic integration tests

### Production Mode
```bash
export KROGER_DEV_MODE=false
export KROGER_CLIENT_ID="real_client_id"
export KROGER_CLIENT_SECRET="real_client_secret"
```
- Uses real Kroger API
- Requires valid credentials
- Real network interactions
- Suitable for full integration testing

### Hardcoded User Mode
```bash
export KROGER_USER_ACCESS_TOKEN="user_access_token"
export KROGER_USER_REFRESH_TOKEN="user_refresh_token"
export KROGER_USER_TOKEN_EXPIRES_AT="1640995200"
export KROGER_HARDCODED_USER_ID="user_default"
```
- Simulates authenticated user for cart operations
- Bypasses OAuth flow for testing
- Enables cart operation testing without full OAuth setup

## Test Data Management

### Mock Data Factories

The test suite uses factory classes to generate consistent test data:

#### `KrogerAuthDataFactory`
- OAuth token responses
- Client credentials tokens
- Error responses
- User profiles

#### `CartAuthTestHelper`
- Cart item data
- Cart requests
- Mock cart responses

#### `TestDataFactory`
- Random strings and identifiers
- User data
- Server configurations
- Performance data

### Token Storage Testing

Tests validate token persistence using:
- **MockTokenStorage**: In-memory storage for unit tests
- **Real file storage**: JSON file persistence for integration tests
- **Concurrent access**: Multi-process storage testing

## Performance Benchmarks

### Expected Performance Metrics

#### Response Times
- **Token refresh**: < 1 second
- **Product search**: < 2 seconds
- **Cart operations**: < 3 seconds
- **Complete LLM workflow**: < 15 seconds

#### Throughput
- **Concurrent requests**: 20+ simultaneous operations
- **Success rate**: > 90% under normal load
- **Token operations**: > 100 tokens/minute

#### Resource Usage
- **Memory growth**: < 50MB during load tests
- **Storage efficiency**: < 10KB per user token
- **Network bandwidth**: Optimized for LLM usage

### Performance Test Categories

#### Load Testing
```bash
python run_kroger_auth_tests.py --performance --concurrent-users 20
```

#### Stress Testing
```bash
python run_kroger_auth_tests.py --categories "performance" --concurrent-users 50
```

#### Endurance Testing
Long-running tests to verify system stability over time.

## Debugging and Troubleshooting

### Common Issues

#### 1. Server Not Running
**Error**: "Server not available for integration tests"
**Solution**: 
```bash
python kroger_mcp_server.py &
python run_kroger_auth_tests.py --integration
```

#### 2. Missing Dependencies
**Error**: "ModuleNotFoundError: No module named 'pytest'"
**Solution**:
```bash
pip install -r requirements-dev.txt
```

#### 3. Authentication Failures
**Error**: "401 Unauthorized" or "403 Forbidden"
**Solution**: 
- Verify environment variables are set
- Check server configuration
- Enable dev mode for testing: `export KROGER_DEV_MODE=true`

#### 4. Rate Limiting
**Error**: "429 Too Many Requests"
**Solution**:
- Reduce concurrent users in performance tests
- Add delays between test runs
- Check rate limit configuration

### Debug Mode

#### Verbose Logging
```bash
python run_kroger_auth_tests.py --verbose --unit
```

#### Coverage Analysis
```bash
python run_kroger_auth_tests.py --coverage --unit
open htmlcov/index.html
```

#### Test-Specific Debugging
```bash
# Run specific test with maximum verbosity
pytest -vvs tests/unit/test_kroger_auth_comprehensive.py::TestKrogerAuthTokenLifecycle::test_client_credentials_token_creation
```

### Log Analysis

#### Server Logs
Monitor server logs during test execution:
```bash
tail -f kroger_mcp.log
```

#### Test Results
Review detailed test results:
```bash
cat test-results/kroger_auth_test_report.json | jq '.results[] | select(.exit_code != 0)'
```

## Continuous Integration

### GitHub Actions Integration

```yaml
name: Kroger Auth Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
      - name: Run unit tests
        run: |
          python run_kroger_auth_tests.py --unit --coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

### Test Execution Pipeline

1. **Unit Tests**: Always run, no dependencies
2. **Integration Tests**: Run if server can be started
3. **E2E Tests**: Run if full environment available
4. **Performance Tests**: Run on schedule or manual trigger

## Best Practices

### Test Development

1. **Isolation**: Each test should be independent
2. **Deterministic**: Tests should produce consistent results
3. **Fast Feedback**: Unit tests should run quickly
4. **Clear Naming**: Test names should describe the scenario
5. **Comprehensive Coverage**: Cover both success and failure paths

### Test Maintenance

1. **Regular Updates**: Keep tests in sync with code changes
2. **Performance Monitoring**: Track test execution times
3. **Flaky Test Detection**: Monitor and fix unreliable tests
4. **Documentation**: Keep test documentation current

### LLM-Focused Testing

1. **Realistic Scenarios**: Model actual LLM usage patterns
2. **Error Message Quality**: Ensure errors are helpful for LLMs
3. **Response Optimization**: Test response sizes and formats
4. **Latency Sensitivity**: Validate acceptable response times

## Future Enhancements

### Planned Improvements

1. **Chaos Testing**: Introduce random failures to test resilience
2. **Property-Based Testing**: Use hypothesis for input generation
3. **Visual Testing**: Screenshots and visual regression testing
4. **API Contract Testing**: Schema validation for all responses
5. **Security Penetration Testing**: Automated security scanning

### Test Infrastructure

1. **Containerized Testing**: Docker-based test environments
2. **Parallel Execution**: Distributed test execution
3. **Test Data Management**: Automated test data generation and cleanup
4. **Monitoring Integration**: Real-time test result monitoring

## Conclusion

This comprehensive test suite ensures the reliability, performance, and security of the Kroger MCP authentication system. Regular execution of these tests validates that the system meets the requirements for LLM integration and provides a robust, user-friendly authentication experience.

For questions or issues with the test suite, refer to the troubleshooting section or check the project's issue tracker.
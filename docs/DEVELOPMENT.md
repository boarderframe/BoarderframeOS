# BoarderframeOS Development Guide

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/boarderframe/BoarderframeOS.git
   cd BoarderframeOS
   ```

2. **Run the setup script**
   ```bash
   ./scripts/setup-dev.sh
   ```

3. **Configure environment**
   - Copy `.env.example` to `.env`
   - Add your API keys (OpenAI, Anthropic, etc.)

4. **Start the system**
   ```bash
   make start-system
   ```

## Development Workflow

### Creating a New Feature

1. **Create an issue**
   - Use the feature request template
   - Describe the feature and its benefits
   - Get it approved before starting work

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Write clean, documented code
   - Follow the existing patterns
   - Add tests for new functionality

4. **Test your changes**
   ```bash
   make test
   make lint
   ```

5. **Commit with conventional commits**
   ```bash
   git add .
   git commit -m "feat: add amazing new feature"
   ```

6. **Push and create PR**
   ```bash
   git push -u origin feature/your-feature-name
   ```
   Then create a pull request on GitHub.

## Code Style Guidelines

### Python
- Follow PEP 8
- Use type hints where possible
- Maximum line length: 88 characters (Black default)
- Use descriptive variable names

### Imports
- Standard library imports first
- Third-party imports second
- Local imports last
- Alphabetically ordered within groups

### Functions
- Single responsibility principle
- Docstrings for all public functions
- Type hints for parameters and returns
- Keep functions under 50 lines

### Classes
- Use dataclasses where appropriate
- Inherit from appropriate base classes
- Document class purpose and usage
- Keep classes focused

## Testing Guidelines

### Unit Tests
- Test individual functions/methods
- Mock external dependencies
- Aim for 80%+ coverage
- Use descriptive test names

### Integration Tests
- Test component interactions
- Use real databases (test instances)
- Test error conditions
- Verify data persistence

### Running Tests
```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest tests/test_base_agent.py -v

# Run specific test
pytest tests/test_base_agent.py::TestBaseAgent::test_agent_initialization -v
```

## Agent Development

### Creating a New Agent

1. **Choose the appropriate department**
   - Review `departments/boarderframeos-departments.json`
   - Select the right biblical department

2. **Inherit from BaseAgent**
   ```python
   from core.base_agent import BaseAgent
   
   class YourAgent(BaseAgent):
       def __init__(self, **kwargs):
           super().__init__(
               name="YourAgentName",
               department="Department",
               role="Specific Role",
               **kwargs
           )
   ```

3. **Implement required methods**
   - `think()`: Decision making logic
   - `act()`: Action execution
   - `handle_user_chat()`: User interaction

4. **Register with the system**
   - Add to department configuration
   - Update agent registry

### Agent Communication

Use the message bus for inter-agent communication:

```python
from core.message_bus import send_task_request, MessagePriority

correlation_id = await send_task_request(
    from_agent="your_agent",
    to_agent="target_agent",
    task={
        "type": "request_type",
        "data": {"key": "value"}
    },
    priority=MessagePriority.NORMAL
)
```

## MCP Server Development

### Creating a New MCP Server

1. **Create server file**
   ```python
   # mcp/your_server.py
   from mcp import MCPServer
   
   class YourServer(MCPServer):
       def __init__(self, port: int):
           super().__init__(port)
           self.setup_tools()
   ```

2. **Define tools**
   ```python
   def setup_tools(self):
       self.add_tool(
           name="your_tool",
           description="What it does",
           schema={...},
           handler=self.handle_your_tool
       )
   ```

3. **Add to server launcher**
   - Update `mcp/server_launcher.py`
   - Add health check endpoint

## Database Development

### Schema Changes

1. **Create migration file**
   ```sql
   -- migrations/008_your_change.sql
   ALTER TABLE agents ADD COLUMN new_field TEXT;
   ```

2. **Update models**
   - Reflect changes in Python models
   - Update any ORM mappings

3. **Test migration**
   ```bash
   # Run migration
   psql -U boarderframe -d boarderframeos -f migrations/008_your_change.sql
   
   # Verify
   psql -U boarderframe -d boarderframeos -c "\d agents"
   ```

## UI Development

### Corporate HQ Pages

1. **Add route in corporate_headquarters.py**
   ```python
   @app.route('/your-page')
   def your_page():
       return render_template_string(YOUR_PAGE_TEMPLATE)
   ```

2. **Create template**
   - Use existing style patterns
   - Include navigation
   - Add to tab system if needed

3. **Add metrics integration**
   - Use HQ Metrics Layer
   - Update metrics calculations

## Debugging

### Common Issues

1. **Import errors**
   - Check PYTHONPATH
   - Verify virtual environment
   - Check for circular imports

2. **Database connection**
   - Ensure Docker is running
   - Check port 5434
   - Verify credentials

3. **Agent communication**
   - Check message bus status
   - Verify agent registration
   - Review correlation IDs

### Debug Tools

```bash
# Check running processes
ps aux | grep python

# View logs
tail -f logs/*.log

# Database queries
psql -U boarderframe -d boarderframeos

# Port checking
lsof -i :8888  # Corporate HQ
lsof -i :5434  # PostgreSQL
```

## Performance Optimization

### Code Optimization
- Profile before optimizing
- Use async/await properly
- Batch database operations
- Cache expensive computations

### Database Optimization
- Add appropriate indexes
- Use connection pooling
- Optimize queries with EXPLAIN
- Consider partitioning for large tables

### Agent Optimization
- Implement event-driven patterns
- Use cost optimization checks
- Minimize LLM calls
- Cache agent decisions

## Documentation

### Code Documentation
- Docstrings for all public APIs
- Type hints throughout
- Inline comments for complex logic
- Update CLAUDE.md for AI guidance

### User Documentation
- Update README.md for features
- Add to docs/ directory
- Include examples
- Keep changelog updated

## Release Process

1. **Update version**
   - Update `pyproject.toml`
   - Update `setup.py`
   - Update CHANGELOG.md

2. **Create release branch**
   ```bash
   git checkout -b release/v0.2.0
   ```

3. **Final testing**
   - Run full test suite
   - Manual smoke tests
   - Performance benchmarks

4. **Tag and release**
   ```bash
   git tag -a v0.2.0 -m "Release version 0.2.0"
   git push origin v0.2.0
   ```

## Contributing Checklist

- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Changelog entry added
- [ ] All tests passing
- [ ] Linting passes
- [ ] PR description complete
- [ ] Linked to issue
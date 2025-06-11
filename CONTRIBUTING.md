# Contributing to BoarderframeOS

## Development Workflow

### 1. Branch Strategy
We use GitHub Flow with the following branch naming conventions:
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test additions/improvements

### 2. Creating Issues
Before starting work:
1. Create an issue describing the work
2. Add appropriate labels (bug, enhancement, documentation, etc.)
3. Assign to yourself or discuss assignment
4. Reference issue number in commits: `feat: add metrics API #123`

### 3. Development Process
```bash
# 1. Create feature branch
git checkout -b feature/agent-metrics

# 2. Make changes and commit with conventional commits
git add .
git commit -m "feat: add real-time metrics to agent dashboard"

# 3. Push branch and create PR
git push -u origin feature/agent-metrics
```

### 4. Commit Message Format
We use [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Maintenance tasks

### 5. Pull Request Process
1. Ensure all tests pass
2. Update documentation if needed
3. Add description linking to issue
4. Request review from maintainers
5. Address review feedback
6. Squash merge when approved

### 6. Code Style
- Python: Follow PEP 8
- Use type hints where possible
- Add docstrings to all public functions
- Keep functions focused and small
- Write self-documenting code

### 7. Testing
- Write tests for new features
- Maintain test coverage above 80%
- Run tests before pushing: `pytest`
- Include integration tests for agents

### 8. Documentation
- Update README.md for user-facing changes
- Update CLAUDE.md for AI-specific guidance
- Add inline comments for complex logic
- Keep documentation close to code

# Contributing to Open WebUI Complete

Thank you for your interest in contributing to Open WebUI Complete! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Issues

1. Check existing issues to avoid duplicates
2. Use issue templates when available
3. Include:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, versions)
   - Relevant logs or screenshots

### Suggesting Features

1. Open a discussion first for major features
2. Explain the use case and benefits
3. Consider implementation complexity
4. Be open to feedback and alternatives

### Submitting Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit with clear messages
6. Push to your fork
7. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone --recursive https://github.com/YOUR_USERNAME/open-webui-complete.git
cd open-webui-complete

# Set up environment
cp .env.example .env.litellm
# Edit .env.litellm with your API keys

# Start development environment
./start_dev_environment.sh
```

## Code Standards

### Python
- Follow PEP 8
- Use type hints where appropriate
- Write docstrings for functions/classes
- Keep functions focused and small

### JavaScript/TypeScript
- Use ESLint configuration
- Prefer async/await over callbacks
- Use meaningful variable names
- Comment complex logic

### Shell Scripts
- Use bash for scripts
- Add error handling
- Include usage information
- Make scripts idempotent

## Testing

- Test your changes locally
- Include tests for new features
- Ensure existing tests pass
- Test across different environments when possible

## Documentation

- Update README for user-facing changes
- Update CLAUDE.md for technical details
- Add inline comments for complex code
- Include examples where helpful

## Commit Messages

Format: `type(scope): description`

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Testing
- `chore`: Maintenance

Example: `feat(pipelines): add memory persistence`

## Review Process

1. Maintainers will review PRs promptly
2. Address feedback constructively
3. Be patient with the review process
4. Small, focused PRs are easier to review

## Community

- Be respectful and inclusive
- Help others when you can
- Share knowledge and learnings
- Celebrate contributions

## Questions?

- Open a discussion for general questions
- Check documentation first
- Join community channels (if available)

Thank you for contributing!
# Repository Setup Guide

This document outlines the recommended setup for collaborative development on the MCP Server Manager project.

## Branch Protection Rules

### Main Branch Protection
Configure the following branch protection rules for the `main` branch:

1. **Require pull request reviews before merging**
   - Required number of reviews: 2
   - Dismiss stale reviews when new commits are pushed
   - Require review from code owners

2. **Require status checks to pass before merging**
   - Require branches to be up to date before merging
   - Required status checks:
     - `lint-and-format`
     - `security-scan`
     - `test-backend`
     - `test-frontend`
     - `e2e-tests`
     - `docker-build`

3. **Restrict pushes that create files over 100MB**

4. **Require signed commits**

5. **Include administrators in restrictions**

### Develop Branch Protection
Configure similar rules for the `develop` branch with slightly relaxed requirements:

1. **Require pull request reviews before merging**
   - Required number of reviews: 1
   - Dismiss stale reviews when new commits are pushed

2. **Require status checks to pass before merging**
   - Same required status checks as main branch

## Repository Settings

### General Settings
- **Default branch**: `main`
- **Template repository**: Disabled
- **Issues**: Enabled
- **Discussions**: Enabled (optional)
- **Wiki**: Enabled
- **Projects**: Enabled

### Security Settings
- **Dependency graph**: Enabled
- **Dependabot alerts**: Enabled
- **Dependabot security updates**: Enabled
- **Dependabot version updates**: Enabled
- **Code scanning alerts**: Enabled
- **Secret scanning**: Enabled
- **Secret scanning push protection**: Enabled

### Code Security and Analysis
```yaml
# .github/dependabot.yml (create this file)
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    commit-message:
      prefix: "deps"
      prefix-development: "deps-dev"
      include: "scope"

  - package-ecosystem: "npm"
    directory: "/frontend"
    schedule:
      interval: "weekly"
    commit-message:
      prefix: "deps"
      prefix-development: "deps-dev"
      include: "scope"

  - package-ecosystem: "docker"
    directory: "/docker"
    schedule:
      interval: "weekly"
    commit-message:
      prefix: "deps"
      include: "scope"

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    commit-message:
      prefix: "ci"
      include: "scope"
```

## Environment Setup

### Required Secrets
Configure the following secrets in repository settings:

#### Development/Staging Environment
- `STAGING_DATABASE_URL`
- `STAGING_SECRET_KEY`
- `STAGING_DOCKER_REGISTRY_URL`
- `STAGING_DOCKER_USERNAME`
- `STAGING_DOCKER_PASSWORD`

#### Production Environment
- `PROD_DATABASE_URL`
- `PROD_SECRET_KEY`
- `PROD_DOCKER_REGISTRY_URL`
- `PROD_DOCKER_USERNAME`
- `PROD_DOCKER_PASSWORD`
- `PROD_DEPLOYMENT_KEY`

### Environment Protection Rules
- **Production Environment**:
  - Required reviewers: 2
  - Wait timer: 5 minutes
  - Deployment branches: `main` only

- **Staging Environment**:
  - Required reviewers: 1
  - Deployment branches: `develop` and `main`

## Git Workflow

### Branch Naming Convention
- **Feature branches**: `feature/description-of-feature`
- **Bug fix branches**: `fix/description-of-bug`
- **Hotfix branches**: `hotfix/critical-issue-description`
- **Release branches**: `release/v1.0.0`
- **Chore branches**: `chore/description-of-task`

### Commit Message Convention
Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools

### Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes and Commit**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

3. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a pull request through GitHub UI.

4. **Code Review Process**
   - Automated CI/CD checks must pass
   - Required number of approvals
   - Address review feedback
   - Squash and merge or rebase as appropriate

5. **Cleanup**
   ```bash
   git checkout main
   git pull origin main
   git branch -d feature/your-feature-name
   ```

## Release Process

### Semantic Versioning
- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality additions
- **PATCH** version for backwards-compatible bug fixes

### Release Steps
1. Create release branch from `develop`
2. Update version numbers and CHANGELOG.md
3. Merge release branch to `main`
4. Tag the release
5. Deploy to production
6. Merge back to `develop`

## Monitoring and Maintenance

### Regular Tasks
- Weekly dependency updates review
- Monthly security scan reviews
- Quarterly access review
- Performance monitoring alerts

### Code Quality Metrics
- Test coverage: >80%
- Security scan: No high/critical vulnerabilities
- Performance: Response time <200ms for API endpoints
- Uptime: >99.9% for production environment

## Getting Started for New Contributors

1. Fork the repository
2. Clone your fork locally
3. Set up development environment (see README.md)
4. Create feature branch
5. Make changes with tests
6. Submit pull request

## Support and Documentation

- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Discussions**: Use GitHub Discussions for questions and community interaction
- **Security**: Report security issues to security@example.com (replace with actual contact)
- **Documentation**: Keep docs updated with code changes
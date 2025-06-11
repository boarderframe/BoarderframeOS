# Changelog

All notable changes to BoarderframeOS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub development workflow setup
- Issue templates for bugs and features
- Pull request template
- Contributing guidelines
- CI/CD pipeline with GitHub Actions
- Changelog for version tracking

### Changed
- Enhanced documentation structure

### Fixed
- Server status display inconsistencies
- Database port references

## [0.1.0] - 2025-06-10

### Added
- Initial BoarderframeOS implementation
- Agent framework with BaseAgent foundation
- Message bus for inter-agent communication
- Agent orchestrator with lifecycle management
- 8 MCP servers (Registry, Filesystem, Database, Analytics, Payment, Customer, LLM, SQLite)
- Corporate Headquarters UI (port 8888)
- HQ Metrics Layer for real-time metrics
- PostgreSQL database with pgvector support
- Redis for caching and messaging
- Docker infrastructure setup
- Solomon (Chief of Staff) and David (CEO) agents
- Adam (Agent Creator), Eve (Agent Evolver), Bezalel (Master Programmer)
- 24 biblical-named departments structure
- Cost optimization system (99.9% API cost reduction)
- Comprehensive startup.py with 11-phase boot process

### Security
- Container isolation for agents
- Access control matrix by agent tier
- Audit logging for all operations

[Unreleased]: https://github.com/boarderframe/BoarderframeOS/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/boarderframe/BoarderframeOS/releases/tag/v0.1.0

# Changelog

All notable changes to BoarderframeOS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-06-26

### Added
- **Enterprise-grade features for production readiness:**
  - Secret Management System with Fernet encryption
  - Blue-Green Hot Reload System for zero-downtime updates
  - LLM Policy Engine with 99.9% cost optimization
  - OpenTelemetry Integration for distributed tracing
  - Multi-Tenancy with PostgreSQL Row Level Security
  - Agent Health Monitoring with real-time health scores
  - Distributed Task Queue with Celery and Redis
  - Governance Controller for policy enforcement
- **Enhanced Agent Communication Center (ACC):**
  - WebSocket-based real-time chat
  - Agent response broadcasting
  - Unified message handling
  - Support for Solomon and David agents
- **Agent Cortex UI Integration:**
  - Intelligent agent orchestration interface
  - Cost tracking and optimization display
  - Real-time agent status monitoring
- **Improved Infrastructure:**
  - Screenshot MCP server (port 8011) for UI capture
  - Agent Cortex UI server (port 8889)
  - Enhanced startup with deferred registry loading
  - Automatic virtual environment detection
  - Process management improvements

### Changed
- Migrated from SQLite to PostgreSQL for all database operations
- Updated all database references from port 8004 to 8010
- Enhanced agent orchestrator with dynamic path resolution
- Improved Corporate HQ service naming consistency
- Upgraded message bus to use 'content' instead of 'data' parameter
- Enhanced kill process script with development tool protection
- Improved startup timing and retry logic
- Updated requirements.txt with all missing dependencies

### Fixed
- OpenTelemetry instrumentation errors
- Multi-tenancy UUID type casting issues
- Prometheus metric reader configuration
- Agent implementation path resolution
- Agent Cortex UI status display
- Corporate HQ server status consistency
- Celery worker path resolution
- Database migration skip logic
- Process cleanup exclusions
- Startup dependency ordering

### Security
- Added comprehensive audit logging
- Implemented SOC2 compliance features
- Enhanced secret rotation policies
- Improved tenant isolation

## [Unreleased]

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

[Unreleased]: https://github.com/boarderframe/BoarderframeOS/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/boarderframe/BoarderframeOS/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/boarderframe/BoarderframeOS/releases/tag/v0.1.0

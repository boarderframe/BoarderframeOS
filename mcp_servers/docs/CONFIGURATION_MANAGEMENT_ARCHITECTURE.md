# MCP Server Configuration Management Architecture

## Overview

This document describes the comprehensive configuration management system for MCP servers, providing a robust, secure, and extensible framework for managing server configurations across different server types.

## System Architecture

```mermaid
graph TB
    subgraph "API Layer"
        API[Configuration API Endpoints]
        VAL[Validation Endpoint]
        SCHEMA[Schema Endpoint]
    end
    
    subgraph "Service Layer"
        CS[Configuration Service]
        VS[Validation Service]
        ES[Encryption Service]
    end
    
    subgraph "Data Layer"
        CM[Configuration Model]
        CHM[Configuration History]
        EM[Environment Model]
    end
    
    subgraph "Database"
        PG[(PostgreSQL)]
    end
    
    API --> CS
    VAL --> VS
    SCHEMA --> VS
    CS --> ES
    CS --> CM
    CS --> CHM
    CM --> PG
    CHM --> PG
    EM --> PG
```

## Core Components

### 1. Database Schema

#### Configuration Table
```sql
CREATE TABLE configurations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    key VARCHAR(255) NOT NULL,
    config_type VARCHAR(50) NOT NULL,
    mcp_server_id INTEGER REFERENCES mcp_servers(id),
    user_id INTEGER REFERENCES users(id),
    environment_id INTEGER REFERENCES environments(id),
    value JSONB NOT NULL,
    default_value JSONB,
    description TEXT,
    validation_schema JSONB,
    constraints JSONB,
    is_required BOOLEAN DEFAULT FALSE,
    is_secret BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'DRAFT',
    version INTEGER DEFAULT 1,
    parent_id INTEGER REFERENCES configurations(id),
    effective_from TIMESTAMP,
    effective_until TIMESTAMP,
    tags JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by_id INTEGER NOT NULL REFERENCES users(id)
);
```

#### Configuration History Table
```sql
CREATE TABLE configuration_history (
    id SERIAL PRIMARY KEY,
    configuration_id INTEGER NOT NULL REFERENCES configurations(id),
    action VARCHAR(50) NOT NULL,
    old_value JSONB,
    new_value JSONB,
    change_summary TEXT,
    changed_by_id INTEGER NOT NULL REFERENCES users(id),
    change_reason TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    changed_at TIMESTAMP DEFAULT NOW()
);
```

### 2. API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/configurations` | Create new configuration |
| GET | `/api/v1/configurations/{id}` | Get configuration by ID |
| PUT | `/api/v1/configurations/{id}` | Update configuration |
| DELETE | `/api/v1/configurations/{id}` | Archive configuration |
| GET | `/api/v1/servers/{id}/config` | Get server configurations |
| PUT | `/api/v1/servers/{id}/config` | Update server configuration |
| POST | `/api/v1/servers/{id}/config/validate` | Validate configuration |
| GET | `/api/v1/servers/{id}/config/schema` | Get configuration schema |
| GET | `/api/v1/configurations/history/{id}` | Get configuration history |
| POST | `/api/v1/configurations/rollback` | Rollback to previous version |
| POST | `/api/v1/configurations/backup` | Create configuration backup |
| POST | `/api/v1/servers/{id}/config/apply` | Apply configuration to server |

### 3. Configuration Types

#### Filesystem Server Configuration
```json
{
    "allowed_directories": ["/home/user/documents", "/tmp/workspace"],
    "blocked_paths": ["/etc", "/root", "/.ssh"],
    "file_size_limit_mb": 100,
    "max_directory_depth": 10,
    "permissions": {
        "read": true,
        "write": true,
        "delete": false,
        "execute": false
    },
    "file_type_filters": [".txt", ".json", ".md"]
}
```

#### Database Server Configuration
```json
{
    "connection_string": "postgresql://user:pass@localhost/db",
    "database_type": "postgresql",
    "pool_size": 10,
    "timeout_seconds": 30,
    "allowed_operations": ["SELECT", "INSERT", "UPDATE"],
    "allowed_tables": ["users", "products", "orders"],
    "query_limits": {
        "max_rows": 10000,
        "max_execution_time_ms": 30000
    }
}
```

#### API Server Configuration
```json
{
    "base_url": "https://api.example.com",
    "auth_type": "api_key",
    "auth_config": {
        "key": "your-api-key",
        "header_name": "X-API-Key"
    },
    "allowed_endpoints": ["/users", "/products"],
    "rate_limits": {
        "requests_per_minute": 60,
        "concurrent_requests": 5
    },
    "timeout_seconds": 30,
    "retry_config": {
        "max_retries": 3,
        "retry_delay_ms": 1000
    }
}
```

## Security Features

### 1. Input Validation
- **JSON Schema Validation**: All configurations validated against predefined schemas
- **Path Traversal Protection**: File paths sanitized to prevent directory traversal
- **SQL Injection Prevention**: Database configurations validated for safe operations
- **Rate Limiting**: API endpoints protected with rate limits

### 2. Encryption
- **Sensitive Data Encryption**: Passwords, tokens, and API keys encrypted at rest
- **Field-Level Encryption**: Automatic detection and encryption of sensitive fields
- **Key Management**: Master key derivation using PBKDF2 with SHA256

### 3. Access Control
- **Role-Based Access**: Different permission levels for configuration management
- **Audit Trail**: Complete history of all configuration changes
- **Approval Workflow**: Optional approval process for production changes

### 4. Validation Rules

#### Path Validation
```python
blocked_paths = [
    '/etc/passwd', '/etc/shadow', '/etc/sudoers',
    '/root', '/sys', '/proc', '/.ssh', '/.env'
]

def validate_path(path):
    # Remove path traversal attempts
    if '..' in path:
        raise ValueError("Path traversal detected")
    
    # Check against blocked paths
    for blocked in blocked_paths:
        if path.startswith(blocked):
            raise ValueError(f"Access to {blocked} is restricted")
```

## Configuration Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Draft: Create
    Draft --> Active: Approve
    Active --> Deprecated: New Version
    Active --> Archived: Archive
    Deprecated --> Archived: Cleanup
    Archived --> [*]
```

### States
- **DRAFT**: Initial state, configuration pending review
- **ACTIVE**: Configuration is live and being used
- **DEPRECATED**: Replaced by newer version but kept for history
- **ARCHIVED**: No longer in use, kept for audit purposes

## Versioning Strategy

### Version Creation
- New version created on significant changes
- Previous version marked as DEPRECATED
- Parent-child relationship maintained for rollback

### Version Management
```python
# Create new version
new_config = current_config.create_new_version(
    new_value=updated_data,
    change_reason="Updated database connection pool size"
)

# Rollback to previous version
rollback_config = configuration_service.rollback_configuration(
    configuration_id=123,
    target_version=2,
    reason="Performance issues with v3"
)
```

## Best Practices

### 1. Configuration Organization
- Use consistent naming conventions: `service.component.setting`
- Group related configurations using tags
- Document all configuration options

### 2. Security Guidelines
- Never store plaintext passwords or secrets
- Rotate encryption keys regularly
- Implement least-privilege access control
- Regular security audits of configurations

### 3. Change Management
- Always provide change reasons
- Test configurations in non-production first
- Use gradual rollout for critical changes
- Maintain rollback plans

### 4. Monitoring
- Track configuration drift
- Alert on unauthorized changes
- Monitor configuration apply failures
- Regular configuration backups

## Error Handling

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| Validation Failed | Invalid configuration format | Check against schema |
| Path Blocked | Attempting to access restricted path | Use allowed directories |
| Encryption Error | Failed to encrypt sensitive data | Check encryption keys |
| Version Conflict | Concurrent configuration updates | Use version locking |
| Apply Failed | Server rejected configuration | Check server logs |

## Performance Considerations

### Caching Strategy
- Cache active configurations in memory
- Invalidate cache on configuration updates
- Use read-through cache for frequently accessed configs

### Database Optimization
- Index on (mcp_server_id, key, status) for fast lookups
- Partition configuration_history by date
- Archive old configurations to cold storage

### Batch Operations
- Support bulk configuration updates
- Batch validation for multiple configurations
- Async processing for large configuration applies

## Integration Points

### 1. Process Manager
- Restart servers when configuration requires
- Apply configurations to running servers
- Validate server state before applying

### 2. Monitoring System
- Track configuration changes in metrics
- Alert on configuration anomalies
- Monitor configuration apply success rate

### 3. Backup System
- Regular configuration backups
- Point-in-time recovery support
- Cross-region backup replication

## Future Enhancements

### Planned Features
1. **Configuration Templates**: Reusable configuration patterns
2. **A/B Testing**: Test configurations on subset of servers
3. **Auto-Discovery**: Automatic configuration based on server type
4. **Configuration Drift Detection**: Alert when running config differs from stored
5. **GitOps Integration**: Sync configurations with Git repository
6. **Policy Engine**: Define and enforce configuration policies
7. **Multi-Environment Sync**: Promote configurations across environments

### Extensibility Points
- Custom validation plugins
- External secret managers integration
- Configuration webhooks
- Custom encryption providers

## Conclusion

The MCP Server Configuration Management system provides a comprehensive, secure, and scalable solution for managing server configurations. With built-in versioning, encryption, validation, and audit capabilities, it ensures configurations are managed safely and efficiently across the entire server fleet.
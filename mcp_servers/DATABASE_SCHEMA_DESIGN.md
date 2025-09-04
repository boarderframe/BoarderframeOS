# MCP Server Management - Database Schema Design

## Overview

This document describes the comprehensive PostgreSQL database schema design for MCP Server Management, including security restrictions, performance optimizations, and compliance features.

## Schema Architecture

### Core Design Principles

1. **Security First**: All tables include audit trails, access controls, and security policies
2. **Performance Optimized**: Strategic indexing for common query patterns and time-series data
3. **Compliance Ready**: Built-in support for SOC2, ISO27001, GDPR, and HIPAA requirements
4. **Scalable**: Designed to handle high-volume audit logs and concurrent server management
5. **Extensible**: Flexible JSON fields for configuration and metadata

### Database Tables

#### 1. User Management Tables

**user_roles**
- Defines role-based access control (RBAC) permissions
- System and custom roles with JSON permission arrays
- Supports hierarchical permission inheritance

**users** 
- Complete user management with security features
- Multi-factor authentication support
- Account lockout and password policies
- API key management with expiration
- Soft delete capability for compliance

**user_sessions**
- Session tracking for security and audit
- Device fingerprinting and IP tracking
- Automatic session expiration and revocation
- Concurrent session limiting

#### 2. MCP Server Management Tables

**mcp_servers**
- Enhanced server configuration with security controls
- Resource usage monitoring (CPU, memory)
- Health check and restart policies
- Owner-based access control
- Security policy association

**environments**
- Multi-environment deployment support
- Environment-specific configurations and limits
- Maintenance window management
- Deployment tracking and rollback capability

#### 3. Configuration Management Tables

**configurations**
- Versioned configuration management
- Environment and server-specific settings
- Approval workflow for sensitive changes
- Schema validation and constraints
- Encrypted storage for secrets

**configuration_history**
- Complete audit trail of configuration changes
- Change reason tracking and approval records
- Rollback capability with version management

#### 4. Security and Access Control Tables

**security_policies**
- Comprehensive security policy definitions
- Network, authentication, and resource restrictions
- Threat detection and response configuration
- Policy inheritance and priority management

**access_controls**
- Fine-grained resource access permissions
- Time-based and conditional access rules
- Usage tracking and quota management
- Audit trail for access grants/revocations

**rate_limits**
- Multi-dimensional rate limiting (user, IP, endpoint)
- Sliding window implementation
- Policy-based limit configuration
- Real-time quota tracking

#### 5. Audit and Compliance Tables

**audit_logs**
- Comprehensive activity logging
- Request/response data capture (sanitized)
- Performance metrics (duration, status codes)
- Multi-dimensional indexing for fast queries

**security_events**
- Security-specific event tracking
- Threat scoring and indicator management
- Incident response workflow
- Geographic and behavioral analytics

**audit_logs_archive**
- Long-term compliance storage
- Data integrity verification (checksums)
- Legal hold and retention management
- Compressed historical data

## Performance Optimizations

### Indexing Strategy

#### Primary Indexes
- **B-tree indexes** on primary keys and foreign keys
- **Unique indexes** for natural keys (usernames, emails, server names)
- **Composite indexes** for multi-column queries

#### Performance Indexes
```sql
-- Time-series queries (audit logs, events)
CREATE INDEX idx_audit_logs_created_action ON audit_logs (created_at, action_type);
CREATE INDEX idx_security_events_occurred_severity ON security_events (occurred_at, severity);

-- User activity patterns
CREATE INDEX idx_user_sessions_user_active ON user_sessions (user_id, is_active);
CREATE INDEX idx_access_controls_user_server ON access_controls (user_id, mcp_server_id);

-- Server management
CREATE INDEX idx_mcp_servers_owner_status ON mcp_servers (owner_id, status);
CREATE INDEX idx_mcp_servers_health_check ON mcp_servers (last_health_check, status);
```

#### Partial Indexes
```sql
-- Failed operations (security focus)
CREATE INDEX idx_audit_logs_failures ON audit_logs (action_type, created_at) 
WHERE success = false;

-- Critical unresolved security events
CREATE INDEX idx_security_events_critical_unresolved ON security_events (occurred_at, event_type) 
WHERE severity IN ('HIGH', 'CRITICAL') AND resolved = false;

-- Active configurations by scope
CREATE UNIQUE INDEX idx_config_unique_server_key ON configurations (mcp_server_id, key, status) 
WHERE mcp_server_id IS NOT NULL AND status = 'ACTIVE';
```

#### Full-Text Search Indexes
```sql
-- Log content analysis
CREATE INDEX idx_audit_logs_description_fts ON audit_logs 
USING gin(to_tsvector('english', description));

CREATE INDEX idx_security_events_description_fts ON security_events 
USING gin(to_tsvector('english', description));
```

### Query Optimization Patterns

#### 1. Time-Range Queries
Optimized for dashboard queries and reporting:
```sql
-- Efficient audit log queries with covering indexes
SELECT action_type, COUNT(*), AVG(duration_ms)
FROM audit_logs 
WHERE created_at >= NOW() - INTERVAL '24 hours'
  AND user_id = $1
GROUP BY action_type
ORDER BY COUNT(*) DESC;
```

#### 2. Security Analytics
Fast security event analysis:
```sql
-- Real-time threat detection
SELECT ip_address, COUNT(*) as failed_attempts
FROM security_events 
WHERE event_type = 'failed_login' 
  AND occurred_at >= NOW() - INTERVAL '1 hour'
GROUP BY ip_address
HAVING COUNT(*) >= 5;
```

#### 3. Server Health Monitoring
Efficient server status queries:
```sql
-- Server performance dashboard
SELECT s.name, s.status, s.cpu_usage, s.memory_usage,
       EXTRACT(EPOCH FROM (NOW() - s.last_health_check)) / 60 as minutes_since_health_check
FROM mcp_servers s
WHERE s.is_enabled = true
  AND s.owner_id = $1
ORDER BY s.last_activity_at DESC;
```

## Security Features

### Access Control
- **Role-Based Access Control (RBAC)**: Hierarchical permission system
- **Resource-Level Permissions**: Fine-grained access to specific servers/configurations
- **Time-Based Access**: Temporary access grants with automatic expiration
- **Conditional Access**: Context-aware permissions based on location, time, device

### Data Protection
- **Encryption at Rest**: Sensitive configuration data encrypted using AES-256-GCM
- **Secrets Management**: Integration with HashiCorp Vault, AWS Secrets Manager
- **Data Masking**: Automatic sanitization of sensitive data in logs
- **Secure Deletion**: Cryptographic erasure of sensitive data

### Audit and Monitoring
- **Comprehensive Logging**: All actions logged with full context
- **Integrity Protection**: Cryptographic checksums for audit log integrity
- **Real-time Monitoring**: Stream processing for security events
- **Compliance Reporting**: Pre-built reports for SOC2, ISO27001, GDPR

## Compliance Features

### Data Retention
```sql
-- Automated data lifecycle management
-- Archive audit logs older than 90 days
INSERT INTO audit_logs_archive (original_audit_log_id, audit_data, checksum, archive_reason)
SELECT id, row_to_json(audit_logs.*), encode(sha256(row_to_json(audit_logs.*)::text::bytea), 'hex'), 'retention_policy'
FROM audit_logs 
WHERE created_at < NOW() - INTERVAL '90 days';

-- Legal hold prevention
UPDATE audit_logs_archive 
SET retention_until = NULL 
WHERE legal_hold = true;
```

### Compliance Standards Support

#### SOC2 Type II
- Continuous monitoring of access controls
- Automated compliance reporting
- Change management audit trails
- Security incident tracking

#### GDPR
- Right to erasure implementation
- Data processing audit logs
- Consent management tracking
- Data minimization enforcement

#### ISO27001
- Risk assessment data capture
- Incident response workflow
- Asset management tracking
- Regular security reviews

## Configuration Management

### Secure Configuration Structure

The `/config/mcp.json` file implements:

1. **Schema Validation**: JSON Schema with 150+ validation rules
2. **Security Policies**: Comprehensive security controls per server
3. **Resource Limits**: CPU, memory, and network constraints
4. **Access Restrictions**: File system, database, and operation controls
5. **Compliance Settings**: Audit requirements and data protection

### Key Security Features

```json
{
  "security": {
    "global_policy": {
      "require_authentication": true,
      "require_tls": true,
      "min_tls_version": "1.2",
      "require_mfa": true,
      "session_timeout_minutes": 480,
      "enable_audit_logging": true,
      "enable_intrusion_detection": true
    },
    "network_security": {
      "allowed_ip_ranges": ["10.0.0.0/8"],
      "rate_limiting": {
        "requests_per_minute": 100,
        "block_on_exceed": true
      }
    }
  }
}
```

### Server-Specific Security

Each server configuration includes:
- **Access Restrictions**: Allowed/denied paths, operations, databases
- **Resource Limits**: CPU, memory, timeout constraints  
- **Audit Configuration**: Logging levels and sensitive data handling
- **Health Monitoring**: Automated health checks and restart policies

## Migration Strategy

### Database Migrations

1. **Initial Schema (`001_initial_schema.py`)**
   - Creates core tables with primary indexes
   - Establishes foreign key relationships
   - Sets up basic constraints and validations

2. **Extended Features (`002_remaining_tables.py`)**
   - Adds audit and security tables
   - Creates performance-optimized indexes
   - Implements full-text search capabilities

### Performance Migration

```sql
-- Example: Add partitioning for large audit tables
CREATE TABLE audit_logs_y2025m01 PARTITION OF audit_logs
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

-- Create monthly partitions automatically
CREATE OR REPLACE FUNCTION create_monthly_partitions()
RETURNS void AS $$
DECLARE
    start_date date;
    end_date date;
BEGIN
    start_date := date_trunc('month', CURRENT_DATE);
    end_date := start_date + interval '1 month';
    
    EXECUTE format('CREATE TABLE IF NOT EXISTS audit_logs_%s PARTITION OF audit_logs
                    FOR VALUES FROM (%L) TO (%L)',
                   to_char(start_date, 'YYYY"m"MM'),
                   start_date,
                   end_date);
END;
$$ LANGUAGE plpgsql;
```

## Monitoring and Maintenance

### Performance Monitoring Queries

The included `performance_queries.sql` provides:
- Index usage analysis
- Query performance benchmarking  
- Table bloat detection
- Security event analysis
- Automated maintenance recommendations

### Key Metrics to Monitor

1. **Query Performance**
   - Average response time by endpoint
   - Slow query identification (>100ms)
   - Index hit ratio (target >95%)

2. **Security Metrics**
   - Failed authentication attempts
   - Privilege escalation events
   - Suspicious IP activity
   - Data access patterns

3. **Resource Utilization**
   - Server CPU/memory usage
   - Database connection pooling
   - Audit log growth rate
   - Configuration change frequency

## Best Practices

### Database Operations

1. **Regular Maintenance**
   ```sql
   -- Weekly maintenance tasks
   VACUUM ANALYZE audit_logs;
   REINDEX INDEX CONCURRENTLY idx_audit_logs_created_action;
   ```

2. **Backup Strategy**
   - Point-in-time recovery capability
   - Encrypted backup storage
   - Cross-region replication for DR
   - Regular restore testing

3. **Security Hardening**
   - Row-level security (RLS) policies
   - Connection encryption (SSL/TLS)
   - Database user privilege separation
   - Regular security updates

### Application Integration

1. **Connection Pooling**
   ```python
   # Optimized connection pool settings
   engine = create_engine(
       database_url,
       pool_size=20,
       max_overflow=30,
       pool_pre_ping=True,
       pool_recycle=300
   )
   ```

2. **Query Optimization**
   - Use prepared statements
   - Implement query result caching
   - Batch operations where possible
   - Monitor N+1 query patterns

## Conclusion

This database schema design provides a robust, secure, and scalable foundation for MCP Server Management. The combination of comprehensive security controls, performance optimizations, and compliance features ensures the system can handle enterprise-scale deployments while maintaining strong security posture and regulatory compliance.

The modular design allows for incremental deployment and customization based on specific organizational requirements, while the extensive audit capabilities provide the visibility needed for security operations and compliance reporting.
"""
Complete remaining tables for MCP Server Management

This migration completes the schema by adding:
- configurations
- configuration_history  
- access_controls
- rate_limits
- audit_logs
- security_events
- audit_logs_archive

Performance optimizations included:
- Optimized indexes for audit log queries by date ranges
- Partial indexes for active records and failed operations
- Composite indexes for complex filtering scenarios
- Text search indexes for log content analysis
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    """Create remaining tables with optimized indexes."""
    
    # Create configurations table
    op.create_table(
        'configurations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('key', sa.String(255), nullable=False),
        sa.Column('config_type', sa.Enum('SYSTEM', 'SERVER', 'USER', 'ENVIRONMENT', 'SECURITY', 'LOGGING', 'MONITORING', name='configurationtype'), nullable=False),
        sa.Column('mcp_server_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('environment_id', sa.Integer(), nullable=True),
        sa.Column('value', sa.JSON(), nullable=False),
        sa.Column('default_value', sa.JSON(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('validation_schema', sa.JSON(), nullable=True),
        sa.Column('constraints', sa.JSON(), nullable=True),
        sa.Column('is_required', sa.Boolean(), nullable=False),
        sa.Column('is_secret', sa.Boolean(), nullable=False),
        sa.Column('status', sa.Enum('DRAFT', 'ACTIVE', 'DEPRECATED', 'ARCHIVED', name='configurationstatus'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('effective_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.CheckConstraint('version > 0', name='valid_version'),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['environment_id'], ['environments.id'], ),
        sa.ForeignKeyConstraint(['mcp_server_id'], ['mcp_servers.id'], ),
        sa.ForeignKeyConstraint(['parent_id'], ['configurations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Configuration indexes
    op.create_index(op.f('ix_configurations_id'), 'configurations', ['id'])
    op.create_index('ix_configurations_name', 'configurations', ['name'])
    op.create_index('ix_configurations_key', 'configurations', ['key'])
    op.create_index('ix_configurations_config_type', 'configurations', ['config_type'])
    op.create_index('ix_configurations_mcp_server_id', 'configurations', ['mcp_server_id'])
    op.create_index('ix_configurations_user_id', 'configurations', ['user_id'])
    op.create_index('ix_configurations_environment_id', 'configurations', ['environment_id'])
    op.create_index('ix_configurations_status', 'configurations', ['status'])
    op.create_index('ix_configurations_parent_id', 'configurations', ['parent_id'])
    op.create_index('ix_configurations_approved_by_id', 'configurations', ['approved_by_id'])
    op.create_index('ix_configurations_created_by_id', 'configurations', ['created_by_id'])
    op.create_index('ix_configurations_created_at', 'configurations', ['created_at'])
    
    # Configuration composite indexes for performance
    op.create_index('idx_configurations_type_status', 'configurations', ['config_type', 'status'])
    op.create_index('idx_configurations_effective', 'configurations', ['effective_from', 'effective_until', 'status'])
    op.create_index('idx_configurations_server_type', 'configurations', ['mcp_server_id', 'config_type'])
    op.create_index('idx_configurations_creator', 'configurations', ['created_by_id', 'created_at'])
    op.create_index('idx_configurations_parent_version', 'configurations', ['parent_id', 'version'])
    
    # Partial unique indexes for active configurations
    op.execute("""
        CREATE UNIQUE INDEX idx_config_unique_server_key 
        ON configurations (mcp_server_id, key, status) 
        WHERE mcp_server_id IS NOT NULL AND status = 'ACTIVE'
    """)
    op.execute("""
        CREATE UNIQUE INDEX idx_config_unique_user_key 
        ON configurations (user_id, key, status) 
        WHERE user_id IS NOT NULL AND status = 'ACTIVE'
    """)
    op.execute("""
        CREATE UNIQUE INDEX idx_config_unique_global_key 
        ON configurations (key, status) 
        WHERE mcp_server_id IS NULL AND user_id IS NULL AND status = 'ACTIVE'
    """)

    # Create configuration_history table
    op.create_table(
        'configuration_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('configuration_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('old_value', sa.JSON(), nullable=True),
        sa.Column('new_value', sa.JSON(), nullable=True),
        sa.Column('change_summary', sa.Text(), nullable=True),
        sa.Column('changed_by_id', sa.Integer(), nullable=False),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['changed_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['configuration_id'], ['configurations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_configuration_history_configuration_id', 'configuration_history', ['configuration_id'])
    op.create_index('ix_configuration_history_action', 'configuration_history', ['action'])
    op.create_index('ix_configuration_history_changed_by_id', 'configuration_history', ['changed_by_id'])
    op.create_index('ix_configuration_history_changed_at', 'configuration_history', ['changed_at'])
    op.create_index('idx_config_history_config_date', 'configuration_history', ['configuration_id', 'changed_at'])
    op.create_index('idx_config_history_user_date', 'configuration_history', ['changed_by_id', 'changed_at'])
    op.create_index('idx_config_history_action_date', 'configuration_history', ['action', 'changed_at'])

    # Create access_controls table
    op.create_table(
        'access_controls',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('mcp_server_id', sa.Integer(), nullable=False),
        sa.Column('resource_path', sa.String(500), nullable=True),
        sa.Column('access_level', sa.Enum('NONE', 'READ', 'WRITE', 'EXECUTE', 'ADMIN', name='accesslevel'), nullable=False),
        sa.Column('security_policy_id', sa.Integer(), nullable=True),
        sa.Column('allowed_operations', sa.JSON(), nullable=True),
        sa.Column('denied_operations', sa.JSON(), nullable=True),
        sa.Column('conditions', sa.JSON(), nullable=True),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('max_requests_per_hour', sa.Integer(), nullable=True),
        sa.Column('max_concurrent_requests', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_temporary', sa.Boolean(), nullable=False),
        sa.Column('granted_by_id', sa.Integer(), nullable=False),
        sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.CheckConstraint('max_requests_per_hour >= 0', name='valid_max_requests'),
        sa.CheckConstraint('max_concurrent_requests >= 0', name='valid_max_concurrent'),
        sa.CheckConstraint('usage_count >= 0', name='valid_usage_count'),
        sa.ForeignKeyConstraint(['granted_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['mcp_server_id'], ['mcp_servers.id'], ),
        sa.ForeignKeyConstraint(['security_policy_id'], ['security_policies.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Access control indexes
    op.create_index('ix_access_controls_user_id', 'access_controls', ['user_id'])
    op.create_index('ix_access_controls_mcp_server_id', 'access_controls', ['mcp_server_id'])
    op.create_index('ix_access_controls_access_level', 'access_controls', ['access_level'])
    op.create_index('ix_access_controls_security_policy_id', 'access_controls', ['security_policy_id'])
    op.create_index('ix_access_controls_granted_by_id', 'access_controls', ['granted_by_id'])
    op.create_index('ix_access_controls_created_at', 'access_controls', ['created_at'])
    op.create_index('idx_access_controls_user_server', 'access_controls', ['user_id', 'mcp_server_id'])
    op.create_index('idx_access_controls_server_access', 'access_controls', ['mcp_server_id', 'access_level'])
    op.create_index('idx_access_controls_validity', 'access_controls', ['valid_from', 'valid_until', 'is_active'])
    op.create_index('idx_access_controls_user_active', 'access_controls', ['user_id', 'is_active'])
    op.create_index('idx_access_controls_granted', 'access_controls', ['granted_by_id', 'granted_at'])
    op.create_index('idx_access_controls_unique', 'access_controls', ['user_id', 'mcp_server_id', 'resource_path'], unique=True)

    # Create rate_limits table
    op.create_table(
        'rate_limits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('mcp_server_id', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('api_endpoint', sa.String(500), nullable=True),
        sa.Column('limit_type', sa.Enum('REQUESTS_PER_MINUTE', 'REQUESTS_PER_HOUR', 'REQUESTS_PER_DAY', 'CONCURRENT_CONNECTIONS', 'BANDWIDTH', name='ratelimittype'), nullable=False),
        sa.Column('limit_value', sa.Integer(), nullable=False),
        sa.Column('window_size_seconds', sa.Integer(), nullable=False),
        sa.Column('security_policy_id', sa.Integer(), nullable=True),
        sa.Column('block_on_exceed', sa.Boolean(), nullable=False),
        sa.Column('reset_on_exceed', sa.Boolean(), nullable=False),
        sa.Column('notification_threshold', sa.Float(), nullable=True),
        sa.Column('current_count', sa.Integer(), nullable=False),
        sa.Column('window_start', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_reset_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.CheckConstraint('limit_value > 0', name='valid_limit_value'),
        sa.CheckConstraint('window_size_seconds > 0', name='valid_window_size'),
        sa.CheckConstraint('current_count >= 0', name='valid_current_count'),
        sa.CheckConstraint('notification_threshold >= 0.0 AND notification_threshold <= 1.0', name='valid_notification_threshold'),
        sa.ForeignKeyConstraint(['mcp_server_id'], ['mcp_servers.id'], ),
        sa.ForeignKeyConstraint(['security_policy_id'], ['security_policies.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Rate limit indexes
    op.create_index('ix_rate_limits_user_id', 'rate_limits', ['user_id'])
    op.create_index('ix_rate_limits_mcp_server_id', 'rate_limits', ['mcp_server_id'])
    op.create_index('ix_rate_limits_ip_address', 'rate_limits', ['ip_address'])
    op.create_index('ix_rate_limits_limit_type', 'rate_limits', ['limit_type'])
    op.create_index('ix_rate_limits_security_policy_id', 'rate_limits', ['security_policy_id'])
    op.create_index('ix_rate_limits_created_at', 'rate_limits', ['created_at'])
    op.create_index('idx_rate_limits_user_type', 'rate_limits', ['user_id', 'limit_type'])
    op.create_index('idx_rate_limits_server_type', 'rate_limits', ['mcp_server_id', 'limit_type'])
    op.create_index('idx_rate_limits_ip_type', 'rate_limits', ['ip_address', 'limit_type'])
    op.create_index('idx_rate_limits_endpoint_type', 'rate_limits', ['api_endpoint', 'limit_type'])
    op.create_index('idx_rate_limits_window', 'rate_limits', ['window_start', 'is_active'])

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('action_type', sa.Enum('CREATE', 'READ', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'PASSWORD_CHANGE', 'PERMISSION_CHANGE', 'SERVER_START', 'SERVER_STOP', 'SERVER_RESTART', 'CONFIG_CHANGE', 'SECURITY_VIOLATION', 'API_ACCESS', 'EXPORT', 'IMPORT', name='auditactiontype'), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', sa.String(100), nullable=True),
        sa.Column('mcp_server_id', sa.Integer(), nullable=True),
        sa.Column('target_user_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('request_path', sa.String(500), nullable=True),
        sa.Column('request_method', sa.String(10), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('request_data', sa.JSON(), nullable=True),
        sa.Column('response_data', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['mcp_server_id'], ['mcp_servers.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['user_sessions.id'], ),
        sa.ForeignKeyConstraint(['target_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Audit log indexes - optimized for common queries
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_session_id', 'audit_logs', ['session_id'])
    op.create_index('ix_audit_logs_ip_address', 'audit_logs', ['ip_address'])
    op.create_index('ix_audit_logs_action_type', 'audit_logs', ['action_type'])
    op.create_index('ix_audit_logs_resource_type', 'audit_logs', ['resource_type'])
    op.create_index('ix_audit_logs_resource_id', 'audit_logs', ['resource_id'])
    op.create_index('ix_audit_logs_mcp_server_id', 'audit_logs', ['mcp_server_id'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])
    
    # Composite indexes for performance
    op.create_index('idx_audit_logs_user_action', 'audit_logs', ['user_id', 'action_type'])
    op.create_index('idx_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('idx_audit_logs_server_action', 'audit_logs', ['mcp_server_id', 'action_type'])
    op.create_index('idx_audit_logs_created_action', 'audit_logs', ['created_at', 'action_type'])
    op.create_index('idx_audit_logs_ip_created', 'audit_logs', ['ip_address', 'created_at'])
    op.create_index('idx_audit_logs_success_created', 'audit_logs', ['success', 'created_at'])
    op.create_index('idx_audit_logs_user_created', 'audit_logs', ['user_id', 'created_at'])
    
    # Partial index for failed operations
    op.execute("""
        CREATE INDEX idx_audit_logs_failures 
        ON audit_logs (action_type, created_at) 
        WHERE success = false
    """)

    # Create security_events table
    op.create_table(
        'security_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('severity', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='securityeventseverity'), nullable=False),
        sa.Column('source', sa.String(100), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('threat_score', sa.Float(), nullable=True),
        sa.Column('indicators', sa.JSON(), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('request_path', sa.String(500), nullable=True),
        sa.Column('request_method', sa.String(10), nullable=True),
        sa.Column('request_headers', sa.JSON(), nullable=True),
        sa.Column('request_body', sa.Text(), nullable=True),
        sa.Column('country_code', sa.String(2), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('action_taken', sa.String(100), nullable=True),
        sa.Column('resolved', sa.Boolean(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by_id', sa.Integer(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('related_audit_log_id', sa.Integer(), nullable=True),
        sa.Column('external_reference', sa.String(255), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['related_audit_log_id'], ['audit_logs.id'], ),
        sa.ForeignKeyConstraint(['resolved_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Security event indexes
    op.create_index('ix_security_events_event_type', 'security_events', ['event_type'])
    op.create_index('ix_security_events_severity', 'security_events', ['severity'])
    op.create_index('ix_security_events_user_id', 'security_events', ['user_id'])
    op.create_index('ix_security_events_ip_address', 'security_events', ['ip_address'])
    op.create_index('ix_security_events_occurred_at', 'security_events', ['occurred_at'])
    
    # Composite indexes for security analytics
    op.create_index('idx_security_events_type_severity', 'security_events', ['event_type', 'severity'])
    op.create_index('idx_security_events_ip_occurred', 'security_events', ['ip_address', 'occurred_at'])
    op.create_index('idx_security_events_user_occurred', 'security_events', ['user_id', 'occurred_at'])
    op.create_index('idx_security_events_unresolved', 'security_events', ['resolved', 'severity', 'occurred_at'])
    op.create_index('idx_security_events_threat_score', 'security_events', ['threat_score', 'occurred_at'])
    op.create_index('idx_security_events_source_type', 'security_events', ['source', 'event_type'])
    
    # Partial index for high severity unresolved events
    op.execute("""
        CREATE INDEX idx_security_events_critical_unresolved 
        ON security_events (occurred_at, event_type) 
        WHERE severity IN ('HIGH', 'CRITICAL') AND resolved = false
    """)

    # Create audit_logs_archive table
    op.create_table(
        'audit_logs_archive',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('original_audit_log_id', sa.Integer(), nullable=False),
        sa.Column('audit_data', sa.JSON(), nullable=False),
        sa.Column('checksum', sa.String(64), nullable=False),
        sa.Column('archived_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('archive_reason', sa.String(100), nullable=False),
        sa.Column('retention_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('legal_hold', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_logs_archive_original_audit_log_id', 'audit_logs_archive', ['original_audit_log_id'])
    op.create_index('ix_audit_logs_archive_archived_at', 'audit_logs_archive', ['archived_at'])
    op.create_index('ix_audit_logs_archive_retention_until', 'audit_logs_archive', ['retention_until'])
    op.create_index('idx_audit_archive_original_id', 'audit_logs_archive', ['original_audit_log_id'])
    op.create_index('idx_audit_archive_retention', 'audit_logs_archive', ['retention_until', 'legal_hold'])

    # Create additional performance indexes for common query patterns
    
    # Time-based partitioning friendly indexes
    op.execute("""
        CREATE INDEX idx_audit_logs_monthly_partition 
        ON audit_logs (date_trunc('month', created_at), action_type)
    """)
    
    op.execute("""
        CREATE INDEX idx_security_events_monthly_partition 
        ON security_events (date_trunc('month', occurred_at), severity)
    """)
    
    # Full-text search indexes for log analysis
    op.execute("""
        CREATE INDEX idx_audit_logs_description_fts 
        ON audit_logs USING gin(to_tsvector('english', description))
    """)
    
    op.execute("""
        CREATE INDEX idx_security_events_description_fts 
        ON security_events USING gin(to_tsvector('english', description))
    """)


def downgrade():
    """Drop remaining tables in reverse order."""
    
    # Drop tables in reverse order
    op.drop_table('audit_logs_archive')
    op.drop_table('security_events')
    op.drop_table('audit_logs')
    op.drop_table('rate_limits')
    op.drop_table('access_controls')
    op.drop_table('configuration_history')
    op.drop_table('configurations')
    
    # Drop custom enum types
    op.execute('DROP TYPE IF EXISTS securityeventseverity')
    op.execute('DROP TYPE IF EXISTS auditactiontype')
    op.execute('DROP TYPE IF EXISTS ratelimittype')
    op.execute('DROP TYPE IF EXISTS configurationstatus')
    op.execute('DROP TYPE IF EXISTS configurationtype')
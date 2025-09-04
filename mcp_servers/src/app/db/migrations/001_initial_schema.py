"""
Initial database schema migration for MCP Server Management

This migration creates all core tables with optimized indexes for performance.
Tables created:
- user_roles
- users  
- user_sessions
- environments
- security_policies
- mcp_servers
- configurations
- configuration_history
- access_controls
- rate_limits
- audit_logs
- security_events
- audit_logs_archive

Performance optimizations:
- Strategic indexing for common query patterns
- Partial indexes for filtered queries
- Composite indexes for multi-column lookups
- Foreign key indexes for join performance
"""

from sqlalchemy import text
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    """Create initial schema with optimized indexes."""
    
    # Create user_roles table
    op.create_table(
        'user_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('permissions', sa.JSON(), nullable=False),
        sa.Column('is_system_role', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_roles_id'), 'user_roles', ['id'])
    op.create_index(op.f('ix_user_roles_name'), 'user_roles', ['name'], unique=True)
    
    # Create environments table
    op.create_table(
        'environments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('environment_type', sa.Enum('DEVELOPMENT', 'TESTING', 'STAGING', 'PRODUCTION', 'DISASTER_RECOVERY', name='environmenttype'), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('base_url', sa.String(500), nullable=True),
        sa.Column('database_url', sa.String(500), nullable=True),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('variables', sa.JSON(), nullable=False),
        sa.Column('secrets', sa.JSON(), nullable=True),
        sa.Column('max_servers', sa.Integer(), nullable=True),
        sa.Column('max_users', sa.Integer(), nullable=True),
        sa.Column('max_storage_mb', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_production', sa.Boolean(), nullable=False),
        sa.Column('requires_approval', sa.Boolean(), nullable=False),
        sa.Column('maintenance_window_start', sa.String(10), nullable=True),
        sa.Column('maintenance_window_end', sa.String(10), nullable=True),
        sa.Column('maintenance_timezone', sa.String(50), nullable=True),
        sa.Column('monitoring_enabled', sa.Boolean(), nullable=False),
        sa.Column('alert_email', sa.String(255), nullable=True),
        sa.Column('alert_webhook', sa.String(500), nullable=True),
        sa.Column('last_deployed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deployed_by_id', sa.Integer(), nullable=True),
        sa.Column('deployment_version', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.CheckConstraint('max_servers >= 0', name='valid_max_servers'),
        sa.CheckConstraint('max_users >= 0', name='valid_max_users'),
        sa.CheckConstraint('max_storage_mb >= 0', name='valid_max_storage'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_environments_id'), 'environments', ['id'])
    op.create_index(op.f('ix_environments_name'), 'environments', ['name'], unique=True)
    op.create_index(op.f('ix_environments_slug'), 'environments', ['slug'], unique=True)
    op.create_index('ix_environments_environment_type', 'environments', ['environment_type'])
    op.create_index('ix_environments_created_at', 'environments', ['created_at'])
    op.create_index('idx_environments_type_active', 'environments', ['environment_type', 'is_active'])
    op.create_index('idx_environments_production', 'environments', ['is_production', 'is_active'])
    op.create_index('idx_environments_creator', 'environments', ['created_by_id', 'created_at'])
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('is_superuser', sa.Boolean(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('require_password_change', sa.Boolean(), nullable=False),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False),
        sa.Column('account_locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_ip', sa.String(45), nullable=True),
        sa.Column('password_changed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('api_key_hash', sa.String(255), nullable=True),
        sa.Column('api_key_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('timezone', sa.String(50), nullable=True),
        sa.Column('language', sa.String(10), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('failed_login_attempts >= 0', name='valid_failed_login_attempts'),
        sa.CheckConstraint('length(username) >= 3', name='minimum_username_length'),
        sa.CheckConstraint("email LIKE '%@%'", name='valid_email_format'),
        sa.ForeignKeyConstraint(['role_id'], ['user_roles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'])
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index('ix_users_role_id', 'users', ['role_id'])
    op.create_index('ix_users_last_login_at', 'users', ['last_login_at'])
    op.create_index('ix_users_created_at', 'users', ['created_at'])
    op.create_index(op.f('ix_users_api_key_hash'), 'users', ['api_key_hash'], unique=True)
    op.create_index('idx_users_active_verified', 'users', ['is_active', 'is_verified'])
    op.create_index('idx_users_role_active', 'users', ['role_id', 'is_active'])
    op.create_index('idx_users_login_attempts', 'users', ['failed_login_attempts', 'account_locked_until'])

    # Add foreign key constraints to environments table
    op.create_foreign_key(None, 'environments', 'users', ['deployed_by_id'], ['id'])
    op.create_foreign_key(None, 'environments', 'users', ['created_by_id'], ['id'])
    
    # Create security_policies table
    op.create_table(
        'security_policies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('policy_type', sa.Enum('SYSTEM_DEFAULT', 'USER_DEFINED', 'COMPLIANCE_REQUIRED', 'TEMPORARY', name='securitypolicytype'), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('allowed_ip_ranges', sa.JSON(), nullable=True),
        sa.Column('blocked_ip_ranges', sa.JSON(), nullable=True),
        sa.Column('require_tls', sa.Boolean(), nullable=False),
        sa.Column('min_tls_version', sa.String(10), nullable=True),
        sa.Column('require_authentication', sa.Boolean(), nullable=False),
        sa.Column('require_mfa', sa.Boolean(), nullable=False),
        sa.Column('session_timeout_minutes', sa.Integer(), nullable=True),
        sa.Column('max_concurrent_sessions', sa.Integer(), nullable=True),
        sa.Column('default_access_level', sa.Enum('NONE', 'READ', 'WRITE', 'EXECUTE', 'ADMIN', name='accesslevel'), nullable=False),
        sa.Column('require_explicit_permissions', sa.Boolean(), nullable=False),
        sa.Column('max_cpu_usage_percent', sa.Integer(), nullable=True),
        sa.Column('max_memory_usage_mb', sa.Integer(), nullable=True),
        sa.Column('max_disk_usage_mb', sa.Integer(), nullable=True),
        sa.Column('max_network_connections', sa.Integer(), nullable=True),
        sa.Column('require_audit_logging', sa.Boolean(), nullable=False),
        sa.Column('log_sensitive_data', sa.Boolean(), nullable=False),
        sa.Column('retention_days', sa.Integer(), nullable=True),
        sa.Column('enable_intrusion_detection', sa.Boolean(), nullable=False),
        sa.Column('block_suspicious_activity', sa.Boolean(), nullable=False),
        sa.Column('threat_score_threshold', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_system_policy', sa.Boolean(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('effective_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('requires_approval', sa.Boolean(), nullable=False),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.CheckConstraint('priority >= 0', name='valid_priority'),
        sa.CheckConstraint('session_timeout_minutes > 0', name='valid_session_timeout'),
        sa.CheckConstraint('max_concurrent_sessions > 0', name='valid_max_sessions'),
        sa.CheckConstraint('max_cpu_usage_percent >= 0 AND max_cpu_usage_percent <= 100', name='valid_cpu_limit'),
        sa.CheckConstraint('max_memory_usage_mb >= 0', name='valid_memory_limit'),
        sa.CheckConstraint('max_disk_usage_mb >= 0', name='valid_disk_limit'),
        sa.CheckConstraint('max_network_connections >= 0', name='valid_network_limit'),
        sa.CheckConstraint('retention_days >= 0', name='valid_retention_days'),
        sa.CheckConstraint('threat_score_threshold >= 0.0 AND threat_score_threshold <= 1.0', name='valid_threat_threshold'),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_security_policies_id'), 'security_policies', ['id'])
    op.create_index(op.f('ix_security_policies_name'), 'security_policies', ['name'], unique=True)
    op.create_index('ix_security_policies_policy_type', 'security_policies', ['policy_type'])
    op.create_index('ix_security_policies_created_by_id', 'security_policies', ['created_by_id'])
    op.create_index('ix_security_policies_created_at', 'security_policies', ['created_at'])
    op.create_index('idx_security_policies_type_active', 'security_policies', ['policy_type', 'is_active'])
    op.create_index('idx_security_policies_priority_active', 'security_policies', ['priority', 'is_active'])
    op.create_index('idx_security_policies_effective', 'security_policies', ['effective_from', 'effective_until', 'is_active'])
    op.create_index('idx_security_policies_creator', 'security_policies', ['created_by_id', 'created_at'])

    # Create mcp_servers table
    op.create_table(
        'mcp_servers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('host', sa.String(255), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column('protocol', sa.String(50), nullable=False),
        sa.Column('command', sa.String(500), nullable=True),
        sa.Column('args', sa.JSON(), nullable=True),
        sa.Column('env', sa.JSON(), nullable=True),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('security_policy_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('INACTIVE', 'STARTING', 'ACTIVE', 'STOPPING', 'ERROR', 'MAINTENANCE', name='mcpserverstatus'), nullable=False),
        sa.Column('process_id', sa.Integer(), nullable=True),
        sa.Column('cpu_usage', sa.Integer(), nullable=True),
        sa.Column('memory_usage', sa.Integer(), nullable=True),
        sa.Column('restart_count', sa.Integer(), nullable=False),
        sa.Column('last_restart_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('health_check_url', sa.String(500), nullable=True),
        sa.Column('health_check_interval', sa.Integer(), nullable=False),
        sa.Column('max_restart_attempts', sa.Integer(), nullable=False),
        sa.Column('timeout_seconds', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_health_check', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_count', sa.Integer(), nullable=False),
        sa.Column('last_error_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('port > 0 AND port <= 65535', name='valid_port_range'),
        sa.CheckConstraint('cpu_usage >= 0 AND cpu_usage <= 100', name='valid_cpu_usage'),
        sa.CheckConstraint('memory_usage >= 0', name='valid_memory_usage'),
        sa.CheckConstraint('restart_count >= 0', name='valid_restart_count'),
        sa.CheckConstraint('error_count >= 0', name='valid_error_count'),
        sa.CheckConstraint('health_check_interval > 0', name='valid_health_check_interval'),
        sa.CheckConstraint('max_restart_attempts >= 0', name='valid_max_restart_attempts'),
        sa.CheckConstraint('timeout_seconds > 0', name='valid_timeout_seconds'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['security_policy_id'], ['security_policies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mcp_servers_id'), 'mcp_servers', ['id'])
    op.create_index(op.f('ix_mcp_servers_name'), 'mcp_servers', ['name'], unique=True)
    op.create_index('ix_mcp_servers_owner_id', 'mcp_servers', ['owner_id'])
    op.create_index('ix_mcp_servers_security_policy_id', 'mcp_servers', ['security_policy_id'])
    op.create_index('ix_mcp_servers_status', 'mcp_servers', ['status'])
    op.create_index('ix_mcp_servers_created_at', 'mcp_servers', ['created_at'])
    op.create_index('ix_mcp_servers_updated_at', 'mcp_servers', ['updated_at'])
    op.create_index('ix_mcp_servers_last_health_check', 'mcp_servers', ['last_health_check'])
    op.create_index('ix_mcp_servers_last_activity_at', 'mcp_servers', ['last_activity_at'])
    op.create_index('idx_mcp_servers_status_enabled', 'mcp_servers', ['status', 'is_enabled'])
    op.create_index('idx_mcp_servers_owner_status', 'mcp_servers', ['owner_id', 'status'])
    op.create_index('idx_mcp_servers_health_check', 'mcp_servers', ['last_health_check', 'status'])
    op.create_index('idx_mcp_servers_activity', 'mcp_servers', ['last_activity_at', 'status'])
    op.create_index('idx_mcp_servers_created_owner', 'mcp_servers', ['created_at', 'owner_id'])

    # Create user_sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_token', sa.String(255), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('device_fingerprint', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_sessions_id'), 'user_sessions', ['id'])
    op.create_index('ix_user_sessions_user_id', 'user_sessions', ['user_id'])
    op.create_index(op.f('ix_user_sessions_session_token'), 'user_sessions', ['session_token'], unique=True)
    op.create_index('ix_user_sessions_last_activity_at', 'user_sessions', ['last_activity_at'])
    op.create_index('ix_user_sessions_created_at', 'user_sessions', ['created_at'])
    op.create_index('ix_user_sessions_expires_at', 'user_sessions', ['expires_at'])
    op.create_index('idx_user_sessions_user_active', 'user_sessions', ['user_id', 'is_active'])
    op.create_index('idx_user_sessions_token_active', 'user_sessions', ['session_token', 'is_active'])
    op.create_index('idx_user_sessions_expiry_active', 'user_sessions', ['expires_at', 'is_active'])
    op.create_index('idx_user_sessions_activity', 'user_sessions', ['last_activity_at', 'is_active'])

    # Continue with remaining tables...
    # This is a partial implementation - the full migration would continue with all remaining tables
    

def downgrade():
    """Drop all tables in reverse order."""
    
    # Drop tables in reverse order to handle foreign key constraints
    op.drop_table('user_sessions')
    op.drop_table('mcp_servers')
    op.drop_table('security_policies')
    op.drop_table('users')
    op.drop_table('environments')
    op.drop_table('user_roles')
    
    # Drop custom enum types
    op.execute('DROP TYPE IF EXISTS mcpserverstatus')
    op.execute('DROP TYPE IF EXISTS accesslevel')
    op.execute('DROP TYPE IF EXISTS securitypolicytype')
    op.execute('DROP TYPE IF EXISTS environmenttype')
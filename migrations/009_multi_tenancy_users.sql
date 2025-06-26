-- Migration 009: Add Multi-Tenancy User Tables
-- This migration adds the missing tenant_users table and related tables

-- Ensure tenants table exists (in case migration 008 hasn't run yet)
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'trial', 'pending')),
    plan VARCHAR(50) DEFAULT 'free',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create default tenant if not exists
INSERT INTO tenants (id, name, slug, status, plan)
VALUES ('00000000-0000-0000-0000-000000000000', 'Default', 'default', 'active', 'enterprise')
ON CONFLICT (slug) DO NOTHING;

-- Create tenant_users table for user-tenant relationships
CREATE TABLE IF NOT EXISTS tenant_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    role VARCHAR(50) DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
    permissions JSONB DEFAULT '{}'::jsonb,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    invited_by UUID,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'pending', 'suspended')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, user_id)
);

-- Create users table if it doesn't exist
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(255) UNIQUE,
    full_name VARCHAR(255),
    password_hash VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}'::jsonb,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create tenant resource quotas table
CREATE TABLE IF NOT EXISTS tenant_resource_quotas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    resource_type VARCHAR(100) NOT NULL,
    quota_limit INTEGER NOT NULL,
    current_usage INTEGER DEFAULT 0,
    unit VARCHAR(50) DEFAULT 'count',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, resource_type)
);

-- Create tenant billing table
CREATE TABLE IF NOT EXISTS tenant_billing (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    stripe_customer_id VARCHAR(255),
    billing_email VARCHAR(255),
    payment_method VARCHAR(50),
    billing_cycle VARCHAR(50) DEFAULT 'monthly',
    next_billing_date DATE,
    amount_cents INTEGER,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_tenant_users_tenant_id ON tenant_users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_users_user_id ON tenant_users(user_id);
CREATE INDEX IF NOT EXISTS idx_tenant_users_status ON tenant_users(status);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_tenant_resource_quotas_tenant_id ON tenant_resource_quotas(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_billing_tenant_id ON tenant_billing(tenant_id);

-- Add RLS (Row Level Security) policies
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE departments ENABLE ROW LEVEL SECURITY;
ALTER TABLE divisions ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for agents
CREATE POLICY tenant_isolation_agents ON agents
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Create RLS policies for departments
CREATE POLICY tenant_isolation_departments ON departments
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Create RLS policies for divisions
CREATE POLICY tenant_isolation_divisions ON divisions
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Add comments for documentation
COMMENT ON TABLE tenant_users IS 'Maps users to tenants with roles and permissions';
COMMENT ON TABLE users IS 'User accounts for the system';
COMMENT ON TABLE tenant_resource_quotas IS 'Resource usage limits per tenant';
COMMENT ON TABLE tenant_billing IS 'Billing information and subscription details per tenant';
COMMENT ON COLUMN tenant_users.role IS 'User role within the tenant: owner, admin, member, viewer';
COMMENT ON COLUMN tenant_resource_quotas.resource_type IS 'Type of resource: agents, api_calls, storage_gb, etc.';
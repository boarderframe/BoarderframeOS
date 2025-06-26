-- Migration 008: Fix Missing Columns for Enhanced Features
-- This migration adds columns required by the enhanced startup process

-- Add development_status column to agents table if it doesn't exist
ALTER TABLE agents ADD COLUMN IF NOT EXISTS development_status VARCHAR(50) DEFAULT 'planned';

-- Add health_score column to agents table if it doesn't exist
ALTER TABLE agents ADD COLUMN IF NOT EXISTS health_score INTEGER DEFAULT 0 CHECK (health_score >= 0 AND health_score <= 100);

-- Add configuration column to divisions table if it doesn't exist
ALTER TABLE divisions ADD COLUMN IF NOT EXISTS configuration JSONB DEFAULT '{}'::jsonb;

-- Create leaders table if it doesn't exist
CREATE TABLE IF NOT EXISTS leaders (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    leadership_tier VARCHAR(50) NOT NULL,
    department_id UUID REFERENCES departments(id),
    active_status VARCHAR(50) DEFAULT 'hired',
    development_status VARCHAR(50) DEFAULT 'not_built',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create tenants table for multi-tenancy support
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

-- Add tenant_id to agents table for multi-tenancy
ALTER TABLE agents ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) DEFAULT '00000000-0000-0000-0000-000000000000';

-- Add tenant_id to other tables that need it
ALTER TABLE departments ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) DEFAULT '00000000-0000-0000-0000-000000000000';
ALTER TABLE divisions ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) DEFAULT '00000000-0000-0000-0000-000000000000';

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_agents_development_status ON agents(development_status);
CREATE INDEX IF NOT EXISTS idx_agents_health_score ON agents(health_score);
CREATE INDEX IF NOT EXISTS idx_agents_tenant_id ON agents(tenant_id);
CREATE INDEX IF NOT EXISTS idx_leaders_leadership_tier ON leaders(leadership_tier);
CREATE INDEX IF NOT EXISTS idx_tenants_slug ON tenants(slug);

-- Add comments for documentation
COMMENT ON COLUMN agents.development_status IS 'Development status: planned, in_development, implemented, operational, deployed';
COMMENT ON COLUMN agents.health_score IS 'Agent health score from 0-100';
COMMENT ON COLUMN divisions.configuration IS 'JSON configuration including visual metadata';
COMMENT ON COLUMN leaders.leadership_tier IS 'Leadership tier: executive, senior, middle, team_lead';
COMMENT ON TABLE tenants IS 'Multi-tenancy support table';
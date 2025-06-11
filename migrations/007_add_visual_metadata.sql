-- Migration: Add visual metadata (colors, icons) to departments and divisions
-- This migration updates the configuration/metadata JSONB columns to include visual styling

-- Update departments configuration to include color and icon
UPDATE departments
SET configuration = jsonb_set(
    COALESCE(configuration, '{}'::jsonb),
    '{visual}',
    '{}'::jsonb,
    true
)
WHERE configuration IS NULL OR configuration->>'visual' IS NULL;

-- Update department_registry metadata to include color and icon
UPDATE department_registry
SET metadata = jsonb_set(
    COALESCE(metadata, '{}'::jsonb),
    '{visual}',
    '{}'::jsonb,
    true
)
WHERE metadata IS NULL OR metadata->>'visual' IS NULL;

-- Add visual configuration to divisions (using the configuration pattern)
ALTER TABLE divisions
ADD COLUMN IF NOT EXISTS configuration JSONB DEFAULT '{}';

-- Create indexes for better JSONB query performance
CREATE INDEX IF NOT EXISTS idx_departments_visual ON departments ((configuration->'visual'));
CREATE INDEX IF NOT EXISTS idx_department_registry_visual ON department_registry ((metadata->'visual'));
CREATE INDEX IF NOT EXISTS idx_divisions_configuration ON divisions USING gin (configuration);

-- Add comments
COMMENT ON COLUMN departments.configuration IS 'Department configuration including visual metadata (color, icon, theme)';
COMMENT ON COLUMN department_registry.metadata IS 'Registry metadata including visual styling and display preferences';
COMMENT ON COLUMN divisions.configuration IS 'Division configuration including visual metadata (color, icon, theme)';

-- Sample structure for visual metadata:
-- {
--   "visual": {
--     "color": "#6366f1",
--     "icon": "fa-crown",
--     "theme": "executive",
--     "accent_color": "#4f46e5",
--     "custom_css": {}
--   }
-- }

-- Add product type support to idea_banks table
-- Date: 2025-01-28
-- Description: Update idea_banks table to support product type with product_name and product_description fields

-- Update the comment to reflect the new schema
COMMENT ON COLUMN public.idea_banks.data IS 'JSON field containing idea data: {"type": "article|text|product", "value": "string", "title": "string", "product_name": "string", "product_description": "string", "time_sensitive": boolean, "ai_suggested": boolean}';

-- Add constraint to validate the type field
-- This is for documentation purposes as we rely on application-level validation 
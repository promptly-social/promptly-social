-- Migration: Update writing_style_analysis schema
-- Drop old unique constraint on (user_id, platform) if it exists
-- Ensure there is a single analysis per user by adding unique constraint on user_id

ALTER TABLE writing_style_analysis
DROP CONSTRAINT IF EXISTS writing_style_analysis_user_id_platform_key;

-- Remove composite index on (user_id, source) created previously if you prefer a simple unique user_id. Comment out if you want to keep it for querying by source.
DROP INDEX IF EXISTS idx_writing_style_analysis_user_source;

-- Add unique constraint on user_id
ALTER TABLE writing_style_analysis
ADD CONSTRAINT writing_style_analysis_user_id_key UNIQUE (user_id); 

-- 1. Drop obsolete columns `platform` and `content_count`
-- 2. Add new column `source` to track writing sample origin


ALTER TABLE writing_style_analysis
DROP COLUMN IF EXISTS platform,
DROP COLUMN IF EXISTS content_count;

ALTER TABLE writing_style_analysis
ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT 'import';

-- Optionally, create an index for faster lookup
CREATE INDEX IF NOT EXISTS idx_writing_style_analysis_user_source
    ON writing_style_analysis (user_id, source); 
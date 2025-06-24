-- Migration: Update suggested_posts table and drop unnecessary tables

-- =============================================================================
-- UPDATE SUGGESTED_POSTS TABLE
-- =============================================================================

-- Drop existing foreign key constraint and indices that reference scraped_content
DROP INDEX IF EXISTS idx_suggested_posts_topics;
ALTER TABLE public.suggested_posts DROP CONSTRAINT IF EXISTS suggested_posts_original_source_id_fkey;

-- Drop columns that are no longer needed
ALTER TABLE public.suggested_posts 
    DROP COLUMN IF EXISTS original_source_id,
    DROP COLUMN IF EXISTS relevance_score;

-- Add new columns
ALTER TABLE public.suggested_posts 
    ADD COLUMN idea_bank_id UUID REFERENCES public.idea_banks(id),
    ADD COLUMN recommendation_score INTEGER DEFAULT 0,
    ADD COLUMN platform TEXT NOT NULL DEFAULT 'linkedin';

-- Make title column nullable
ALTER TABLE public.suggested_posts 
    ALTER COLUMN title DROP NOT NULL;

-- =============================================================================
-- DROP UNNECESSARY TABLES
-- =============================================================================

-- Drop scraped_content table and its dependencies
DROP INDEX IF EXISTS idx_scraped_content_user_id;
DROP INDEX IF EXISTS idx_scraped_content_topics;
DROP TABLE IF EXISTS public.scraped_content CASCADE;

-- Drop imported_content table
DROP TABLE IF EXISTS public.imported_content CASCADE;

-- =============================================================================
-- RECREATE INDEXES
-- =============================================================================

-- Recreate the topics index for suggested_posts
CREATE INDEX idx_suggested_posts_topics ON public.suggested_posts USING GIN (topics);

-- Add index for the new columns
CREATE INDEX idx_suggested_posts_idea_bank_id ON public.suggested_posts(idea_bank_id);
CREATE INDEX idx_suggested_posts_platform ON public.suggested_posts(platform);
CREATE INDEX idx_suggested_posts_recommendation_score ON public.suggested_posts(recommendation_score DESC); 
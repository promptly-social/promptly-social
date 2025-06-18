-- Migration: Refactor content_ideas to contents and create publications table
-- Date: 2025-01-20
-- Description: Split publication data from content_ideas into separate publications table

BEGIN;

-- 1. Create the new publications table first
CREATE TABLE publications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID NOT NULL, -- Will be updated after table rename
    platform VARCHAR(50) NOT NULL,
    post_id VARCHAR(255), -- Platform-specific post ID (e.g., LinkedIn post ID)
    scheduled_date TIMESTAMPTZ,
    published_date TIMESTAMPTZ,
    publication_error TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'scheduled', 'published', 'canceled', 'error')),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 2. Create indexes for the publications table
CREATE INDEX idx_publications_content_id ON publications(content_id);
CREATE INDEX idx_publications_platform ON publications(platform);
CREATE INDEX idx_publications_status ON publications(status);
CREATE INDEX idx_publications_scheduled_date ON publications(scheduled_date);
CREATE INDEX idx_publications_published_date ON publications(published_date);

-- 3. Migrate existing publication data from content_ideas to publications
-- Only migrate records that have publication-related data
INSERT INTO publications (content_id, platform, post_id, scheduled_date, published_date, publication_error, status, created_at, updated_at)
SELECT 
    id as content_id,
    CASE 
        WHEN linkedin_post_id IS NOT NULL THEN 'linkedin'
        ELSE 'unknown'
    END as platform,
    linkedin_post_id as post_id,
    scheduled_date,
    published_date,
    publication_error,
    CASE 
        WHEN published_date IS NOT NULL THEN 'published'
        WHEN scheduled_date IS NOT NULL THEN 'scheduled'
        WHEN publication_error IS NOT NULL THEN 'error'
        ELSE 'pending'
    END as status,
    created_at,
    updated_at
FROM content_ideas 
WHERE linkedin_post_id IS NOT NULL 
   OR scheduled_date IS NOT NULL 
   OR published_date IS NOT NULL 
   OR publication_error IS NOT NULL;

-- 4. Rename content_ideas table to contents
ALTER TABLE content_ideas RENAME TO contents;

-- 5. Drop the publication-related columns from contents table
ALTER TABLE contents 
    DROP COLUMN IF EXISTS scheduled_date,
    DROP COLUMN IF EXISTS published_date,
    DROP COLUMN IF EXISTS publication_error,
    DROP COLUMN IF EXISTS linkedin_post_id;

-- 6. Add foreign key constraint to publications table
ALTER TABLE publications 
    ADD CONSTRAINT fk_publications_content_id 
    FOREIGN KEY (content_id) REFERENCES contents(id) 
    ON DELETE CASCADE;

-- 7. Update the suggested_posts table foreign key reference
ALTER TABLE suggested_posts 
    RENAME COLUMN content_idea_id TO content_id;

-- Add foreign key constraint for suggested_posts if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_suggested_posts_content_id'
    ) THEN
        ALTER TABLE suggested_posts 
            ADD CONSTRAINT fk_suggested_posts_content_id 
            FOREIGN KEY (content_id) REFERENCES contents(id) 
            ON DELETE SET NULL;
    END IF;
END $$;

-- 8. Create updated_at trigger for publications table
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_publications_updated_at 
    BEFORE UPDATE ON publications 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 9. Update any existing RLS policies if they exist
-- Drop old policies for content_ideas (they won't apply to contents)
DROP POLICY IF EXISTS "Users can view their own content ideas" ON content_ideas;
DROP POLICY IF EXISTS "Users can insert their own content ideas" ON content_ideas;
DROP POLICY IF EXISTS "Users can update their own content ideas" ON content_ideas;
DROP POLICY IF EXISTS "Users can delete their own content ideas" ON content_ideas;

-- Create new RLS policies for contents table
ALTER TABLE contents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own content" ON contents
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert their own content" ON contents
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update their own content" ON contents
    FOR UPDATE USING (auth.uid()::text = user_id);

CREATE POLICY "Users can delete their own content" ON contents
    FOR DELETE USING (auth.uid()::text = user_id);

-- Create RLS policies for publications table
ALTER TABLE publications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view publications for their content" ON publications
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM contents 
            WHERE contents.id = publications.content_id 
            AND contents.user_id = auth.uid()::text
        )
    );

CREATE POLICY "Users can insert publications for their content" ON publications
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM contents 
            WHERE contents.id = content_id 
            AND contents.user_id = auth.uid()::text
        )
    );

CREATE POLICY "Users can update publications for their content" ON publications
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM contents 
            WHERE contents.id = publications.content_id 
            AND contents.user_id = auth.uid()::text
        )
    );

CREATE POLICY "Users can delete publications for their content" ON publications
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM contents 
            WHERE contents.id = publications.content_id 
            AND contents.user_id = auth.uid()::text
        )
    );

COMMIT; 
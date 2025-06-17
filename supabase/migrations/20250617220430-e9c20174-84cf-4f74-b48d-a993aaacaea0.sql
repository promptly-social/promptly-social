
-- Add scheduling columns to content_ideas table
ALTER TABLE public.content_ideas 
ADD COLUMN IF NOT EXISTS status TEXT CHECK (status IN ('draft', 'approved', 'scheduled', 'published', 'failed')) DEFAULT 'draft',
ADD COLUMN IF NOT EXISTS scheduled_date TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS published_date TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS publication_error TEXT,
ADD COLUMN IF NOT EXISTS linkedin_post_id TEXT;

-- Create index for scheduled posts
CREATE INDEX IF NOT EXISTS idx_content_ideas_scheduled 
ON content_ideas (scheduled_date) 
WHERE status = 'scheduled';

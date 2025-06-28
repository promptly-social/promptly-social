-- Add posted_at column to posts table
ALTER TABLE public.posts ADD COLUMN posted_at TIMESTAMPTZ NULL;

-- Create index for scheduled posts query performance
CREATE INDEX idx_posts_posted_at ON public.posts(posted_at) WHERE posted_at IS NOT NULL;

-- Create index for scheduled posts by status and posted_at
CREATE INDEX idx_posts_status_posted_at ON public.posts(status, posted_at) WHERE posted_at IS NOT NULL; 
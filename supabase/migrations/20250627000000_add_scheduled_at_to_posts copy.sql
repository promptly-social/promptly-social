-- Add scheduled_at column to posts table
ALTER TABLE public.posts ADD COLUMN scheduled_at TIMESTAMPTZ NULL;

-- Create index for scheduled posts query performance
CREATE INDEX idx_posts_scheduled_at ON public.posts(scheduled_at) WHERE scheduled_at IS NOT NULL;

-- Create index for scheduled posts by status and scheduled_at
CREATE INDEX idx_posts_status_scheduled_at ON public.posts(status, scheduled_at) WHERE scheduled_at IS NOT NULL; 
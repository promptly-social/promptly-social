-- Add additional fields needed for post scheduling and sharing functionality
ALTER TABLE public.posts ADD COLUMN scheduler_job_name VARCHAR(255) NULL;
ALTER TABLE public.posts ADD COLUMN linkedin_post_id VARCHAR(255) NULL;
ALTER TABLE public.posts ADD COLUMN sharing_error TEXT NULL;

-- Create index for scheduler job name lookups
CREATE INDEX idx_posts_scheduler_job_name ON public.posts(scheduler_job_name) WHERE scheduler_job_name IS NOT NULL;

-- Create index for LinkedIn post ID lookups
CREATE INDEX idx_posts_linkedin_post_id ON public.posts(linkedin_post_id) WHERE linkedin_post_id IS NOT NULL;

-- Create composite index for scheduled posts that need to be processed
CREATE INDEX idx_posts_scheduled_pending ON public.posts(scheduled_at, status) WHERE scheduled_at IS NOT NULL AND status = 'scheduled';
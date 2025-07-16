-- Create the new post_media table
CREATE TABLE IF NOT EXISTS public.post_media (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    post_id uuid NOT NULL,
    user_id uuid NOT NULL,
    media_type text,
    file_name text,
    storage_path text,
    gcs_url text,
    linkedin_asset_urn text,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    CONSTRAINT post_media_pkey PRIMARY KEY (id),
    CONSTRAINT post_media_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.posts(id) ON DELETE CASCADE,
    CONSTRAINT post_media_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_post_media_post_id ON public.post_media(post_id);
CREATE INDEX IF NOT EXISTS idx_post_media_user_id ON public.post_media(user_id);

-- Enable RLS
ALTER TABLE public.post_media ENABLE ROW LEVEL SECURITY;

-- RLS Policies for post_media
DROP POLICY IF EXISTS "Allow full access to own media" ON public.post_media;
CREATE POLICY "Allow full access to own media" ON public.post_media
    FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Drop old columns from posts table
ALTER TABLE IF EXISTS public.posts DROP COLUMN IF EXISTS media_type;
ALTER TABLE IF EXISTS public.posts DROP COLUMN IF EXISTS media_url;
ALTER TABLE IF EXISTS public.posts DROP COLUMN IF EXISTS linkedin_asset_urn;

-- Function to update 'updated_at' timestamp
-- This function is also defined in 20250624000003_add_updated_at_to_suggested_posts.sql
-- We use CREATE OR REPLACE to avoid errors if it already exists.
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for post_media
CREATE TRIGGER trigger_update_post_media_updated_at
BEFORE UPDATE ON public.post_media
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column(); 
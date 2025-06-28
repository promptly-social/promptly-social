-- Drop contents and publications tables
DROP TABLE IF EXISTS public.contents CASCADE;
DROP TABLE IF EXISTS public.publications CASCADE;

-- Rename suggested_posts table to posts
ALTER TABLE public.suggested_posts RENAME TO posts;

-- Update indexes to match new table name
DROP INDEX IF EXISTS idx_suggested_posts_user_id;
DROP INDEX IF EXISTS idx_suggested_posts_topics;
DROP INDEX IF EXISTS idx_suggested_posts_idea_bank_id;
DROP INDEX IF EXISTS idx_suggested_posts_platform;
DROP INDEX IF EXISTS idx_suggested_posts_recommendation_score;
DROP INDEX IF EXISTS idx_suggested_posts_user_feedback;
DROP INDEX IF EXISTS idx_suggested_posts_updated_at;

-- Recreate indexes with new table name
CREATE INDEX idx_posts_user_id ON public.posts(user_id);
CREATE INDEX idx_posts_topics ON public.posts USING GIN (topics);
CREATE INDEX idx_posts_idea_bank_id ON public.posts(idea_bank_id);
CREATE INDEX idx_posts_platform ON public.posts(platform);
CREATE INDEX idx_posts_recommendation_score ON public.posts(recommendation_score DESC);
CREATE INDEX idx_posts_user_feedback ON public.posts(user_feedback) WHERE user_feedback IS NOT NULL;
CREATE INDEX idx_posts_updated_at ON public.posts(updated_at DESC);

-- Update RLS policies to match new table name
DROP POLICY IF EXISTS "suggested_posts_select_policy" ON public.posts;
DROP POLICY IF EXISTS "suggested_posts_insert_policy" ON public.posts;
DROP POLICY IF EXISTS "suggested_posts_update_policy" ON public.posts;

CREATE POLICY "posts_select_policy" 
ON public.posts FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "posts_insert_policy" 
ON public.posts FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "posts_update_policy" 
ON public.posts FOR UPDATE 
USING (auth.uid() = user_id);

-- Update trigger name
DROP TRIGGER IF EXISTS trigger_update_suggested_posts_updated_at ON public.posts;
CREATE TRIGGER trigger_update_posts_updated_at
    BEFORE UPDATE ON public.posts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create content_strategies table
CREATE TABLE public.content_strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    platform TEXT NOT NULL,
    strategy TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Enable RLS for content_strategies
ALTER TABLE public.content_strategies ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for content_strategies
CREATE POLICY "content_strategies_select_policy" 
ON public.content_strategies FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "content_strategies_insert_policy" 
ON public.content_strategies FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "content_strategies_update_policy" 
ON public.content_strategies FOR UPDATE 
USING (auth.uid() = user_id);

CREATE POLICY "content_strategies_delete_policy" 
ON public.content_strategies FOR DELETE 
USING (auth.uid() = user_id);

-- Create indexes for content_strategies
CREATE INDEX idx_content_strategies_user_id ON public.content_strategies(user_id);
CREATE INDEX idx_content_strategies_platform ON public.content_strategies(platform);

-- Create trigger for content_strategies updated_at
CREATE TRIGGER trigger_update_content_strategies_updated_at
    BEFORE UPDATE ON public.content_strategies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column(); 
-- Fix content_strategies table user_id reference to point to public.users instead of auth.users

-- Drop the existing foreign key constraint
ALTER TABLE public.content_strategies
DROP CONSTRAINT IF EXISTS content_strategies_user_id_fkey;

-- Clean up orphaned content strategies before adding the new constraint
DELETE FROM public.content_strategies
WHERE user_id NOT IN (SELECT id FROM public.users);

-- Add the new foreign key constraint to reference public.users
ALTER TABLE public.content_strategies
ADD CONSTRAINT content_strategies_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;

-- Add an index for better performance
CREATE INDEX IF NOT EXISTS idx_content_strategies_user_id 
ON public.content_strategies(user_id);

-- Add unique constraint to prevent duplicate platform strategies per user
ALTER TABLE public.content_strategies
ADD CONSTRAINT content_strategies_user_platform_unique 
UNIQUE (user_id, platform); 
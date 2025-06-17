
-- Drop the existing unique constraint on user_id only
ALTER TABLE public.writing_style_analysis DROP CONSTRAINT IF EXISTS writing_style_analysis_user_id_key;

-- Add platform column to writing_style_analysis table
ALTER TABLE public.writing_style_analysis ADD COLUMN IF NOT EXISTS platform TEXT CHECK (platform IN ('substack', 'linkedin'));

-- Update the constraint to be unique on user_id + platform combination
ALTER TABLE public.writing_style_analysis ADD CONSTRAINT writing_style_analysis_user_id_platform_key UNIQUE (user_id, platform);

-- Update existing records to have a default platform (if any exist)
UPDATE public.writing_style_analysis SET platform = 'substack' WHERE platform IS NULL;

-- Make platform column NOT NULL after setting default values
ALTER TABLE public.writing_style_analysis ALTER COLUMN platform SET NOT NULL;

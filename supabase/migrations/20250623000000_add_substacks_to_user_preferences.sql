-- Add substacks column to user_preferences table and migrate existing data

-- Add the new substacks column
ALTER TABLE public.user_preferences 
ADD COLUMN substacks TEXT[] DEFAULT '{}';

-- Migrate data from websites column to substacks column
UPDATE public.user_preferences 
SET substacks = websites 
WHERE websites IS NOT NULL AND array_length(websites, 1) > 0;

-- Add comment for documentation
COMMENT ON COLUMN public.user_preferences.substacks IS 'Array of favorite Substack newsletter URLs or names'; 

-- Create a table to store content ideas and their generated outlines
CREATE TABLE public.content_ideas (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users NOT NULL,
  title TEXT NOT NULL,
  original_input TEXT NOT NULL,
  input_type TEXT NOT NULL CHECK (input_type IN ('text', 'audio')),
  generated_outline JSONB,
  content_type TEXT NOT NULL CHECK (content_type IN ('blog_post', 'linkedin_post')),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Add Row Level Security (RLS) to ensure users can only see their own content ideas
ALTER TABLE public.content_ideas ENABLE ROW LEVEL SECURITY;

-- Create policy that allows users to SELECT their own content ideas
CREATE POLICY "Users can view their own content ideas" 
  ON public.content_ideas 
  FOR SELECT 
  USING (auth.uid() = user_id);

-- Create policy that allows users to INSERT their own content ideas
CREATE POLICY "Users can create their own content ideas" 
  ON public.content_ideas 
  FOR INSERT 
  WITH CHECK (auth.uid() = user_id);

-- Create policy that allows users to UPDATE their own content ideas
CREATE POLICY "Users can update their own content ideas" 
  ON public.content_ideas 
  FOR UPDATE 
  USING (auth.uid() = user_id);

-- Create policy that allows users to DELETE their own content ideas
CREATE POLICY "Users can delete their own content ideas" 
  ON public.content_ideas 
  FOR DELETE 
  USING (auth.uid() = user_id);

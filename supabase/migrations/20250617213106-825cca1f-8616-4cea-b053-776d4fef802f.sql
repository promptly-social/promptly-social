
-- Create a table to store social media connections
CREATE TABLE public.social_connections (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users NOT NULL,
  platform TEXT NOT NULL CHECK (platform IN ('substack', 'linkedin')),
  platform_username TEXT,
  connection_data JSONB,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  UNIQUE(user_id, platform)
);

-- Create a table to store imported content for analysis
CREATE TABLE public.imported_content (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users NOT NULL,
  platform TEXT NOT NULL CHECK (platform IN ('substack', 'linkedin')),
  title TEXT,
  content TEXT NOT NULL,
  published_date TIMESTAMP WITH TIME ZONE,
  source_url TEXT,
  metadata JSONB,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create a table to store writing style analysis
CREATE TABLE public.writing_style_analysis (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users NOT NULL,
  analysis_data JSONB NOT NULL,
  content_count INTEGER NOT NULL DEFAULT 0,
  last_analyzed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  UNIQUE(user_id)
);

-- Add Row Level Security (RLS) policies
ALTER TABLE public.social_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.imported_content ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.writing_style_analysis ENABLE ROW LEVEL SECURITY;

-- Social connections policies
CREATE POLICY "Users can view their own social connections" 
  ON public.social_connections 
  FOR SELECT 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own social connections" 
  ON public.social_connections 
  FOR INSERT 
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own social connections" 
  ON public.social_connections 
  FOR UPDATE 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own social connections" 
  ON public.social_connections 
  FOR DELETE 
  USING (auth.uid() = user_id);

-- Imported content policies
CREATE POLICY "Users can view their own imported content" 
  ON public.imported_content 
  FOR SELECT 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own imported content" 
  ON public.imported_content 
  FOR INSERT 
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own imported content" 
  ON public.imported_content 
  FOR UPDATE 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own imported content" 
  ON public.imported_content 
  FOR DELETE 
  USING (auth.uid() = user_id);

-- Writing style analysis policies
CREATE POLICY "Users can view their own writing style analysis" 
  ON public.writing_style_analysis 
  FOR SELECT 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own writing style analysis" 
  ON public.writing_style_analysis 
  FOR INSERT 
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own writing style analysis" 
  ON public.writing_style_analysis 
  FOR UPDATE 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own writing style analysis" 
  ON public.writing_style_analysis 
  FOR DELETE 
  USING (auth.uid() = user_id);

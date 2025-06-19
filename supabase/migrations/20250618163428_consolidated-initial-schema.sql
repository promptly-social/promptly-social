-- Consolidated migration - combines all previous migrations

-- =============================================================================
-- CONTENT IDEAS TABLE
-- =============================================================================

-- Create a table to store content ideas and their generated outlines
CREATE TABLE public.content_ideas (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES public.users NOT NULL,
  title TEXT NOT NULL,
  generated_outline JSONB,
  content_type TEXT NOT NULL CHECK (content_type IN ('blog_post', 'linkedin_post')),
  -- Scheduling columns (from migration 4)
  status TEXT CHECK (status IN ('draft', 'approved', 'scheduled', 'published', 'failed')) DEFAULT 'draft',
  scheduled_date TIMESTAMP WITH TIME ZONE,
  published_date TIMESTAMP WITH TIME ZONE,
  publication_error TEXT,
  linkedin_post_id TEXT,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Add Row Level Security (RLS)
ALTER TABLE public.content_ideas ENABLE ROW LEVEL SECURITY;

-- Content ideas policies
CREATE POLICY "Users can view their own content ideas" 
  ON public.content_ideas 
  FOR SELECT 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own content ideas" 
  ON public.content_ideas 
  FOR INSERT 
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own content ideas" 
  ON public.content_ideas 
  FOR UPDATE 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own content ideas" 
  ON public.content_ideas 
  FOR DELETE 
  USING (auth.uid() = user_id);

-- Create index for scheduled posts
CREATE INDEX idx_content_ideas_scheduled 
ON content_ideas (scheduled_date) 
WHERE status = 'scheduled';


-- =============================================================================
-- SOCIAL CONNECTIONS TABLE
-- =============================================================================

-- Create a table to store social media connections
CREATE TABLE public.social_connections (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES public.users NOT NULL,
  platform TEXT NOT NULL CHECK (platform IN ('substack', 'linkedin')),
  platform_username TEXT,
  connection_data JSONB,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  UNIQUE(user_id, platform)
);

-- Add Row Level Security (RLS)
ALTER TABLE public.social_connections ENABLE ROW LEVEL SECURITY;

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

-- =============================================================================
-- IMPORTED CONTENT TABLE
-- =============================================================================

-- Create a table to store imported content for analysis
CREATE TABLE public.imported_content (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES public.users NOT NULL,
  platform TEXT NOT NULL CHECK (platform IN ('substack', 'linkedin')),
  title TEXT,
  content TEXT NOT NULL,
  published_date TIMESTAMP WITH TIME ZONE,
  source_url TEXT,
  metadata JSONB,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Add Row Level Security (RLS)
ALTER TABLE public.imported_content ENABLE ROW LEVEL SECURITY;

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

-- =============================================================================
-- WRITING STYLE ANALYSIS TABLE
-- =============================================================================

-- Create a table to store writing style analysis
CREATE TABLE public.writing_style_analysis (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES public.users NOT NULL,
  platform TEXT NOT NULL CHECK (platform IN ('substack', 'linkedin')),
  analysis_data TEXT NOT NULL DEFAULT '',
  content_count INTEGER NOT NULL DEFAULT 0,
  last_analyzed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  UNIQUE(user_id, platform)
);

-- Add Row Level Security (RLS)
ALTER TABLE public.writing_style_analysis ENABLE ROW LEVEL SECURITY;

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

-- =============================================================================
-- USER PREFERENCES TABLE
-- =============================================================================

-- Add user preferences table
CREATE TABLE public.user_preferences (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES public.users NOT NULL,
  topics_of_interest TEXT[] DEFAULT '{}',
  websites TEXT[] DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  UNIQUE(user_id)
);

-- Add Row Level Security (RLS)
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;

-- User preferences policies
CREATE POLICY "Users can view their own preferences" 
  ON public.user_preferences 
  FOR SELECT 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own preferences" 
  ON public.user_preferences 
  FOR INSERT 
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own preferences" 
  ON public.user_preferences 
  FOR UPDATE 
  USING (auth.uid() = user_id);

-- =============================================================================
-- SCRAPED CONTENT TABLE
-- =============================================================================

-- Add scraped content table
CREATE TABLE public.scraped_content (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES public.users NOT NULL,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  source_url TEXT NOT NULL,
  source_type TEXT NOT NULL, -- 'website', 'substack', etc.
  topics TEXT[] DEFAULT '{}',
  scraped_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  relevance_score DECIMAL DEFAULT 0,
  suggested_for_linkedin BOOLEAN DEFAULT false
);

-- Add Row Level Security (RLS)
ALTER TABLE public.scraped_content ENABLE ROW LEVEL SECURITY;

-- Scraped content policies
CREATE POLICY "Users can view their own scraped content" 
  ON public.scraped_content 
  FOR SELECT 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own scraped content" 
  ON public.scraped_content 
  FOR INSERT 
  WITH CHECK (auth.uid() = user_id);

-- =============================================================================
-- SUGGESTED POSTS TABLE
-- =============================================================================

-- Add suggested posts table
CREATE TABLE public.suggested_posts (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES public.users NOT NULL,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  original_source_id UUID REFERENCES public.scraped_content(id),
  relevance_score DECIMAL NOT NULL,
  topics TEXT[] DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  status TEXT DEFAULT 'suggested' -- 'suggested', 'posted', 'dismissed'
);

-- Add Row Level Security (RLS)
ALTER TABLE public.suggested_posts ENABLE ROW LEVEL SECURITY;

-- Suggested posts policies
CREATE POLICY "Users can view their own suggested posts" 
  ON public.suggested_posts 
  FOR SELECT 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own suggested posts" 
  ON public.suggested_posts 
  FOR INSERT 
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own suggested posts" 
  ON public.suggested_posts 
  FOR UPDATE 
  USING (auth.uid() = user_id);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Add indexes for better performance
CREATE INDEX idx_scraped_content_user_id ON public.scraped_content(user_id);
CREATE INDEX idx_suggested_posts_user_id ON public.suggested_posts(user_id);
CREATE INDEX idx_scraped_content_topics ON public.scraped_content USING GIN (topics);
CREATE INDEX idx_suggested_posts_topics ON public.suggested_posts USING GIN (topics); 
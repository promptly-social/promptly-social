
-- Add user preferences table
CREATE TABLE public.user_preferences (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL,
  topics_of_interest TEXT[] DEFAULT '{}',
  websites TEXT[] DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  UNIQUE(user_id)
);

-- Add scraped content table
CREATE TABLE public.scraped_content (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  source_url TEXT NOT NULL,
  source_type TEXT NOT NULL, -- 'website', 'substack', etc.
  topics TEXT[] DEFAULT '{}',
  scraped_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  relevance_score DECIMAL DEFAULT 0,
  suggested_for_linkedin BOOLEAN DEFAULT false
);

-- Add suggested posts table
CREATE TABLE public.suggested_posts (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  original_source_id UUID REFERENCES public.scraped_content(id),
  relevance_score DECIMAL NOT NULL,
  topics TEXT[] DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  status TEXT DEFAULT 'suggested' -- 'suggested', 'posted', 'dismissed'
);

-- Add RLS policies
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scraped_content ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.suggested_posts ENABLE ROW LEVEL SECURITY;

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

-- Scraped content policies
CREATE POLICY "Users can view their own scraped content" 
  ON public.scraped_content 
  FOR SELECT 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own scraped content" 
  ON public.scraped_content 
  FOR INSERT 
  WITH CHECK (auth.uid() = user_id);

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

-- Add indexes for better performance
CREATE INDEX idx_scraped_content_user_id ON public.scraped_content(user_id);
CREATE INDEX idx_suggested_posts_user_id ON public.suggested_posts(user_id);
CREATE INDEX idx_scraped_content_topics ON public.scraped_content USING GIN (topics);
CREATE INDEX idx_suggested_posts_topics ON public.suggested_posts USING GIN (topics);

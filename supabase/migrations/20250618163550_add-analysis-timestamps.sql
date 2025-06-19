-- Add analysis timestamp columns to social_connections table
-- These columns will track when analysis is started and completed

ALTER TABLE public.social_connections 
ADD COLUMN analysis_started_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN analysis_completed_at TIMESTAMP WITH TIME ZONE;

-- Add indexes for better query performance
CREATE INDEX idx_social_connections_analysis_started 
ON public.social_connections (analysis_started_at) 
WHERE analysis_started_at IS NOT NULL;

CREATE INDEX idx_social_connections_analysis_completed 
ON public.social_connections (analysis_completed_at) 
WHERE analysis_completed_at IS NOT NULL;

-- Add a partial index for active substack connections with ongoing analysis
CREATE INDEX idx_social_connections_substack_analysis 
ON public.social_connections (user_id, analysis_started_at) 
WHERE platform = 'substack' AND is_active = true AND analysis_started_at IS NOT NULL AND analysis_completed_at IS NULL; 
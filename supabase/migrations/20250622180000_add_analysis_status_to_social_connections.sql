ALTER TABLE social_connections
ADD COLUMN IF NOT EXISTS analysis_status text NOT NULL DEFAULT 'not_started'; 
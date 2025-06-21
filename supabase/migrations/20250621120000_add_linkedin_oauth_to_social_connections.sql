ALTER TABLE social_connections
ADD COLUMN access_token TEXT,
ADD COLUMN refresh_token TEXT,
ADD COLUMN expires_at TIMESTAMPTZ,
ADD COLUMN scope TEXT; 
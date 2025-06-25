-- Add updated_at column to suggested_posts table
ALTER TABLE suggested_posts 
ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL;

-- Create or replace function to update the updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update updated_at on row updates
CREATE TRIGGER trigger_update_suggested_posts_updated_at
    BEFORE UPDATE ON suggested_posts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add index for updated_at queries
CREATE INDEX idx_suggested_posts_updated_at ON suggested_posts(updated_at DESC); 
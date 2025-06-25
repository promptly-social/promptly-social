-- Add updated_at column to suggested_posts table
ALTER TABLE suggested_posts 
ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

-- Update existing rows to have updated_at = created_at
UPDATE suggested_posts 
SET updated_at = created_at 
WHERE updated_at IS NULL;

-- Create a trigger to automatically update the updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_suggested_posts_updated_at 
    BEFORE UPDATE ON suggested_posts 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column(); 
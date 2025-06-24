-- Add feedback fields to suggested_posts table
ALTER TABLE suggested_posts 
ADD COLUMN user_feedback VARCHAR(20) NULL,
ADD COLUMN feedback_comment TEXT NULL,
ADD COLUMN feedback_at TIMESTAMPTZ NULL;

-- Add check constraint for user_feedback values
ALTER TABLE suggested_posts 
ADD CONSTRAINT suggested_posts_user_feedback_check 
CHECK (user_feedback IN ('positive', 'negative') OR user_feedback IS NULL);

-- Add index for feedback queries
CREATE INDEX idx_suggested_posts_user_feedback ON suggested_posts(user_feedback) WHERE user_feedback IS NOT NULL; 
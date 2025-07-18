-- Create user_onboarding table for tracking onboarding progress
CREATE TABLE user_onboarding (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES public.users(id) ON DELETE CASCADE,
    
    -- Onboarding status
    is_completed BOOLEAN NOT NULL DEFAULT FALSE,
    is_skipped BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Individual step completion tracking
    step_profile_completed BOOLEAN NOT NULL DEFAULT FALSE,
    step_content_preferences_completed BOOLEAN NOT NULL DEFAULT FALSE,
    step_settings_completed BOOLEAN NOT NULL DEFAULT FALSE,
    step_my_posts_completed BOOLEAN NOT NULL DEFAULT FALSE,
    step_content_ideas_completed BOOLEAN NOT NULL DEFAULT FALSE,
    step_posting_schedule_completed BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Current step tracking (1-6 for the 6 steps)
    current_step INTEGER NOT NULL DEFAULT 1,
    
    -- Optional notes or feedback from user
    notes TEXT,
    
    -- Audit logging
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    skipped_at TIMESTAMPTZ
);

-- Create index on user_id for faster lookups
CREATE INDEX idx_user_onboarding_user_id ON user_onboarding(user_id);

-- Create index on completion status for analytics
CREATE INDEX idx_user_onboarding_status ON user_onboarding(is_completed, is_skipped);

-- Enable RLS (Row Level Security)
ALTER TABLE user_onboarding ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can view their own onboarding progress" ON user_onboarding
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update their own onboarding progress" ON user_onboarding
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own onboarding progress" ON user_onboarding
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_user_onboarding_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_user_onboarding_updated_at
    BEFORE UPDATE ON user_onboarding
    FOR EACH ROW
    EXECUTE FUNCTION update_user_onboarding_updated_at();

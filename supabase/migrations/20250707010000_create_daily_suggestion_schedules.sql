CREATE TABLE IF NOT EXISTS public.daily_suggestion_schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    cron_expression TEXT NOT NULL CHECK (cron_expression <> ''),
    timezone TEXT NOT NULL DEFAULT 'UTC',
    last_run_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Ensure each user has at most one schedule (unique constraint)
ALTER TABLE public.daily_suggestion_schedules
    ADD CONSTRAINT daily_suggestion_schedules_user_unique UNIQUE (user_id);

-- RLS: Allow row-level security; users can select/update/delete their own row
ALTER TABLE public.daily_suggestion_schedules ENABLE ROW LEVEL SECURITY;

CREATE POLICY select_own_daily_suggestion_schedule ON public.daily_suggestion_schedules
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY modify_own_daily_suggestion_schedule ON public.daily_suggestion_schedules
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY delete_own_daily_suggestion_schedule ON public.daily_suggestion_schedules
    FOR DELETE USING (auth.uid() = user_id); 
ALTER TABLE public.user_sessions
  ALTER COLUMN session_token TYPE TEXT,
  ALTER COLUMN refresh_token TYPE TEXT; 
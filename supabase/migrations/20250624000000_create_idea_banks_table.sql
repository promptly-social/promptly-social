-- Create idea_banks table
-- Date: 2025-01-24
-- Description: Add idea_banks table to store user ideas with data

CREATE TABLE public.idea_banks (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES public.users(id) NOT NULL,
  data JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Add Row Level Security (RLS)
ALTER TABLE public.idea_banks ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for idea_banks table
CREATE POLICY "Users can view their own idea banks" 
  ON public.idea_banks 
  FOR SELECT 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own idea banks" 
  ON public.idea_banks 
  FOR INSERT 
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own idea banks" 
  ON public.idea_banks 
  FOR UPDATE 
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own idea banks" 
  ON public.idea_banks 
  FOR DELETE 
  USING (auth.uid() = user_id);

-- Add indexes for better performance
CREATE INDEX idx_idea_banks_user_id ON public.idea_banks(user_id);
CREATE INDEX idx_idea_banks_data ON public.idea_banks USING GIN(data);

-- Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_idea_banks_updated_at 
    BEFORE UPDATE ON public.idea_banks 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add comment for documentation
COMMENT ON TABLE public.idea_banks IS 'Store user ideas with flexible data structure';
COMMENT ON COLUMN public.idea_banks.data IS 'JSON field containing idea data: {"type": "substack|text", "value": "string", "time_sensitive": boolean}'; 
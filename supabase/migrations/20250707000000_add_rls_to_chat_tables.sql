-- Add RLS policies to conversations and messages tables

-- Enable RLS on conversations table
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;

-- Drop existing policy if it exists
DROP POLICY IF EXISTS "Users can manage their own conversations" ON public.conversations;

-- Allow users to manage their own conversations
CREATE POLICY "Users can manage their own conversations"
ON public.conversations
FOR ALL
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- Enable RLS on messages table
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- Drop existing policy if it exists
DROP POLICY IF EXISTS "Users can manage messages in their own conversations" ON public.messages;

-- Allow users to manage messages within their own conversations
CREATE POLICY "Users can manage messages in their own conversations"
ON public.messages
FOR ALL
USING (
    EXISTS (
        SELECT 1
        FROM public.conversations
        WHERE id = messages.conversation_id AND user_id = auth.uid()
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1
        FROM public.conversations
        WHERE id = messages.conversation_id AND user_id = auth.uid()
    )
); 
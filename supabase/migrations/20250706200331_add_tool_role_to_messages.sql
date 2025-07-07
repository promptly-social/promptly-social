-- First, drop the existing constraint
ALTER TABLE public.messages DROP CONSTRAINT messages_role_check;

-- Then, add the new constraint with 'tool' included
ALTER TABLE public.messages ADD CONSTRAINT messages_role_check 
CHECK (role IN ('user', 'assistant', 'system', 'tool'));

-- Finally, update the comment on the column to reflect the change
COMMENT ON COLUMN public.messages.role IS 'Role of message sender (user, assistant, system, tool)';

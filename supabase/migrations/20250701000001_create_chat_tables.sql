-- Create tables for chat functionality
-- conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    idea_bank_id UUID REFERENCES idea_banks(id) ON DELETE SET NULL,
    conversation_type VARCHAR(50) NOT NULL DEFAULT 'post_generation',
    title VARCHAR(255),
    context JSONB,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    message_type VARCHAR(20) NOT NULL DEFAULT 'text',
    message_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_idea_bank_id ON conversations(idea_bank_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_created_at ON conversations(created_at);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_role ON messages(role);
CREATE INDEX idx_messages_created_at ON messages(created_at);

-- Add update trigger for conversations table
CREATE OR REPLACE FUNCTION update_conversations_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER conversations_updated_at_trigger
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_conversations_updated_at();

-- Add constraints
ALTER TABLE conversations 
ADD CONSTRAINT conversations_status_check 
CHECK (status IN ('active', 'completed', 'cancelled'));

ALTER TABLE messages
ADD CONSTRAINT messages_role_check 
CHECK (role IN ('user', 'assistant', 'system'));

ALTER TABLE messages
ADD CONSTRAINT messages_message_type_check 
CHECK (message_type IN ('text', 'voice', 'system'));

-- Add comments
COMMENT ON TABLE conversations IS 'Stores chat conversations for post generation';
COMMENT ON TABLE messages IS 'Stores individual messages within conversations';
COMMENT ON COLUMN conversations.conversation_type IS 'Type of conversation (post_generation, etc.)';
COMMENT ON COLUMN conversations.context IS 'Additional context data for the conversation';
COMMENT ON COLUMN conversations.status IS 'Current status of the conversation';
COMMENT ON COLUMN messages.role IS 'Role of message sender (user, assistant, system)';
COMMENT ON COLUMN messages.message_type IS 'Type of message (text, voice, system)';
COMMENT ON COLUMN messages.message_metadata IS 'Additional metadata for the message'; 


-- Update the comment to reflect the new schema
COMMENT ON COLUMN public.idea_banks.data IS 'JSON field containing idea data: {"type": "url|text|product", "value": "string", "title": "string", "product_name": "string", "product_description": "string", "time_sensitive": boolean, "ai_suggested": boolean}';

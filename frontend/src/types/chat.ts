export interface ConversationMessage {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  message_type: "text" | "voice" | "system";
  message_metadata?: Record<string, unknown>;
  created_at: string;
}

export interface Conversation {
  id: string;
  user_id: string;
  idea_bank_id?: string;
  post_id?: string;
  conversation_type: string;
  title?: string;
  context?: Record<string, unknown>;
  status: "active" | "completed" | "cancelled";
  created_at: string;
  updated_at: string;
  messages: ConversationMessage[];
}

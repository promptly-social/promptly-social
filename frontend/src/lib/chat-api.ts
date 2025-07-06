import { apiClient } from "./auth-api";
import { Conversation } from "@/types/chat";

export const createOrGetConversation = async (
  ideaBankId: string
): Promise<Conversation> => {
  try {
    // First, try to get an existing conversation
    const conversation = await apiClient.request<Conversation | null>(
      `/chat/conversations?idea_bank_id=${ideaBankId}`
    );
    if (conversation) {
      return conversation;
    }
  } catch (error) {
    console.warn(
      "Could not fetch existing conversation. Attempting to create a new one.",
      error
    );
  }

  // If not found or error, create a new one
  return apiClient.request<Conversation>("/chat/conversations", {
    method: "POST",
    body: JSON.stringify({
      idea_bank_id: ideaBankId,
      conversation_type: "post_generation",
    }),
  });
}; 
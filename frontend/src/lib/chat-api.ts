import { apiClient } from "./auth-api";
import { Conversation } from "@/types/chat";

export const createOrGetConversation = async (
  conversationType: "post_generation" | "brainstorm",
  ideaBankId?: string
): Promise<Conversation> => {
  try {
    let conversation: Conversation | null = null;
    // First, try to get an existing conversation
    if (conversationType === "post_generation") {
      conversation = ideaBankId
        ? await apiClient.request<Conversation | null>(
            `/chat/conversations?idea_bank_id=${ideaBankId}&conversation_type=${conversationType}`
          )
        : null;
    }
    if (conversationType === "brainstorm") {
      conversation = await apiClient.request<Conversation | null>(
        `/chat/conversations?conversation_type=${conversationType}`
      );
    }

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
      conversation_type: conversationType,
    }),
  });
};

export const archiveConversation = async (
  conversationId: string
): Promise<Conversation> => {
  return apiClient.request<Conversation>(
    `/chat/conversations/${conversationId}`,
    {
      method: "PATCH",
      body: JSON.stringify({ status: "completed" }),
    }
  );
};

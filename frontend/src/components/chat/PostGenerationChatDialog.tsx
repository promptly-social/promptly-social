import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { type IdeaBankWithPost } from "@/lib/idea-bank-api";
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  type ChatModelAdapter,
  type ThreadMessage,
} from "@assistant-ui/react";
import { Thread } from "@/components/assistant-ui/thread";
import { useEffect, useState } from "react";
import { createOrGetConversation } from "@/lib/chat-api";
import { Conversation, ConversationMessage } from "@/types/chat";

type PostGenerationChatDialogProps = {
  idea: IdeaBankWithPost | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

const ChatDialogContent = ({ idea }: { idea: IdeaBankWithPost }) => {
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [initialMessages, setInitialMessages] = useState<ThreadMessage[]>([]);

  useEffect(() => {
    if (idea) {
      createOrGetConversation(idea.idea_bank.id).then((conv) => {
        setConversation(conv);
        const messages: ThreadMessage[] = conv.messages.map(
          (m: ConversationMessage) =>
            ({
              id: m.id,
              role: m.role,
              content: [{ type: "text", text: m.content }],
              createdAt: new Date(m.created_at),
              status: m.role === "assistant" ? "done" : undefined,
            } as unknown as ThreadMessage)
        );
        setInitialMessages(messages);
      });
    }
  }, [idea]);

  if (!conversation) {
    return (
      <DialogContent>
        <div className="flex items-center justify-center h-full">
          <p>Initializing conversation...</p>
        </div>
      </DialogContent>
    );
  }

  const ideaText = idea.idea_bank.data.title || idea.idea_bank.data.value;
  const prefillText = `I want to write a post about "${ideaText}"`;

  return (
    <ChatThreadRuntime
      conversation={conversation}
      initialMessages={initialMessages}
      initialText={initialMessages.length === 0 ? prefillText : undefined}
      placeholder="Write a message..."
    />
  );
};

const ChatThreadRuntime = ({
  conversation,
  initialMessages,
  placeholder,
  initialText,
}: {
  conversation: Conversation;
  initialMessages: ThreadMessage[];
  placeholder?: string;
  initialText?: string;
}) => {
  const modelAdapter: ChatModelAdapter = {
    async *run({ messages }) {
      if (!conversation) return;

      const apiMessages = messages.map((m) => ({
        role: m.role,
        content: m.content
          .map((c) => (c.type === "text" ? c.text : ""))
          .join("\n"),
      }));

      const token = localStorage.getItem("access_token");

      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/v1/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          conversation_id: conversation.id,
          messages: apiMessages,
        }),
      });

      if (!response.body) return;
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedText = "";
      let lastYieldedText = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const json = JSON.parse(line.substring(6));
              if (json.type === "message" && json.content) {
                accumulatedText += json.content;
                if (accumulatedText !== lastYieldedText) {
                  yield {
                    content: [{ type: "text", text: accumulatedText }],
                  };
                  lastYieldedText = accumulatedText;
                }
              } else if (json.type !== "message") {
                // ignore other event types
              } else if (json.type === "error") {
                console.error("Stream error:", json.error);
                yield {
                  content: [
                    {
                      type: "text",
                      text: `An error occurred: ${json.error}`,
                    },
                  ],
                };
                return;
              }
            } catch (e) {
              // ignore parsing errors
            }
          }
        }
      }
    },
  };

  const runtime = useLocalRuntime(modelAdapter, {
    initialMessages,
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <DialogContent className="sm:max-w-[625px] h-[70vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Generate Post</DialogTitle>
        </DialogHeader>
        <div className="flex-grow overflow-y-auto">
          <Thread placeholder={placeholder} initialText={initialText} />
        </div>
      </DialogContent>
    </AssistantRuntimeProvider>
  );
};

export const PostGenerationChatDialog = ({
  idea,
  open,
  onOpenChange,
}: PostGenerationChatDialogProps) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {idea && <ChatDialogContent idea={idea} />}
    </Dialog>
  );
};

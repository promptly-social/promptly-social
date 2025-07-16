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
import { createContext, useContext, useEffect, useState } from "react";
import { createOrGetConversation } from "@/lib/chat-api";
import { Conversation, ConversationMessage } from "@/types/chat";
import { postsApi } from "@/lib/posts-api";
import { Post } from "@/types/posts";
import { PostScheduleModal } from "../schedule-modal/PostScheduleModal";
import { useToast } from "../ui/use-toast";
import { useAuth } from "@/contexts/AuthContext";
import { ConfirmationModal } from "../shared/modals/ConfirmationModal";
import { Button } from "../ui/button";
import { archiveConversation } from "@/lib/chat-api";

type PostSchedulingContextType = {
  onSchedule: (content: string) => void;
};

const PostSchedulingContext = createContext<PostSchedulingContextType | null>(
  null
);

export const usePostScheduling = () => {
  const context = useContext(PostSchedulingContext);
  if (!context) {
    throw new Error(
      "usePostScheduling must be used within a PostSchedulingProvider"
    );
  }
  return context;
};

type PostGenerationChatDialogProps = {
  conversationType: "post_generation" | "brainstorm";
  idea?: IdeaBankWithPost | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onScheduleComplete: () => void;
};

const ChatDialogContent = ({
  conversationType,
  idea,
  onScheduleComplete,
  onClose,
}: {
  conversationType: "post_generation" | "brainstorm";
  idea?: IdeaBankWithPost | null;
  onScheduleComplete: () => void;
  onClose: () => void;
}) => {
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [initialMessages, setInitialMessages] = useState<ThreadMessage[]>([]);
  const [isScheduling, setIsScheduling] = useState(false);

  const [isConfirmArchiveOpen, setIsConfirmArchiveOpen] = useState(false);
  const [isArchiving, setIsArchiving] = useState(false);

  const [postToSchedule, setPostToSchedule] = useState<Post | null>(null);
  const { toast } = useToast();
  const { user } = useAuth();

  const handleOpenScheduleModal = (content: string) => {
    if (!user) return;
    const tempPost: Post = {
      id: `temp-${Date.now()}`,
      content,
      idea_bank_id: idea?.idea_bank.id,
      status: "draft",
      scheduled_at: undefined,
      posted_at: undefined,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      user_id: user.id,
      platform: "linkedin",
      topics: [],
      media: [],
    };
    setPostToSchedule(tempPost);
  };

  const handleSchedule = async (_postId: string, scheduledAt: string) => {
    if (!postToSchedule) return;

    setIsScheduling(true);
    try {
      const newPost = await postsApi.createPost({
        content: postToSchedule.content,
        idea_bank_id: idea?.idea_bank.id,
        status: "draft",
      });

      await postsApi.schedulePost(newPost.id, scheduledAt);

      toast({
        title: "Success",
        description: "Post scheduled successfully.",
      });
      setPostToSchedule(null); // Close modal on success
      onScheduleComplete();
      onClose();
    } catch (error) {
      console.error("Failed to schedule post:", error);
      toast({
        title: "Error",
        description: "Failed to schedule post. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsScheduling(false);
    }
  };

  const handleStartNewConversation = () => {
    setIsConfirmArchiveOpen(true);
  };

  const handleConfirmArchive = async () => {
    if (!conversation) return;
    try {
      setIsArchiving(true);
      await archiveConversation(conversation.id);
      // After archiving, create a new conversation
      const newConv = await createOrGetConversation(
        conversationType,
        idea?.idea_bank.id
      );
      setConversation(newConv);
      setInitialMessages([]);
    } catch (error) {
      console.error("Failed to archive conversation:", error);
      toast({
        title: "Error",
        description: "Failed to start a new conversation. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsArchiving(false);
      setIsConfirmArchiveOpen(false);
    }
  };

  useEffect(() => {
    createOrGetConversation(conversationType, idea?.idea_bank.id).then(
      (conv) => {
        setConversation(conv);
        const messages: ThreadMessage[] = conv.messages.map(
          (m: ConversationMessage) => {
            const isTool = (m.role as string) === "tool";
            return {
              id: m.id,
              role: isTool ? "assistant" : m.role,
              content: [
                {
                  type: isTool ? "tool-call" : "text",
                  text: m.content,
                  result: isTool ? m.content : undefined,
                },
              ],
              createdAt: new Date(m.created_at),
              status: m.role === "assistant" ? "done" : undefined,
            } as unknown as ThreadMessage;
          }
        );
        setInitialMessages(messages);
      }
    );
  }, [idea, conversationType]);

  if (!conversation) {
    return (
      <DialogContent>
        <div className="flex items-center justify-center h-full">
          <p>Initializing conversation...</p>
        </div>
      </DialogContent>
    );
  }

  const ideaText = idea?.idea_bank.data.value;
  const prefillText = `Help me draft a LinkedIn post and here is the idea: "${ideaText}"`;

  return (
    <PostSchedulingContext.Provider
      value={{ onSchedule: handleOpenScheduleModal }}
    >
      <ChatThreadRuntime
        key={conversation.id}
        conversation={conversation}
        initialMessages={initialMessages}
        initialText={
          initialMessages.length === 0 && ideaText ? prefillText : undefined
        }
        placeholder="Write a message..."
        onStartNewConversation={handleStartNewConversation}
      />
      <PostScheduleModal
        isOpen={!!postToSchedule}
        onClose={() => setPostToSchedule(null)}
        post={postToSchedule}
        onSchedule={handleSchedule}
        isScheduling={isScheduling}
      />

      <ConfirmationModal
        isOpen={isConfirmArchiveOpen}
        onClose={() => setIsConfirmArchiveOpen(false)}
        onConfirm={handleConfirmArchive}
        title="Start a new conversation?"
        description="This will archive the current conversation and start a new one. Are you sure?"
        isLoading={isArchiving}
      />
    </PostSchedulingContext.Provider>
  );
};

const ChatThreadRuntime = ({
  conversation,
  initialMessages,
  placeholder,
  initialText,
  onStartNewConversation,
}: {
  conversation: Conversation;
  initialMessages: ThreadMessage[];
  placeholder?: string;
  initialText?: string;
  onStartNewConversation: () => void;
}) => {
  const modelAdapter: ChatModelAdapter = {
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore
    async *run({ messages, getThread }) {
      if (!conversation) return;

      const apiMessages = messages.flatMap((m: ThreadMessage) => {
        const parts: { role: string; content: string }[] = [];
        let textContent = "";

        m.content.forEach((c) => {
          if (c.type === "text") {
            textContent += `${c.text}\n`;
          } else if (c.type === "tool-call") {
            parts.push({ role: "tool", content: c.text });
          }
        });

        if (textContent.trim()) {
          parts.unshift({ role: m.role, content: textContent.trim() });
        }

        return parts;
      });

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
              } else if (json.type === "tool_output") {
                yield {
                  role: "assistant",
                  content: [
                    {
                      type: "tool-call",
                      text: json.content,
                      result: json.content,
                    },
                  ],
                };
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
        <DialogHeader className="flex flex-row items-center justify-between p-2">
          <DialogTitle>Draft Post</DialogTitle>
          <Button variant="outline" size="sm" onClick={onStartNewConversation}>
            Start New Conversation
          </Button>
        </DialogHeader>
        <div className="flex-grow overflow-y-auto">
          <Thread placeholder={placeholder} initialText={initialText} />
        </div>
      </DialogContent>
    </AssistantRuntimeProvider>
  );
};

export const PostGenerationChatDialog = ({
  conversationType,
  idea,
  open,
  onOpenChange,
  onScheduleComplete,
}: PostGenerationChatDialogProps) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {open && (
        <ChatDialogContent
          conversationType={conversationType}
          idea={idea}
          onScheduleComplete={onScheduleComplete}
          onClose={() => onOpenChange(false)}
        />
      )}
    </Dialog>
  );
};

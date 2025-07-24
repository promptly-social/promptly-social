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
import { CreatePostModal } from "../post-modal/CreatePostModal";
import { useToast } from "../ui/use-toast";
import { ConfirmationModal } from "../shared/modals/ConfirmationModal";
import { Button } from "../ui/button";
import { archiveConversation } from "@/lib/chat-api";
import { streamChatMessages, type ChatMessage } from "@/lib/chat-streaming-api";
import { Loader2 } from "lucide-react";

type PostSchedulingContextType = {
  onSchedule: (content: string, topics?: string[], ideaBankId?: string) => void;
  ideaBankId?: string;
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
  const [ideaBankId, setIdeaBankId] = useState<string | undefined>(undefined);
  const [initialMessages, setInitialMessages] = useState<ThreadMessage[]>([]);
  const [isScheduling, setIsScheduling] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const [isConfirmArchiveOpen, setIsConfirmArchiveOpen] = useState(false);
  const [isArchiving, setIsArchiving] = useState(false);

  const [postToSchedule, setPostToSchedule] = useState<Post | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [draftContent, setDraftContent] = useState("");
  const [draftTopics, setDraftTopics] = useState<string[]>([]);
  const { toast } = useToast();

  const handleOpenCreateModal = (
    content: string,
    topics?: string[],
    ideaBankId?: string
  ) => {
    setDraftContent(content);
    setDraftTopics(topics || []);
    setShowCreateModal(true);
    setIdeaBankId(ideaBankId);
  };

  const handleScheduleRequest = (post: Post) => {
    setPostToSchedule(post);
  };

  const handleSchedule = async (_postId: string, scheduledAt: string) => {
    if (!postToSchedule) return;

    setIsScheduling(true);
    try {
      await postsApi.schedulePost(postToSchedule.id, scheduledAt);

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

      toast({
        title: "Success",
        description: "Started new conversation.",
      });
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
    const initializeConversation = async () => {
      try {
        setIsLoading(true);
        const conv = await createOrGetConversation(conversationType, idea?.idea_bank.id);
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
      } catch (error) {
        console.error("Error initializing conversation:", error);
        toast({
          title: "Error",
          description: "Failed to load conversation.",
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };

    initializeConversation();
  }, [idea, conversationType, toast]);

  useEffect(() => {
    if (idea?.idea_bank.id) {
      setIdeaBankId(idea.idea_bank.id);
    }
  }, [idea]);

  if (isLoading || !conversation) {
    return (
      <DialogContent className="sm:max-w-[625px] h-[70vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Draft Post</DialogTitle>
        </DialogHeader>
        <div className="flex-grow flex items-center justify-center">
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            <p className="text-sm text-muted-foreground">Loading conversation...</p>
          </div>
        </div>
      </DialogContent>
    );
  }

  const ideaText = idea?.idea_bank.data.value;
  const prefillText = `Help me draft a LinkedIn post using this idea`;

  return (
    <PostSchedulingContext.Provider
      value={{ onSchedule: handleOpenCreateModal, ideaBankId }}
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
        isStartingNewConversation={isArchiving}
      />

      <CreatePostModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreated={onScheduleComplete}
        onScheduleRequest={handleScheduleRequest}
        initialContent={draftContent}
        initialTopics={draftTopics}
        ideaBankId={ideaBankId}
        ideaBankValue={idea?.idea_bank.data.value}
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
  isStartingNewConversation = false,
}: {
  conversation: Conversation;
  initialMessages: ThreadMessage[];
  placeholder?: string;
  initialText?: string;
  onStartNewConversation: () => void;
  isStartingNewConversation?: boolean;
}) => {
  const modelAdapter: ChatModelAdapter = {
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore
    async *run({ messages, getThread }) {
      if (!conversation) return;

      // Transform assistant-ui messages to API format
      const apiMessages: ChatMessage[] = messages.flatMap(
        (m: ThreadMessage) => {
          const parts: ChatMessage[] = [];
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
        }
      );

      // Use the new streaming API
      try {
        const streamGenerator = streamChatMessages({
          conversation_id: conversation.id,
          messages: apiMessages,
        });

        for await (const response of streamGenerator) {
          yield response;
        }
      } catch (error) {
        console.error("Chat streaming error:", error);
        yield {
          content: [
            {
              type: "text",
              text: `Error: ${
                error instanceof Error ? error.message : "Unknown error"
              }`,
            },
          ],
        };
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
          <Button
            variant="outline"
            size="sm"
            onClick={onStartNewConversation}
            disabled={isStartingNewConversation}
          >
            {isStartingNewConversation ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Starting...
              </>
            ) : (
              "Start New Conversation"
            )}
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

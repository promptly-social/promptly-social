import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  type ChatModelAdapter,
  type ThreadMessage,
} from "@assistant-ui/react";
import { Thread } from "@/components/assistant-ui/thread";
import { createContext, useContext, useEffect, useState } from "react";
import { createOrGetPostEditingConversation } from "@/lib/chat-api";
import { Conversation, ConversationMessage } from "@/types/chat";
import { postsApi } from "@/lib/posts-api";
import { Post } from "@/types/posts";
import { useToast } from "../ui/use-toast";
import { Button } from "../ui/button";
import { archiveConversation } from "@/lib/chat-api";
import { streamChatMessages, type ChatMessage } from "@/lib/chat-streaming-api";
import { Loader2 } from "lucide-react";

type PostEditingContextType = {
  onUseRevision: (content: string, topics?: string[]) => void;
  post: Post;
};

const PostEditingContext = createContext<PostEditingContextType | null>(null);

export const usePostEditing = () => {
  const context = useContext(PostEditingContext);
  if (!context) {
    throw new Error(
      "usePostEditing must be used within a PostEditingProvider"
    );
  }
  return context;
};

type PostEditingChatDialogProps = {
  post: Post;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onPostUpdated: (updatedPost: Post) => void;
};

const ChatDialogContent = ({
  post,
  onPostUpdated,
  onClose,
}: {
  post: Post;
  onPostUpdated: (updatedPost: Post) => void;
  onClose: () => void;
}) => {
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [initialMessages, setInitialMessages] = useState<ThreadMessage[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();

  const handleUseRevision = async (content: string, topics?: string[]) => {
    try {
      const updatedPost = await postsApi.updatePost(post.id, {
        content,
        topics: topics || post.topics,
      });

      toast({
        title: "Post updated",
        description: "Your post has been updated with the AI revision.",
      });

      onPostUpdated(updatedPost);
      onClose();
    } catch (error) {
      console.error("Error updating post:", error);
      toast({
        title: "Error",
        description: "Failed to update the post. Please try again.",
        variant: "destructive",
      });
    }
  };

  const [isStartingNewConversation, setIsStartingNewConversation] = useState(false);

  const handleStartNewConversation = async () => {
    try {
      setIsStartingNewConversation(true);
      if (conversation) {
        await archiveConversation(conversation.id);
      }
      const newConversation = await createOrGetPostEditingConversation(post.id);
      setConversation(newConversation);
      setInitialMessages([]);

      toast({
        title: "Success",
        description: "Started new conversation.",
      });
    } catch (error) {
      console.error("Error starting new conversation:", error);
      toast({
        title: "Error",
        description: "Failed to start new conversation.",
        variant: "destructive",
      });
    } finally {
      setIsStartingNewConversation(false);
    }
  };

  useEffect(() => {
    const initializeConversation = async () => {
      try {
        setIsLoading(true);
        const conv = await createOrGetPostEditingConversation(post.id);
        setConversation(conv);

        // Convert existing messages to ThreadMessage format
        // Handle tool messages the same way as PostGenerationChatDialog
        const threadMessages: ThreadMessage[] = conv.messages.map(
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

        setInitialMessages(threadMessages);
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

    if (post.id) {
      initializeConversation();
    }
  }, [post.id, toast]);

  if (isLoading || !conversation) {
    return (
      <DialogContent className="sm:max-w-[625px] h-[70vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Edit with AI</DialogTitle>
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

  return (
    <PostEditingContext.Provider value={{ onUseRevision: handleUseRevision, post }}>
      <ChatThreadRuntime
        key={conversation.id}
        conversation={conversation}
        initialMessages={initialMessages}
        placeholder="Describe how you'd like to edit this post..."
        onStartNewConversation={handleStartNewConversation}
        isStartingNewConversation={isStartingNewConversation}
      />
    </PostEditingContext.Provider>
  );
};

type ChatThreadRuntimeProps = {
  conversation: Conversation;
  initialMessages: ThreadMessage[];
  initialText?: string;
  placeholder: string;
  onStartNewConversation: () => void;
  isStartingNewConversation?: boolean;
};

const ChatThreadRuntime = ({
  conversation,
  initialMessages,
  initialText,
  placeholder,
  onStartNewConversation,
  isStartingNewConversation = false,
}: ChatThreadRuntimeProps) => {
  const adapter: ChatModelAdapter = {
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore
    async *run({ messages, abortSignal }) {
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

      const streamGenerator = streamChatMessages({
        conversation_id: conversation.id,
        messages: apiMessages,
      });

      for await (const response of streamGenerator) {
        if (abortSignal?.aborted) {
          break;
        }
        yield response;
      }
    },
  };

  const runtime = useLocalRuntime(adapter, {
    initialMessages,
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <DialogContent className="sm:max-w-[625px] h-[70vh] flex flex-col">
        <DialogHeader className="flex flex-row items-center justify-between p-2">
          <DialogTitle>Edit Post with AI</DialogTitle>
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

export const PostEditingChatDialog = ({
  post,
  open,
  onOpenChange,
  onPostUpdated,
}: PostEditingChatDialogProps) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {open && (
        <ChatDialogContent
          post={post}
          onPostUpdated={onPostUpdated}
          onClose={() => onOpenChange(false)}
        />
      )}
    </Dialog>
  );
};

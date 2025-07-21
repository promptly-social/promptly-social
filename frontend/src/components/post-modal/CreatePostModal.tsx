import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { postsApi } from "@/lib/posts-api";
import { Post } from "@/types/posts";
import { usePostEditor } from "@/hooks/usePostEditor";
import { PostEditorFields } from "@/components/shared/post-card/components/PostEditorFields";
import { ConfirmationModal } from "@/components/shared/modals/ConfirmationModal";

interface CreatePostModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated?: (post: Post) => void;
  onScheduleRequest?: (post: Post) => void;
  initialContent?: string;
  initialTopics?: string[];
  ideaBankId?: string;
  ideaBankValue?: string;
}

function isUrl(url: string): boolean {
  try {
    new URL(url.trim());
    return true;
  } catch (e) {
    return false;
  }
}

export const CreatePostModal: React.FC<CreatePostModalProps> = ({
  isOpen,
  onClose,
  onCreated,
  onScheduleRequest,
  initialContent,
  initialTopics,
  ideaBankId,
  ideaBankValue,
}) => {
  const editor = usePostEditor();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [createdPost, setCreatedPost] = useState<Post | null>(null);
  const [showScheduleConfirmation, setShowScheduleConfirmation] =
    useState(false);
  const { toast } = useToast();

  // Initialize editor with initial values when modal opens
  React.useEffect(() => {
    if (isOpen) {
      // Reset editor with initial values if provided, otherwise reset to clean state

      let articleUrl = undefined;
      if (ideaBankValue && isUrl(ideaBankValue)) {
        articleUrl = ideaBankValue;
      }

      editor.reset({
        content: initialContent || "",
        topics: initialTopics || [],
        articleUrl,
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, initialContent, initialTopics]);

  const handleSubmit = async () => {
    if (isSubmitting) return;
    setIsSubmitting(true);

    try {
      // Create post first
      const newPost = await postsApi.createPost({
        content: editor.content,
        topics: editor.topics,
        article_url: editor.articleUrl || undefined,
        status: "draft",
        platform: "linkedin", // default platform; adjust as needed
        idea_bank_id: ideaBankId,
      });

      // Upload media if any
      if (editor.mediaFiles.length > 0) {
        await postsApi.uploadPostMedia(newPost.id, editor.mediaFiles);
      }

      toast({
        title: "Post created",
        description: "Your draft has been created.",
      });

      setCreatedPost(newPost);
      onCreated?.(newPost);
      editor.reset();

      // Show scheduling confirmation if onScheduleRequest is provided
      if (onScheduleRequest) {
        setShowScheduleConfirmation(true);
      } else {
        onClose();
      }
    } catch (error) {
      console.error("Failed to create post", error);
      toast({
        title: "Error",
        description: "Failed to create post. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleScheduleConfirmation = () => {
    if (createdPost && onScheduleRequest) {
      onScheduleRequest(createdPost);
    }
    setShowScheduleConfirmation(false);
    setCreatedPost(null);
    onClose();
  };

  const handleScheduleDecline = () => {
    setShowScheduleConfirmation(false);
    setCreatedPost(null);
    onClose();
  };

  return (
    <>
      <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader className="border-b border-border pb-4">
            <DialogTitle className="text-foreground text-xl font-semibold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              Create New Post
            </DialogTitle>
          </DialogHeader>
          <PostEditorFields editor={editor} />
          <DialogFooter className="pt-4 border-t border-border">
            <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} disabled={isSubmitting} className="bg-gradient-to-r from-primary to-secondary hover:from-primary/90 hover:to-secondary/90">
              {isSubmitting ? "Creating..." : "Create"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ConfirmationModal
        isOpen={showScheduleConfirmation}
        onClose={handleScheduleDecline}
        cancelButtonText="No"
        onConfirm={handleScheduleConfirmation}
        title="Schedule this post?"
        description="Would you like to schedule this post for publication?"
      />
    </>
  );
};

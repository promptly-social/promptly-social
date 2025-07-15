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

interface CreatePostModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated?: (post: Post) => void;
}

export const CreatePostModal: React.FC<CreatePostModalProps> = ({
  isOpen,
  onClose,
  onCreated,
}) => {
  const editor = usePostEditor();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

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
      });

      // Upload media if any
      if (editor.mediaFiles.length > 0) {
        await postsApi.uploadPostMedia(newPost.id, editor.mediaFiles);
      }

      toast({ title: "Post created", description: "Your draft has been created." });
      onCreated?.(newPost);
      editor.reset();
      onClose();
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

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create New Post</DialogTitle>
        </DialogHeader>
        <PostEditorFields editor={editor} />
        <DialogFooter className="pt-4">
          <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isSubmitting}>
            {isSubmitting ? "Creating..." : "Create"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

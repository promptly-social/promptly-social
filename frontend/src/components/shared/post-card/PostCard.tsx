import React, { useState, useEffect, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Edit3, Check, MoreHorizontal } from "lucide-react";
import { Post, PostMedia, PostUpdate } from "@/types/posts";
import { PostCardHeader } from "./components/PostCardHeader";
import { PostContent } from "./components/PostContent";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { PostEditorFields } from "./components/PostEditorFields";
import { PostCardMeta } from "./components/PostCardMeta";
import { PostCardTopics } from "./components/PostCardTopics";
import { PostCardActions } from "./components/PostCardActions";
import { PostCardFeedback } from "./components/PostCardFeedback";
import { PostSharingError } from "./components/PostSharingError";
import { PostScheduleModal } from "@/components/schedule-modal/PostScheduleModal";
import { NegativeFeedbackModal } from "@/components/shared/modals/NegativeFeedbackModal";
import { ConfirmationModal } from "@/components/shared/modals/ConfirmationModal";
import { postsApi } from "@/lib/posts-api";
import { useToast } from "@/hooks/use-toast";
import { usePostEditor } from "@/hooks/usePostEditor";
import { ideaBankApi, IdeaBankData } from "@/lib/idea-bank-api";
import { PostInspiration } from "./components/PostInspiration";

interface PostCardProps {
  post: Post;
  onPostUpdate?: (updatedPost?: Post) => void;
}

export const PostCard: React.FC<PostCardProps> = ({ post, onPostUpdate }) => {
  const [isEditing, setIsEditing] = useState(false);

  // Editor hook consolidates all field state & handlers
  const editor = usePostEditor({
    content: post.content,
    topics: post.topics,
    articleUrl: post.article_url,
    existingMedia: post.media || [],
  });

  const [signedMedia, setSignedMedia] = useState<PostMedia[]>(post.media);
  const [inspiration, setInspiration] = useState<IdeaBankData | null>(null);
  const [inspirationLoading, setInspirationLoading] = useState(false);

  // Helper to fetch the latest signed media from backend
  const refreshSignedMedia = useCallback(async () => {
    try {
      const media = await postsApi.getPostMedia(post.id);
      setSignedMedia(media);
      editor.reset({
        content: editor.content,
        topics: editor.topics,
        articleUrl: editor.articleUrl,
        existingMedia: media,
      });
    } catch (error) {
      console.error("Failed to refresh media", error);
    }
  }, [post.id, editor]);

  const [isSaving, setIsSaving] = useState(false);
  const [isDismissing, setIsDismissing] = useState(false);
  const [isPosting, setIsPosting] = useState(false);
  const [schedulingPostId, setSchedulingPostId] = useState<string | null>(null);

  const [feedbackModal, setFeedbackModal] = useState(false);
  const [confirmationModal, setConfirmationModal] = useState<{
    isOpen: boolean;
    action: "dismiss" | "remove" | null;
  }>({ isOpen: false, action: null });

  const [isProcessingConfirmation, setIsProcessingConfirmation] =
    useState(false);

  const { toast } = useToast();

  // Sync editor fields when entering edit mode
  useEffect(() => {
    if (isEditing) {
      editor.reset({
        content: post.content,
        topics: post.topics,
        articleUrl: post.article_url,
        existingMedia: signedMedia,
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isEditing, post, signedMedia]);

  useEffect(() => {
    const fetchSignedMedia = async () => {
      try {
        const media = await postsApi.getPostMedia(post.id);
        setSignedMedia(media);
        if (!isEditing) {
          editor.reset({
            content: post.content,
            topics: post.topics,
            articleUrl: post.article_url,
            existingMedia: media,
          });
        }
      } catch (error) {
        console.error("Failed to load media", error);
      }
    };

    fetchSignedMedia();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [post.id, post.updated_at, post.media?.length]);

  // Fetch inspiration data when post has idea_bank_id
  useEffect(() => {
    const fetchInspiration = async () => {
      if (!post.idea_bank_id) {
        setInspiration(null);
        return;
      }

      setInspirationLoading(true);
      try {
        const ideaBankData = await ideaBankApi.getIdeaBank(post.idea_bank_id);
        setInspiration(ideaBankData);
      } catch (error) {
        console.error("Failed to fetch inspiration data:", error);
        setInspiration(null);
      } finally {
        setInspirationLoading(false);
      }
    };

    fetchInspiration();
  }, [post.idea_bank_id]);

  // Cleanup object URLs
  useEffect(() => {
    return () => {
      editor.mediaPreviews.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [editor.mediaPreviews]);

  const handleStartEditing = () => setIsEditing(true);
  const handleCancelEdit = () => {
    setIsEditing(false);
    editor.reset({
      content: post.content,
      topics: post.topics,
      articleUrl: post.article_url,
      existingMedia: signedMedia,
    });
  };

  const handleSaveEdit = async () => {
    setIsSaving(true);
    try {
      const updatedPostData: PostUpdate = {
        content: editor.content,
        topics: editor.topics,
      };

      if (editor.articleUrl) {
        updatedPostData.article_url = editor.articleUrl;
      }

      const updatedPost = await postsApi.updatePost(post.id, updatedPostData);

      if (editor.mediaFiles.length > 0) {
        await postsApi.uploadPostMedia(post.id, editor.mediaFiles);
        await refreshSignedMedia();
      }

      toast({ title: "Success", description: "Post updated successfully." });
      onPostUpdate?.(updatedPost);
      handleCancelEdit();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save post.",
        variant: "destructive",
      });
      console.error(error);
    } finally {
      setIsSaving(false);
    }
  };

  // Topic handlers are now inside hook (editor)

  // Media change & removal now handled within "editor" hook and PostEditorFields

  const handleExistingMediaRemove = async (media: PostMedia) => {
    try {
      await postsApi.deletePostMedia(post.id, media.id);
      await refreshSignedMedia();
      toast({
        title: "Success",
        description: "Media removed successfully.",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to remove media.",
        variant: "destructive",
      });
    }
  };

  const handleSubmitPositiveFeedback = async () => {
    try {
      await postsApi.submitFeedback(post.id, { feedback_type: "positive" });
      // TODO: change this to avoid re-fetching the posts
      onPostUpdate?.();
      toast({ title: "Feedback submitted" });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to submit feedback",
        variant: "destructive",
      });
    }
  };

  const handleNegativeFeedbackSubmit = async (comment: string) => {
    try {
      await postsApi.submitFeedback(post.id, {
        feedback_type: "negative",
        comment,
      });
      // Use dismiss endpoint which will also clean up any uploaded media
      await postsApi.dismissPost(post.id);
      // TODO: change this to avoid re-fetching the posts
      onPostUpdate?.();
      toast({ title: "Feedback submitted" });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to submit feedback",
        variant: "destructive",
      });
      throw error; // Let modal keep open if needed
    }
  };

  const handleScheduleSubmit = async (postId: string, scheduledAt: string) => {
    try {
      await postsApi.schedulePost(postId, scheduledAt);
      onPostUpdate?.();
      toast({ title: "Post scheduled" });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to schedule post",
        variant: "destructive",
      });
    }
    setSchedulingPostId(null);
  };

  const handleDismissPost = async () => {
    setIsProcessingConfirmation(true);
    setIsDismissing(true);
    try {
      await postsApi.dismissPost(post.id);
      onPostUpdate?.();
      toast({ title: "Post deleted" });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete post",
        variant: "destructive",
      });
    } finally {
      setIsDismissing(false);
      setIsProcessingConfirmation(false);
      setConfirmationModal({ isOpen: false, action: null });
    }
  };

  const handleSaveForLater = async () => {
    setIsSaving(true);
    try {
      await postsApi.updatePost(post.id, { status: "draft" });
      onPostUpdate?.();
      toast({ title: "Post moved to Drafts" });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save post",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleRemoveFromSchedule = async () => {
    setIsProcessingConfirmation(true);
    try {
      await postsApi.updatePost(post.id, {
        status: "draft",
        scheduled_at: null,
      });
      onPostUpdate?.();
      toast({ title: "Post unscheduled and moved to Drafts" });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to unschedule post",
        variant: "destructive",
      });
    }
    setIsProcessingConfirmation(false);
    setConfirmationModal({ isOpen: false, action: null });
  };

  const handlePostNow = async () => {
    setIsPosting(true);
    try {
      await postsApi.postNow(post.id);
      onPostUpdate?.();
      toast({ 
        title: "Success", 
        description: "Post published successfully!" 
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to publish post. Please try again.",
        variant: "destructive",
      });
      console.error("Error posting now:", error);
    } finally {
      setIsPosting(false);
    }
  };

  const handleConfirmation = () => {
    if (confirmationModal.action === "dismiss") {
      handleDismissPost();
    } else if (confirmationModal.action === "remove") {
      handleRemoveFromSchedule();
    }
  };

  return (
    <>
      <Card className="relative hover:shadow-md transition-shadow flex flex-col h-full bg-white max-w-[600]">
        <div className="flex justify-between items-start p-4">
          <div className="flex-grow">
            <PostCardHeader />
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreHorizontal className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={handleStartEditing}>
                <Edit3 className="w-4 h-4 mr-2" />
                Edit Post
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        <CardContent className="space-y-4 flex-grow flex flex-col pt-0">
          {isEditing ? (
            <div className="space-y-3">
              <PostEditorFields
                editor={editor}
                onExistingMediaRemove={handleExistingMediaRemove}
                postStatus={post.status}
              />
              <div className="flex gap-2 py-2">
                <Button size="sm" onClick={handleSaveEdit} disabled={isSaving}>
                  <Check className="w-4 h-4 mr-1" />
                  {isSaving ? "Saving..." : "Save"}
                </Button>
                <Button size="sm" variant="outline" onClick={handleCancelEdit}>
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <PostContent post={{ ...post, media: signedMedia }} />
          )}

          {!isEditing && (
            <>
              <div className="flex items-center justify-between">
                <PostCardMeta post={post} />
                <PostSharingError hasError={!!post.sharing_error} />
              </div>
              <PostCardTopics topics={post.topics} />

              {inspiration && !inspirationLoading && (
                <PostInspiration inspiration={inspiration} />
              )}

              {!post.user_feedback && post.status === "suggested" && (
                <PostCardFeedback
                  postId={post.id}
                  onSubmitPositiveFeedback={handleSubmitPositiveFeedback}
                  onOpenNegativeFeedbackModal={() => setFeedbackModal(true)}
                />
              )}

              <div className="flex-grow"></div>

              <PostCardActions
                post={post}
                savingPostId={isSaving ? post.id : null}
                dismissingPostId={isDismissing ? post.id : null}
                postingPostId={isPosting ? post.id : null}
                onSchedulePost={() => setSchedulingPostId(post.id)}
                onRemoveFromSchedule={() =>
                  setConfirmationModal({ isOpen: true, action: "remove" })
                }
                onReschedulePost={() => setSchedulingPostId(post.id)}
                onSaveForLater={handleSaveForLater}
                onDismissPost={() =>
                  setConfirmationModal({ isOpen: true, action: "dismiss" })
                }
                onPostNow={handlePostNow}
              />
            </>
          )}
        </CardContent>
      </Card>
      <NegativeFeedbackModal
        isOpen={feedbackModal}
        onClose={() => setFeedbackModal(false)}
        onSubmit={handleNegativeFeedbackSubmit}
      />
      <ConfirmationModal
        isOpen={confirmationModal.isOpen}
        onClose={() => setConfirmationModal({ isOpen: false, action: null })}
        onConfirm={handleConfirmation}
        title={
          confirmationModal.action === "dismiss"
            ? "Delete Post"
            : "Remove from Schedule"
        }
        description={
          confirmationModal.action === "dismiss"
            ? "Are you sure you want to delete this post? This action cannot be undone."
            : "Are you sure you want to remove this post from the schedule? It will be moved to your Drafts tab."
        }
        isLoading={isProcessingConfirmation}
      />
      <PostScheduleModal
        isOpen={!!schedulingPostId}
        onClose={() => setSchedulingPostId(null)}
        post={post}
        onSchedule={handleScheduleSubmit}
      />
    </>
  );
};

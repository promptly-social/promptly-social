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
import { PostScheduleModal } from "@/components/schedule-modal/PostScheduleModal";
import { NegativeFeedbackModal } from "@/components/shared/modals/NegativeFeedbackModal";
import { ConfirmationModal } from "@/components/shared/modals/ConfirmationModal";
import { postsApi } from "@/lib/posts-api";
import { useToast } from "@/hooks/use-toast";

interface PostCardProps {
  post: Post;
  onPostUpdate?: (updatedPost?: Post) => void;
}

export const PostCard: React.FC<PostCardProps> = ({ post, onPostUpdate }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState(post.content);
  const [editedTopics, setEditedTopics] = useState(post.topics);
  const [topicInput, setTopicInput] = useState("");
  const [editedArticleUrl, setEditedArticleUrl] = useState(
    post.media?.find((m) => m.media_type === "article")?.gcs_url || ""
  );
  const [editedMediaFiles, setEditedMediaFiles] = useState<File[]>([]);
  const [existingMedia, setExistingMedia] = useState(post.media || []);
  const [mediaPreviews, setMediaPreviews] = useState<string[]>([]);
  const [signedMedia, setSignedMedia] = useState<PostMedia[]>(post.media);

  // Helper to fetch the latest signed media from backend
  const refreshSignedMedia = useCallback(async () => {
    try {
      const media = await postsApi.getPostMedia(post.id);
      setSignedMedia(media);
      setExistingMedia(media);
    } catch (error) {
      console.error("Failed to refresh media", error);
    }
  }, [post.id]);

  const [isSaving, setIsSaving] = useState(false);
  const [isDismissing, setIsDismissing] = useState(false);
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
      setEditedContent(post.content);
      setEditedTopics(post.topics);
      setEditedArticleUrl(post.article_url);
      setEditedMediaFiles([]);
      setExistingMedia(signedMedia);
    }
  }, [isEditing, post, signedMedia]);

  useEffect(() => {
    const fetchSignedMedia = async () => {
      try {
        const media = await postsApi.getPostMedia(post.id);
        setSignedMedia(media);
        if (!isEditing) {
          setExistingMedia(media);
        }
      } catch (error) {
        console.error("Failed to load media", error);
      }
    };

    fetchSignedMedia();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [post.id, post.updated_at, post.media?.length]);

  // Cleanup object URLs
  useEffect(() => {
    return () => {
      mediaPreviews.forEach(URL.revokeObjectURL);
    };
  }, [mediaPreviews]);

  const handleStartEditing = () => setIsEditing(true);
  const handleCancelEdit = () => {
    setIsEditing(false);
    mediaPreviews.forEach(URL.revokeObjectURL);
    setMediaPreviews([]);
  };

  const handleSaveEdit = async () => {
    setIsSaving(true);
    try {
      const updatedPostData: PostUpdate = {
        content: editedContent,
        topics: editedTopics,
      };

      if (editedArticleUrl) {
        updatedPostData.article_url = editedArticleUrl;
      }

      const updatedPost = await postsApi.updatePost(post.id, updatedPostData);

      if (editedMediaFiles.length > 0) {
        await postsApi.uploadPostMedia(post.id, editedMediaFiles);
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

  const handleTopicAdd = () => {
    if (topicInput && !editedTopics.includes(topicInput)) {
      setEditedTopics([...editedTopics, topicInput]);
      setTopicInput("");
    }
  };
  const handleTopicRemove = (topic: string) =>
    setEditedTopics(editedTopics.filter((t) => t !== topic));

  const handleMediaFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      // Revoke previous previews to avoid memory leaks
      mediaPreviews.forEach(URL.revokeObjectURL);

      const file = e.target.files[0];
      setEditedMediaFiles([file]);
      setMediaPreviews([URL.createObjectURL(file)]);
    }
  };

  const handleNewMediaRemove = (fileToRemove: File, indexToRemove: number) => {
    setEditedMediaFiles((prev) =>
      prev.filter((_, index) => index !== indexToRemove)
    );
    setMediaPreviews((prev) => {
      const newPreviews = [...prev];
      const [revokedUrl] = newPreviews.splice(indexToRemove, 1);
      URL.revokeObjectURL(revokedUrl);
      return newPreviews;
    });
  };

  const handleExistingMediaRemove = async (media: PostMedia) => {
    try {
      await postsApi.deletePostMedia(post.id, media.id);
      setExistingMedia(existingMedia.filter((m) => m.id !== media.id));
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
                content={editedContent}
                onContentChange={setEditedContent}
                topics={editedTopics}
                topicInput={topicInput}
                onTopicInputChange={setTopicInput}
                onTopicAdd={handleTopicAdd}
                onTopicRemove={handleTopicRemove}
                articleUrl={editedArticleUrl}
                onArticleUrlChange={setEditedArticleUrl}
                existingMedia={existingMedia}
                mediaFiles={editedMediaFiles}
                mediaPreviews={mediaPreviews}
                onMediaFileChange={handleMediaFileChange}
                onExistingMediaRemove={handleExistingMediaRemove}
                onNewMediaRemove={handleNewMediaRemove}
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
              <PostCardMeta post={post} />
              <PostCardTopics topics={post.topics} />

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
                onSchedulePost={() => setSchedulingPostId(post.id)}
                onRemoveFromSchedule={() =>
                  setConfirmationModal({ isOpen: true, action: "remove" })
                }
                onReschedulePost={() => setSchedulingPostId(post.id)}
                onSaveForLater={handleSaveForLater}
                onDismissPost={() =>
                  setConfirmationModal({ isOpen: true, action: "dismiss" })
                }
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

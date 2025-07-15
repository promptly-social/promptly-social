import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Calendar,
  Bookmark,
  Edit3,
  Trash2,
  RefreshCw,
  Save,
  X,
} from "lucide-react";
import { Post, PostMedia } from "@/types/posts";
import { postsApi } from "@/lib/posts-api";
import { PostCardHeader } from "../shared/post-card/components/PostCardHeader";
import { PostContent } from "../shared/post-card/components/PostContent";
import { PostEditorFields } from "../shared/post-card/components/PostEditorFields";
import { usePostEditor } from "@/hooks/usePostEditor";

interface ScheduledPostDetailsProps {
  isOpen: boolean;
  onClose: () => void;
  post: Post | null;
  onSaveForLater?: (post: Post) => void;
  onReschedule?: (post: Post) => void;
  onDelete?: (post: Post) => void;
  onUpdatePost?: (
    postId: string,
    newContent: string,
    newTopics: string[]
  ) => Promise<void>;
  onPostPublished?: (postId: string) => void;
  isProcessing?: boolean;
  isNewPost?: boolean;
  formatDateTime?: (dateString: string) => string;
}

export const ScheduledPostDetails: React.FC<ScheduledPostDetailsProps> = ({
  isOpen,
  onClose,
  post,
  onSaveForLater,
  onReschedule,
  onDelete,
  onUpdatePost,
  onPostPublished,
  isProcessing = false,
  isNewPost = false,
  formatDateTime,
}) => {
  const [isEditing, setIsEditing] = React.useState(false);
  const [isSaving, setIsSaving] = React.useState(false);
  const editor = usePostEditor();
  const [isPublishing, setIsPublishing] = React.useState(false);

  React.useEffect(() => {
    if (post) {
      editor.reset({
        content: post.content,
        topics: post.topics || [],
        articleUrl: post.article_url || "",
        existingMedia: post.media || [],
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [post]);

  React.useEffect(() => {
    if (!isOpen) {
      setIsEditing(false);
      setIsPublishing(false);
      editor.reset();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  // Topic & media handlers now encapsulated within editor hook

  const handleMediaRemove = async (media: PostMedia | File, index?: number) => {
    if ("id" in media) {
      if (!post) return;
      try {
        await postsApi.deletePostMedia(post.id, media.id);
        editor.removeExistingMedia(media);
        if (media.media_type === "article") {
          editor.setArticleUrl("");
        }
      } catch (error) {
        console.error("Failed to delete media:", error);
      }
    } else {
      if (index === undefined) return;
      editor.removeNewMedia(media as File, index);
    }
  };

  // Save handler that works whether parent supplies an `onUpdatePost` callback or not.
  const handleSave = async () => {
    if (!post) return;
    setIsSaving(true);

    try {
      // If the parent provided an explicit updater, use that first so it can manage its own cache/state.
      if (onUpdatePost) {
        await onUpdatePost(post.id, editor.content, editor.topics);
      } else {
        // Fallback: update the post directly via API.
        await postsApi.updatePost(post.id, {
          content: editor.content,
          topics: editor.topics,
        });
      }

      // Handle article URL changes (including clearing the field)
      await postsApi.updatePost(post.id, {
        article_url: editor.articleUrl || null,
      });

      // Upload any newly-selected media files first (if any)
      if (editor.mediaFiles.length > 0) {
        await postsApi.uploadPostMedia(post.id, editor.mediaFiles);
      }

      // Immediately exit edit mode – background refresh afterwards
      setIsEditing(false);

      // Refresh media list (non-blocking for user perception)
      try {
        const refreshedMedia = await postsApi.getPostMedia(post.id);
        editor.reset({
          content: editor.content,
          topics: editor.topics,
          articleUrl: editor.articleUrl,
          existingMedia: refreshedMedia,
        });
      } catch (err) {
        console.error("Failed to refresh media", err);
      }

      // TODO: consider refreshing post data so UI reflects new media without closing dialog
    } catch (error) {
      console.error("Failed to save scheduled post edits:", error);
      // You might want to show a toast notification here
    } finally {
      setIsSaving(false);
    }
  };

  const handlePublish = async () => {
    if (post) {
      setIsPublishing(true);
      try {
        await postsApi.publishPost(post.id, "linkedin");
        if (onPostPublished) {
          onPostPublished(post.id);
        }
        onClose();
      } catch (error) {
        console.error("Failed to publish post:", error);
        // You might want to show a toast notification here
      } finally {
        setIsPublishing(false);
      }
    }
  };

  const handleCancel = () => {
    if (post) {
      editor.reset({
        content: post.content,
        topics: post.topics || [],
        articleUrl: post.article_url || "",
        existingMedia: post.media || [],
      });
    }
    setIsEditing(false);
  };

  const defaultFormatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const dateTimeFormatter = formatDateTime || defaultFormatDateTime;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Scheduled Post Details
          </DialogTitle>
        </DialogHeader>

        {post && (
          <div className="flex-1 overflow-y-auto pr-2 flex flex-col space-y-4">
            <div className="border rounded-lg p-4 bg-white">
              <PostCardHeader />
              <div className="mt-4">
                {isEditing ? (
                  <div className="space-y-4">
                    <PostEditorFields
                      editor={editor}
                      onExistingMediaRemove={(media) =>
                        handleMediaRemove(media as PostMedia)
                      }
                    />
                  </div>
                ) : (
                  <PostContent
                    post={{
                      ...post,
                      content: editor.content,
                      media: editor.existingMedia,
                    }}
                  />
                )}
              </div>
            </div>

            <div className="flex-shrink-0 flex items-center gap-4 text-sm text-gray-600">
              <div className="flex items-center gap-1">
                <Calendar className="w-4 h-4" />
                <span>
                  {post.scheduled_at && dateTimeFormatter(post.scheduled_at)}
                </span>
              </div>
            </div>

            {!isEditing && post.topics.length > 0 && (
              <div className="flex-shrink-0 space-y-2">
                <p className="text-sm font-medium text-gray-700">Categories:</p>
                <div className="flex flex-wrap gap-1">
                  {post.topics.map((topic, idx) => (
                    <Badge key={idx} variant="outline" className="text-xs">
                      {topic}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        <DialogFooter className="flex-shrink-0 gap-2">
          {isEditing ? (
            <>
              <Button
                variant="outline"
                onClick={handleCancel}
                disabled={isProcessing || isSaving}
              >
                <X className="w-4 h-4 mr-2" />
                Cancel
              </Button>
              <Button onClick={handleSave} disabled={isProcessing || isSaving}>
                {isProcessing || isSaving ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Save className="w-4 h-4 mr-2" />
                )}
                Save Changes
              </Button>
            </>
          ) : (
            <>
              {onSaveForLater && (
                <Button
                  variant="outline"
                  onClick={() => post && onSaveForLater(post)}
                  disabled={isProcessing}
                >
                  {isProcessing ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Bookmark className="w-4 h-4 mr-2" />
                      Remove from Schedule
                    </>
                  )}
                </Button>
              )}
              <Button variant="outline" onClick={() => setIsEditing(true)}>
                <Edit3 className="w-4 h-4 mr-2" />
                Edit
              </Button>
              {onReschedule && (
                <Button
                  variant="default"
                  onClick={() => post && onReschedule(post)}
                >
                  <Calendar className="w-4 h-4 mr-2" />
                  {isNewPost ? "Schedule" : "Reschedule"}
                </Button>
              )}
              {onDelete && (
                <Button
                  variant="destructive"
                  onClick={() => post && onDelete(post)}
                  disabled={isProcessing}
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete
                </Button>
              )}
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

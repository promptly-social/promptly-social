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
  const [editedContent, setEditedContent] = React.useState("");
  const [editedTopics, setEditedTopics] = React.useState<string[]>([]);
  const [topicInput, setTopicInput] = React.useState("");
  const [isPublishing, setIsPublishing] = React.useState(false);
  const [articleUrl, setArticleUrl] = React.useState("");
  const [mediaFiles, setMediaFiles] = React.useState<File[]>([]);
  const [existingMedia, setExistingMedia] = React.useState<PostMedia[]>([]);
  const [mediaPreviews, setMediaPreviews] = React.useState<string[]>([]);

  React.useEffect(() => {
    if (post) {
      setEditedContent(post.content);
      setEditedTopics(post.topics || []);
      setExistingMedia(post.media || []);
      setArticleUrl(post.article_url || "");
    }
  }, [post]);

  React.useEffect(() => {
    if (!isOpen) {
      setIsEditing(false);
      setIsPublishing(false);
      setArticleUrl("");
      setMediaFiles([]);
      mediaPreviews.forEach(URL.revokeObjectURL);
      setMediaPreviews([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  const handleTopicAdd = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && topicInput.trim() !== "") {
      e.preventDefault();
      const newTopic = topicInput.trim();
      if (!editedTopics.includes(newTopic)) {
        setEditedTopics([...editedTopics, newTopic]);
      }
      setTopicInput("");
    }
  };

  const handleTopicRemove = (topicToRemove: string) => {
    setEditedTopics(editedTopics.filter((topic) => topic !== topicToRemove));
  };

  const handleMediaFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      // Revoke previous previews
      mediaPreviews.forEach(URL.revokeObjectURL);

      const file = e.target.files[0];
      setMediaFiles([file]);
      setMediaPreviews([URL.createObjectURL(file)]);
    }
  };

  const handleMediaRemove = async (media: PostMedia | File, index?: number) => {
    if ("id" in media) {
      // It's a PostMedia object, so it exists on the server
      if (post) {
        try {
          await postsApi.deletePostMedia(post.id, media.id);
          setExistingMedia((prev) => prev.filter((m) => m.id !== media.id));
          if (media.media_type === "article") {
            setArticleUrl("");
          }
        } catch (error) {
          console.error("Failed to delete media:", error);
          // TODO: Add user-facing error notification
        }
      }
    } else {
      // It's a File object, so it's a new file that hasn't been uploaded yet
      if (index === undefined) return;
      setMediaFiles((prev) => prev.filter((_f, i) => i !== index));
      setMediaPreviews((prev) => {
        const newPreviews = [...prev];
        const [removed] = newPreviews.splice(index, 1);
        URL.revokeObjectURL(removed);
        return newPreviews;
      });
    }
  };

  // Save handler that works whether parent supplies an `onUpdatePost` callback or not.
  const handleSave = async () => {
    if (!post) return;

    try {
      // If the parent provided an explicit updater, use that first so it can manage its own cache/state.
      if (onUpdatePost) {
        await onUpdatePost(post.id, editedContent, editedTopics);
      } else {
        // Fallback: update the post directly via API.
        await postsApi.updatePost(post.id, {
          content: editedContent,
          topics: editedTopics,
        });
      }

      // Handle article URL changes (including clearing the field)
      await postsApi.updatePost(post.id, { article_url: articleUrl || null });

      // Upload any newly-selected media files
      if (mediaFiles.length > 0) {
        await postsApi.uploadPostMedia(post.id, mediaFiles);
      }

      setIsEditing(false);
      // TODO: consider refreshing post data so UI reflects new media without closing dialog
    } catch (error) {
      console.error("Failed to save scheduled post edits:", error);
      // You might want to show a toast notification here
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
      setEditedContent(post.content);
      setEditedTopics(post.topics || []);
      setExistingMedia(post.media || []);
      const article = post.media?.find((m) => m.media_type === "article");
      setArticleUrl(post.article_url || article?.gcs_url || "");
    }
    setMediaFiles([]);
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
                      content={editedContent}
                      onContentChange={setEditedContent}
                      topics={editedTopics}
                      topicInput={topicInput}
                      onTopicInputChange={setTopicInput}
                      onTopicAdd={() => {
                        if (topicInput.trim() !== "") {
                          const newTopic = topicInput.trim();
                          if (!editedTopics.includes(newTopic)) {
                            setEditedTopics([...editedTopics, newTopic]);
                          }
                          setTopicInput("");
                        }
                      }}
                      onTopicRemove={handleTopicRemove}
                      articleUrl={articleUrl}
                      onArticleUrlChange={setArticleUrl}
                      existingMedia={existingMedia}
                      mediaFiles={mediaFiles}
                      mediaPreviews={mediaPreviews}
                      onMediaFileChange={handleMediaFileChange}
                      onExistingMediaRemove={(media) =>
                        handleMediaRemove(media)
                      }
                      onNewMediaRemove={(file, index) =>
                        handleMediaRemove(file, index)
                      }
                    />
                  </div>
                ) : (
                  <PostContent post={{ ...post, content: editedContent }} />
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
                disabled={isProcessing}
              >
                <X className="w-4 h-4 mr-2" />
                Cancel
              </Button>
              <Button onClick={handleSave} disabled={isProcessing}>
                {isProcessing ? (
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

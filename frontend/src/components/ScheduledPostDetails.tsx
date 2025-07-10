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
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Calendar,
  Bookmark,
  Edit3,
  Trash2,
  RefreshCw,
  Save,
  X,
  Share2,
} from "lucide-react";
import { Post, postsApi } from "@/lib/posts-api";
import { PostCardHeader } from "./PostCardHeader";
import { PostContent } from "./PostContent";
import { Textarea } from "./ui/textarea";
import { Input } from "./ui/input";
import { Label } from "./ui/label";

interface ScheduledPostDetailsProps {
  isOpen: boolean;
  onClose: () => void;
  post: Post | null;
  onSaveForLater?: (post: Post) => void;
  onReschedule?: (post: Post) => void;
  onDelete?: (post: Post) => void;
  onUpdatePost?: (postId: string, newContent: string) => Promise<void>;
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
  const [isPublishing, setIsPublishing] = React.useState(false);
  const [articleUrl, setArticleUrl] = React.useState("");
  const [mediaFile, setMediaFile] = React.useState<File | null>(null);

  React.useEffect(() => {
    if (post) {
      setEditedContent(post.content);
      setArticleUrl(post.media_url || "");
    }
  }, [post]);

  React.useEffect(() => {
    if (!isOpen) {
      setIsEditing(false);
      setIsPublishing(false);
      setArticleUrl("");
      setMediaFile(null);
    }
  }, [isOpen]);

  const handleSave = async () => {
    if (post && onUpdatePost) {
      await onUpdatePost(post.id, editedContent);

      if (articleUrl) {
        await postsApi.updatePost(post.id, {
          media_type: "article",
          media_url: articleUrl,
        });
      } else if (mediaFile) {
        await postsApi.uploadPostMedia(post.id, mediaFile);
      }

      setIsEditing(false);
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
                  <Textarea
                    value={editedContent}
                    onChange={(e) => setEditedContent(e.target.value)}
                    className="min-h-[200px] max-h-[400px] resize-y w-full"
                    autoFocus
                  />
                ) : (
                  <PostContent post={{ ...post, content: editedContent }} />
                )}
              </div>
              {isEditing && (
                <div className="space-y-4 pt-4">
                  <div>
                    <Label htmlFor="article-url">Article URL</Label>
                    <Input
                      id="article-url"
                      placeholder="https://example.com/article"
                      value={articleUrl}
                      onChange={(e) => setArticleUrl(e.target.value)}
                      disabled={!!mediaFile}
                    />
                  </div>
                  <div className="text-center text-sm text-gray-500">OR</div>
                  <div>
                    <Label htmlFor="media-file">Image/Video</Label>
                    <Input
                      id="media-file"
                      type="file"
                      onChange={(e) =>
                        setMediaFile(e.target.files?.[0] || null)
                      }
                      accept="image/*,video/*"
                      disabled={!!articleUrl}
                    />
                  </div>
                </div>
              )}

              {post.media_url && !isEditing && (
                <div className="mt-4">
                  <p className="text-sm font-medium text-gray-700">
                    Attachment:
                  </p>
                  {post.media_type === "article" ? (
                    <a
                      href={post.media_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-500 hover:underline"
                    >
                      {post.media_url}
                    </a>
                  ) : (
                    <img
                      src={post.media_url}
                      alt="Post media"
                      className="mt-2 rounded-lg border max-h-60"
                    />
                  )}
                </div>
              )}
            </div>

            <div className="flex-shrink-0 flex items-center gap-4 text-sm text-gray-600">
              <div className="flex items-center gap-1">
                <Calendar className="w-4 h-4" />
                <span>
                  {post.scheduled_at && dateTimeFormatter(post.scheduled_at)}
                </span>
              </div>
            </div>

            {post.topics.length > 0 && (
              <div className="flex-shrink-0 space-y-2">
                <p className="text-sm font-medium text-gray-700">Topics:</p>
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
              {/* {post?.status === "scheduled" && (
                <Button
                  onClick={handlePublish}
                  disabled={isPublishing || isProcessing}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {isPublishing ? (
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Share2 className="w-4 h-4 mr-2" />
                  )}
                  Post Now
                </Button>
              )} */}
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
                      Save for Later
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

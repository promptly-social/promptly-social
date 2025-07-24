import React from "react";
import { Button } from "@/components/ui/button";
import { RefreshCw, Calendar, X, Bookmark, Send, Edit3 } from "lucide-react";
import { Post } from "@/types/posts";

interface PostCardActionsProps {
  post: Post;
  savingPostId?: string | null;
  dismissingPostId?: string | null;
  postingPostId?: string | null;
  onSchedulePost?: (postId: string) => void;
  onRemoveFromSchedule?: (post: Post) => void;
  onReschedulePost?: (postId: string) => void;
  onSaveForLater?: (post: Post) => void;
  onDismissPost?: (post: Post) => void;
  onPostNow?: (post: Post) => void;
  onEdit?: () => void;
}

export const PostCardActions: React.FC<PostCardActionsProps> = ({
  post,
  savingPostId,
  dismissingPostId,
  postingPostId,
  onSchedulePost,
  onRemoveFromSchedule,
  onReschedulePost,
  onSaveForLater,
  onDismissPost,
  onPostNow,
  onEdit,
}) => {
  if (post.status === "posted") {
    return null;
  }

  return (
    <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 pt-3 border-t border-border">
      {post.status === "scheduled" ? (
        <>
          <Button
            onClick={() => onReschedulePost?.(post.id)}
            className="flex-1"
          >
            <Calendar className="w-4 h-4 mr-2" />
            Reschedule
          </Button>
          <Button
            onClick={() => onPostNow?.(post)}
            variant="outline"
            className="flex-1"
            disabled={postingPostId === post.id}
          >
            {postingPostId === post.id ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Posting...
              </>
            ) : (
              <>
                <Send className="w-4 h-4 mr-2" />
                Post Now
              </>
            )}
          </Button>
          <Button
            onClick={() => onRemoveFromSchedule?.(post)}
            variant="secondary"
            className="flex-1"
          >
            <X className="w-4 h-4 mr-2" />
            Remove from Schedule
          </Button>
        </>
      ) : (
        <>
          <Button
            onClick={() => onSchedulePost?.(post.id)}
            className="flex-1"
          >
            <Calendar className="w-4 h-4 mr-2" />
            Schedule Post
          </Button>
          <Button
            onClick={() => onPostNow?.(post)}
            variant="outline"
            className="flex-1"
            disabled={postingPostId === post.id}
          >
            {postingPostId === post.id ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Posting...
              </>
            ) : (
              <>
                <Send className="w-4 h-4 mr-2" />
                Post Now
              </>
            )}
          </Button>
        </>
      )}

      <Button
        onClick={onEdit}
        variant="outline"
        className="flex-1"
      >
        <Edit3 className="w-4 h-4 mr-2" />
        Edit
      </Button>
      <Button
        variant="destructive"
        className="flex-1"
        onClick={() => onDismissPost?.(post)}
        disabled={dismissingPostId === post.id}
      >
        {dismissingPostId === post.id ? (
          <>
            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
            Deleting...
          </>
        ) : (
          <>
            <X className="w-4 h-4 mr-2" />
            Delete
          </>
        )}
      </Button>
    </div>
  );
};

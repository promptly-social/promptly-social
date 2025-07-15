import React from "react";
import { Button } from "@/components/ui/button";
import { RefreshCw, Calendar, X, Bookmark } from "lucide-react";
import { Post } from "@/types/posts";

interface PostCardActionsProps {
  post: Post;
  savingPostId?: string | null;
  dismissingPostId?: string | null;
  onSchedulePost?: (postId: string) => void;
  onRemoveFromSchedule?: (post: Post) => void;
  onReschedulePost?: (postId: string) => void;
  onSaveForLater?: (post: Post) => void;
  onDismissPost?: (post: Post) => void;
}

export const PostCardActions: React.FC<PostCardActionsProps> = ({
  post,
  savingPostId,
  dismissingPostId,
  onSchedulePost,
  onRemoveFromSchedule,
  onReschedulePost,
  onSaveForLater,
  onDismissPost,
}) => {
  if (post.status === "posted") {
    return null;
  }

  return (
    <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 pt-3 border-t border-gray-100">
      {post.status === "scheduled" ? (
        <>
          <Button
            onClick={() => onRemoveFromSchedule?.(post)}
            variant="outline"
            className="flex-1 text-orange-600 hover:text-orange-700 hover:bg-orange-50"
          >
            <X className="w-4 h-4 mr-2" />
            Remove from Schedule
          </Button>
          <Button
            onClick={() => onReschedulePost?.(post.id)}
            className="bg-blue-600 hover:bg-blue-700 flex-1"
          >
            <Calendar className="w-4 h-4 mr-2" />
            Reschedule
          </Button>
        </>
      ) : (
        <>
          <Button
            onClick={() => onSchedulePost?.(post.id)}
            className="bg-green-600 hover:bg-green-700 flex-1"
          >
            <Calendar className="w-4 h-4 mr-2" />
            Schedule Post
          </Button>
        </>
      )}
      {post.status === "dismissed" ? (
        <Button
          onClick={() => onSaveForLater?.(post)}
          variant="outline"
          className="flex-1 text-purple-600 hover:text-purple-700 hover:bg-purple-50"
          disabled={savingPostId === post.id}
        >
          {savingPostId === post.id ? (
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
      ) : (
        <Button
          variant="outline"
          className="flex-1 text-red-600 hover:text-red-700 hover:bg-red-50"
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
      )}
    </div>
  );
};

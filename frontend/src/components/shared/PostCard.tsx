import React, { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  RefreshCw,
  Calendar,
  Clock,
  ThumbsUp,
  ThumbsDown,
  Edit3,
  Check,
  X,
  Bookmark,
  Zap,
  CheckCircle,
  XCircle,
  Info,
  MoreHorizontal,
} from "lucide-react";
import { Post } from "@/lib/posts-api";
import { PostCardHeader } from "./PostCardHeader";
import { PostContent } from "./PostContent";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface PostCardProps {
  post: Post;
  index: number;
  // Edit functionality (optional)
  editingPostId?: string | null;
  editedContent?: string;
  onStartEditing?: (post: Post) => void;
  onSaveEdit?: (postId: string) => void;
  onCancelEdit?: () => void;
  onEditContentChange?: (content: string) => void;
  // Loading states (optional)
  savingPostId?: string | null;
  dismissingPostId?: string | null;
  // Feedback (optional)
  onSubmitPositiveFeedback?: (postId: string) => void;
  onOpenNegativeFeedbackModal?: (postId: string) => void;
  // Actions (optional)
  onSchedulePost?: (postId: string) => void;
  onRemoveFromSchedule?: (post: Post) => void;
  onReschedulePost?: (postId: string) => void;
  onSaveForLater?: (post: Post) => void;
  onDismissPost?: (post: Post) => void;
}

export const PostCard: React.FC<PostCardProps> = ({
  post,
  index,
  editingPostId,
  editedContent,
  savingPostId,
  dismissingPostId,
  onStartEditing,
  onSaveEdit,
  onCancelEdit,
  onEditContentChange,
  onSubmitPositiveFeedback,
  onOpenNegativeFeedbackModal,
  onSchedulePost,
  onRemoveFromSchedule,
  onReschedulePost,
  onSaveForLater,
  onDismissPost,
}) => {
  const getStatusColor = (status: string) => {
    const statusColors: Record<string, string> = {
      suggested: "bg-blue-100 text-blue-800",
      saved: "bg-purple-100 text-purple-800",
      posted: "bg-green-100 text-green-800",
      scheduled: "bg-yellow-100 text-yellow-800",
      canceled: "bg-orange-100 text-orange-800",
      dismissed: "bg-red-100 text-red-800",
    };
    return statusColors[status] || "bg-gray-100 text-gray-800";
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "suggested":
        return <Zap className="w-3 h-3" />;
      case "posted":
        return <CheckCircle className="w-3 h-3" />;
      case "dismissed":
        return <XCircle className="w-3 h-3" />;
      case "saved":
        return <Bookmark className="w-3 h-3" />;
      default:
        return <Info className="w-3 h-3" />;
    }
  };

  const renderContentWithNewlines = (content: string) => {
    return content.split("\n").map((line, index) => (
      <React.Fragment key={index}>
        {line}
        {index < content.split("\n").length - 1 && <br />}
      </React.Fragment>
    ));
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <Card
      key={post.id}
      className="relative hover:shadow-md transition-shadow flex flex-col h-full bg-white"
    >
      <div className="flex justify-between items-start p-4">
        <div className="flex-grow">
          <PostCardHeader />
        </div>
        {onStartEditing && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreHorizontal className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onStartEditing(post)}>
                <Edit3 className="w-4 h-4 mr-2" />
                Edit Post
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>

      <CardContent className="space-y-4 flex-grow flex flex-col pt-0">
        {editingPostId === post.id ? (
          <div className="space-y-3">
            <Textarea
              value={editedContent}
              onChange={(e) => onEditContentChange?.(e.target.value)}
              className="min-h-[200px] max-h-[400px] resize-y bg-gray-50"
              placeholder="Edit your post content..."
            />
            <div className="flex gap-2">
              <Button size="sm" onClick={() => onSaveEdit?.(post.id)}>
                <Check className="w-4 h-4 mr-1" />
                Save
              </Button>
              <Button size="sm" variant="outline" onClick={onCancelEdit}>
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <PostContent post={post} />
        )}

        {post.media && post.media.length > 0 && (
          <div className="mt-4 border rounded-lg overflow-hidden">
            <img
              src={post.media[0].url}
              alt="Post media"
              className="w-full h-auto object-cover"
            />
          </div>
        )}

        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-gray-500 pt-4">
          <div className="flex items-center gap-2">
            <Badge
              className={`${getStatusColor(post.status)} text-xs`}
              variant="secondary"
            >
              {getStatusIcon(post.status)}
              <span className="ml-1 capitalize">{post.status}</span>
            </Badge>
            {post.user_feedback && (
              <Badge
                variant={
                  post.user_feedback === "positive" ? "default" : "destructive"
                }
                className="text-xs"
              >
                {post.user_feedback === "positive" ? (
                  <>
                    <ThumbsUp className="w-3 h-3 mr-1" />
                    Liked
                  </>
                ) : (
                  <>
                    <ThumbsDown className="w-3 h-3 mr-1" />
                    Disliked
                  </>
                )}
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            <span>Last updated: {formatDate(post.updated_at)}</span>
          </div>
        </div>

        {post.topics.length > 0 && (
          <div className="space-y-2 pt-2">
            <p className="text-xs sm:text-sm font-medium text-gray-700">
              Topics:
            </p>
            <div className="flex flex-wrap gap-1 sm:gap-2">
              {post.topics.map((topic, idx) => (
                <Badge key={idx} variant="outline" className="text-xs">
                  {topic}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {!post.user_feedback &&
          onSubmitPositiveFeedback &&
          onOpenNegativeFeedbackModal && (
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg mt-4">
              <span className="text-sm text-gray-600">
                How is this suggestion?
              </span>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onSubmitPositiveFeedback(post.id)}
                  className="text-green-600 hover:text-green-700 hover:bg-green-50"
                >
                  <ThumbsUp className="w-4 h-4" />
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onOpenNegativeFeedbackModal(post.id)}
                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                >
                  <ThumbsDown className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}

        <div className="flex-grow"></div>

        {post.status !== "posted" && (
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
                {post.status === "suggested" && (
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
                        Save for Later
                      </>
                    )}
                  </Button>
                )}
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
                    Save for Later
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
                    Dismissing...
                  </>
                ) : (
                  <>
                    <X className="w-4 h-4 mr-2" />
                    Dismiss
                  </>
                )}
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

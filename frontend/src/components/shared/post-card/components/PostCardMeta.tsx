import React from "react";
import { Badge } from "@/components/ui/badge";
import { Clock, Zap, CheckCircle, XCircle, Bookmark, Info } from "lucide-react";
import { Post } from "@/types/posts";

interface PostCardMetaProps {
  post: Post;
}

const getStatusColor = (status: string) => {
  const statusColors: Record<string, string> = {
    suggested: "bg-blue-100 text-blue-800",
    draft: "bg-purple-100 text-purple-800",
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
    case "draft":
      return <Bookmark className="w-3 h-3" />;
    default:
      return <Info className="w-3 h-3" />;
  }
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

const getStatusTimestamp = (post: Post) => {
  const { status, updated_at, posted_at, scheduled_at } = post;
  switch (status) {
    case "posted":
      return "Posted: " + formatDate(posted_at);
    case "scheduled":
      return "Scheduled: " + formatDate(scheduled_at);
    default:
      return "Last updated: " + formatDate(updated_at);
  }
};

export const PostCardMeta: React.FC<PostCardMetaProps> = ({ post }) => {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-gray-500 pt-4">
      <div className="flex items-center gap-2">
        <Badge
          className={`${getStatusColor(post.status)} text-xs`}
          variant="secondary"
        >
          {getStatusIcon(post.status)}
          <span className="ml-1 capitalize">{post.status}</span>
        </Badge>
      </div>
      <div className="flex items-center gap-1">
        <Clock className="w-3 h-3" />
        <span>{getStatusTimestamp(post)}</span>
      </div>
    </div>
  );
};

import React from "react";
import { Badge } from "@/components/ui/badge";
import { Clock, Zap, CheckCircle, XCircle, Bookmark, Info } from "lucide-react";
import { Post } from "@/types/posts";

interface PostCardMetaProps {
  post: Post;
}

const getStatusColor = (status: string) => {
  const statusColors: Record<string, string> = {
    suggested: "bg-accent/20 text-accent-foreground border-accent/30",
    draft: "bg-secondary/20 text-secondary-foreground border-secondary/30",
    posted: "bg-primary/10 text-primary border-primary/40",
    scheduled: "bg-accent/20 text-accent-foreground border-accent/30",
    canceled: "bg-secondary/20 text-secondary-foreground border-secondary/30",
    dismissed: "bg-destructive/20 text-destructive-foreground border-destructive/30",
  };
  return statusColors[status] || "bg-muted text-muted-foreground border-border";
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
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-muted-foreground pt-4">
      <div className="flex items-center gap-2">
        <Badge
          className={`${getStatusColor(post.status)} text-xs border`}
          variant="outline"
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

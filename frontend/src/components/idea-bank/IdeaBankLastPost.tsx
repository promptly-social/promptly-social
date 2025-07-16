import React from "react";
import { ExternalLink } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { SuggestedPost } from "@/lib/idea-bank-api";

interface IdeaBankLastPostProps {
  latestPost?: SuggestedPost;
  onView(post: SuggestedPost): void;
}

const getStatusColor = (status: string) => {
  const statusColors: Record<string, string> = {
    suggested: "bg-gray-100 text-gray-800",
    draft: "bg-purple-100 text-purple-800",
    posted: "bg-green-100 text-green-800",
    scheduled: "bg-yellow-100 text-yellow-800",
    canceled: "bg-orange-100 text-orange-800",
    dismissed: "bg-red-100 text-red-800",
  };
  return statusColors[status] || "bg-gray-100 text-gray-800";
};

const IdeaBankLastPost: React.FC<IdeaBankLastPostProps> = ({
  latestPost,
  onView,
}) => {
  if (!latestPost) {
    return <span className="text-muted-foreground">No post created yet</span>;
  }

  return (
    <div className="space-y-1">
      <button
        onClick={() => onView(latestPost)}
        className="text-blue-600 hover:text-blue-800 hover:underline flex items-center gap-1"
      >
        View Post
        <ExternalLink className="w-3 h-3" />
      </button>
      <div>
        <Badge
          className={getStatusColor(latestPost.status)}
          variant="secondary"
        >
          {latestPost.status.charAt(0).toUpperCase() +
            latestPost.status.slice(1)}
        </Badge>
      </div>
    </div>
  );
};

export default IdeaBankLastPost;

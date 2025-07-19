import React from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Calendar as CalendarIcon } from "lucide-react";
import { Post } from "@/types/posts";

interface ScheduledPostsListProps {
  posts: Post[];
  isLoading: boolean;
  onPostClick: (post: Post) => void;
  formatTime: (dateString: string) => string;
}

export const ScheduledPostsList: React.FC<ScheduledPostsListProps> = ({
  posts,
  isLoading,
  onPostClick,
  formatTime,
}) => {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (posts.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <CalendarIcon className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p className="text-sm">No posts scheduled yet</p>
      </div>
    );
  }

  return (
    <ScrollArea className="h-full">
      <div className="space-y-2 pr-2">
        {posts.map((scheduledPost) => (
          <Card
            key={scheduledPost.id}
            className="cursor-pointer hover:bg-gray-50 transition-colors"
            onClick={() => onPostClick(scheduledPost)}
          >
            <CardContent className="p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-gray-500">
                  {scheduledPost.scheduled_at &&
                    formatTime(scheduledPost.scheduled_at)}
                </span>
              </div>
              <p className="text-xs text-gray-800 line-clamp-2">
                {scheduledPost.content}
              </p>
              {scheduledPost.topics.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {scheduledPost.topics.slice(0, 2).map((topic) => (
                    <Badge
                      key={topic}
                      variant="secondary"
                      className="text-xs px-1 py-0"
                    >
                      {topic}
                    </Badge>
                  ))}
                  {scheduledPost.topics.length > 2 && (
                    <Badge
                      variant="outline"
                      className="text-xs px-1 py-0"
                    >
                      +{scheduledPost.topics.length - 2}
                    </Badge>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </ScrollArea>
  );
};

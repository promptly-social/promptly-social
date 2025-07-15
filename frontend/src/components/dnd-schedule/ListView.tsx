import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ListViewPostCard } from "./ListViewPostCard";
import { Post } from "@/types/posts";
import { ChevronLeft, ChevronRight, Calendar } from "lucide-react";

interface PostListViewProps {
  posts: Post[];
  title: string;
  onPostClick: (post: Post) => void;
  isDragDropEnabled: boolean;
  onNavigate?: (direction: "prev" | "next") => void;
  showNavigation?: boolean;
}

const PostListView: React.FC<PostListViewProps> = ({
  posts,
  title,
  onPostClick,
  isDragDropEnabled,
  onNavigate,
  showNavigation = false,
}) => {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        {showNavigation && onNavigate ? (
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onNavigate("prev")}
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <h3 className="text-lg font-semibold">{title}</h3>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onNavigate("next")}
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        ) : (
          <h3 className="text-lg font-semibold">{title}</h3>
        )}
      </div>

      {posts.length > 0 ? (
        <div className="space-y-3">
          {posts.map((post) => (
            <ListViewPostCard
              key={post.id}
              post={post}
              onClick={() => onPostClick(post)}
              className="hover:shadow-md transition-shadow"
              showDragHandle={isDragDropEnabled}
              compact={false}
            />
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="py-12 text-center">
            <Calendar className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <h3 className="text-lg font-medium mb-2">No Scheduled Posts</h3>
            <p className="text-gray-600">
              {showNavigation
                ? "No posts scheduled for this period."
                : "Your scheduled posts will appear here. Start by scheduling some posts!"}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

interface ListViewProps {
  posts: Post[];
  onPostClick: (post: Post) => void;
  isDragDropEnabled: boolean;
}

export const ListView: React.FC<ListViewProps> = ({
  posts,
  onPostClick,
  isDragDropEnabled,
}) => {
  return (
    <PostListView
      posts={posts}
      title="Upcoming Posts"
      onPostClick={onPostClick}
      isDragDropEnabled={isDragDropEnabled}
    />
  );
};

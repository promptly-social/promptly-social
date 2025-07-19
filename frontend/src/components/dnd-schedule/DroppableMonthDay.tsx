import React from "react";
import { useDroppable } from "@dnd-kit/core";
import { Post } from "@/types/posts";
import { MonthViewPostCard } from "./MonthViewPostCard";
import { useIsMobile } from "@/hooks/use-mobile";

interface DroppableMonthDayProps {
  date: Date;
  posts: Post[];
  isCurrentMonth: boolean;
  isToday: boolean;
  onPostClick?: (post: Post) => void;
  className?: string;
  showDropZone?: boolean;
}

// Utility function to separate posts by type
const separatePostsByType = (posts: Post[]) => {
  const scheduledPosts = posts.filter(post => post.status === 'scheduled');
  const postedPosts = posts.filter(post => post.status === 'posted');
  return { scheduledPosts, postedPosts };
};

export const DroppableMonthDay: React.FC<DroppableMonthDayProps> = ({
  date,
  posts,
  isCurrentMonth,
  isToday,
  onPostClick,
  className = "",
  showDropZone = true,
}) => {
  const { setNodeRef, isOver } = useDroppable({
    id: `day-${date.toISOString().split("T")[0]}`,
    data: {
      type: "day",
      date,
    },
    disabled: !showDropZone,
  });

  const isMobile = useIsMobile();

  // Check if this date is in the past
  const isPastDate = (() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const checkDate = new Date(date);
    checkDate.setHours(0, 0, 0, 0);
    return checkDate < today;
  })();

  // Separate posts by type for different handling
  const { scheduledPosts, postedPosts } = separatePostsByType(posts);
  const totalPosts = scheduledPosts.length + postedPosts.length;
  
  const maxPostsToShow = isMobile ? 1 : 2;

  return (
    <div
      ref={setNodeRef}
      className={`min-h-[140px] border-r border-b last:border-r-0 transition-all duration-200 ${
        !isCurrentMonth ? "bg-gray-50" : "bg-white"
      } ${isToday ? "bg-blue-50 ring-1 ring-blue-200" : ""} ${
        isOver && !isPastDate && isCurrentMonth && showDropZone
          ? "ring-2 ring-green-500 bg-green-50 scale-[1.02] shadow-md"
          : ""
      } ${
        isPastDate
          ? "bg-gray-100 opacity-60"
          : isCurrentMonth
          ? "hover:bg-gray-50"
          : ""
      } ${className}`}
    >
      <div className="p-2">
        <div className="flex items-center justify-between mb-2">
          <span
            className={`text-sm font-medium ${
              !isCurrentMonth
                ? "text-gray-400"
                : isToday
                ? "text-blue-600 font-bold"
                : isPastDate
                ? "text-gray-500"
                : "text-gray-900"
            }`}
          >
            {date.getDate()}
          </span>
        </div>

        <div
          className="space-y-1.5 p-1"
          style={{ maxHeight: "120px", overflowY: "auto" }}
        >
          {/* Render posted posts first (they appear at top) */}
          {postedPosts.map((post) => (
            <MonthViewPostCard
              key={post.id}
              post={post}
              onClick={() => onPostClick?.(post)}
              className="text-xs"
              showDragHandle={false} // Posted posts are not draggable
              compact={true}
              enableDroppable={false}
              isPosted={true} // New prop to identify posted posts
            />
          ))}

          {/* Add spacing between posted and scheduled posts if both exist */}
          {postedPosts.length > 0 && scheduledPosts.length > 0 && (
            <div className="border-t border-gray-200 my-1.5" />
          )}

          {/* Render scheduled posts (they can be dragged) */}
          {scheduledPosts.map((post) => (
            <MonthViewPostCard
              key={post.id}
              post={post}
              onClick={() => onPostClick?.(post)}
              className="text-xs"
              showDragHandle={showDropZone}
              compact={true}
              enableDroppable={false}
              isPosted={false}
            />
          ))}

          {totalPosts > maxPostsToShow && (
            <div className="text-center">
              <span className="text-xs text-gray-500">
                +{totalPosts - maxPostsToShow} more
              </span>
            </div>
          )}

          {totalPosts === 0 &&
            isOver &&
            !isPastDate &&
            isCurrentMonth &&
            showDropZone && (
              <div className="text-center">
                <span className="text-xs text-green-600 font-medium">
                  Drop here
                </span>
              </div>
            )}

          {totalPosts === 0 && isPastDate && isCurrentMonth && (
            <div className="text-center">
              <span className="text-xs text-gray-400">Past</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

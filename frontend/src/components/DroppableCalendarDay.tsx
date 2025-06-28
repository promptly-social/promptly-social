import React from "react";
import { useDroppable } from "@dnd-kit/core";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Post } from "@/lib/posts-api";

interface DroppableCalendarDayProps {
  date: Date;
  posts: Post[];
  isToday?: boolean;
  className?: string;
  showDropZone?: boolean;
}

export const DroppableCalendarDay: React.FC<DroppableCalendarDayProps> = ({
  date,
  posts,
  isToday = false,
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

  // Check if this date is in the past
  const isPastDate = (() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const checkDate = new Date(date);
    checkDate.setHours(0, 0, 0, 0);
    return checkDate < today;
  })();

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    });
  };

  return (
    <Card
      ref={setNodeRef}
      className={`min-h-[200px] transition-all duration-200 ${
        isToday ? "ring-2 ring-blue-500 bg-blue-50" : ""
      } ${
        isOver && !isPastDate && showDropZone
          ? "ring-2 ring-green-500 bg-green-50 scale-[1.02] shadow-lg"
          : ""
      } ${
        isPastDate ? "bg-gray-100 opacity-60" : "hover:shadow-md bg-white"
      } ${className}`}
    >
      <CardHeader className="pb-2">
        <div className="flex flex-col items-center">
          <h4
            className={`font-medium text-sm ${
              isToday
                ? "text-blue-600"
                : isPastDate
                ? "text-gray-500"
                : "text-gray-900"
            }`}
          >
            {date.toLocaleDateString("en-US", {
              weekday: "short",
            })}
          </h4>
          <span
            className={`text-lg font-bold ${
              isToday
                ? "text-blue-600"
                : isPastDate
                ? "text-gray-500"
                : "text-gray-900"
            }`}
          >
            {date.getDate()}
          </span>
          {isToday && (
            <span className="text-xs text-blue-600 font-medium">Today</span>
          )}
          {isPastDate && (
            <span className="text-xs text-gray-500 font-medium">Past</span>
          )}
        </div>
      </CardHeader>
      <CardContent className="pt-0 px-3">
        {posts.length > 0 ? (
          <div className="space-y-2">
            <Badge variant="outline" className="text-xs mb-2">
              {posts.length} post{posts.length > 1 ? "s" : ""}
            </Badge>
            {posts.slice(0, 3).map((post) => (
              <div
                key={post.id}
                className="text-xs p-2 bg-gray-50 rounded border"
              >
                <div className="font-medium text-gray-900 mb-1">
                  {post.scheduled_at && formatTime(post.scheduled_at)}
                </div>
                <div className="text-gray-600 truncate">
                  {post.content.substring(0, 50)}...
                </div>
              </div>
            ))}
            {posts.length > 3 && (
              <div className="text-center text-xs text-gray-500">
                +{posts.length - 3} more
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-6">
            <p
              className={`text-xs ${
                isOver && !isPastDate && showDropZone
                  ? "text-green-600 font-medium"
                  : isPastDate
                  ? "text-gray-400"
                  : "text-gray-400"
              }`}
            >
              {isOver && !isPastDate && showDropZone
                ? "Drop here to schedule"
                : isPastDate
                ? "Cannot schedule in past"
                : "No posts"}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

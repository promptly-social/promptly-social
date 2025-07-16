import React from "react";
import { Button } from "@/components/ui/button";
import { DroppableMonthDay } from "./DroppableMonthDay";
import { Post } from "@/types/posts";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface MonthViewProps {
  currentDate: Date;
  posts: Post[];
  onNavigateMonth: (direction: "prev" | "next") => void;
  onPostClick: (post: Post) => void;
  isDragDropEnabled: boolean;
}

const getMonthCalendarDays = (baseDate: Date) => {
  const year = baseDate.getFullYear();
  const month = baseDate.getMonth();

  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);

  const startDate = new Date(firstDay);
  startDate.setDate(firstDay.getDate() - firstDay.getDay());

  const endDate = new Date(lastDay);
  endDate.setDate(lastDay.getDate() + (6 - lastDay.getDay()));

  const days = [];
  const day = new Date(startDate);

  while (day <= endDate) {
    days.push(new Date(day));
    day.setDate(day.getDate() + 1);
  }

  return days;
};

const getPostsForDate = (date: Date, posts: Post[]) => {
  return posts.filter((post) => {
    if (!post.scheduled_at) return false;
    const postDate = new Date(post.scheduled_at);
    return (
      postDate.getDate() === date.getDate() &&
      postDate.getMonth() === date.getMonth() &&
      postDate.getFullYear() === date.getFullYear()
    );
  });
};

export const MonthView: React.FC<MonthViewProps> = ({
  currentDate,
  posts,
  onNavigateMonth,
  onPostClick,
  isDragDropEnabled,
}) => {
  const calendarDays = getMonthCalendarDays(currentDate);
  const currentMonth = currentDate.getMonth();
  const today = new Date();
  const monthTitle = currentDate.toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onNavigateMonth("prev")}
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <h3 className="text-lg font-semibold">{monthTitle}</h3>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onNavigateMonth("next")}
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>

      <div className="bg-white rounded-lg border">
        <div className="grid grid-cols-7 border-b">
          {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
            <div
              key={day}
              className="p-3 text-center text-sm font-medium text-gray-600 border-r last:border-r-0"
            >
              {day}
            </div>
          ))}
        </div>

        <div className="grid grid-cols-7">
          {calendarDays.map((date, idx) => {
            const postsForDate = getPostsForDate(date, posts);
            const isCurrentMonth = date.getMonth() === currentMonth;
            const isToday = date.toDateString() === today.toDateString();

            return (
              <DroppableMonthDay
                key={idx}
                date={date}
                posts={postsForDate}
                isCurrentMonth={isCurrentMonth}
                isToday={isToday}
                onPostClick={onPostClick}
                showDropZone={isDragDropEnabled}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
};

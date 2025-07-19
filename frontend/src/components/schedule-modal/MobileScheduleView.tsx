import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { DateTimeSelector } from "./DateTimeSelector";
import { ScheduledPostsList } from "./ScheduledPostsList";
import { Post } from "@/types/posts";

interface MobileScheduleViewProps {
  selectedDate: Date;
  selectedHour: string;
  selectedMinute: string;
  onDateSelect: (date: Date) => void;
  onHourChange: (hour: string) => void;
  onMinuteChange: (minute: string) => void;
  availableHours: string[];
  availableMinutes: string[];
  datesWithScheduledPosts: Date[];
  onMonthChange: (month: Date) => void;
  isDateDisabled: (date: Date) => boolean;
  scheduledPosts: Post[];
  isLoadingScheduledPosts: boolean;
  onPostClick: (post: Post) => void;
  formatTime: (dateString: string) => string;
  headerText: string;
  headerGradientClass: string;
}

export const MobileScheduleView: React.FC<MobileScheduleViewProps> = ({
  selectedDate,
  selectedHour,
  selectedMinute,
  onDateSelect,
  onHourChange,
  onMinuteChange,
  availableHours,
  availableMinutes,
  datesWithScheduledPosts,
  onMonthChange,
  isDateDisabled,
  scheduledPosts,
  isLoadingScheduledPosts,
  onPostClick,
  formatTime,
  headerText,
  headerGradientClass,
}) => {
  return (
    <div className="space-y-4">
      <Card className={`border-l-4 ${headerGradientClass}`}>
        <CardContent className="p-4">
          <p className="text-sm font-medium text-gray-700 mb-2">
            {headerText}
          </p>
          <p className="text-lg font-semibold text-gray-900">
            {selectedDate.toLocaleDateString("en-US", {
              weekday: "long",
              year: "numeric",
              month: "long",
              day: "numeric",
            })}{" "}
            at {selectedHour}:{selectedMinute}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <DateTimeSelector
            selectedDate={selectedDate}
            selectedHour={selectedHour}
            selectedMinute={selectedMinute}
            onDateSelect={onDateSelect}
            onHourChange={onHourChange}
            onMinuteChange={onMinuteChange}
            availableHours={availableHours}
            availableMinutes={availableMinutes}
            datesWithScheduledPosts={datesWithScheduledPosts}
            onMonthChange={onMonthChange}
            isDateDisabled={isDateDisabled}
          />
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <h3 className="font-medium mb-3">Scheduled Posts</h3>
          <div className="h-48">
            <ScheduledPostsList
              posts={scheduledPosts}
              isLoading={isLoadingScheduledPosts}
              onPostClick={onPostClick}
              formatTime={formatTime}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

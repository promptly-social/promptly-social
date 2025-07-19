import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { RefreshCw, Clock, CalendarIcon } from "lucide-react";
import { format } from "date-fns";
import { Post } from "@/types/posts";

interface PushPostsDialogProps {
  isOpen: boolean;
  onClose: () => void;
  posts: Post[];
  selectedDate: Date;
  onScheduleAnyway: () => void;
  onPushAndSchedule: () => void;
  isPushing: boolean;
  isSubmitting: boolean;
  formatTime: (dateString: string) => string;
  submittingText: string;
}

export const PushPostsDialog: React.FC<PushPostsDialogProps> = ({
  isOpen,
  onClose,
  posts,
  selectedDate,
  onScheduleAnyway,
  onPushAndSchedule,
  isPushing,
  isSubmitting,
  formatTime,
  submittingText,
}) => {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <RefreshCw className="w-5 h-5 text-blue-600" />
            Posts Already Scheduled
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            You have {posts.length} post
            {posts.length !== 1 ? "s" : ""} already scheduled on{" "}
            {format(selectedDate, "MMMM d, yyyy")}:
          </p>

          <div className="space-y-2 max-h-40 overflow-y-auto">
            {posts.map((dayPost) => (
              <div key={dayPost.id} className="bg-gray-50 p-3 rounded-lg">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-gray-500">
                    {dayPost.scheduled_at && formatTime(dayPost.scheduled_at)}
                  </span>
                </div>
                <p className="text-sm text-gray-800 line-clamp-2">
                  {dayPost.content}
                </p>
              </div>
            ))}
          </div>

          <p className="text-sm text-gray-600">
            Would you like to push the existing posts to the next available day
            and schedule this post on {format(selectedDate, "MMMM d")}?
          </p>
        </div>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={onScheduleAnyway}
            disabled={isSubmitting || isPushing}
            variant="outline"
          >
            {isSubmitting ? (
              <>
                <Clock className="w-4 h-4 mr-2 animate-spin" />
                {submittingText}
              </>
            ) : (
              <>
                <CalendarIcon className="w-4 h-4 mr-2" />
                Schedule Anyway
              </>
            )}
          </Button>
          <Button
            onClick={onPushAndSchedule}
            disabled={isSubmitting || isPushing}
          >
            {isPushing ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Pushing Posts...
              </>
            ) : isSubmitting ? (
              <>
                <Clock className="w-4 h-4 mr-2 animate-spin" />
                {submittingText}
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4 mr-2" />
                Push & Schedule
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent } from "@/components/ui/card";
import { Calendar as CalendarIcon, Clock, Info } from "lucide-react";
import { Post } from "@/lib/posts-api";
import { useIsMobile } from "@/hooks/use-mobile";
import { ScheduledPostDetails } from "@/components/ScheduledPostDetails";

interface RescheduleModalProps {
  isOpen: boolean;
  onClose: () => void;
  post: Post | null;
  scheduledPosts: Post[];
  onReschedule: (postId: string, scheduledAt: string) => void;
  isRescheduling?: boolean;
}

export const RescheduleModal: React.FC<RescheduleModalProps> = ({
  isOpen,
  onClose,
  post,
  scheduledPosts,
  onReschedule,
  isRescheduling = false,
}) => {
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [selectedHour, setSelectedHour] = useState<string>("09");
  const [selectedMinute, setSelectedMinute] = useState<string>("00");
  const [conflictingPosts, setConflictingPosts] = useState<Post[]>([]);
  const [showConflictDialog, setShowConflictDialog] = useState(false);
  const [selectedScheduledPost, setSelectedScheduledPost] =
    useState<Post | null>(null);

  const isMobile = useIsMobile();

  // Reset form when modal opens/closes
  useEffect(() => {
    if (isOpen && post) {
      // Set initial date/time to current scheduled time or tomorrow
      if (post.scheduled_at) {
        const currentScheduled = new Date(post.scheduled_at);
        setSelectedDate(currentScheduled);
        setSelectedHour(
          currentScheduled.getHours().toString().padStart(2, "0")
        );
        setSelectedMinute(
          currentScheduled.getMinutes().toString().padStart(2, "0")
        );
      } else {
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        setSelectedDate(tomorrow);
        setSelectedHour("09");
        setSelectedMinute("00");
      }
      setConflictingPosts([]);
      setShowConflictDialog(false);
      setSelectedScheduledPost(null);
    }
  }, [isOpen, post]);

  const formatDateTime = (date: Date, hour: string, minute: string) => {
    const dateTime = new Date(date);
    dateTime.setHours(parseInt(hour), parseInt(minute), 0, 0);
    return dateTime.toISOString();
  };

  // Check for conflicts when date/time changes (excluding current post)
  const checkForConflicts = (date: Date, hour: string, minute: string) => {
    const scheduledAt = formatDateTime(date, hour, minute);
    const scheduledTime = new Date(scheduledAt);

    const conflicts = scheduledPosts.filter((p) => {
      if (!p.scheduled_at || p.id === post?.id) return false;
      const postTime = new Date(p.scheduled_at);
      // Check if posts are scheduled at the exact same time
      return postTime.getTime() === scheduledTime.getTime();
    });

    setConflictingPosts(conflicts);
  };

  // Update conflicts when date/time selection changes
  useEffect(() => {
    checkForConflicts(selectedDate, selectedHour, selectedMinute);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDate, selectedHour, selectedMinute, scheduledPosts, post]);

  const handleReschedule = () => {
    if (!post) return;

    if (conflictingPosts.length > 0) {
      setShowConflictDialog(true);
      return;
    }

    const scheduledAt = formatDateTime(
      selectedDate,
      selectedHour,
      selectedMinute
    );
    onReschedule(post.id, scheduledAt);
  };

  const handleConfirmReschedule = () => {
    if (!post) return;
    const scheduledAt = formatDateTime(
      selectedDate,
      selectedHour,
      selectedMinute
    );
    onReschedule(post.id, scheduledAt);
    setShowConflictDialog(false);
  };

  // Get dates that have scheduled posts for calendar highlighting
  const getDatesWithScheduledPosts = () => {
    const datesWithPosts = new Set<string>();
    scheduledPosts.forEach((post) => {
      if (post.scheduled_at) {
        const date = new Date(post.scheduled_at);
        datesWithPosts.add(date.toDateString());
      }
    });
    return Array.from(datesWithPosts).map((dateString) => new Date(dateString));
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    });
  };

  const hours = Array.from({ length: 24 }, (_, i) =>
    i.toString().padStart(2, "0")
  );
  const minutes = Array.from({ length: 60 }, (_, i) =>
    i.toString().padStart(2, "0")
  ).filter((_, i) => i % 15 === 0); // 15-minute intervals

  if (!post) return null;

  const datesWithScheduledPosts = getDatesWithScheduledPosts();

  return (
    <>
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent
          className={`${
            isMobile ? "max-w-full h-[95vh] mx-2" : "max-w-4xl h-[85vh]"
          } flex flex-col`}
        >
          <DialogHeader className="flex-shrink-0">
            <DialogTitle className="flex items-center gap-2">
              <CalendarIcon className="w-5 h-5" />
              Reschedule Post
            </DialogTitle>
          </DialogHeader>

          {/* Prominent Rescheduling Time Display */}
          <div className="flex-shrink-0 bg-gradient-to-r from-orange-50 to-red-50 border border-orange-200 rounded-lg p-3 mb-3">
            <div className="text-center">
              <p className="text-xs text-gray-600 mb-1">
                📅 Post will be rescheduled to
              </p>
              <p
                className={`font-bold text-gray-900 ${
                  isMobile ? "text-lg" : "text-xl"
                }`}
              >
                {new Date(
                  formatDateTime(selectedDate, selectedHour, selectedMinute)
                ).toLocaleString("en-US", {
                  timeZoneName: "short",
                })}
              </p>
              {conflictingPosts.length > 0 && (
                <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded-lg text-start">
                  <div className="flex gap-2 text-yellow-800 items-center">
                    <Info className="w-3 h-3" />
                    <span className="text-xs font-medium">
                      {conflictingPosts.length} post
                      {conflictingPosts.length !== 1 ? "s" : ""} already
                      scheduled at this time
                    </span>
                  </div>
                  <p className="text-xs text-yellow-700 mt-1">
                    You can still reschedule this post, but it will be published
                    at the same time.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Main Content Area */}
          <div className="flex-1 min-h-0 overflow-hidden">
            {isMobile ? (
              // Mobile Layout: Vertical stack with calendar first, then scheduled posts
              <div className="space-y-3 h-full overflow-y-auto">
                {/* Date & Time Selection */}
                <Card>
                  <CardContent className="p-3">
                    <h3 className="font-medium mb-3 flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      Select New Date & Time
                    </h3>
                    <div className="space-y-3">
                      <div className="flex justify-center">
                        <Calendar
                          mode="single"
                          selected={selectedDate}
                          onSelect={(date) => date && setSelectedDate(date)}
                          disabled={(date) => date < new Date()}
                          modifiers={{
                            hasScheduledPost: datesWithScheduledPosts,
                          }}
                          modifiersClassNames={{
                            hasScheduledPost:
                              'relative after:absolute after:top-1 after:right-1 after:w-2 after:h-2 after:bg-green-500 after:rounded-full after:content-[""]',
                          }}
                          className="rounded-md border"
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="text-xs font-medium mb-1 block">
                            Hour
                          </label>
                          <Select
                            value={selectedHour}
                            onValueChange={setSelectedHour}
                          >
                            <SelectTrigger className="h-9">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {hours.map((hour) => (
                                <SelectItem key={hour} value={hour}>
                                  {hour}:00
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <label className="text-xs font-medium mb-1 block">
                            Minute
                          </label>
                          <Select
                            value={selectedMinute}
                            onValueChange={setSelectedMinute}
                          >
                            <SelectTrigger className="h-9">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {minutes.map((minute) => (
                                <SelectItem key={minute} value={minute}>
                                  :{minute}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Scheduled Posts Preview */}
                <Card>
                  <CardContent className="p-3">
                    <h3 className="font-medium mb-3">Scheduled Posts</h3>
                    <div className="max-h-80 overflow-y-auto">
                      <div className="space-y-2">
                        {scheduledPosts.length > 0 ? (
                          scheduledPosts
                            .sort(
                              (a, b) =>
                                new Date(a.scheduled_at || 0).getTime() -
                                new Date(b.scheduled_at || 0).getTime()
                            )
                            .map((scheduledPost) => (
                              <div
                                key={scheduledPost.id}
                                className={`border rounded p-3 cursor-pointer hover:bg-gray-50 transition-colors ${
                                  scheduledPost.id === post.id
                                    ? "border-blue-300 bg-blue-50"
                                    : ""
                                }`}
                                onClick={() =>
                                  setSelectedScheduledPost(scheduledPost)
                                }
                              >
                                <div className="flex items-center justify-between mb-2">
                                  <span className="text-xs text-gray-500">
                                    {scheduledPost.scheduled_at &&
                                      new Date(
                                        scheduledPost.scheduled_at
                                      ).toLocaleString("en-US", {
                                        month: "short",
                                        day: "numeric",
                                        hour: "2-digit",
                                        minute: "2-digit",
                                      })}
                                  </span>
                                </div>
                                <p className="text-xs text-gray-800 line-clamp-2 leading-relaxed">
                                  {scheduledPost.content}
                                </p>
                              </div>
                            ))
                        ) : (
                          <div className="text-center py-4 text-gray-500">
                            <CalendarIcon className="w-6 h-6 mx-auto mb-1 opacity-50" />
                            <p className="text-xs">No posts scheduled yet</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            ) : (
              // Desktop Layout: Side-by-side layout
              <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 h-full">
                {/* Left Column: Time Selection */}
                <div className="lg:col-span-2 space-y-4 overflow-y-auto">
                  {/* Date & Time Selection */}
                  <Card>
                    <CardContent className="p-4">
                      <h3 className="font-medium mb-3 flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        Select New Date & Time
                      </h3>
                      <div className="space-y-4">
                        <div className="flex justify-center">
                          <Calendar
                            mode="single"
                            selected={selectedDate}
                            onSelect={(date) => date && setSelectedDate(date)}
                            disabled={(date) => date < new Date()}
                            modifiers={{
                              hasScheduledPost: datesWithScheduledPosts,
                            }}
                            modifiersClassNames={{
                              hasScheduledPost:
                                'relative after:absolute after:top-1 after:right-1 after:w-2 after:h-2 after:bg-green-500 after:rounded-full after:content-[""]',
                            }}
                            className="rounded-md border"
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <label className="text-sm font-medium mb-2 block">
                              Hour
                            </label>
                            <Select
                              value={selectedHour}
                              onValueChange={setSelectedHour}
                            >
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {hours.map((hour) => (
                                  <SelectItem key={hour} value={hour}>
                                    {hour}:00
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                          <div>
                            <label className="text-sm font-medium mb-2 block">
                              Minute
                            </label>
                            <Select
                              value={selectedMinute}
                              onValueChange={setSelectedMinute}
                            >
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {minutes.map((minute) => (
                                  <SelectItem key={minute} value={minute}>
                                    :{minute}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Right Column: Scheduled Posts Preview */}
                <div className="lg:col-span-3 flex flex-col min-h-0">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-medium">Scheduled Posts</h3>
                  </div>

                  <ScrollArea className="flex-1">
                    <div className="space-y-3">
                      {scheduledPosts.length > 0 ? (
                        scheduledPosts
                          .sort(
                            (a, b) =>
                              new Date(a.scheduled_at || 0).getTime() -
                              new Date(b.scheduled_at || 0).getTime()
                          )
                          .map((scheduledPost) => (
                            <Card
                              key={scheduledPost.id}
                              className={`cursor-pointer hover:bg-gray-50 transition-colors ${
                                scheduledPost.id === post.id
                                  ? "border-blue-300 bg-blue-50"
                                  : ""
                              }`}
                              onClick={() =>
                                setSelectedScheduledPost(scheduledPost)
                              }
                            >
                              <CardContent className="p-3">
                                <div className="flex items-center justify-between mb-2">
                                  <span className="text-xs text-gray-500">
                                    {scheduledPost.scheduled_at &&
                                      new Date(
                                        scheduledPost.scheduled_at
                                      ).toLocaleString("en-US", {
                                        month: "short",
                                        day: "numeric",
                                        hour: "2-digit",
                                        minute: "2-digit",
                                      })}
                                  </span>
                                </div>
                                <p className="text-sm text-gray-800 line-clamp-2">
                                  {scheduledPost.content}
                                </p>
                              </CardContent>
                            </Card>
                          ))
                      ) : (
                        <div className="text-center py-8 text-gray-500">
                          <CalendarIcon className="w-8 h-8 mx-auto mb-2 opacity-50" />
                          <p className="text-sm">No posts scheduled yet</p>
                        </div>
                      )}
                    </div>
                  </ScrollArea>
                </div>
              </div>
            )}
          </div>

          {/* Always Visible Footer */}
          <DialogFooter className="flex-shrink-0 border-t pt-3 mt-3">
            <Button variant="outline" onClick={onClose} className="px-4">
              Cancel
            </Button>
            <Button
              onClick={handleReschedule}
              disabled={isRescheduling}
              className="px-4"
            >
              {isRescheduling ? (
                <>
                  <Clock className="w-4 h-4 mr-2 animate-spin" />
                  Rescheduling...
                </>
              ) : (
                <>
                  <CalendarIcon className="w-4 h-4 mr-2" />
                  {isMobile ? "Reschedule" : "Confirm & Reschedule Post"}
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>

        {/* Conflict Confirmation Dialog */}
        <Dialog open={showConflictDialog} onOpenChange={setShowConflictDialog}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Info className="w-5 h-5 text-yellow-600" />
                Rescheduling Conflict
              </DialogTitle>
            </DialogHeader>

            <div className="space-y-4">
              <p className="text-sm text-gray-600">
                You have {conflictingPosts.length} post
                {conflictingPosts.length !== 1 ? "s" : ""} already scheduled at
                the same time:
              </p>

              <div className="space-y-2 max-h-40 overflow-y-auto">
                {conflictingPosts.map((conflictPost) => (
                  <div
                    key={conflictPost.id}
                    className="bg-gray-50 p-3 rounded-lg"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-gray-500">
                        {conflictPost.scheduled_at &&
                          formatTime(conflictPost.scheduled_at)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-800 line-clamp-2">
                      {conflictPost.content}
                    </p>
                  </div>
                ))}
              </div>

              <p className="text-sm text-gray-600">
                Are you sure you want to reschedule this post at the same time?
              </p>
            </div>

            <DialogFooter className="gap-2">
              <Button
                variant="outline"
                onClick={() => setShowConflictDialog(false)}
              >
                Cancel
              </Button>
              <Button
                onClick={handleConfirmReschedule}
                disabled={isRescheduling}
              >
                {isRescheduling ? (
                  <>
                    <Clock className="w-4 h-4 mr-2 animate-spin" />
                    Rescheduling...
                  </>
                ) : (
                  <>
                    <CalendarIcon className="w-4 h-4 mr-2" />
                    Reschedule Anyway
                  </>
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </Dialog>

      {/* Scheduled Post Details Modal */}
      <ScheduledPostDetails
        isOpen={!!selectedScheduledPost}
        onClose={() => setSelectedScheduledPost(null)}
        post={selectedScheduledPost}
      />
    </>
  );
};

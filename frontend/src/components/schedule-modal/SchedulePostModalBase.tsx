import React, { useState, useEffect, useCallback, useMemo } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent } from "@/components/ui/card";
import { Calendar as CalendarIcon, Clock, Info, RefreshCw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Post } from "@/types/posts";
import { postsApi } from "@/lib/posts-api";
import { useIsMobile } from "@/hooks/use-mobile";
import { ScheduledPostDetails } from "@/components/schedule-modal/ScheduledPostDetails";
import { useProfile } from "@/contexts/ProfileContext";
import { toDate, format, toZonedTime } from "date-fns-tz";
import {
  addDays,
  endOfMonth,
  startOfMonth,
  subDays,
  isSameDay,
} from "date-fns";
import { toast } from "@/hooks/use-toast";

interface SchedulePostModalBaseProps {
  mode: "schedule" | "reschedule";
  isOpen: boolean;
  onClose: () => void;
  post: Post | null;
  onSubmit: (postId: string, scheduledAt: string) => void;
  isSubmitting?: boolean;
}

export const SchedulePostModalBase: React.FC<SchedulePostModalBaseProps> = ({
  mode,
  isOpen,
  onClose,
  post,
  onSubmit,
  isSubmitting = false,
}) => {
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [selectedHour, setSelectedHour] = useState<string>("09");
  const [selectedMinute, setSelectedMinute] = useState<string>("00");
  const [scheduledPosts, setScheduledPosts] = useState<Post[]>([]);
  const [isLoadingScheduledPosts, setIsLoadingScheduledPosts] = useState(false);
  const [conflictingPosts, setConflictingPosts] = useState<Post[]>([]);
  const [showConflictDialog, setShowConflictDialog] = useState(false);
  // Local loading flag to give immediate feedback and prevent duplicate clicks
  const [localSubmitting, setLocalSubmitting] = useState(false);
  const [selectedScheduledPost, setSelectedScheduledPost] =
    useState<Post | null>(null);
  const [showPushDialog, setShowPushDialog] = useState(false);
  const [postsOnSelectedDay, setPostsOnSelectedDay] = useState<Post[]>([]);
  const [isPushing, setIsPushing] = useState(false);
  const { userPreferences: contextPrefs } = useProfile();

  const userPreferences = useMemo(() => {
    return {
      preferred_posting_time: "09:00",
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      ...contextPrefs,
    } as typeof contextPrefs & {
      preferred_posting_time?: string;
      timezone?: string;
    };
  }, [contextPrefs]);

  const [selectedTimezone, setSelectedTimezone] = useState<string>("");
  const [timezones, setTimezones] = useState<string[]>([]);

  const isMobile = useIsMobile();

  const submitting = isSubmitting || localSubmitting; // combined flag

  // Track whether we've already initialized defaults for the currently open modal
  const initializedRef = React.useRef(false);
  const isScheduleMode = mode === "schedule";

  const modalTitle = isScheduleMode ? "Schedule Post" : "Reschedule Post";
  const headerText = isScheduleMode
    ? "📅 Post will be published on"
    : "📅 Post will be rescheduled to";
  const submitButtonText = isMobile
    ? isScheduleMode
      ? "Schedule"
      : "Reschedule"
    : isScheduleMode
    ? "Confirm & Schedule Post"
    : "Confirm & Reschedule Post";
  const submittingText = isScheduleMode ? "Scheduling..." : "Rescheduling...";
  const conflictTitle = "Scheduling Conflict";
  const conflictSubmitText = "Schedule Anyway";

  const fetchScheduledPosts = useCallback(async (month: Date) => {
    setIsLoadingScheduledPosts(true);
    try {
      const startDate = subDays(startOfMonth(month), 10);
      const endDate = addDays(endOfMonth(month), 10);

      const response = await postsApi.getPosts({
        status: ["scheduled"],
        after_date: format(startDate, "yyyy-MM-dd"),
        before_date: format(endDate, "yyyy-MM-dd"),
        size: 100,
      });
      setScheduledPosts(response.items);
    } catch (error) {
      console.error("Failed to fetch scheduled posts", error);
    } finally {
      setIsLoadingScheduledPosts(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      const initialDateForMonthView = post?.scheduled_at
        ? new Date(post.scheduled_at)
        : new Date();
      fetchScheduledPosts(initialDateForMonthView);
    }
  }, [isOpen, post, fetchScheduledPosts]);

  const handleMonthChange = (month: Date) => {
    fetchScheduledPosts(month);
  };

  useEffect(() => {
    setTimezones(Intl.supportedValuesOf("timeZone"));
  }, []);

  useEffect(() => {
    if (!isOpen) {
      initializedRef.current = false; // reset for next open
      return;
    }

    if (!initializedRef.current) {
      const targetTimezone =
        userPreferences.timezone ||
        Intl.DateTimeFormat().resolvedOptions().timeZone;
      setSelectedTimezone(targetTimezone);

      if (isScheduleMode) {
        const today = new Date();
        setSelectedDate(today);

        const defaultTime = userPreferences.preferred_posting_time;
        if (defaultTime) {
          const [hour, minute] = defaultTime.split(":");
          setSelectedHour(hour || "09");
          setSelectedMinute(minute || "00");
        } else {
          setSelectedHour("09");
          setSelectedMinute("00");
        }
      } else {
        if (post.scheduled_at) {
          const zonedDate = toZonedTime(post.scheduled_at, targetTimezone);
          setSelectedDate(zonedDate);
          setSelectedHour(format(zonedDate, "HH"));
          setSelectedMinute(format(zonedDate, "mm"));
        } else {
          const today = new Date();
          setSelectedDate(today);
          setSelectedHour("09");
          setSelectedMinute("00");
        }
      }

      setConflictingPosts([]);
      setShowConflictDialog(false);
      setSelectedScheduledPost(null);

      initializedRef.current = true;
    }
  }, [isOpen, post, userPreferences, isScheduleMode]);

  // Reset local loading flag
  // 1. When modal closes, always reset
  useEffect(() => {
    if (!isOpen) {
      setLocalSubmitting(false);
    }
  }, [isOpen]);

  // 2. When parent call finishes (isSubmitting becomes false), clear local flag
  useEffect(() => {
    if (!isSubmitting) {
      setLocalSubmitting(false);
    }
  }, [isSubmitting]);

  const formatDateTime = (date: Date, hour: string, minute: string) => {
    const timezone =
      selectedTimezone ||
      userPreferences.timezone ||
      Intl.DateTimeFormat().resolvedOptions().timeZone;
    const dateString = `${format(date, "yyyy-MM-dd")}T${hour}:${minute}:00`;
    const utcDate = toDate(dateString, { timeZone: timezone });
    return utcDate.toISOString();
  };

  const formatTime = (dateString: string) => {
    const timezone =
      selectedTimezone ||
      userPreferences.timezone ||
      Intl.DateTimeFormat().resolvedOptions().timeZone;
    const zonedDate = toZonedTime(dateString, timezone);
    return format(zonedDate, "h:mm a");
  };

  const getCurrentTimeInTimezone = () => {
    const timezone =
      selectedTimezone ||
      userPreferences.timezone ||
      Intl.DateTimeFormat().resolvedOptions().timeZone;
    return toZonedTime(new Date(), timezone);
  };

  const isValidTimeForToday = (hour: string, minute: string) => {
    const now = getCurrentTimeInTimezone();
    const selectedTime = new Date(now);
    selectedTime.setHours(parseInt(hour), parseInt(minute), 0, 0);

    return selectedTime.getTime() > now.getTime() + 1 * 60 * 1000;
  };

  const isDateDisabled = (date: Date) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const checkDate = new Date(date);
    checkDate.setHours(0, 0, 0, 0);
    const isDisabled = checkDate < today;

    return isDisabled;
  };

  const allMinutes = Array.from({ length: 60 }, (_, i) =>
    i.toString().padStart(2, "0")
  ).filter((_, i) => i % 5 === 0);

  const getAvailableHours = () => {
    const allHours = Array.from({ length: 24 }, (_, i) =>
      i.toString().padStart(2, "0")
    );

    const isToday = isSameDay(selectedDate, getCurrentTimeInTimezone());

    if (!isToday) {
      return allHours;
    }

    const now = getCurrentTimeInTimezone();
    const currentHour = now.getHours();
    const currentMinute = now.getMinutes();

    const availableHours = allHours.filter((hour) => {
      const hourNum = parseInt(hour);
      if (hourNum > currentHour) return true;
      if (hourNum === currentHour) {
        // Check if any minute in this hour would be valid
        const hasValidMinutes = allMinutes.some((minute) => {
          const minuteNum = parseInt(minute);
          return minuteNum > currentMinute + 1; // At least 1 minute buffer
        });
        return hasValidMinutes;
      }
      return false;
    });

    return availableHours;
  };

  const getAvailableMinutes = () => {
    const isToday = isSameDay(selectedDate, getCurrentTimeInTimezone());

    if (!isToday) {
      return allMinutes;
    }

    const now = getCurrentTimeInTimezone();
    const currentHour = now.getHours();
    const currentMinute = now.getMinutes();
    const selectedHourNum = parseInt(selectedHour);

    if (selectedHourNum > currentHour) {
      return allMinutes;
    }

    if (selectedHourNum === currentHour) {
      const availableMinutes = allMinutes.filter((minute) => {
        const minuteNum = parseInt(minute);
        return minuteNum > currentMinute + 1; // At least 1 minute buffer
      });
      return availableMinutes;
    }

    return [];
  };

  const handlePushPosts = async (targetDate: Date) => {
    const targetDateOnly = new Date(targetDate);
    targetDateOnly.setHours(0, 0, 0, 0);

    const subsequentPosts = scheduledPosts
      .filter((p) => {
        if (!p.scheduled_at) return false;
        const postDate = new Date(p.scheduled_at);
        postDate.setHours(0, 0, 0, 0);
        return postDate.getTime() >= targetDateOnly.getTime();
      })
      .sort(
        (a, b) =>
          new Date(a.scheduled_at!).getTime() -
          new Date(b.scheduled_at!).getTime()
      );

    if (subsequentPosts.length === 0) {
      return;
    }

    const postsToShift = [];
    let lastPushedDate = new Date(subsequentPosts[0].scheduled_at!);
    lastPushedDate.setHours(0, 0, 0, 0);

    postsToShift.push(subsequentPosts[0]);

    for (let i = 1; i < subsequentPosts.length; i++) {
      const currentPostDate = new Date(subsequentPosts[i].scheduled_at!);
      currentPostDate.setHours(0, 0, 0, 0);

      const expectedNextDate = new Date(lastPushedDate);
      expectedNextDate.setDate(expectedNextDate.getDate() + 1);

      if (currentPostDate.getTime() === expectedNextDate.getTime()) {
        postsToShift.push(subsequentPosts[i]);
        lastPushedDate = currentPostDate;
      } else {
        break;
      }
    }

    const updatedPosts = postsToShift.map((post) => {
      const newDate = new Date(post.scheduled_at!);
      newDate.setDate(newDate.getDate() + 1);
      return {
        ...post,
        id: post.id,
        scheduled_at: newDate.toISOString(),
      };
    });

    try {
      await postsApi.batchUpdatePosts({ posts: updatedPosts });

      await fetchScheduledPosts(selectedDate);

      toast({
        title: "Posts Pushed",
        description: `${postsToShift.length} post${
          postsToShift.length !== 1 ? "s" : ""
        } pushed to the next available day.`,
      });
    } catch (error) {
      console.error("Failed to push posts:", error);
      toast({
        title: "Error",
        description: "Failed to push posts. Please try again.",
        variant: "destructive",
      });
    }
  };

  const checkForConflicts = (date: Date, hour: string, minute: string) => {
    // Check for same-day conflicts (any posts on the selected day)
    const conflicts = scheduledPosts.filter((p) => {
      if (!p.scheduled_at || p.id === post?.id) return false;
      const postDate = new Date(p.scheduled_at);
      return isSameDay(postDate, date);
    });

    // Set both conflicting posts and posts on selected day to the same value
    // since we're treating same-day as conflict now
    setConflictingPosts(conflicts);
    setPostsOnSelectedDay(conflicts);
  };

  useEffect(() => {
    if (post) {
      checkForConflicts(selectedDate, selectedHour, selectedMinute);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDate, selectedHour, selectedMinute, scheduledPosts, post]);

  const handleSubmit = () => {
    if (submitting) return; // guard against double click
    if (!post) return;

    if (
      isSameDay(selectedDate, getCurrentTimeInTimezone()) &&
      !isValidTimeForToday(selectedHour, selectedMinute)
    ) {
      toast({
        title: "Invalid Time",
        description:
          "Please select a time that is at least 1 minute in the future.",
        variant: "destructive",
      });
      return;
    }

    // Check for same-day conflicts (now the primary conflict type)
    if (conflictingPosts.length > 0) {
      setShowPushDialog(true);
      return;
    }

    const scheduledAt = formatDateTime(
      selectedDate,
      selectedHour,
      selectedMinute
    );
    setLocalSubmitting(true);
    onSubmit(post.id, scheduledAt);
  };

  const handleConfirmSubmit = () => {
    if (submitting) return; // guard against double click
    if (!post) return;
    const scheduledAt = formatDateTime(
      selectedDate,
      selectedHour,
      selectedMinute
    );
    setLocalSubmitting(true);
    onSubmit(post.id, scheduledAt);
    setShowConflictDialog(false);
  };

  const getDatesWithScheduledPosts = () => {
    const datesWithPosts = new Set<string>();
    scheduledPosts.forEach((p) => {
      if (p.scheduled_at) {
        const date = new Date(p.scheduled_at);
        datesWithPosts.add(date.toDateString());
      }
    });
    return Array.from(datesWithPosts).map((dateString) => new Date(dateString));
  };

  const hours = getAvailableHours();
  const minutes = getAvailableMinutes();

  const handleScheduleAnyway = (post: Post) => {
    const scheduledAt = formatDateTime(
      selectedDate,
      selectedHour,
      selectedMinute
    );
    setLocalSubmitting(true);
    onSubmit(post!.id, scheduledAt);
    setShowPushDialog(false);
  };

  const handlePushAndSchedule = async (post: Post) => {
    {
      try {
        setIsPushing(true);
        await handlePushPosts(selectedDate);
        const scheduledAt = formatDateTime(
          selectedDate,
          selectedHour,
          selectedMinute
        );
        setLocalSubmitting(true);
        onSubmit(post!.id, scheduledAt);
        setShowPushDialog(false);
      } catch (error) {
        console.error("Failed to push posts:", error);
        toast({
          title: "Error",
          description: "Failed to push posts. Please try again.",
          variant: "destructive",
        });
      } finally {
        setIsPushing(false);
      }
    }
  };

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
          <DialogHeader className="flex-shrink-0 border-b border-border pb-4">
            <DialogTitle className="flex items-center gap-2 text-foreground bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              <CalendarIcon className="w-5 h-5 text-primary" />
              {modalTitle}
            </DialogTitle>
          </DialogHeader>

          <div className="flex-shrink-0 bg-gradient-to-r from-accent/10 to-secondary/10 border border-accent/20 rounded-lg p-3 mb-3">
            <div className="text-center">
              <p className="text-xs text-muted-foreground mb-1">{headerText}</p>
              <p
                className={`font-bold text-gray-900 ${
                  isMobile ? "text-lg" : "text-xl"
                }`}
              >
                {selectedTimezone &&
                  new Date(
                    formatDateTime(selectedDate, selectedHour, selectedMinute)
                  ).toLocaleString("en-US", {
                    timeZone: selectedTimezone,
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
                      scheduled on this day
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="flex-1 min-h-0 overflow-hidden">
            {isMobile ? (
              <div className="space-y-3 h-full overflow-y-auto">
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
                          disabled={isDateDisabled}
                          modifiers={{
                            hasScheduledPost: datesWithScheduledPosts,
                          }}
                          modifiersClassNames={{
                            hasScheduledPost:
                              'relative after:absolute after:top-1 after:right-1 after:w-2 after:h-2 after:bg-green-500 after:rounded-full after:content-[""]',
                          }}
                          className="rounded-md border"
                          onMonthChange={handleMonthChange}
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
                              {minutes.length === 0 && (
                                <SelectItem value="" disabled>
                                  No valid times available
                                </SelectItem>
                              )}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="col-span-2">
                          <label className="text-xs font-medium mb-1 block">
                            Timezone
                          </label>
                          <Select
                            value={selectedTimezone}
                            onValueChange={setSelectedTimezone}
                          >
                            <SelectTrigger className="h-9">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {timezones.map((tz) => (
                                <SelectItem key={tz} value={tz}>
                                  {tz}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-3">
                    <h3 className="font-medium mb-3">Scheduled Posts</h3>
                    <div className="max-h-80 overflow-y-auto">
                      {isLoadingScheduledPosts ? (
                        <div className="text-center py-4 text-gray-500">
                          <RefreshCw className="w-6 h-6 mx-auto mb-1 opacity-50 animate-spin" />
                          <p className="text-xs">Loading scheduled posts...</p>
                        </div>
                      ) : (
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
                                        formatTime(scheduledPost.scheduled_at)}
                                    </span>
                                  </div>
                                  <p className="text-xs text-gray-800 line-clamp-2">
                                    {scheduledPost.content}
                                  </p>
                                  {scheduledPost.topics.length > 0 && (
                                    <div className="space-y-2 pt-2">
                                      <div className="flex flex-wrap gap-1 sm:gap-2">
                                        {scheduledPost.topics.map(
                                          (topic, idx) => (
                                            <Badge
                                              key={idx}
                                              variant="outline"
                                              className="text-xs"
                                            >
                                              {topic}
                                            </Badge>
                                          )
                                        )}
                                      </div>
                                    </div>
                                  )}
                                </div>
                              ))
                          ) : (
                            <div className="text-center py-4 text-gray-500">
                              <CalendarIcon className="w-6 h-6 mx-auto mb-1 opacity-50" />
                              <p className="text-xs">No posts scheduled yet</p>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 h-full">
                <div className="lg:col-span-2 space-y-4 overflow-y-auto">
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
                            disabled={isDateDisabled}
                            modifiers={{
                              hasScheduledPost: datesWithScheduledPosts,
                            }}
                            modifiersClassNames={{
                              hasScheduledPost:
                                'relative after:absolute after:top-1 after:right-1 after:w-2 after:h-2 after:bg-green-500 after:rounded-full after:content-[""]',
                            }}
                            className="rounded-md border"
                            onMonthChange={handleMonthChange}
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
                                {allMinutes.map((minute) => (
                                  <SelectItem key={minute} value={minute}>
                                    :{minute}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="col-span-2">
                            <label className="text-sm font-medium mb-2 block">
                              Timezone
                            </label>
                            <Select
                              value={selectedTimezone}
                              onValueChange={setSelectedTimezone}
                            >
                              <SelectTrigger className="w-full">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {timezones.map((tz) => (
                                  <SelectItem key={tz} value={tz}>
                                    {tz}
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

                <div className="lg:col-span-3 flex flex-col min-h-0">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-medium">Scheduled Posts</h3>
                  </div>

                  <ScrollArea className="flex-1">
                    {isLoadingScheduledPosts ? (
                      <div className="text-center py-8 text-gray-500">
                        <RefreshCw className="w-8 h-8 mx-auto mb-2 opacity-50 animate-spin" />
                        <p className="text-sm">Loading scheduled posts...</p>
                      </div>
                    ) : (
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
                                  {scheduledPost.topics.length > 0 && (
                                    <div className="space-y-2 pt-2">
                                      <div className="flex flex-wrap gap-1 sm:gap-2">
                                        {scheduledPost.topics.map(
                                          (topic, idx) => (
                                            <Badge
                                              key={idx}
                                              variant="outline"
                                              className="text-xs"
                                            >
                                              {topic}
                                            </Badge>
                                          )
                                        )}
                                      </div>
                                    </div>
                                  )}
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
                    )}
                  </ScrollArea>
                </div>
              </div>
            )}
          </div>

          <DialogFooter className="flex-shrink-0 border-t border-border pt-3 mt-3">
            <Button variant="outline" onClick={onClose} className="px-4">
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={submitting}
              className="px-4 bg-primary hover:bg-primary/90"
            >
              {submitting ? (
                <>
                  <Clock className="w-4 h-4 mr-2 animate-spin" />
                  {submittingText}
                </>
              ) : (
                <>
                  <CalendarIcon className="w-4 h-4 mr-2" />
                  {submitButtonText}
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>

        <Dialog open={showConflictDialog} onOpenChange={setShowConflictDialog}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Info className="w-5 h-5 text-yellow-600" />
                {conflictTitle}
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
                Are you sure you want to schedule this post at the same time?
              </p>
            </div>

            <DialogFooter className="gap-2">
              <Button
                variant="outline"
                onClick={() => setShowConflictDialog(false)}
              >
                Cancel
              </Button>
              <Button onClick={handleConfirmSubmit} disabled={submitting}>
                {submitting ? (
                  <>
                    <Clock className="w-4 h-4 mr-2 animate-spin" />
                    {submittingText}
                  </>
                ) : (
                  <>
                    <CalendarIcon className="w-4 h-4 mr-2" />
                    {conflictSubmitText}
                  </>
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog open={showPushDialog} onOpenChange={setShowPushDialog}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <RefreshCw className="w-5 h-5 text-blue-600" />
                Posts Already Scheduled
              </DialogTitle>
            </DialogHeader>

            <div className="space-y-4">
              <p className="text-sm text-gray-600">
                You have {postsOnSelectedDay.length} post
                {postsOnSelectedDay.length !== 1 ? "s" : ""} already scheduled
                on {format(selectedDate, "MMMM d, yyyy")}:
              </p>

              <div className="space-y-2 max-h-40 overflow-y-auto">
                {postsOnSelectedDay.map((dayPost) => (
                  <div key={dayPost.id} className="bg-gray-50 p-3 rounded-lg">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-gray-500">
                        {dayPost.scheduled_at &&
                          formatTime(dayPost.scheduled_at)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-800 line-clamp-2">
                      {dayPost.content}
                    </p>
                  </div>
                ))}
              </div>

              <p className="text-sm text-gray-600">
                Would you like to push the existing posts to the next available
                day and schedule this post on {format(selectedDate, "MMMM d")}?
              </p>
            </div>

            <DialogFooter className="gap-2">
              <Button
                variant="outline"
                onClick={() => setShowPushDialog(false)}
              >
                Cancel
              </Button>
              <Button
                onClick={() => {
                  const scheduledAt = formatDateTime(
                    selectedDate,
                    selectedHour,
                    selectedMinute
                  );
                  setLocalSubmitting(true);
                  onSubmit(post!.id, scheduledAt);
                  setShowPushDialog(false);
                }}
                disabled={submitting}
                variant="outline"
              >
                {submitting ? (
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
                onClick={async () => {
                  try {
                    setIsPushing(true);
                    await handlePushPosts(selectedDate);
                    const scheduledAt = formatDateTime(
                      selectedDate,
                      selectedHour,
                      selectedMinute
                    );
                    setLocalSubmitting(true);
                    onSubmit(post!.id, scheduledAt);
                    setShowPushDialog(false);
                  } catch (error) {
                    console.error("Failed to push posts:", error);
                    toast({
                      title: "Error",
                      description: "Failed to push posts. Please try again.",
                      variant: "destructive",
                    });
                  } finally {
                    setIsPushing(false);
                  }
                }}
                disabled={submitting || isPushing}
              >
                {isPushing ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Pushing Posts...
                  </>
                ) : submitting ? (
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
      </Dialog>

      <ScheduledPostDetails
        isOpen={!!selectedScheduledPost}
        onClose={() => setSelectedScheduledPost(null)}
        post={selectedScheduledPost}
      />
    </>
  );
};

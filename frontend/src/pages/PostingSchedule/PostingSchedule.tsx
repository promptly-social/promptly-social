import React, { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  DragOverEvent,
  PointerSensor,
  useSensor,
  useSensors,
  closestCenter,
} from "@dnd-kit/core";
import AppLayout from "@/components/AppLayout";
import { RescheduleModal } from "@/components/RescheduleModal";
import { ScheduledPostDetails } from "@/components/ScheduledPostDetails";
import { DraggablePostCard } from "@/components/DraggablePostCard";
import { DroppableCalendarDay } from "@/components/DroppableCalendarDay";
import { DroppableMonthDay } from "@/components/DroppableMonthDay";
import { toast } from "@/hooks/use-toast";
import { postsApi, Post } from "@/lib/posts-api";
import { useIsMobile } from "@/hooks/use-mobile";
import {
  Calendar,
  Clock,
  Grid,
  List,
  Edit3,
  Bookmark,
  Trash2,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Loader2,
  Share2,
  Globe,
  User,
  ArrowDown,
  Shuffle,
} from "lucide-react";

const PostingSchedule: React.FC = () => {
  const [scheduledPosts, setScheduledPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<"list" | "month">("list");
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedPost, setSelectedPost] = useState<Post | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isRescheduling, setIsRescheduling] = useState(false);

  // Reschedule modal state
  const [isRescheduleModalOpen, setIsRescheduleModalOpen] = useState(false);
  const [postToReschedule, setPostToReschedule] = useState<Post | null>(null);

  // Drag and drop state
  const [activePost, setActivePost] = useState<Post | null>(null);
  const [activePostStyle, setActivePostStyle] = useState<React.CSSProperties>(
    {}
  );

  // List view drag and drop state
  const [isDropActionModalOpen, setIsDropActionModalOpen] = useState(false);
  const [dropActionData, setDropActionData] = useState<{
    draggedPost: Post;
    targetPost: Post;
    action: "swap" | "push" | "cancel";
  } | null>(null);

  const isMobile = useIsMobile();

  // Check if drag and drop should be enabled
  const isDragDropEnabled = () => {
    if (viewMode === "list") return true;
    if (viewMode === "month") return true; // Enable for all devices including mobile
    return false;
  };

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 3,
      },
    })
  );

  // Helper function to sort posts by scheduled_at in ascending order
  const sortPostsByScheduledAt = (posts: Post[]) => {
    return [...posts].sort((a, b) => {
      if (!a.scheduled_at && !b.scheduled_at) return 0;
      if (!a.scheduled_at) return 1;
      if (!b.scheduled_at) return -1;
      return (
        new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime()
      );
    });
  };

  useEffect(() => {
    fetchScheduledPosts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchScheduledPosts = async () => {
    try {
      setLoading(true);
      const response = await postsApi.getPosts({
        status: ["scheduled"],
        order_by: "scheduled_at",
        order_direction: "asc",
        size: 100,
      });
      setScheduledPosts(sortPostsByScheduledAt(response.items));
    } catch (error) {
      console.error("Error fetching scheduled posts:", error);
      toast({
        title: "Error",
        description: "Failed to load scheduled posts. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleReschedulePost = async (
    postId: string,
    newScheduledAt: string
  ) => {
    try {
      setIsRescheduling(true);
      const updatedPost = await postsApi.updatePost(postId, {
        scheduled_at: newScheduledAt,
      });

      // Update the posts list
      setScheduledPosts((prev) =>
        sortPostsByScheduledAt(
          prev.map((post) => (post.id === postId ? updatedPost : post))
        )
      );

      // Close modals
      setIsRescheduleModalOpen(false);
      setPostToReschedule(null);
      if (selectedPost?.id === postId) {
        setSelectedPost(null);
        setIsExpanded(false);
      }

      toast({
        title: "Post Rescheduled",
        description: "Post has been successfully rescheduled.",
      });
    } catch (error) {
      console.error("Error rescheduling post:", error);
      toast({
        title: "Error",
        description: "Failed to reschedule post. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsRescheduling(false);
    }
  };

  const openRescheduleModal = (post: Post) => {
    setPostToReschedule(post);
    setIsRescheduleModalOpen(true);
  };

  const handleSaveForLater = async (post: Post) => {
    try {
      setIsRescheduling(true);
      const updatedPost = await postsApi.updatePost(post.id, {
        status: "saved",
        scheduled_at: undefined,
      });

      setScheduledPosts(
        sortPostsByScheduledAt(scheduledPosts.filter((p) => p.id !== post.id))
      );
      if (selectedPost?.id === post.id) {
        setSelectedPost(null);
        setIsExpanded(false);
      }

      toast({
        title: "Saved for Later",
        description: "Post has been removed from schedule and saved for later.",
      });
    } catch (error) {
      console.error("Error saving post for later:", error);
      toast({
        title: "Error",
        description: "Failed to save post for later. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsRescheduling(false);
    }
  };

  const handleDeletePost = async (post: Post) => {
    if (
      !window.confirm(
        "Are you sure you want to delete this post? This action cannot be undone."
      )
    ) {
      return;
    }

    try {
      await postsApi.deletePost(post.id);
      setScheduledPosts(
        sortPostsByScheduledAt(scheduledPosts.filter((p) => p.id !== post.id))
      );
      if (selectedPost?.id === post.id) {
        setSelectedPost(null);
        setIsExpanded(false);
      }

      toast({
        title: "Post Deleted",
        description: "The post has been permanently deleted.",
      });
    } catch (error) {
      console.error("Error deleting post:", error);
      toast({
        title: "Error",
        description: "Failed to delete post. Please try again.",
        variant: "destructive",
      });
    }
  };

  const getPostsForPeriod = (periodType: "month", baseDate: Date) => {
    // month
    const monthStart = new Date(baseDate.getFullYear(), baseDate.getMonth(), 1);
    monthStart.setHours(0, 0, 0, 0); // Set to start of day
    const monthEnd = new Date(
      baseDate.getFullYear(),
      baseDate.getMonth() + 1,
      0,
      23,
      59,
      59,
      999
    );

    const filteredPosts = scheduledPosts.filter((post) => {
      if (!post.scheduled_at) return false;
      const postDate = new Date(post.scheduled_at);
      return postDate >= monthStart && postDate <= monthEnd;
    });

    return filteredPosts;
  };

  // Drag and drop handlers
  const handleDragStart = (event: DragStartEvent) => {
    if (!isDragDropEnabled()) return;

    const { active } = event;

    // Get the correct posts array based on view mode
    let postsToSearch = scheduledPosts;
    if (viewMode === "month") {
      postsToSearch = getPostsForPeriod("month", currentDate);
    }

    const post = postsToSearch.find((p) => p.id === active.id);
    if (post) {
      setActivePost(post);

      // Only capture dimensions if we're in list view (where dimensions match)
      // For calendar views, let the drag overlay use its natural size
      if (viewMode === "list" && active.rect.current.initial) {
        setActivePostStyle({
          width: active.rect.current.initial.width,
          height: active.rect.current.initial.height,
        });
      } else {
        // Clear any previous dimensions for calendar views
        setActivePostStyle({});
      }
    }
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    if (!isDragDropEnabled()) return;

    const { active, over } = event;
    setActivePost(null);
    setActivePostStyle({});

    if (!over) {
      return;
    }

    const postId = active.id as string;
    const overId = over.id as string;

    // Get the correct posts array based on view mode
    let postsToSearch = scheduledPosts;
    if (viewMode === "month") {
      postsToSearch = getPostsForPeriod("month", currentDate);
    }

    // Handle dropping on another post in list view
    if (viewMode === "list" && overId !== postId) {
      const draggedPost = postsToSearch.find((p) => p.id === postId);
      const targetPost = postsToSearch.find((p) => p.id === overId);

      if (draggedPost && targetPost) {
        setDropActionData({
          draggedPost,
          targetPost,
          action: "swap", // default action
        });
        setIsDropActionModalOpen(true);
        return;
      }
    }

    // Handle calendar drops (existing logic)
    const dayId = overId;
    const dateMatch = dayId.match(/^day-(\d{4}-\d{2}-\d{2})$/);
    if (!dateMatch) {
      return;
    }

    // Create date properly to avoid timezone issues
    const [year, month, day] = dateMatch[1].split("-").map(Number);
    const newDate = new Date(year, month - 1, day); // month is 0-indexed

    const post = postsToSearch.find((p) => p.id === postId);

    if (!post || !post.scheduled_at) {
      return;
    }

    // Check if the new date is in the past (compare only the date part, not time)
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const targetDate = new Date(newDate);
    targetDate.setHours(0, 0, 0, 0);

    if (targetDate < today) {
      toast({
        title: "Cannot Schedule in Past",
        description:
          "Posts cannot be scheduled for past dates. Please select a future date.",
        variant: "destructive",
      });
      return;
    }

    // Keep the same time, just change the date
    const currentTime = new Date(post.scheduled_at);
    newDate.setHours(
      currentTime.getHours(),
      currentTime.getMinutes(),
      currentTime.getSeconds(),
      currentTime.getMilliseconds()
    );

    console.log("Rescheduling post:", {
      postId,
      oldDate: post.scheduled_at,
      newDate: newDate.toISOString(),
      targetDay: dateMatch[1],
      createdDate: newDate.toDateString(),
    });

    // Reschedule the post
    await handleReschedulePost(postId, newDate.toISOString());

    toast({
      title: "Post Rescheduled",
      description: `Post scheduled for ${newDate.toLocaleDateString("en-US", {
        weekday: "short",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: true,
      })}`,
    });
  };

  const handleDragOver = (event: DragOverEvent) => {
    if (!isDragDropEnabled()) return;

    const { over } = event;

    if (over) {
      const dayId = over.id as string;
      const dateMatch = dayId.match(/^day-(\d{4}-\d{2}-\d{2})$/);

      if (dateMatch) {
        // Create date properly to avoid timezone issues
        const [year, month, day] = dateMatch[1].split("-").map(Number);
        const date = new Date(year, month - 1, day); // month is 0-indexed

        const today = new Date();
        today.setHours(0, 0, 0, 0);
        date.setHours(0, 0, 0, 0);
      }
    }
  };

  // Handle drop action modal actions
  const handleDropAction = async (action: "swap" | "push" | "cancel") => {
    if (!dropActionData) return;

    const { draggedPost, targetPost } = dropActionData;

    try {
      setIsRescheduling(true);

      switch (action) {
        case "push":
          // Push all posts from target date onwards by one day
          await handlePushPosts(targetPost);
          break;
        case "swap":
          // Swap the scheduled dates of the two posts
          if (draggedPost.scheduled_at && targetPost.scheduled_at) {
            await handleSwapPosts(draggedPost, targetPost);
          }
          break;
        case "cancel":
          // Do nothing, just close the modal
          break;
      }

      setIsDropActionModalOpen(false);
      setDropActionData(null);
    } catch (error) {
      console.error("Error handling drop action:", error);
      toast({
        title: "Error",
        description: "Failed to process the action. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsRescheduling(false);
    }
  };

  // Push all posts from target date onwards by one day
  const handlePushPosts = async (targetPost: Post) => {
    if (!targetPost.scheduled_at) return;

    const targetDate = new Date(targetPost.scheduled_at);
    const postsToPush = scheduledPosts.filter((post) => {
      if (!post.scheduled_at) return false;
      const postDate = new Date(post.scheduled_at);
      return postDate >= targetDate;
    });

    // Sort by scheduled_at to process in order
    const sortedPostsToPush = sortPostsByScheduledAt(postsToPush);

    // Push each post by one day
    for (const post of sortedPostsToPush) {
      if (post.scheduled_at) {
        const newDate = new Date(post.scheduled_at);
        newDate.setDate(newDate.getDate() + 1);
        await postsApi.updatePost(post.id, {
          scheduled_at: newDate.toISOString(),
        });
      }
    }

    // Refresh the posts list
    await fetchScheduledPosts();

    toast({
      title: "Posts Pushed",
      description: `All posts from ${targetDate.toLocaleDateString()} onwards have been pushed by one day.`,
    });
  };

  // Swap the scheduled dates of two posts
  const handleSwapPosts = async (post1: Post, post2: Post) => {
    if (!post1.scheduled_at || !post2.scheduled_at) return;

    const tempDate = post1.scheduled_at;

    // Update both posts
    await Promise.all([
      postsApi.updatePost(post1.id, { scheduled_at: post2.scheduled_at }),
      postsApi.updatePost(post2.id, { scheduled_at: tempDate }),
    ]);

    // Refresh the posts list
    await fetchScheduledPosts();

    toast({
      title: "Posts Swapped",
      description: "The scheduled dates of the two posts have been swapped.",
    });
  };

  const getSourceIcon = (platform: string) => {
    switch (platform) {
      case "linkedin":
        return <Share2 className="w-3 h-3" />;
      case "article":
        return <Globe className="w-3 h-3" />;
      default:
        return <User className="w-3 h-3" />;
    }
  };

  const getSourceLabel = (platform: string) => {
    switch (platform) {
      case "linkedin":
        return "LinkedIn";
      case "article":
        return "Article";
      default:
        return "General";
    }
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString("en-US", {
      weekday: "short",
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    });
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    });
  };

  const getPostsForDate = (date: Date) => {
    return scheduledPosts.filter((post) => {
      if (!post.scheduled_at) return false;
      const postDate = new Date(post.scheduled_at);
      return (
        postDate.getDate() === date.getDate() &&
        postDate.getMonth() === date.getMonth() &&
        postDate.getFullYear() === date.getFullYear()
      );
    });
  };

  const navigateMonth = (direction: "prev" | "next") => {
    const newDate = new Date(currentDate);
    newDate.setMonth(currentDate.getMonth() + (direction === "next" ? 1 : -1));
    setCurrentDate(newDate);
  };

  // Shared Post List View Component - Reusable across all views for consistent list display
  const PostListView: React.FC<{
    posts: Post[];
    title: string;
    onRefresh: () => void;
    onNavigate?: (direction: "prev" | "next") => void;
    showNavigation?: boolean;
  }> = ({ posts, title, onRefresh, onNavigate, showNavigation = false }) => {
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
          <Button variant="outline" size="sm" onClick={onRefresh}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>

        {posts.length > 0 ? (
          <div className="space-y-3">
            {posts.map((post) => (
              <DraggablePostCard
                key={post.id}
                post={post}
                onClick={() => {
                  setSelectedPost(post);
                  setIsExpanded(true);
                }}
                className="hover:shadow-md transition-shadow"
                showDragHandle={isDragDropEnabled()}
                compact={false} // Always use full display for list views
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

  // Main list view using the reusable PostListView component
  const renderListView = () => {
    return (
      <PostListView
        posts={scheduledPosts}
        title="All Scheduled Posts"
        onRefresh={fetchScheduledPosts}
      />
    );
  };

  const getMonthCalendarDays = (baseDate: Date) => {
    const year = baseDate.getFullYear();
    const month = baseDate.getMonth();

    // First day of the month
    const firstDay = new Date(year, month, 1);
    // Last day of the month
    const lastDay = new Date(year, month + 1, 0);

    // Start from the Sunday before the first day of the month
    const startDate = new Date(firstDay);
    startDate.setDate(firstDay.getDate() - firstDay.getDay());

    // End on the Saturday after the last day of the month
    const endDate = new Date(lastDay);
    endDate.setDate(lastDay.getDate() + (6 - lastDay.getDay()));

    const days = [];
    const currentDate = new Date(startDate);

    while (currentDate <= endDate) {
      days.push(new Date(currentDate));
      currentDate.setDate(currentDate.getDate() + 1);
    }

    return days;
  };

  const renderMonthView = () => {
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
              onClick={() => navigateMonth("prev")}
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <h3 className="text-lg font-semibold">{monthTitle}</h3>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigateMonth("next")}
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
          <Button variant="outline" size="sm" onClick={fetchScheduledPosts}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>

        {/* Calendar Grid - Full Width */}
        <div className="bg-white rounded-lg border">
          {/* Day headers */}
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

          {/* Calendar days */}
          <div className="grid grid-cols-7">
            {calendarDays.map((date, idx) => {
              const postsForDate = getPostsForDate(date);
              const isCurrentMonth = date.getMonth() === currentMonth;
              const isToday = date.toDateString() === today.toDateString();

              return (
                <DroppableMonthDay
                  key={idx}
                  date={date}
                  posts={postsForDate}
                  isCurrentMonth={isCurrentMonth}
                  isToday={isToday}
                  onPostClick={(post) => {
                    setSelectedPost(post);
                    setIsExpanded(true);
                  }}
                  showDropZone={isDragDropEnabled()}
                />
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <AppLayout title="Posting Schedule" emailBreakpoint="md">
        <main className="py-4 px-4 sm:py-8 sm:px-6">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin mr-3" />
              <span>Loading scheduled posts...</span>
            </div>
          </div>
        </main>
      </AppLayout>
    );
  }

  return (
    <AppLayout title="Posting Schedule" emailBreakpoint="md">
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        onDragOver={handleDragOver}
      >
        <main className="py-4 px-4 sm:py-8 sm:px-6">
          <div className="max-w-7xl mx-auto">
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-600">
                    Manage your content calendar and scheduled posts.
                  </p>
                  <p className="text-gray-600">
                    You may drag and drop posts to change their schedule.
                  </p>
                </div>

                <Tabs
                  value={viewMode}
                  onValueChange={(v) => setViewMode(v as "list" | "month")}
                >
                  <TabsList className="grid w-[240px] grid-cols-2">
                    <TabsTrigger value="list" className="text-xs">
                      <List className="w-3 h-3 mr-1" />
                      List
                    </TabsTrigger>
                    <TabsTrigger value="month" className="text-xs">
                      <CalendarDays className="w-3 h-3 mr-1" />
                      Month
                    </TabsTrigger>
                  </TabsList>
                </Tabs>
              </div>

              {viewMode === "list" && renderListView()}
              {viewMode === "month" && renderMonthView()}
            </div>
          </div>
        </main>

        <DragOverlay>
          {activePost ? (
            <DraggablePostCard
              post={activePost}
              showDragHandle={false}
              className="shadow-xl opacity-95"
              style={activePostStyle}
              isOverlay={true}
              compact={viewMode === "month"}
            />
          ) : null}
        </DragOverlay>
      </DndContext>

      {/* Post Detail Modal */}
      <ScheduledPostDetails
        isOpen={isExpanded}
        onClose={() => {
          setIsExpanded(false);
          setSelectedPost(null);
        }}
        post={selectedPost}
        onSaveForLater={handleSaveForLater}
        onReschedule={openRescheduleModal}
        onDelete={handleDeletePost}
        isProcessing={isRescheduling}
        getSourceIcon={getSourceIcon}
        getSourceLabel={getSourceLabel}
        formatDateTime={formatDateTime}
      />

      {/* Reschedule Modal */}
      <RescheduleModal
        isOpen={isRescheduleModalOpen}
        onClose={() => {
          setIsRescheduleModalOpen(false);
          setPostToReschedule(null);
        }}
        post={postToReschedule}
        scheduledPosts={scheduledPosts}
        onReschedule={handleReschedulePost}
        isRescheduling={isRescheduling}
      />

      {/* Drop Action Modal */}
      <Dialog
        open={isDropActionModalOpen}
        onOpenChange={setIsDropActionModalOpen}
      >
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Shuffle className="w-5 h-5" />
              Choose Drop Action
            </DialogTitle>
          </DialogHeader>

          {dropActionData && (
            <div className="space-y-4">
              <div className="text-sm text-gray-600">
                <p>
                  You dropped a post onto another post. Choose how to handle
                  this:
                </p>
              </div>

              <div className="space-y-3">
                <Button
                  variant="outline"
                  className="w-full justify-start h-auto p-4"
                  onClick={() => handleDropAction("swap")}
                  disabled={isRescheduling}
                >
                  <div className="flex items-center gap-3">
                    <Shuffle className="w-5 h-5 text-purple-600" />
                    <div className="text-left">
                      <div className="font-medium">Swap Schedules</div>
                      <div className="text-xs text-gray-500">
                        Swap the scheduled dates of the two posts
                      </div>
                    </div>
                  </div>
                </Button>

                <Button
                  variant="outline"
                  className="w-full justify-start h-auto p-4"
                  onClick={() => handleDropAction("push")}
                  disabled={isRescheduling}
                >
                  <div className="flex items-center gap-3">
                    <ArrowDown className="w-5 h-5 text-blue-600" />
                    <div className="text-left">
                      <div className="font-medium">Push Posts</div>
                      <div className="text-xs text-gray-500">
                        Push all posts from{" "}
                        {dropActionData.targetPost.scheduled_at &&
                          new Date(
                            dropActionData.targetPost.scheduled_at
                          ).toLocaleDateString()}{" "}
                        onwards by one day
                      </div>
                    </div>
                  </div>
                </Button>

                <Button
                  variant="outline"
                  className="w-full justify-start h-auto p-4"
                  onClick={() => handleDropAction("cancel")}
                  disabled={isRescheduling}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-5 h-5 text-gray-600" />
                    <div className="text-left">
                      <div className="font-medium">Cancel</div>
                      <div className="text-xs text-gray-500">
                        Cancel the operation and keep posts as they are
                      </div>
                    </div>
                  </div>
                </Button>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsDropActionModalOpen(false);
                setDropActionData(null);
              }}
              disabled={isRescheduling}
            >
              Cancel
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AppLayout>
  );
};

export default PostingSchedule;

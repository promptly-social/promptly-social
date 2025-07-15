import React, { useState, useEffect, useCallback } from "react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
import { RescheduleModal } from "@/components/schedule-modal/RescheduleModal";
import { ScheduledPostDetails } from "@/components/schedule-modal/ScheduledPostDetails";
import { DraggablePostCard } from "@/components/dnd-schedule/DraggablePostCard";
import { toast } from "@/hooks/use-toast";
import { postsApi } from "@/lib/posts-api";
import { Post } from "@/types/posts";
import { List, CalendarDays, Loader2 } from "lucide-react";
import { ListView } from "@/components/dnd-schedule/ListView";
import { MonthView } from "@/components/dnd-schedule/MonthView";
import {
  DropActionModal,
  DropActionData,
} from "@/components/dnd-schedule/DropActionModal";

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
  const [dropActionData, setDropActionData] = useState<DropActionData | null>(
    null
  );

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

  const fetchScheduledPosts = useCallback(async () => {
    try {
      setLoading(true);
      let after_date: string | undefined;
      let before_date: string | undefined;

      if (viewMode === "list") {
        after_date = new Date().toISOString();
      } else {
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth();
        const startDate = new Date(year, month - 1, 1);
        const endDate = new Date(year, month + 2, 0);
        after_date = startDate.toISOString();
        before_date = endDate.toISOString();
      }

      const response = await postsApi.getPosts({
        status: ["scheduled"],
        after_date,
        before_date,
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
  }, [viewMode, currentDate]);

  useEffect(() => {
    fetchScheduledPosts();
  }, [fetchScheduledPosts]);

  useEffect(() => {
    if (!isDropActionModalOpen) {
      const timer = setTimeout(() => {
        setDropActionData(null);
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [isDropActionModalOpen]);

  useEffect(() => {
    if (!isExpanded) {
      const timer = setTimeout(() => {
        setSelectedPost(null);
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [isExpanded]);

  useEffect(() => {
    if (!isRescheduleModalOpen) {
      const timer = setTimeout(() => {
        setPostToReschedule(null);
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [isRescheduleModalOpen]);

  const handleReschedulePost = async (
    postId: string,
    newScheduledAt: string
  ) => {
    try {
      setIsRescheduling(true);
      const updatedPost = await postsApi.updatePost(postId, {
        scheduled_at: newScheduledAt,
      });

      setScheduledPosts((prev) =>
        sortPostsByScheduledAt(
          prev.map((post) => (post.id === postId ? updatedPost : post))
        )
      );

      setIsRescheduleModalOpen(false);
      if (selectedPost?.id === postId) {
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

  const handleUpdatePost = async (
    postId: string,
    content: string,
    topics?: string[]
  ) => {
    try {
      setIsRescheduling(true);
      const payload: Record<string, unknown> = { content };
      if (Array.isArray(topics)) {
        payload.topics = topics;
      }

      const updatedPost = await postsApi.updatePost(postId, payload);

      setScheduledPosts((prev) =>
        sortPostsByScheduledAt(
          prev.map((post) => (post.id === postId ? updatedPost : post))
        )
      );

      if (selectedPost?.id === postId) {
        setSelectedPost(updatedPost);
      }

      toast({
        title: "Post Updated",
        description: "Your post has been successfully updated.",
      });
    } catch (error) {
      console.error("Error updating post:", error);
      toast({
        title: "Error",
        description: "Failed to update post. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsRescheduling(false);
    }
  };

  const handlePostPublished = (postId: string) => {
    setScheduledPosts((prev) =>
      prev.map((p) => (p.id === postId ? { ...p, status: "posted" } : p))
    );
    toast({
      title: "Post Published",
      description: "Your post has been successfully published to LinkedIn.",
    });
  };

  const openRescheduleModal = (post: Post) => {
    setPostToReschedule(post);
    setIsRescheduleModalOpen(true);
  };

  const handleSaveForLater = async (post: Post) => {
    try {
      setIsRescheduling(true);
      const updatedPost = await postsApi.updatePost(post.id, {
        status: "draft",
        scheduled_at: undefined,
      });

      setScheduledPosts(
        sortPostsByScheduledAt(scheduledPosts.filter((p) => p.id !== post.id))
      );
      if (selectedPost?.id === post.id) {
        setIsExpanded(false);
      }

      toast({
        title: "Saved for Later",
        description: "Post has been removed from schedule and moved to Drafts.",
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

  const handleDragStart = (event: DragStartEvent) => {
    if (!isDragDropEnabled()) return;

    const { active } = event;
    const post = scheduledPosts.find((p) => p.id === active.id);

    if (post) {
      setActivePost(post);

      if (viewMode === "list" && active.rect.current.initial) {
        setActivePostStyle({
          width: active.rect.current.initial.width,
          height: active.rect.current.initial.height,
        });
      } else {
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

    if (viewMode === "list" && overId !== postId) {
      const draggedPost = scheduledPosts.find((p) => p.id === postId);
      const targetPost = scheduledPosts.find((p) => p.id === overId);

      if (draggedPost && targetPost) {
        setDropActionData({
          draggedPost,
          targetPost,
        });
        setIsDropActionModalOpen(true);
        return;
      }
    }

    const dayId = overId;
    const dateMatch = dayId.match(/^day-(\d{4}-\d{2}-\d{2})$/);
    if (!dateMatch) {
      return;
    }

    const [year, month, day] = dateMatch[1].split("-").map(Number);
    const newDate = new Date(year, month - 1, day);

    const post = scheduledPosts.find((p) => p.id === postId);

    if (!post || !post.scheduled_at) {
      return;
    }

    const postsOnTargetDate = scheduledPosts.filter((p) => {
      if (!p.scheduled_at) return false;
      const postDate = new Date(p.scheduled_at);
      return (
        postDate.getFullYear() === newDate.getFullYear() &&
        postDate.getMonth() === newDate.getMonth() &&
        postDate.getDate() === newDate.getDate()
      );
    });

    if (postsOnTargetDate.length > 0 && postsOnTargetDate[0].id !== post.id) {
      setDropActionData({
        draggedPost: post,
        targetPost: postsOnTargetDate[0],
      });
      setIsDropActionModalOpen(true);
      return;
    }

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

    const currentTime = new Date(post.scheduled_at);
    newDate.setHours(
      currentTime.getHours(),
      currentTime.getMinutes(),
      currentTime.getSeconds(),
      currentTime.getMilliseconds()
    );

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
        const [year, month, day] = dateMatch[1].split("-").map(Number);
        const date = new Date(year, month - 1, day);

        const today = new Date();
        today.setHours(0, 0, 0, 0);
        date.setHours(0, 0, 0, 0);
      }
    }
  };

  const handlePushPosts = async (targetPost: Post) => {
    if (!targetPost.scheduled_at) return;

    const targetDate = new Date(targetPost.scheduled_at);
    targetDate.setHours(0, 0, 0, 0);

    // Find all posts on or after the target date, sorted
    const subsequentPosts = scheduledPosts
      .filter((p) => {
        if (!p.scheduled_at) return false;
        const postDate = new Date(p.scheduled_at);
        postDate.setHours(0, 0, 0, 0);
        return postDate.getTime() >= targetDate.getTime();
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

    await postsApi.batchUpdatePosts({ posts: updatedPosts });

    toast({
      title: "Posts Pushed",
      description: "Posts have been pushed to the next available slot.",
    });
  };

  const handleSwapPosts = async (post1: Post, post2: Post) => {
    if (!post1.scheduled_at || !post2.scheduled_at) return;

    const tempDate = post1.scheduled_at;

    await Promise.all([
      postsApi.updatePost(post1.id, { scheduled_at: post2.scheduled_at }),
      postsApi.updatePost(post2.id, { scheduled_at: tempDate }),
    ]);

    toast({
      title: "Posts Swapped",
      description: "The scheduled dates of the two posts have been swapped.",
    });
  };

  const handleDropAction = async (action: "swap" | "push") => {
    if (!dropActionData) return;

    const { draggedPost, targetPost } = dropActionData;

    try {
      setIsRescheduling(true);

      switch (action) {
        case "push": {
          const targetDate = targetPost.scheduled_at;
          await handlePushPosts(targetPost);
          if (targetDate) {
            await postsApi.updatePost(draggedPost.id, {
              scheduled_at: targetDate,
            });
          }
          break;
        }
        case "swap":
          if (draggedPost.scheduled_at && targetPost.scheduled_at) {
            await handleSwapPosts(draggedPost, targetPost);
          }
          break;
      }
    } catch (error) {
      console.error("Error handling drop action:", error);
      toast({
        title: "Error",
        description: "Failed to process the action. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsRescheduling(false);
      setIsDropActionModalOpen(false);
      await fetchScheduledPosts();
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

  const navigateMonth = (direction: "prev" | "next") => {
    const newDate = new Date(currentDate);
    newDate.setMonth(currentDate.getMonth() + (direction === "next" ? 1 : -1));
    setCurrentDate(newDate);
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

              {viewMode === "list" && (
                <ListView
                  posts={scheduledPosts}
                  onPostClick={(post) => {
                    setSelectedPost(post);
                    setIsExpanded(true);
                  }}
                  isDragDropEnabled={isDragDropEnabled()}
                />
              )}
              {viewMode === "month" && (
                <MonthView
                  currentDate={currentDate}
                  posts={scheduledPosts}
                  onNavigateMonth={navigateMonth}
                  onPostClick={(post) => {
                    setSelectedPost(post);
                    setIsExpanded(true);
                  }}
                  isDragDropEnabled={isDragDropEnabled()}
                />
              )}
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

      <ScheduledPostDetails
        isOpen={isExpanded}
        onClose={() => {
          setIsExpanded(false);
        }}
        post={selectedPost}
        onSaveForLater={handleSaveForLater}
        onReschedule={openRescheduleModal}
        onDelete={handleDeletePost}
        onUpdatePost={handleUpdatePost}
        onPostPublished={handlePostPublished}
        isProcessing={isRescheduling}
        formatDateTime={formatDateTime}
      />

      <RescheduleModal
        isOpen={isRescheduleModalOpen}
        onClose={() => {
          setIsRescheduleModalOpen(false);
        }}
        post={postToReschedule}
        onReschedule={handleReschedulePost}
        isRescheduling={isRescheduling}
      />

      <DropActionModal
        isOpen={isDropActionModalOpen}
        onOpenChange={setIsDropActionModalOpen}
        onAction={handleDropAction}
        isProcessing={isRescheduling}
        dropActionData={dropActionData}
      />
    </AppLayout>
  );
};

export default PostingSchedule;

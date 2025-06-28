import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import AppLayout from "@/components/AppLayout";
import { PostCard } from "@/components/PostCard";
import { PostScheduleModal } from "@/components/PostScheduleModal";
import { RefreshCw, ArrowLeft, Filter, TrendingUp } from "lucide-react";

import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { postsApi, Post } from "@/lib/posts-api";
import { toast } from "sonner";

interface Filters {
  status?: string[];
  platform?: string;
  order_by?: string;
  order_direction?: "asc" | "desc";
}

const MyContent: React.FC = () => {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const postId = searchParams.get("post");

  const [posts, setPosts] = useState<Post[]>([]);
  const [selectedPost, setSelectedPost] = useState<Post | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [editingPostId, setEditingPostId] = useState<string | null>(null);
  const [editedContent, setEditedContent] = useState<string>("");
  const [feedbackModal, setFeedbackModal] = useState<{
    isOpen: boolean;
    postId: string | null;
  }>({ isOpen: false, postId: null });
  const [feedbackComment, setFeedbackComment] = useState<string>("");
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);
  const [dismissingPostId, setDismissingPostId] = useState<string | null>(null);
  const [savingPostId, setSavingPostId] = useState<string | null>(null);
  const [undoTimeouts, setUndoTimeouts] = useState<Map<string, NodeJS.Timeout>>(
    new Map()
  );
  const [scheduleModal, setScheduleModal] = useState<{
    isOpen: boolean;
    post: Post | null;
  }>({ isOpen: false, post: null });
  const [scheduledPosts, setScheduledPosts] = useState<Post[]>([]);
  const [isScheduling, setIsScheduling] = useState(false);
  const [filters, setFilters] = useState<Filters>({
    status: ["suggested", "saved"], // Show suggested and saved by default
    platform: undefined,
    order_by: "created_at",
    order_direction: "desc",
  });
  const [pendingFilters, setPendingFilters] = useState<Filters>({
    status: ["suggested", "saved"], // Show suggested and saved by default
    platform: undefined,
    order_by: "created_at",
    order_direction: "desc",
  });

  useEffect(() => {
    const fetchData = async () => {
      if (!user) return;

      try {
        setIsLoading(true);

        if (postId) {
          // Fetch specific post
          const post = await postsApi.getPost(postId);
          setSelectedPost(post);
          setPosts([post]);
        } else {
          // Fetch all posts with filters
          const postsResponse = await postsApi.getPosts(filters);
          setPosts(postsResponse.items);
          setSelectedPost(null);

          // Fetch scheduled posts for the schedule modal
          const scheduledResponse = await postsApi.getPosts({
            status: ["scheduled"],
            order_by: "scheduled_at",
            order_direction: "asc",
            size: 100,
          });
          setScheduledPosts(scheduledResponse.items);
        }
      } catch (error) {
        console.error("Error fetching data:", error);
        toast.error("Failed to fetch posts. Please try again.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [user, postId, filters]);

  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => {
      undoTimeouts.forEach((timeoutId) => {
        clearTimeout(timeoutId);
      });
    };
  }, [undoTimeouts]);

  const handlePendingFilterChange = (newFilters: Partial<Filters>) => {
    setPendingFilters((prev) => ({ ...prev, ...newFilters }));
  };

  const applyFilters = () => {
    setFilters(pendingFilters);
  };

  const clearPendingFilters = () => {
    const defaultFilters: Filters = {
      status: ["suggested", "saved"],
      platform: undefined,
      order_by: "created_at",
      order_direction: "desc",
    };
    setPendingFilters(defaultFilters);
  };

  const clearAllFilters = () => {
    const defaultFilters: Filters = {
      status: ["suggested", "saved"],
      platform: undefined,
      order_by: "created_at",
      order_direction: "desc",
    };
    setPendingFilters(defaultFilters);
    setFilters(defaultFilters);
  };

  const getActiveFilterCount = () => {
    let count = 0;
    if (
      filters.status &&
      !(
        filters.status.length === 2 &&
        filters.status.includes("suggested") &&
        filters.status.includes("saved")
      )
    ) {
      count++;
    }
    if (filters.platform) count++;
    if (filters.order_by && filters.order_by !== "created_at") count++;
    if (filters.order_direction && filters.order_direction !== "desc") count++;
    return count;
  };

  const goBackToList = () => {
    setSearchParams({});
    setSelectedPost(null);
  };

  const dismissPost = async (post: Post) => {
    setDismissingPostId(post.id);

    // Create undo timeout
    const timeoutId = setTimeout(async () => {
      try {
        await postsApi.dismissPost(post.id);
        setPosts(posts.filter((p) => p.id !== post.id));
        setUndoTimeouts((prev) => {
          const newMap = new Map(prev);
          newMap.delete(post.id);
          return newMap;
        });
        // If this was the selected post, go back to list
        if (selectedPost?.id === post.id) {
          goBackToList();
        }
      } catch (error) {
        console.error("Error dismissing post:", error);
        toast.error("Failed to dismiss post. Please try again.");
      }
      setDismissingPostId(null);
    }, 3000);

    // Store timeout for potential undo
    setUndoTimeouts((prev) => new Map(prev).set(post.id, timeoutId));

    // Show toast with undo option
    toast.success("Post dismissed", {
      description: "Post will be removed in 3 seconds",
      action: {
        label: "Undo",
        onClick: () => undoDismiss(post.id),
      },
      duration: 3100,
    });
  };

  const undoDismiss = (postId: string) => {
    const timeoutId = undoTimeouts.get(postId);
    if (timeoutId) {
      clearTimeout(timeoutId);
      setUndoTimeouts((prev) => {
        const newMap = new Map(prev);
        newMap.delete(postId);
        return newMap;
      });
    }
    setDismissingPostId(null);
    toast.success("Dismiss cancelled", {
      description: "Post has been restored.",
    });
  };

  const schedulePost = (postId: string) => {
    const post = posts.find((p) => p.id === postId);
    if (post) {
      setScheduleModal({ isOpen: true, post });
    }
  };

  const handleSchedulePost = async (postId: string, scheduledAt: string) => {
    setIsScheduling(true);
    try {
      const updatedPost = await postsApi.schedulePost(postId, scheduledAt);

      // Update posts list
      setPosts(posts.map((p) => (p.id === postId ? updatedPost : p)));

      // Update selected post if it's the same one
      if (selectedPost?.id === postId) {
        setSelectedPost(updatedPost);
      }

      // Add to scheduled posts
      setScheduledPosts([...scheduledPosts, updatedPost]);

      // Close modal
      setScheduleModal({ isOpen: false, post: null });

      toast.success("Post Scheduled", {
        description: `Post has been scheduled for ${new Date(
          scheduledAt
        ).toLocaleString()}`,
      });
    } catch (error) {
      console.error("Error scheduling post:", error);
      toast.error("Failed to schedule post. Please try again.");
    } finally {
      setIsScheduling(false);
    }
  };

  const removeFromSchedule = async (post: Post) => {
    try {
      const updatedPost = await postsApi.updatePost(post.id, {
        status: "saved",
      });

      setPosts(posts.map((p) => (p.id === post.id ? updatedPost : p)));
      if (selectedPost?.id === post.id) {
        setSelectedPost(updatedPost);
      }

      toast.success("Removed from Schedule", {
        description: "Post has been removed from schedule and saved for later.",
      });
    } catch (error) {
      console.error("Error removing from schedule:", error);
      toast.error("Failed to remove from schedule. Please try again.");
    }
  };

  const reschedulePost = (postId: string) => {
    console.log("Rescheduling post:", postId);

    toast.success("Coming Soon", {
      description: "Post rescheduling will be available soon!",
    });
  };

  const saveForLater = async (post: Post) => {
    setSavingPostId(post.id);
    try {
      const updatedPost = await postsApi.updatePost(post.id, {
        status: "saved",
      });

      setPosts(posts.map((p) => (p.id === post.id ? updatedPost : p)));
      if (selectedPost?.id === post.id) {
        setSelectedPost(updatedPost);
      }

      toast.success("Post Saved", {
        description: "Post has been saved for later.",
      });
    } catch (error) {
      console.error("Error saving post:", error);
      toast.error("Failed to save post. Please try again.");
    } finally {
      setSavingPostId(null);
    }
  };

  const startEditing = (post: Post) => {
    setEditingPostId(post.id);
    setEditedContent(post.content);
  };

  const saveEdit = async (postId: string) => {
    try {
      const updatedPost = await postsApi.updatePost(postId, {
        content: editedContent,
      });

      setPosts(posts.map((p) => (p.id === postId ? updatedPost : p)));
      if (selectedPost?.id === postId) {
        setSelectedPost(updatedPost);
      }
      setEditingPostId(null);
      setEditedContent("");

      toast.success("Post Updated", {
        description: "Your changes have been saved.",
      });
    } catch (error) {
      console.error("Error updating post:", error);
      toast.error("Failed to update the post. Please try again.");
    }
  };

  const cancelEdit = () => {
    setEditingPostId(null);
    setEditedContent("");
  };

  const submitPositiveFeedback = async (postId: string) => {
    try {
      const updatedPost = await postsApi.submitFeedback(postId, {
        feedback_type: "positive",
      });

      setPosts(posts.map((p) => (p.id === postId ? updatedPost : p)));
      if (selectedPost?.id === postId) {
        setSelectedPost(updatedPost);
      }

      toast.success("Feedback Submitted", {
        description: "Thank you for your positive feedback!",
      });
    } catch (error) {
      console.error("Error submitting feedback:", error);
      toast.error("Failed to submit feedback. Please try again.");
    }
  };

  const openNegativeFeedbackModal = (postId: string) => {
    setFeedbackModal({ isOpen: true, postId });
    setFeedbackComment("");
  };

  const submitNegativeFeedback = async () => {
    if (!feedbackModal.postId) return;

    setIsSubmittingFeedback(true);
    try {
      const updatedPost = await postsApi.submitFeedback(feedbackModal.postId, {
        feedback_type: "negative",
        comment: feedbackComment || undefined,
      });

      setPosts(
        posts.map((p) => (p.id === feedbackModal.postId ? updatedPost : p))
      );
      if (selectedPost?.id === feedbackModal.postId) {
        setSelectedPost(updatedPost);
      }

      setFeedbackModal({ isOpen: false, postId: null });
      setFeedbackComment("");

      toast.success("Feedback Submitted", {
        description:
          "Thank you for your feedback! We'll use it to improve suggestions.",
      });
    } catch (error) {
      console.error("Error submitting feedback:", error);
      toast.error("Failed to submit feedback. Please try again.");
    } finally {
      setIsSubmittingFeedback(false);
    }
  };

  const filterButton = (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm" className="relative">
          <Filter className="w-4 h-4 sm:mr-2" />
          <span className="hidden sm:inline">Filter</span>
          {getActiveFilterCount() > 0 && (
            <Badge className="absolute -top-2 -right-2 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs">
              {getActiveFilterCount()}
            </Badge>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="font-medium">Filters</h4>
            <Button variant="ghost" size="sm" onClick={clearPendingFilters}>
              Clear
            </Button>
          </div>

          <div className="space-y-3">
            <div className="space-y-2">
              <Label>Post Status</Label>
              <div className="space-y-2">
                {[
                  "suggested",
                  "saved",
                  "posted",
                  "scheduled",
                  "canceled",
                  "dismissed",
                ].map((status) => (
                  <div key={status} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id={`status-${status}`}
                      checked={pendingFilters.status?.includes(status) || false}
                      onChange={(e) => {
                        const currentStatuses = pendingFilters.status || [];
                        if (e.target.checked) {
                          handlePendingFilterChange({
                            status: [...currentStatuses, status],
                          });
                        } else {
                          handlePendingFilterChange({
                            status: currentStatuses.filter((s) => s !== status),
                          });
                        }
                      }}
                      className="rounded border-gray-300"
                    />
                    <Label htmlFor={`status-${status}`} className="capitalize">
                      {status}
                    </Label>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="flex gap-2 pt-3 border-t">
            <Button onClick={applyFilters} size="sm" className="flex-1">
              Apply Filters
            </Button>
            <Button
              onClick={clearAllFilters}
              variant="outline"
              size="sm"
              className="flex-1"
            >
              Clear All
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );

  if (isLoading) {
    return (
      <AppLayout title="My Content" emailBreakpoint="md">
        <main className="py-4 px-4 sm:py-8 sm:px-6">
          <div className="max-w-7xl mx-auto">
            <div className="text-center py-8">
              <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2" />
              <p className="text-gray-600">Loading content...</p>
            </div>
          </div>
        </main>
      </AppLayout>
    );
  }

  return (
    <AppLayout title="My Content" emailBreakpoint="md">
      <main className="py-4 px-4 sm:py-8 sm:px-6">
        <div className="max-w-7xl mx-auto">
          {/* Single Post View */}
          {selectedPost ? (
            <div className="space-y-4 sm:space-y-6">
              <Button
                variant="ghost"
                size="sm"
                onClick={goBackToList}
                className="flex items-center gap-2"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to My Posts
              </Button>

              <div className="max-w-4xl">
                <PostCard
                  post={selectedPost}
                  index={0}
                  editingPostId={editingPostId}
                  editedContent={editedContent}
                  savingPostId={savingPostId}
                  dismissingPostId={dismissingPostId}
                  onStartEditing={startEditing}
                  onSaveEdit={saveEdit}
                  onCancelEdit={cancelEdit}
                  onEditContentChange={setEditedContent}
                  onSubmitPositiveFeedback={submitPositiveFeedback}
                  onOpenNegativeFeedbackModal={openNegativeFeedbackModal}
                  onSchedulePost={schedulePost}
                  onRemoveFromSchedule={removeFromSchedule}
                  onReschedulePost={reschedulePost}
                  onSaveForLater={saveForLater}
                  onDismissPost={dismissPost}
                />
              </div>
            </div>
          ) : (
            /* Posts List View */
            <div className="space-y-4 sm:space-y-6">
              <div className="text-center">
                <p className="text-sm sm:text-lg text-gray-600 max-w-2xl mx-auto">
                  Manage your content suggestions and posts
                </p>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-md text-gray-600 font-medium">
                  {posts.length} {posts.length === 1 ? "post" : "posts"}
                </span>
                <div className="flex items-center gap-2">{filterButton}</div>
              </div>

              {posts.length === 0 ? (
                <Card>
                  <CardContent className="py-8 sm:py-12 text-center">
                    <TrendingUp className="w-8 sm:w-12 h-8 sm:h-12 mx-auto mb-4 text-gray-400" />
                    <h3 className="text-base sm:text-lg font-medium mb-2">
                      No posts found
                    </h3>
                    <p className="text-sm sm:text-base text-gray-600">
                      Your suggested and published posts will appear here
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid gap-4 sm:gap-6">
                  {posts.map((post, index) => (
                    <PostCard
                      key={post.id}
                      post={post}
                      index={index}
                      editingPostId={editingPostId}
                      editedContent={editedContent}
                      savingPostId={savingPostId}
                      dismissingPostId={dismissingPostId}
                      onStartEditing={startEditing}
                      onSaveEdit={saveEdit}
                      onCancelEdit={cancelEdit}
                      onEditContentChange={setEditedContent}
                      onSubmitPositiveFeedback={submitPositiveFeedback}
                      onOpenNegativeFeedbackModal={openNegativeFeedbackModal}
                      onSchedulePost={schedulePost}
                      onRemoveFromSchedule={removeFromSchedule}
                      onReschedulePost={reschedulePost}
                      onSaveForLater={saveForLater}
                      onDismissPost={dismissPost}
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </main>

      {/* Negative Feedback Modal */}
      <Dialog
        open={feedbackModal.isOpen}
        onOpenChange={(open) =>
          !open && setFeedbackModal({ isOpen: false, postId: null })
        }
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Help us improve</DialogTitle>
            <DialogDescription>
              We'd appreciate your feedback on why this suggestion wasn't
              helpful. This is optional but helps us improve future suggestions.
            </DialogDescription>
          </DialogHeader>
          <Textarea
            placeholder="Tell us what was wrong with this suggestion... (optional)"
            value={feedbackComment}
            onChange={(e) => setFeedbackComment(e.target.value)}
            className="min-h-[100px] resize-none"
          />
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setFeedbackModal({ isOpen: false, postId: null })}
            >
              Skip
            </Button>
            <Button
              onClick={submitNegativeFeedback}
              disabled={isSubmittingFeedback}
            >
              {isSubmittingFeedback ? "Submitting..." : "Submit Feedback"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Schedule Post Modal */}
      <PostScheduleModal
        isOpen={scheduleModal.isOpen}
        onClose={() => setScheduleModal({ isOpen: false, post: null })}
        post={scheduleModal.post}
        scheduledPosts={scheduledPosts}
        onSchedule={handleSchedulePost}
        isScheduling={isScheduling}
      />
    </AppLayout>
  );
};

export default MyContent;

import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import AppLayout from "@/components/AppLayout";
import {
  RefreshCw,
  Calendar,
  ArrowLeft,
  Filter,
  TrendingUp,
  Clock,
  Share2,
  Globe,
  User,
  ThumbsUp,
  ThumbsDown,
  Edit3,
  Check,
  X,
  Bookmark,
} from "lucide-react";

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
import { suggestedPostsApi, SuggestedPost } from "@/lib/suggested-posts-api";
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

  const [posts, setPosts] = useState<SuggestedPost[]>([]);
  const [selectedPost, setSelectedPost] = useState<SuggestedPost | null>(null);
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
  const [filters, setFilters] = useState<Filters>({
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
          const post = await suggestedPostsApi.getSuggestedPost(postId);
          setSelectedPost(post);
          setPosts([post]);
        } else {
          // Fetch all posts with filters
          const postsResponse = await suggestedPostsApi.getSuggestedPosts(
            filters
          );
          setPosts(postsResponse.items);
          setSelectedPost(null);
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

  const handleFilterChange = (newFilters: Partial<Filters>) => {
    setFilters((prev) => ({ ...prev, ...newFilters }));
  };

  const clearFilters = () => {
    setFilters({
      status: ["suggested", "saved"],
      platform: undefined,
      order_by: "created_at",
      order_direction: "desc",
    });
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

  const dismissPost = async (post: SuggestedPost) => {
    setDismissingPostId(post.id);

    // Create undo timeout
    const timeoutId = setTimeout(async () => {
      try {
        await suggestedPostsApi.dismissSuggestedPost(post.id);
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
    console.log("Scheduling post:", postId);
    // TODO: Implement scheduling logic
    toast.success("Coming Soon", {
      description: "Post scheduling will be available soon!",
    });
  };

  const removeFromSchedule = async (post: SuggestedPost) => {
    try {
      const updatedPost = await suggestedPostsApi.updateSuggestedPost(post.id, {
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
    // TODO: Implement rescheduling logic
    toast.success("Coming Soon", {
      description: "Post rescheduling will be available soon!",
    });
  };

  const saveForLater = async (post: SuggestedPost) => {
    setSavingPostId(post.id);
    try {
      const updatedPost = await suggestedPostsApi.updateSuggestedPost(post.id, {
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

  const startEditing = (post: SuggestedPost) => {
    setEditingPostId(post.id);
    setEditedContent(post.content);
  };

  const saveEdit = async (postId: string) => {
    try {
      const updatedPost = await suggestedPostsApi.updateSuggestedPost(postId, {
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
      const updatedPost = await suggestedPostsApi.submitFeedback(postId, {
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
      const updatedPost = await suggestedPostsApi.submitFeedback(
        feedbackModal.postId,
        {
          feedback_type: "negative",
          comment: feedbackComment || undefined,
        }
      );

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

  const getSourceIcon = (platform: string) => {
    switch (platform) {
      case "linkedin":
        return <Share2 className="w-3 h-3" />;
      case "substack":
        return <Globe className="w-3 h-3" />;
      default:
        return <User className="w-3 h-3" />;
    }
  };

  const getSourceLabel = (platform: string) => {
    switch (platform) {
      case "linkedin":
        return "LinkedIn";
      case "substack":
        return "Substack";
      default:
        return "General";
    }
  };

  const getStatusColor = (status: string) => {
    const statusColors: Record<string, string> = {
      suggested: "bg-gray-100 text-gray-800",
      saved: "bg-purple-100 text-purple-800",
      posted: "bg-green-100 text-green-800",
      scheduled: "bg-yellow-100 text-yellow-800",
      canceled: "bg-orange-100 text-orange-800",
      dismissed: "bg-red-100 text-red-800",
    };
    return statusColors[status] || "bg-gray-100 text-gray-800";
  };

  const renderContentWithNewlines = (content: string) => {
    return content.split("\n").map((line, index) => (
      <React.Fragment key={index}>
        {line}
        {index < content.split("\n").length - 1 && <br />}
      </React.Fragment>
    ));
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const renderPost = (post: SuggestedPost, index: number) => (
    <Card
      key={post.id}
      className="relative hover:shadow-md transition-shadow flex flex-col h-full"
    >
      <CardHeader className="pb-3 sm:pb-4">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant="secondary" className="text-xs">
                {getSourceIcon(post.platform)}
                <span className="ml-1">{getSourceLabel(post.platform)}</span>
              </Badge>
              <Badge
                className={`${getStatusColor(post.status)} text-xs`}
                variant="secondary"
              >
                {post.status.charAt(0).toUpperCase() + post.status.slice(1)}
              </Badge>
              {post.user_feedback && (
                <Badge
                  variant={
                    post.user_feedback === "positive"
                      ? "default"
                      : "destructive"
                  }
                  className="text-xs"
                >
                  {post.user_feedback === "positive" ? (
                    <>
                      <ThumbsUp className="w-3 h-3 mr-1" />
                      Liked
                    </>
                  ) : (
                    <>
                      <ThumbsDown className="w-3 h-3 mr-1" />
                      Disliked
                    </>
                  )}
                </Badge>
              )}
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 flex-grow flex flex-col">
        <div className="bg-gray-50 p-3 sm:p-4 rounded-lg relative">
          {editingPostId === post.id ? (
            <div className="space-y-3">
              <Textarea
                value={editedContent}
                onChange={(e) => setEditedContent(e.target.value)}
                className="min-h-[300px] max-h-[400px] resize-y"
                placeholder="Edit your post content..."
              />
              <div className="flex gap-2">
                <Button size="sm" onClick={() => saveEdit(post.id)}>
                  <Check className="w-4 h-4 mr-1" />
                  Save
                </Button>
                <Button size="sm" variant="outline" onClick={cancelEdit}>
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <>
              <p className="text-sm sm:text-base text-gray-800 leading-relaxed whitespace-pre-wrap">
                {renderContentWithNewlines(post.content)}
              </p>
              <Button
                size="sm"
                variant="ghost"
                className="absolute top-2 right-2 p-1 h-6 w-6"
                onClick={() => startEditing(post)}
              >
                <Edit3 className="w-3 h-3" />
              </Button>
            </>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 text-xs sm:text-sm">
          <div className="flex items-center gap-2 text-gray-600">
            <TrendingUp className="w-4 h-4 text-green-500" />
            <span>
              Recommendation score:{" "}
              <strong>{post.recommendation_score}/100</strong>
            </span>
          </div>
          <div className="flex items-center gap-2 text-gray-600">
            <Clock className="w-4 h-4 text-blue-500" />
            <span>
              Created: <strong>{formatDate(post.created_at)}</strong>
            </span>
          </div>
        </div>

        {post.topics.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs sm:text-sm font-medium text-gray-700">
              Topics:
            </p>
            <div className="flex flex-wrap gap-1 sm:gap-2">
              {post.topics.map((topic, idx) => (
                <Badge key={idx} variant="outline" className="text-xs">
                  {topic}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Feedback Section */}
        {!post.user_feedback && (
          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <span className="text-sm text-gray-600">
              How is this suggestion?
            </span>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => submitPositiveFeedback(post.id)}
                className="text-green-600 hover:text-green-700 hover:bg-green-50"
              >
                <ThumbsUp className="w-4 h-4" />
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => openNegativeFeedbackModal(post.id)}
                className="text-red-600 hover:text-red-700 hover:bg-red-50"
              >
                <ThumbsDown className="w-4 h-4" />
              </Button>
            </div>
          </div>
        )}

        <div className="flex-grow"></div>

        {post.status !== "posted" && (
          <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 pt-3 border-t border-gray-100">
            {post.status === "scheduled" ? (
              <>
                <Button
                  onClick={() => removeFromSchedule(post)}
                  variant="outline"
                  className="flex-1 text-orange-600 hover:text-orange-700 hover:bg-orange-50"
                >
                  <X className="w-4 h-4 mr-2" />
                  Remove from Schedule
                </Button>
                <Button
                  onClick={() => reschedulePost(post.id)}
                  className="bg-blue-600 hover:bg-blue-700 flex-1"
                >
                  <Calendar className="w-4 h-4 mr-2" />
                  Reschedule
                </Button>
              </>
            ) : (
              <>
                <Button
                  onClick={() => schedulePost(post.id)}
                  className="bg-green-600 hover:bg-green-700 flex-1"
                >
                  <Calendar className="w-4 h-4 mr-2" />
                  Schedule Post
                </Button>
                {post.status === "suggested" && (
                  <Button
                    onClick={() => saveForLater(post)}
                    variant="outline"
                    className="flex-1 text-purple-600 hover:text-purple-700 hover:bg-purple-50"
                    disabled={savingPostId === post.id}
                  >
                    {savingPostId === post.id ? (
                      <>
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      <>
                        <Bookmark className="w-4 h-4 mr-2" />
                        Save for Later
                      </>
                    )}
                  </Button>
                )}
              </>
            )}
            <Button
              variant="outline"
              className="flex-1 text-red-600 hover:text-red-700 hover:bg-red-50"
              onClick={() => dismissPost(post)}
              disabled={dismissingPostId === post.id}
            >
              {dismissingPostId === post.id ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Dismissing...
                </>
              ) : (
                <>
                  <X className="w-4 h-4 mr-2" />
                  Dismiss
                </>
              )}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );

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
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              Clear all
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
                      checked={filters.status?.includes(status) || false}
                      onChange={(e) => {
                        const currentStatuses = filters.status || [];
                        if (e.target.checked) {
                          handleFilterChange({
                            status: [...currentStatuses, status],
                          });
                        } else {
                          handleFilterChange({
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
        </div>
      </PopoverContent>
    </Popover>
  );

  const refreshButton = (
    <Button
      onClick={() => window.location.reload()}
      disabled={isLoading}
      variant="outline"
      size="sm"
    >
      <RefreshCw
        className={`w-4 h-4 ${isLoading ? "animate-spin" : ""} sm:mr-2`}
      />
      <span className="hidden sm:inline">Refresh</span>
    </Button>
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

              <div className="max-w-4xl">{renderPost(selectedPost, 0)}</div>
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
                <div className="flex items-center gap-2">
                  {filterButton}
                  {refreshButton}
                </div>
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
                  {posts.map((post, index) => renderPost(post, index))}
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
    </AppLayout>
  );
};

export default MyContent;

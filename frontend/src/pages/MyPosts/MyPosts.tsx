import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import AppLayout from "@/components/AppLayout";
import { PostCard } from "@/components/shared/PostCard";
import { PostScheduleModal } from "@/components/PostScheduleModal";
import { RescheduleModal } from "@/components/RescheduleModal";
import { RefreshCw, ArrowLeft, TrendingUp } from "lucide-react";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";

type TabName = "drafts" | "scheduled" | "posted";

const MyPosts: React.FC = () => {
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
  const [rescheduleModal, setRescheduleModal] = useState<{
    isOpen: boolean;
    post: Post | null;
  }>({ isOpen: false, post: null });
  const [scheduledPosts, setScheduledPosts] = useState<Post[]>([]);
  const [isScheduling, setIsScheduling] = useState(false);
  const [isRescheduling, setIsRescheduling] = useState(false);

  const [activeTab, setActiveTab] = useState<TabName>("drafts");
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalPosts, setTotalPosts] = useState(0);

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
          setTotalPages(1);
          setTotalPosts(1);
        } else {
          // Fetch all posts with filters for the active tab
          const statusMap: Record<TabName, string[]> = {
            drafts: ["suggested", "saved"],
            scheduled: ["scheduled"],
            posted: ["posted"],
          };
          const postsResponse = await postsApi.getPosts({
            status: statusMap[activeTab],
            order_by: activeTab === "scheduled" ? "scheduled_at" : "created_at",
            order_direction: "desc",
            page: currentPage,
            size: 10,
          });
          setPosts(postsResponse.items);
          setTotalPosts(postsResponse.total);
          setTotalPages(postsResponse.pages);
          setSelectedPost(null);
        }

        // Fetch scheduled posts for the schedule modal
        const scheduledResponse = await postsApi.getPosts({
          status: ["scheduled"],
          order_by: "scheduled_at",
          order_direction: "asc",
          size: 100,
        });
        setScheduledPosts(scheduledResponse.items);
      } catch (error) {
        console.error("Error fetching data:", error);
        toast.error("Failed to fetch posts. Please try again.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [user, postId, activeTab, currentPage]);

  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => {
      undoTimeouts.forEach((timeoutId) => {
        clearTimeout(timeoutId);
      });
    };
  }, [undoTimeouts]);

  const handleTabChange = (tab: string) => {
    setActiveTab(tab as TabName);
    setCurrentPage(1); // Reset to first page on tab change
  };

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
    }
  };

  const goBackToList = () => {
    setSearchParams({});
    setSelectedPost(null);
    // Refetch data for the current tab and page
    setCurrentPage(1); // or refetch current page
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

      // Optimistically remove from current list and update other lists
      setPosts(posts.filter((p) => p.id !== postId));
      setTotalPosts((prev) => prev - 1);

      // Update selected post if it's the same one
      if (selectedPost?.id === postId) {
        setSelectedPost(updatedPost);
      }

      // Add to scheduled posts
      setScheduledPosts(
        [...scheduledPosts, updatedPost].sort(
          (a, b) =>
            new Date(a.scheduled_at).getTime() -
            new Date(b.scheduled_at).getTime()
        )
      );

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

      // Optimistically remove from current list
      setPosts(posts.filter((p) => p.id !== post.id));
      setTotalPosts((prev) => prev - 1);

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
    const post = posts.find((p) => p.id === postId);
    if (post) {
      setRescheduleModal({ isOpen: true, post });
    }
  };

  const handleReschedulePost = async (postId: string, scheduledAt: string) => {
    setIsRescheduling(true);
    try {
      const updatedPost = await postsApi.schedulePost(postId, scheduledAt);

      // Update posts list
      setPosts(posts.map((p) => (p.id === postId ? updatedPost : p)));

      // Update scheduled posts list
      setScheduledPosts(
        scheduledPosts
          .map((p) => (p.id === postId ? updatedPost : p))
          .sort(
            (a, b) =>
              new Date(a.scheduled_at).getTime() -
              new Date(b.scheduled_at).getTime()
          )
      );

      // Update selected post if it's the same one
      if (selectedPost?.id === postId) {
        setSelectedPost(updatedPost);
      }

      // Close modal
      setRescheduleModal({ isOpen: false, post: null });

      toast.success("Post Rescheduled", {
        description: `Post has been rescheduled for ${new Date(
          scheduledAt
        ).toLocaleString()}`,
      });
    } catch (error) {
      console.error("Error rescheduling post:", error);
      toast.error("Failed to reschedule post. Please try again.");
    } finally {
      setIsRescheduling(false);
    }
  };

  const saveForLater = async (post: Post) => {
    setSavingPostId(post.id);
    try {
      const updatedPost = await postsApi.updatePost(post.id, {
        status: "saved",
      });

      // If viewing suggested posts, this one becomes 'saved' so it can stay in 'drafts'
      if (activeTab === "drafts") {
        setPosts(posts.map((p) => (p.id === post.id ? updatedPost : p)));
      } else {
        // If coming from another tab, remove it from the current view
        setPosts(posts.filter((p) => p.id !== post.id));
        setTotalPosts((prev) => prev - 1);
      }

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

  const title = "My Posts";

  if (isLoading && posts.length === 0) {
    return (
      <AppLayout title={title} emailBreakpoint="md">
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
    <AppLayout title={title} emailBreakpoint="md">
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

              <Tabs
                value={activeTab}
                onValueChange={handleTabChange}
                className="w-full"
              >
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="drafts">Drafts</TabsTrigger>
                  <TabsTrigger value="scheduled">Scheduled</TabsTrigger>
                  <TabsTrigger value="posted">Posted</TabsTrigger>
                </TabsList>
                <TabsContent value="drafts">
                  <PostList
                    posts={posts}
                    isLoading={isLoading}
                    totalPosts={totalPosts}
                    currentPage={currentPage}
                    totalPages={totalPages}
                    onPageChange={handlePageChange}
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
                </TabsContent>
                <TabsContent value="scheduled">
                  <PostList
                    posts={posts}
                    isLoading={isLoading}
                    totalPosts={totalPosts}
                    currentPage={currentPage}
                    totalPages={totalPages}
                    onPageChange={handlePageChange}
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
                </TabsContent>
                <TabsContent value="posted">
                  <PostList
                    posts={posts}
                    isLoading={isLoading}
                    totalPosts={totalPosts}
                    currentPage={currentPage}
                    totalPages={totalPages}
                    onPageChange={handlePageChange}
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
                </TabsContent>
              </Tabs>
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
      <RescheduleModal
        isOpen={rescheduleModal.isOpen}
        onClose={() => setRescheduleModal({ isOpen: false, post: null })}
        post={rescheduleModal.post}
        scheduledPosts={scheduledPosts}
        onReschedule={handleReschedulePost}
        isRescheduling={isRescheduling}
      />
    </AppLayout>
  );
};

interface PostListProps {
  posts: Post[];
  isLoading: boolean;
  totalPosts: number;
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  editingPostId: string | null;
  editedContent: string;
  savingPostId: string | null;
  dismissingPostId: string | null;
  onStartEditing: (post: Post) => void;
  onSaveEdit: (postId: string) => void;
  onCancelEdit: () => void;
  onEditContentChange: (content: string) => void;
  onSubmitPositiveFeedback: (postId: string) => void;
  onOpenNegativeFeedbackModal: (postId: string) => void;
  onSchedulePost: (postId: string) => void;
  onRemoveFromSchedule: (post: Post) => void;
  onReschedulePost: (postId: string) => void;
  onSaveForLater: (post: Post) => void;
  onDismissPost: (post: Post) => void;
}

const PostList: React.FC<PostListProps> = ({
  posts,
  isLoading,
  totalPosts,
  currentPage,
  totalPages,
  onPageChange,
  ...postCardProps
}) => {
  if (isLoading && posts.length === 0) {
    return (
      <div className="text-center py-8">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2" />
        <p className="text-gray-600">Loading posts...</p>
      </div>
    );
  }

  if (posts.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 sm:py-12 text-center">
          <TrendingUp className="w-8 sm:w-12 h-8 sm:h-12 mx-auto mb-4 text-gray-400" />
          <h3 className="text-base sm:text-lg font-medium mb-2">
            No posts found
          </h3>
          <p className="text-sm sm:text-base text-gray-600">
            There are no posts in this category.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex items-center justify-between">
        <span className="text-md text-gray-600 font-medium">
          {totalPosts} {totalPosts === 1 ? "post" : "posts"}
        </span>
      </div>

      <div className="grid gap-4 sm:gap-6">
        {posts.map((post, index) => (
          <PostCard
            key={post.id}
            post={post}
            index={index}
            {...postCardProps}
          />
        ))}
      </div>

      {totalPages > 1 && (
        <Pagination>
          <PaginationContent>
            <PaginationItem>
              <PaginationPrevious
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  onPageChange(currentPage - 1);
                }}
                className={
                  currentPage === 1 ? "pointer-events-none opacity-50" : ""
                }
              />
            </PaginationItem>
            <PaginationItem>
              <PaginationNext
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  onPageChange(currentPage + 1);
                }}
                className={
                  currentPage === totalPages
                    ? "pointer-events-none opacity-50"
                    : ""
                }
              />
            </PaginationItem>
          </PaginationContent>
        </Pagination>
      )}
    </div>
  );
};

export default MyPosts;

import React, { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  CardFooter,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Clock,
  RefreshCw,
  Calendar,
  TrendingUp,
  User,
  Globe,
  Share2,
  ThumbsUp,
  ThumbsDown,
  Edit3,
  Check,
  X,
  Bookmark,
  Eye,
  EyeOff,
  Copy,
  ExternalLink,
  Loader2,
} from "lucide-react";
import { postsApi, Post } from "@/lib/posts-api";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/contexts/AuthContext";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";

interface SuggestedPostsProps {
  className?: string;
}

interface PostWithFeedback extends Post {
  showFeedback?: boolean;
  feedbackComment?: string;
}

export function SuggestedPosts({ className }: SuggestedPostsProps) {
  const [posts, setPosts] = useState<PostWithFeedback[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
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
  const [toastDismissers, setToastDismissers] = useState<
    Map<string, () => void>
  >(new Map());
  const { toast } = useToast();
  const { user } = useAuth();

  useEffect(() => {
    const fetchData = async () => {
      if (!user) return;

      try {
        setLoading(true);
        const postsResponse = await postsApi.getPosts({
          status: ["suggested"],
          order_by: "recommendation_score",
          order_direction: "desc",
        });

        setPosts(postsResponse.items);
      } catch (error) {
        console.error("Error fetching data:", error);
        toast({
          title: "Error",
          description: "Failed to fetch suggested posts. Please try again.",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [user, toast]);

  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => {
      undoTimeouts.forEach((timeoutId) => {
        clearTimeout(timeoutId);
      });
    };
  }, [undoTimeouts]);

  const handleCopyContent = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      toast({
        title: "Content Copied",
        description: "Content has been copied to clipboard",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to copy content",
        variant: "destructive",
      });
    }
  };

  const handleDismiss = async (postId: string) => {
    setDismissingPostId(postId);

    // Show toast with undo option first to get the dismiss function
    const { dismiss: dismissToast } = toast({
      title: "Post dismissed",
      description: (
        <div className="space-y-2">
          <p>Post will be removed in 3 seconds</p>
          <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
            <div
              className="bg-red-600 h-2 rounded-full"
              style={{
                width: "100%",
                animation: "shrink-width 3s linear forwards",
              }}
            />
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              undoDismiss(postId);
              dismissToast();
            }}
            className="w-full"
          >
            Undo
          </Button>
        </div>
      ),
      duration: 3100,
    });

    // Store toast dismisser for potential undo and cleanup
    setToastDismissers((prev) => new Map(prev).set(postId, dismissToast));

    // Create undo timeout
    const timeoutId = setTimeout(async () => {
      try {
        await postsApi.dismissPost(postId);
        setPosts(posts.filter((p) => p.id !== postId));
        setUndoTimeouts((prev) => {
          const newMap = new Map(prev);
          newMap.delete(postId);
          return newMap;
        });
        setToastDismissers((prev) => {
          const newMap = new Map(prev);
          newMap.delete(postId);
          return newMap;
        });
        // Dismiss the toast when the timeout completes
        dismissToast();
      } catch (error) {
        console.error("Error dismissing post:", error);
        toast({
          title: "Error",
          description: "Failed to dismiss post. Please try again.",
          variant: "destructive",
        });
        // Dismiss the original toast on error as well
        dismissToast();
      }
      setDismissingPostId(null);
    }, 3000);

    // Store timeout for potential undo
    setUndoTimeouts((prev) => new Map(prev).set(postId, timeoutId));
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

    // Clean up toast dismisser
    setToastDismissers((prev) => {
      const newMap = new Map(prev);
      newMap.delete(postId);
      return newMap;
    });

    setDismissingPostId(null);
    toast({
      title: "Dismiss cancelled",
      description: "Post has been restored.",
    });
  };

  const handleMarkAsPosted = async (postId: string) => {
    try {
      setLoadingAction(`mark-posted-${postId}`);
      await postsApi.markAsPosted(postId);
      setPosts(posts.filter((p) => p.id !== postId));
      toast({
        title: "Post marked as posted",
        description: "Post has been marked as posted",
      });
    } catch (error) {
      console.error("Error marking post as posted:", error);
      toast({
        title: "Error",
        description: "Failed to mark post as posted",
        variant: "destructive",
      });
    } finally {
      setLoadingAction(null);
    }
  };

  const handleFeedback = async (
    postId: string,
    feedbackType: "positive" | "negative",
    comment?: string
  ) => {
    try {
      setLoadingAction(`feedback-${postId}`);
      await postsApi.submitFeedback(postId, {
        feedback_type: feedbackType,
        comment: comment || undefined,
      });

      // Update the post in the state
      setPosts(
        posts.map((post) =>
          post.id === postId
            ? {
                ...post,
                user_feedback: feedbackType,
                feedback_comment: comment,
                showFeedback: false,
              }
            : post
        )
      );

      toast({
        title: `${
          feedbackType === "positive" ? "Positive" : "Negative"
        } feedback submitted`,
        description: "Thank you for your feedback!",
      });
    } catch (error) {
      console.error("Error submitting feedback:", error);
      toast({
        title: "Error",
        description: "Failed to submit feedback. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoadingAction(null);
    }
  };

  const toggleFeedback = (postId: string) => {
    setPosts(
      posts.map((post) =>
        post.id === postId
          ? { ...post, showFeedback: !post.showFeedback }
          : post
      )
    );
  };

  const updateFeedbackComment = (postId: string, comment: string) => {
    setPosts(
      posts.map((post) =>
        post.id === postId ? { ...post, feedbackComment: comment } : post
      )
    );
  };

  const generateNewPosts = async () => {
    setIsGenerating(true);
    try {
      // TODO: Implement actual post generation API call
      // For now, just refresh the existing posts
      const postsResponse = await postsApi.getPosts({
        status: ["suggested"],
        order_by: "created_at",
        order_direction: "desc",
      });

      // Sort by created_at (desc) first, then by recommendation_score (desc) for items with same created_at
      const sortedPosts = postsResponse.items.sort((a, b) => {
        // First sort by created_at (desc)
        const dateA = new Date(a.created_at).getTime();
        const dateB = new Date(b.created_at).getTime();
        if (dateB !== dateA) {
          return dateB - dateA;
        }

        // If created_at is the same, sort by recommendation_score (desc)
        return b.recommendation_score - a.recommendation_score;
      });

      setPosts(sortedPosts);

      toast({
        title: "Posts Refreshed",
        description: "Your suggested posts have been updated.",
      });
    } catch (error) {
      console.error("Error generating posts:", error);
      toast({
        title: "Error",
        description: "Failed to generate new posts. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const startEditing = (post: PostWithFeedback) => {
    setEditingPostId(post.id);
    setEditedContent(post.content);
  };

  const saveEdit = async (postId: string) => {
    try {
      const updatedPost = await postsApi.updatePost(postId, {
        content: editedContent,
      });

      setPosts(posts.map((p) => (p.id === postId ? updatedPost : p)));
      setEditingPostId(null);
      setEditedContent("");

      toast({
        title: "Post Updated",
        description: "Your changes have been saved.",
      });
    } catch (error) {
      console.error("Error updating post:", error);
      toast({
        title: "Error",
        description: "Failed to update the post. Please try again.",
        variant: "destructive",
      });
    }
  };

  const cancelEdit = () => {
    setEditingPostId(null);
    setEditedContent("");
  };

  const openNegativeFeedbackModal = (postId: string) => {
    setFeedbackModal({ isOpen: true, postId });
    setFeedbackComment("");
  };

  const submitNegativeFeedback = async () => {
    if (!feedbackModal.postId) return;

    setIsSubmittingFeedback(true);
    try {
      await handleFeedback(feedbackModal.postId, "negative", feedbackComment);
      setFeedbackModal({ isOpen: false, postId: null });
      setFeedbackComment("");
    } catch (error) {
      console.error("Error submitting feedback:", error);
      toast({
        title: "Error",
        description: "Failed to submit feedback. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSubmittingFeedback(false);
    }
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

  const renderContentWithNewlines = (content: string) => {
    return content.split("\n").map((line, index) => (
      <React.Fragment key={index}>
        {line}
        {index < content.split("\n").length - 1 && <br />}
      </React.Fragment>
    ));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading posts...</span>
      </div>
    );
  }

  if (posts.length === 0) {
    return (
      <div className="text-center p-8">
        <p className="text-muted-foreground">
          No posts available. Generate some ideas first!
        </p>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900">
            Suggested Posts ({posts.length})
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            AI-suggested posts based on your writing style, interests, and
            ideas.
          </p>
        </div>
        <Button
          onClick={generateNewPosts}
          disabled={isGenerating}
          className="bg-blue-600 hover:bg-blue-700 w-full sm:w-auto"
        >
          {isGenerating ? (
            <>
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <RefreshCw className="w-4 h-4 mr-2" />
              Generate New Posts
            </>
          )}
        </Button>
      </div>

      {posts.map((post) => (
        <Card key={post.id} className="w-full">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Badge variant="outline">{getSourceIcon(post.platform)}</Badge>
                <Badge variant="secondary">
                  Score: {post.recommendation_score}
                </Badge>
              </div>
              <div className="flex items-center gap-2">
                {post.user_feedback && (
                  <Badge
                    variant={
                      post.user_feedback === "positive"
                        ? "default"
                        : "destructive"
                    }
                  >
                    {post.user_feedback === "positive" ? "Liked" : "Disliked"}
                  </Badge>
                )}
              </div>
            </div>
            {post.title && (
              <CardTitle className="text-lg">{post.title}</CardTitle>
            )}
            <CardDescription>
              {post.topics.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {post.topics.map((topic, index) => (
                    <Badge key={index} variant="outline" className="text-xs">
                      {topic}
                    </Badge>
                  ))}
                </div>
              )}
            </CardDescription>
          </CardHeader>

          <CardContent>
            <div className="whitespace-pre-wrap text-sm leading-relaxed">
              {renderContentWithNewlines(post.content)}
            </div>
          </CardContent>

          <CardFooter className="flex flex-col gap-3">
            <div className="flex items-center gap-2 w-full">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleCopyContent(post.content)}
                className="flex items-center gap-2"
              >
                <Copy className="h-4 w-4" />
                Copy
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={() => toggleFeedback(post.id)}
                className="flex items-center gap-2"
              >
                {post.showFeedback ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
                {post.showFeedback ? "Hide" : "Feedback"}
              </Button>

              <div className="ml-auto flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleDismiss(post.id)}
                  disabled={loadingAction === `dismiss-${post.id}`}
                >
                  {loadingAction === `dismiss-${post.id}` ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    "Dismiss"
                  )}
                </Button>

                <Button
                  size="sm"
                  onClick={() => handleMarkAsPosted(post.id)}
                  disabled={loadingAction === `mark-posted-${post.id}`}
                  className="flex items-center gap-2"
                >
                  {loadingAction === `mark-posted-${post.id}` ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <>
                      <ExternalLink className="h-4 w-4" />
                      Mark as Posted
                    </>
                  )}
                </Button>
              </div>
            </div>

            {post.showFeedback && (
              <div className="w-full border-t pt-3 space-y-3">
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      handleFeedback(post.id, "positive", post.feedbackComment)
                    }
                    disabled={loadingAction === `feedback-${post.id}`}
                    className="flex items-center gap-2"
                  >
                    <ThumbsUp className="h-4 w-4" />
                    {loadingAction === `feedback-${post.id}` ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      "Like"
                    )}
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      handleFeedback(post.id, "negative", post.feedbackComment)
                    }
                    disabled={loadingAction === `feedback-${post.id}`}
                    className="flex items-center gap-2"
                  >
                    <ThumbsDown className="h-4 w-4" />
                    {loadingAction === `feedback-${post.id}` ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      "Dislike"
                    )}
                  </Button>
                </div>

                <Textarea
                  placeholder="Add your feedback (optional)..."
                  value={post.feedbackComment || ""}
                  onChange={(e) =>
                    updateFeedbackComment(post.id, e.target.value)
                  }
                  className="text-sm"
                  rows={3}
                />
              </div>
            )}
          </CardFooter>
        </Card>
      ))}

      {posts.length === 0 && (
        <Card className="text-center py-8 sm:py-12">
          <CardContent>
            <TrendingUp className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              No posts available
            </h3>
            <p className="text-gray-600 mb-4 text-sm sm:text-base">
              No suggested posts found. Generate new content suggestions to get
              started.
            </p>
            <Button onClick={generateNewPosts} disabled={isGenerating}>
              {isGenerating ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Generate New Posts
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      )}

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
    </div>
  );
}

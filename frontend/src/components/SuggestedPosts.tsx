import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
} from "lucide-react";
import { suggestedPostsApi, SuggestedPost } from "@/lib/suggested-posts-api";
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

export const SuggestedPosts: React.FC = () => {
  const [posts, setPosts] = useState<SuggestedPost[]>([]);
  const [isLoading, setIsLoading] = useState(true);
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
  const [undoTimeouts, setUndoTimeouts] = useState<Map<string, NodeJS.Timeout>>(
    new Map()
  );
  const { toast } = useToast();
  const { user } = useAuth();

  useEffect(() => {
    const fetchData = async () => {
      if (!user) return;

      try {
        const postsResponse = await suggestedPostsApi.getSuggestedPosts({
          status: ["suggested"],
          platform: "linkedin",
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
        setIsLoading(false);
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
      } catch (error) {
        console.error("Error dismissing post:", error);
        toast({
          title: "Error",
          description: "Failed to dismiss post. Please try again.",
          variant: "destructive",
        });
      }
      setDismissingPostId(null);
    }, 3000);

    // Store timeout for potential undo
    setUndoTimeouts((prev) => new Map(prev).set(post.id, timeoutId));

    // Show toast with undo option
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
              undoDismiss(post.id);
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
    toast({
      title: "Dismiss cancelled",
      description: "Post has been restored.",
    });
  };

  const schedulePost = (postId: string) => {
    console.log("Scheduling post:", postId);
    // TODO: Implement scheduling logic
    toast({
      title: "Coming Soon",
      description: "Post scheduling will be available soon!",
    });
  };

  const generateNewPosts = async () => {
    setIsGenerating(true);
    try {
      // TODO: Implement actual post generation API call
      // For now, just refresh the existing posts
      const postsResponse = await suggestedPostsApi.getSuggestedPosts({
        status: ["suggested"],
        platform: "linkedin",
        order_by: "recommendation_score",
        order_direction: "desc",
      });
      setPosts(postsResponse.items);

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

  const submitPositiveFeedback = async (postId: string) => {
    try {
      const updatedPost = await suggestedPostsApi.submitFeedback(postId, {
        feedback_type: "positive",
      });

      setPosts(posts.map((p) => (p.id === postId ? updatedPost : p)));

      toast({
        title: "Feedback Submitted",
        description: "Thank you for your positive feedback!",
      });
    } catch (error) {
      console.error("Error submitting feedback:", error);
      toast({
        title: "Error",
        description: "Failed to submit feedback. Please try again.",
        variant: "destructive",
      });
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

      setFeedbackModal({ isOpen: false, postId: null });
      setFeedbackComment("");

      toast({
        title: "Feedback Submitted",
        description:
          "Thank you for your feedback! We'll use it to improve suggestions.",
      });
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

  const renderContentWithNewlines = (content: string) => {
    return content.split("\n").map((line, index) => (
      <React.Fragment key={index}>
        {line}
        {index < content.split("\n").length - 1 && <br />}
      </React.Fragment>
    ));
  };

  if (isLoading) {
    return (
      <div className="space-y-4 sm:space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900">
              Suggested Posts
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              AI-suggested posts based on your writing style, interests, and
              ideas.
            </p>
          </div>
        </div>
        <div className="grid gap-4 sm:gap-6">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader>
                <div className="h-4 bg-gray-200 rounded w-1/4"></div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="h-4 bg-gray-200 rounded"></div>
                  <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900">
            Suggested Posts
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

      <div className="grid gap-4 sm:gap-6">
        {posts.map((post, index) => (
          <Card
            key={post.id}
            className="relative hover:shadow-md transition-shadow"
          >
            <CardHeader className="pb-3 sm:pb-4">
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="secondary" className="text-xs">
                      {getSourceIcon(post.platform)}
                      <span className="ml-1">
                        {getSourceLabel(post.platform)}
                      </span>
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
                  <CardTitle className="text-base sm:text-lg font-semibold text-gray-900">
                    {post.title || `Post #${index + 1}`}
                  </CardTitle>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
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
                    Created:{" "}
                    <strong>
                      {new Date(post.created_at).toLocaleDateString()}
                    </strong>
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

              <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 pt-3 border-t border-gray-100">
                <Button
                  onClick={() => schedulePost(post.id)}
                  className="bg-green-600 hover:bg-green-700 flex-1"
                  disabled={post.status === "posted"}
                >
                  <Calendar className="w-4 h-4 mr-2" />
                  Schedule Post
                </Button>
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
            </CardContent>
          </Card>
        ))}
      </div>

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
};

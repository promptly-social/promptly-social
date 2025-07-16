import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RefreshCw, TrendingUp, Loader2 } from "lucide-react";
import { PostCard } from "@/components/shared/post-card/PostCard";
import { PostScheduleModal } from "@/components/schedule-modal/PostScheduleModal";
import { postsApi } from "@/lib/posts-api";
import { Post } from "@/types/posts";
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

export function SuggestedPosts({ className }: SuggestedPostsProps) {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [feedbackModal, setFeedbackModal] = useState<{
    isOpen: boolean;
    postId: string | null;
  }>({ isOpen: false, postId: null });
  const [feedbackComment, setFeedbackComment] = useState<string>("");
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);
  const [scheduleModal, setScheduleModal] = useState<{
    isOpen: boolean;
    post: Post | null;
  }>({ isOpen: false, post: null });
  const [scheduledPosts, setScheduledPosts] = useState<Post[]>([]);
  const [isScheduling, setIsScheduling] = useState(false);
  const { toast } = useToast();
  const { user } = useAuth();

  useEffect(() => {
    const fetchData = async () => {
      if (!user) return;

      try {
        setLoading(true);

        // Fetch suggested posts
        const postsResponse = await postsApi.getPosts({
          status: ["suggested"],
          order_by: "created_at",
          order_direction: "desc",
        });

        setPosts(postsResponse.items);

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
        toast({
          title: "Error",
          description: "Failed to fetch posts. Please try again.",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [user, toast]);

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

  const handleSchedulePost = async (postId: string, scheduledAt: string) => {
    setIsScheduling(true);
    try {
      const updatedPost = await postsApi.schedulePost(postId, scheduledAt);

      // Remove from suggested posts
      setPosts(posts.filter((p) => p.id !== postId));

      // Add to scheduled posts
      setScheduledPosts([...scheduledPosts, updatedPost]);

      // Close modal
      setScheduleModal({ isOpen: false, post: null });

      toast({
        title: "Post Scheduled",
        description: `Post has been scheduled for ${new Date(
          scheduledAt
        ).toLocaleString()}`,
      });
    } catch (error) {
      console.error("Error scheduling post:", error);
      toast({
        title: "Error",
        description: "Failed to schedule post. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsScheduling(false);
    }
  };

  const generateNewPosts = async () => {
    setIsGenerating(true);
    try {
      await postsApi.generatePosts();
      toast({
        title: "Post generation started",
        description:
          "Your new posts will be ready in a few minutes. Please check back.",
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

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading posts...</span>
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
        <div className="flex gap-x-2">
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
      </div>

      {posts.map((post, index) => (
        <PostCard key={post.id} post={post} onPostUpdate={() => {}} />
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

      {/* Schedule Post Modal */}
      <PostScheduleModal
        isOpen={scheduleModal.isOpen}
        onClose={() => setScheduleModal({ isOpen: false, post: null })}
        post={scheduleModal.post}
        onSchedule={handleSchedulePost}
        isScheduling={isScheduling}
      />
    </div>
  );
}

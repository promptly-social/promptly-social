import React, { useState } from "react";
import { usePosts, usePostCounts, postsKeys } from "@/lib/posts-queries";
import { Post } from "@/types/posts";
import { PostCard } from "@/components/shared/post-card/PostCard";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import AppLayout from "@/components/AppLayout";
import { CreatePostModal } from "@/components/post-modal/CreatePostModal";
import { PostScheduleModal } from "@/components/schedule-modal/PostScheduleModal";
import { PlusIcon, Sparkles } from "lucide-react";
import { PostGenerationChatDialog } from "@/components/chat/PostGenerationChatDialog";
import { useQueryClient } from "@tanstack/react-query";
import { postsApi } from "@/lib/posts-api";
import { useToast } from "@/hooks/use-toast";

const PostListLayout = ({ children }: { children: React.ReactNode }) => (
  <div className="space-y-6 p-4 sm:p-6 max-w-4xl mx-auto w-full">
    {children}
  </div>
);

export const MyPosts: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"drafts" | "scheduled" | "posted">(
    "drafts"
  );
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isBrainstormOpen, setIsBrainstormOpen] = useState(false);
  const [postToSchedule, setPostToSchedule] = useState<Post | null>(null);
  const [isScheduling, setIsScheduling] = useState(false);

  const [currentPage, setCurrentPage] = useState(1);
  const postsPerPage = 10;

  const queryClient = useQueryClient();
  const { toast } = useToast();

  const statusArray =
    activeTab === "drafts" ? ["suggested", "draft"] : [activeTab];

  const {
    data: postsResponse,
    isLoading,
    error: postsError,
  } = usePosts({
    status: statusArray,
    page: currentPage,
    size: postsPerPage,
  });

  const posts = postsResponse?.items ?? [];
  const totalPages = Math.max(
    1,
    Math.ceil((postsResponse?.total ?? 0) / postsPerPage)
  );

  const { data: postCounts } = usePostCounts();

  const invalidatePostsData = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: postsKeys.all }),
      queryClient.invalidateQueries({ queryKey: postsKeys.counts }),
    ]);
  };

  // Exposed handler for children ----------------------------------------
  const handlePostUpdate = async () => {
    await invalidatePostsData();
  };

  const handleScheduleRequest = (post: Post) => {
    setPostToSchedule(post);
  };

  const handleSchedule = async (postId: string, scheduledAt: string) => {
    setIsScheduling(true);
    try {
      await postsApi.schedulePost(postId, scheduledAt);
      toast({
        title: "Success",
        description: "Post scheduled successfully.",
      });
      setPostToSchedule(null);
      await invalidatePostsData();
    } catch (error) {
      console.error("Failed to schedule post:", error);
      toast({
        title: "Error",
        description: "Failed to schedule post. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsScheduling(false);
    }
  };

  if (postsError) {
    return (
      <div className="flex justify-center items-center h-full">
        <p className="text-red-500">Failed to fetch posts.</p>
      </div>
    );
  }

  return (
    <AppLayout title="My Posts" emailBreakpoint="md">
      <div className="p-4 sm:p-6 border-b">
        <div className="max-w-4xl mx-auto w-full">
          <div className="flex justify-end mb-4">
            <Button
              variant="default"
              size="sm"
              onClick={() => setIsCreateModalOpen(true)}
            >
              <PlusIcon className="h-5 w-5 mr-2" /> New Post
            </Button>
            <Button
              variant="default"
              size="sm"
              className="ml-2"
              onClick={() => setIsBrainstormOpen(true)}
            >
              <Sparkles className="h-5 w-5 mr-2" /> Brain Storm
            </Button>
          </div>

          <Tabs
            value={activeTab}
            onValueChange={(value) => {
              setActiveTab(value as "drafts" | "scheduled" | "posted");
              setCurrentPage(1);
            }}
            className="mt-4"
          >
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="drafts">
                Drafts {postCounts ? `(${postCounts.drafts})` : ""}
              </TabsTrigger>
              <TabsTrigger value="scheduled">
                Scheduled {postCounts ? `(${postCounts.scheduled})` : ""}
              </TabsTrigger>
              <TabsTrigger value="posted">
                Posted {postCounts ? `(${postCounts.posted})` : ""}
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        <div className="flex-1 overflow-y-scroll">
          {isLoading ? (
            <PostListLayout>
              {Array.from({ length: 3 }).map((_, index) => (
                <Skeleton key={index} className="h-96 w-full" />
              ))}
            </PostListLayout>
          ) : (
            <PostListLayout>
              {posts.map((post) => (
                <PostCard
                  key={post.id}
                  post={post}
                  onPostUpdate={handlePostUpdate}
                />
              ))}
            </PostListLayout>
          )}
        </div>

        <div className="flex justify-center items-center p-4">
          <Button
            onClick={() => setCurrentPage((p) => p - 1)}
            disabled={currentPage === 1}
            variant="outline"
            size="sm"
          >
            Previous
          </Button>
          <span className="mx-4 text-sm">
            Page {currentPage} of {totalPages}
          </span>
          <Button
            onClick={() => setCurrentPage((p) => p + 1)}
            disabled={currentPage === totalPages}
            variant="outline"
            size="sm"
          >
            Next
          </Button>
        </div>
      </div>
      <CreatePostModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onCreated={async () => {
          await invalidatePostsData();
        }}
        onScheduleRequest={handleScheduleRequest}
      />
      <PostGenerationChatDialog
        conversationType="brainstorm"
        open={isBrainstormOpen}
        onOpenChange={setIsBrainstormOpen}
        onScheduleComplete={async () => {
          await invalidatePostsData();
        }}
      />
      <PostScheduleModal
        isOpen={!!postToSchedule}
        onClose={() => setPostToSchedule(null)}
        post={postToSchedule}
        onSchedule={handleSchedule}
        isScheduling={isScheduling}
      />
    </AppLayout>
  );
};

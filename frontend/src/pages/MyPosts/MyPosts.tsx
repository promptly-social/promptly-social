import React, { useState, useEffect, useCallback, useRef } from "react";
import { postsApi } from "@/lib/posts-api";
import { Post } from "@/types/posts";
import { PostCard } from "@/components/shared/post-card/PostCard";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/hooks/use-toast";
import { Skeleton } from "@/components/ui/skeleton";
import AppLayout from "@/components/AppLayout";
import { CreatePostModal } from "@/components/post-modal/CreatePostModal";
import { PlusIcon } from "lucide-react";

const PostListLayout = ({ children }: { children: React.ReactNode }) => (
  <div className="space-y-6 p-4 sm:p-6 max-w-4xl mx-auto w-full">
    {children}
  </div>
);

export const MyPosts: React.FC = () => {
  const [posts, setPosts] = useState<Post[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("drafts");
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [postCounts, setPostCounts] = useState<{
    drafts: number;
    scheduled: number;
    posted: number;
  } | null>(null);

  // Simple in-memory cache for posts per tab & page
  const postsCache = useRef<
    Record<string, Record<number, { items: Post[]; total: number }>>
  >({});

  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const postsPerPage = 10;

  const { toast } = useToast();

  const fetchCounts = useCallback(async () => {
    try {
      const counts = await postsApi.getPostCounts();
      setPostCounts(counts);
    } catch (err) {
      console.error(err);
    }
  }, []);

  const fetchPosts = useCallback(async () => {
    setIsLoading(true);
    const statusArray =
      activeTab === "drafts" ? ["suggested", "draft"] : [activeTab];

    // Check cache first
    const cached = postsCache.current[activeTab]?.[currentPage];
    if (cached) {
      setPosts(cached.items);
      setTotalPages(Math.ceil(cached.total / postsPerPage));
      setIsLoading(false);
      return;
    }

    try {
      const postsResponse = await postsApi.getPosts({
        status: statusArray,
        page: currentPage,
        size: postsPerPage,
      });

      // Update cache
      postsCache.current[activeTab] = postsCache.current[activeTab] || {};
      postsCache.current[activeTab][currentPage] = {
        items: postsResponse.items,
        total: postsResponse.total,
      };

      setPosts(postsResponse.items);
      setTotalPages(Math.ceil(postsResponse.total / postsPerPage));
      setError(null);
    } catch (err) {
      setError("Failed to fetch posts.");
      toast({
        title: "Error",
        description: "Failed to fetch post data.",
        variant: "destructive",
      });
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, [activeTab, currentPage, toast]);

  // Fetch counts once on mount
  useEffect(() => {
    fetchCounts();
  }, [fetchCounts]);

  // Fetch posts when tab or page changes
  useEffect(() => {
    fetchPosts();
  }, [fetchPosts]);

  // Handle post updates more intelligently to avoid full reloads when unnecessary
  const handlePostUpdate = async (updatedPost?: Post) => {
    // If we receive an updated post object, update local state & cache without network calls
    if (updatedPost) {
      setPosts((prev) =>
        prev.map((p) => (p.id === updatedPost.id ? updatedPost : p))
      );

      const cachePage = postsCache.current[activeTab]?.[currentPage];
      if (cachePage) {
        cachePage.items = cachePage.items.map((p) =>
          p.id === updatedPost.id ? updatedPost : p
        );
      }
      return;
    }

    // Otherwise invalidate caches & refetch, since the post likely moved tabs or was deleted
    delete postsCache.current[activeTab];
    await fetchPosts();
    await fetchCounts();
  };

  if (error) {
    return (
      <div className="flex justify-center items-center h-full">
        <p className="text-red-500">{error}</p>
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
          </div>

          <Tabs
            value={activeTab}
            onValueChange={(value) => {
              setActiveTab(value);
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
        onCreated={(post) => {
          // Invalidate cache and refresh lists/counts
          delete postsCache.current["drafts"];
          handlePostUpdate();
        }}
      />
    </AppLayout>
  );
};

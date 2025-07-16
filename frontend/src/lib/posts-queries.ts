import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  postsApi,
  type GetPostsParams,
  type PostsListResponse,
  type CreatePostRequest,
  type PostCounts,
  type PostBatchUpdateRequest,
} from "./posts-api";
import { Post, PostUpdate } from "@/types/posts";

/**
 * Centralised query keys for all post-related queries.
 * Keeping them in one place guarantees we invalidate/refetch consistently.
 */
export const postsKeys = {
  all: ["posts"] as const,
  list: (params: GetPostsParams) => ["posts", params] as const,
  counts: ["postCounts"] as const,
};

// ---------------------------------------------------------------------------
// Queries
// ---------------------------------------------------------------------------

export const usePosts = (params: GetPostsParams) =>
  useQuery<PostsListResponse, Error>({
    queryKey: postsKeys.list(params),
    queryFn: () => postsApi.getPosts(params),
    staleTime: 60 * 1000, // 1 min
  });

export const usePostCounts = () =>
  useQuery<PostCounts, Error>({
    queryKey: postsKeys.counts,
    queryFn: () => postsApi.getPostCounts(),
    staleTime: 60 * 1000,
  });

// ---------------------------------------------------------------------------
// Mutations – each one invalidates the relevant cached queries automatically
// ---------------------------------------------------------------------------

export const useCreatePost = () => {
  const qc = useQueryClient();
  return useMutation<Post, Error, CreatePostRequest>({
    mutationFn: (data) => postsApi.createPost(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: postsKeys.all });
      qc.invalidateQueries({ queryKey: postsKeys.counts });
    },
  });
};

export const useUpdatePost = () => {
  const qc = useQueryClient();
  return useMutation<Post, Error, { postId: string; data: PostUpdate }>({
    mutationFn: ({ postId, data }) => postsApi.updatePost(postId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: postsKeys.all });
      qc.invalidateQueries({ queryKey: postsKeys.counts });
    },
  });
};

export const useBatchUpdatePosts = () => {
  const qc = useQueryClient();
  return useMutation<PostsListResponse, Error, PostBatchUpdateRequest>({
    mutationFn: (data) => postsApi.batchUpdatePosts(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: postsKeys.all });
    },
  });
};

export const useDeletePost = () => {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: (postId) => postsApi.deletePost(postId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: postsKeys.all });
      qc.invalidateQueries({ queryKey: postsKeys.counts });
    },
  });
};

// Additional hooks (schedule, dismiss, etc.) could be added in the same style.

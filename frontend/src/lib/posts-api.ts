/**
 * Posts API client
 */

import { apiClient } from "./auth-api";

export interface Post {
  id: string;
  user_id: string;
  idea_bank_id?: string;
  title?: string;
  content: string;
  platform: string;
  topics: string[];
  recommendation_score: number;
  status: string;
  user_feedback?: string;
  feedback_comment?: string;
  feedback_at?: string;
  scheduled_at?: string;
  created_at: string;
  updated_at: string;
}

export interface PostsListResponse {
  items: Post[];
  total: number;
  page: number;
  size: number;
  has_next: boolean;
}

export interface CreatePostRequest {
  idea_bank_id?: string;
  title?: string;
  content: string;
  platform?: string;
  topics?: string[];
  recommendation_score?: number;
  status?: string;
}

export interface UpdatePostRequest {
  title?: string;
  content?: string;
  platform?: string;
  topics?: string[];
  recommendation_score?: number;
  status?: string;
  scheduled_at?: string;
}

export interface PostFeedbackRequest {
  feedback_type: "positive" | "negative";
  comment?: string;
}

export interface GetPostsParams {
  platform?: string;
  status?: string[];
  after_date?: string;
  before_date?: string;
  page?: number;
  size?: number;
  order_by?: string;
  order_direction?: "asc" | "desc";
}

class PostsAPI {
  /**
   * Get posts with filtering and pagination
   */
  async getPosts(params: GetPostsParams = {}): Promise<PostsListResponse> {
    const searchParams = new URLSearchParams();

    if (params.platform) searchParams.append("platform", params.platform);
    if (params.status) {
      params.status.forEach((s) => searchParams.append("status", s));
    }
    if (params.after_date) searchParams.append("after_date", params.after_date);
    if (params.before_date)
      searchParams.append("before_date", params.before_date);
    if (params.page) searchParams.append("page", params.page.toString());
    if (params.size) searchParams.append("size", params.size.toString());
    if (params.order_by) searchParams.append("order_by", params.order_by);
    if (params.order_direction)
      searchParams.append("order_direction", params.order_direction);

    const queryString = searchParams.toString();
    const url = `/posts/${queryString ? `?${queryString}` : ""}`;

    const response = await apiClient.request<PostsListResponse>(url);
    return response;
  }

  /**
   * Get a specific post
   */
  async getPost(postId: string): Promise<Post> {
    const response = await apiClient.request<Post>(`/posts/${postId}`);
    return response;
  }

  /**
   * Create a new post
   */
  async createPost(data: CreatePostRequest): Promise<Post> {
    const response = await apiClient.request<Post>("/posts/", {
      method: "POST",
      body: JSON.stringify(data),
    });
    return response;
  }

  /**
   * Update a post
   */
  async updatePost(postId: string, data: UpdatePostRequest): Promise<Post> {
    const response = await apiClient.request<Post>(`/posts/${postId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
    return response;
  }

  /**
   * Delete a post
   */
  async deletePost(postId: string): Promise<void> {
    await apiClient.request<void>(`/posts/${postId}`, {
      method: "DELETE",
    });
  }

  /**
   * Mark a post as dismissed
   */
  async dismissPost(postId: string): Promise<Post> {
    const response = await apiClient.request<Post>(`/posts/${postId}/dismiss`, {
      method: "POST",
    });
    return response;
  }

  /**
   * Mark a post as posted
   */
  async markAsPosted(postId: string): Promise<Post> {
    const response = await apiClient.request<Post>(
      `/posts/${postId}/mark-posted`,
      {
        method: "POST",
      }
    );
    return response;
  }

  /**
   * Submit feedback for a post
   */
  async submitFeedback(
    postId: string,
    feedback: PostFeedbackRequest
  ): Promise<Post> {
    const response = await apiClient.request<Post>(
      `/posts/${postId}/feedback`,
      {
        method: "POST",
        body: JSON.stringify(feedback),
      }
    );
    return response;
  }

  /**
   * Schedule a post for publishing
   */
  async schedulePost(postId: string, scheduledAt: string): Promise<Post> {
    const response = await apiClient.request<Post>(
      `/posts/${postId}/schedule`,
      {
        method: "POST",
        body: JSON.stringify({ scheduled_at: scheduledAt }),
      }
    );
    return response;
  }

  /**
   * Remove a post from schedule
   */
  async unschedulePost(postId: string): Promise<Post> {
    const response = await apiClient.request<Post>(
      `/posts/${postId}/schedule`,
      {
        method: "DELETE",
      }
    );
    return response;
  }

  /**
   * Generate new post suggestions
   */
  async generatePosts(): Promise<{ message: string }> {
    const response = await apiClient.request<{ message: string }>(
      "/posts/generate-suggestions",
      {
        method: "POST",
      }
    );
    return response;
  }
}

export const postsApi = new PostsAPI();

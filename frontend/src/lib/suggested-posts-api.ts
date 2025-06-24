import { apiClient } from './api';

export interface SuggestedPost {
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
  created_at: string;
}

export interface SuggestedPostCreate {
  idea_bank_id?: string;
  title?: string;
  content: string;
  platform?: string;
  topics?: string[];
  recommendation_score?: number;
  status?: string;
}

export interface SuggestedPostUpdate {
  title?: string;
  content?: string;
  platform?: string;
  topics?: string[];
  recommendation_score?: number;
  status?: string;
}

export interface PostFeedback {
  feedback_type: 'positive' | 'negative';
  comment?: string;
}

export interface SuggestedPostListResponse {
  items: SuggestedPost[];
  total: number;
  page: number;
  size: number;
  has_next: boolean;
}

export interface SuggestedPostsFilters {
  platform?: string;
  status?: string[];
  page?: number;
  size?: number;
  order_by?: string;
  order_direction?: 'asc' | 'desc';
}

export const suggestedPostsApi = {
  /**
   * Get suggested posts with filtering and pagination
   */
  async getSuggestedPosts(filters?: SuggestedPostsFilters): Promise<SuggestedPostListResponse> {
    const params = new URLSearchParams();
    
    if (filters?.platform) {
      params.append('platform', filters.platform);
    }
    
    if (filters?.status) {
      filters.status.forEach(status => params.append('status', status));
    }
    
    if (filters?.page) {
      params.append('page', filters.page.toString());
    }
    
    if (filters?.size) {
      params.append('size', filters.size.toString());
    }
    
    if (filters?.order_by) {
      params.append('order_by', filters.order_by);
    }
    
    if (filters?.order_direction) {
      params.append('order_direction', filters.order_direction);
    }

    const queryString = params.toString();
    const url = `/suggested-posts/${queryString ? `?${queryString}` : ''}`;
    
    const response = await apiClient.request<SuggestedPostListResponse>(url);
    return response;
  },

  /**
   * Get a specific suggested post
   */
  async getSuggestedPost(postId: string): Promise<SuggestedPost> {
    const response = await apiClient.request<SuggestedPost>(`/suggested-posts/${postId}`);
    return response;
  },

  /**
   * Create a new suggested post
   */
  async createSuggestedPost(postData: SuggestedPostCreate): Promise<SuggestedPost> {
    const response = await apiClient.request<SuggestedPost>('/suggested-posts/', {
      method: 'POST',
      body: JSON.stringify(postData),
    });
    return response;
  },

  /**
   * Update a suggested post
   */
  async updateSuggestedPost(postId: string, updateData: SuggestedPostUpdate): Promise<SuggestedPost> {
    const response = await apiClient.request<SuggestedPost>(`/suggested-posts/${postId}`, {
      method: 'PUT',
      body: JSON.stringify(updateData),
    });
    return response;
  },

  /**
   * Delete a suggested post
   */
  async deleteSuggestedPost(postId: string): Promise<void> {
    await apiClient.request<void>(`/suggested-posts/${postId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Dismiss a suggested post
   */
  async dismissSuggestedPost(postId: string): Promise<SuggestedPost> {
    const response = await apiClient.request<SuggestedPost>(`/suggested-posts/${postId}/dismiss`, {
      method: 'POST',
    });
    return response;
  },

  /**
   * Mark a suggested post as posted
   */
  async markAsPosted(postId: string): Promise<SuggestedPost> {
    const response = await apiClient.request<SuggestedPost>(`/suggested-posts/${postId}/mark-posted`, {
      method: 'POST',
    });
    return response;
  },

  /**
   * Submit feedback for a suggested post
   */
  async submitFeedback(postId: string, feedback: PostFeedback): Promise<SuggestedPost> {
    const response = await apiClient.request<SuggestedPost>(`/suggested-posts/${postId}/feedback`, {
      method: 'POST',
      body: JSON.stringify(feedback),
    });
    return response;
  },
}; 
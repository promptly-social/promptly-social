import { apiClient } from './auth-api';

export interface IdeaBankData {
  type: 'article' | 'text';
  value: string;
  title?: string;
  time_sensitive: boolean;
  ai_suggested: boolean;
}

export interface IdeaBank {
  id: string;
  user_id: string;
  data: IdeaBankData;
  created_at: string;
  updated_at: string;
}

export interface IdeaBankCreate {
  data: IdeaBankData;
}

export interface IdeaBankUpdate {
  data: Partial<IdeaBankData>;
}

export interface IdeaBankListResponse {
  items: IdeaBank[];
  total: number;
  page: number;
  size: number;
  has_next: boolean;
}

export interface IdeaBankFilters {
  page?: number;
  size?: number;
  order_by?: string;
  order_direction?: 'asc' | 'desc';
  ai_suggested?: boolean;
  evergreen?: boolean;
  has_post?: boolean;
  post_status?: string[];
}

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
  updated_at: string;
}

export interface IdeaBankWithPost {
  idea_bank: IdeaBank;
  latest_post?: SuggestedPost;
}

export interface IdeaBankWithPostsResponse {
  items: IdeaBankWithPost[];
  total: number;
  page: number;
  size: number;
  has_next: boolean;
}

export const ideaBankApi = {
  /**
   * Get idea banks list with filtering and pagination
   */
  async list(filters?: IdeaBankFilters): Promise<IdeaBankListResponse> {
    const params = new URLSearchParams();
    
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

    if (filters?.ai_suggested !== undefined) {
      params.append('ai_suggested', filters.ai_suggested.toString());
    }

    if (filters?.evergreen !== undefined) {
      params.append('evergreen', filters.evergreen.toString());
    }

    if (filters?.has_post !== undefined) {
      params.append('has_post', filters.has_post.toString());
    }

    if (filters?.post_status) {
      filters.post_status.forEach(status => params.append('post_status', status));
    }

    const queryString = params.toString();
    const url = `/idea-banks/${queryString ? `?${queryString}` : ''}`;
    
    const response = await apiClient.request<IdeaBankListResponse>(url);
    return response;
  },

  /**
   * Get idea banks with their latest suggested posts
   */
  async listWithPosts(filters?: IdeaBankFilters): Promise<IdeaBankWithPostsResponse> {
    const params = new URLSearchParams();
    
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

    if (filters?.ai_suggested !== undefined) {
      params.append('ai_suggested', filters.ai_suggested.toString());
    }

    if (filters?.evergreen !== undefined) {
      params.append('evergreen', filters.evergreen.toString());
    }

    if (filters?.has_post !== undefined) {
      params.append('has_post', filters.has_post.toString());
    }

    if (filters?.post_status) {
      filters.post_status.forEach(status => params.append('post_status', status));
    }

    const queryString = params.toString();
    const url = `/idea-banks/with-posts${queryString ? `?${queryString}` : ''}`;
    
    const response = await apiClient.request<IdeaBankWithPostsResponse>(url);
    return response;
  },

  /**
   * Get a specific idea bank
   */
  async get(id: string): Promise<IdeaBank> {
    const response = await apiClient.request<IdeaBank>(`/idea-banks/${id}`);
    return response;
  },

  /**
   * Get a specific idea bank with its latest post
   */
  async getWithPost(id: string): Promise<{ idea_bank: IdeaBank; latest_post?: SuggestedPost }> {
    const response = await apiClient.request<{ idea_bank: IdeaBank; latest_post?: SuggestedPost }>(`/idea-banks/${id}/with-post`);
    return response;
  },

  /**
   * Create a new idea bank
   */
  async create(ideaBankData: IdeaBankCreate): Promise<IdeaBank> {
    const response = await apiClient.request<IdeaBank>('/idea-banks/', {
      method: 'POST',
      body: JSON.stringify(ideaBankData),
    });
    return response;
  },

  /**
   * Update an idea bank
   */
  async update(id: string, updateData: IdeaBankUpdate): Promise<IdeaBank> {
    const response = await apiClient.request<IdeaBank>(`/idea-banks/${id}`, {
      method: 'PUT',
      body: JSON.stringify(updateData),
    });
    return response;
  },

  /**
   * Delete an idea bank
   */
  async delete(id: string): Promise<void> {
    await apiClient.request<void>(`/idea-banks/${id}`, {
      method: 'DELETE',
    });
  },
}; 
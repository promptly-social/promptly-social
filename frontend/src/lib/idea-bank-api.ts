import { apiClient } from './api';

export interface IdeaBankData {
  type: 'substack' | 'text';
  value: string;
  title?: string;
  time_sensitive?: boolean;
  last_used_post_id?: string;
  ai_suggested?: boolean;
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
  data?: Partial<IdeaBankData>;
}

export interface IdeaBankListResponse {
  items: IdeaBank[];
  total: number;
  page: number;
  size: number;
  has_next: boolean;
}

export interface IdeaBankListParams {
  page?: number;
  size?: number;
  order_by?: string;
  order_direction?: 'asc' | 'desc';
}

// API functions
export const ideaBankApi = {
  // Get list of idea banks
  async list(params: IdeaBankListParams = {}): Promise<IdeaBankListResponse> {
    const searchParams = new URLSearchParams();
    
    if (params.page) searchParams.append('page', params.page.toString());
    if (params.size) searchParams.append('size', params.size.toString());
    if (params.order_by) searchParams.append('order_by', params.order_by);
    if (params.order_direction) searchParams.append('order_direction', params.order_direction);

    return await apiClient.request<IdeaBankListResponse>(`/idea-banks/?${searchParams.toString()}`, {
      method: 'GET',
    });
  },

  // Get a specific idea bank
  async get(id: string): Promise<IdeaBank> {
    return await apiClient.request<IdeaBank>(`/idea-banks/${id}`, {
      method: 'GET',
    });
  },

  // Create a new idea bank
  async create(data: IdeaBankCreate): Promise<IdeaBank> {
    return await apiClient.request<IdeaBank>('/idea-banks/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // Update an idea bank
  async update(id: string, data: IdeaBankUpdate): Promise<IdeaBank> {
    return await apiClient.request<IdeaBank>(`/idea-banks/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  // Delete an idea bank
  async delete(id: string): Promise<void> {
    await apiClient.request<void>(`/idea-banks/${id}`, {
      method: 'DELETE',
    });
  },
}; 
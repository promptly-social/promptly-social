import { apiClient } from './auth-api';

// Content Types - Updated to match backend schemas
export interface Content {
  id: string;
  user_id: string;
  title: string;
  original_input: string | null;
  content_type: string;
  status: string;
  generated_outline?: unknown;
  created_at: string;
  updated_at: string;
  publications?: Publication[];
}

export interface ContentCreate {
  title: string;
  original_input?: string;
  content_type: string;
  status?: string;
  generated_outline?: unknown;
}

export interface ContentUpdate {
  title?: string;
  status?: string;
  generated_outline?: unknown;
}

export interface ContentListResponse {
  items: Content[];
  total: number;
  page: number;
  size: number;
  has_next: boolean;
}

// Publication Types - New publication model
export interface Publication {
  id: string;
  content_id: string;
  platform: string;
  scheduled_date: string | null;
  published_date: string | null;
  publication_error: string | null;
  post_id: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface PublicationCreate {
  content_id: string;
  platform: string;
  scheduled_date?: string;
  status?: string;
}

export interface PublicationUpdate {
  scheduled_date?: string;
  published_date?: string;
  publication_error?: string;
  post_id?: string;
  status?: string;
}

// Content API - Updated with new endpoints
export const contentApi = {
  // New Content API (recommended)
  async getContent(params?: {
    status?: string[];
    content_type?: string;
    page?: number;
    size?: number;
    order_by?: string;
    order_direction?: 'asc' | 'desc';
  }): Promise<ContentListResponse> {
    const searchParams = new URLSearchParams();
    
    if (params?.status) {
      params.status.forEach(s => searchParams.append('status', s));
    }
    if (params?.content_type) searchParams.append('content_type', params.content_type);
    if (params?.page) searchParams.append('page', params.page.toString());
    if (params?.size) searchParams.append('size', params.size.toString());
    if (params?.order_by) searchParams.append('order_by', params.order_by);
    if (params?.order_direction) searchParams.append('order_direction', params.order_direction);

    return apiClient.request<ContentListResponse>(`/content/?${searchParams.toString()}`);
  },

  async getContentById(id: string): Promise<Content> {
    return apiClient.request<Content>(`/content/${id}`);
  },

  async createContent(data: ContentCreate): Promise<Content> {
    return apiClient.request<Content>('/content/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async updateContent(id: string, data: ContentUpdate): Promise<Content> {
    return apiClient.request<Content>(`/content/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  async deleteContent(id: string): Promise<void> {
    await apiClient.request<void>(`/content/${id}`, {
      method: 'DELETE',
    });
  },

  // Publication API
  async getContentPublications(contentId: string): Promise<Publication[]> {
    return apiClient.request<Publication[]>(`/content/${contentId}/publications`);
  },

  async createPublication(data: PublicationCreate): Promise<Publication> {
    return apiClient.request<Publication>('/content/publications', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async updatePublication(id: string, data: PublicationUpdate): Promise<Publication> {
    return apiClient.request<Publication>(`/content/publications/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  async deletePublication(id: string): Promise<void> {
    await apiClient.request<void>(`/content/publications/${id}`, {
      method: 'DELETE',
    });
  },
}; 
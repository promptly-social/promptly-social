import { apiClient } from './api';

// Types for API requests/responses
export interface ContentIdea {
  id: string;
  user_id: string;
  title: string;
  original_input: string | null;
  content_type: string;
  status: string;
  generated_outline?: unknown;
  scheduled_date: string | null;
  published_date: string | null;
  publication_error: string | null;
  linkedin_post_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ContentIdeaCreate {
  title: string;
  original_input?: string;
  content_type: string;
  status?: string;
  generated_outline?: unknown;
}

export interface ContentIdeaUpdate {
  title?: string;
  status?: string;
  scheduled_date?: string;
  published_date?: string;
  publication_error?: string;
  linkedin_post_id?: string;
}

export interface ContentIdeaListResponse {
  items: ContentIdea[];
  total: number;
  page: number;
  size: number;
  has_next: boolean;
}

export interface UserPreferences {
  id: string;
  user_id: string;
  topics_of_interest: string[];
  websites: string[];
  created_at: string;
  updated_at: string;
}

export interface UserPreferencesUpdate {
  topics_of_interest: string[];
  websites: string[];
}

export interface SocialConnection {
  id: string;
  user_id: string;
  platform: string;
  platform_username: string | null;
  connection_data?: unknown;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SocialConnectionUpdate {
  platform_username?: string;
  connection_data?: unknown;
  is_active?: boolean;
}

export interface PlatformAnalysisData {
  writing_style: {
    tone: string;
    complexity: string;
    avg_length: number;
    key_themes: string[];
  };
  topics: string[];
  posting_patterns: {
    frequency: string;
    best_times: string[];
  };
  engagement_insights: {
    high_performing_topics: string[];
    content_types: string[];
  };
}

export interface PlatformAnalysisResponse {
  analysis_data: PlatformAnalysisData | null;
  last_analyzed: string | null;
  is_connected: boolean;
}

export interface SubstackData {
  name: string;
  url: string;
  topics: string[];
  subscriber_count?: number;
  recent_posts?: Array<{
    title: string;
    url: string;
    published_date: string;
  }>;
}

export interface SubstackAnalysisResponse {
  substack_data: SubstackData[];
  is_connected: boolean;
  analyzed_at: string | null;
}

// Content Ideas API
export const contentApi = {
  // Content Ideas
  async getContentIdeas(params?: {
    status?: string[];
    content_type?: string;
    page?: number;
    size?: number;
    order_by?: string;
    order_direction?: 'asc' | 'desc';
  }): Promise<ContentIdeaListResponse> {
    const searchParams = new URLSearchParams();
    
    if (params?.status) {
      params.status.forEach(s => searchParams.append('status', s));
    }
    if (params?.content_type) searchParams.append('content_type', params.content_type);
    if (params?.page) searchParams.append('page', params.page.toString());
    if (params?.size) searchParams.append('size', params.size.toString());
    if (params?.order_by) searchParams.append('order_by', params.order_by);
    if (params?.order_direction) searchParams.append('order_direction', params.order_direction);

    return apiClient.request<ContentIdeaListResponse>(`/content/ideas?${searchParams.toString()}`);
  },

  async getContentIdea(id: string): Promise<ContentIdea> {
    return apiClient.request<ContentIdea>(`/content/ideas/${id}`);
  },

  async createContentIdea(data: ContentIdeaCreate): Promise<ContentIdea> {
    return apiClient.request<ContentIdea>('/content/ideas', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async updateContentIdea(id: string, data: ContentIdeaUpdate): Promise<ContentIdea> {
    return apiClient.request<ContentIdea>(`/content/ideas/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  async deleteContentIdea(id: string): Promise<void> {
    await apiClient.request<void>(`/content/ideas/${id}`, {
      method: 'DELETE',
    });
  },

  // User Preferences
  async getUserPreferences(): Promise<UserPreferences> {
    return apiClient.request<UserPreferences>('/content/preferences');
  },

  async updateUserPreferences(data: UserPreferencesUpdate): Promise<UserPreferences> {
    return apiClient.request<UserPreferences>('/content/preferences', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  // Social Connections
  async getSocialConnections(): Promise<SocialConnection[]> {
    return apiClient.request<SocialConnection[]>('/content/social-connections');
  },

  async getSocialConnection(platform: string): Promise<SocialConnection> {
    return apiClient.request<SocialConnection>(`/content/social-connections/${platform}`);
  },

  async updateSocialConnection(platform: string, data: SocialConnectionUpdate): Promise<SocialConnection> {
    return apiClient.request<SocialConnection>(`/content/social-connections/${platform}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  // Writing Style Analysis
  async getWritingStyleAnalysis(platform: string): Promise<PlatformAnalysisResponse> {
    return apiClient.request<PlatformAnalysisResponse>(`/content/writing-analysis/${platform}`);
  },

  async runWritingStyleAnalysis(platform: string): Promise<PlatformAnalysisResponse> {
    return apiClient.request<PlatformAnalysisResponse>(`/content/writing-analysis/${platform}`, {
      method: 'POST',
    });
  },

  // Substack Analysis
  async getSubstackAnalysis(): Promise<SubstackAnalysisResponse> {
    return apiClient.request<SubstackAnalysisResponse>('/content/substack-analysis');
  },

  async runSubstackAnalysis(): Promise<SubstackAnalysisResponse> {
    return apiClient.request<SubstackAnalysisResponse>('/content/substack-analysis', {
      method: 'POST',
    });
  },
}; 
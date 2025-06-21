import { makeAuthenticatedRequest } from './api-interceptor';

// Types for API requests/responses
export interface UserPreferences {
  id: string;
  user_id: string;
  topics_of_interest: string[];
  websites: string[];
  bio: string;
  created_at: string;
  updated_at: string;
}

export interface UserPreferencesUpdate {
  topics_of_interest?: string[];
  websites?: string[];
  bio?: string;
}

export interface SocialConnection {
  id: string;
  user_id: string;
  platform: string;
  platform_username: string | null;
  connection_data?: unknown;
  is_active: boolean;
  analysis_started_at?: string | null;
  analysis_completed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface SocialConnectionUpdate {
  platform_username?: string;
  connection_data?: unknown;
  is_active?: boolean;
}

export interface PlatformAnalysisResponse {
  analysis_data: string | null;
  last_analyzed: string | null;
  is_connected: boolean;
}

export interface WritingStyleAnalysisUpdate {
  analysis_data?: string;
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
  analysis_started_at?: string | null;
  analysis_completed_at?: string | null;
  is_analyzing?: boolean;
}

export interface LinkedInAuthResponse {
  authorization_url: string;
}

// Profile API
export const profileApi = {

  // User Preferences
  async getUserPreferences(): Promise<UserPreferences> {
    return makeAuthenticatedRequest<UserPreferences>('/profile/preferences');
  },

  async updateUserPreferences(data: UserPreferencesUpdate): Promise<UserPreferences> {
    return makeAuthenticatedRequest<UserPreferences>('/profile/preferences', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  // Social Connections
  async getSocialConnections(): Promise<SocialConnection[]> {
    return makeAuthenticatedRequest<SocialConnection[]>('/profile/social-connections');
  },

  async getSocialConnection(platform: string): Promise<SocialConnection> {
    return makeAuthenticatedRequest<SocialConnection>(`/profile/social-connections/${platform}`);
  },

  async updateSocialConnection(platform: string, data: SocialConnectionUpdate): Promise<SocialConnection> {
    return makeAuthenticatedRequest<SocialConnection>(`/profile/social-connections/${platform}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  // Writing Style Analysis
  async getWritingStyleAnalysis(platform: string): Promise<PlatformAnalysisResponse> {
    return makeAuthenticatedRequest<PlatformAnalysisResponse>(`/profile/writing-analysis/${platform}`);
  },

  async runWritingStyleAnalysis(platform: string): Promise<PlatformAnalysisResponse> {
    return makeAuthenticatedRequest<PlatformAnalysisResponse>(`/profile/writing-analysis/${platform}`, {
      method: 'POST',
    });
  },

  async updateWritingStyleAnalysis(platform: string, data: WritingStyleAnalysisUpdate): Promise<PlatformAnalysisResponse> {
    return makeAuthenticatedRequest<PlatformAnalysisResponse>(`/profile/writing-analysis/${platform}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  // Substack Analysis
  async getSubstackAnalysis(): Promise<SubstackAnalysisResponse> {
    return makeAuthenticatedRequest<SubstackAnalysisResponse>('/profile/substack-analysis');
  },

  async runSubstackAnalysis(): Promise<SubstackAnalysisResponse> {
    return makeAuthenticatedRequest<SubstackAnalysisResponse>('/profile/analyze-substack', {
      method: 'POST',
    });
  },

  // LinkedIn Integration
  async linkedinAuthorize(): Promise<LinkedInAuthResponse> {
    return makeAuthenticatedRequest<LinkedInAuthResponse>('/profile/linkedin/authorize');
  },

  async linkedinCallback(code: string, state: string): Promise<SocialConnection> {
    return makeAuthenticatedRequest<SocialConnection>(`/profile/linkedin/callback?code=${code}&state=${state}`);
  },

  async shareOnLinkedIn(text: string): Promise<{ share_id: string }> {
    return makeAuthenticatedRequest<{ share_id: string }>('/profile/linkedin/share', {
      method: 'POST',
      body: JSON.stringify({ text }),
    });
  },
}; 
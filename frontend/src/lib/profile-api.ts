import { apiClient } from "./auth-api";

// Types for API requests/responses
export interface ContentStrategy {
  id: string;
  user_id: string;
  platform: string;
  strategy: string;
  created_at: string;
  updated_at: string;
}

export interface UserPreferences {
  id: string;
  user_id: string;
  topics_of_interest: string[];
  websites: string[];
  substacks: string[];
  bio: string;
  preferred_posting_time: string | null;
  timezone: string | null;
  image_generation_style: string | null;
  content_strategies: ContentStrategy[];
  created_at: string;
  updated_at: string;
}

export interface UserPreferencesUpdate {
  topics_of_interest?: string[];
  websites?: string[];
  substacks?: string[];
  bio?: string;
  preferred_posting_time?: string | null;
  timezone?: string | null;
  image_generation_style?: string | null;
  content_strategies?: { [platform: string]: string };
}

export interface SocialConnection {
  id: string;
  user_id: string;
  platform: string;
  platform_username: string | null;
  // All authentication data is now stored in connection_data JSON field
  // Structure varies by auth method:
  // - Native LinkedIn: {"auth_method": "native", "access_token": "...", "refresh_token": "...", "expires_at": "...", "scope": "...", "linkedin_user_id": "...", "email": "..."}
  connection_data?: {
    auth_method?: "native";
    // Native LinkedIn fields
    access_token?: string;
    refresh_token?: string;
    expires_at?: string;
    scope?: string;
    linkedin_user_id?: string;
    email?: string;
    avatar_url?: string;
    // Analytics-specific fields
    analytics_access_token?: string;
    analytics_refresh_token?: string;
    analytics_expires_at?: string;
    analytics_scope?: string;
  };
  is_active: boolean;
  analysis_started_at?: string | null;
  analysis_completed_at?: string | null;
  analysis_status?:
    | "not_started"
    | "in_progress"
    | "error"
    | "completed"
    | null;
  created_at: string;
  updated_at: string;
}

export interface SocialConnectionUpdate {
  platform_username?: string;
  connection_data?: unknown;
  is_active?: boolean;
  access_token?: string | null;
  refresh_token?: string | null;
  expires_at?: string | null;
}

export interface PlatformAnalysisResponse {
  analysis_data: string | null;
  last_analyzed: string | null;
  is_connected: boolean;
}

export interface WritingStyleAnalysisUpdate {
  analysis_data?: string;
}

export interface SubstackAnalysisResponse {
  is_connected: boolean;
  analyzed_at: string | null;
  analysis_started_at?: string | null;
  analysis_completed_at?: string | null;
  is_analyzing?: boolean;
}

export interface LinkedInAuthResponse {
  authorization_url: string;
}

export interface LinkedInAuthInfo {
  auth_method: "native";
  provider: string;
  configured: boolean;
}

export interface LinkedInConnectionStatus {
  connected: boolean;
  auth_method?: string;
  account_id?: string;
  error?: string;
}

// Profile API
export const profileApi = {
  // User Preferences
  async getUserPreferences(): Promise<UserPreferences> {
    return apiClient.request<UserPreferences>("/profile/preferences");
  },

  async updateUserPreferences(
    data: UserPreferencesUpdate
  ): Promise<UserPreferences> {
    return apiClient.request<UserPreferences>("/profile/preferences", {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  // Social Connections
  async getSocialConnections(): Promise<SocialConnection[]> {
    return apiClient.request<SocialConnection[]>("/profile/social-connections");
  },

  async getSocialConnection(platform: string): Promise<SocialConnection> {
    return apiClient.request<SocialConnection>(
      `/profile/social-connections/${platform}`
    );
  },

  async updateSocialConnection(
    platform: string,
    data: SocialConnectionUpdate
  ): Promise<SocialConnection> {
    return apiClient.request<SocialConnection>(
      `/profile/social-connections/${platform}`,
      {
        method: "PUT",
        body: JSON.stringify(data),
      }
    );
  },

  // Writing Style Analysis
  async getWritingStyleAnalysis(
    platform?: string
  ): Promise<PlatformAnalysisResponse> {
    const url = platform
      ? `/profile/writing-analysis/${platform}`
      : "/profile/writing-analysis";
    return apiClient.request<PlatformAnalysisResponse>(url);
  },

  async runWritingStyleAnalysis(
    source: string,
    data?: Record<string, unknown>
  ): Promise<PlatformAnalysisResponse> {
    return apiClient.request<PlatformAnalysisResponse>(
      `/profile/writing-analysis/${source}`,
      {
        method: "POST",
        body: data ? JSON.stringify(data) : undefined,
      }
    );
  },

  async updateWritingStyleAnalysis(
    data: WritingStyleAnalysisUpdate,
    platform?: string
  ): Promise<PlatformAnalysisResponse> {
    const url = platform
      ? `/profile/writing-analysis/${platform}`
      : "/profile/writing-analysis";
    return apiClient.request<PlatformAnalysisResponse>(url, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  // Substack Analysis
  async getSubstackAnalysis(): Promise<SubstackAnalysisResponse> {
    return apiClient.request<SubstackAnalysisResponse>(
      "/profile/substack-analysis"
    );
  },

  async runSubstackAnalysis(
    contentToAnalyze: string[]
  ): Promise<SubstackAnalysisResponse> {
    return apiClient.request<SubstackAnalysisResponse>(
      "/profile/analyze-substack",
      {
        method: "POST",
        body: JSON.stringify({ content_to_analyze: contentToAnalyze }),
      }
    );
  },

  async checkLinkedInConnectionStatus(
    state: string
  ): Promise<LinkedInConnectionStatus> {
    return apiClient.request<LinkedInConnectionStatus>(
      `/profile/linkedin/connection-status/${state}`
    );
  },

  async shareOnLinkedIn(text: string): Promise<{ share_id: string }> {
    return apiClient.request<{ share_id: string }>("/profile/linkedin/share", {
      method: "POST",
      body: JSON.stringify({ text }),
    });
  },

  // LinkedIn Analysis
  async runLinkedInAnalysis(
    contentToAnalyze: string[]
  ): Promise<SubstackAnalysisResponse> {
    return apiClient.request<SubstackAnalysisResponse>(
      "/profile/analyze-linkedin",
      {
        method: "POST",
        body: JSON.stringify({ content_to_analyze: contentToAnalyze }),
      }
    );
  },
};

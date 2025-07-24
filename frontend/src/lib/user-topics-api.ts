/**
 * User Topics API client
 */

import { apiClient } from "./auth-api";

export interface UserTopic {
  id: string;
  user_id: string;
  topic: string;
  color: string;
  created_at: string;
  updated_at: string;
}

export interface UserTopicsListResponse {
  topics: UserTopic[];
  total: number;
}

export interface UserTopicCreate {
  topic: string;
  color?: string;
}

export interface UserTopicUpdate {
  topic?: string;
  color?: string;
}

export interface BulkTopicCreateRequest {
  topics: string[];
}

export interface TopicColorMap {
  topic: string;
  color: string;
}

export interface TopicColorsResponse {
  topic_colors: TopicColorMap[];
}

class UserTopicsAPI {
  /**
   * Get all topics for the current user
   */
  async getUserTopics(): Promise<UserTopicsListResponse> {
    const response = await apiClient.request<UserTopicsListResponse>("/user-topics/");
    return response;
  }

  /**
   * Get topic-color mapping for the current user
   */
  async getTopicColors(): Promise<TopicColorsResponse> {
    const response = await apiClient.request<TopicColorsResponse>("/user-topics/colors");
    return response;
  }

  /**
   * Get a specific topic for the current user
   */
  async getUserTopic(topicId: string): Promise<UserTopic> {
    const response = await apiClient.request<UserTopic>(`/user-topics/${topicId}`);
    return response;
  }

  /**
   * Create a new topic for the current user
   */
  async createUserTopic(data: UserTopicCreate): Promise<UserTopic> {
    const response = await apiClient.request<UserTopic>("/user-topics/", {
      method: "POST",
      body: JSON.stringify(data),
    });
    return response;
  }

  /**
   * Bulk create topics for the current user
   */
  async bulkCreateTopics(data: BulkTopicCreateRequest): Promise<UserTopic[]> {
    const response = await apiClient.request<UserTopic[]>("/user-topics/bulk", {
      method: "POST",
      body: JSON.stringify(data),
    });
    return response;
  }

  /**
   * Sync topics from user's posts to create missing UserTopic entries
   */
  async syncTopicsFromPosts(): Promise<UserTopic[]> {
    const response = await apiClient.request<UserTopic[]>("/user-topics/sync-from-posts", {
      method: "POST",
    });
    return response;
  }

  /**
   * Update a topic for the current user
   */
  async updateUserTopic(topicId: string, data: UserTopicUpdate): Promise<UserTopic> {
    const response = await apiClient.request<UserTopic>(`/user-topics/${topicId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
    return response;
  }

  /**
   * Delete a topic for the current user
   */
  async deleteUserTopic(topicId: string): Promise<void> {
    await apiClient.request<void>(`/user-topics/${topicId}`, {
      method: "DELETE",
    });
  }
}

export const userTopicsApi = new UserTopicsAPI();

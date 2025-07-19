/**
 * API service for onboarding functionality
 */
import { apiClient } from "../auth-api";

import type {
  OnboardingProgress,
  OnboardingStepUpdate,
  OnboardingSkip,
  OnboardingUpdate,
} from "../../types/onboarding";

export const onboardingApi = {
  /**
   * Get current user's onboarding progress
   */
  getProgress: async (): Promise<OnboardingProgress> => {
    return apiClient.request<OnboardingProgress>("/onboarding/");
  },

  /**
   * Update a specific onboarding step
   */
  updateStep: async (
    stepUpdate: OnboardingStepUpdate
  ): Promise<OnboardingProgress> => {
    return apiClient.request<OnboardingProgress>("/onboarding/step", {
      method: "PUT",
      body: JSON.stringify(stepUpdate),
    });
  },

  /**
   * Skip the entire onboarding process
   */
  skipOnboarding: async (
    skipData: OnboardingSkip = {}
  ): Promise<OnboardingProgress> => {
    return apiClient.request<OnboardingProgress>("/onboarding/skip", {
      method: "POST",
      body: JSON.stringify(skipData),
    });
  },

  /**
   * Update onboarding progress with multiple fields
   */
  updateProgress: async (
    updateData: OnboardingUpdate
  ): Promise<OnboardingProgress> => {
    return apiClient.request<OnboardingProgress>("/onboarding/", {
      method: "PUT",
      body: JSON.stringify(updateData),
    });
  },

  /**
   * Mark onboarding as completed
   */
  completeOnboarding: async (): Promise<OnboardingProgress> => {
    return apiClient.request<OnboardingProgress>("/onboarding/complete", {
      method: "POST",
    });
  },

  /**
   * Reset onboarding progress to start over
   */
  resetOnboarding: async (): Promise<OnboardingProgress> => {
    return apiClient.request<OnboardingProgress>("/onboarding/reset", {
      method: "POST",
    });
  },

  /**
   * Delete onboarding progress
   */
  deleteOnboarding: async (): Promise<{ message: string }> => {
    return apiClient.request<{ message: string }>("/onboarding/", {
      method: "DELETE",
    });
  },
};

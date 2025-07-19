/**
 * Custom hook for managing onboarding state
 */

import { useState, useEffect, useCallback } from "react";
import { onboardingApi } from "../lib/api/onboarding-api";
import type { OnboardingProgress, OnboardingStep } from "../types/onboarding";
import { ONBOARDING_STEPS } from "../types/onboarding";
import { useAuth } from "../contexts/AuthContext";

export const useOnboarding = () => {
  const [progress, setProgress] = useState<OnboardingProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user, loading: authLoading } = useAuth();

  // Fetch onboarding progress
  const fetchProgress = useCallback(async () => {
    // Don't fetch if user is not authenticated
    if (!user) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const data = await onboardingApi.getProgress();
      setProgress(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to fetch onboarding progress"
      );
    } finally {
      setLoading(false);
    }
  }, [user]);

  // Update a specific step
  const updateStep = useCallback(
    async (step: number, completed: boolean = true) => {
      try {
        setError(null);
        const data = await onboardingApi.updateStep({ step, completed });
        setProgress(data);
        return data;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to update step";
        setError(errorMessage);
        throw new Error(errorMessage);
      }
    },
    []
  );

  // Skip onboarding
  const skipOnboarding = useCallback(async (notes?: string) => {
    try {
      setError(null);
      const data = await onboardingApi.skipOnboarding({ notes });
      setProgress(data);
      return data;
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to skip onboarding";
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, []);


  // Complete onboarding
  const completeOnboarding = useCallback(async () => {
    try {
      setError(null);
      const data = await onboardingApi.completeOnboarding();
      setProgress(data);
      return data;
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to complete onboarding";
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, []);

  // Reset onboarding
  const resetOnboarding = useCallback(async () => {
    try {
      setError(null);
      const data = await onboardingApi.resetOnboarding();
      setProgress(data);
      return data;
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to reset onboarding";
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  }, []);

  // Get enriched steps with completion status
  const getStepsWithStatus = useCallback((): OnboardingStep[] => {
    if (!progress) return [];

    return ONBOARDING_STEPS.map((step) => ({
      ...step,
      isCompleted: getStepCompletionStatus(step.id, progress),
      isActive: step.id === progress.current_step,
    }));
  }, [progress]);

  // Helper function to get step completion status
  const getStepCompletionStatus = (
    stepId: number,
    progress: OnboardingProgress
  ): boolean => {
    switch (stepId) {
      case 1:
        return progress.step_profile_completed;
      case 2:
        return progress.step_content_preferences_completed;
      case 3:
        return progress.step_settings_completed;
      case 4:
        return progress.step_my_posts_completed;
      case 5:
        return progress.step_content_ideas_completed;
      case 6:
        return progress.step_posting_schedule_completed;
      default:
        return false;
    }
  };

  // Check if onboarding should be shown
  const shouldShowOnboarding = useCallback((): boolean => {
    if (!progress) return false;
    return !progress.is_completed && !progress.is_skipped;
  }, [progress]);

  // Get current step info
  const getCurrentStep = useCallback((): OnboardingStep | null => {
    if (!progress) return null;

    const stepConfig = ONBOARDING_STEPS.find(
      (s) => s.id === progress.current_step
    );
    if (!stepConfig) return null;

    return {
      ...stepConfig,
      isCompleted: getStepCompletionStatus(stepConfig.id, progress),
      isActive: true,
    };
  }, [progress]);

  // Initialize on mount, but only after auth is loaded
  useEffect(() => {
    if (!authLoading) {
      fetchProgress();
    }
  }, [fetchProgress, authLoading]);

  return {
    progress,
    loading,
    error,
    updateStep,
    skipOnboarding,
    completeOnboarding,
    resetOnboarding,
    getStepsWithStatus,
    shouldShowOnboarding,
    getCurrentStep,
    refetch: fetchProgress,
  };
};

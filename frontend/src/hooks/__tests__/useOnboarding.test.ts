/**
 * Tests for useOnboarding hook
 */

import { renderHook, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
import { useOnboarding } from "../useOnboarding";
import { onboardingApi } from "../../lib/api/onboarding-api";
import type { OnboardingProgress } from "../../types/onboarding";

// Mock the API
vi.mock("../../lib/api/onboarding", () => ({
  onboardingApi: {
    getProgress: vi.fn(),
    updateStep: vi.fn(),
    skipOnboarding: vi.fn(),
    resetOnboarding: vi.fn(),
    updateProgress: vi.fn(),
    deleteOnboarding: vi.fn(),
  },
}));

// Mock react-router-dom
vi.mock("react-router-dom", () => ({
  useNavigate: () => vi.fn(),
}));

const mockProgress: OnboardingProgress = {
  id: "test-id",
  user_id: "test-user",
  is_completed: false,
  is_skipped: false,
  step_profile_completed: false,
  step_content_preferences_completed: false,
  step_settings_completed: false,
  step_my_posts_completed: false,
  step_content_ideas_completed: false,
  step_posting_schedule_completed: false,
  current_step: 1,
  progress_percentage: 0,
  created_at: "2024-01-01T00:00:00Z",
};

describe("useOnboarding", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should fetch onboarding progress on mount", async () => {
    vi.mocked(onboardingApi.getProgress).mockResolvedValue(mockProgress);

    const { result } = renderHook(() => useOnboarding());

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.progress).toEqual(mockProgress);
    expect(onboardingApi.getProgress).toHaveBeenCalledTimes(1);
  });

  it("should handle API errors gracefully", async () => {
    const errorMessage = "Failed to fetch progress";
    vi.mocked(onboardingApi.getProgress).mockRejectedValue(
      new Error(errorMessage)
    );

    const { result } = renderHook(() => useOnboarding());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe(errorMessage);
    expect(result.current.progress).toBeNull();
  });

  it("should update step successfully", async () => {
    const updatedProgress = {
      ...mockProgress,
      step_profile_completed: true,
      current_step: 2,
    };
    vi.mocked(onboardingApi.getProgress).mockResolvedValue(mockProgress);
    vi.mocked(onboardingApi.updateStep).mockResolvedValue(updatedProgress);

    const { result } = renderHook(() => useOnboarding());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await result.current.updateStep(1, true);

    expect(onboardingApi.updateStep).toHaveBeenCalledWith({
      step: 1,
      completed: true,
    });
    expect(result.current.progress).toEqual(updatedProgress);
  });

  it("should skip onboarding successfully", async () => {
    const skippedProgress = { ...mockProgress, is_skipped: true };
    vi.mocked(onboardingApi.getProgress).mockResolvedValue(mockProgress);
    vi.mocked(onboardingApi.skipOnboarding).mockResolvedValue(skippedProgress);

    const { result } = renderHook(() => useOnboarding());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await result.current.skipOnboarding("User chose to skip");

    expect(onboardingApi.skipOnboarding).toHaveBeenCalledWith({
      notes: "User chose to skip",
    });
    expect(result.current.progress).toEqual(skippedProgress);
  });

  it("should reset onboarding successfully", async () => {
    const resetProgress = { ...mockProgress, current_step: 1 };
    vi.mocked(onboardingApi.getProgress).mockResolvedValue(mockProgress);
    vi.mocked(onboardingApi.resetOnboarding).mockResolvedValue(resetProgress);

    const { result } = renderHook(() => useOnboarding());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await result.current.resetOnboarding();

    expect(onboardingApi.resetOnboarding).toHaveBeenCalledTimes(1);
    expect(result.current.progress).toEqual(resetProgress);
  });

  it("should determine if onboarding should be shown", async () => {
    vi.mocked(onboardingApi.getProgress).mockResolvedValue(mockProgress);

    const { result } = renderHook(() => useOnboarding());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.shouldShowOnboarding()).toBe(true);

    // Test with completed onboarding
    const completedProgress = { ...mockProgress, is_completed: true };
    vi.mocked(onboardingApi.getProgress).mockResolvedValue(completedProgress);

    await result.current.refetch();

    expect(result.current.shouldShowOnboarding()).toBe(false);
  });

  it("should get steps with correct status", async () => {
    const progressWithSteps = {
      ...mockProgress,
      step_profile_completed: true,
      step_content_preferences_completed: true,
      current_step: 3,
    };
    vi.mocked(onboardingApi.getProgress).mockResolvedValue(progressWithSteps);

    const { result } = renderHook(() => useOnboarding());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    const steps = result.current.getStepsWithStatus();

    expect(steps).toHaveLength(6);
    expect(steps[0].isCompleted).toBe(true); // Profile step
    expect(steps[1].isCompleted).toBe(true); // Content preferences step
    expect(steps[2].isActive).toBe(true); // Settings step (current)
    expect(steps[3].isCompleted).toBe(false); // My posts step
  });

  it("should get current step info", async () => {
    const progressWithCurrentStep = { ...mockProgress, current_step: 2 };
    vi.mocked(onboardingApi.getProgress).mockResolvedValue(
      progressWithCurrentStep
    );

    const { result } = renderHook(() => useOnboarding());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    const currentStep = result.current.getCurrentStep();

    expect(currentStep).toBeDefined();
    expect(currentStep?.id).toBe(2);
    expect(currentStep?.title).toBe("Content Preferences");
    expect(currentStep?.isActive).toBe(true);
  });
});

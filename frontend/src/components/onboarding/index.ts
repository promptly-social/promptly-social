/**
 * Onboarding Components and Hooks
 */
export { OnboardingProvider, useOnboardingContext } from "./OnboardingProvider";
export { OnboardingModal } from "./OnboardingModal";
export { OnboardingProgress } from "./OnboardingProgress";
export { OnboardingBanner } from "./OnboardingBanner";
export { OnboardingWelcome } from "./OnboardingWelcome";
// Hooks
export { useOnboarding } from "@/hooks/useOnboarding";

// Types
export type {
  OnboardingStep,
  OnboardingProgress as OnboardingProgressType,
  OnboardingStepUpdate,
  OnboardingSkip,
  OnboardingUpdate,
} from "@/types/onboarding";
export { ONBOARDING_STEPS } from "@/types/onboarding";

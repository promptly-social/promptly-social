/**
 * Onboarding Components and Hooks
 */
export { OnboardingProvider, useOnboardingContext } from "./OnboardingProvider";
export { OnboardingModal } from "./OnboardingModal";
// Hooks
export { useOnboarding } from "@/hooks/useOnboarding";

// Types
export type {
  OnboardingStep,
  OnboardingStepUpdate,
  OnboardingSkip,
  OnboardingUpdate,
} from "@/types/onboarding";
export { ONBOARDING_STEPS } from "@/types/onboarding";

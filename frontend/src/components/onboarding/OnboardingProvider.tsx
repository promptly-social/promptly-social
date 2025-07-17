/**
 * Onboarding Provider Component
 * 
 * Main provider that manages onboarding state and provides onboarding
 * functionality throughout the application.
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useOnboarding } from '../../hooks/useOnboarding';
import { OnboardingModal } from './OnboardingModal';
import { OnboardingProgress } from './OnboardingProgress';
import type { OnboardingProgress as OnboardingProgressType } from '../../types/onboarding';

interface OnboardingContextType {
  progress: OnboardingProgressType | null;
  loading: boolean;
  error: string | null;
  showOnboarding: boolean;
  showModal: boolean;
  showProgress: boolean;
  setShowModal: (show: boolean) => void;
  setShowProgress: (show: boolean) => void;
  skipOnboarding: () => Promise<void>;
  resetOnboarding: () => Promise<void>;
  updateStep: (step: number, completed?: boolean) => Promise<void>;
}

const OnboardingContext = createContext<OnboardingContextType | undefined>(undefined);

export const useOnboardingContext = () => {
  const context = useContext(OnboardingContext);
  if (context === undefined) {
    throw new Error('useOnboardingContext must be used within an OnboardingProvider');
  }
  return context;
};

interface OnboardingProviderProps {
  children: React.ReactNode;
  autoShowModal?: boolean;
  showProgressIndicator?: boolean;
}

export const OnboardingProvider: React.FC<OnboardingProviderProps> = ({
  children,
  autoShowModal = true,
  showProgressIndicator = true
}) => {
  const {
    progress,
    loading,
    error,
    updateStep,
    skipOnboarding: skipOnboardingHook,
    resetOnboarding: resetOnboardingHook,
    shouldShowOnboarding
  } = useOnboarding();

  const [showModal, setShowModal] = useState(false);
  const [showProgress, setShowProgress] = useState(showProgressIndicator);
  const [hasShownInitialModal, setHasShownInitialModal] = useState(false);

  // Auto-show modal for new users
  useEffect(() => {
    if (
      autoShowModal &&
      !loading &&
      !hasShownInitialModal &&
      shouldShowOnboarding() &&
      progress &&
      progress.current_step === 1 &&
      !progress.step_profile_completed
    ) {
      setShowModal(true);
      setHasShownInitialModal(true);
    }
  }, [autoShowModal, loading, hasShownInitialModal, shouldShowOnboarding, progress]);

  const handleSkipOnboarding = async () => {
    try {
      await skipOnboardingHook();
      setShowModal(false);
    } catch (error) {
      console.error('Failed to skip onboarding:', error);
    }
  };

  const handleResetOnboarding = async () => {
    try {
      await resetOnboardingHook();
      setHasShownInitialModal(false);
    } catch (error) {
      console.error('Failed to reset onboarding:', error);
    }
  };

  const handleUpdateStep = async (step: number, completed: boolean = true) => {
    try {
      await updateStep(step, completed);
    } catch (error) {
      console.error('Failed to update step:', error);
    }
  };

  const contextValue: OnboardingContextType = {
    progress,
    loading,
    error,
    showOnboarding: shouldShowOnboarding(),
    showModal,
    showProgress,
    setShowModal,
    setShowProgress,
    skipOnboarding: handleSkipOnboarding,
    resetOnboarding: handleResetOnboarding,
    updateStep: handleUpdateStep
  };

  return (
    <OnboardingContext.Provider value={contextValue}>
      {children}
      
      {/* Onboarding Modal */}
      <OnboardingModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onSkip={handleSkipOnboarding}
      />
      
      {/* Progress Indicator */}
      {showProgress && shouldShowOnboarding() && (
        <div className="fixed bottom-4 right-4 z-40">
          <OnboardingProgress
            compact={true}
            className="bg-white shadow-lg border"
          />
        </div>
      )}
    </OnboardingContext.Provider>
  );
};

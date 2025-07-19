/**
 * Onboarding Provider Component
 * 
 * Main provider that manages onboarding state and provides onboarding
 * functionality throughout the application.
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useOnboarding } from '../../hooks/useOnboarding';
import { OnboardingModal } from './OnboardingModal';
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
  completeOnboarding: () => Promise<void>;
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
  const location = useLocation();
  const {
    progress,
    loading,
    error,
    updateStep,
    skipOnboarding: skipOnboardingHook,
    completeOnboarding: completeOnboardingHook,
    resetOnboarding: resetOnboardingHook,
    shouldShowOnboarding,
    getStepsWithStatus
  } = useOnboarding();

  const [showModal, setShowModal] = useState(false);
  const [showProgress, setShowProgress] = useState(showProgressIndicator);
  const [hasShownInitialModal, setHasShownInitialModal] = useState(false);

  // Auto-show modal for new users (only on protected routes where onboarding is needed)
  useEffect(() => {
    const allowedPaths = ['/my-posts', '/content-ideas', '/posting-schedule', '/profile', '/content-preferences', '/settings'];
    
    if (
      autoShowModal &&
      !loading &&
      !hasShownInitialModal &&
      shouldShowOnboarding() &&
      progress &&
      allowedPaths.includes(location.pathname)
    ) {
      setShowModal(true);
      setHasShownInitialModal(true);
    }
  }, [autoShowModal, loading, hasShownInitialModal, shouldShowOnboarding, progress, location.pathname]);

  const handleSkipOnboarding = async () => {
    try {
      await skipOnboardingHook();
      setShowModal(false);
    } catch (error) {
      console.error('Failed to skip onboarding:', error);
    }
  };

  const handleCompleteOnboarding = async () => {
    try {
      await completeOnboardingHook();
      setShowModal(false);
    } catch (error) {
      console.error('Failed to complete onboarding:', error);
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
    completeOnboarding: handleCompleteOnboarding,
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
        onComplete={handleCompleteOnboarding}
        progress={progress}
        loading={loading}
        getStepsWithStatus={getStepsWithStatus}
        updateStep={updateStep}
      />
      
    </OnboardingContext.Provider>
  );
};

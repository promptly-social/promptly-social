/**
 * Onboarding Banner Component
 * 
 * Shows contextual onboarding guidance on specific pages
 * with step-specific instructions and highlights.
 */

import React from 'react';
import { X, ArrowRight, Lightbulb } from 'lucide-react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { useOnboarding } from '../../hooks/useOnboarding';

interface OnboardingBannerProps {
  stepId: number;
  onDismiss?: () => void;
  className?: string;
}

export const OnboardingBanner: React.FC<OnboardingBannerProps> = ({
  stepId,
  onDismiss,
  className = ''
}) => {
  const { progress, getStepsWithStatus, updateStep, goToNextStep } = useOnboarding();
  const steps = getStepsWithStatus();
  const currentStep = steps.find(s => s.id === stepId);

  // Debug logging
  console.log(`[OnboardingBanner] Step ${stepId}:`, {
    progress: progress ? {
      is_completed: progress.is_completed,
      is_skipped: progress.is_skipped,
      current_step: progress.current_step,
      step_posting_schedule_completed: progress.step_posting_schedule_completed
    } : null,
    currentStep: currentStep ? { id: currentStep.id, isCompleted: currentStep.isCompleted } : null
  });

  // Don't show banner if onboarding is completed/skipped or step doesn't match
  if (!progress || progress.is_completed || progress.is_skipped || !currentStep) {
    console.log(`[OnboardingBanner] Hiding banner for step ${stepId}:`, {
      noProgress: !progress,
      isCompleted: progress?.is_completed,
      isSkipped: progress?.is_skipped,
      noCurrentStep: !currentStep
    });
    return null;
  }

  // Only show banner for current or upcoming steps
  if (stepId < progress.current_step && currentStep.isCompleted) {
    return null;
  }

  const handleCompleteStep = async () => {
    try {
      await updateStep(stepId, true);
      // Auto-navigate to next step after a short delay
      setTimeout(() => {
        goToNextStep();
      }, 1000);
    } catch (error) {
      console.error('Failed to complete step:', error);
    }
  };

  return (
    <div className={`bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4 mb-6 ${className}`}>
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0">
          <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
            <Lightbulb className="h-4 w-4 text-blue-600" />
          </div>
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <Badge variant="outline" className="text-blue-700 border-blue-300">
              Step {stepId} of 6
            </Badge>
            <span className="text-sm font-medium text-blue-900">
              {currentStep.title}
            </span>
          </div>
          
          <p className="text-blue-800 text-sm mb-3">
            {currentStep.description}
          </p>

          {/* Step-specific highlights */}
          {currentStep.highlights && currentStep.highlights.length > 0 && (
            <div className="mb-3">
              <ul className="space-y-1">
                {currentStep.highlights.slice(0, 3).map((highlight, index) => (
                  <li key={index} className="text-blue-700 text-xs flex items-start gap-2">
                    <span className="text-blue-500 mt-1">•</span>
                    <span>{highlight}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Special step-specific content */}
          {stepId === 1 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded p-2 mb-3">
              <p className="text-yellow-800 text-xs">
                💡 <strong>Tip:</strong> Click the "Analyze" button after adding your LinkedIn handle. 
                The analysis takes up to 5 minutes and will help personalize your content.
              </p>
            </div>
          )}

          {stepId === 3 && (
            <div className="bg-green-50 border border-green-200 rounded p-2 mb-3">
              <p className="text-green-800 text-xs">
                ⏰ <strong>Daily Suggestions:</strong> Setting up your preferred time will automatically 
                generate 5 draft posts based on your interests and news sources.
              </p>
            </div>
          )}

          <div className="flex items-center gap-2">
            <Button
              size="sm"
              onClick={handleCompleteStep}
              className="flex items-center gap-1"
            >
              Mark Complete
              <ArrowRight className="h-3 w-3" />
            </Button>
            
            {onDismiss && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onDismiss}
                className="text-blue-600 hover:text-blue-800"
              >
                Dismiss
              </Button>
            )}
          </div>
        </div>

        {onDismiss && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onDismiss}
            className="flex-shrink-0 text-blue-500 hover:text-blue-700"
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  );
};

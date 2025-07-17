/**
 * Onboarding Modal Component
 *
 * Main modal that guides users through the onboarding process
 * with step-by-step instructions and progress tracking.
 */

import React, { useState } from "react";
import { X, ChevronRight, ChevronLeft, SkipForward } from "lucide-react";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { useOnboarding } from "../../hooks/useOnboarding";
import type { OnboardingStep } from "../../types/onboarding";

interface OnboardingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSkip: () => void;
}

export const OnboardingModal: React.FC<OnboardingModalProps> = ({
  isOpen,
  onClose,
  onSkip,
}) => {
  const {
    progress,
    loading,
    getStepsWithStatus,
    goToStep,
    goToNextStep,
    updateStep,
  } = useOnboarding();

  const [currentViewStep, setCurrentViewStep] = useState(1);
  const steps = getStepsWithStatus();
  const currentStep = steps.find((s) => s.id === currentViewStep);

  if (!isOpen || loading || !progress) return null;

  const handleStepComplete = async () => {
    try {
      await updateStep(currentViewStep, true);
      if (currentViewStep < 6) {
        setCurrentViewStep(currentViewStep + 1);
      } else {
        onClose();
      }
    } catch (error) {
      console.error("Failed to update step:", error);
    }
  };

  const handleGoToStep = () => {
    if (currentStep) {
      goToStep(currentStep.id);
      onClose();
    }
  };

  const handleNext = () => {
    if (currentViewStep < 6) {
      setCurrentViewStep(currentViewStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentViewStep > 1) {
      setCurrentViewStep(currentViewStep - 1);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-semibold text-gray-900">
              Welcome to Promptly Social Scribe! 🎉
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={onSkip}
              className="text-gray-500 hover:text-gray-700"
            >
              <SkipForward className="h-4 w-4 mr-1" />
              Skip Tour
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="px-6 py-4 bg-gray-50">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              Step {currentViewStep} of 6
            </span>
            <span className="text-sm text-gray-500">
              {Math.round((currentViewStep / 6) * 100)}% Complete
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(currentViewStep / 6) * 100}%` }}
            />
          </div>
        </div>

        {/* Step Content */}
        {currentStep && (
          <div className="p-6">
            <div className="flex items-center gap-3 mb-4">
              <span className="text-3xl">{currentStep.icon}</span>
              <div>
                <h3 className="text-xl font-semibold text-gray-900">
                  {currentStep.title}
                </h3>
                <p className="text-gray-600">{currentStep.description}</p>
              </div>
              {currentStep.isCompleted && (
                <Badge variant="default" className="ml-auto">
                  ✓ Completed
                </Badge>
              )}
            </div>

            {/* Step Highlights */}
            {currentStep.highlights && currentStep.highlights.length > 0 && (
              <div className="bg-blue-50 rounded-lg p-4 mb-6">
                <h4 className="font-medium text-blue-900 mb-2">
                  What you'll do in this step:
                </h4>
                <ul className="space-y-1">
                  {currentStep.highlights.map((highlight, index) => (
                    <li
                      key={index}
                      className="text-blue-800 text-sm flex items-start gap-2"
                    >
                      <span className="text-blue-600 mt-1">•</span>
                      <span>{highlight}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Special Notes */}
            {currentStep.id === 1 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
                <p className="text-yellow-800 text-sm">
                  <strong>Note:</strong> The LinkedIn analysis can take up to 5
                  minutes. You can also highlight the analyze/re-analyze button
                  in the writing style section to provide your own writing
                  sample.
                </p>
              </div>
            )}

            {currentStep.id === 5 && (
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-6">
                <p className="text-orange-800 text-sm">
                  <strong>Note:</strong> URLs to social media platforms are not
                  supported yet.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t bg-gray-50">
          <Button
            variant="outline"
            onClick={handlePrevious}
            disabled={currentViewStep === 1}
            className="flex items-center gap-2"
          >
            <ChevronLeft className="h-4 w-4" />
            Previous
          </Button>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={handleGoToStep}
              className="flex items-center gap-2"
            >
              Go to {currentStep?.title}
            </Button>

            {currentViewStep < 6 ? (
              <Button onClick={handleNext} className="flex items-center gap-2">
                Next
                <ChevronRight className="h-4 w-4" />
              </Button>
            ) : (
              <Button onClick={onClose} className="flex items-center gap-2">
                Finish Tour
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

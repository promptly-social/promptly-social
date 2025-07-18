/**
 * Onboarding Progress Indicator Component
 *
 * Shows the current progress through the onboarding steps
 * with visual indicators and step navigation.
 */

import React, { useState } from "react";
import { Check, Circle, ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { useOnboarding } from "../../hooks/useOnboarding";

interface OnboardingProgressProps {
  showStepNavigation?: boolean;
  compact?: boolean;
  className?: string;
}

export const OnboardingProgress: React.FC<OnboardingProgressProps> = ({
  showStepNavigation = false,
  compact = false,
  className = "",
}) => {
  const { progress, getStepsWithStatus, goToStep } = useOnboarding();
  const steps = getStepsWithStatus();
  const [isExpanded, setIsExpanded] = useState(false);

  // Hide progress component when onboarding is completed or skipped
  if (!progress || progress.is_completed || progress.is_skipped) return null;

  return (
    <div className={`bg-white rounded-lg border shadow-sm p-4 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold text-gray-900">Getting Started</h3>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 hover:bg-gray-100 rounded transition-colors"
            aria-label={isExpanded ? "Collapse" : "Expand"}
          >
            {isExpanded ? (
              <ChevronUp className="h-4 w-4 text-gray-500" />
            ) : (
              <ChevronDown className="h-4 w-4 text-gray-500" />
            )}
          </button>
        </div>
        <Badge variant="outline">
          {Math.round(progress.progress_percentage)}% Complete
        </Badge>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
        <div
          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
          style={{ width: `${progress.progress_percentage}%` }}
        />
      </div>

      {/* Steps List - Only show when expanded */}
      {isExpanded && (
        <div className="space-y-2">
          {steps.map((step, index) => (
            <div
              key={step.id}
              className={`flex items-center gap-3 p-2 rounded-lg transition-colors ${
                step.isActive ? "bg-blue-50 border border-blue-200" : ""
              }`}
            >
              {/* Step Icon */}
              <div
                className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${
                  step.isCompleted
                    ? "bg-green-500 text-white"
                    : step.isActive
                    ? "bg-blue-500 text-white"
                    : "bg-gray-200 text-gray-500"
                }`}
              >
                {step.isCompleted ? (
                  <Check className="h-3 w-3" />
                ) : (
                  <Circle className="h-3 w-3" />
                )}
              </div>

              {/* Step Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm">{step.icon}</span>
                  <span
                    className={`text-sm font-medium ${
                      step.isActive ? "text-blue-900" : "text-gray-900"
                    }`}
                  >
                    {step.title}
                  </span>
                  {step.isCompleted && (
                    <Badge variant="default" className="text-xs">
                      ✓
                    </Badge>
                  )}
                </div>
                <p
                  className={`text-xs mt-1 ${
                    step.isActive ? "text-blue-700" : "text-gray-600"
                  }`}
                >
                  {step.description}
                </p>
              </div>

              {/* Navigation Button */}
              {showStepNavigation && (
                <Button
                  variant={step.isActive ? "default" : "ghost"}
                  size="sm"
                  onClick={() => goToStep(step.id)}
                  className="flex-shrink-0"
                >
                  {step.isActive ? "Continue" : "Go"}
                </Button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Completion Message */}
      {progress.is_completed && (
        <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center gap-2">
            <Check className="h-4 w-4 text-green-600" />
            <span className="text-sm font-medium text-green-900">
              Onboarding Complete! 🎉
            </span>
          </div>
          <p className="text-xs text-green-700 mt-1">
            You're all set up and ready to create amazing content!
          </p>
        </div>
      )}
    </div>
  );
};

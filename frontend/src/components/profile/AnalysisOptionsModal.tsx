import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";

export interface AnalysisOption {
  key: string;
  label: string;
  description: string;
}

interface AnalysisOptionsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAnalyze: (selectedOptions: string[]) => void;
  platform: string;
  isAnalyzing: boolean;
  hasExistingAnalysis: boolean;
}

const COMMON_ANALYSIS_OPTIONS: AnalysisOption[] = [
  {
    key: "bio",
    label: "Bio",
    description:
      "Analyze and update your professional bio based on your content",
  },
  {
    key: "writing_style",
    label: "Writing Style Analysis",
    description: "Analyze your writing patterns, tone, and style preferences",
  },
];

const PLATFORM_SPECIFIC_OPTIONS: Record<string, AnalysisOption[]> = {
  linkedin: [
    {
      key: "interests",
      label: "Topics of Interest",
      description:
        "Identify topics and themes you're interested in from your activity",
    },
  ],
  substack: [
    {
      key: "interests",
      label: "Topics of Interest",
      description:
        "Identify topics and themes from your subscribed newsletters",
    },
    {
      key: "substacks",
      label: "Substack Newsletters",
      description:
        "Analyze your subscribed newsletters to understand your content preferences",
    },
  ],
};

export const AnalysisOptionsModal: React.FC<AnalysisOptionsModalProps> = ({
  isOpen,
  onClose,
  onAnalyze,
  platform,
  isAnalyzing,
  hasExistingAnalysis,
}) => {
  const platformKey = platform.toLowerCase();
  const availableOptions = [
    ...COMMON_ANALYSIS_OPTIONS,
    ...(PLATFORM_SPECIFIC_OPTIONS[platformKey] || []),
  ];

  const [selectedOptions, setSelectedOptions] = useState<string[]>(
    availableOptions.map((opt) => opt.key)
  );

  const handleOptionChange = (optionKey: string, checked: boolean) => {
    setSelectedOptions((prev) =>
      checked ? [...prev, optionKey] : prev.filter((key) => key !== optionKey)
    );
  };

  const handleAnalyze = () => {
    if (selectedOptions.length === 0) {
      return; // Don't proceed if no options selected
    }
    onAnalyze(selectedOptions);
    onClose();
  };

  const handleClose = () => {
    // Reset to default selections when closing
    setSelectedOptions(availableOptions.map((opt) => opt.key));
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>
            {hasExistingAnalysis ? "Re-analyze" : "Analyze"} {platform} Content
          </DialogTitle>
          <DialogDescription>
            Choose what aspects of your {platform} content you'd like to
            analyze. This will help personalize your content recommendations.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          {availableOptions.map((option) => (
            <div key={option.key} className="flex items-start space-x-3">
              <Checkbox
                id={option.key}
                checked={selectedOptions.includes(option.key)}
                onCheckedChange={(checked) =>
                  handleOptionChange(option.key, checked as boolean)
                }
              />
              <div className="grid gap-1.5 leading-none">
                <Label
                  htmlFor={option.key}
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  {option.label}
                </Label>
                <p className="text-xs text-muted-foreground">
                  {option.description}
                </p>
              </div>
            </div>
          ))}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={isAnalyzing}
          >
            Cancel
          </Button>
          <Button
            onClick={handleAnalyze}
            disabled={isAnalyzing || selectedOptions.length === 0}
          >
            {isAnalyzing
              ? "Analyzing..."
              : hasExistingAnalysis
              ? "Re-analyze"
              : "Start Analysis"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

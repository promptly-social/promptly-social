import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Sparkles, AlertCircle } from "lucide-react";

interface ConnectedPlatform {
  platform: string;
  platform_username: string | null;
  is_active: boolean;
}

interface StyleAdaptationToggleProps {
  useStyleAdaptation: boolean;
  onStyleAdaptationChange: (checked: boolean) => void;
  connectedPlatforms: ConnectedPlatform[];
  hasStyleAnalysis: boolean;
}

export const StyleAdaptationToggle: React.FC<StyleAdaptationToggleProps> = ({
  useStyleAdaptation,
  onStyleAdaptationChange,
  connectedPlatforms,
  hasStyleAnalysis,
}) => {
  const shouldShowStyleAdaptation = () => {
    return connectedPlatforms.length > 0 && hasStyleAnalysis;
  };

  if (shouldShowStyleAdaptation()) {
    return (
      <Card className="bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
        <CardContent className="pt-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Sparkles className="w-5 h-5 text-purple-600" />
              <div>
                <Label className="text-sm font-medium text-purple-800">
                  Style Adaptation
                </Label>
                <p className="text-xs text-purple-600">
                  Generate content matching your writing style
                </p>
              </div>
            </div>
            <Switch
              checked={useStyleAdaptation}
              onCheckedChange={onStyleAdaptationChange}
            />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (connectedPlatforms.length === 0 || !hasStyleAnalysis) {
    return (
      <Card className="bg-gradient-to-r from-gray-50 to-blue-50 border-gray-200">
        <CardContent className="pt-4">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-gray-600" />
            <div>
              <Label className="text-sm font-medium text-gray-800">
                Style Adaptation Available
              </Label>
              <p className="text-xs text-gray-600">
                {connectedPlatforms.length === 0
                  ? "Connect social accounts and complete writing analysis to enable style adaptation"
                  : "Complete writing analysis to enable style adaptation"}
              </p>
            </div>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={() => (window.location.href = "/profile")}
            className="mt-3 text-gray-700 border-gray-300 hover:bg-gray-50"
          >
            Go to Writing Profile
          </Button>
        </CardContent>
      </Card>
    );
  }

  return null;
};

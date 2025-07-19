import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import {
  profileApi,
  type SocialConnection as ApiSocialConnection,
} from "@/lib/profile-api";
import { useProfile } from "@/contexts/ProfileContext";
import { Link2, Users } from "lucide-react";
import { PlatformConnectionCard } from "./PlatformConnectionCard";

type SocialConnection = ApiSocialConnection;

export const LinkedInConnection: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisModalOpen, setAnalysisModalOpen] = useState(false);
  const { toast } = useToast();
  const { linkedinConnection: connection, refreshProfile } = useProfile();

  const platformKey = "linkedin";
  const platformName = "LinkedIn";

  const handleSave = async (username: string) => {
    setIsLoading(true);
    try {
      await profileApi.updateSocialConnection(platformKey, {
        platform_username: username,
        is_active: connection?.is_active || true, // Keep it active if it was already
      });
      toast({
        title: "Saved",
        description: `${platformName} username saved successfully`,
      });
      await refreshProfile();
    } catch (error) {
      console.error(`Error saving ${platformName} username:`, error);
      toast({
        title: "Error",
        description: `Failed to save ${platformName} username`,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    setIsLoading(true);
    try {
      // We just deactivate, don't clear username if they want to reconnect
      await profileApi.updateSocialConnection(platformKey, {
        platform_username: "",
      });
      toast({
        title: "Disconnected",
        description: `${platformName} has been disconnected.`,
      });
      await refreshProfile();
    } catch (error) {
      console.error(`Error disconnecting ${platformName}:`, error);
      toast({
        title: "Error",
        description: `Failed to disconnect ${platformName}`,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const openAnalysisModal = () => {
    if (!connection?.platform_username) {
      toast({
        title: "Username required",
        description: `Please set your public ${platformName} username before starting an analysis.`,
        variant: "destructive",
      });
      return;
    }
    setAnalysisModalOpen(true);
  };

  const handleAnalyze = async (contentToAnalyze: string[]) => {
    setIsAnalyzing(true);
    try {
      const result = await profileApi.runLinkedInAnalysis(contentToAnalyze);
      if (result.is_analyzing) {
        toast({
          title: "Analysis Started",
          description: `Analyzing your ${platformName} content...`,
        });
      } else if (result.analysis_completed_at) {
        toast({
          title: "Analysis Completed",
          description: `Your ${platformName} analysis is ready!`,
        });
      }
      await refreshProfile();
    } catch (error) {
      console.error(`Error analyzing ${platformName}:`, error);
      const apiError = error as { response?: { data?: { detail?: string } } };
      toast({
        title: "Analysis Error",
        description:
          apiError.response?.data?.detail ||
          `Failed to start ${platformName} analysis.`,
        variant: "destructive",
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <PlatformConnectionCard
      platformName={platformName}
      icon={Users}
      iconClassName="text-blue-600"
      connection={connection}
      onSave={handleSave}
      onDelete={handleDelete}
      onAnalyze={handleAnalyze}
      openAnalysisModal={openAnalysisModal}
      analysisModalOpen={analysisModalOpen}
      setAnalysisModalOpen={setAnalysisModalOpen}
      isLoading={isLoading}
      isAnalyzing={isAnalyzing}
      usernamePlaceholder="your-public-username"
      usernamePrefix="linkedin.com/in/"
    />
  );
};

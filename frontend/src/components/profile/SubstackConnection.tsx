// frontend/src/components/profile/SubstackConnection.tsx

import React, { useState, useMemo } from "react";
import { useToast } from "@/hooks/use-toast";
import {
  profileApi,
  type SocialConnection as ApiSocialConnection,
} from "@/lib/profile-api";
import { useProfile } from "@/contexts/ProfileContext";
import { FileText } from "lucide-react";
import { PlatformConnectionCard } from "./PlatformConnectionCard";

type SocialConnection = ApiSocialConnection;

export const SubstackConnection: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisModalOpen, setAnalysisModalOpen] = useState(false);
  const { toast } = useToast();
  const { socialConnections, refreshProfile } = useProfile();

  const platformKey = "substack";
  const platformName = "Substack";

  const connection = useMemo(
    () => socialConnections.find((conn) => conn.platform === platformKey) || null,
    [socialConnections]
  );

  const handleSave = async (handle: string) => {
    setIsLoading(true);
    try {
      await profileApi.updateSocialConnection(platformKey, {
        platform_username: handle,
        is_active: true,
      });
      toast({
        title: "Saved",
        description: `${platformName} handle saved successfully`,
      });
      await refreshProfile();
    } catch (error) {
      console.error(`Error saving ${platformName} handle:`, error);
      toast({
        title: "Error",
        description: `Failed to save ${platformName} handle`,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    setIsLoading(true);
    try {
      await profileApi.updateSocialConnection(platformKey, {
        platform_username: "",
        is_active: false,
      });
      toast({
        title: "Deleted",
        description: `${platformName} handle removed successfully`,
      });
      await refreshProfile();
    } catch (error) {
      console.error(`Error deleting ${platformName} handle:`, error);
      toast({
        title: "Error",
        description: `Failed to remove ${platformName} handle`,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const openAnalysisModal = () => {
    if (!connection?.platform_username) {
      toast({
        title: "Error",
        description: `Please set your ${platformName} handle first`,
        variant: "destructive",
      });
      return;
    }
    setAnalysisModalOpen(true);
  };

  const handleAnalyze = async (contentToAnalyze: string[]) => {
    setIsAnalyzing(true);
    try {
      const result = await profileApi.runSubstackAnalysis(contentToAnalyze);
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
      icon={FileText}
      iconClassName="text-orange-600"
      connection={connection}
      onSave={handleSave}
      onDelete={handleDelete}
      onAnalyze={handleAnalyze}
      openAnalysisModal={openAnalysisModal}
      analysisModalOpen={analysisModalOpen}
      setAnalysisModalOpen={setAnalysisModalOpen}
      isLoading={isLoading}
      isAnalyzing={isAnalyzing}
      usernamePlaceholder="your-handle"
      usernameSuffix=".substack.com"
    />
  );
};

import React, { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import {
  profileApi,
  type SocialConnection as ApiSocialConnection,
} from "@/lib/profile-api";
import { useAuth } from "@/contexts/AuthContext";
import { Link2, Users, FileText } from "lucide-react";
import { SubstackConnection } from "./SubstackConnection";

type SocialConnection = ApiSocialConnection;

export const SocialConnections: React.FC = () => {
  const [connections, setConnections] = useState<SocialConnection[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const { toast } = useToast();
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      fetchConnections();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const fetchConnections = async () => {
    try {
      const data = await profileApi.getSocialConnections();
      setConnections(data || []);
    } catch (error) {
      console.error("Error fetching connections:", error);
      toast({
        title: "Error",
        description: "Failed to fetch social connections",
        variant: "destructive",
      });
    }
  };

  const connectPlatform = async (platform: "linkedin") => {
    if (platform === "linkedin") {
      setIsLoading(true);
      try {
        const { authorization_url } = await profileApi.linkedinAuthorize();
        window.location.href = authorization_url;
      } catch (error) {
        console.error("Error starting LinkedIn connection:", error);
        toast({
          title: "Connection Error",
          description:
            "Could not initiate LinkedIn connection. Please try again.",
          variant: "destructive",
        });
        setIsLoading(false);
      }
    }
  };

  const disconnectPlatform = async (platform: "linkedin") => {
    setIsLoading(true);
    try {
      await profileApi.updateSocialConnection(platform, {
        is_active: false,
      });

      toast({
        title: "Disconnected",
        description: `Successfully disconnected from ${platform}`,
      });

      fetchConnections();
    } catch (error) {
      console.error("Error disconnecting platform:", error);
      toast({
        title: "Disconnection Error",
        description: `Failed to disconnect from ${platform}`,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const analyzePlatform = async (platform: "linkedin") => {
    if (platform === "linkedin") {
      const connection = getConnection("linkedin");
      if (!connection) {
        toast({
          title: "Error",
          description: "Please connect to LinkedIn first",
          variant: "destructive",
        });
        return;
      }

      setIsAnalyzing(true);
      try {
        // Trigger the analysis
        const result = await profileApi.runLinkedInAnalysis();

        if (result.is_analyzing) {
          toast({
            title: "Analysis Started",
            description: "Analyzing your LinkedIn bio and interests...",
          });
        } else if (result.analysis_completed_at) {
          toast({
            title: "Analysis Completed",
            description: "Your LinkedIn analysis is ready!",
          });
        }

        // Refresh the connection data to show updated status
        fetchConnections();
      } catch (error) {
        console.error("Error analyzing LinkedIn:", error);
        const apiError = error as { response?: { data?: { detail?: string } } };
        toast({
          title: "Analysis Error",
          description:
            apiError.response?.data?.detail ||
            "Failed to start LinkedIn analysis.",
          variant: "destructive",
        });
      } finally {
        setIsAnalyzing(false);
      }
    }
  };

  const getConnection = (platform: string) =>
    connections.find((conn) => conn.platform === platform && conn.is_active);

  const linkedinConnection = getConnection("linkedin");

  const platforms = [
    {
      name: "LinkedIn",
      key: "linkedin" as const,
      icon: Users,
      color: "blue",
      connection: linkedinConnection,
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Link2 className="w-5 h-5" />
          Social Media Connections
        </CardTitle>
        <CardDescription>
          Connect your social media accounts to get personalized content
          recommendations by analyzing your bio and content preferences.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Substack Connection Component */}
        <SubstackConnection />

        {/* Other Platform Connections */}
        {platforms.map((platform) => (
          <div
            key={platform.key}
            className="flex flex-col gap-3 p-4 border rounded-lg"
          >
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-3">
                <platform.icon
                  className={`w-5 h-5 text-${platform.color}-600`}
                />
                <div>
                  <p className="font-medium">{platform.name}</p>
                  <div className="text-sm text-gray-500">
                    <p>{platform.connection ? "Connected" : "Not connected"}</p>
                    {platform.connection?.analysis_completed_at &&
                      platform.connection?.analysis_status === "completed" && (
                        <p className="text-xs text-green-600">
                          Last analyzed:{" "}
                          {new Date(
                            platform.connection.analysis_completed_at
                          ).toLocaleDateString()}
                        </p>
                      )}
                    {platform.connection?.analysis_status === "error" && (
                      <p className="text-xs text-red-600">Analysis failed</p>
                    )}
                    {platform.connection?.analysis_status === "in_progress" && (
                      <p className="text-xs text-blue-600">
                        Analysis in progress...
                      </p>
                    )}
                  </div>
                </div>
              </div>

              {platform.connection ? (
                <div className="flex gap-2">
                  <Button
                    onClick={() => analyzePlatform(platform.key)}
                    size="sm"
                    disabled={
                      isLoading ||
                      isAnalyzing ||
                      platform.connection?.analysis_status === "in_progress"
                    }
                  >
                    <FileText className="w-4 h-4 mr-2" />
                    {isAnalyzing ||
                    platform.connection?.analysis_status === "in_progress"
                      ? "Analyzing..."
                      : platform.connection?.analysis_status === "completed"
                      ? "Re-analyze"
                      : platform.connection?.analysis_status === "error"
                      ? "Retry"
                      : "Analyze"}
                  </Button>
                </div>
              ) : (
                <Button
                  onClick={() => connectPlatform(platform.key)}
                  size="sm"
                  disabled={isLoading}
                >
                  <Link2 className="w-4 h-4 mr-2" />
                  Connect
                </Button>
              )}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
};

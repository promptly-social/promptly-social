import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";
import {
  profileApi,
  type SocialConnection as ApiSocialConnection,
} from "@/lib/profile-api";
import { useAuth } from "@/contexts/AuthContext";
import { FileText, Check, X, Edit, Trash2 } from "lucide-react";

type SocialConnection = ApiSocialConnection;

export const SubstackConnection: React.FC = () => {
  const [connection, setConnection] = useState<SocialConnection | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [handle, setHandle] = useState("");
  const { toast } = useToast();
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      fetchConnection();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const fetchConnection = async () => {
    try {
      const connections = await profileApi.getSocialConnections();
      const substackConnection = connections?.find(
        (conn) => conn.platform === "substack" && conn.is_active
      );
      setConnection(substackConnection || null);
      if (substackConnection?.platform_username) {
        setHandle(substackConnection.platform_username);
      }
    } catch (error) {
      console.error("Error fetching Substack connection:", error);
      toast({
        title: "Error",
        description: "Failed to fetch Substack connection",
        variant: "destructive",
      });
    }
  };

  const handleSave = async () => {
    if (!handle.trim()) {
      toast({
        title: "Error",
        description: "Please enter a valid Substack handle",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    try {
      await profileApi.updateSocialConnection("substack", {
        platform_username: handle.trim(),
        is_active: true,
      });

      toast({
        title: "Saved",
        description: "Substack handle saved successfully",
      });

      setIsEditing(false);
      fetchConnection();
    } catch (error) {
      console.error("Error saving Substack handle:", error);
      toast({
        title: "Error",
        description: "Failed to save Substack handle",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    setHandle(connection?.platform_username || "");
  };

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleDelete = async () => {
    setIsLoading(true);
    try {
      await profileApi.updateSocialConnection("substack", {
        platform_username: "",
        is_active: false,
      });

      toast({
        title: "Deleted",
        description: "Substack handle removed successfully",
      });

      setHandle("");
      fetchConnection();
    } catch (error) {
      console.error("Error deleting Substack handle:", error);
      toast({
        title: "Error",
        description: "Failed to remove Substack handle",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!connection?.platform_username) {
      toast({
        title: "Error",
        description: "Please set your Substack handle first",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    try {
      // Trigger the analysis
      const result = await profileApi.runSubstackAnalysis();

      if (result.is_analyzing) {
        toast({
          title: "Analysis Started",
          description: "Analyzing your Substack content...",
        });
      } else if (result.analysis_completed_at) {
        toast({
          title: "Analysis Completed",
          description: "Your Substack analysis is ready!",
        });
      }

      // Refresh the connection data to show updated status
      fetchConnection();
    } catch (error) {
      console.error("Error analyzing Substack:", error);
      toast({
        title: "Analysis Error",
        description: "Failed to analyze Substack content",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col justify-between p-4 border rounded-lg gap-1">
      <div className="flex items-center justify-between w-full">
        <div className="flex items-center gap-3">
          <FileText className="w-5 h-5 text-orange-600" />
          <div className="flex-1">
            <p className="font-medium">Substack</p>
          </div>
        </div>

        <Button
          onClick={handleAnalyze}
          size="sm"
          disabled={isLoading || !connection?.platform_username}
        >
          <FileText className="w-4 h-4 mr-2" />
          {connection?.analysis_started_at && !connection?.analysis_completed_at
            ? "Analyzing..."
            : connection?.analysis_completed_at
            ? "Re-analyze"
            : "Analyze"}
        </Button>
      </div>
      <div className="flex gap-2 mt-1 w-full md:w-[50%]">
        {isEditing ? (
          <>
            <Input
              value={handle}
              onChange={(e) => setHandle(e.target.value)}
              placeholder="Your handle (e.g., justinsowhat)"
              className="h-8 text-sm w-full"
              disabled={isLoading}
            />
            <Button
              onClick={handleSave}
              size="sm"
              variant="ghost"
              className="h-8 w-8 p-0"
              disabled={isLoading}
            >
              <Check className="w-4 h-4 text-green-600" />
            </Button>
            <Button
              onClick={handleCancel}
              size="sm"
              variant="ghost"
              className="h-8 w-8 p-0"
              disabled={isLoading}
            >
              <X className="w-4 h-4 text-red-600" />
            </Button>
          </>
        ) : (
          <>
            <div className="flex flex-col gap-1">
              <p className="text-sm text-gray-500">
                {connection?.platform_username || "No handle set"}
              </p>
              {connection?.analysis_started_at &&
                !connection?.analysis_completed_at && (
                  <p className="text-xs text-blue-600">
                    Analysis in progress...
                  </p>
                )}
              {connection?.analysis_completed_at && (
                <p className="text-xs text-green-600">
                  Last analyzed:{" "}
                  {new Date(
                    connection.analysis_completed_at
                  ).toLocaleDateString()}
                </p>
              )}
            </div>
            {connection?.platform_username && (
              <>
                <Button
                  onClick={handleEdit}
                  size="sm"
                  variant="ghost"
                  className="h-6 w-6 p-0"
                  disabled={isLoading}
                >
                  <Edit className="w-3 h-3" />
                </Button>
                <Button
                  onClick={handleDelete}
                  size="sm"
                  variant="ghost"
                  className="h-6 w-6 p-0"
                  disabled={isLoading}
                >
                  <Trash2 className="w-3 h-3 text-red-600" />
                </Button>
              </>
            )}
            {!connection?.platform_username && (
              <Button
                onClick={handleEdit}
                size="sm"
                variant="ghost"
                className="h-6 w-6 p-0"
                disabled={isLoading}
              >
                <Edit className="w-3 h-3" />
              </Button>
            )}
          </>
        )}
      </div>
    </div>
  );
};

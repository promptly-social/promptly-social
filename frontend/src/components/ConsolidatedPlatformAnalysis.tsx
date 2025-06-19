import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useAuth } from "@/contexts/AuthContext";
import { profileApi, PlatformAnalysisResponse } from "@/lib/profile-api";
import { BarChart3, Edit3, Check, X, Loader2 } from "lucide-react";

interface SocialConnection {
  platform: string;
  is_active: boolean;
}

export const ConsolidatedPlatformAnalysis: React.FC = () => {
  const { user } = useAuth();
  const [connections, setConnections] = useState<SocialConnection[]>([]);
  const [selectedPlatform, setSelectedPlatform] = useState<string>("");
  const [analysisData, setAnalysisData] =
    useState<PlatformAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedText, setEditedText] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (user) {
      fetchConnections();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const fetchConnections = async () => {
    try {
      const data = await profileApi.getSocialConnections();

      // Filter for active connections
      const connectionsData = data
        .filter((conn) => conn.is_active)
        .map((conn) => ({
          platform: conn.platform,
          is_active: conn.is_active,
        }));

      setConnections(connectionsData);

      // Auto-select first platform if available
      if (connectionsData.length > 0 && !selectedPlatform) {
        setSelectedPlatform(connectionsData[0].platform);
      }
    } catch (error) {
      console.error("Error fetching connections:", error);
    }
  };

  const getPlatformDisplayName = (platform: string) => {
    switch (platform) {
      case "substack":
        return "Substack";
      case "linkedin":
        return "LinkedIn";
      default:
        return platform.charAt(0).toUpperCase() + platform.slice(1);
    }
  };

  const fetchAnalysisData = async (platform: string) => {
    if (!platform) return;

    setLoading(true);
    try {
      const data = await profileApi.getWritingStyleAnalysis(platform);
      setAnalysisData(data);
      setEditedText(data.analysis_data || "");
    } catch (error) {
      console.error("Error fetching analysis data:", error);
      setAnalysisData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleEditClick = () => {
    setIsEditing(true);
    setEditedText(analysisData?.analysis_data || "");
  };

  const handleSave = async () => {
    if (!selectedPlatform || !editedText.trim()) return;

    setSaving(true);
    try {
      const updatedData = await profileApi.updateWritingStyleAnalysis(
        selectedPlatform,
        { analysis_data: editedText.trim() }
      );
      setAnalysisData(updatedData);
      setIsEditing(false);
    } catch (error) {
      console.error("Error updating analysis data:", error);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditedText(analysisData?.analysis_data || "");
  };

  // Fetch analysis data when platform changes
  useEffect(() => {
    if (selectedPlatform) {
      fetchAnalysisData(selectedPlatform);
    }
  }, [selectedPlatform]);

  if (connections.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Platform Writing Styles
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <p className="text-gray-600">No connected platforms found</p>
            <p className="text-sm text-gray-500">
              Connect your social accounts to analyze your writing style
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Platform Writing Styles
            </div>
            <div className="flex items-center gap-2">
              {!isEditing && analysisData?.analysis_data && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleEditClick}
                  className="flex items-center gap-2"
                >
                  <Edit3 className="w-4 h-4" />
                  Edit
                </Button>
              )}
              <Select
                value={selectedPlatform}
                onValueChange={setSelectedPlatform}
              >
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Select platform" />
                </SelectTrigger>
                <SelectContent>
                  {connections.map((connection) => (
                    <SelectItem
                      key={connection.platform}
                      value={connection.platform}
                    >
                      {getPlatformDisplayName(connection.platform)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {selectedPlatform && (
            <>
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin" />
                  <span className="ml-2">Loading analysis...</span>
                </div>
              ) : isEditing ? (
                <div className="space-y-4">
                  <Textarea
                    value={editedText}
                    onChange={(e) => setEditedText(e.target.value)}
                    placeholder="Enter your writing style analysis..."
                    className="min-h-[200px] resize-none"
                  />
                  <div className="flex gap-2 justify-end">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleCancel}
                      disabled={saving}
                    >
                      <X className="w-4 h-4 mr-1" />
                      Cancel
                    </Button>
                    <Button
                      size="sm"
                      onClick={handleSave}
                      disabled={saving || !editedText.trim()}
                    >
                      {saving ? (
                        <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                      ) : (
                        <Check className="w-4 h-4 mr-1" />
                      )}
                      {saving ? "Saving..." : "Save"}
                    </Button>
                  </div>
                </div>
              ) : analysisData?.analysis_data ? (
                <div className="space-y-4">
                  <div className="prose max-w-none">
                    <p className="whitespace-pre-wrap text-gray-700">
                      {analysisData.analysis_data}
                    </p>
                  </div>
                  {analysisData.last_analyzed && (
                    <div className="text-xs text-gray-500">
                      Last analyzed:{" "}
                      {new Date(analysisData.last_analyzed).toLocaleString()}
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-600">No analysis data found</p>
                  <p className="text-sm text-gray-500">
                    Run an analysis to see your writing style insights
                  </p>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

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
import { BarChart3, Edit3, Check, X, Loader2, Play, Link2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogTrigger,
  DialogClose,
} from "@/components/ui/dialog";

export const ConsolidatedPlatformAnalysis: React.FC = () => {
  const { user } = useAuth();
  const [connections, setConnections] = useState<Record<string, boolean>>({});
  const [selectedSource, setSelectedSource] = useState<string>("import");
  const [analysisData, setAnalysisData] =
    useState<PlatformAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedText, setEditedText] = useState("");
  const [saving, setSaving] = useState(false);

  // Analyze modal state
  const [analyzeModalOpen, setAnalyzeModalOpen] = useState(false);
  const [importText, setImportText] = useState("");

  useEffect(() => {
    if (user) {
      fetchConnections();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const fetchConnections = async () => {
    try {
      const data = await profileApi.getSocialConnections();
      const active: Record<string, boolean> = {};
      data.forEach((conn) => {
        if (conn.is_active) {
          active[conn.platform] = true;
        }
      });
      setConnections(active);
    } catch (error) {
      console.error("Error fetching connections:", error);
    }
  };

  const fetchAnalysisData = async () => {
    setLoading(true);
    try {
      const data = await profileApi.getWritingStyleAnalysis();
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
    if (!selectedSource || !editedText.trim()) return;

    setSaving(true);
    try {
      const updatedData = await profileApi.updateWritingStyleAnalysis({
        analysis_data: editedText.trim(),
      });
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

  const handleAnalyze = async () => {
    try {
      if (selectedSource === "import") {
        if (!importText.trim()) return;
        await profileApi.runWritingStyleAnalysis("import", {
          text: importText.trim(),
        });
      } else {
        await profileApi.runWritingStyleAnalysis(selectedSource);
      }

      setAnalyzeModalOpen(false);
      setImportText("");

      // Refresh analysis data
      fetchAnalysisData();
    } catch (error) {
      console.error("Error running analysis:", error);
    }
  };

  // Fetch analysis data on component mount and when user changes
  useEffect(() => {
    if (user) {
      fetchAnalysisData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Writing Styles
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

              {/* Analyze Dialog Trigger */}
              <Dialog
                open={analyzeModalOpen}
                onOpenChange={setAnalyzeModalOpen}
              >
                <DialogTrigger asChild>
                  <Button size="sm" className="flex items-center gap-2">
                    <Play className="w-4 h-4" /> Analyze
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-lg">
                  <DialogHeader>
                    <DialogTitle>Select Writing Sample Source</DialogTitle>
                  </DialogHeader>

                  {/* Source Selection */}
                  <Select
                    value={selectedSource}
                    onValueChange={(value) => {
                      setSelectedSource(value);
                    }}
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select source" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="linkedin">LinkedIn</SelectItem>
                      <SelectItem value="substack">Substack</SelectItem>
                      <SelectItem value="import">Import</SelectItem>
                    </SelectContent>
                  </Select>

                  {/* Conditional UI based on source */}
                  {selectedSource === "import" && (
                    <Textarea
                      value={importText}
                      onChange={(e) => setImportText(e.target.value)}
                      placeholder="Paste your writing sample here..."
                      className="mt-4 min-h-[180px] resize-none"
                    />
                  )}

                  {(selectedSource === "linkedin" ||
                    selectedSource === "substack") && (
                    <div className="mt-4">
                      {connections[selectedSource] ? (
                        <p className="text-sm text-gray-600">
                          Connection detected. Click Analyze to proceed.
                        </p>
                      ) : (
                        <div className="flex items-center gap-2 text-red-600 text-sm">
                          <Link2 className="w-4 h-4" />
                          Please connect your {selectedSource} account first.
                        </div>
                      )}
                    </div>
                  )}

                  <DialogFooter className="mt-4">
                    <DialogClose asChild>
                      <Button variant="outline">Cancel</Button>
                    </DialogClose>
                    <Button
                      onClick={handleAnalyze}
                      disabled={
                        selectedSource === "import"
                          ? !importText.trim()
                          : !connections[selectedSource]
                      }
                    >
                      {selectedSource === "import" ? "Analyze" : "Analyze"}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {selectedSource && (
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

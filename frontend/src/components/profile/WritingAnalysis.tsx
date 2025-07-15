import React, { useState, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
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
import {
  BarChart3,
  Edit3,
  Check,
  X,
  Loader2,
  Play,
  Link2,
  AlertTriangle,
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogTrigger,
  DialogClose,
} from "@/components/ui/dialog";
import { useToast } from "@/hooks/use-toast";
import { Alert, AlertDescription } from "@/components/ui/alert";

export const WritingAnalysis: React.FC = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [connections, setConnections] = useState<Record<string, boolean>>({});
  const [selectedSource, setSelectedSource] = useState<string>("import");
  const [analysisData, setAnalysisData] =
    useState<PlatformAnalysisResponse | null>(null);
  // React Query for fetching analysis
  const queryClient = useQueryClient();
  const { data: queryAnalysis, isLoading: isAnalysisLoading } = useQuery({
    queryKey: ["writingAnalysis"],
    queryFn: async () => {
      return await profileApi.getWritingStyleAnalysis();
    },
    staleTime: 1000 * 60 * 10,
  });

  useEffect(() => {
    setAnalysisData(queryAnalysis || null);
  }, [queryAnalysis]);
  const [analyzing, setAnalyzing] = useState(false);
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

  const refetchAnalysis = async () => {
    await queryClient.invalidateQueries({ queryKey: ["writingAnalysis"] });
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
    // Prevent multiple parallel analyze requests
    if (analyzing) return;

    setAnalyzing(true);
    try {
      if (selectedSource === "import") {
        if (!importText.trim()) return;
        await profileApi.runWritingStyleAnalysis("import", {
          text: importText.trim(),
        });
        toast({
          title: "Analysis Complete",
          description: "Your imported text has been analyzed successfully.",
        });
      } else {
        // For LinkedIn and Substack, call the writing style analysis endpoint
        await profileApi.runWritingStyleAnalysis(selectedSource);

        const platformName =
          selectedSource.charAt(0).toUpperCase() + selectedSource.slice(1);
        toast({
          title: "Analysis Started",
          description: `Analyzing your ${platformName} writing style. This may take a few minutes.`,
        });
      }

      setAnalyzeModalOpen(false);
      setImportText("");

      // Refresh analysis data
      await refetchAnalysis();
    } catch (error) {
      console.error("Error running analysis:", error);
      const apiError = error as { response?: { data?: { detail?: string } } };
      toast({
        title: "Analysis Error",
        description:
          apiError.response?.data?.detail ||
          `Failed to start ${selectedSource} analysis. Please try again.`,
        variant: "destructive",
      });
    } finally {
      setAnalyzing(false);
    }
  };

  // Trigger refetch when user changes (ensures query runs)
  useEffect(() => {
    if (user) {
      refetchAnalysis();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  // Check if there's existing analysis data to show warning
  const hasExistingAnalysis =
    analysisData?.analysis_data && analysisData.analysis_data.trim() !== "";

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Writing Style
          </CardTitle>
        </CardHeader>
        <CardContent>
          {selectedSource && (
            <>
              {isAnalysisLoading ? (
                <div className="space-y-3">
                  <Skeleton className="h-4 w-1/2" />
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-3 w-5/6" />
                  <Skeleton className="h-3 w-4/6" />
                  <Skeleton className="h-3 w-2/3" />
                </div>
              ) : (
                <div className="space-y-3">
                  {/* Edit and Analyze buttons positioned at top right, outside the text content */}
                  {!isEditing && (
                    <div className="flex justify-end gap-2">
                      {analysisData?.analysis_data && (
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
                          <Button
                            size="sm"
                            className="flex items-center gap-2"
                            disabled={analyzing}
                          >
                            {analyzing ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <Play className="w-4 h-4" />
                            )}
                            {analyzing
                              ? "Analyzing..."
                              : analysisData?.analysis_data
                              ? "Re-analyze"
                              : "Analyze"}
                          </Button>
                        </DialogTrigger>
                        <DialogContent className="sm:max-w-lg">
                          <DialogHeader>
                            <DialogTitle>
                              Select Writing Sample Source
                            </DialogTitle>
                          </DialogHeader>

                          {/* Warning about overwriting existing analysis */}
                          {hasExistingAnalysis && (
                            <Alert className="border-yellow-200 bg-yellow-50">
                              <AlertTriangle className="h-4 w-4 text-yellow-600" />
                              <AlertDescription className="text-yellow-800">
                                <strong>Warning:</strong> You already have a
                                writing style analysis. Running a new analysis
                                will overwrite your existing analysis.
                              </AlertDescription>
                            </Alert>
                          )}

                          {/* Source Selection */}
                          <Select
                            value={selectedSource}
                            onValueChange={(value) => {
                              if (analyzing) return; // Don't allow changes while analyzing
                              setSelectedSource(value);
                            }}
                            disabled={analyzing}
                          >
                            <SelectTrigger
                              className="w-full"
                              disabled={analyzing}
                            >
                              <SelectValue placeholder="Select source" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="linkedin">LinkedIn</SelectItem>
                              <SelectItem value="substack">Substack</SelectItem>
                              <SelectItem value="import">
                                Import Writing Sample
                              </SelectItem>
                            </SelectContent>
                          </Select>

                          {/* Conditional UI based on source */}
                          {selectedSource === "import" && (
                            <div className="space-y-3">
                              <Textarea
                                value={importText}
                                onChange={(e) => setImportText(e.target.value)}
                                placeholder="Paste your writing sample here... (e.g., blog posts, articles, social media posts)"
                                className="min-h-[180px] resize-none"
                              />
                              <p className="text-xs text-gray-500">
                                Tip: Include 2-3 substantial pieces of your
                                writing for the best analysis results.
                              </p>
                            </div>
                          )}

                          {(selectedSource === "linkedin" ||
                            selectedSource === "substack") && (
                            <div className="mt-4">
                              {analyzing ? (
                                <div className="space-y-2">
                                  <p className="text-sm text-gray-600">
                                    We are analyzing your {selectedSource}{" "}
                                    writing style. This may take a few minutes.
                                  </p>
                                  <div className="flex items-center gap-2 text-blue-600 text-xs">
                                    <Loader2 className="w-3 h-3 animate-spin" />
                                    Analysis in progress...
                                  </div>
                                </div>
                              ) : connections[selectedSource] ? (
                                <div className="space-y-2">
                                  <p className="text-sm text-gray-600">
                                    Connection detected. Click Analyze to
                                    analyze your {selectedSource} writing style.
                                  </p>
                                  <p className="text-xs text-gray-500">
                                    This will analyze your posts and content to
                                    understand your writing patterns.
                                  </p>
                                </div>
                              ) : (
                                <div className="flex items-center gap-2 text-red-600 text-sm">
                                  <Link2 className="w-4 h-4" />
                                  Please connect your {selectedSource} account
                                  first to analyze your writing style.
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
                                analyzing ||
                                (selectedSource === "import"
                                  ? !importText.trim()
                                  : !connections[selectedSource])
                              }
                            >
                              {analyzing ? (
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                              ) : null}
                              {analyzing ? "Analyzing..." : "Analyze"}
                            </Button>
                          </DialogFooter>
                        </DialogContent>
                      </Dialog>
                    </div>
                  )}

                  {isEditing ? (
                    <div className="border rounded-lg p-4 space-y-3 bg-blue-50">
                      <Textarea
                        value={editedText}
                        onChange={(e) => setEditedText(e.target.value)}
                        placeholder="Enter your writing style analysis..."
                        className="min-h-[250px] text-sm bg-white border-gray-200 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
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
                      <div className="min-h-[100px] p-4 bg-gray-50 rounded-lg border border-gray-200">
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">
                          {analysisData.analysis_data}
                        </p>
                      </div>
                      {analysisData.last_analyzed && (
                        <div className="text-xs text-gray-500">
                          Last updated:{" "}
                          {new Date(
                            analysisData.last_analyzed
                          ).toLocaleString()}
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
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

import { useProfile } from "@/contexts/ProfileContext";
import { profileApi, ContentStrategy } from "@/lib/profile-api";
import { useToast } from "@/hooks/use-toast";
import { Target, Edit3, Check, X, Plus } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

export const ContentStrategies: React.FC = () => {
  const { userPreferences, loading: isLoading, refreshProfile } = useProfile();
  const { toast } = useToast();
  const strategies = userPreferences?.content_strategies || [];

  const [editingStrategyId, setEditingStrategyId] = useState<string | null>(
    null
  );
  const [editingStrategy, setEditingStrategy] = useState<string>("");
  const [isSaving, setIsSaving] = useState(false);
  const [isAddingNew, setIsAddingNew] = useState(false);

  // Only supporting LinkedIn for now
  const LINKEDIN_PLATFORM = "linkedin";

  const handleEdit = (strategy: ContentStrategy) => {
    setEditingStrategyId(strategy.id);
    setEditingStrategy(strategy.strategy);
  };

  const handleCancel = () => {
    setEditingStrategyId(null);
    setEditingStrategy("");
    setIsAddingNew(false);
  };

  const handleConfirm = async () => {
    if (!editingStrategy.trim()) {
      toast({
        title: "Error",
        description: "Please enter a strategy",
        variant: "destructive",
      });
      return;
    }

    setIsSaving(true);
    try {
      await profileApi.updateUserPreferences({
        content_strategies: {
          [LINKEDIN_PLATFORM]: editingStrategy,
        },
      });

      await refreshProfile();

      setEditingStrategyId(null);
      setEditingStrategy("");
      setIsAddingNew(false);

      toast({
        title: "Success",
        description: "Content strategy updated successfully",
      });
    } catch (error) {
      console.error("Error saving content strategy:", error);
      toast({
        title: "Error",
        description: "Failed to save content strategy",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleAddNew = () => {
    setIsAddingNew(true);
    setEditingStrategy("");
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-2xl">
          <Target className="w-5 h-5" />
          Post Style
        </CardTitle>
        <p className="text-xs sm:text-sm text-gray-600">
          Define your post style and format for LinkedIn to instruct the AI to
          draft posts that sound like you.
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <div className="space-y-3">
            <Skeleton className="w-full h-6" />
            <Skeleton className="w-full h-24" />
            <Skeleton className="w-full h-6" />
            <Skeleton className="w-full h-24" />
          </div>
        ) : (
          <div className="space-y-4">
            {/* Edit buttons positioned at top right, outside the text boxes */}
            {strategies.length > 0 &&
              !isAddingNew &&
              editingStrategyId === null && (
                <div className="flex justify-end">
                  {strategies.map((strategy) => (
                    <Button
                      key={strategy.id}
                      onClick={() => handleEdit(strategy)}
                      size="sm"
                      variant="outline"
                      className="flex items-center gap-2"
                    >
                      <Edit3 className="w-4 h-4" />
                      Edit
                    </Button>
                  ))}
                </div>
              )}

            {/* Display existing strategies */}
            {strategies.map((strategy) => (
              <div key={strategy.id}>
                {editingStrategyId === strategy.id ? (
                  <div className="border rounded-lg p-4 space-y-3 bg-accent/10">
                    <Textarea
                      value={editingStrategy}
                      onChange={(e) => setEditingStrategy(e.target.value)}
                      placeholder="Describe your LinkedIn content strategy..."
                      className="min-h-[250px] text-sm bg-background border-border focus:border-primary focus:ring-1 focus:ring-primary"
                      disabled={isSaving}
                      autoFocus
                    />
                    <div className="flex justify-end gap-2">
                      <Button
                        onClick={handleCancel}
                        size="sm"
                        variant="outline"
                        disabled={isSaving}
                      >
                        <X className="w-4 h-4 mr-1" />
                        Cancel
                      </Button>
                      <Button
                        onClick={handleConfirm}
                        size="sm"
                        disabled={isSaving}
                      >
                        <Check className="w-4 h-4 mr-1" />
                        {isSaving ? "Saving..." : "Save"}
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="min-h-[100px] p-4 bg-muted/30 rounded-lg border border-border">
                    <p className="text-sm text-foreground whitespace-pre-wrap">
                      {strategy.strategy}
                    </p>
                  </div>
                )}
              </div>
            ))}

            {/* Add new strategy */}
            {isAddingNew && (
              <div className="border rounded-lg p-4 space-y-3 bg-accent/10">
                <Textarea
                  value={editingStrategy}
                  onChange={(e) => setEditingStrategy(e.target.value)}
                  placeholder="Describe your LinkedIn content strategy..."
                  className="min-h-[250px] text-sm bg-background border-border focus:border-primary focus:ring-1 focus:ring-primary"
                  disabled={isSaving}
                  autoFocus
                />
                <div className="flex justify-end gap-2">
                  <Button
                    onClick={handleCancel}
                    size="sm"
                    variant="outline"
                    disabled={isSaving}
                  >
                    <X className="w-4 h-4 mr-1" />
                    Cancel
                  </Button>
                  <Button onClick={handleConfirm} size="sm" disabled={isSaving}>
                    <Check className="w-4 h-4 mr-1" />
                    {isSaving ? "Saving..." : "Save"}
                  </Button>
                </div>
              </div>
            )}

            {/* Add new strategy button */}
            {!isAddingNew &&
              strategies.length === 0 &&
              editingStrategyId === null && (
                <Button
                  onClick={handleAddNew}
                  variant="outline"
                  className="w-full sm:w-auto"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Add LinkedIn Strategy
                </Button>
              )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

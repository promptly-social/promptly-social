import React, { useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useProfile } from "@/contexts/ProfileContext";
import { useUpdateUserPreferences } from "@/lib/profile-queries";
import { useToast } from "@/hooks/use-toast";
import { Palette, Save, X } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

interface ImageGenerationStyleEditorProps {
  /** Whether to show as a card (for standalone use) or just the content (for modal use) */
  variant?: "card" | "content";
  /** Optional callback when style is saved (useful for modals) */
  onSave?: (style: string | null) => void;
  /** Optional callback when editing is cancelled (useful for modals) */
  onCancel?: () => void;
  /** Whether to show save/cancel buttons (defaults to true for card, false for content) */
  showActions?: boolean;
}

export const ImageGenerationStyleEditor: React.FC<
  ImageGenerationStyleEditorProps
> = ({ variant = "card", onSave, onCancel, showActions }) => {
  const { userPreferences, loading: isLoading } = useProfile();
  const { toast } = useToast();
  const updatePreferencesMutation = useUpdateUserPreferences();

  const [isEditing, setIsEditing] = useState(false);
  const [pendingStyle, setPendingStyle] = useState<string>("");
  const [isSaving, setIsSaving] = useState(false);

  const currentStyle = userPreferences?.image_generation_style || "";
  const shouldShowActions = showActions ?? variant === "card";

  const startEditing = useCallback(() => {
    setPendingStyle(currentStyle);
    setIsEditing(true);
  }, [currentStyle]);

  const cancelEditing = useCallback(() => {
    setPendingStyle("");
    setIsEditing(false);
    onCancel?.();
  }, [onCancel]);

  const saveStyle = useCallback(async () => {
    setIsSaving(true);
    try {
      const styleToSave = pendingStyle.trim() || null;

      await updatePreferencesMutation.mutateAsync({
        image_generation_style: styleToSave,
      });

      setIsEditing(false);
      setPendingStyle("");

      toast({
        title: "Saved",
        description: "Image generation style updated successfully",
      });

      onSave?.(styleToSave);
    } catch (error) {
      console.error("Error saving image generation style:", error);
      toast({
        title: "Error",
        description: "Failed to save image generation style",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  }, [pendingStyle, updatePreferencesMutation, toast, onSave]);

  const content = (
    <>
      <div className="space-y-3 sm:space-y-4">
        <div className="flex items-center gap-2">
          <Palette className="w-4 h-4 text-purple-500" />
          <h3 className="font-medium text-sm sm:text-base">
            Image Generation Style
          </h3>
        </div>

        <p className="text-xs sm:text-sm text-gray-600">
          Customize how AI generates image prompts for your posts. Describe your
          preferred visual style, color palette, composition, or artistic
          approach. This will override default style options.
        </p>

        {isLoading ? (
          <Skeleton className="w-full h-24" />
        ) : isEditing ? (
          <div className="space-y-3">
            <Textarea
              placeholder="Describe your preferred image style (e.g., 'Minimalist vector illustrations with a blue and white color palette, clean lines, and modern typography' or 'Photorealistic 3D renders with warm lighting and professional corporate aesthetics')"
              value={pendingStyle}
              onChange={(e) => setPendingStyle(e.target.value)}
              className="min-h-24 text-sm sm:text-base resize-none"
              disabled={isSaving}
            />

            {shouldShowActions && (
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={cancelEditing}
                  disabled={isSaving}
                  size="sm"
                >
                  <X className="w-4 h-4 mr-1" />
                  Cancel
                </Button>
                <Button onClick={saveStyle} disabled={isSaving} size="sm">
                  <Save className="w-4 h-4 mr-1" />
                  {isSaving ? "Saving..." : "Save Style"}
                </Button>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {currentStyle ? (
              <div className="p-3 bg-muted/30 border border-border rounded-md">
                <p className="text-sm text-foreground whitespace-pre-wrap">
                  {currentStyle}
                </p>
              </div>
            ) : (
              <div className="p-3 bg-muted/30 border border-border rounded-md">
                <p className="text-sm text-gray-500 italic">
                  No custom image style set. Default AI style options will be
                  used.
                </p>
              </div>
            )}

            {shouldShowActions && (
              <Button
                variant="outline"
                onClick={startEditing}
                size="sm"
                disabled={isLoading}
              >
                <Palette className="w-4 h-4 mr-1" />
                {currentStyle ? "Edit Style" : "Set Custom Style"}
              </Button>
            )}
          </div>
        )}
      </div>
    </>
  );

  if (variant === "content") {
    return <div className="space-y-4">{content}</div>;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-2xl">
          <Palette className="w-5 h-5" />
          Image Generation Preferences
        </CardTitle>
      </CardHeader>
      <CardContent>{content}</CardContent>
    </Card>
  );
};

import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import { ImageGenerationStyleEditor } from "@/components/preferences/ImageGenerationStyleEditor";
import { Palette, ChevronDown, ChevronUp } from "lucide-react";
import { useProfile } from "@/contexts/ProfileContext";

interface PromptGenerationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCopy: (prompt: string) => void;
  onRegenerate: () => void;
  prompt: string;
}

export const PromptGenerationModal: React.FC<PromptGenerationModalProps> = ({
  isOpen,
  onClose,
  onCopy,
  onRegenerate,
  prompt,
}) => {
  const [editedPrompt, setEditedPrompt] = useState(prompt);
  const [showStyleEditor, setShowStyleEditor] = useState(false);
  const { toast } = useToast();
  const { userPreferences } = useProfile();

  useEffect(() => {
    setEditedPrompt(prompt);
  }, [prompt]);

  const handleCopy = () => {
    navigator.clipboard.writeText(editedPrompt);
    toast({
      title: "Prompt copied!",
      description: "The prompt has been copied to your clipboard.",
    });
    onCopy(editedPrompt);
    onClose();
  };

  const handleClose = () => {
    setShowStyleEditor(false);
    onClose();
  };

  const handleStyleSave = () => {
    setShowStyleEditor(false);
    toast({
      title: "Style Updated",
      description: "Your image generation style has been updated. Regenerate the prompt to apply the new style.",
    });
  };

  const toggleStyleEditor = () => {
    setShowStyleEditor(!showStyleEditor);
  };

  const handleRegenerate = () => {
    // Close the modal first
    handleClose();
    // Then trigger regeneration (which will reopen the modal with new content)
    onRegenerate();
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Generated Prompt</DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          <Textarea
            value={editedPrompt}
            onChange={(e) => setEditedPrompt(e.target.value)}
            className="min-h-[150px] resize-y"
          />
          
          {/* Image Generation Style Section */}
          <div className="border-t pt-4">
            <Button
              variant="ghost"
              onClick={toggleStyleEditor}
              className="w-full justify-between p-2 h-auto"
            >
              <div className="flex items-center gap-2">
                <Palette className="w-4 h-4 text-purple-500" />
                <span className="text-sm font-medium">
                  Image Generation Style
                  {userPreferences?.image_generation_style && (
                    <span className="ml-2 text-xs text-purple-600 bg-purple-100 px-2 py-0.5 rounded">
                      Custom
                    </span>
                  )}
                </span>
              </div>
              {showStyleEditor ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </Button>
            
            {showStyleEditor && (
              <div className="mt-3 p-3 bg-gray-50 rounded-md">
                <ImageGenerationStyleEditor
                  variant="content"
                  onSave={handleStyleSave}
                  onCancel={() => setShowStyleEditor(false)}
                  showActions={true}
                />
              </div>
            )}
          </div>
        </div>
        
        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>
            Close
          </Button>
          <Button variant="outline" onClick={handleRegenerate}>
            Regenerate
          </Button>
          <Button onClick={handleCopy}>Copy</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

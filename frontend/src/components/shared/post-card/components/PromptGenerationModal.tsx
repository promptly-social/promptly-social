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
  const { toast } = useToast();

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

  const handleRegenerate = () => {
    onRegenerate();
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Generated Prompt</DialogTitle>
        </DialogHeader>
        <Textarea
          value={editedPrompt}
          onChange={(e) => setEditedPrompt(e.target.value)}
          className="min-h-[150px] resize-y"
        />
        <DialogFooter>
          <Button variant="outline" onClick={handleRegenerate}>
            Regenerate
          </Button>
          <Button onClick={handleCopy}>Copy</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

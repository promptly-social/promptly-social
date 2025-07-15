import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Post } from "@/lib/posts-api";
import { Shuffle, ArrowDown } from "lucide-react";

export interface DropActionData {
  draggedPost: Post;
  targetPost: Post;
}

interface DropActionModalProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  onAction: (action: "swap" | "push") => void;
  isProcessing: boolean;
  dropActionData: DropActionData | null;
}

export const DropActionModal: React.FC<DropActionModalProps> = ({
  isOpen,
  onOpenChange,
  onAction,
  isProcessing,
  dropActionData,
}) => {
  if (!dropActionData) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Shuffle className="w-5 h-5" />
            Choose Drop Action
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="text-sm text-gray-600">
            <p>
              A post is already scheduled for this time. How should we proceed?
            </p>
          </div>

          <div className="space-y-3">
            <Button
              variant="outline"
              className="w-full max-w-md justify-start h-auto p-4"
              onClick={() => onAction("swap")}
              disabled={isProcessing}
            >
              <div className="flex items-center gap-3">
                <Shuffle className="w-5 h-5 text-purple-600" />
                <div className="text-left">
                  <div className="font-medium">Swap Schedules</div>
                  <div className="text-xs text-gray-500 text-wrap">
                    Swap the scheduled dates of the two posts.
                  </div>
                </div>
              </div>
            </Button>

            <Button
              variant="outline"
              className="w-full max-w-md justify-start h-auto p-4"
              onClick={() => onAction("push")}
              disabled={isProcessing}
            >
              <div className="flex items-center gap-3">
                <ArrowDown className="w-5 h-5 text-blue-600" />
                <div className="text-left text-wrap">
                  <div className="font-medium">Push & Schedule</div>
                  <div className="text-xs text-gray-500">
                    Push subsequent posts to the next available day and schedule
                    this post.
                  </div>
                </div>
              </div>
            </Button>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="ghost"
            onClick={() => onOpenChange(false)}
            disabled={isProcessing}
          >
            Cancel
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

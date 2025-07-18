import React from "react";
import { AlertTriangle } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface PostSharingErrorProps {
  hasError: boolean;
}

export const PostSharingError: React.FC<PostSharingErrorProps> = ({
  hasError,
}) => {
  if (!hasError) {
    return null;
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="inline-flex items-center">
            <AlertTriangle className="w-4 h-4 text-orange-500 hover:text-orange-600 cursor-help" />
          </div>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-xs">
          <p className="text-sm">
            An error occurred when Promptly tried to post on your behalf. Please
            try to reschedule it or post it now.
          </p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};
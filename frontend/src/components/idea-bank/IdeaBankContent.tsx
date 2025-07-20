import React, { useState } from "react";
import { ExternalLink } from "lucide-react";
import type { IdeaBankWithPost } from "@/lib/idea-bank-api";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

interface IdeaBankContentProps {
  ideaBank: IdeaBankWithPost["idea_bank"];
}

const isUrl = (value: string) => {
  try {
    new URL(value);
    return true;
  } catch {
    return false;
  }
};

const IdeaBankContent: React.FC<IdeaBankContentProps> = ({ ideaBank }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const shouldTruncate = ideaBank.data.value.length > 250;

  const renderContent = () => {
    if (isUrl(ideaBank.data.value)) {
      return (
        <a
          href={ideaBank.data.value}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-start gap-1 text-blue-600 hover:text-blue-800 hover:underline break-all text-sm"
        >
          <span className="break-all">{ideaBank.data.value}</span>
          <ExternalLink className="w-3 h-3 flex-shrink-0 mt-0.5" />
        </a>
      );
    }

    if (shouldTruncate) {
      return (
        <>
          <div className="whitespace-pre-wrap break-words text-sm">
            {`${ideaBank.data.value.substring(0, 250)}...`}
          </div>
          <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
            <DialogTrigger asChild>
              <Button variant="link" className="p-0 h-auto text-sm">
                Show all
              </Button>
            </DialogTrigger>
            <DialogContent className="max-h-[80vh] flex flex-col">
              <DialogHeader>
                <DialogTitle>
                  {ideaBank.data.title || "Idea Content"}
                </DialogTitle>
              </DialogHeader>
              <div className="flex-grow overflow-y-auto whitespace-pre-wrap break-words text-sm">
                {ideaBank.data.value}
              </div>
            </DialogContent>
          </Dialog>
        </>
      );
    }

    return (
      <div className="whitespace-pre-wrap break-words text-sm">
        {ideaBank.data.value}
      </div>
    );
  };

  return (
    <div className="space-y-1">
      {ideaBank.data.title && (
        <div className="font-medium text-sm text-gray-900">
          {ideaBank.data.title}
        </div>
      )}
      {renderContent()}
    </div>
  );
};

export default IdeaBankContent;

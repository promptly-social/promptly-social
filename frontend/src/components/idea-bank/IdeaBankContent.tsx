import React from "react";
import { ExternalLink } from "lucide-react";
import type { IdeaBankWithPost } from "@/lib/idea-bank-api";

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

const IdeaBankContent: React.FC<IdeaBankContentProps> = ({ ideaBank }) => (
  <div className="space-y-1">
    {ideaBank.data.title && (
      <div className="font-medium text-sm text-gray-900">
        {ideaBank.data.title}
      </div>
    )}
    {isUrl(ideaBank.data.value) ? (
      <a
        href={ideaBank.data.value}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-start gap-1 text-blue-600 hover:text-blue-800 hover:underline break-all text-sm"
      >
        <span className="break-all">{ideaBank.data.value}</span>
        <ExternalLink className="w-3 h-3 flex-shrink-0 mt-0.5" />
      </a>
    ) : (
      <div className="whitespace-pre-wrap break-words text-sm">
        {ideaBank.data.value}
      </div>
    )}
  </div>
);

export default IdeaBankContent;

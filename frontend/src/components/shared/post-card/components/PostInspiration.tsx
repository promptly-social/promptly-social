import React from "react";
import { IdeaBankData } from "@/lib/idea-bank-api";
import { ExternalLink } from "lucide-react";

interface PostInspirationProps {
  inspiration: IdeaBankData;
}

export const PostInspiration: React.FC<PostInspirationProps> = ({
  inspiration,
}) => {
  const isValidUrl = (string: string) => {
    try {
      new URL(string);
      return true;
    } catch (_) {
      return false;
    }
  };

  const renderInspirationContent = () => {
    if (inspiration.type === "url") {
      const displayText = inspiration.title || inspiration.value;
      return (
        <a
          href={inspiration.value}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:text-blue-800 hover:underline inline-flex items-center gap-1"
        >
          <span className="truncate max-w-[300px]">{displayText}</span>
          <ExternalLink className="w-3 h-3 flex-shrink-0" />
        </a>
      );
    }

    // For text and product types, check if the content is a URL and make it clickable
    const displayText = inspiration.value;
    const truncatedText =
      displayText.length > 100
        ? `${displayText.substring(0, 100)}...`
        : displayText;

    // If the text content is a valid URL, render it as a link
    if (isValidUrl(displayText.trim())) {
      return (
        <a
          href={displayText.trim()}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:text-blue-800 hover:underline inline-flex items-center gap-1"
          title={displayText}
        >
          <span className="truncate max-w-[300px]">{truncatedText}</span>
          <ExternalLink className="w-3 h-3 flex-shrink-0" />
        </a>
      );
    }

    return (
      <span className="italic text-gray-600" title={displayText}>
        {truncatedText}
      </span>
    );
  };

  return (
    <div className="text-sm text-muted-foreground">
      <span className="font-medium">Inspiration: </span>
      {renderInspirationContent()}
    </div>
  );
};
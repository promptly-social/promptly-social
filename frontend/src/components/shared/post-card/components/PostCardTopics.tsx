import React from "react";
import { Badge } from "@/components/ui/badge";

interface PostCardTopicsProps {
  topics: string[];
}

export const PostCardTopics: React.FC<PostCardTopicsProps> = ({ topics }) => {
  if (topics.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2 pt-2">
      <p className="text-xs sm:text-sm font-medium text-gray-700">
        Categories:
      </p>
      <div className="flex flex-wrap gap-1 sm:gap-2">
        {topics.map((topic, idx) => (
          <Badge key={idx} variant="outline" className="text-xs">
            {topic}
          </Badge>
        ))}
      </div>
    </div>
  );
};

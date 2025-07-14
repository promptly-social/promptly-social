import React, { useState } from "react";
import { Post } from "@/lib/posts-api";

const renderContentWithNewlines = (content: string) => {
  return content.split("\n").map((line, index) => (
    <React.Fragment key={index}>
      {line}
      {index < content.split("\n").length - 1 && <br />}
    </React.Fragment>
  ));
};

interface PostContentProps {
  post: Post;
  className?: string;
}

export const PostContent: React.FC<PostContentProps> = ({
  post,
  className,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const charLimit = 150;

  const isTruncatable = post.content.length > charLimit;

  const toggleExpansion = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsExpanded(!isExpanded);
  };

  const getDisplayedJsx = () => {
    if (!isTruncatable || isExpanded) {
      return (
        <>
          {renderContentWithNewlines(post.content)}
          {isTruncatable && (
            <a
              href="#"
              onClick={toggleExpansion}
              className="text-blue-600 hover:underline ml-1"
            >
              ...less
            </a>
          )}
        </>
      );
    }

    const truncatedContent = post.content.substring(0, charLimit);

    return (
      <>
        {renderContentWithNewlines(truncatedContent)}
        <a
          href="#"
          onClick={toggleExpansion}
          className="text-blue-600 hover:underline ml-1"
        >
          ...more
        </a>
      </>
    );
  };

  return (
    <div className={className}>
      <div className="whitespace-pre-wrap text-sm text-gray-800">
        {getDisplayedJsx()}
      </div>

      {post.media && post.media.length > 0 && (
        <div className="mt-4 border rounded-lg overflow-hidden">
          <img
            src={post.media[0].url}
            alt="Post media"
            className="w-full h-auto object-cover"
          />
        </div>
      )}
    </div>
  );
};

import React, { useState } from "react";
import { Post, PostMedia } from "@/types/posts";
import { Link } from "lucide-react";

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
  const [isExpanded, setIsExpanded] = useState(true);
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

  const renderMediaItem = (media: PostMedia) => {
    if (!media.gcs_url) return null;

    if (media.media_type === "article") {
      return (
        <a
          href={media.gcs_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-500 hover:underline flex items-center gap-2 bg-gray-50 p-3 rounded-lg"
        >
          <Link className="w-4 h-4 flex-shrink-0" />
          <span className="truncate">{media.gcs_url}</span>
        </a>
      );
    }
    if (media.media_type === "image") {
      return (
        <img
          src={media.gcs_url}
          alt={media.file_name || "Post media"}
          className="rounded-lg border w-full object-cover max-w-[600]"
        />
      );
    }
    if (media.media_type === "video") {
      return (
        <video
          src={media.gcs_url}
          controls
          className="rounded-lg border w-full bg-black max-w-[600]"
        />
      );
    }
    return null;
  };

  return (
    <div className={className}>
      <div className="whitespace-pre-wrap text-sm text-gray-800">
        {getDisplayedJsx()}
      </div>

      {post.media && post.media.length > 0 && (
        <div className="mt-4 grid gap-2 grid-cols-1 sm:grid-cols-2">
          {post.media.map((media) => (
            <div key={media.id} className="first:col-span-full">
              {renderMediaItem(media)}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

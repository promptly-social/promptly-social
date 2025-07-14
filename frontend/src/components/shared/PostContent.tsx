import React from "react";
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
  return (
    <div className={className}>
      <div className="whitespace-pre-wrap text-sm text-gray-800">
        {renderContentWithNewlines(post.content)}
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

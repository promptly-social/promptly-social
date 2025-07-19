import { Button } from "@/components/ui/button";
import { Link } from "lucide-react";
import { Post } from "@/types/posts";

interface LinkedInButtonProps {
  post: Post;
}

export const LinkedInButton = ({ post }: LinkedInButtonProps) => {
  return (
    post.status === "posted" &&
    post.linkedin_article_url && (
      <a
        href={post.linkedin_article_url}
        target="_blank"
        rel="noopener noreferrer"
        className="mr-2"
      >
        <Button variant="outline" size="sm">
          <Link className="h-4 w-4 mr-2" />
          View on LinkedIn
        </Button>
      </a>
    )
  );
};

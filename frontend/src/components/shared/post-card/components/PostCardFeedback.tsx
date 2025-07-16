import React from "react";
import { Button } from "@/components/ui/button";
import { ThumbsUp, ThumbsDown } from "lucide-react";

interface PostCardFeedbackProps {
  postId: string;
  onSubmitPositiveFeedback: (postId: string) => void;
  onOpenNegativeFeedbackModal: (postId: string) => void;
}

export const PostCardFeedback: React.FC<PostCardFeedbackProps> = ({
  postId,
  onSubmitPositiveFeedback,
  onOpenNegativeFeedbackModal,
}) => {
  return (
    <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg mt-4">
      <span className="text-sm text-gray-600">How is this suggestion?</span>
      <div className="flex gap-2">
        <Button
          size="sm"
          variant="outline"
          onClick={() => onSubmitPositiveFeedback(postId)}
          className="text-green-600 hover:text-green-700 hover:bg-green-50"
        >
          <ThumbsUp className="w-4 h-4" />
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => onOpenNegativeFeedbackModal(postId)}
          className="text-red-600 hover:text-red-700 hover:bg-red-50"
        >
          <ThumbsDown className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
};

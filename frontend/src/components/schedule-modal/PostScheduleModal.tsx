import React from "react";
import { SchedulePostModalBase } from "./SchedulePostModalBase";
import { Post } from "@/types/posts";

interface PostScheduleModalProps {
  isOpen: boolean;
  onClose: () => void;
  post: Post | null;
  onSchedule: (postId: string, scheduledAt: string) => void;
  isScheduling?: boolean;
}

export const PostScheduleModal: React.FC<PostScheduleModalProps> = ({
  isOpen,
  onClose,
  post,
  onSchedule,
  isScheduling = false,
}) => {
  return (
    <SchedulePostModalBase
      mode="schedule"
      isOpen={isOpen}
      onClose={onClose}
      post={post}
      onSubmit={onSchedule}
      isSubmitting={isScheduling}
    />
  );
};

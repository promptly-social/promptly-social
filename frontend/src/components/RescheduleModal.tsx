import React from "react";
import { SchedulePostModalBase } from "./SchedulePostModalBase";
import { Post } from "@/lib/posts-api";

interface RescheduleModalProps {
  isOpen: boolean;
  onClose: () => void;
  post: Post | null;
  scheduledPosts: Post[];
  onReschedule: (postId: string, scheduledAt: string) => void;
  isRescheduling?: boolean;
}

export const RescheduleModal: React.FC<RescheduleModalProps> = ({
  isOpen,
  onClose,
  post,
  scheduledPosts,
  onReschedule,
  isRescheduling = false,
}) => {
  return (
    <SchedulePostModalBase
      mode="reschedule"
      isOpen={isOpen}
      onClose={onClose}
      post={post}
      scheduledPosts={scheduledPosts}
      onSubmit={onReschedule}
      isSubmitting={isRescheduling}
    />
  );
};

import React from "react";
import { SchedulePostModalBase } from "./SchedulePostModalBase";
import { Post } from "@/types/posts";

interface RescheduleModalProps {
  isOpen: boolean;
  onClose: () => void;
  post: Post | null;
  onReschedule: (postId: string, scheduledAt: string) => void;
  isRescheduling?: boolean;
}

export const RescheduleModal: React.FC<RescheduleModalProps> = ({
  isOpen,
  onClose,
  post,
  onReschedule,
  isRescheduling = false,
}) => {
  return (
    <SchedulePostModalBase
      mode="reschedule"
      isOpen={isOpen}
      onClose={onClose}
      post={post}
      onSubmit={onReschedule}
      isSubmitting={isRescheduling}
    />
  );
};

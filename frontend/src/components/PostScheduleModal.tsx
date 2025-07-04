import React from "react";
import { SchedulePostModalBase } from "./SchedulePostModalBase";
import { Post } from "@/lib/posts-api";

interface PostScheduleModalProps {
  isOpen: boolean;
  onClose: () => void;
  post: Post | null;
  scheduledPosts: Post[];
  onSchedule: (postId: string, scheduledAt: string) => void;
  isScheduling?: boolean;
}

export const PostScheduleModal: React.FC<PostScheduleModalProps> = ({
  isOpen,
  onClose,
  post,
  scheduledPosts,
  onSchedule,
  isScheduling = false,
}) => {
  return (
    <SchedulePostModalBase
      mode="schedule"
      isOpen={isOpen}
      onClose={onClose}
      post={post}
      scheduledPosts={scheduledPosts}
      onSubmit={onSchedule}
      isSubmitting={isScheduling}
    />
  );
};

import { Post } from "@/types/posts";
import { Button } from "@/components/ui/button";
import {
  Edit3,
  RefreshCw,
  Save,
  X,
  Bookmark,
  Calendar,
  Trash2,
} from "lucide-react";
import { useState } from "react";

type ScheduledPostActionsProps = {
  post: Post;
  onSaveForLater?: () => void;
  onReschedule?: () => void;
  onDelete?: () => void;
  onEdit?: () => void;
  handleCancel: () => void;
  handleSave: () => void;
  isProcessing?: boolean;
  isNewPost?: boolean;
  isSaving?: boolean;
  isEditing?: boolean;
};

export const ScheduledPostActions: React.FC<ScheduledPostActionsProps> = ({
  post,
  onSaveForLater,
  onReschedule,
  onDelete,
  onEdit,
  handleCancel,
  handleSave,
  isEditing,
  isSaving,
  isProcessing,
  isNewPost,
}) => {
  if (post.posted_at) {
    return null;
  }

  return isEditing ? (
    <>
      <Button
        variant="outline"
        onClick={handleCancel}
        disabled={isProcessing || isSaving}
      >
        <X className="w-4 h-4 mr-2" />
        Cancel
      </Button>
      <Button onClick={handleSave} disabled={isProcessing || isSaving}>
        {isProcessing || isSaving ? (
          <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
        ) : (
          <Save className="w-4 h-4 mr-2" />
        )}
        Save Changes
      </Button>
    </>
  ) : (
    <>
      {onSaveForLater && (
        <Button
          variant="outline"
          onClick={onSaveForLater}
          disabled={isProcessing}
        >
          {isProcessing ? (
            <>
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Bookmark className="w-4 h-4 mr-2" />
              Remove from Schedule
            </>
          )}
        </Button>
      )}
      <Button variant="outline" onClick={onEdit}>
        <Edit3 className="w-4 h-4 mr-2" />
        Edit
      </Button>
      {onReschedule && (
        <Button variant="default" onClick={onReschedule}>
          <Calendar className="w-4 h-4 mr-2" />
          {isNewPost ? "Schedule" : "Reschedule"}
        </Button>
      )}
      {onDelete && (
        <Button
          variant="destructive"
          onClick={onDelete}
          disabled={isProcessing}
        >
          <Trash2 className="w-4 h-4 mr-2" />
          Delete
        </Button>
      )}
    </>
  );
};

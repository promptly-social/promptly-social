import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Calendar, Bookmark, Edit3, Trash2, RefreshCw } from "lucide-react";
import { Post } from "@/lib/posts-api";

interface ScheduledPostDetailsProps {
  isOpen: boolean;
  onClose: () => void;
  post: Post | null;
  onSaveForLater?: (post: Post) => void;
  onReschedule?: (post: Post) => void;
  onDelete?: (post: Post) => void;
  isProcessing?: boolean;
  isNewPost?: boolean;
  formatDateTime?: (dateString: string) => string;
}

export const ScheduledPostDetails: React.FC<ScheduledPostDetailsProps> = ({
  isOpen,
  onClose,
  post,
  onSaveForLater,
  onReschedule,
  onDelete,
  isProcessing = false,
  isNewPost = false,
  formatDateTime,
}) => {
  const defaultFormatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const dateTimeFormatter = formatDateTime || defaultFormatDateTime;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Scheduled Post Details
          </DialogTitle>
        </DialogHeader>

        {post && (
          <div className="flex-1 overflow-hidden flex flex-col space-y-4">
            <div className="flex-1 overflow-hidden">
              <ScrollArea className="h-[300px]">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap pb-4">
                    {post.content}
                  </p>
                </div>
              </ScrollArea>
            </div>

            <div className="flex-shrink-0 flex items-center gap-4 text-sm text-gray-600">
              <div className="flex items-center gap-1">
                <Calendar className="w-4 h-4" />
                <span>
                  {post.scheduled_at && dateTimeFormatter(post.scheduled_at)}
                </span>
              </div>
            </div>

            {post.topics.length > 0 && (
              <div className="flex-shrink-0 space-y-2">
                <p className="text-sm font-medium text-gray-700">Topics:</p>
                <div className="flex flex-wrap gap-1">
                  {post.topics.map((topic, idx) => (
                    <Badge key={idx} variant="outline" className="text-xs">
                      {topic}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        <DialogFooter className="flex-shrink-0 gap-2">
          {onSaveForLater && (
            <Button
              variant="outline"
              onClick={() => post && onSaveForLater(post)}
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
                  Save for Later
                </>
              )}
            </Button>
          )}
          {onReschedule && (
            <Button
              variant="outline"
              onClick={() => post && onReschedule(post)}
            >
              <Edit3 className="w-4 h-4 mr-2" />
              {isNewPost ? "Schedule" : "Reschedule"}
            </Button>
          )}
          {onDelete && (
            <Button
              variant="destructive"
              onClick={() => post && onDelete(post)}
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Delete
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

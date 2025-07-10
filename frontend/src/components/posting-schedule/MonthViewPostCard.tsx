import React from "react";
import { useDraggable, useDroppable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Clock } from "lucide-react";
import { Post } from "@/lib/posts-api";
import { useIsMobile } from "@/hooks/use-mobile";

interface DraggablePostCardProps {
  post: Post;
  onClick?: () => void;
  className?: string;
  showDragHandle?: boolean;
  isOverlay?: boolean;
  compact?: boolean;
  style?: React.CSSProperties;
  enableDroppable?: boolean;
}

export const MonthViewPostCard: React.FC<DraggablePostCardProps> = ({
  post,
  onClick,
  className = "",
  showDragHandle = true,
  isOverlay = false,
  compact = false,
  style: customStyle,
  enableDroppable = true,
}) => {
  const isMobile = useIsMobile();
  const isPast = post.scheduled_at
    ? new Date(post.scheduled_at) < new Date()
    : false;

  const {
    attributes,
    listeners,
    setNodeRef: setDragRef,
    transform,
    isDragging,
  } = useDraggable({
    id: post.id,
    data: {
      type: "post",
      post,
    },
    disabled: !showDragHandle || isPast,
  });

  const { setNodeRef: setDropRef, isOver } = useDroppable({
    id: post.id,
    disabled: !showDragHandle || !enableDroppable || isPast,
  });

  // Combine the refs
  const setNodeRef = (node: HTMLElement | null) => {
    setDragRef(node);
    if (enableDroppable) {
      setDropRef(node);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    });
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    });
  };

  // Static overlay component - no drag/drop functionality
  if (isOverlay) {
    if (compact) {
      // Compact overlay for calendar views
      return (
        <Card className={`shadow-lg ${className}`} style={customStyle}>
          <CardContent className="p-2.5">
            <div className="flex items-center justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1 mb-1.5">
                  <span className="text-xs font-semibold text-gray-900">
                    {post.scheduled_at && formatTime(post.scheduled_at)}
                  </span>
                </div>
                <p className="text-xs text-gray-600 leading-tight truncate">
                  {post.content}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      );
    } else {
      // Full overlay for list views
      return (
        <Card className={`shadow-lg ${className}`} style={customStyle}>
          <CardContent className="p-2 sm:p-3">
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <div className="bg-gray-50 p-1.5 sm:p-2 rounded-lg mb-1.5 sm:mb-2">
                  <p className="text-xs sm:text-sm text-gray-800 leading-relaxed line-clamp-2">
                    {post.content}
                  </p>
                </div>

                <div className="flex items-center gap-1 sm:gap-2 text-xs sm:text-sm text-gray-600">
                  <div className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    <span>
                      {post.scheduled_at && formatDate(post.scheduled_at)}
                    </span>
                  </div>
                </div>

                {post.topics.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-1.5 sm:mt-2">
                    {post.topics.slice(0, 1).map((topic, idx) => (
                      <Badge key={idx} variant="outline" className="text-xs">
                        {topic}
                      </Badge>
                    ))}
                    {post.topics.length > 1 && (
                      <Badge variant="outline" className="text-xs">
                        +{post.topics.length - 1} more
                      </Badge>
                    )}
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      );
    }
  }

  const style = {
    ...customStyle,
    transform: CSS.Translate.toString(transform),
    opacity: isDragging ? 0 : 1,
  };

  // Compact version for calendar views
  if (compact) {
    return (
      <Card
        ref={setNodeRef}
        style={style}
        className={`transition-all select-none ${
          showDragHandle
            ? "cursor-grab active:cursor-grabbing"
            : "cursor-pointer"
        } hover:shadow-md ${
          isOver && enableDroppable ? "ring-2 ring-blue-400 bg-blue-50" : ""
        } ${className}`}
        {...(showDragHandle ? { ...attributes, ...listeners } : {})}
        onClick={onClick}
      >
        <CardContent className="p-2.5">
          <div className="flex items-center justify-between">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1 mb-1.5">
                <span className="text-xs font-semibold text-gray-900">
                  {post.scheduled_at && formatTime(post.scheduled_at)}
                </span>
              </div>
              <p
                className={`text-xs text-gray-600 leading-tight ${
                  isMobile ? "line-clamp-2" : "truncate"
                }`}
              >
                {post.content}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Full version for list view
  return (
    <Card
      ref={setNodeRef}
      style={style}
      className={`transition-all ${
        showDragHandle ? "cursor-grab active:cursor-grabbing" : "cursor-pointer"
      } hover:shadow-md ${
        isOver && enableDroppable ? "ring-2 ring-blue-400 bg-blue-50" : ""
      } ${className}`}
      onClick={onClick}
      {...(showDragHandle ? { ...attributes, ...listeners } : {})}
    >
      <CardContent className="p-3">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="bg-gray-50 p-2 rounded-lg mb-2">
              <p className="text-sm text-gray-800 leading-relaxed line-clamp-2">
                {post.content}
              </p>
            </div>

            <div className="flex items-center gap-2 text-sm text-gray-600">
              <div className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                <span>
                  {post.scheduled_at && formatDate(post.scheduled_at)}
                </span>
              </div>
            </div>

            {post.topics.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {post.topics.slice(0, 2).map((topic, idx) => (
                  <Badge key={idx} variant="outline" className="text-xs">
                    {topic}
                  </Badge>
                ))}
                {post.topics.length > 2 && (
                  <Badge variant="outline" className="text-xs">
                    +{post.topics.length - 2} more
                  </Badge>
                )}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

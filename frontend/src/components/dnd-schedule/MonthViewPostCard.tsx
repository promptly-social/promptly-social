import React from "react";
import { useDraggable, useDroppable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Clock } from "lucide-react";
import { Post } from "@/types/posts";
import { useIsMobile } from "@/hooks/use-mobile";
import { formatTime, formatDate } from "@/utils/datetime";

interface DraggablePostCardProps {
  post: Post;
  onClick?: () => void;
  className?: string;
  showDragHandle?: boolean;
  isOverlay?: boolean;
  compact?: boolean;
  style?: React.CSSProperties;
  enableDroppable?: boolean;
  isPosted?: boolean;
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
  isPosted = false,
}) => {
  const isMobile = useIsMobile();
  const isPast = post.scheduled_at
    ? new Date(post.scheduled_at) < new Date()
    : false;

  // Posted posts should never be draggable
  const isDragDisabled = !showDragHandle || isPast || isPosted;

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
    disabled: isDragDisabled,
  });

  const { setNodeRef: setDropRef, isOver } = useDroppable({
    id: post.id,
    disabled: !showDragHandle || !enableDroppable || isPast || isPosted,
  });

  // Get styling based on post type
  const getPostStyling = () => {
    if (isPosted) {
      return {
        cardClass:
          "bg-gray-50 border-gray-200 hover:bg-gray-100 hover:border-gray-300 transition-colors",
        textClass: "text-gray-800",
        timeClass: "text-gray-600 font-medium",
        cursor: "cursor-pointer hover:shadow-sm", // No drag cursor for posted posts, subtle hover effect
        contentBg: "bg-gray-50",
        badgeClass: "bg-gray-100 text-gray-800 border-gray-300",
      };
    }
    return {
      cardClass:
        "bg-white border-gray-200 hover:border-gray-300 transition-colors",
      textClass: "text-gray-600",
      timeClass: "text-gray-900",
      cursor: showDragHandle
        ? "cursor-grab active:cursor-grabbing hover:shadow-md"
        : "cursor-pointer hover:shadow-sm",
      contentBg: "bg-gray-50",
      badgeClass: "bg-gray-100 text-gray-800 border-gray-300",
    };
  };

  const styling = getPostStyling();

  // Combine the refs
  const setNodeRef = (node: HTMLElement | null) => {
    setDragRef(node);
    if (enableDroppable) {
      setDropRef(node);
    }
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
          styling.cursor
        } hover:shadow-md ${
          isOver && enableDroppable ? "ring-2 ring-blue-400 bg-blue-50" : ""
        } ${styling.cardClass} ${className}`}
        {...(!isDragDisabled ? { ...attributes, ...listeners } : {})}
        onClick={onClick}
      >
        <CardContent className="p-2.5">
          <div className="flex items-center justify-between">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1 mb-1.5">
                <span className={`text-xs font-semibold ${styling.timeClass}`}>
                  {isPosted
                    ? post.posted_at && formatTime(post.posted_at)
                    : post.scheduled_at && formatTime(post.scheduled_at)}
                </span>
              </div>
              <p
                className={`text-xs ${styling.textClass} leading-tight ${
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
      className={`transition-all ${styling.cursor} hover:shadow-md ${
        isOver && enableDroppable ? "ring-2 ring-blue-400 bg-blue-50" : ""
      } ${styling.cardClass} ${className}`}
      onClick={onClick}
      {...(!isDragDisabled ? { ...attributes, ...listeners } : {})}
    >
      <CardContent className="p-3">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className={`${styling.contentBg} p-2 rounded-lg mb-2`}>
              <p
                className={`text-sm ${
                  isPosted ? "text-green-800" : "text-gray-800"
                } leading-relaxed line-clamp-2`}
              >
                {post.content}
              </p>
            </div>

            <div
              className={`flex items-center gap-2 text-sm ${styling.textClass}`}
            >
              <div className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                <span>
                  {isPosted
                    ? post.posted_at && formatDate(post.posted_at)
                    : post.scheduled_at && formatDate(post.scheduled_at)}
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

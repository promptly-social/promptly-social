import React from "react";
import { PostMedia } from "@/types/posts";
import { UsePostEditorReturn } from "@/hooks/usePostEditor";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { FileVideo, Trash2, X } from "lucide-react";

interface PostEditorFieldsProps {
  editor: UsePostEditorReturn;
  onExistingMediaRemove?: (media: PostMedia) => void;
}

export const PostEditorFields: React.FC<PostEditorFieldsProps> = ({
  editor,
  onExistingMediaRemove,
}) => {
  const {
    content,
    setContent,
    topics,
    topicInput,
    setTopicInput,
    addTopic,
    removeTopic,
    articleUrl,
    setArticleUrl,
    existingMedia,
    mediaFiles,
    mediaPreviews,
    handleMediaFileChange,
    removeExistingMedia,
    removeNewMedia,
  } = editor;
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  // Tooltip open state ensures it only shows on explicit hover.
  const [tooltipOpen, setTooltipOpen] = React.useState(false);

  // Close tooltip automatically when the media limit is cleared.
  React.useEffect(() => {
    if (mediaFiles.length === 0 && existingMedia.length === 0) {
      setTooltipOpen(false);
    }
  }, [mediaFiles.length, existingMedia.length]);

  // Clear the file input value when no new media files remain so picking the
  // same file again will still trigger the `onChange` event.
  React.useEffect(() => {
    if (mediaFiles.length === 0 && fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, [mediaFiles]);

  return (
    <div className="space-y-4">
      <Textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        className="min-h-[200px] max-h-[400px] resize-y w-full"
        autoFocus
        placeholder="Edit your post content..."
      />
      <div className="mt-2 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
        {/* Render existing media */}
        {(existingMedia || [])
          .filter((m) => m.media_type !== "article")
          .map((media) => (
            <div key={media.id} className="relative group">
              {media.media_type === "image" ? (
                <img
                  src={media.gcs_url!}
                  alt={media.file_name!}
                  className="w-full h-24 object-cover rounded max-w-[600]"
                />
              ) : (
                <video
                  src={media.gcs_url!}
                  controls
                  className="w-full h-24 rounded bg-black max-w-[600]"
                />
              )}
              <Button
                variant="destructive"
                size="icon"
                className="absolute top-1 right-1 h-6 w-6 opacity-0 group-hover:opacity-100"
                onClick={() => {
                  removeExistingMedia(media);
                  onExistingMediaRemove?.(media);
                }}
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          ))}
        {/* Render new media previews */}
        {(mediaFiles || []).map((file, index) => (
          <div key={index} className="relative group">
            {mediaPreviews[index] && file.type.startsWith("image/") ? (
              <img
                src={mediaPreviews[index]}
                alt={file.name}
                className="w-full h-24 object-cover rounded max-w-[600]"
              />
            ) : (
              <div className="w-full h-24 bg-gray-100 rounded flex items-center justify-center">
                <FileVideo className="w-8 h-8 text-gray-400" />
              </div>
            )}
            <Button
              variant="destructive"
              size="icon"
              className="absolute top-1 right-1 h-6 w-6 opacity-0 group-hover:opacity-100"
              onClick={() => removeNewMedia(file, index)}
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        ))}
      </div>

      <div className="space-y-2 flex flex-col gap-2">
        <Label htmlFor="article-url">Article URL</Label>
        <Input
          id="article-url"
          placeholder="https://example.com/article"
          value={articleUrl}
          onChange={(e) => setArticleUrl(e.target.value)}
        />
      </div>

      <div className="space-y-2 flex flex-col gap-2">
        <Label htmlFor="media-file">Image/Video</Label>
        <Input
          id="media-file"
          type="file"
          ref={fileInputRef}
          onChange={handleMediaFileChange}
          accept="image/*,video/*"
          className="hidden"
        />

        {/* Determine if an image or video already exists */}
        {(() => {
          const hasExistingMedia =
            existingMedia?.some((m) => m.media_type !== "article") || false;
          const hasNewMedia = (mediaFiles?.length || 0) > 0;
          const mediaLimitReached = hasExistingMedia || hasNewMedia;

          return (
            <Tooltip
              open={tooltipOpen}
              onOpenChange={(open) => setTooltipOpen(open)}
              delayDuration={0}
            >
              <TooltipTrigger
                asChild
                onMouseEnter={() => setTooltipOpen(true)}
                onMouseLeave={() => setTooltipOpen(false)}
              >
                <div>
                  <Button
                    variant="outline"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={mediaLimitReached}
                    className={mediaLimitReached ? "cursor-not-allowed" : ""}
                  >
                    Choose File
                  </Button>
                </div>
              </TooltipTrigger>
              <TooltipContent side="top">
                Only one image or video can be attached per post. Remove the
                existing file to replace it.
              </TooltipContent>
            </Tooltip>
          );
        })()}
      </div>

      <div className="space-y-2">
        <Label htmlFor="topics-input">Categories:</Label>
        <div className="flex flex-wrap gap-2 my-2">
          {(topics || []).map((topic) => (
            <Badge key={topic} variant="secondary">
              {topic}
              <button
                type="button"
                onClick={() => removeTopic(topic)}
                className="ml-1.5 -mr-1 p-0.5 rounded-full hover:bg-background"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
        <Input
          id="topics-input"
          placeholder="Type a category and press Enter to add"
          value={topicInput}
          onChange={(e) => setTopicInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              addTopic();
            }
          }}
        />
      </div>
    </div>
  );
};

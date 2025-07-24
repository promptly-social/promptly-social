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
import { FileVideo, Trash2, Copy, Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { postsApi } from "@/lib/posts-api";
import { PromptGenerationModal } from "./PromptGenerationModal";
import { TopicSelector } from "./TopicSelector";

interface PostEditorFieldsProps {
  editor: UsePostEditorReturn;
  onExistingMediaRemove?: (media: PostMedia) => void;
  isReadOnly?: boolean;
  postStatus?: string;
}

export const PostEditorFields: React.FC<PostEditorFieldsProps> = ({
  editor,
  onExistingMediaRemove,
  isReadOnly = false,
  postStatus,
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
  const { toast } = useToast();
  const [isGeneratingPrompt, setIsGeneratingPrompt] = React.useState(false);
  const [prompt, setPrompt] = React.useState("");
  const [isModalOpen, setIsModalOpen] = React.useState(false);

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

  // Determine if post is posted and should have read-only restrictions
  const isPosted = postStatus === "posted" || isReadOnly;

  const generatePrompt = async () => {
    const trimmedContent = content.trim();
    if (!trimmedContent) {
      toast({
        title: "No content",
        description: "Please enter some post content first.",
        variant: "destructive",
      });
      return;
    }

    setIsGeneratingPrompt(true);

    try {
      const response = await postsApi.generateImagePrompt(trimmedContent);
      if (!response.imagePrompt) {
        throw new Error("Invalid response format: missing imagePrompt");
      }
      setPrompt(response.imagePrompt);
      setIsModalOpen(true);
    } catch (err) {
      console.error("Failed to generate image prompt:", err);
      toast({
        title: "Failed to generate prompt",
        description: "Unable to generate image prompt. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsGeneratingPrompt(false);
    }
  };

  const handleCopyPrompt = (promptToCopy: string) => {
    // The modal already copies to clipboard and shows a toast.
    // This function is mainly for any additional logic needed in the parent.
    console.log("Prompt copied:", promptToCopy);
  };

  return (
    <div className="space-y-4">
      <Textarea
        value={content}
        onChange={isPosted ? undefined : (e) => setContent(e.target.value)}
        readOnly={isPosted}
        className={`min-h-[200px] max-h-[400px] resize-y w-full ${
          isPosted ? "bg-muted/30 cursor-not-allowed text-muted-foreground" : ""
        }`}
        autoFocus={!isPosted}
        placeholder={
          isPosted
            ? "Content cannot be edited for posted posts"
            : "Edit your post content..."
        }
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
              {!isPosted && (
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
              )}
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
              <div className="w-full h-24 bg-muted/30 rounded flex items-center justify-center">
                <FileVideo className="w-8 h-8 text-muted-foreground" />
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
          placeholder={
            isPosted
              ? "Article URL cannot be edited for posted posts"
              : "https://example.com/article"
          }
          value={articleUrl}
          onChange={isPosted ? undefined : (e) => setArticleUrl(e.target.value)}
          readOnly={isPosted}
          className={isPosted ? "bg-muted/30 cursor-not-allowed text-muted-foreground" : ""}
        />
      </div>

      <div className="space-y-2 flex flex-col gap-2">
        <Label htmlFor="media-file">Image</Label>
        <Input
          id="media-file"
          type="file"
          ref={fileInputRef}
          onChange={handleMediaFileChange}
          accept="image/*"
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
                    disabled={mediaLimitReached || isPosted}
                    className={mediaLimitReached || isPosted ? "cursor-not-allowed" : ""}
                  >
                    {isPosted ? "Media Upload Disabled" : "Choose Image"}
                  </Button>
                </div>
              </TooltipTrigger>
              <TooltipContent side="top">
                Only one image can be attached per post. Remove the
                existing file to replace it.
              </TooltipContent>
            </Tooltip>
          );
        })()}

        {/* New AI Image Generation Section */}
        <div className="mt-3 pt-3 border-t border-border">
          <div className="flex flex-col items-start gap-2">
            <span className="text-sm text-muted-foreground">
              Using AI to generate an image?
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={generatePrompt}
              disabled={isGeneratingPrompt || isPosted}
              className="flex items-center gap-2"
            >
              {isGeneratingPrompt ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Copy className="w-4 h-4" />
              )}
              {isPosted
                ? "Disabled for Posted Posts"
                : isGeneratingPrompt
                ? "Generating..."
                : "Generate Prompt"}
            </Button>
          </div>
        </div>
      </div>
      <PromptGenerationModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCopy={handleCopyPrompt}
        onRegenerate={generatePrompt}
        prompt={prompt}
      />

      <TopicSelector
        selectedTopics={topics || []}
        onTopicsChange={(newTopics) => {
          // Update the topics in the editor
          editor.setTopics(newTopics);
        }}
        isReadOnly={isPosted}
      />
    </div>
  );
};

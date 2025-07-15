import React from "react";
import { PostMedia } from "@/types/posts";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { FileVideo, Trash2, X } from "lucide-react";

interface PostEditorFieldsProps {
  content: string;
  onContentChange: (value: string) => void;

  topics: string[];
  topicInput: string;
  onTopicInputChange: (value: string) => void;
  onTopicAdd: () => void;
  onTopicRemove: (topic: string) => void;

  articleUrl: string;
  onArticleUrlChange: (value: string) => void;

  existingMedia: PostMedia[];
  mediaFiles: File[];
  mediaPreviews: string[];
  onMediaFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onExistingMediaRemove: (media: PostMedia) => void;
  onNewMediaRemove: (file: File, index: number) => void;
}

export const PostEditorFields: React.FC<PostEditorFieldsProps> = ({
  content,
  onContentChange,
  topics,
  topicInput,
  onTopicInputChange,
  onTopicAdd,
  onTopicRemove,
  articleUrl,
  onArticleUrlChange,
  existingMedia,
  mediaFiles,
  mediaPreviews,
  onMediaFileChange,
  onExistingMediaRemove,
  onNewMediaRemove,
}) => {
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  return (
    <div className="space-y-4">
      <Textarea
        value={content}
        onChange={(e) => onContentChange(e.target.value)}
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
                onClick={() => onExistingMediaRemove(media)}
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
              onClick={() => onNewMediaRemove(file, index)}
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
          onChange={(e) => onArticleUrlChange(e.target.value)}
        />
      </div>

      <div className="space-y-2 flex flex-col gap-2">
        <Label htmlFor="media-file">Image/Video</Label>
        <Input
          id="media-file"
          type="file"
          ref={fileInputRef}
          multiple
          onChange={onMediaFileChange}
          accept="image/*,video/*"
          className="hidden"
        />
        <Button variant="outline" onClick={() => fileInputRef.current?.click()}>
          Choose Files
        </Button>
      </div>

      <div className="space-y-2">
        <Label htmlFor="topics-input">Categories:</Label>
        <div className="flex flex-wrap gap-2 my-2">
          {(topics || []).map((topic) => (
            <Badge key={topic} variant="secondary">
              {topic}
              <button
                type="button"
                onClick={() => onTopicRemove(topic)}
                className="ml-1.5 -mr-1 p-0.5 rounded-full hover:bg-background"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
        <Input
          id="topics-input"
          placeholder="Type a topic and press Enter to add"
          value={topicInput}
          onChange={(e) => onTopicInputChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              onTopicAdd();
            }
          }}
        />
      </div>
    </div>
  );
};

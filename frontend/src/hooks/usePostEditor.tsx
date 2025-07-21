import React from "react";
import { PostMedia } from "@/types/posts";

export interface PostEditorState {
  content: string;
  topics: string[];
  topicInput: string;
  articleUrl: string;
  existingMedia: PostMedia[];
  mediaFiles: File[];
  mediaPreviews: string[];
}

export interface UsePostEditorReturn extends PostEditorState {
  setContent: (val: string) => void;
  setTopics: (val: string[]) => void;
  setTopicInput: (val: string) => void;
  addTopic: () => void;
  removeTopic: (topic: string) => void;
  setArticleUrl: (val: string) => void;
  handleMediaFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  removeExistingMedia: (media: PostMedia) => void;
  removeNewMedia: (file: File, index: number) => void;
  reset: (init?: Partial<PostEditorState>) => void;
}

export const usePostEditor = (
  initial?: Partial<PostEditorState>
): UsePostEditorReturn => {
  // Core fields
  const [content, setContent] = React.useState(initial?.content ?? "");
  const [topics, setTopics] = React.useState<string[]>(initial?.topics ?? []);
  const [topicInput, setTopicInput] = React.useState("");
  const [articleUrl, setArticleUrl] = React.useState(initial?.articleUrl ?? "");

  // Media handling
  const [existingMedia, setExistingMedia] = React.useState<PostMedia[]>(
    initial?.existingMedia ?? []
  );
  const [mediaFiles, setMediaFiles] = React.useState<File[]>([]);
  const [mediaPreviews, setMediaPreviews] = React.useState<string[]>([]);

  // Cleanup object URLs on unmount
  React.useEffect(() => {
    return () => {
      mediaPreviews.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [mediaPreviews]);

  // Topic helpers
  const addTopic = React.useCallback(() => {
    const trimmed = topicInput.trim();
    if (trimmed && !topics.includes(trimmed)) {
      setTopics([...topics, trimmed]);
    }
    setTopicInput("");
  }, [topicInput, topics]);

  const removeTopic = React.useCallback(
    (topic: string) => {
      setTopics(topics.filter((t) => t !== topic));
    },
    [topics]
  );

  // Media helpers
  const handleMediaFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      // Revoke previous previews to avoid memory leaks
      mediaPreviews.forEach((url) => URL.revokeObjectURL(url));

      const file = e.target.files[0];
      setMediaFiles([file]);
      setMediaPreviews([URL.createObjectURL(file)]);
    }
  };

  const removeNewMedia = (file: File, index: number) => {
    setMediaFiles((prev) => prev.filter((_, i) => i !== index));
    setMediaPreviews((prev) => {
      const next = [...prev];
      const [revoked] = next.splice(index, 1);
      if (revoked) URL.revokeObjectURL(revoked);
      return next;
    });
  };

  const removeExistingMedia = (media: PostMedia) => {
    setExistingMedia((prev) => prev.filter((m) => m.id !== media.id));
  };

  // Reset helper (useful when switching posts or cancelling edits)
  const reset = (init?: Partial<PostEditorState>) => {
    setContent(init?.content ?? "");
    setTopics(init?.topics ?? []);
    setTopicInput("");
    setArticleUrl(init?.articleUrl ?? "");
    setExistingMedia(init?.existingMedia ?? []);
    setMediaFiles([]);
    mediaPreviews.forEach((url) => URL.revokeObjectURL(url));
    setMediaPreviews([]);
  };

  return {
    content,
    topics,
    topicInput,
    articleUrl,
    existingMedia,
    mediaFiles,
    mediaPreviews,
    setContent,
    setTopics,
    setTopicInput,
    addTopic,
    removeTopic,
    setArticleUrl,
    handleMediaFileChange,
    removeExistingMedia,
    removeNewMedia,
    reset,
  };
};

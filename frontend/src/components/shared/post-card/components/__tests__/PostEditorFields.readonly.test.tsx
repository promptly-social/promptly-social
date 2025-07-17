/* eslint-disable @typescript-eslint/no-explicit-any */
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { PostEditorFields } from "../PostEditorFields";
import { UsePostEditorReturn } from "@/hooks/usePostEditor";
import { PostMedia } from "@/types/posts";

// Mock the UI components
vi.mock("@/components/ui/textarea", () => ({
  Textarea: ({ value, onChange, readOnly, className, placeholder, ...props }: any) => (
    <textarea
      value={value}
      onChange={onChange}
      readOnly={readOnly}
      className={className}
      placeholder={placeholder}
      data-testid="content-textarea"
      {...props}
    />
  ),
}));

vi.mock("@/components/ui/input", () => ({
  Input: ({ value, onChange, readOnly, className, placeholder, ...props }: any) => (
    <input
      value={value}
      onChange={onChange}
      readOnly={readOnly}
      className={className}
      placeholder={placeholder}
      data-testid={props.id}
      {...props}
    />
  ),
}));

vi.mock("@/components/ui/button", () => ({
  Button: ({ children, onClick, disabled, className, ...props }: any) => (
    <button
      onClick={onClick}
      disabled={disabled}
      className={className}
      data-testid={props["data-testid"] || "button"}
    >
      {children}
    </button>
  ),
}));

vi.mock("@/components/ui/tooltip", () => ({
  Tooltip: ({ children }: any) => <div>{children}</div>,
  TooltipTrigger: ({ children }: any) => <div>{children}</div>,
  TooltipContent: ({ children }: any) => <div>{children}</div>,
}));

vi.mock("@/lib/posts-api", () => ({
  postsApi: {
    generateImagePrompt: vi.fn(),
  },
}));

const mockEditor: UsePostEditorReturn = {
  content: "Test content",
  setContent: vi.fn(),
  topics: ["test"],
  topicInput: "",
  setTopicInput: vi.fn(),
  addTopic: vi.fn(),
  removeTopic: vi.fn(),
  articleUrl: "https://example.com",
  setArticleUrl: vi.fn(),
  existingMedia: [],
  mediaFiles: [],
  mediaPreviews: [],
  handleMediaFileChange: vi.fn(),
  removeExistingMedia: vi.fn(),
  removeNewMedia: vi.fn(),
  reset: vi.fn(),
};

describe("PostEditorFields - Read-only behavior", () => {
  it("renders content textarea as read-only for posted posts", () => {
    render(
      <PostEditorFields
        editor={mockEditor}
        postStatus="posted"
      />
    );

    const textarea = screen.getByTestId("content-textarea");
    expect(textarea).toHaveAttribute("readOnly");
    expect(textarea).toHaveAttribute("placeholder", "Content cannot be edited for posted posts");
    expect(textarea).toHaveClass("bg-gray-50", "cursor-not-allowed", "text-gray-600");
  });

  it("renders content textarea as editable for non-posted posts", () => {
    render(
      <PostEditorFields
        editor={mockEditor}
        postStatus="draft"
      />
    );

    const textarea = screen.getByTestId("content-textarea");
    expect(textarea).not.toHaveAttribute("readOnly");
    expect(textarea).toHaveAttribute("placeholder", "Edit your post content...");
    expect(textarea).not.toHaveClass("bg-gray-50", "cursor-not-allowed", "text-gray-600");
  });

  it("renders article URL input as read-only for posted posts", () => {
    render(
      <PostEditorFields
        editor={mockEditor}
        postStatus="posted"
      />
    );

    const input = screen.getByTestId("article-url");
    expect(input).toHaveAttribute("readOnly");
    expect(input).toHaveAttribute("placeholder", "Article URL cannot be edited for posted posts");
    expect(input).toHaveClass("bg-gray-50", "cursor-not-allowed", "text-gray-600");
  });

  it("renders article URL input as editable for non-posted posts", () => {
    render(
      <PostEditorFields
        editor={mockEditor}
        postStatus="draft"
      />
    );

    const input = screen.getByTestId("article-url");
    expect(input).not.toHaveAttribute("readOnly");
    expect(input).toHaveAttribute("placeholder", "https://example.com/article");
    expect(input).not.toHaveClass("bg-gray-50", "cursor-not-allowed", "text-gray-600");
  });

  it("disables media upload button for posted posts", () => {
    render(
      <PostEditorFields
        editor={mockEditor}
        postStatus="posted"
      />
    );

    const uploadButton = screen.getByText("Media Upload Disabled");
    expect(uploadButton).toBeDisabled();
    expect(uploadButton).toHaveClass("cursor-not-allowed");
  });

  it("enables media upload button for non-posted posts", () => {
    render(
      <PostEditorFields
        editor={mockEditor}
        postStatus="draft"
      />
    );

    const uploadButton = screen.getByText("Choose Image");
    expect(uploadButton).not.toBeDisabled();
  });

  it("disables AI prompt generation for posted posts", () => {
    render(
      <PostEditorFields
        editor={mockEditor}
        postStatus="posted"
      />
    );

    const promptButton = screen.getByText("Disabled for Posted Posts");
    expect(promptButton).toBeDisabled();
  });

  it("enables AI prompt generation for non-posted posts", () => {
    render(
      <PostEditorFields
        editor={mockEditor}
        postStatus="draft"
      />
    );

    const promptButton = screen.getByText("Generate Prompt");
    expect(promptButton).not.toBeDisabled();
  });

  it("hides media removal buttons for posted posts", () => {
    const mediaWithExisting: PostMedia[] = [
      {
        id: "1",
        post_id: "1",
        user_id: "1",
        media_type: "image",
        file_name: "test.jpg",
        gcs_url: "https://example.com/test.jpg",
        linkedin_asset_urn: null,
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
      },
    ];

    const editorWithMedia = {
      ...mockEditor,
      existingMedia: mediaWithExisting,
    };

    render(
      <PostEditorFields
        editor={editorWithMedia}
        postStatus="posted"
      />
    );

    // Media removal buttons should not be present for posted posts
    expect(screen.queryByRole("button", { name: /delete/i })).not.toBeInTheDocument();
  });

  it("shows media removal buttons for non-posted posts", () => {
    const mediaWithExisting: PostMedia[] = [
      {
        id: "1",
        post_id: "1",
        user_id: "1",
        media_type: "image",
        file_name: "test.jpg",
        gcs_url: "https://example.com/test.jpg",
        linkedin_asset_urn: null,
        created_at: "2024-01-01T00:00:00Z",
        updated_at: "2024-01-01T00:00:00Z",
      },
    ];

    const editorWithMedia = {
      ...mockEditor,
      existingMedia: mediaWithExisting,
    };

    render(
      <PostEditorFields
        editor={editorWithMedia}
        postStatus="draft"
      />
    );

    // Media removal buttons should be present for non-posted posts
    expect(screen.getAllByRole("button")).toHaveLength(4); // Should have multiple buttons including the media removal button
  });

  it("respects explicit isReadOnly prop regardless of post status", () => {
    render(
      <PostEditorFields
        editor={mockEditor}
        postStatus="draft"
        isReadOnly={true}
      />
    );

    const textarea = screen.getByTestId("content-textarea");
    expect(textarea).toHaveAttribute("readOnly");
    expect(textarea).toHaveClass("bg-gray-50", "cursor-not-allowed", "text-gray-600");
  });
});
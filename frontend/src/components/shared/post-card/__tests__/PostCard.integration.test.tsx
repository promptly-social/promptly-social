import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { PostCard } from "../PostCard";
import { Post } from "@/types/posts";
import { ideaBankApi, IdeaBankData } from "@/lib/idea-bank-api";
import { postsApi } from "@/lib/posts-api";

// Mock the APIs
jest.mock("@/lib/idea-bank-api");
jest.mock("@/lib/posts-api");
jest.mock("@/hooks/use-toast", () => ({
  useToast: () => ({ toast: jest.fn() }),
}));

// Mock the UI components
jest.mock("@/components/ui/card", () => ({
  Card: ({ children, className }: any) => <div className={className}>{children}</div>,
  CardContent: ({ children, className }: any) => <div className={className}>{children}</div>,
}));

jest.mock("@/components/ui/button", () => ({
  Button: ({ children, onClick, disabled, className, ...props }: any) => (
    <button
      onClick={onClick}
      disabled={disabled}
      className={className}
      data-testid={props["data-testid"]}
    >
      {children}
    </button>
  ),
}));

jest.mock("@/components/ui/dropdown-menu", () => ({
  DropdownMenu: ({ children }: any) => <div>{children}</div>,
  DropdownMenuContent: ({ children }: any) => <div>{children}</div>,
  DropdownMenuItem: ({ children, onClick }: any) => (
    <div onClick={onClick}>{children}</div>
  ),
  DropdownMenuTrigger: ({ children }: any) => <div>{children}</div>,
}));

// Mock other components
jest.mock("../components/PostCardHeader", () => ({
  PostCardHeader: () => <div>Post Header</div>,
}));

jest.mock("../components/PostContent", () => ({
  PostContent: ({ post }: any) => (
    <div>
      <div>Post Content: {post.content}</div>
    </div>
  ),
}));

jest.mock("../components/PostCardMeta", () => ({
  PostCardMeta: () => <div>Post Meta</div>,
}));

jest.mock("../components/PostCardTopics", () => ({
  PostCardTopics: () => <div>Post Topics</div>,
}));

jest.mock("../components/PostInspiration", () => ({
  PostInspiration: ({ inspiration }: any) => (
    <div>Inspiration: {inspiration.value}</div>
  ),
}));

jest.mock("../components/PostCardActions", () => ({
  PostCardActions: () => <div>Post Actions</div>,
}));

jest.mock("../components/PostSharingError", () => ({
  PostSharingError: () => <div>Sharing Error</div>,
}));

const mockPost: Post = {
  id: "1",
  user_id: "1",
  content: "Test post content",
  platform: "linkedin",
  topics: ["test"],
  status: "suggested",
  idea_bank_id: "idea-1",
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
  media: [],
};

const mockIdeaBankData: IdeaBankData = {
  type: "url",
  value: "https://example.com/inspiration",
  title: "Inspiration Article",
  time_sensitive: false,
  ai_suggested: false,
};

describe("PostCard Integration - Inspiration Fetching", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (postsApi.getPostMedia as jest.Mock).mockResolvedValue([]);
  });

  it("fetches and displays inspiration data when post has idea_bank_id", async () => {
    (ideaBankApi.getIdeaBank as jest.Mock).mockResolvedValue(mockIdeaBankData);

    render(<PostCard post={mockPost} />);

    await waitFor(() => {
      expect(ideaBankApi.getIdeaBank).toHaveBeenCalledWith("idea-1");
    });

    await waitFor(() => {
      expect(screen.getByText("Inspiration: https://example.com/inspiration")).toBeInTheDocument();
    });
  });

  it("does not fetch inspiration when post has no idea_bank_id", async () => {
    const postWithoutIdeaBank = { ...mockPost, idea_bank_id: undefined };

    render(<PostCard post={postWithoutIdeaBank} />);

    await waitFor(() => {
      expect(ideaBankApi.getIdeaBank).not.toHaveBeenCalled();
    });

    expect(screen.queryByText(/Inspiration:/)).not.toBeInTheDocument();
  });

  it("handles inspiration fetching errors gracefully", async () => {
    (ideaBankApi.getIdeaBank as jest.Mock).mockRejectedValue(new Error("API Error"));
    const consoleSpy = jest.spyOn(console, "error").mockImplementation();

    render(<PostCard post={mockPost} />);

    await waitFor(() => {
      expect(ideaBankApi.getIdeaBank).toHaveBeenCalledWith("idea-1");
    });

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(
        "Failed to fetch inspiration data:",
        expect.any(Error)
      );
    });

    expect(screen.queryByText(/Inspiration:/)).not.toBeInTheDocument();

    consoleSpy.mockRestore();
  });

  it("handles media fetch errors gracefully", async () => {
    (ideaBankApi.getIdeaBank as jest.Mock).mockResolvedValue(mockIdeaBankData);
    (postsApi.getPostMedia as jest.Mock).mockRejectedValue(new Error("Media fetch failed"));
    const consoleSpy = jest.spyOn(console, "error").mockImplementation();

    render(<PostCard post={mockPost} />);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith("Failed to load media", expect.any(Error));
    });

    consoleSpy.mockRestore();
  });

  it("refetches inspiration when idea_bank_id changes", async () => {
    (ideaBankApi.getIdeaBank as jest.Mock).mockResolvedValue(mockIdeaBankData);

    const { rerender } = render(<PostCard post={mockPost} />);

    await waitFor(() => {
      expect(ideaBankApi.getIdeaBank).toHaveBeenCalledWith("idea-1");
    });

    const updatedPost = { ...mockPost, idea_bank_id: "idea-2" };
    rerender(<PostCard post={updatedPost} />);

    await waitFor(() => {
      expect(ideaBankApi.getIdeaBank).toHaveBeenCalledWith("idea-2");
    });

    expect(ideaBankApi.getIdeaBank).toHaveBeenCalledTimes(2);
  });
});
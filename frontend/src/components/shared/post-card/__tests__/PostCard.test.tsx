import { render } from "@testing-library/react";
import { PostCard } from "../PostCard";
import { Post } from "@/types/posts";
import { vi } from "vitest";

// Mock the API client
vi.mock("@/lib/auth-api", () => ({
  apiClient: {
    request: vi.fn(),
  },
}));

vi.mock("@/lib/posts-api", () => ({
  postsApi: {
    getPostMedia: vi.fn().mockResolvedValue([]),
  },
}));

vi.mock("@/lib/idea-bank-api", () => ({
  ideaBankApi: {
    getIdeaBank: vi.fn().mockResolvedValue(null),
  },
}));

// Mock the AuthContext to avoid provider errors
vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({
    user: {
      id: "test-user",
      email: "test@example.com",
    },
    isLoading: false,
    signOut: vi.fn(),
  }),
}));

// Mock the ProfileContext to avoid provider errors
vi.mock("@/contexts/ProfileContext", () => ({
  useProfile: () => ({
    profile: {
      id: "test-user",
      bio: "Test bio",
      substacks: [],
    },
    updateProfile: vi.fn(),
    isLoading: false,
  }),
}));

describe("PostCard", () => {
  const post: Post = {
    id: "1",
    user_id: "1",
    content: "Test post content",
    platform: "linkedin",
    topics: ["test", "react"],
    status: "posted",
    linkedin_article_url: "https://www.linkedin.com/pulse/test-article",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    media: [],
  };

  it("renders without crashing", () => {
    render(<PostCard post={post} />);
  });
});
